"""C4 labelling rules, shared by the renderer and the SVG linter.

One model, one set of checks, two front ends:

``render.py`` builds a :class:`Model` from a ``.c4.json`` spec and refuses
to draw a diagram that breaks a rule. ``lint.py`` rebuilds the same model
from a rendered ``.svg`` and runs the same checks, plus the ones only the
output can answer (is the key on the page, does it cover every colour).

Every finding carries the rule id from the lint table in
``references/insight-diagrams.md#lint-rules`` (T, K, N, L, S and X rules).
``error`` findings fail a run; ``review`` findings are the rules the spec
marks as needing a human eye (an inference, or a keyword that is only a
hint), and are reported but never fail it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, replace

SCHEMA = 2

LEVELS = ("context", "container", "component")
DIAGRAM_TYPES = {
    "context": "System Context",
    "container": "Container",
    "component": "Component",
}
ELEMENT_TYPES = ("Person", "Software System", "Container", "Component")
BOUNDARY_TYPES = ("Software System", "Container", "Group")
EDGE_KINDS = ("default", "accent", "link")
STATUSES = ("", "optional", "retired")

# Acronyms explained in every key without the spec having to spell them out.
# Anything else in upper case must be expanded in the spec's ``acronyms``.
COMMON_ACRONYMS = {
    "AI": "Artificial Intelligence",
    "AKS": "Azure Kubernetes Service",
    "AMQP": "Advanced Message Queuing Protocol",
    "API": "Application Programming Interface",
    "ASGI": "Asynchronous Server Gateway Interface",
    "AWS": "Amazon Web Services",
    "CDN": "Content Delivery Network",
    "CLI": "Command-Line Interface",
    "CRUD": "Create, Read, Update, Delete",
    "CSV": "Comma-Separated Values",
    "DNS": "Domain Name System",
    "ETL": "Extract, Transform, Load",
    "GCP": "Google Cloud Platform",
    "GPT": "Generative Pre-trained Transformer",
    "HTML": "HyperText Markup Language",
    "HTTP": "Hypertext Transfer Protocol",
    "HTTPS": "Hypertext Transfer Protocol Secure",
    "ID": "Identifier",
    "IP": "Internet Protocol",
    "JSON": "JavaScript Object Notation",
    "JWT": "JSON Web Token",
    "LLM": "Large Language Model",
    "MCP": "Model Context Protocol",
    "MQTT": "MQ Telemetry Transport",
    "OCR": "Optical Character Recognition",
    "OIDC": "OpenID Connect",
    "ORM": "Object-Relational Mapping",
    "PDF": "Portable Document Format",
    "RAG": "Retrieval-Augmented Generation",
    "REST": "Representational State Transfer",
    "RPC": "Remote Procedure Call",
    "SAML": "Security Assertion Markup Language",
    "SDK": "Software Development Kit",
    "SFTP": "SSH File Transfer Protocol",
    "SMTP": "Simple Mail Transfer Protocol",
    "SPA": "Single-Page Application",
    "SQL": "Structured Query Language",
    "SSE": "Server-Sent Events",
    "SSH": "Secure Shell",
    "SSO": "Single Sign-On",
    "TCP": "Transmission Control Protocol",
    "TLS": "Transport Layer Security",
    "UI": "User Interface",
    "URL": "Uniform Resource Locator",
    "UUID": "Universally Unique Identifier",
    "VM": "Virtual Machine",
    "WSGI": "Web Server Gateway Interface",
    "XML": "Extensible Markup Language",
    "YAML": "YAML Ain't Markup Language",
}

ACRONYM_RE = re.compile(r"\b[A-Z]{2,}\b")
TYPE_LINE_RE = re.compile(r"^\[(Person|Software System|Container|Component)(?::\s*(.+))?\]$")

# A relationship label reads source -> label -> target, so it ends on the
# word that binds the target ("Makes API requests to", "Reads from").
PREPOSITIONS = {
    "about", "across", "against", "at", "by", "for", "from", "in", "into",
    "of", "on", "onto", "over", "through", "to", "toward", "towards",
    "using", "via", "with",
}
VAGUE_LABEL_RE = re.compile(r"^(uses|calls|data|connects|talks to|depends on|links to)$", re.I)

GENERIC_WORDS = {
    "a", "all", "an", "and", "business", "code", "common", "contains", "core",
    "does", "everything", "functionality", "general", "handles", "helper",
    "helpers", "logic", "main", "misc", "miscellaneous", "module", "of",
    "other", "service", "shared", "stuff", "the", "things", "util",
    "utilities", "utility", "utils", "various",
}

# A shared library is not a container (it is not a runtime construct) and a
# message bus is not one either; these words on a container are an error.
NOT_A_CONTAINER_RE = re.compile(
    r"\b(library|libraries|lib|jar|dll|assembly|sdk|package|message bus|event bus)\b", re.I
)
# A container's technology lists what it is built with, and that routinely
# includes SDKs and packages ("Python 3.12, azure-eventhub SDK"). Only a
# technology that names the element itself as a library artefact marks it as
# not a container; SDKs and packages it uses do not.
NOT_A_CONTAINER_TECH_RE = re.compile(r"^\s*(a\s+)?(shared\s+)?(library|jar|dll|assembly|message bus|event bus)\b", re.I)
# These are only a hint: a component named after a folder or namespace is
# usually an organisational unit, not a component.
REVIEW_CONTAINER_RE = re.compile(r"\b(module|namespace)\b", re.I)
REVIEW_COMPONENT_RE = re.compile(r"\b(folder|directory|namespace|package|library|lib|utils?|helpers?)\b", re.I)

MAX_NAME = 40
MAX_DESCRIPTION = 120
MAX_TECHNOLOGY = 48
MAX_LABEL = 56
MAX_EDGE_TECHNOLOGY = 32


@dataclass
class Finding:
    rule: str
    message: str
    severity: str = "error"  # "error" fails the run, "review" is reported only

    def __str__(self) -> str:
        tag = "" if self.severity == "error" else " (review)"
        return f"{self.rule}{tag} {self.message}"


@dataclass
class Element:
    id: str
    name: str
    type: str
    technology: str = ""
    description: str = ""
    external: bool = False
    store: bool = False
    focus: bool = False
    status: str = ""
    icon: str = ""
    href: str = ""
    width: int | None = None
    type_line: str = ""  # as drawn; derived when built from a spec

    def __post_init__(self) -> None:
        if not self.type_line:
            self.type_line = type_line(self.type, self.technology)


@dataclass
class Relationship:
    src: str
    dst: str
    label: str
    technology: str = ""
    kind: str = "default"
    dashed: bool = False


@dataclass
class Boundary:
    name: str
    type: str
    members: list[str]
    security: bool = False
    label_align: str = "left"


@dataclass
class Model:
    level: str
    elements: dict[str, Element]
    relationships: list[Relationship]
    boundaries: list[Boundary]
    acronyms: dict[str, str] = field(default_factory=dict)  # every one the key may explain
    title: str = ""
    subtitle: str = ""
    desc: str = ""
    path: str = ""


class SpecError(Exception):
    """A spec the renderer cannot build a model from; carries every finding."""

    def __init__(self, findings: list[Finding]) -> None:
        super().__init__("; ".join(str(f) for f in findings))
        self.findings = findings


# --------------------------------------------------------------------------
# labels
# --------------------------------------------------------------------------


def type_line(kind: str, technology: str) -> str:
    """``[Container: Python 3.12, FastAPI]``, or ``[Person]`` with no technology."""
    return f"[{kind}: {technology}]" if technology else f"[{kind}]"


def boundary_label(b: Boundary) -> str:
    return f"{b.name} [{b.type}]" if b.type != "Group" else b.name


def treatment(e: Element, level: str, in_scope: str | None) -> str:
    """The Insight treatment an element takes, derived from what it is.

    Derived, never chosen, so one kind of element looks the same on every
    diagram (X2) and the key's wording is always true.
    """
    if e.status:
        return e.status
    if e.focus or (level == "context" and e.id == in_scope):
        return "focal"
    if e.type == "Person":
        return "input"
    if e.external:
        return "external"
    if e.type == "Container" and e.store:
        return "store"
    return "backend"


def element_class(e: Element) -> str:
    """The plain-words class the key uses for an element."""
    if e.type == "Person":
        return "Person"
    if e.type == "Software System":
        return "External software system" if e.external else "Software system"
    if e.type == "Container":
        what = "data store" if e.store else "application"
        return f"{'External container' if e.external else 'Container'} ({what})"
    return "Component"


def derive_title(m: Model) -> str:
    """``<Diagram type> diagram for <scope>``, the form the C4 notation recommends."""
    scope = scope_name(m)
    return f"{DIAGRAM_TYPES[m.level]} diagram for {scope}" if scope else ""


def scope_name(m: Model) -> str:
    if m.level == "context":
        inside = [e for e in m.elements.values() if e.type == "Software System" and not e.external]
        return inside[0].name if len(inside) == 1 else ""
    systems = [b for b in m.boundaries if b.type == "Software System"]
    if m.level == "container":
        return systems[0].name if len(systems) == 1 else ""
    containers = [b for b in m.boundaries if b.type == "Container"]
    if len(systems) == 1 and len(containers) == 1:
        return f"{systems[0].name} - {containers[0].name}"
    return ""


def in_scope_system(m: Model) -> str | None:
    if m.level != "context":
        return None
    inside = [e.id for e in m.elements.values() if e.type == "Software System" and not e.external]
    return inside[0] if len(inside) == 1 else None


def visible_text(m: Model) -> list[str]:
    """Every string a reader sees on the diagram, for the acronym check."""
    out = [m.title, m.subtitle]
    for e in m.elements.values():
        out += [e.name, e.type_line, e.description]
    for r in m.relationships:
        out += [r.label, r.technology]
    out += [boundary_label(b) for b in m.boundaries]
    return [s for s in out if s]


def acronyms_used(m: Model) -> list[str]:
    found: dict[str, None] = {}
    for s in visible_text(m):
        for tok in ACRONYM_RE.findall(s):
            found[tok] = None
    return sorted(found)


# --------------------------------------------------------------------------
# spec -> model
# --------------------------------------------------------------------------

TOP_KEYS = {
    "schema", "level", "subtitle", "desc", "eyebrow", "preset", "rows", "nodes",
    "boundaries", "edges", "acronyms", "slug",
}
NODE_KEYS = {
    "name", "type", "technology", "description", "external", "store", "focus",
    "status", "icon", "href", "width",
}
EDGE_KEYS = {"from", "to", "label", "technology", "kind", "dashed"}
BOUNDARY_KEYS = {"name", "type", "members", "security", "labelAlign"}


def _str(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def model_from_spec(spec: dict) -> Model:
    """Validate a schema 2 spec's shape and build the model. Raises SpecError."""
    bad: list[Finding] = []
    if spec.get("schema") != SCHEMA:
        raise SpecError([Finding(
            "spec",
            f"schema {spec.get('schema', 1)!r} is not supported: this renderer reads schema {SCHEMA}, "
            "which states every element's type, technology and description. Upgrade the spec per "
            "insight-diagrams.md#upgrading-a-schema-1-spec",
        )])
    for key in sorted(set(spec) - TOP_KEYS):
        hint = " (the title is derived from the level and the scope)" if key == "title" else ""
        hint = " (use boundaries)" if key == "zones" else hint
        bad.append(Finding("spec", f"unknown top-level key {key!r}{hint}"))
    level = spec.get("level")
    if level not in LEVELS:
        bad.append(Finding("T2", f"level {level!r} is not one of {', '.join(LEVELS)}"))
        level = "context"

    elements: dict[str, Element] = {}
    for nid, n in (spec.get("nodes") or {}).items():
        if not isinstance(n, dict):
            bad.append(Finding("spec", f"node {nid!r} is not an object"))
            continue
        for key in sorted(set(n) - NODE_KEYS):
            hint = {
                "kind": " (the treatment is derived from type, external, store, focus and status)",
                "sublabel": " (use technology)",
                "tag": " (the bracketed type line replaces the tag)",
            }.get(key, "")
            bad.append(Finding("spec", f"node {nid!r}: unknown key {key!r}{hint}"))
        status = _str(n.get("status"))
        if status not in STATUSES:
            bad.append(Finding("spec", f"node {nid!r}: status {status!r} is not optional or retired"))
            status = ""
        width = n.get("width")
        elements[nid] = Element(
            id=nid,
            name=_str(n.get("name")),
            type=_str(n.get("type")),
            technology=_str(n.get("technology")),
            description=_str(n.get("description")),
            external=bool(n.get("external", False)),
            store=bool(n.get("store", False)),
            focus=bool(n.get("focus", False)),
            status=status,
            icon=_str(n.get("icon")),
            href=_str(n.get("href")),
            width=int(width) if isinstance(width, int) else None,
        )

    rels: list[Relationship] = []
    for k, e in enumerate(spec.get("edges") or []):
        for key in sorted(set(e) - EDGE_KEYS):
            bad.append(Finding("spec", f"edge {k}: unknown key {key!r}"))
        src, dst = _str(e.get("from")), _str(e.get("to"))
        if src not in elements or dst not in elements:
            bad.append(Finding("spec", f"edge {src}->{dst} names an unknown node"))
            continue
        kind = _str(e.get("kind")) or "default"
        if kind not in EDGE_KINDS:
            bad.append(Finding("spec", f"edge {src}->{dst}: kind {kind!r} is not one of {', '.join(EDGE_KINDS)}"))
            kind = "default"
        rels.append(Relationship(
            src=src, dst=dst, label=_str(e.get("label")), technology=_str(e.get("technology")),
            kind=kind, dashed=bool(e.get("dashed", False)),
        ))

    bounds: list[Boundary] = []
    for b in spec.get("boundaries") or []:
        for key in sorted(set(b) - BOUNDARY_KEYS):
            bad.append(Finding("spec", f"boundary {b.get('name')!r}: unknown key {key!r}"))
        members = [m for m in b.get("members", []) if isinstance(m, str)]
        for m in members:
            if m not in elements:
                bad.append(Finding("spec", f"boundary {b.get('name')!r} names unknown node {m!r}"))
        bounds.append(Boundary(
            name=_str(b.get("name")), type=_str(b.get("type")),
            members=[m for m in members if m in elements],
            security=bool(b.get("security", False)), label_align=_str(b.get("labelAlign")) or "left",
        ))

    acronyms = dict(COMMON_ACRONYMS)
    for k, v in (spec.get("acronyms") or {}).items():
        if isinstance(v, str) and v.strip():
            acronyms[k] = v.strip()
        else:
            bad.append(Finding("K8", f"acronym {k!r} has no expansion"))
    if not _str(spec.get("desc")):
        bad.append(Finding("spec", "desc is required: one sentence a screen reader reads out"))
    if bad:
        raise SpecError(bad)
    m = Model(
        level=level, elements=elements, relationships=rels, boundaries=bounds,
        acronyms=acronyms, subtitle=_str(spec.get("subtitle")), desc=_str(spec.get("desc")),
    )
    m.title = derive_title(m)
    return m


# --------------------------------------------------------------------------
# checks on one diagram
# --------------------------------------------------------------------------


def check_model(m: Model) -> list[Finding]:
    """Every rule from the lint table that the model can answer."""
    out: list[Finding] = []
    out += _check_title(m)
    out += _check_elements(m)
    out += _check_relationships(m)
    out += _check_boundaries(m)
    out += _check_scope(m)
    out += _check_acronyms(m)
    return out


def _check_title(m: Model) -> list[Finding]:
    if not m.title:
        return [Finding("T1", "the diagram has no title; its scope element is missing (see the S findings)")]
    out = []
    if not re.match(r"^(System Context|System Landscape|Container|Component|Code|Dynamic|Deployment) diagram for \S", m.title):
        out.append(Finding("T2", f"title {m.title!r} does not read '<Diagram type> diagram for <scope>'"))
    expected = derive_title(m)
    if expected and m.title != expected:
        out.append(Finding("T3", f"title {m.title!r} does not name the scope; expected {expected!r}"))
    return out


def _check_element_text(e: Element) -> list[Finding]:
    out: list[Finding] = []
    who = f"element {e.id!r}"
    if not e.name:
        out.append(Finding("N1", f"{who} has no name"))
    elif len(e.name) > MAX_NAME:
        out.append(Finding("N1", f"{who}: name is over {MAX_NAME} characters; shorten it"))
    match = TYPE_LINE_RE.match(e.type_line)
    if e.type not in ELEMENT_TYPES or not match or match.group(1) != e.type:
        what = "is drawn by UML or an entity relationship diagram, not here" if e.type == "Code" else \
            f"must be one of {', '.join(ELEMENT_TYPES)}"
        out.append(Finding("N2", f"{who}: type {e.type!r} {what}"))
        return out
    tech = match.group(2) or ""
    if e.type in ("Container", "Component") and not tech:
        out.append(Finding("N3", f"{who}: a {e.type} states its technology, e.g. [{e.type}: Python 3.12, FastAPI]"))
    if e.type in ("Person", "Software System") and tech:
        out.append(Finding("N5", f"{who}: a {e.type} carries no technology; drop {tech!r}"))
    if len(tech) > MAX_TECHNOLOGY:
        out.append(Finding("N3", f"{who}: technology is over {MAX_TECHNOLOGY} characters"))
    words = re.findall(r"[A-Za-z0-9][\w'/-]*", e.description)
    if len(words) < 3:
        out.append(Finding("N4", f"{who}: needs a description of three words or more saying what it does"))
    elif not e.description.endswith("."):
        out.append(Finding("N4", f"{who}: the description is one sentence ending in a full stop"))
    elif len(e.description) > MAX_DESCRIPTION:
        out.append(Finding("N4", f"{who}: description is over {MAX_DESCRIPTION} characters; keep it at a glance"))
    if words and {w.lower() for w in words} <= GENERIC_WORDS:
        out.append(Finding("N6", f"{who}: description {e.description!r} is generic; name the responsibility"))
    elif "business logic" in e.description.lower():
        out.append(Finding("N6", f"{who}: 'business logic' is a generic term; say which logic", "review"))
    return out


def _check_elements(m: Model) -> list[Finding]:
    out: list[Finding] = []
    focus = [e.id for e in m.elements.values() if e.focus and not (m.level == "context" and e.type == "Software System")]
    if len(focus) > 1:
        out.append(Finding("spec", f"{len(focus)} elements have focus ({', '.join(focus)}); a diagram is about one"))
    for e in m.elements.values():
        out += _check_element_text(e)
        who = f"element {e.id!r}"
        hay = f"{e.name} {e.technology}"
        bad = NOT_A_CONTAINER_RE.search(e.name) or NOT_A_CONTAINER_TECH_RE.search(e.technology)
        if e.type == "Container" and bad:
            out.append(Finding(
                "N7", f"{who}: {bad.group(0).strip()!r} is not a container. A shared "
                "library is code inside the containers that use it; a message bus is infrastructure "
                "(model its queues or topics as containers, or name them on the relationship)",
            ))
        elif e.type == "Container" and REVIEW_CONTAINER_RE.search(hay):
            out.append(Finding("N7", f"{who}: a container is an application or data store, not a module", "review"))
        if e.type == "Component" and REVIEW_COMPONENT_RE.search(e.name):
            out.append(Finding("N7", f"{who}: a component is functionality behind an interface, not a folder or package", "review"))
        if e.store and e.type != "Container":
            out.append(Finding("N2", f"{who}: only a Container is a data store"))
        if e.type == "Person" and e.external:
            out.append(Finding("N2", f"{who}: external applies to software systems, not people"))
        if e.external and e.type in ("Container", "Component"):
            out.append(Finding(
                "S7", f"{who}: an external element is drawn as a software system; you cannot see inside what you do not own",
                "review",
            ))
    return out


def _needs_technology(level: str, a: Element, b: Element) -> bool:
    if level == "context" or "Person" in (a.type, b.type):
        return False
    types = {a.type, b.type}
    if "Container" in types:
        return True
    return "Component" in types and types != {"Component"}


def _check_relationships(m: Model) -> list[Finding]:
    out: list[Finding] = []
    for r in m.relationships:
        a, b = m.elements[r.src], m.elements[r.dst]
        who = f"relationship {r.src}->{r.dst}"
        label = r.label
        if r.src == r.dst:
            out.append(Finding("L4", f"{who} starts and ends on the same element"))
        if not label:
            out.append(Finding("L1", f"{who} has no label; say what the source does to the target"))
            continue
        words = label.split()
        if len(words) < 2 or VAGUE_LABEL_RE.match(label):
            out.append(Finding("L2", f"{who}: {label!r} is too vague; use a specific verb phrase, e.g. 'Reads orders from'"))
        if words[-1].lower().strip(".,") not in PREPOSITIONS:
            out.append(Finding(
                "L3", f"{who}: {label!r} must read source-label-target and end on the word that binds the target "
                "(to, from, using, with, into, ...), e.g. 'Sends e-mails to'",
            ))
        if label[0].islower() or label == label.upper():
            out.append(Finding("L3", f"{who}: {label!r} is a sentence-case verb phrase, e.g. 'Makes API requests to'"))
        if len(label) > MAX_LABEL:
            out.append(Finding("L2", f"{who}: label is over {MAX_LABEL} characters; put the detail in the .md"))
        tech = r.technology
        if "[" in tech or "]" in tech:
            out.append(Finding("L5", f"{who}: write the technology without brackets; the renderer adds them"))
        if len(tech) > MAX_EDGE_TECHNOLOGY:
            out.append(Finding("L5", f"{who}: technology is over {MAX_EDGE_TECHNOLOGY} characters"))
        if _needs_technology(m.level, a, b) and not tech:
            out.append(Finding("L5", f"{who}: a relationship with a container or across a container boundary names its technology or protocol, e.g. JSON/HTTPS"))
        if tech and m.level == "context":
            out.append(Finding("L6", f"{who}: a system context diagram shows no technology; drop {tech!r}"))
        elif tech and "Person" in (a.type, b.type):
            out.append(Finding("L6", f"{who}: a relationship with a person carries no technology; drop {tech!r}"))
        if r.kind == "link" and not (a.external or b.external):
            out.append(Finding("K2", f"{who}: kind 'link' means 'with an external system', and neither end is external"))
    return out


def _check_boundaries(m: Model) -> list[Finding]:
    out: list[Finding] = []
    if len(m.boundaries) > 3:
        out.append(Finding("spec", f"{len(m.boundaries)} boundaries; the ceiling is 3"))
    for b in m.boundaries:
        if not b.name:
            out.append(Finding("N1", "a boundary has no name"))
        if b.type not in BOUNDARY_TYPES:
            out.append(Finding("N2", f"boundary {b.name!r}: type {b.type!r} is not one of {', '.join(BOUNDARY_TYPES)}"))
        if not b.members:
            out.append(Finding("spec", f"boundary {b.name!r} has no members"))
    sets = [(b, set(b.members)) for b in m.boundaries]
    for i, (b1, s1) in enumerate(sets):
        for b2, s2 in sets[i + 1:]:
            if s1 & s2 and not (s1 <= s2 or s2 <= s1):
                out.append(Finding("S7", f"boundaries {b1.name!r} and {b2.name!r} overlap without nesting"))
    return out


def _connected(m: Model, nid: str, to: set[str]) -> bool:
    return any(
        (r.src == nid and r.dst in to) or (r.dst == nid and r.src in to) for r in m.relationships
    )


def _check_scope(m: Model) -> list[Finding]:
    return {"context": _scope_context, "container": _scope_container, "component": _scope_component}[m.level](m)


def _scope_context(m: Model) -> list[Finding]:
    out: list[Finding] = []
    inside = [e for e in m.elements.values() if e.type == "Software System" and not e.external]
    if len(inside) != 1:
        out.append(Finding(
            "S1", f"a system context diagram has exactly one software system in scope (not external); found {len(inside)}",
        ))
    for e in m.elements.values():
        if e.type in ("Container", "Component"):
            out.append(Finding("S7", f"element {e.id!r}: a {e.type} does not belong on a system context diagram"))
        if e.focus and inside and e.id != inside[0].id:
            out.append(Finding("S1", f"element {e.id!r}: the focus of a context diagram is the system in scope"))
    for b in m.boundaries:
        if b.type != "Group":
            out.append(Finding("S1", f"boundary {b.name!r}: a system context diagram draws no {b.type} boundary"))
    if len(inside) == 1:
        scope = {inside[0].id}
        for e in m.elements.values():
            if e.id not in scope and not _connected(m, e.id, scope):
                out.append(Finding("S1", f"element {e.id!r} has no relationship with the system in scope"))
    return out


def _scope_container(m: Model) -> list[Finding]:
    out: list[Finding] = []
    systems = [b for b in m.boundaries if b.type == "Software System"]
    if len(systems) != 1:
        out.append(Finding("S3", f"a container diagram has exactly one software system boundary; found {len(systems)}"))
    for b in m.boundaries:
        if b.type == "Container":
            out.append(Finding("S3", f"boundary {b.name!r}: a container diagram draws no container boundary"))
    inside = set(systems[0].members) if len(systems) == 1 else set()
    containers = {e.id for e in m.elements.values() if e.type == "Container"}
    for e in m.elements.values():
        if e.type == "Component":
            out.append(Finding("S7", f"element {e.id!r}: a Component does not belong on a container diagram"))
        elif e.type == "Container" and systems and e.id not in inside:
            out.append(Finding("S3", f"element {e.id!r}: every container sits inside the software system boundary"))
        elif e.id in inside and (e.type != "Container" or e.external):
            out.append(Finding("S3", f"element {e.id!r}: only the system's own containers sit inside its boundary"))
        elif e.type in ("Person", "Software System") and containers and not _connected(m, e.id, containers):
            out.append(Finding("S3", f"element {e.id!r} has no relationship with any container"))
    return out


def _scope_component(m: Model) -> list[Finding]:
    out: list[Finding] = []
    systems = [b for b in m.boundaries if b.type == "Software System"]
    holders = [b for b in m.boundaries if b.type == "Container"]
    if len(holders) != 1:
        out.append(Finding("S4", f"a component diagram has exactly one container boundary; found {len(holders)}"))
    if len(systems) != 1:
        out.append(Finding("S4", f"a component diagram draws the container inside one software system boundary; found {len(systems)}"))
    in_c = set(holders[0].members) if len(holders) == 1 else set()
    in_s = set(systems[0].members) if len(systems) == 1 else set()
    if in_c and in_s and not in_c <= in_s:
        out.append(Finding("S4", "the container boundary sits inside the software system boundary; add its members to the system's"))
    components = {e.id for e in m.elements.values() if e.type == "Component"}
    for e in m.elements.values():
        if e.type == "Component" and holders and e.id not in in_c:
            out.append(Finding("S4", f"element {e.id!r}: every component sits inside the container boundary"))
        elif e.id in in_c and e.type != "Component":
            out.append(Finding("S4", f"element {e.id!r}: only the container's components sit inside its boundary"))
        elif e.type == "Container" and systems and e.id not in in_s:
            out.append(Finding("S4", f"element {e.id!r}: a sibling container sits inside the software system boundary"))
        elif e.id in in_s - in_c and (e.type != "Container" or e.external):
            out.append(Finding("S4", f"element {e.id!r}: only the system's containers sit inside its boundary"))
        elif e.type in ("Person", "Software System", "Container") and components and not _connected(m, e.id, components):
            out.append(Finding("S4", f"element {e.id!r} has no relationship with any component"))
    return out


def _check_acronyms(m: Model) -> list[Finding]:
    missing = [a for a in acronyms_used(m) if a not in m.acronyms]
    if not missing:
        return []
    return [Finding(
        "K8", f"acronym{'s' if len(missing) > 1 else ''} {', '.join(missing)} not explained; add "
        f"{'them' if len(missing) > 1 else 'it'} to the spec's \"acronyms\" map or spell the words out",
    )]


# --------------------------------------------------------------------------
# checks across a set of diagrams (one system's codemap)
# --------------------------------------------------------------------------


def check_set(models: list[Model]) -> list[tuple[str, Finding]]:
    """X1-X3: one element and one relationship read the same on every diagram."""
    out: list[tuple[str, Finding]] = []
    seen: dict[str, tuple[str, str, str, str]] = {}  # name -> (type line, desc, treatment, path)
    rels: dict[tuple[str, str], tuple[str, str, str]] = {}  # (src, dst) -> (label, tech, path)
    for m in models:
        for e in m.elements.values():
            # focus is per diagram by design; compare what the element is
            plain = treatment(replace(e, focus=False), m.level, None)
            if e.name not in seen:
                seen[e.name] = (e.type_line, e.description, plain, m.path)
                continue
            line, desc, prev, where = seen[e.name]
            if (e.type_line, e.description) != (line, desc):
                out.append((m.path, Finding(
                    "X1", f"{e.name!r} reads {e.type_line} {e.description!r} here and {line} {desc!r} in {where}",
                )))
            elif plain != prev:
                out.append((m.path, Finding("X2", f"{e.name!r} is drawn as {plain} here and {prev} in {where}")))
        for r in m.relationships:
            key = (m.elements[r.src].name, m.elements[r.dst].name)
            tech = "" if m.level == "context" else r.technology
            if key not in rels:
                rels[key] = (r.label, tech, m.path)
                continue
            label, prev_tech, where = rels[key]
            if r.label != label or (tech and prev_tech and tech != prev_tech):
                out.append((m.path, Finding(
                    "X3", f"{key[0]} -> {key[1]} reads {r.label!r} [{tech}] here and {label!r} [{prev_tech}] in {where}",
                )))
            elif tech and not prev_tech:
                rels[key] = (label, tech, m.path)
    return out
