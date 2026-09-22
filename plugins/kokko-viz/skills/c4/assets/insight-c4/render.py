#!/usr/bin/env python3
"""Render an Insight-branded C4 diagram from a JSON spec.

    python3 render.py context.c4.json                 # writes context.html + context.svg
    python3 render.py '**/*.c4.json' --png            # and rasterises each one
    python3 render.py context.c4.json --check         # spec + geometry checks only

The spec schema is documented in
``skills/c4/references/insight-diagrams.md#spec-schema``. The renderer is
pure standard library; only ``--png`` shells out, and it tries Playwright
first (true Inter) then ``rsvg-convert``/``magick`` (Arial fallback).

Design tokens, node treatments and the connector grammar come from the
``insight-diagram-design`` skill and live in ``tokens.py``; the band layout
and the orthogonal router live in ``layout.py``.
"""

from __future__ import annotations

import argparse
import glob
import html
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from layout import Edge, Layout, Node, Zone, text_geometry  # noqa: E402
from tokens import (  # noqa: E402
    ACCENT,
    EDGE_COLOURS,
    EDGE_MARKERS,
    EDGE_WIDTHS,
    ELBOW_R,
    FONTS_HREF,
    HOP_R,
    INK,
    LEGEND_H,
    LINK,
    MARGIN,
    MONO,
    MUTED,
    PAPER,
    PRESETS,
    RADIUS_NODE,
    RADIUS_TAG,
    RADIUS_ZONE,
    RAMPS,
    RULE,
    SANS,
    SOFT,
    TREATMENTS,
    rgba,
)

# Average glyph advance as a fraction of the font size, measured on Inter 600
# and Geist Mono 400. Only used to wrap and to size label masks.
SANS_ADV = 0.55
MONO_ADV = 0.60

KIND_LABELS = {
    "focal": "Focus of this diagram",
    "backend": "Application or component",
    "store": "Data store",
    "external": "External system",
    "input": "Person or actor",
    "optional": "Optional or async",
    "security": "Trust boundary",
    "retired": "Removed or under review",
}
EDGE_LABELS = {
    "default": "Internal call",
    "accent": "Primary flow",
    "link": "HTTP / external API",
}


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------


def esc(text: str) -> str:
    return html.escape(str(text), quote=True)


def text_w(s: str, size: float, mono: bool = False) -> float:
    return len(s) * size * (MONO_ADV if mono else SANS_ADV)


def wrap(name: str, width: float, size: float, max_lines: int = 2) -> list[str]:
    limit = max(4, int((width - 16) / (size * SANS_ADV)))
    words, lines, cur = name.split(), [], ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if len(trial) <= limit or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1][: max(1, limit - 1)].rstrip() + "…"
    return lines


# --------------------------------------------------------------------------
# Azure / Fabric icon inlining
# --------------------------------------------------------------------------


def find_icon_dirs(explicit: str | None) -> list[Path]:
    """Icon packs, in the order the insight-diagram-design skill prescribes."""
    if explicit:
        return [Path(explicit)]
    roots = [
        Path.home() / ".claude/plugins/cache",
        Path.home() / ".claude/skills/synced",
        Path.home() / ".claude/skills",
    ]
    out: list[Path] = []
    for root in roots:
        if not root.is_dir():
            continue
        for sub in ("azure-icons", "fabric-icons/fabric-items", "fabric-icons/fabric-core"):
            out += sorted(root.glob(f"**/insight-diagram-design/**/assets/{sub}"))
    return out


class Icons:
    def __init__(self, dirs: list[Path]) -> None:
        self.dirs = dirs
        self.missing: set[str] = set()
        self._n = 0

    def inline(self, slug: str, x: float, y: float, size: int) -> str:
        path = None
        for d in self.dirs:
            cand = d / f"{slug}.svg"
            if cand.is_file():
                path = cand
                break
        if path is None:
            self.missing.add(slug)
            return ""
        raw = path.read_text(encoding="utf-8")
        m = re.search(r"<svg\b([^>]*)>(.*)</svg>", raw, re.S)
        if not m:
            self.missing.add(slug)
            return ""
        attrs, body = m.group(1), m.group(2)
        vb = re.search(r'viewBox="([^"]+)"', attrs)
        view_box = vb.group(1) if vb else "0 0 18 18"
        body = re.sub(r"<title>.*?</title>", "", body, flags=re.S)
        # The official packs carry fixed gradient ids; two copies of one icon on
        # a page would otherwise share them. Namespace per instance.
        self._n += 1
        pfx = f"i{self._n}_"
        for gid in set(re.findall(r'\bid="([^"]+)"', body)):
            body = body.replace(f'id="{gid}"', f'id="{pfx}{gid}"')
            body = body.replace(f"url(#{gid})", f"url(#{pfx}{gid})")
            body = body.replace(f'href="#{gid}"', f'href="#{pfx}{gid}"')
        return (
            f'<svg x="{x:g}" y="{y:g}" width="{size}" height="{size}" '
            f'viewBox="{view_box}" aria-hidden="true">{body.strip()}</svg>'
        )


# --------------------------------------------------------------------------
# path building
# --------------------------------------------------------------------------


def elbow_path(points: list[tuple[float, float]], lay: Layout, idx: int) -> str:
    """Orthogonal path with r=8 quarter arcs at every bend, hops on crossings."""
    if len(points) < 2:
        return ""
    d = [f"M {points[0][0]:g},{points[0][1]:g}"]
    for k in range(1, len(points)):
        x0, y0 = points[k - 1]
        x1, y1 = points[k]
        horizontal = abs(y1 - y0) < 0.5
        last = k == len(points) - 1
        # shorten the incoming leg by r so the arc into the next leg fits
        if not last:
            x2, y2 = points[k + 1]
            r = min(
                ELBOW_R,
                abs(x1 - x0) / 2 if horizontal else abs(y1 - y0) / 2,
                abs(x2 - x1) / 2 if not horizontal else abs(y2 - y1) / 2,
            )
            r = max(r, 0)
        else:
            r = 0.0
        if horizontal:
            sign = 1 if x1 > x0 else -1
            end = x1 - sign * r
            if not last:
                for hx in lay.hops(idx, x0, x1, y0):
                    if min(x0, end) < hx < max(x0, end):
                        d.append(f"H {hx - sign * HOP_R:g}")
                        sweep = 1 if sign > 0 else 0
                        d.append(f"a {HOP_R},{HOP_R} 0 0,{sweep} {sign * 2 * HOP_R:g},0")
            else:
                for hx in lay.hops(idx, x0, x1, y0):
                    d.append(f"H {hx - sign * HOP_R:g}")
                    sweep = 1 if sign > 0 else 0
                    d.append(f"a {HOP_R},{HOP_R} 0 0,{sweep} {sign * 2 * HOP_R:g},0")
            d.append(f"H {end:g}")
            if not last:
                x2, y2 = points[k + 1]
                vs = 1 if y2 > y1 else -1
                sweep = 1 if (sign > 0) == (vs > 0) else 0
                d.append(f"Q {x1:g},{y1:g} {x1:g},{y1 + vs * r:g}" if r else "")
        else:
            sign = 1 if y1 > y0 else -1
            end = y1 - sign * r
            d.append(f"V {end:g}")
            if not last:
                x2, y2 = points[k + 1]
                hs = 1 if x2 > x1 else -1
                d.append(f"Q {x1:g},{y1:g} {x1 + hs * r:g},{y1:g}" if r else "")
    return " ".join(p for p in d if p)


def label_box(x: float, y: float, lw: float, vertical: bool, side: int = 1) -> tuple[float, float, float, float]:
    """The mask rect a label would occupy at this point on its connector."""
    if vertical:
        left = x + 10 if side > 0 else x - 10 - lw
        return (left, left + lw, y - 6, y + 6)
    return (x - lw / 2, x + lw / 2, y - 20, y - 8)


def _hits_stroke(box: tuple[float, float, float, float], edges: list[Edge], own: Edge) -> bool:
    """True if any connector's stroke runs through this mask rect."""
    x0, x1, y0, y1 = box
    for e in edges:
        pts = e.points
        for k in range(1, len(pts)):
            (ax, ay), (bx, by) = pts[k - 1], pts[k]
            if abs(by - ay) < 0.5:  # horizontal
                if y0 - 1 <= ay <= y1 + 1 and min(ax, bx) < x1 and max(ax, bx) > x0:
                    return True
            elif x0 - 1 <= ax <= x1 + 1 and min(ay, by) < y1 and max(ay, by) > y0:
                return True
    return False


def place_label(
    edge: Edge,
    lw: float,
    nodes: list[Node],
    edges: list[Edge],
    taken: list[tuple[float, float, float, float]],
    bounds: tuple[float, float],
) -> tuple[float, float, bool, int]:
    """Find the point on the connector where the label reads most clearly.

    Rule 2 of the connector grammar keeps a label off its own stroke and rule
    6 keeps its mask off a node whose fill would clip it. Neither is enough on
    a busy gutter, where a mask can land on a different connector, on another
    label, or past the edge of the canvas. So every candidate is scored
    against all four and the best one wins — scored rather than first-clear,
    because on a dense diagram there may be no perfect spot and "least bad in
    clear air" beats "the default, wherever it lands".
    """
    pts = edge.points
    width, height = bounds
    segments = []
    for k in range(1, len(pts)):
        (x0, y0), (x1, y1) = pts[k - 1], pts[k]
        horizontal = abs(y1 - y0) < 0.5
        length = abs(x1 - x0) if horizontal else abs(y1 - y0)
        segments.append((horizontal, length, x0, y0, x1, y1))
    # prefer a long horizontal run: a label reads best above the line
    segments.sort(key=lambda sgm: (not sgm[0], -sgm[1]))

    best: tuple[float, tuple[float, float, bool, int]] | None = None
    for rank, (horizontal, length, x0, y0, x1, y1) in enumerate(segments):
        if length < lw * 0.5 + 12:
            continue
        for t in (0.5, 0.4, 0.6, 0.3, 0.7, 0.25, 0.75):
            px, py = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            for side in (1, -1) if not horizontal else (1,):
                box = label_box(px, py, lw, not horizontal, side)
                penalty = rank + abs(t - 0.5) * 2
                if box[0] < 8 or box[1] > width - 8 or box[2] < 4 or box[3] > height:
                    penalty += 1000
                penalty += 100 * sum(
                    1
                    for n in nodes
                    if box[0] < n.right + 2 and box[1] > n.x - 2
                    and box[2] < n.bottom + 2 and box[3] > n.y - 2
                )
                penalty += 20 * sum(
                    1
                    for b in taken
                    if box[0] < b[1] + 4 and box[1] > b[0] - 4
                    and box[2] < b[3] + 2 and box[3] > b[2] - 2
                )
                if _hits_stroke(box, edges, edge):
                    penalty += 10
                if best is None or penalty < best[0]:
                    best = (penalty, (px, py, not horizontal, side))
                if penalty == rank + abs(t - 0.5) * 2:  # perfectly clear
                    return best[1]
    if best is not None:
        return best[1]
    cx, cy = edge.label_at or (0.0, 0.0)
    return cx, cy, edge.label_vertical, 1


# --------------------------------------------------------------------------
# diagram
# --------------------------------------------------------------------------


class Diagram:
    def __init__(self, spec: dict, icons: Icons) -> None:
        self.spec = spec
        self.icons = icons
        self.slug = spec.get("slug") or "diagram"
        self.title = spec.get("title", self.slug)
        self.eyebrow = spec.get("eyebrow") or f"C4 {spec.get('level', 'diagram')} · Insight"
        self.subtitle = spec.get("subtitle", "")
        self.desc = spec.get("desc", self.title)
        preset = spec.get("preset", "fit")
        if preset not in PRESETS:
            raise SystemExit(f"{self.slug}: unknown preset {preset!r}")
        pw, ph, ramp_name = PRESETS[preset]
        self.ramp = RAMPS[ramp_name]
        self.fixed = (pw, ph)

        raw_nodes = spec.get("nodes", {})
        self.nodes = {
            nid: Node(
                id=nid,
                name=n.get("name", nid),
                sublabel=n.get("sublabel", ""),
                tag=n.get("tag", ""),
                kind=n.get("kind", "backend"),
                icon=n.get("icon", ""),
                href=n.get("href", ""),
                width=int(n.get("width", self._auto_width(n))),
            )
            for nid, n in raw_nodes.items()
        }
        for nid, n in self.nodes.items():
            if n.kind not in TREATMENTS:
                raise SystemExit(f"{self.slug}: node {nid!r} has unknown kind {n.kind!r}")
        for n in self.nodes.values():
            n.name_lines = len(wrap(n.name, n.width, self.ramp["node"]))
        self.rows = [list(r) for r in spec.get("rows", [])]
        known = {n for row in self.rows for n in row}
        missing = set(self.nodes) - known
        if missing:
            raise SystemExit(f"{self.slug}: nodes not placed on any row: {sorted(missing)}")
        for row in self.rows:
            for nid in row:
                if nid not in self.nodes:
                    raise SystemExit(f"{self.slug}: row references unknown node {nid!r}")

        self.edges = []
        for e in spec.get("edges", []):
            if e["from"] not in self.nodes or e["to"] not in self.nodes:
                raise SystemExit(f"{self.slug}: edge {e['from']}->{e['to']} names an unknown node")
            label = e.get("label", "")
            if len(label) > 14:
                raise SystemExit(
                    f"{self.slug}: arrow label {label!r} is over 14 characters"
                )
            self.edges.append(
                Edge(
                    src=e["from"],
                    dst=e["to"],
                    label=label.upper(),
                    kind=e.get("kind", "default"),
                    dashed=bool(e.get("dashed", False)),
                    label_w=text_w(label.upper(), self.ramp["arrow"], mono=True) + 8,
                )
            )
        self.zones = [
            Zone(
                label=z.get("label", "").upper(),
                members=list(z.get("members", [])),
                security=bool(z.get("security", False)),
                label_align=z.get("labelAlign", "left"),
            )
            for z in spec.get("zones", [])
        ]
        if len(self.zones) > 3:
            raise SystemExit(f"{self.slug}: {len(self.zones)} zones; the ceiling is 3")

        self.lay = Layout(
            self.rows,
            self.nodes,
            self.edges,
            self.zones,
            ramp=ramp_name,
            min_width=pw or 960,
        )
        self.lay.run()
        self.width = pw or self.lay.width
        self.height = ph or self.lay.height

    def _auto_width(self, n: dict) -> int:
        size = 12
        longest = max(
            [text_w(w, size) for w in n.get("name", "").split()] + [0]
        )
        sub = text_w(n.get("sublabel", ""), 9, mono=True)
        need = max(longest, sub, text_w(n.get("name", ""), size) / 2) + 32
        for w in (120, 140, 160, 180, 200, 240):
            if need <= w:
                return w
        return 240

    # -- svg pieces ------------------------------------------------------

    def _defs(self) -> str:
        return (
            "<defs>"
            f'<marker id="arrow" markerWidth="8" markerHeight="6" refX="7" refY="3" '
            f'orient="auto"><polygon points="0 0, 8 3, 0 6" fill="{MUTED}"/></marker>'
            f'<marker id="arrow-accent" markerWidth="8" markerHeight="6" refX="7" refY="3" '
            f'orient="auto"><polygon points="0 0, 8 3, 0 6" fill="{ACCENT}"/></marker>'
            f'<marker id="arrow-link" markerWidth="8" markerHeight="6" refX="7" refY="3" '
            f'orient="auto"><polygon points="0 0, 8 3, 0 6" fill="{LINK}"/></marker>'
            "</defs>"
        )

    def _zones(self) -> list[str]:
        out = []
        for z in self.zones:
            if not z.width:
                continue
            fill = "rgba(212,14,140,0.05)" if z.security else "rgba(62,51,45,0.02)"
            stroke = "rgba(212,14,140,0.50)" if z.security else "rgba(62,51,45,0.10)"
            dash = ' stroke-dasharray="4,4"' if z.security else ""
            out.append(
                f'<rect x="{z.x}" y="{z.y}" width="{z.width}" height="{z.height}" '
                f'rx="{RADIUS_ZONE}" fill="{fill}" stroke="{stroke}" stroke-width="0.8"{dash}/>'
            )
            if not z.label:
                continue
            lw = max(28, text_w(z.label, 7, mono=True) + 0.14 * 7 * len(z.label) + 12)
            lx = self.lay.label_slot(z, lw)
            out.append(
                f'<rect x="{lx:g}" y="{z.y + 4}" width="{lw:g}" height="12" rx="2" fill="{PAPER}"/>'
                f'<text x="{lx + lw / 2:g}" y="{z.y + 13}" fill="rgba(62,51,45,0.40)" font-size="7" '
                f'font-family="{MONO}" text-anchor="middle" letter-spacing="0.14em">{esc(z.label)}</text>'
            )
        return out

    def _edges(self) -> list[str]:
        out = []
        for i, e in enumerate(self.edges):
            colour = EDGE_COLOURS.get(e.kind, MUTED)
            marker = EDGE_MARKERS.get(e.kind, "arrow")
            w = EDGE_WIDTHS.get(e.kind, 1.0)
            dash = ' stroke-dasharray="5,4"' if e.dashed else ""
            d = elbow_path(e.points, self.lay, i)
            out.append(
                f'<path d="{d}" fill="none" stroke="{colour}" stroke-width="{w}"'
                f'{dash} marker-end="url(#{marker})"/>'
            )
        nodes = list(self.nodes.values())
        taken: list[tuple[float, float, float, float]] = []
        bounds = (self.width, self.height - LEGEND_H)
        for e in self.edges:  # labels after every stroke, so no stroke sits on a mask
            if not e.label or not e.label_at:
                continue
            size = self.ramp["arrow"]
            lw = text_w(e.label, size, mono=True) + 0.06 * size * len(e.label) + 8
            cx, cy, vertical, side = place_label(e, lw, nodes, self.edges, taken, bounds)
            bx = label_box(cx, cy, lw, vertical, side)
            taken.append(bx)
            ty = cy + 3 if vertical else cy - 11
            out.append(
                f'<rect x="{bx[0]:g}" y="{bx[2]:g}" width="{lw:g}" height="12" rx="2" fill="{PAPER}"/>'
                f'<text x="{(bx[0] + bx[1]) / 2:g}" y="{ty:g}" fill="{SOFT}" font-size="{size}" '
                f'font-family="{MONO}" text-anchor="middle" letter-spacing="0.06em">{esc(e.label)}</text>'
            )
        return out

    def _nodes(self) -> list[str]:
        out = []
        for n in self.nodes.values():
            fill, stroke, dash, textc = TREATMENTS[n.kind]
            dasha = f' stroke-dasharray="{dash}"' if dash else ""
            body = [
                f'<rect x="{n.x}" y="{n.y}" width="{n.width}" height="{n.height}" '
                f'rx="{RADIUS_NODE}" fill="{PAPER}"/>',
                f'<rect x="{n.x}" y="{n.y}" width="{n.width}" height="{n.height}" '
                f'rx="{RADIUS_NODE}" fill="{fill}" stroke="{stroke}" stroke-width="1"{dasha}/>',
            ]
            if n.tag and n.kind != "retired":
                tag = n.tag.upper()[:10]
                tw = max(28, text_w(tag, 7, mono=True) + 0.08 * 7 * len(tag) + 10)
                body.append(
                    f'<rect x="{n.x + 8}" y="{n.y + 6}" width="{tw:g}" height="12" rx="{RADIUS_TAG}" '
                    f'fill="transparent" stroke="{rgba(stroke, 0.40)}" stroke-width="0.8"/>'
                    f'<text x="{n.x + 8 + tw / 2:g}" y="{n.y + 15}" fill="{rgba(stroke, 0.80)}" font-size="7" '
                    f'font-family="{MONO}" text-anchor="middle" letter-spacing="0.08em">{esc(tag)}</text>'
                )
            icon_sz = self.ramp["icon"]
            name_size = self.ramp["node"]
            lines = wrap(n.name, n.width, name_size)
            name_ys, sub_y, _ = text_geometry(n, self.ramp)
            if n.icon:
                body.append(self.icons.inline(n.icon, n.cx - icon_sz / 2, n.y + 16, icon_sz))
            for k, line in enumerate(lines):
                body.append(
                    f'<text x="{n.cx:g}" y="{n.y + name_ys[k]:g}" fill="{textc}" '
                    f'font-size="{name_size}" font-weight="600" font-family="{SANS}" '
                    f'text-anchor="middle">{esc(line)}</text>'
                )
            if n.sublabel and sub_y is not None:
                body.append(
                    f'<text x="{n.cx:g}" y="{n.y + sub_y:g}" fill="{MUTED}" '
                    f'font-size="{self.ramp["sublabel"]}" '
                    f'font-family="{MONO}" text-anchor="middle">{esc(n.sublabel)}</text>'
                )
            inner = "".join(body)
            title = f"<title>{esc(n.name)}{' — ' + esc(n.sublabel) if n.sublabel else ''}</title>"
            if n.href:
                out.append(
                    f'<a href="{esc(n.href)}" target="_blank" rel="noopener">{title}{inner}</a>'
                )
            else:
                out.append(f"<g>{title}{inner}</g>")
        return out

    def _legend(self) -> list[str]:
        kinds = sorted({n.kind for n in self.nodes.values()}, key=lambda k: list(TREATMENTS).index(k))
        edge_kinds = sorted({e.kind for e in self.edges}, key=lambda k: list(EDGE_COLOURS).index(k))
        items = [(k, KIND_LABELS[k], "node") for k in kinds]
        items += [(k, EDGE_LABELS[k], "edge") for k in edge_kinds if k != "default" or len(edge_kinds) > 1]
        if any(e.dashed for e in self.edges):
            items.append(("dashed", "Optional or async", "edge"))
        y = self.height - LEGEND_H + 20
        out = [
            f'<line x1="{MARGIN}" y1="{y - 16}" x2="{self.width - MARGIN}" y2="{y - 16}" '
            f'stroke="{RULE}" stroke-width="1"/>',
            f'<text x="{MARGIN}" y="{y + 4}" fill="{MUTED}" font-size="8" font-family="{MONO}" '
            f'letter-spacing="0.14em">LEGEND</text>',
        ]
        x = MARGIN + 72
        for key, label, sort in items:
            if x + 160 > self.width - MARGIN:
                break
            if sort == "node":
                fill, stroke, dash, _ = TREATMENTS[key]
                dasha = f' stroke-dasharray="{dash}"' if dash else ""
                out.append(
                    f'<rect x="{x}" y="{y - 5}" width="16" height="10" rx="2" fill="{fill}" '
                    f'stroke="{stroke}" stroke-width="0.8"{dasha}/>'
                )
            elif key == "dashed":
                out.append(
                    f'<line x1="{x}" y1="{y}" x2="{x + 16}" y2="{y}" stroke="{MUTED}" '
                    f'stroke-width="1" stroke-dasharray="5,4"/>'
                )
            else:
                out.append(
                    f'<line x1="{x}" y1="{y}" x2="{x + 16}" y2="{y}" stroke="{EDGE_COLOURS[key]}" '
                    f'stroke-width="{EDGE_WIDTHS[key]}"/>'
                )
            out.append(
                f'<text x="{x + 24}" y="{y + 3}" fill="{MUTED}" font-size="8" font-family="{MONO}" '
                f'letter-spacing="0.06em">{esc(label)}</text>'
            )
            x += 160
        return out

    # -- assembly --------------------------------------------------------

    def svg(self, standalone: bool = False) -> str:
        parts = [
            f'<svg viewBox="0 0 {self.width} {self.height}" xmlns="http://www.w3.org/2000/svg" '
            f'role="img" aria-labelledby="{self.slug}-title {self.slug}-desc">',
            f'<title id="{self.slug}-title">{esc(self.title)}</title>',
            f'<desc id="{self.slug}-desc">{esc(self.desc)}</desc>',
            self._defs(),
            f'<rect width="100%" height="100%" fill="{PAPER}"/>',
        ]
        parts += self._zones()
        parts += self._edges()
        parts += self._nodes()
        parts += self._legend()
        parts.append("</svg>")
        return "\n".join(parts)

    def page(self) -> str:
        sub = (
            f'<p class="sub">{esc(self.subtitle)}</p>' if self.subtitle else ""
        )
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{esc(self.title)}</title>
<link href="{FONTS_HREF}" rel="stylesheet">
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  :root {{ --paper:{PAPER}; --paper-2:#F5F5F5; --ink:{INK}; --muted:{MUTED}; --soft:{SOFT};
          --accent:{ACCENT}; --link:{LINK};
          --sans:{SANS}; --mono:{MONO}; --slab:'Roboto Slab','Klinic Slab',Georgia,serif; }}
  body {{ font-family:var(--sans); background:var(--paper); color:var(--ink); min-height:100vh;
         display:flex; align-items:center; justify-content:center; padding:3rem 2rem; }}
  .frame {{ max-width:1200px; width:100%; }}
  .eyebrow {{ font-family:var(--mono); font-size:0.66rem; font-weight:500; letter-spacing:0.18em;
             text-transform:uppercase; color:var(--muted); margin-bottom:0.5rem; }}
  h1 {{ font-family:var(--sans); font-size:clamp(1.5rem,2.4vw + 0.75rem,1.75rem); font-weight:600;
       letter-spacing:-0.02em; line-height:1.15; }}
  .sub {{ font-family:var(--mono); font-size:0.72rem; color:var(--muted); margin-top:0.5rem; }}
  svg {{ width:100%; min-width:900px; display:block; margin-top:1.5rem; }}
  svg a {{ cursor:pointer; }}
  svg a:hover rect[stroke] {{ stroke:var(--accent); }}
</style>
</head>
<body><div class="frame">
<p class="eyebrow">{esc(self.eyebrow)}</p>
<h1>{esc(self.title)}</h1>
{sub}
{self.svg()}
</div></body></html>
"""


# --------------------------------------------------------------------------
# checks
# --------------------------------------------------------------------------


def check(d: Diagram) -> list[str]:
    """The machine-checkable half of the insight-diagram-design checklist."""
    issues: list[str] = []
    n_nodes = len(d.nodes)
    if n_nodes > 16:
        issues.append(f"{n_nodes} nodes; a C4 level tops out at 16 — split the level")
    accents = [n.id for n in d.nodes.values() if n.kind == "focal"]
    if len(accents) > 2:
        issues.append(f"{len(accents)} focal nodes ({', '.join(accents)}); the ceiling is 2")
    for n in d.nodes.values():
        for v, what in ((n.x, "x"), (n.y, "y"), (n.width, "width"), (n.height, "height")):
            if v % 4:
                issues.append(f"node {n.id}: {what}={v} is off the 4px grid")
    # text must stay inside its box, with air under the last baseline
    for n in d.nodes.values():
        name_ys, sub_y, _ = text_geometry(n, d.ramp)
        last = sub_y if sub_y is not None else name_ys[-1]
        if last + 6 > n.height:
            issues.append(
                f"node {n.id}: text reaches {last + 6:g} of a {n.height} box - no bottom margin"
            )
        if name_ys[0] - d.ramp["node"] < 4:
            issues.append(f"node {n.id}: first name line sits on the top edge")
        widest = max(
            [text_w(line, d.ramp["node"]) for line in wrap(n.name, n.width, d.ramp["node"])]
            + [text_w(n.sublabel, d.ramp["sublabel"], mono=True)]
        )
        if widest > n.width - 16:
            issues.append(
                f"node {n.id}: text is {widest:.0f}px wide in a {n.width}px box - widen it"
            )

    # a connector must not cross a node it does not terminate on
    for i, e in enumerate(d.edges):
        pts = e.points
        for k in range(1, len(pts)):
            x0, y0 = pts[k - 1]
            x1, y1 = pts[k]
            for n in d.nodes.values():
                if n.id in (e.src, e.dst):
                    continue
                if abs(y1 - y0) < 0.5:
                    if n.y + 1 < y0 < n.bottom - 1 and min(x0, x1) < n.right - 1 and max(x0, x1) > n.x + 1:
                        issues.append(f"edge {e.src}->{e.dst} runs behind node {n.id}")
                elif n.x + 1 < x0 < n.right - 1 and min(y0, y1) < n.bottom - 1 and max(y0, y1) > n.y + 1:
                    issues.append(f"edge {e.src}->{e.dst} runs behind node {n.id}")
    # a label mask must not land on a node
    nodes = list(d.nodes.values())
    taken: list[tuple[float, float, float, float]] = []
    bounds = (d.width, d.height - LEGEND_H)
    for e in d.edges:
        if not e.label or not e.label_at:
            continue
        size = d.ramp["arrow"]
        lw = text_w(e.label, size, mono=True) + 0.06 * size * len(e.label) + 8
        cx, cy, vertical, side = place_label(e, lw, nodes, d.edges, taken, bounds)
        bx = label_box(cx, cy, lw, vertical, side)
        taken.append(bx)
        if bx[0] < 8 or bx[1] > d.width - 8:
            issues.append(f"label {e.label!r} on {e.src}->{e.dst} runs off the canvas")
        for n in nodes:
            if bx[0] < n.right and bx[1] > n.x and bx[2] < n.bottom and bx[3] > n.y:
                issues.append(f"label {e.label!r} on {e.src}->{e.dst} overlaps node {n.id}")
                break
    if d.icons.missing:
        issues.append(
            "no official icon for: " + ", ".join(sorted(d.icons.missing)) + " (drawn without one)"
        )
    return issues


# --------------------------------------------------------------------------
# png
# --------------------------------------------------------------------------


def to_png(html_path: Path, png_path: Path, scale: int) -> str:
    """Rasterise. Playwright renders real Inter; rsvg/magick fall back to Arial."""
    script = f"""
const {{ chromium }} = require('playwright');
(async () => {{
  const b = await chromium.launch();
  const p = await b.newPage({{ deviceScaleFactor: {scale} }});
  await p.goto('file://{html_path.resolve()}');
  await p.waitForLoadState('networkidle');
  await p.locator('svg').first().screenshot({{ path: '{png_path.resolve()}', omitBackground: true }});
  await b.close();
}})();
"""
    for cwd in (Path.cwd(), Path.cwd() / "src/frontend", Path.cwd() / "frontend"):
        if (cwd / "node_modules/playwright").is_dir() or (cwd / "node_modules/@playwright/test").is_dir():
            tmp = cwd / ".c4-shot.js"
            tmp.write_text(script)
            try:
                r = subprocess.run(["node", str(tmp)], cwd=cwd, capture_output=True, text=True)
                if r.returncode == 0 and png_path.exists():
                    return "playwright"
            finally:
                tmp.unlink(missing_ok=True)
    svg_path = html_path.with_suffix(".svg")
    if not svg_path.exists():
        return "no-rasteriser"
    if shutil.which("rsvg-convert"):
        subprocess.run(
            ["rsvg-convert", "-z", str(scale), "-o", str(png_path), str(svg_path)], check=True
        )
        return "rsvg-convert"
    if shutil.which("magick"):
        subprocess.run(
            ["magick", "-density", str(96 * scale), str(svg_path), "-background", "none", str(png_path)],
            check=True,
        )
        return "magick"
    return "no-rasteriser"


# --------------------------------------------------------------------------
# cli
# --------------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("specs", nargs="+", help="spec JSON files or globs")
    ap.add_argument("-o", "--outdir", help="write beside the spec when omitted")
    ap.add_argument("--png", action="store_true", help="also rasterise")
    ap.add_argument("--scale", type=int, default=2, help="PNG scale factor (2 doc, 3 print)")
    ap.add_argument("--no-svg", action="store_true", help="skip the standalone .svg")
    ap.add_argument("--icons", help="icon pack directory (auto-discovered otherwise)")
    ap.add_argument("--check", action="store_true", help="run checks only, write nothing")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    paths: list[Path] = []
    for pattern in args.specs:
        hits = [Path(p) for p in glob.glob(pattern, recursive=True)]
        paths += hits or ([Path(pattern)] if Path(pattern).exists() else [])
    if not paths:
        print("no spec files matched", file=sys.stderr)
        return 1

    icon_dirs = find_icon_dirs(args.icons)
    failures = 0
    for spec_path in sorted(set(paths)):
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        spec.setdefault("slug", spec_path.name.split(".")[0])
        diagram = Diagram(spec, Icons(icon_dirs))
        issues = check(diagram)
        out_dir = Path(args.outdir) if args.outdir else spec_path.parent
        stem = spec_path.name.split(".")[0]
        if not args.check:
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / f"{stem}.html").write_text(diagram.page(), encoding="utf-8")
            if not args.no_svg:
                svg = diagram.svg(standalone=True)
                fonts = FONTS_HREF.replace("&", "&amp;")
                svg = svg.replace(
                    "<defs>", f"<defs><style>@import url('{fonts}');</style>", 1
                )
                (out_dir / f"{stem}.svg").write_text(
                    '<?xml version="1.0" encoding="UTF-8"?>\n' + svg, encoding="utf-8"
                )
            if args.png:
                how = to_png(out_dir / f"{stem}.html", out_dir / f"{stem}.png", args.scale)
                if how == "no-rasteriser":
                    issues.append("no rasteriser available (playwright, rsvg-convert or magick)")
        status = "FAIL" if any("runs behind" in i or "overlaps node" in i for i in issues) else "ok"
        if status == "FAIL":
            failures += 1
        if not args.quiet or issues:
            size = f"{diagram.width}x{diagram.height}"
            print(f"{spec_path}: {status} ({len(diagram.nodes)} nodes, {len(diagram.edges)} edges, {size})")
            for issue in issues:
                print(f"  - {issue}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
