"""Deterministic orthogonal layout for Insight-styled C4 diagrams.

The layout is a band model: nodes sit on ordered rows, and every connector
runs through a *gutter* (the empty band between two rows) or a *side lane*
(an empty column outside the widest row). Nothing ever routes across a row,
so the "a connector does not pass behind a box that is not its source or
destination" rule holds by construction rather than by inspection.

Routes come in four shapes:

``straight-h``  two nodes adjacent in the same row, drawn side to side.
``straight-v``  two nodes one row apart whose ports line up on one x.
``zigzag``      two nodes one row apart: down, across a gutter channel, down.
``lane``        two nodes more than one row apart: into a gutter, out to a
                side lane, along the lane, back into the far gutter, in.

Every bend is a quarter arc at ``ELBOW_R``; a horizontal channel run that
crosses another route's vertical segment gets a hop.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tokens import (
    CHANNEL_INSET,
    CHANNEL_STEP,
    ELBOW_R,
    LEGEND_H,
    MARGIN,
    NODE_GAP,
    NODE_W,
    RAMPS,
    ZONE_HEADROOM,
    snap,
)

MIN_GUTTER = 64
MIN_EDGE_GUTTER = 48  # the headroom gutter and the one below the last row
BOTTOM_PAD = 32  # clear air under the last row, so a zone never meets the legend
MIN_DX = 20  # below this a zigzag cannot hold two r=8 arcs; straighten instead
PORT_MIN_INSET = 12  # ports never sit within this of a corner


@dataclass
class Node:
    id: str
    name: str
    sublabel: str = ""
    tag: str = ""
    kind: str = "backend"
    icon: str = ""
    href: str = ""
    width: int = NODE_W
    # filled in by layout
    x: int = 0
    y: int = 0
    height: int = 0
    row: int = 0

    @property
    def cx(self) -> float:
        return self.x + self.width / 2

    @property
    def cy(self) -> float:
        return self.y + self.height / 2

    @property
    def right(self) -> int:
        return self.x + self.width

    @property
    def bottom(self) -> int:
        return self.y + self.height


@dataclass
class Edge:
    src: str
    dst: str
    label: str = ""
    kind: str = "default"
    dashed: bool = False
    label_w: float = 0.0  # set by the caller; decides if a label fits a row gap
    # filled in by layout
    shape: str = ""
    points: list[tuple[float, float]] = field(default_factory=list)
    label_at: tuple[float, float] | None = None
    label_vertical: bool = False


@dataclass
class Zone:
    label: str
    members: list[str]
    security: bool = False
    label_align: str = "left"
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0


class Layout:
    """Places nodes on rows and routes every edge orthogonally."""

    def __init__(
        self,
        rows: list[list[str]],
        nodes: dict[str, Node],
        edges: list[Edge],
        zones: list[Zone],
        ramp: str = "standard",
        min_width: int = 960,
    ) -> None:
        self.rows = rows
        self.nodes = nodes
        self.edges = edges
        self.zones = zones
        self.ramp = RAMPS[ramp]
        self.min_width = min_width
        self.width = 0
        self.height = 0
        self.row_y: list[int] = []
        self.row_h: list[int] = []
        self.gutter_y: list[int] = []
        self.gutter_h: list[int] = []
        # gutter index -> ordered list of edge indexes occupying a channel
        self._gutter_edges: dict[int, list[int]] = {}
        self._channel_of: dict[tuple[int, int], int] = {}
        self._lane_of: dict[int, tuple[str, int]] = {}
        self._lanes: dict[str, int] = {"left": 0, "right": 0}
        self._ports: dict[tuple[str, str, int], float] = {}
        self._verticals: list[tuple[int, float, float, float]] = []

    # -- public ----------------------------------------------------------

    def run(self) -> None:
        self._index_rows()
        self._classify_edges()
        self._size_gutters()
        self._place_rows()
        self._assign_lanes()
        self._assign_ports()
        self._route()
        self._place_zones()
        self.height = snap(self.gutter_y[-1] + self.gutter_h[-1] + LEGEND_H)

    # -- rows ------------------------------------------------------------

    def _index_rows(self) -> None:
        for r, ids in enumerate(self.rows):
            for nid in ids:
                self.nodes[nid].row = r
        for r, ids in enumerate(self.rows):
            has_icon = any(self.nodes[i].icon for i in ids)
            h = self.ramp["icon_node_h"] if has_icon else self.ramp["node_h"]
            for nid in ids:
                self.nodes[nid].height = h
            self.row_h.append(h)

    def _row_width(self, r: int) -> int:
        ids = self.rows[r]
        if not ids:
            return 0
        return sum(self.nodes[i].width for i in ids) + NODE_GAP * (len(ids) - 1)

    def _place_rows(self) -> None:
        content_w = max([self._row_width(r) for r in range(len(self.rows))] + [0])
        lane_w = (self._lanes["left"] + self._lanes["right"]) * CHANNEL_STEP
        if lane_w:
            lane_w += 2 * CHANNEL_INSET
        self.width = max(self.min_width, snap(content_w + 2 * MARGIN + lane_w))
        left_pad = self._lanes["left"] * CHANNEL_STEP + (CHANNEL_INSET if self._lanes["left"] else 0)
        right_pad = self._lanes["right"] * CHANNEL_STEP + (CHANNEL_INSET if self._lanes["right"] else 0)
        band_l = MARGIN + left_pad
        band_r = self.width - MARGIN - right_pad

        y = MARGIN
        for r in range(len(self.rows)):
            y += self.gutter_h[r]
            self.gutter_y.append(y - self.gutter_h[r])
            self.row_y.append(snap(y))
            row_w = self._row_width(r)
            x = snap(band_l + (band_r - band_l - row_w) / 2)
            for nid in self.rows[r]:
                n = self.nodes[nid]
                n.x, n.y = x, snap(y)
                x += n.width + NODE_GAP
            y = snap(y + self.row_h[r])
        self.gutter_y.append(y)

    # -- edge classification ---------------------------------------------

    def _adjacent(self, a: Node, b: Node) -> bool:
        ids = self.rows[a.row]
        return abs(ids.index(a.id) - ids.index(b.id)) == 1

    def _classify_edges(self) -> None:
        n_rows = len(self.rows)
        for i, e in enumerate(self.edges):
            a, b = self.nodes[e.src], self.nodes[e.dst]
            dr = b.row - a.row
            if dr == 0:
                # A side-to-side line only works when the row gap can hold the
                # label's mask with its 6px margins; otherwise go over the row.
                if self._adjacent(a, b) and NODE_GAP >= e.label_w + 12:
                    e.shape = "straight-h"
                else:
                    e.shape = "u"
                    self._gutter_edges.setdefault(a.row, []).append(i)
            elif abs(dr) == 1:
                e.shape = "zigzag"
                self._gutter_edges.setdefault(max(a.row, b.row), []).append(i)
            else:
                e.shape = "lane"
                g_src = a.row + 1 if dr > 0 else a.row
                g_dst = b.row if dr > 0 else b.row + 1
                self._gutter_edges.setdefault(g_src, []).append(i)
                self._gutter_edges.setdefault(g_dst, []).append(i)
        # channel order inside a gutter: shortest horizontal span nearest the top
        for g, idxs in self._gutter_edges.items():
            ordered = sorted(
                dict.fromkeys(idxs),
                key=lambda i: (
                    self.edges[i].shape == "u",
                    abs(self.nodes[self.edges[i].src].cx - self.nodes[self.edges[i].dst].cx),
                    i,
                ),
            )
            self._gutter_edges[g] = ordered
            for k, i in enumerate(ordered):
                self._channel_of[(g, i)] = k

    def _zone_top_rows(self) -> set[int]:
        out = set()
        for z in self.zones:
            rows = [self.nodes[m].row for m in z.members if m in self.nodes]
            if rows:
                out.add(min(rows))
        return out

    def _size_gutters(self) -> None:
        n_rows = len(self.rows)
        # Channels fill a gutter from its top down, so a gutter that a zone's
        # headroom band reaches into is grown at the bottom: the wash and its
        # label then sit in clear air instead of under a connector.
        zone_tops = self._zone_top_rows()
        for g in range(n_rows + 1):
            c = len(self._gutter_edges.get(g, []))
            if 0 < g < n_rows:
                floor = MIN_GUTTER
            elif g == n_rows:
                floor = max(BOTTOM_PAD, MIN_EDGE_GUTTER if c else 0)
            else:
                floor = MIN_EDGE_GUTTER if c else 0
            h = max(floor, CHANNEL_INSET * 2 + (c - 1) * CHANNEL_STEP) if c else floor
            if g in zone_tops:
                h = max(h, CHANNEL_INSET + max(0, c - 1) * CHANNEL_STEP + ZONE_HEADROOM + 8)
            self.gutter_h.append(snap(h))

    def _assign_lanes(self) -> None:
        lane_edges = [i for i, e in enumerate(self.edges) if e.shape == "lane"]
        if not lane_edges:
            return
        mid = self._provisional_centre()
        left, right = [], []
        for i in lane_edges:
            e = self.edges[i]
            cx = (self.nodes[e.src].cx + self.nodes[e.dst].cx) / 2
            (left if cx <= mid else right).append(i)
        for side, group in (("left", left), ("right", right)):
            group.sort(key=lambda i: -abs(self.nodes[self.edges[i].src].row - self.nodes[self.edges[i].dst].row))
            for k, i in enumerate(group):
                self._lane_of[i] = (side, k)
            self._lanes[side] = len(group)

    def _provisional_centre(self) -> float:
        widest = max(range(len(self.rows)), key=self._row_width)
        return self._row_width(widest) / 2

    # -- ports -------------------------------------------------------------

    def _port_side(self, e: Edge, at: str) -> str:
        """Which side of the ``at`` ("src"/"dst") node this edge leaves from."""
        a, b = self.nodes[e.src], self.nodes[e.dst]
        if e.shape == "straight-h":
            left_first = a.x < b.x
            if at == "src":
                return "right" if left_first else "left"
            return "left" if left_first else "right"
        if e.shape == "u":
            return "top"
        node, other = (a, b) if at == "src" else (b, a)
        return "bottom" if other.row > node.row else "top"

    def _assign_ports(self) -> None:
        groups: dict[tuple[str, str], list[tuple[float, int, str]]] = {}
        for i, e in enumerate(self.edges):
            for at, nid in (("src", e.src), ("dst", e.dst)):
                side = self._port_side(e, at)
                other = self.nodes[e.dst if at == "src" else e.src]
                desire = other.cy if side in ("left", "right") else self._desired_x(i, at)
                groups.setdefault((nid, side), []).append((desire, i, at))

        for (nid, side), items in groups.items():
            node = self.nodes[nid]
            items.sort()
            span = node.width if side in ("top", "bottom") else node.height
            origin = node.x if side in ("top", "bottom") else node.y
            n = len(items)
            usable = span - 2 * PORT_MIN_INSET
            for k, (_, i, at) in enumerate(items):
                pos = origin + PORT_MIN_INSET + usable * (k + 1) / (n + 1)
                self._ports[(nid, at, i)] = pos
        self._straighten()

    def _desired_x(self, i: int, at: str) -> float:
        e = self.edges[i]
        if e.shape == "lane":
            side, _ = self._lane_of[i]
            return -1e9 if side == "left" else 1e9
        other = self.nodes[e.dst if at == "src" else e.src]
        return other.cx

    def _straighten(self) -> None:
        """Collapse a zigzag whose two ports are almost aligned into one line."""
        counts: dict[tuple[str, str], int] = {}
        for i, e in enumerate(self.edges):
            for at, nid in (("src", e.src), ("dst", e.dst)):
                counts[(nid, self._port_side(e, at))] = counts.get((nid, self._port_side(e, at)), 0) + 1
        for i, e in enumerate(self.edges):
            if e.shape != "zigzag":
                continue
            sx = self._ports[(e.src, "src", i)]
            dx = self._ports[(e.dst, "dst", i)]
            if abs(sx - dx) >= MIN_DX:
                continue
            src_side, dst_side = self._port_side(e, "src"), self._port_side(e, "dst")
            if counts[(e.dst, dst_side)] == 1 and self._inside(self.nodes[e.dst], sx):
                self._ports[(e.dst, "dst", i)] = sx
            elif counts[(e.src, src_side)] == 1 and self._inside(self.nodes[e.src], dx):
                self._ports[(e.src, "src", i)] = dx
            else:
                shift = MIN_DX if dx >= sx else -MIN_DX
                self._ports[(e.dst, "dst", i)] = self._clamp(self.nodes[e.dst], sx + shift)
            e.shape = "straight-v" if abs(
                self._ports[(e.src, "src", i)] - self._ports[(e.dst, "dst", i)]
            ) < 1 else "zigzag"

    @staticmethod
    def _inside(node: Node, x: float) -> bool:
        return node.x + PORT_MIN_INSET <= x <= node.right - PORT_MIN_INSET

    @staticmethod
    def _clamp(node: Node, x: float) -> float:
        return min(max(x, node.x + PORT_MIN_INSET), node.right - PORT_MIN_INSET)

    # -- routing -----------------------------------------------------------

    def _channel_y(self, g: int, i: int) -> float:
        return self.gutter_y[g] + CHANNEL_INSET + self._channel_of[(g, i)] * CHANNEL_STEP

    def _lane_x(self, i: int) -> float:
        side, k = self._lane_of[i]
        if side == "left":
            return MARGIN + CHANNEL_INSET + k * CHANNEL_STEP
        return self.width - MARGIN - CHANNEL_INSET - k * CHANNEL_STEP

    def _route(self) -> None:
        for i, e in enumerate(self.edges):
            a, b = self.nodes[e.src], self.nodes[e.dst]
            if e.shape == "straight-h":
                y = min(a.cy, b.cy)
                sy = self._ports[(e.src, "src", i)]
                dy = self._ports[(e.dst, "dst", i)]
                y = (sy + dy) / 2
                x1 = a.right if a.x < b.x else a.x
                x2 = b.x if a.x < b.x else b.right
                e.points = [(x1, y), (x2, y)]
                e.label_at = ((x1 + x2) / 2, y)
            elif e.shape == "straight-v":
                x = self._ports[(e.src, "src", i)]
                y1 = a.bottom if b.row > a.row else a.y
                y2 = b.y if b.row > a.row else b.bottom
                e.points = [(x, y1), (x, y2)]
                e.label_at = (x, (y1 + y2) / 2)
                e.label_vertical = True
                self._verticals.append((i, x, min(y1, y2), max(y1, y2)))
            elif e.shape == "zigzag":
                g = max(a.row, b.row)
                cy = self._channel_y(g, i)
                x1 = self._ports[(e.src, "src", i)]
                x2 = self._ports[(e.dst, "dst", i)]
                y1 = a.bottom if b.row > a.row else a.y
                y2 = b.y if b.row > a.row else b.bottom
                e.points = [(x1, y1), (x1, cy), (x2, cy), (x2, y2)]
                e.label_at = ((x1 + x2) / 2, cy)
                self._verticals.append((i, x1, min(y1, cy), max(y1, cy)))
                self._verticals.append((i, x2, min(cy, y2), max(cy, y2)))
            elif e.shape == "u":
                g = a.row
                cy = self._channel_y(g, i)
                x1 = self._ports[(e.src, "src", i)]
                x2 = self._ports[(e.dst, "dst", i)]
                e.points = [(x1, a.y), (x1, cy), (x2, cy), (x2, b.y)]
                e.label_at = ((x1 + x2) / 2, cy)
                self._verticals.append((i, x1, cy, a.y))
                self._verticals.append((i, x2, cy, b.y))
            else:  # lane
                down = b.row > a.row
                g_src = a.row + 1 if down else a.row
                g_dst = b.row if down else b.row + 1
                y_src = self._channel_y(g_src, i)
                y_dst = self._channel_y(g_dst, i)
                lx = self._lane_x(i)
                x1 = self._ports[(e.src, "src", i)]
                x2 = self._ports[(e.dst, "dst", i)]
                y1 = a.bottom if down else a.y
                y2 = b.y if down else b.bottom
                e.points = [
                    (x1, y1),
                    (x1, y_src),
                    (lx, y_src),
                    (lx, y_dst),
                    (x2, y_dst),
                    (x2, y2),
                ]
                e.label_at = (lx, (y_src + y_dst) / 2)
                e.label_vertical = True
                self._verticals.append((i, x1, min(y1, y_src), max(y1, y_src)))
                self._verticals.append((i, x2, min(y_dst, y2), max(y_dst, y2)))
                self._verticals.append((i, lx, min(y_src, y_dst), max(y_src, y_dst)))

    def hops(self, i: int, x1: float, x2: float, y: float) -> list[float]:
        """X positions where this horizontal run crosses a foreign vertical."""
        lo, hi = min(x1, x2), max(x1, x2)
        out = []
        for j, vx, vy1, vy2 in self._verticals:
            if j == i:
                continue
            if vy1 + 1 < y < vy2 - 1 and lo + 3 * ELBOW_R < vx < hi - 3 * ELBOW_R:
                out.append(vx)
        return sorted(set(out), reverse=x2 < x1)

    # -- zones -------------------------------------------------------------

    def label_slot(self, z: "Zone", width: float) -> float:
        """An x for the zone label on its top edge that no connector crosses.

        Zones are painted before arrows, so a connector running over the top
        edge would strike through the label text. The label position is free,
        so try the ends first and then walk inward.
        """
        y = z.y
        candidates = [z.x + 12, z.x + z.width - width - 12, z.x + (z.width - width) / 2]
        step = 40
        x = z.x + 12
        while x + width + 12 <= z.x + z.width:
            candidates.append(x)
            x += step
        if z.label_align == "right":
            candidates[0], candidates[1] = candidates[1], candidates[0]
        for cx in candidates:
            if not self._crosses(cx - 4, cx + width + 4, y - 8, y + 20):
                return cx
        return candidates[0]

    def _crosses(self, x0: float, x1: float, y0: float, y1: float) -> bool:
        for e in self.edges:
            pts = e.points
            for k in range(1, len(pts)):
                ax, ay = pts[k - 1]
                bx, by = pts[k]
                if min(ax, bx) - ELBOW_R < x1 and max(ax, bx) + ELBOW_R > x0 \
                        and min(ay, by) - ELBOW_R < y1 and max(ay, by) + ELBOW_R > y0:
                    return True
        return False

    def _place_zones(self) -> None:
        pad = 16
        for z in self.zones:
            members = [self.nodes[m] for m in z.members if m in self.nodes]
            if not members:
                continue
            z.x = snap(min(m.x for m in members) - pad) - 4
            z.width = snap(max(m.right for m in members) + pad - z.x)
            top = min(m.y for m in members)
            z.y = snap(top - ZONE_HEADROOM)
            z.height = snap(max(m.bottom for m in members) + pad - z.y)
