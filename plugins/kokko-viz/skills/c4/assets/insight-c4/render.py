#!/usr/bin/env python3
"""Render an Insight-branded C4 diagram from a JSON spec.

    python3 render.py context.c4.json                 # writes context.html + context.svg
    python3 render.py '**/*.c4.json' --png            # and rasterises each one
    python3 render.py context.c4.json --check         # spec, C4 and geometry checks only

The spec schema is documented in
``skills/c4/references/insight-diagrams.md#spec-schema``. The renderer is
pure standard library; only ``--png`` shells out, and it tries Playwright
first (true Inter) then ``rsvg-convert``/``magick`` (Arial fallback).

A spec that breaks a C4 labelling rule is not drawn: every element states
its name, ``[Type: technology]`` and description, every relationship a verb
phrase and, between containers, its technology, the title is derived as
``<Diagram type> diagram for <scope>``, and the key is generated from what
the diagram uses. The rules live in ``rules.py`` and are shared with
``lint.py``, which re-checks the rendered SVG.

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
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from layout import Edge, Layout, Node, Zone, text_geometry  # noqa: E402
from rules import (  # noqa: E402
    Finding,
    Model,
    SpecError,
    acronyms_used,
    boundary_label,
    check_model,
    check_set,
    element_class,
    in_scope_system,
    model_from_spec,
    treatment,
)
from tokens import (  # noqa: E402
    ACCENT,
    EDGE_COLOURS,
    EDGE_MARKERS,
    EDGE_WIDTHS,
    ELBOW_R,
    FONTS_HREF,
    HOP_R,
    INK,
    LINK,
    MARGIN,
    MONO,
    MUTED,
    NODE_STROKE_W,
    NODE_STROKE_W_DEFAULT,
    PAPER,
    PRESETS,
    RADIUS_NODE,
    RADIUS_ZONE,
    RAMPS,
    RULE,
    SANS,
    SOFT,
    TREATMENTS,
    ZONE_STROKE_W,
)

# Average glyph advance as a fraction of the font size, measured on Inter 600
# and Geist Mono 400. Only used to wrap and to size label masks.
SANS_ADV = 0.55
MONO_ADV = 0.60

ALLOWED_WIDTHS = (120, 140, 160, 180, 200, 240)
LABEL_WRAP = 30  # characters per relationship label line
MAX_NAME_LINES = 3
MAX_TYPE_LINES = 2
MAX_LABEL_LINES = 2

# What each treatment means, for the key. ``{}`` is filled with the classes
# of element that take the treatment on this diagram (rules.element_class).
TREATMENT_TEXT = {
    "focal": "Focus of this diagram: {}",
    "backend": "{}",
    "store": "{}",
    "external": "{}, not owned by this team",
    "input": "{}",
    "optional": "Optional: {}",
    "retired": "Removed or under review: {}",
}
EDGE_TEXT = {
    "default": "Relationship, one way: source, label, target; the arrowhead marks the target",
    "accent": "Primary flow: the path this diagram exists to show",
    "link": "Relationship with an external system",
}
DASHED_TEXT = " (dashed: asynchronous, optional or fallback)"
ZONE_FILL = {False: "rgba(62,51,45,0.02)", True: "rgba(212,14,140,0.05)"}
ZONE_STROKE = {False: "rgba(62,51,45,0.25)", True: "rgba(212,14,140,0.50)"}
ZONE_DASH = {False: None, True: "4,4"}


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------


def esc(text: str) -> str:
    return html.escape(str(text), quote=True)


def text_w(s: str, size: float, mono: bool = False) -> float:
    return len(s) * size * (MONO_ADV if mono else SANS_ADV)


def wrap(text: str, width: float, size: float, mono: bool = False) -> list[str]:
    """Greedy word wrap to ``width``; never truncates (callers bound the count)."""
    limit = max(4, int((width - 16) / (size * (MONO_ADV if mono else SANS_ADV))))
    lines, cur = [], ""
    for w in text.split():
        trial = f"{cur} {w}".strip()
        if len(trial) <= limit or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def dash_attr(dash: str | None) -> str:
    return f' stroke-dasharray="{dash}"' if dash else ""


def icon_title(slug: str) -> str:
    """``azure-openai`` -> ``Azure OpenAI``, for the key."""
    fixed = {"ai": "AI", "openai": "OpenAI", "sql": "SQL", "api": "API", "bi": "BI", "db": "DB"}
    return " ".join(fixed.get(w, w.capitalize()) for w in slug.split("-"))


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

    def find(self, slug: str) -> Path | None:
        for d in self.dirs:
            cand = d / f"{slug}.svg"
            if cand.is_file():
                return cand
        self.missing.add(slug)
        return None

    def inline(self, slug: str, x: float, y: float, size: int, attr: str = "data-c4-icon") -> str:
        path = self.find(slug)
        if path is None:
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
            f'viewBox="{view_box}" aria-hidden="true" {attr}="{esc(slug)}">{body.strip()}</svg>'
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
            for hx in lay.hops(idx, x0, x1, y0):
                if last or min(x0, end) < hx < max(x0, end):
                    d.append(f"H {hx - sign * HOP_R:g}")
                    sweep = 1 if sign > 0 else 0
                    d.append(f"a {HOP_R},{HOP_R} 0 0,{sweep} {sign * 2 * HOP_R:g},0")
            d.append(f"H {end:g}")
            if not last:
                x2, y2 = points[k + 1]
                vs = 1 if y2 > y1 else -1
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


def label_box(
    x: float, y: float, lw: float, lh: float, vertical: bool, side: int = 1
) -> tuple[float, float, float, float]:
    """The mask rect a label block would occupy at this point on its connector."""
    if vertical:
        left = x + 10 if side > 0 else x - 10 - lw
        return (left, left + lw, y - lh / 2, y + lh / 2)
    return (x - lw / 2, x + lw / 2, y - 8 - lh, y - 8)


def _hits_stroke(box: tuple[float, float, float, float], edges: list[Edge]) -> bool:
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
    lw, lh = edge.label_w, edge.label_h
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
        if length < (lw if horizontal else lh) * 0.5 + 12:
            continue
        for t in (0.5, 0.4, 0.6, 0.3, 0.7, 0.25, 0.75):
            px, py = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            for side in (1, -1) if not horizontal else (1,):
                box = label_box(px, py, lw, lh, not horizontal, side)
                base = rank + abs(t - 0.5) * 2
                penalty = base
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
                if _hits_stroke(box, edges):
                    penalty += 10
                if best is None or penalty < best[0]:
                    best = (penalty, (px, py, not horizontal, side))
                if penalty == base:  # perfectly clear
                    return best[1]
    if best is not None:
        return best[1]
    cx, cy = edge.label_at or (0.0, 0.0)
    return cx, cy, edge.label_vertical, 1


# --------------------------------------------------------------------------
# diagram
# --------------------------------------------------------------------------


class Diagram:
    """One spec, validated into a C4 model, laid out and drawn."""

    def __init__(self, spec: dict, model: Model, icons: Icons) -> None:
        self.spec = spec
        self.model = model
        self.icons = icons
        self.slug = spec.get("slug") or "diagram"
        self.title = model.title
        self.subtitle = model.subtitle
        self.desc = model.desc
        self.eyebrow = spec.get("eyebrow") or f"C4 {model.level} · Insight"
        preset = spec.get("preset", "fit")
        if preset not in PRESETS:
            raise SpecError([Finding("spec", f"unknown preset {preset!r}")])
        pw, ph, ramp_name = PRESETS[preset]
        self.ramp = RAMPS[ramp_name]
        self.fixed = (pw, ph)
        self.warnings: list[str] = []
        bad: list[Finding] = []

        scope = in_scope_system(model)
        self.lines: dict[str, tuple[list[str], list[str], list[str]]] = {}
        self.nodes: dict[str, Node] = {}
        for nid, e in model.elements.items():
            width = e.width or self._auto_width(e.name, e.type_line, e.description)
            if width not in ALLOWED_WIDTHS:
                bad.append(Finding("spec", f"node {nid!r}: width {width} is not one of {ALLOWED_WIDTHS}"))
                width = ALLOWED_WIDTHS[-1]
            names = wrap(e.name, width, self.ramp["node"])
            types = wrap(e.type_line, width, self.ramp["sublabel"], mono=True)
            descs = wrap(e.description, width, self.ramp["desc"])
            if len(names) > MAX_NAME_LINES:
                bad.append(Finding("N1", f"element {nid!r}: the name wraps past {MAX_NAME_LINES} lines; shorten it"))
            if len(types) > MAX_TYPE_LINES:
                bad.append(Finding(
                    "N3", f"element {nid!r}: {e.type_line} wraps past {MAX_TYPE_LINES} lines; shorten the technology",
                ))
            self.lines[nid] = (names, types, descs)
            self.nodes[nid] = Node(
                id=nid,
                name=e.name,
                kind=treatment(e, model.level, scope),
                icon=e.icon,
                href=e.href,
                width=width,
                name_lines=len(names),
                type_lines=len(types),
                desc_lines=len(descs),
            )

        self.rows = [list(r) for r in spec.get("rows", [])]
        placed = [n for row in self.rows for n in row]
        for nid in sorted(set(self.nodes) - set(placed)):
            bad.append(Finding("spec", f"node {nid!r} is not placed on any row"))
        for nid in placed:
            if nid not in self.nodes:
                bad.append(Finding("spec", f"row references unknown node {nid!r}"))
        for nid in sorted({n for n in placed if placed.count(n) > 1}):
            bad.append(Finding("spec", f"node {nid!r} is placed on more than one row"))

        size = self.ramp["arrow"]
        step = size + 3
        self.edge_lines: list[list[tuple[str, str]]] = []
        self.edges: list[Edge] = []
        for r in model.relationships:
            text = wrap(r.label, LABEL_WRAP * size * SANS_ADV + 16, size)
            if len(text) > MAX_LABEL_LINES:
                bad.append(Finding(
                    "L2", f"relationship {r.src}->{r.dst}: the label wraps past {MAX_LABEL_LINES} lines; shorten it",
                ))
            lines = [("c4-label", t) for t in text]
            if r.technology:
                lines.append(("c4-tech", f"[{r.technology}]"))
            lw = max(text_w(t, size, mono=(cls == "c4-tech")) for cls, t in lines) + 10
            self.edge_lines.append(lines)
            self.edges.append(Edge(
                src=r.src, dst=r.dst, label=r.label, kind=r.kind, dashed=r.dashed,
                label_w=lw, label_h=len(lines) * step + 2,
            ))
        if bad:
            raise SpecError(bad)

        self.zones = [
            Zone(label=boundary_label(b), members=list(b.members), security=b.security, label_align=b.label_align)
            for b in model.boundaries
        ]
        self.zone_types = [b.type for b in model.boundaries]
        self.zone_names = [b.name for b in model.boundaries]

        # title band, drawn inside the SVG so the PNG carries it too
        self.title_y = MARGIN + self.ramp["svg_title"]
        self.subtitle_y = self.title_y + self.ramp["sublabel"] + 10 if self.subtitle else self.title_y
        top = -(-(self.subtitle_y + 24) // 4) * 4
        self.lay = Layout(
            self.rows,
            self.nodes,
            self.edges,
            self.zones,
            ramp=ramp_name,
            min_width=pw or 960,
            top=top,
            label_h=max([e.label_h for e in self.edges] + [12]),
        )
        self.lay.run()
        self.width = pw or self.lay.width
        self.content_bottom = self.lay.content_bottom
        self.legend_parts, legend_h = self._legend()
        need = self.content_bottom + legend_h
        if ph and need > ph:
            self.warnings.append(f"content and key need {need}px; the preset height is {ph}px")
        self.height = max(ph or 0, need)

    def _auto_width(self, name: str, type_line: str, description: str) -> int:
        r = self.ramp
        need = max(
            [text_w(w, r["node"]) for w in name.split()]
            + [text_w(name, r["node"]) / 2, text_w(type_line, r["sublabel"], mono=True)]
        ) + 32
        need = max(need, 200 if len(description) > 72 else 160)
        for w in ALLOWED_WIDTHS:
            if need <= w:
                return w
        return ALLOWED_WIDTHS[-1]

    # -- svg pieces ------------------------------------------------------

    def _defs(self) -> str:
        out = ["<defs>"]
        for kind, marker in EDGE_MARKERS.items():
            out.append(
                f'<marker id="{marker}" markerWidth="8" markerHeight="6" refX="7" refY="3" '
                f'orient="auto"><polygon points="0 0, 8 3, 0 6" fill="{EDGE_COLOURS[kind]}"/></marker>'
            )
        out.append("</defs>")
        return "".join(out)

    def _title(self) -> list[str]:
        out = [
            f'<text class="c4-title" x="{MARGIN}" y="{self.title_y}" fill="{INK}" '
            f'font-size="{self.ramp["svg_title"]}" font-weight="600" font-family="{SANS}">{esc(self.title)}</text>'
        ]
        if self.subtitle:
            out.append(
                f'<text class="c4-subtitle" x="{MARGIN}" y="{self.subtitle_y}" fill="{MUTED}" '
                f'font-size="{self.ramp["sublabel"]}" font-family="{MONO}">{esc(self.subtitle)}</text>'
            )
        return out

    def _zones(self) -> list[str]:
        out = []
        for i, (z, ztype) in enumerate(zip(self.zones, self.zone_types)):
            if not z.width:
                continue
            sec = z.security
            out.append(
                f'<g class="c4-boundary" data-c4-boundary="{i}" data-c4-type="{esc(ztype)}" '
                f'data-c4-security="{str(sec).lower()}" data-c4-members="{esc(" ".join(z.members))}">'
                f'<rect class="c4-zone" x="{z.x}" y="{z.y}" width="{z.width}" height="{z.height}" '
                f'rx="{RADIUS_ZONE}" fill="{ZONE_FILL[sec]}" stroke="{ZONE_STROKE[sec]}" '
                f'stroke-width="{ZONE_STROKE_W}"{dash_attr(ZONE_DASH[sec])}/></g>'
            )
        return out

    def _zone_labels(self) -> list[str]:
        """Boundary labels, drawn above the connectors so a line never strikes one through.

        The label slot avoids connectors where it can; on a narrow boundary
        there may be no clear slot, and then the label's mask interrupts the
        line instead of the line crossing the text.
        """
        out = []
        size = 8
        for i, z in enumerate(self.zones):
            if not z.width:
                continue
            lw = text_w(z.label, size, mono=True) + 12
            lx = self.lay.label_slot(z, lw)
            out.append(
                f'<g class="c4-boundary-name" data-c4-boundary="{i}">'
                f'<rect x="{lx:g}" y="{z.y + 4}" width="{lw:g}" height="13" rx="2" fill="{PAPER}"/>'
                f'<text class="c4-boundary-label" x="{lx + lw / 2:g}" y="{z.y + 14}" fill="{MUTED}" '
                f'font-size="{size}" font-family="{MONO}" text-anchor="middle">{esc(z.label)}</text></g>'
            )
        return out

    def _edges(self) -> list[str]:
        out = []
        for i, e in enumerate(self.edges):
            d = elbow_path(e.points, self.lay, i)
            out.append(
                f'<path class="c4-rel" data-c4-rel="{i}" data-c4-from="{esc(e.src)}" data-c4-to="{esc(e.dst)}" '
                f'd="{d}" fill="none" stroke="{EDGE_COLOURS[e.kind]}" stroke-width="{EDGE_WIDTHS[e.kind]}"'
                f'{dash_attr("5,4" if e.dashed else None)} marker-end="url(#{EDGE_MARKERS[e.kind]})"/>'
            )
        nodes = list(self.nodes.values())
        taken: list[tuple[float, float, float, float]] = []
        bounds = (self.width, self.content_bottom)
        size = self.ramp["arrow"]
        step = size + 3
        for i, e in enumerate(self.edges):  # labels after every stroke, so no stroke sits on a mask
            if not e.label_at:
                continue
            cx, cy, vertical, side = place_label(e, nodes, self.edges, taken, bounds)
            bx = label_box(cx, cy, e.label_w, e.label_h, vertical, side)
            taken.append(bx)
            mid = (bx[0] + bx[1]) / 2
            body = [
                f'<rect x="{bx[0]:g}" y="{bx[2]:g}" width="{e.label_w:g}" height="{e.label_h:g}" '
                f'rx="2" fill="{PAPER}"/>'
            ]
            for k, (cls, text) in enumerate(self.edge_lines[i]):
                mono = cls == "c4-tech"
                body.append(
                    f'<text class="{cls}" x="{mid:g}" y="{bx[2] + (k + 1) * step - 2:g}" '
                    f'fill="{MUTED if mono else INK}" font-size="{size}" '
                    f'font-family="{MONO if mono else SANS}" text-anchor="middle">{esc(text)}</text>'
                )
            out.append(f'<g class="c4-rel-label" data-c4-rel="{i}">{"".join(body)}</g>')
        return out

    def _nodes(self) -> list[str]:
        out = []
        for nid, n in self.nodes.items():
            e = self.model.elements[nid]
            fill, stroke, dash, textc = TREATMENTS[n.kind]
            sw = NODE_STROKE_W.get(n.kind, NODE_STROKE_W_DEFAULT)
            body = [
                f'<rect class="c4-underlay" x="{n.x}" y="{n.y}" width="{n.width}" height="{n.height}" '
                f'rx="{RADIUS_NODE}" fill="{PAPER}"/>',
                f'<rect class="c4-shape" x="{n.x}" y="{n.y}" width="{n.width}" height="{n.height}" '
                f'rx="{RADIUS_NODE}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{dash_attr(dash)}/>',
            ]
            icon_sz = self.ramp["icon"]
            if n.icon:
                body.append(self.icons.inline(n.icon, n.cx - icon_sz / 2, n.y + 16, icon_sz))
            name_ys, type_ys, desc_ys, _ = text_geometry(n, self.ramp)
            names, types, descs = self.lines[nid]
            for cls, ys, lines, extra in (
                ("c4-name", name_ys, names,
                 f'fill="{textc}" font-size="{self.ramp["node"]}" font-weight="600" font-family="{SANS}"'),
                ("c4-type", type_ys, types,
                 f'fill="{MUTED}" font-size="{self.ramp["sublabel"]}" font-family="{MONO}"'),
                ("c4-desc", desc_ys, descs,
                 f'fill="{textc}" font-size="{self.ramp["desc"]}" font-family="{SANS}"'),
            ):
                for y, line in zip(ys, lines):
                    body.append(
                        f'<text class="{cls}" x="{n.cx:g}" y="{n.y + y:g}" {extra} '
                        f'text-anchor="middle">{esc(line)}</text>'
                    )
            title = f"<title>{esc(e.name)} {esc(e.type_line)}: {esc(e.description)}</title>"
            group = (
                f'<g class="c4-element" data-c4-id="{esc(nid)}" data-c4-type="{esc(e.type)}" '
                f'data-c4-external="{str(e.external).lower()}" data-c4-treatment="{n.kind}">'
                f'{title}{"".join(body)}</g>'
            )
            if n.href:
                group = f'<a href="{esc(n.href)}" target="_blank" rel="noopener">{group}</a>'
            out.append(group)
        return out

    # -- key -------------------------------------------------------------

    def _key_entries(self) -> list[tuple[str, str, str]]:
        """(data-c4-key, sample svg around the origin, text), one per thing used."""
        m = self.model
        entries: list[tuple[str, str, str]] = [(
            "shape:box",
            f'<rect x="0" y="-5" width="16" height="10" rx="2" fill="{PAPER}" stroke="{SOFT}" stroke-width="1"/>',
            "Box: one element, read as its name, [type: technology], then what it does",
        )]
        classes: dict[str, dict[str, None]] = defaultdict(dict)
        for nid, n in self.nodes.items():
            classes[n.kind][element_class(m.elements[nid])] = None
        for kind in TREATMENTS:
            if kind not in classes:
                continue
            fill, stroke, dash, _ = TREATMENTS[kind]
            sw = NODE_STROKE_W.get(kind, NODE_STROKE_W_DEFAULT)
            entries.append((
                f"treatment:{kind}",
                f'<rect x="0" y="-5" width="16" height="10" rx="2" fill="{fill}" stroke="{stroke}" '
                f'stroke-width="{sw}"{dash_attr(dash)}/>',
                TREATMENT_TEXT[kind].format(" / ".join(classes[kind])),
            ))
        for z, ztype, name in zip(self.zones, self.zone_types, self.zone_names):
            sec = z.security
            what = "Trust boundary" if sec else ("Group" if ztype == "Group" else "Boundary")
            entries.append((
                f"boundary:{name}",
                f'<rect x="0" y="-5" width="16" height="10" rx="2" fill="{ZONE_FILL[sec]}" '
                f'stroke="{ZONE_STROKE[sec]}" stroke-width="{ZONE_STROKE_W}"{dash_attr(ZONE_DASH[sec])}/>',
                f"{what}: {name}" + (f" [{ztype}]" if ztype != "Group" else ""),
            ))
        combos = dict.fromkeys((e.kind, e.dashed) for e in self.edges)
        for kind in EDGE_COLOURS:
            for dashed in (False, True):
                if (kind, dashed) in combos:
                    entries.append((
                        f"relationship:{kind}{':dashed' if dashed else ''}",
                        f'<line x1="0" y1="0" x2="18" y2="0" stroke="{EDGE_COLOURS[kind]}" '
                        f'stroke-width="{EDGE_WIDTHS[kind]}"{dash_attr("5,4" if dashed else None)} '
                        f'marker-end="url(#{EDGE_MARKERS[kind]})"/>',
                        EDGE_TEXT[kind] + (DASHED_TEXT if dashed else ""),
                    ))
        if self.edges:
            tech = any(r.technology for r in m.relationships)
            entries.append((
                "note:label", "",
                "Line label: what the source does to the target"
                + ("; [brackets]: technology or protocol" if tech else ""),
            ))
        icons = dict.fromkeys(n.icon for n in self.nodes.values() if n.icon)
        for slug in icons:
            sample = self.icons.inline(slug, 0, -7, 14, attr="data-c4-key-icon")
            if sample:
                entries.append((f"icon:{slug}", sample, f"Icon: {icon_title(slug)}"))
        entries.append(("note:size", "", "Box size follows the length of its text and carries no meaning"))
        for a in acronyms_used(m):
            entries.append((f"acronym:{a}", "", f"{a}: {m.acronyms[a]}"))
        return entries

    def _legend(self) -> tuple[list[str], int]:
        """The key: every shape, colour, border, line, arrowhead, icon and acronym used."""
        size = self.ramp["legend"]
        row_h = size + 10
        y0 = self.content_bottom + 4
        out = [
            f'<line x1="{MARGIN}" y1="{y0}" x2="{self.width - MARGIN}" y2="{y0}" stroke="{RULE}" stroke-width="1"/>',
            f'<text class="c4-key-heading" x="{MARGIN}" y="{y0 + 20}" fill="{MUTED}" font-size="{size}" '
            f'font-family="{MONO}" font-weight="600" letter-spacing="0.14em">KEY</text>',
        ]
        left = MARGIN + 48
        x, y = left, y0 + 20
        prev = ""
        for key, sample, text in self._key_entries():
            section = key.split(":")[0]
            sample_w = 26 if sample else 0
            w = sample_w + text_w(text, size) + 24
            new_row = section == "acronym" and prev != "acronym"
            if x > left and (new_row or x + w > self.width - MARGIN):
                x, y = left, y + row_h
            attr = f' data-c4-acronym="{esc(key.split(":", 1)[1])}"' if section == "acronym" else ""
            out.append(
                f'<g class="c4-key-entry" data-c4-key="{esc(key)}"{attr} transform="translate({x:g},{y - 3:g})">'
                f'{sample}<text x="{sample_w}" y="3" fill="{MUTED}" font-size="{size}" '
                f'font-family="{SANS}">{esc(text)}</text></g>'
            )
            x += w
            prev = section
        height = y - y0 + row_h + 8
        return out, int(-(-height // 4) * 4)

    # -- assembly --------------------------------------------------------

    def svg(self) -> str:
        parts = [
            f'<svg viewBox="0 0 {self.width} {self.height}" xmlns="http://www.w3.org/2000/svg" '
            f'role="img" aria-labelledby="{self.slug}-title {self.slug}-desc" '
            f'data-c4-schema="2" data-c4-level="{self.model.level}">',
            f'<title id="{self.slug}-title">{esc(self.title)}</title>',
            f'<desc id="{self.slug}-desc">{esc(self.desc)}</desc>',
            self._defs(),
            f'<rect width="100%" height="100%" fill="{PAPER}"/>',
        ]
        parts += self._title()
        parts += self._zones()
        parts += self._edges()
        parts += self._zone_labels()
        parts += self._nodes()
        parts.append(f'<g class="c4-key">{"".join(self.legend_parts)}</g>')
        parts.append("</svg>")
        return "\n".join(parts)

    def page(self, svg: str) -> str:
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
  svg {{ width:100%; min-width:900px; display:block; }}
  svg a {{ cursor:pointer; }}
  svg a:hover rect.c4-shape {{ stroke:var(--accent); }}
</style>
</head>
<body><div class="frame">
<p class="eyebrow">{esc(self.eyebrow)}</p>
{svg}
</div></body></html>
"""


# --------------------------------------------------------------------------
# geometry checks
# --------------------------------------------------------------------------


def check(d: Diagram) -> tuple[list[str], list[str]]:
    """The machine-checkable half of the insight-diagram-design checklist.

    Returns (failures, warnings). A failure means a reader would misread the
    figure: a line behind a box, a label on a box or off the canvas, text
    through a box edge, or a boundary drawn round an element it does not hold.
    """
    fail: list[str] = []
    warn: list[str] = list(d.warnings)
    if len(d.nodes) > 16:
        warn.append(f"{len(d.nodes)} nodes; a C4 level tops out at 16 — split the level")
    if len(d.edges) > 24:
        warn.append(f"{len(d.edges)} edges; the ceiling is 24 — merge parallel relationships")
    accents = [n.id for n in d.nodes.values() if n.kind == "focal"] + [
        f"{e.src}->{e.dst}" for e in d.edges if e.kind == "accent"
    ]
    if len(accents) > 2:
        warn.append(f"{len(accents)} accent elements ({', '.join(accents)}); the ceiling is 2")
    for nid, n in d.nodes.items():
        for v, what in ((n.x, "x"), (n.y, "y"), (n.width, "width"), (n.height, "height")):
            if v % 4:
                warn.append(f"node {nid}: {what}={v} is off the 4px grid")
        name_ys, type_ys, desc_ys, _ = text_geometry(n, d.ramp)
        last = (desc_ys or type_ys or name_ys)[-1]
        if last + 6 > n.height:
            fail.append(f"node {nid}: text reaches {last + 6:g} of a {n.height} box - no bottom margin")
        names, types, descs = d.lines[nid]
        widest = max(
            [text_w(s, d.ramp["node"]) for s in names]
            + [text_w(s, d.ramp["sublabel"], mono=True) for s in types]
            + [text_w(s, d.ramp["desc"]) for s in descs]
        )
        if widest > n.width - 12:
            warn.append(f"node {nid}: text is {widest:.0f}px wide in a {n.width}px box - widen it")
    if text_w(d.title, d.ramp["svg_title"]) > d.width - 2 * MARGIN:
        warn.append("the title is wider than the canvas")

    # a connector must not cross a node it does not terminate on
    for e in d.edges:
        pts = e.points
        for k in range(1, len(pts)):
            x0, y0 = pts[k - 1]
            x1, y1 = pts[k]
            for n in d.nodes.values():
                if n.id in (e.src, e.dst):
                    continue
                if abs(y1 - y0) < 0.5:
                    if n.y + 1 < y0 < n.bottom - 1 and min(x0, x1) < n.right - 1 and max(x0, x1) > n.x + 1:
                        fail.append(f"edge {e.src}->{e.dst} runs behind node {n.id}")
                elif n.x + 1 < x0 < n.right - 1 and min(y0, y1) < n.bottom - 1 and max(y0, y1) > n.y + 1:
                    fail.append(f"edge {e.src}->{e.dst} runs behind node {n.id}")
    # a label mask must not land on a node or off the canvas
    nodes = list(d.nodes.values())
    taken: list[tuple[float, float, float, float]] = []
    bounds = (d.width, d.content_bottom)
    for e in d.edges:
        if not e.label_at:
            continue
        cx, cy, vertical, side = place_label(e, nodes, d.edges, taken, bounds)
        bx = label_box(cx, cy, e.label_w, e.label_h, vertical, side)
        taken.append(bx)
        if bx[0] < 4 or bx[1] > d.width - 4:
            fail.append(f"label {e.label!r} on {e.src}->{e.dst} runs off the canvas")
        for n in nodes:
            if bx[0] < n.right and bx[1] > n.x and bx[2] < n.bottom and bx[3] > n.y:
                fail.append(f"label {e.label!r} on {e.src}->{e.dst} overlaps node {n.id}")
                break
    # a boundary encloses its members and nothing else
    for z in d.zones:
        if not z.width:
            continue
        for n in nodes:
            if n.id not in z.members and n.x < z.x + z.width and n.right > z.x \
                    and n.y < z.y + z.height and n.bottom > z.y:
                fail.append(
                    f"boundary {z.label!r} encloses node {n.id}, which is not its member - "
                    "put members and non-members on different rows"
                )
    if d.icons.missing:
        warn.append("no official icon for: " + ", ".join(sorted(d.icons.missing)) + " (drawn without one)")
    return fail, warn


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


def set_key(path: Path) -> str:
    """Diagrams of one system share a set: ``codemap/<system>/``, else the run."""
    parts = path.resolve().parts
    if "codemap" in parts:
        i = len(parts) - 1 - parts[::-1].index("codemap")
        return "/".join(parts[: i + 2])
    return ""


def build(spec_path: Path, icon_dirs: list[Path]) -> tuple[Diagram | None, list[Finding]]:
    """Validate one spec and lay it out. Returns (diagram or None, findings)."""
    try:
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, [Finding("spec", f"cannot read: {exc}")]
    if not isinstance(spec, dict):
        return None, [Finding("spec", "the spec is not a JSON object")]
    spec.setdefault("slug", spec_path.name.split(".")[0])
    try:
        model = model_from_spec(spec)
        model.path = str(spec_path)
        findings = check_model(model)
        if any(f.severity == "error" for f in findings):
            return None, findings
        return Diagram(spec, model, Icons(icon_dirs)), findings
    except SpecError as exc:
        return None, exc.findings


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
    sets: dict[str, list[Model]] = defaultdict(list)
    for spec_path in sorted(set(paths)):
        diagram, findings = build(spec_path, icon_dirs)
        if diagram is None:
            failures += 1
            print(f"{spec_path}: FAIL (C4 rules)")
            for f in findings:
                print(f"  - {f}")
            continue
        sets[set_key(spec_path)].append(diagram.model)
        svg = diagram.svg()
        out_dir = Path(args.outdir) if args.outdir else spec_path.parent
        stem = spec_path.name.split(".")[0]
        notes: list[str] = []
        if not args.check:
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / f"{stem}.html").write_text(diagram.page(svg), encoding="utf-8")
            if not args.no_svg:
                fonts = FONTS_HREF.replace("&", "&amp;")
                standalone = svg.replace("<defs>", f"<defs><style>@import url('{fonts}');</style>", 1)
                # trailing newline: POSIX, and it keeps end-of-file-fixer style
                # hooks from rewriting every figure on each regeneration
                (out_dir / f"{stem}.svg").write_text(
                    '<?xml version="1.0" encoding="UTF-8"?>\n' + standalone + "\n",
                    encoding="utf-8",
                )
            if args.png:
                how = to_png(out_dir / f"{stem}.html", out_dir / f"{stem}.png", args.scale)
                if how == "no-rasteriser":
                    notes.append("no rasteriser available (playwright, rsvg-convert or magick)")
        fail, warn = check(diagram)
        failures += bool(fail)
        lines = [f"layout: {i}" for i in fail] + [str(f) for f in findings] + warn + notes
        if not args.quiet or lines:
            size = f"{diagram.width}x{diagram.height}"
            status = "FAIL (layout)" if fail else "ok"
            print(f"{spec_path}: {status} ({len(diagram.nodes)} nodes, {len(diagram.edges)} edges, {size})")
            for line in lines:
                print(f"  - {line}")
    for models in sets.values():
        for path, f in check_set(models):
            failures += f.severity == "error"
            print(f"{path}: FAIL (across diagrams)\n  - {f}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
