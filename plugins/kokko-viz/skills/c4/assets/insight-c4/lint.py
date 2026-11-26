#!/usr/bin/env python3
"""Lint rendered C4 diagrams against the C4 labelling rules, by rule id.

    python3 lint.py 'codemap/**/*.svg'            # one line per violation
    python3 lint.py 'codemap/**/*.svg' --json     # the same, as JSON

``render.py`` refuses to draw a spec that breaks a rule; this checks what was
actually drawn, so a hand-edited, stale or foreign SVG is caught too. It
rebuilds the C4 model from the semantic markup the renderer emits
(``c4-element``, ``c4-rel``, ``c4-boundary``, ``c4-key``) and runs the same
checks as the renderer (``rules.py``), plus the ones only the output can
answer: the title is visible, and the key is present and explains every
colour, shape, border and line style, arrowhead and icon on the page.

Rule ids are the lint table in ``references/insight-diagrams.md#lint-rules``.
An SVG without the markup (drawn by hand or by another tool) fails T1/K1 and
is reported as not produced by this renderer. Exit status is non-zero when any
error-severity finding is reported.
"""

from __future__ import annotations

import argparse
import glob
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from rules import (  # noqa: E402
    TYPE_LINE_RE,
    Boundary,
    Element,
    Finding,
    Model,
    Relationship,
    check_model,
    check_set,
)
from tokens import EDGE_MARKERS  # noqa: E402

KIND_OF_MARKER = {v: k for k, v in EDGE_MARKERS.items()}


def _strip_ns(root: ET.Element) -> ET.Element:
    for el in root.iter():
        if isinstance(el.tag, str) and "}" in el.tag:
            el.tag = el.tag.split("}", 1)[1]
    return root


def load_svg(path: Path) -> ET.Element:
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".html":
        m = re.search(r"<svg\b.*</svg>", text, re.S)
        if not m:
            raise ValueError("no <svg> in the page")
        text = m.group(0)
    return _strip_ns(ET.fromstring(text))


def _classes(el: ET.Element) -> set[str]:
    return set((el.get("class") or "").split())


def _find(root: ET.Element, cls: str) -> list[ET.Element]:
    return [el for el in root.iter() if cls in _classes(el)]


def _joined(group: ET.Element, cls: str) -> str:
    return " ".join((t.text or "").strip() for t in group.iter("text") if cls in _classes(t)).strip()


def _marker(value: str | None) -> str:
    m = re.match(r"url\(#([^)]+)\)", value or "")
    return m.group(1) if m else ""


def model_from_svg(root: ET.Element, path: str) -> tuple[Model, list[Finding]]:
    """Rebuild the C4 model from the renderer's markup, plus output-only findings."""
    out: list[Finding] = []
    level = root.get("data-c4-level") or ""
    titles = _find(root, "c4-title")
    title = (titles[0].text or "").strip() if titles else ""
    if not title:
        out.append(Finding("T1", "no visible title; an <svg><title> alone is not visible"))
    subtitle = " ".join((t.text or "").strip() for t in _find(root, "c4-subtitle"))

    elements: dict[str, Element] = {}
    for g in _find(root, "c4-element"):
        line = _joined(g, "c4-type")
        match = TYPE_LINE_RE.match(line)
        treat = g.get("data-c4-treatment") or ""
        icon = next((s.get("data-c4-icon") for s in g.iter("svg") if s.get("data-c4-icon")), "")
        nid = g.get("data-c4-id") or f"element-{len(elements)}"
        elements[nid] = Element(
            id=nid,
            name=_joined(g, "c4-name"),
            type=g.get("data-c4-type") or "",
            technology=(match.group(2) or "") if match else "",
            description=_joined(g, "c4-desc"),
            external=g.get("data-c4-external") == "true",
            store=treat == "store",
            focus=treat == "focal",
            status=treat if treat in ("optional", "retired") else "",
            icon=icon or "",
            type_line=line or "[]",
        )

    labels = {g.get("data-c4-rel"): g for g in _find(root, "c4-rel-label")}
    rels: list[Relationship] = []
    for p in _find(root, "c4-rel"):
        src, dst = p.get("data-c4-from") or "", p.get("data-c4-to") or ""
        if p.get("marker-start") or not p.get("marker-end"):
            out.append(Finding("L4", f"relationship {src}->{dst} is not drawn one way (one marker-end, no marker-start)"))
        if src not in elements or dst not in elements:
            out.append(Finding("L1", f"relationship {src}->{dst} does not join two drawn elements"))
            continue
        g = labels.get(p.get("data-c4-rel"))
        tech = _joined(g, "c4-tech") if g is not None else ""
        rels.append(Relationship(
            src=src, dst=dst,
            label=_joined(g, "c4-label") if g is not None else "",
            technology=tech[1:-1] if tech.startswith("[") and tech.endswith("]") else tech,
            kind=KIND_OF_MARKER.get(_marker(p.get("marker-end")), "default"),
            dashed=bool(p.get("stroke-dasharray")),
        ))

    names = {g.get("data-c4-boundary"): _joined(g, "c4-boundary-label") for g in _find(root, "c4-boundary-name")}
    bounds: list[Boundary] = []
    for g in _find(root, "c4-boundary"):
        btype = g.get("data-c4-type") or ""
        label = names.get(g.get("data-c4-boundary"), "")
        suffix = f" [{btype}]"
        bounds.append(Boundary(
            name=label[: -len(suffix)] if label.endswith(suffix) else label,
            type=btype,
            members=[m for m in (g.get("data-c4-members") or "").split() if m in elements],
            security=g.get("data-c4-security") == "true",
        ))

    acronyms: dict[str, str] = {}
    for g in root.iter():
        a = g.get("data-c4-acronym")
        if a:
            text = " ".join((t.text or "") for t in g.iter("text"))
            acronyms[a] = text.split(":", 1)[1].strip() if ":" in text else ""
    m = Model(
        level=level if level in ("context", "container", "component") else "context",
        elements=elements, relationships=rels, boundaries=bounds, acronyms=acronyms,
        title=title, subtitle=subtitle, path=path,
    )
    if level not in ("context", "container", "component"):
        out.append(Finding("T2", f"diagram level {level!r} is missing or not context, container or component"))
    return m, out + check_key(root)


def _style(el: ET.Element) -> dict[str, str]:
    return {k: el.get(k) or "" for k in ("fill", "stroke", "stroke-dasharray", "stroke-width")}


def check_key(root: ET.Element) -> list[Finding]:
    """K1-K7: the key exists and explains every visual distinction on the page."""
    keys = _find(root, "c4-key")
    entries = [e for k in keys for e in _find(k, "c4-key-entry")]
    if not entries:
        return [Finding("K1", "no key/legend on the diagram")]
    out: list[Finding] = []
    samples = [el for e in entries for el in e.iter() if el.tag in ("rect", "line", "path", "ellipse", "polygon")]
    key_fill = {s.get("fill") for s in samples} | {s.get("stroke") for s in samples}
    key_dash = {s.get("stroke-dasharray") or "" for s in samples}
    key_width = {s.get("stroke-width") or "" for s in samples}
    key_markers = {_marker(s.get("marker-end")) for s in samples}
    key_shapes = {s.tag for s in samples}
    key_icons = {el.get("data-c4-key-icon") for e in entries for el in e.iter() if el.get("data-c4-key-icon")}

    drawn = _find(root, "c4-shape") + _find(root, "c4-zone") + _find(root, "c4-rel")
    colours, dashes, widths, shapes = set(), set(), set(), set()
    for el in drawn:
        st = _style(el)
        colours |= {c for c in (st["fill"], st["stroke"]) if c and c not in ("none", "transparent")}
        dashes.add(st["stroke-dasharray"])
        widths.add(st["stroke-width"])
        if "c4-rel" not in _classes(el):
            shapes.add(el.tag)
    for c in sorted(colours - key_fill):
        out.append(Finding("K2", f"colour {c} is used but has no sample in the key"))
    for s in sorted(shapes - key_shapes):
        out.append(Finding("K3", f"shape <{s}> is used but not shown in the key"))
    for d in sorted(dashes - key_dash):
        out.append(Finding("K4", f"line or border style dash {d!r} is used but not shown in the key"))
    for w in sorted(widths - key_width):
        out.append(Finding("K4", f"line or border width {w} is used but not shown in the key"))
    for mk in sorted({_marker(p.get("marker-end")) for p in _find(root, "c4-rel")} - key_markers - {""}):
        out.append(Finding("K5", f"arrowhead {mk!r} is used but not shown in the key"))
    icons = {s.get("data-c4-icon") for g in _find(root, "c4-element") for s in g.iter("svg") if s.get("data-c4-icon")}
    for i in sorted(icons - key_icons):
        out.append(Finding("K6", f"icon {i!r} is used but not explained in the key"))
    if not any(e.get("data-c4-key") == "note:size" for e in entries):
        sizes: dict[str, set[str]] = defaultdict(set)
        for g in _find(root, "c4-element"):
            for r in _find(g, "c4-shape"):
                sizes[g.get("data-c4-type") or ""].add(f"{r.get('width')}x{r.get('height')}")
        if any(len(v) > 1 for v in sizes.values()):
            out.append(Finding("K7", "box sizes vary within an element type and the key does not say size carries no meaning"))
    return out


def set_key(path: Path) -> str:
    parts = path.resolve().parts
    if "codemap" in parts:
        i = len(parts) - 1 - parts[::-1].index("codemap")
        return "/".join(parts[: i + 2])
    return ""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+", help="rendered .svg (or .html) files or globs")
    ap.add_argument("--json", action="store_true", help="print findings as a JSON array")
    args = ap.parse_args()

    paths: list[Path] = []
    for pattern in args.files:
        hits = [Path(p) for p in glob.glob(pattern, recursive=True)]
        paths += hits or ([Path(pattern)] if Path(pattern).exists() else [])
    if not paths:
        print("no files matched", file=sys.stderr)
        return 1

    report: list[tuple[str, Finding]] = []
    sets: dict[str, list[Model]] = defaultdict(list)
    for path in sorted(set(paths)):
        try:
            root = load_svg(path)
        except (OSError, ValueError, ET.ParseError) as exc:
            report.append((str(path), Finding("T1", f"cannot parse: {exc}")))
            continue
        if root.get("data-c4-diagram") == "none":
            # a supplementary view that declares itself not a C4 diagram (for example
            # a module view of a shared library) is out of scope, reported as skipped
            report.append((str(path), Finding("skip", "declares data-c4-diagram=\"none\": not a C4 diagram, not linted", "review")))
            continue
        if root.get("data-c4-schema") != "2":
            report.append((str(path), Finding(
                "T1", "not drawn by the kokko-viz renderer (no C4 markup); regenerate it from its .c4.json",
            )))
            continue
        model, found = model_from_svg(root, str(path))
        report += [(str(path), f) for f in found + check_model(model)]
        sets[set_key(path)].append(model)
    for models in sets.values():
        report += check_set(models)

    if args.json:
        print(json.dumps(
            [{"file": p, "rule": f.rule, "severity": f.severity, "message": f.message} for p, f in report],
            indent=2,
        ))
    else:
        by_file: dict[str, list[Finding]] = defaultdict(list)
        for p, f in report:
            by_file[p].append(f)
        for path in sorted({str(p) for p in paths} | set(by_file)):
            found = by_file.get(path, [])
            status = "FAIL" if any(f.severity == "error" for f in found) else "ok"
            print(f"{path}: {status}")
            for f in found:
                print(f"  - {f}")
    return 1 if any(f.severity == "error" for _, f in report) else 0


if __name__ == "__main__":
    raise SystemExit(main())
