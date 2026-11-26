# Insight C4 Diagrams Reference

Every diagram in a `codemap/` is a C4 diagram drawn in the Insight
Enterprises design system, from a JSON spec, by the renderer bundled with
this skill. This file is the contract: what each C4 element means and how it
is labelled, what the spec accepts, how a rendered diagram is checked, and
what the renderer guarantees so you do not have to check it.

Read `#c4-semantics` before you model anything, `#spec-schema` before you
write a spec, and `#lint-rules` before you verify one. The rest is
reference.

The C4 rules here come from c4model.com. The site states its notation rules
as recommendations ("should") and shows a house style in its official
examples; this skill makes both mandatory, so a diagram that breaks either is
not drawn. Where the site only implies something, this file says so and the
point is guidance, checked by eye (`review` in the lint output), never a
failure.

---

## C4 semantics

### Element types

| Type | What it is | Technology on its label? |
| ---- | ---------- | ------------------------ |
| `Person` | A user, actor, role or persona who uses the software systems. | No: `[Person]` |
| `Software System` | The highest level: something that delivers value to its users. The system in scope is the one a single team builds, owns and can see inside. Product domains, bounded contexts, business capabilities, feature teams, tribes and squads are not software systems. | No: `[Software System]` |
| `Container` | An application or a data store: something that must be running for the system to work, a runtime boundary around code being executed or data being stored. | Yes: `[Container: Python 3.12, FastAPI]` |
| `Component` | A grouping of related functionality behind a well-defined interface, inside one container. Not separately deployable: all components of a container run in the same process. | Yes: `[Component: FastAPI router]` |
| Code | Classes, interfaces, functions, tables inside a component. | Not drawn here; C4 uses UML class diagrams or ERDs for this level. |

The hierarchy is strict containment: software system > container >
component > code. A person sits outside it.

### What is and is not a container

A container is one of: a server-side web application, a client-side web
application (JavaScript in a browser), a desktop or mobile app, a console
application or batch process, a single serverless function, a database
schema, a blob or content store (a bucket, a CDN), a file system or a
portion of one, a single shell script.

- **Data stores are containers.** A database schema, a bucket, a folder on a
  file system. Set `"store": true`.
- **A hosted data service you own is your container**, not an external
  system: a cloud bucket or schema you control is part of your architecture
  although someone else hosts it.
- **Queues and topics are containers** (a queue is essentially a data store),
  or are named on the relationship ("via" notation) instead.
- **A web application and its substantial single-page app are two
  containers**: two process spaces talking over JSON/HTTPS. A server that
  renders mostly static HTML is one.
- **Several web apps in one server process are one container each**;
  deployment is a separate concern.
- Microservices one team owns are each one or more containers (an API plus
  its schema). A microservice owned by a separate team is a software system.

Not containers:

- **A shared library, package, JAR, assembly, DLL, SDK or module.** These
  organise code inside the containers that use them; they are not runtime
  constructs. Do not draw one. Its code belongs to the components that use
  it. To document a library itself, C4 suggests UML.
- **A message bus.** Model the queues and topics as containers, or name them
  on the relationships; a hub-and-spoke bus hides the real coupling between
  producers and consumers.
- **A Docker container.** "Container" in C4 means application or data store,
  whatever runs it.

A package, namespace or folder is typically not a component either:
components describe how functionality is partitioned, not how code is filed.
Domain model classes and utility classes are left off a component diagram.

### Internal and external

The system in scope is the one your team owns. Everything else is
`"external": true`: a system you neither own nor can see inside. Ownership
decides, not hosting. *Guidance (an inference, not stated by C4):* an
external element is drawn as a software system or a person, never as a
container or component, because you cannot see inside what you do not own;
the renderer reports an external container as `review`, not as a failure.

### Boundaries

A boundary is a box round the elements it holds, labelled with its name and
type and no technology: `Recipe Planner [Software System]`,
`Planner API [Container]`. A container diagram draws one software system
boundary with every container inside it. A component diagram draws the
container boundary nested inside its software system boundary, with the
system's other containers inside the system boundary but outside the
container boundary. A `Group` boundary is an optional grouping box (say,
one per microservice pair) and a `"security": true` group is a trust
boundary; both are explained in the key.

### Element labels

Every element shows, top to bottom:

```text
Planner API                          name, bold
[Container: Python 3.12, FastAPI]    type and technology, in brackets
Serves recipes and meal plans.       description: one sentence, full stop
```

- The type is a word, always: `[Person]`, `[Software System]`,
  `[Container: ...]`, `[Component: ...]`. Shape alone never states it.
- Every container and component states its technology: language and
  framework, or the store and what it is (`PostgreSQL 16 database schema`,
  `Amazon S3 bucket`, `Directory`). It names the runtime, not the host.
- A person and a software system state no technology.
- The description is a short sentence of at least three words, ending in a
  full stop, saying what the element does or, for a data store, what it
  holds. Generic terms ("business logic", "core", "helpers") say nothing.
- An element keeps the same name, type line and description on every
  diagram it appears on.

### Relationship labels

- Every line is **one way** and carries a label. A two-way conversation is
  either one line labelled for the dominant direction ("Reads from and
  writes to") or, as guidance, two lines with a label each.
- The label is a **sentence-case verb phrase that reads source, label,
  target** and ends on the word that binds the target: "Makes API requests
  to", "Reads from and writes to", "Sends e-mails using". Never a single
  word ("Uses"), never a noun ("customer events"), never upper case.
- **Every relationship with a container, or that crosses a container
  boundary, names its technology or protocol**, drawn in brackets under the
  label: `[JSON/HTTPS]`, `[SQL/TLS]`, `[AMQP]`. Write it in `technology`
  without brackets.
- A system context diagram shows no technology on any line, and a line to
  or from a person carries none.
- Two components inside one container talk in-process; their line may omit
  the technology.
- The same pair of elements carries the same label and technology on every
  diagram it appears on.

### Titles

Every diagram's title is `<Diagram type> diagram for <scope>`, the form the
C4 notation recommends, and the renderer derives it so it cannot drift:

| Level | Title |
| ----- | ----- |
| `context` | `System Context diagram for <the system in scope>` |
| `container` | `Container diagram for <the software system boundary>` |
| `component` | `Component diagram for <system boundary> - <container boundary>` |

The title is drawn inside the SVG, so the PNG a document embeds carries it.
`subtitle` adds one descriptive line under it.

### The key

Every diagram has a key, generated from what the diagram uses and nothing
else: the box shape and how to read its label, every element treatment
(fill, border colour, border style and width), every boundary, every line
colour and style with its arrowhead, how to read a line label, every icon,
the note that box size carries no meaning, and every acronym on the page with
its expansion. Common acronyms (API, HTTPS, JSON, SQL, ...) are expanded by
the renderer; any other upper-case word must be expanded in the spec's
`acronyms` map, or the diagram is not drawn.

---

## Diagram types and files

| File | `level` | C4 diagram | Scope | Holds |
| ---- | ------- | ---------- | ----- | ----- |
| `<system>/context.c4.json` | `context` | System Context | the system | the system in scope, the people who use it, the external systems it talks to |
| `<system>/containers.c4.json` | `container` | Container | the system | its containers inside the system boundary, the people and external systems connected to them |
| `<system>/containers/<id>/container.c4.json` | `component` | Component | one container | its components inside the container boundary, the sibling containers and the people and external systems connected to them |
| `.../components/<id>/component.c4.json` | `component` | Component (focused) | the same container | one component as the `focus`, with only its direct relationships; `subtitle` names the focus |

Scope rules the renderer enforces:

- **Context:** exactly one software system that is not external, which is
  the focus; everything else is a person or an external software system,
  each with a relationship to the system in scope. No containers, no
  components, no system or container boundary.
- **Container:** exactly one software system boundary; every container is
  inside it and nothing else is; everything outside is a person or software
  system with a relationship to a container. No components.
- **Component:** exactly one container boundary inside exactly one software
  system boundary; every component inside the container boundary and only
  components; sibling containers inside the system boundary only; people
  and software systems outside, each with a relationship to a component.

Diagrams this skill does not produce: system landscape, dynamic, deployment
and code. Their rules (S2, S5, S6, L7) do not apply.

---

## Why a spec and not hand-drawn SVG

The `insight-diagram-design` skill is the source of the visual language, and it
says plainly: *"For anything beyond a handful of nodes, do not hand-type the
SVG. Write a short Python generator ... Rebuilding after a fix then takes one
command, two figures in the same document share exact geometry, and the checks
can run on every iteration."*

A codemap is twenty-odd figures that must share exact geometry and be
regenerated whenever the code moves, so the generator is the only workable
form. `assets/insight-c4/render.py` **is** that generator, with the C4 rules
in `rules.py`, the tokens in `tokens.py` and the band layout and orthogonal
router in `layout.py`. You write the model; it owns the drawing and the
labels.

**Never hand-edit a generated `.html`, `.svg` or `.png`.** Edit the spec and
re-run. A hand edit is lost on the next run, and `lint.py` reports it.

---

## Running it

```bash
R="${CLAUDE_PLUGIN_ROOT}/skills/c4/assets/insight-c4"

python3 "$R/render.py" codemap/<system>/context.c4.json --png   # one diagram
python3 "$R/render.py" 'codemap/**/*.c4.json' --png             # the whole model
python3 "$R/render.py" 'codemap/**/*.c4.json' --check           # checks only, writes nothing
python3 "$R/lint.py" 'codemap/**/*.svg'                          # re-check what was drawn
python3 "$R/lint.py" 'codemap/**/*.svg' --json                   # the same, as JSON
```

| Flag | Effect |
| ---- | ------ |
| *(none)* | writes `<name>.html` (the Insight page) and `<name>.svg` beside the spec |
| `--png` | also rasterises; Playwright if the repo has it (real Inter), else `rsvg-convert` or `magick` (Arial fallback) |
| `--scale N` | PNG scale: 2 for documents and screens, 3 for print |
| `--no-svg` | skip the standalone SVG |
| `--icons DIR` | icon pack directory; auto-discovered from the `insight-diagram-design` skill otherwise |
| `--check` | run every check and exit non-zero on a failure, writing nothing |

It is pure standard library. Only `--png` shells out.

The renderer prints one status per spec:

- `FAIL (C4 rules)`: the spec breaks a rule in `#lint-rules` or is
  malformed (`spec`); each finding is listed with its rule id and nothing
  is drawn for that spec. The run continues with the next spec.
- `FAIL (layout)`: the diagram is drawn but a reader would misread it: a
  connector behind a node it does not terminate on, a label on a node or off
  the canvas, text through a box edge, or a boundary drawn round a node that
  is not its member. Fix the rows.
- `FAIL (across diagrams)`: X1 to X3, comparing every diagram of one
  `codemap/<system>/` in the run.
- `ok`: possibly with `review` findings (judgment calls) and warnings: more
  than 16 nodes or 24 edges, more than two accent elements, a coordinate off
  the 4px grid, an Azure service with no official icon.

The exit code is non-zero on any `FAIL`.

---

## C4 to Insight

The treatment, which is the fill, border colour, border style and width a
node takes, is **derived** from what the element is, never chosen, so one
kind of element looks the same on every diagram and the key's wording is
always true:

| Element | Treatment | Key text |
| ------- | --------- | -------- |
| `Person` | `input` | Person |
| `Software System`, in scope (context) or `"focus": true` | `focal` (accent, 2px border) | Focus of this diagram |
| `Software System`, not external, not in focus | `backend` | Software system |
| anything with `"external": true` | `external` | External software system, not owned by this team |
| `Container` with `"store": true` | `store` | Container (data store) |
| `Container` | `backend` | Container (application) |
| `Component` | `backend` | Component |
| `"status": "optional"` | `optional` (dashed) | Optional |
| `"status": "retired"` | `retired` (greyed, dotted) | Removed or under review |
| a boundary | zone wash | Boundary / Group / Trust boundary |

**Focal discipline.** At most one `focus` per diagram: the element the
diagram is about. On a context diagram the system in scope is the focus
automatically. The accent is editorial, not a highlighter. The focal border
is 2px as well as magenta so the distinction survives greyscale printing.

**Icons are mandatory on Azure and Fabric nodes**, per the
`insight-diagram-design` skill, and forbidden everywhere else. A component,
a person, a browser, a third-party SaaS and an on-premises system carry no
icon. Never substitute a generic glyph for a missing one; the renderer warns
and draws the node plain, which is the correct outcome. Every icon drawn is
listed in the key by service name.

Match the icon by service, not by nickname: Cognitive Search is `ai-search`,
Form Recognizer is `document-intelligence`, AI Studio is `ai-foundry`.

| Relationship | `kind` | `dashed` |
| ------------ | ------ | -------- |
| call between two things you own | `default` | no |
| the headline path the diagram exists to show | `accent` | no |
| a call to or from an external element | `link` (one end must be external) | no |
| asynchronous, optional, fallback or message-based | either | yes |

At most two accent elements per diagram, counting focal nodes and accent
edges together.

---

## Budget

The `insight-diagram-design` budget is 9 nodes, and a C4 level routinely needs
more: a context diagram that hides half the external systems is wrong, not
clean. This skill therefore raises the ceiling and keeps the spirit:

| | Ceiling | What to do when you exceed it |
| --- | --- | --- |
| nodes per diagram | **16** | Split the level. C4 drill-down already exists for exactly this. |
| edges | 24 | Merge parallel relationships into one labelled edge. |
| focal nodes | 1 (2 accents in all) | Pick the one the diagram is about. |
| boundaries | 3 | More than three reads as a swimlane, which is a different diagram. |
| element name | 40 characters, 3 lines | Shorten it. |
| technology | 48 characters, 2 lines on the box | Name the language and framework, not every library. |
| description | 120 characters | One sentence at a glance; the detail goes in the `.md`. |
| relationship label | 56 characters, 2 lines | The detail goes in the `.md`. |
| relationship technology | 32 characters | `JSON/HTTPS`, not a list of endpoints. |

A context diagram with 20 external systems is a signal that the externals
want grouping: "Azure AI services" as one external software system, with the
detail in the markdown table, beats twenty boxes nobody reads.

Raising the node ceiling is the one deliberate deviation from the upstream
budget. Everything else (one accent, no shadows, no rainbow, the 4px grid,
the six connector rules) is applied unchanged.

---

## Spec schema

Schema 2. One file per diagram, beside the `.md` it illustrates. Unknown keys
are errors, so a typo cannot silently drop a label. A complete set for one
system lives in `assets/insight-c4/examples/` (context, container and
component); copy from there.

```json
{
  "schema": 2,
  "level": "container",
  "subtitle": "The applications and data stores inside the Recipe Planner",
  "desc": "The cook uses a Vue single-page app, which calls a FastAPI service that stores data in PostgreSQL.",
  "rows": [
    ["cook"],
    ["spa"],
    ["api"],
    ["db"],
    ["aoai"]
  ],
  "nodes": {
    "cook": { "name": "Home Cook", "type": "Person",
              "description": "Plans weekly meals and shops for them." },
    "spa":  { "name": "Planner UI", "type": "Container", "technology": "TypeScript, Vue 3",
              "description": "Lets the cook browse recipes and plan the week in a browser." },
    "api":  { "name": "Planner API", "type": "Container", "technology": "Python 3.12, FastAPI",
              "focus": true, "href": "../../src/api/",
              "description": "Serves recipes, meal plans and shopping lists." },
    "db":   { "name": "Recipe Database", "type": "Container", "store": true,
              "technology": "PostgreSQL 16 database schema",
              "description": "Stores recipes, meal plans and shopping lists." },
    "aoai": { "name": "Azure OpenAI", "type": "Software System", "external": true,
              "icon": "azure-openai",
              "description": "Suggests recipes from a list of ingredients." }
  },
  "boundaries": [
    { "name": "Recipe Planner", "type": "Software System", "members": ["spa", "api", "db"] }
  ],
  "edges": [
    { "from": "cook", "to": "spa", "label": "Plans meals and shopping using" },
    { "from": "spa", "to": "api", "label": "Makes API requests to", "technology": "JSON/HTTPS" },
    { "from": "api", "to": "db", "label": "Reads from and writes to", "technology": "SQL/TLS" },
    { "from": "api", "to": "aoai", "label": "Requests recipe suggestions from",
      "technology": "JSON/HTTPS", "kind": "link" }
  ],
  "acronyms": { "PKCE": "Proof Key for Code Exchange" }
}
```

### Fields

| Key | Required | Meaning |
| --- | -------- | ------- |
| `schema` | yes | `2`. A spec without it is schema 1 and is refused; see `#upgrading-a-schema-1-spec`. |
| `level` | yes | `context`, `container` or `component`: the C4 diagram type (`#diagram-types-and-files`). |
| `desc` | yes | One sentence, in content terms. Becomes the SVG `<desc>`, which is what a screen reader reads. |
| `rows` | yes | Ordered top to bottom; each is a list of node ids. **Every node appears in exactly one row.** |
| `nodes` | yes | Map of id to an element (below). |
| `boundaries` | per level | `{name, type, members, security, labelAlign}`. Required by the container and component scope rules. Up to three. |
| `edges` | no | `{from, to, label, technology, kind, dashed}` (below). |
| `acronyms` | when used | Map of every upper-case acronym on the diagram that the renderer does not already expand, to its expansion. |
| `subtitle` | no | One line under the title. |
| `eyebrow` | no | The HTML page's kicker; defaults to `C4 <level> · Insight`. |
| `preset` | no | `fit` (default), `doc-inline`, `doc-wide`, `slide-16x9`, `slide-4x3`, `print-a4-landscape`. |

There is no `title` field: the title is derived (`#titles`).

### Element fields

| Key | Required | Meaning |
| --- | -------- | ------- |
| `name` | yes | The element's name, as it reads on every diagram. |
| `type` | yes | `Person`, `Software System`, `Container` or `Component`. |
| `technology` | Container, Component | Language and framework, or the store and what it is. Forbidden on a Person or Software System. |
| `description` | yes | One sentence of three words or more, ending in a full stop. |
| `external` | no | `true` for an element your team does not own. |
| `store` | no | `true` for a data store container. |
| `focus` | no | `true` on the one element the diagram is about (not needed on a context diagram). |
| `status` | no | `optional` or `retired`. |
| `icon` | Azure, Fabric | Official icon slug, e.g. `container-apps`, `ai-search`, `lakehouse`. Azure and Fabric nodes only. |
| `href` | no | Link from the HTML page: the source directory or the child `.md`, repo-relative from the diagram's folder. |
| `width` | no | Override the automatic width: 120, 140, 160, 180, 200 or 240. |

### Edge fields

| Key | Required | Meaning |
| --- | -------- | ------- |
| `from`, `to` | yes | Node ids. The arrow points at `to`; the label reads `from` label `to`. |
| `label` | yes | Sentence-case verb phrase ending on its preposition (`#relationship-labels`). |
| `technology` | between containers, across a container boundary | Protocol or technology without brackets: `JSON/HTTPS`. Forbidden on context diagrams and on lines with a person. |
| `kind` | no | `default`, `accent` or `link`. |
| `dashed` | no | `true` for asynchronous, optional, fallback or message-based. |

### Boundary fields

| Key | Meaning |
| --- | ------- |
| `name` | The enclosed element's name: the system, or the container. |
| `type` | `Software System`, `Container` or `Group`. |
| `members` | Node ids inside it. Nested boundaries nest their member sets; overlapping sets that do not nest are an error. |
| `security` | `true` for a trust boundary (dashed accent wash). |
| `labelAlign` | `left` (default) or `right`: where the label prefers to sit. |

### Row design

Rows are the whole layout language, and a good row assignment is most of a
good diagram. A boundary is drawn round the rows its members occupy, so
**members and non-members never share a row**: the renderer fails a
boundary that encloses a node it does not hold. The convention that reads
best top to bottom:

| Level | Rows |
| ----- | ---- |
| Context | people → the system in scope → external systems |
| Container | people → the SPA or entry point → services → data stores → external systems |
| Component | callers (people, sibling containers) → the entry component → the layers it calls → sibling data stores → external systems |

Put nodes that talk to each other in adjacent rows. An edge spanning more than
one row is routed out to a side lane, which is correct but visually louder
than a short hop; if several edges do it, the rows are in the wrong order.

---

## Upgrading a schema 1 spec

Schema 1 specs (no `"schema"` key) carried a `kind`, an uppercase `tag`, a
`sublabel` and a 14-character uppercase arrow label, and nothing that
stated an element's C4 type, technology or description. The renderer refuses
them; nothing can be inferred safely. Upgrade each one from the code:

1. Add `"schema": 2`. Delete `title` (it is derived) and rename `zones` to
   `boundaries`, giving each a `name` and a `type`.
2. For each node, replace `kind`, `tag` and `sublabel` with `type`,
   `technology`, `description` and the flags: `input` was a `Person`;
   `external` is `"external": true` (a `Software System`); `store` is a
   `Container` with `"store": true`; `focal` is `"focus": true` (or the
   system in scope on a context diagram); `backend` is whatever the element
   is. The old `sublabel` usually becomes `technology`; ports and SKUs go in
   the `.md`.
3. Rewrite every edge `label` as a sentence-case verb phrase ending on its
   preposition, and move the protocol (the old label was often only a
   protocol, like `HTTPS + SSE`) into `technology`.
4. Check the level is a real C4 diagram (`#diagram-types-and-files`): an old
   context diagram that drew containers next to external systems is split
   into a `context.c4.json` and a `containers.c4.json`; an old
   `container.c4.json` becomes `"level": "component"` with the two
   boundaries; a node that was a shared package (`PKG`) is removed and its
   relationship is described on the containers that use it.
5. Render with `--check` until every spec is `ok`, then render with `--png`
   and run `lint.py`.

---

## Lint rules

The 36 rules of the C4 checklist, by id. **Where** says who checks it:
`render` refuses the spec, `lint` checks the rendered SVG (`lint.py`),
`construction` means the renderer cannot produce a violation, `review` is a
judgment you make by eye, `n/a` is a diagram type this skill does not draw.
Both `render --check` and `lint.py` print findings as `<id> <message>`;
`(review)` marks a finding that does not fail the run.

| ID | Rule | Where |
| -- | ---- | ----- |
| T1 | The diagram has a visible title | construction; lint |
| T2 | The title names the diagram type (`<Type> diagram for ...`) | construction; lint |
| T3 | The title names the scope | construction; lint |
| K1 | A key is present | construction; lint |
| K2 | Every colour is explained in the key (and `link` only touches an external element) | construction; render (`link`); lint |
| K3 | Every shape is explained | construction; lint |
| K4 | Every border and line style and width is explained | construction; lint |
| K5 | Every arrowhead is explained | construction; lint |
| K6 | Every icon is explained | construction; lint |
| K7 | Element sizes carry no unexplained meaning | construction (key note); lint |
| K8 | Every acronym is explained | render; lint |
| N1 | Every element has a name | render; lint |
| N2 | Every element states its type in words | render; lint |
| N3 | Every container and component states its technology | render; lint |
| N4 | Every element has a description: three words or more, one sentence ending in a full stop | render; lint |
| N5 | People and software systems carry no technology | render; lint |
| N6 | No generic descriptions | render; lint ("business logic" anywhere is `review`) |
| N7 | The element type matches the abstraction: a library, package, SDK or message bus is not a container | render; lint; module and folder names are `review` |
| L1 | Every line is labelled | render; lint |
| L2 | Labels are specific, not one word or "Uses", and short | render; lint |
| L3 | The label reads source, label, target: a sentence-case verb phrase ending on its preposition | render; lint; whether it starts with a verb is `review` |
| L4 | Every line is one way | construction; lint |
| L5 | Lines with a container, or across a container boundary, state technology | render; lint |
| L6 | No technology on context diagram lines or on lines with a person | render; lint |
| L7 | Dynamic diagram steps are numbered | n/a |
| S1 | Context scope: one system in scope, only people and external systems around it, all connected to it | render; lint |
| S2 | Landscape scope | n/a |
| S3 | Container scope: one system boundary holding exactly the containers; people and systems outside, connected | render; lint |
| S4 | Component scope: one container boundary inside one system boundary; components, sibling containers and outside elements where they belong | render; lint |
| S5 | Deployment scope | n/a |
| S6 | Dynamic scope | n/a |
| S7 | Levels are not mixed (and an external element is a software system: `review`) | render; lint |
| X1 | An element has the same name, type line and description on every diagram | render (per run); lint (per run) |
| X2 | An element has the same treatment on every diagram | construction; render; lint |
| X3 | A relationship has the same label and technology on every diagram | render; lint |
| X4 | Colour is never the only carrier of meaning | construction (type lines, focal border, boundaries); review |

`spec` findings are schema problems (unknown key, missing `desc`, schema 1,
a row naming an unknown node); `layout:` findings are the geometry failures
listed under `#running-it`.

---

## What the renderer guarantees

You do not need to check these; they hold by construction, and `--check`
and `lint.py` prove the ones that are checkable.

- **C4 labels.** Every box reads name, `[Type: technology]`, description;
  every line is one way and carries its verb phrase and, where required, its
  `[technology]`; the title is `<Type> diagram for <scope>`.
- **The key** covers every treatment, boundary, line style, arrowhead, icon
  and acronym used and nothing else, wraps onto as many rows as it needs and
  is part of the SVG, so the PNG carries it.
- **Colour and type.** Insight semantic roles only, from `tokens.py`. Harmony
  is the one accent, Vision blue is reserved for `link` edges, node text is
  Inter, technical text is Geist Mono.
- **The six connector rules.** Every bend is a quarter arc at `r=8`; no
  diagonals; labels sit on an opaque paper mask clear of the stroke;
  connectors on a shared edge are fanned at `L·k/(N+1)`, at least 12px apart;
  parallel runs are 16px apart; a horizontal run that crosses another route's
  vertical gets a hop.
- **Rule 5, structurally.** Every connector runs in a *gutter* (the empty band
  between two rows) or a *side lane* (an empty column outside the widest row),
  so nothing can pass behind a node that is not its endpoint. `--check` still
  asserts it.
- **Z-order.** Background, boundaries, arrows, labels, boundary names, nodes,
  key, so a mask can never be clipped by a node drawn after it.
- **The 4px grid** on every coordinate, size and font size.
- **Accessibility.** `role="img"`, `aria-labelledby`, a `<title>` as the first
  child and a `<desc>`, ids prefixed with the diagram slug, and a `<title>` on
  every node group carrying its full label.
- **Semantic markup.** `data-c4-*` attributes and `c4-*` classes on every
  element, relationship, boundary and key entry, which is what `lint.py`
  reads.
- **Single file.** Inline SVG, inlined icons (with per-instance id prefixes so
  two copies of one icon cannot collide), no external asset but the Google
  Fonts stylesheet, no script.

---

## Output per level

```text
codemap/<system>/
  context.c4.json     the model: the source of record, this is what you edit
  context.html        the Insight page (open in a browser, paste into a deck)
  context.svg         standalone SVG
  context.png         raster, at scale 2: this is what the .md embeds
  context.md          the document
```

The `.md` embeds the PNG and links the HTML:

```markdown
## Diagram

[![System Context diagram for Recipe Planner](./context.png)](./context.html)

Drawn in the Insight design system from [`context.c4.json`](./context.c4.json).
Regenerate with `python3 <render.py> codemap/<system>/context.c4.json --png`.
```

The image alt text is the diagram's title. A `.png` is stale when its
`.c4.json` is newer. The spec is the source of record; the three rendered
files are build output.

---

## Icons

The renderer discovers the official packs shipped by the
`insight-diagram-design` skill under `~/.claude/plugins/` and
`~/.claude/skills/`, and takes `--icons DIR` when they live elsewhere. About 90
Azure services and 94 Fabric items are bundled there.

Common slugs for the services that show up in a codemap:

`container-apps` · `container-apps-environments` · `container-registries` ·
`app-services` · `function-apps` · `static-web-apps` · `api-management` ·
`azure-openai` · `ai-search` · `ai-foundry` · `ai-services` ·
`document-intelligence` · `content-safety` · `speech` · `translator` ·
`sql-database` · `sql-server` · `cosmos-db` · `postgresql` · `mysql` ·
`cache-redis` · `storage-accounts` · `blob-block` · `data-lake-storage` ·
`azure-files` · `entra-id` · `managed-identities` · `key-vaults` ·
`app-configuration` · `application-insights` · `log-analytics` · `monitor` ·
`service-bus` · `event-hubs` · `event-grid-topics` · `data-factory` ·
`databricks` · `synapse-analytics` · `power-bi` · `front-door` ·
`application-gateways` · `firewalls` · `private-endpoints` ·
`virtual-networks` · `kubernetes-services` · `browser` · `globe` · `users`

If a service is not in the pack, download the current official set from
`https://learn.microsoft.com/azure/architecture/icons/`, copy the file
unmodified into the `insight-diagram-design` skill's `assets/azure-icons/`
(the folder the renderer searches), and use its slug. Never recolour,
crop or approximate one — Microsoft's terms forbid it and the renderer's
warning is the honest answer.

---

## Checks the renderer cannot make

Run these by eye on the rendered PNG before calling a diagram done; they are
the `review` half of `#lint-rules`.

- **Is every element at the right level of abstraction?** A box that is a
  library, a folder, a team or a bounded context is not a C4 element. A
  container must be something that runs or stores data.
- **Does every label start with a verb and match the arrow's direction?**
  Read it aloud: source, label, target.
- **Is the technology true?** Check `technology` against the manifest
  (`pyproject.toml`, `package.json`, the infrastructure templates).
- **Is ownership right?** External means not owned by this team, whoever
  hosts it.
- Would any two nodes merge into one? Two boxes that always travel together
  are one box.
- Does every edge carry information the layout does not already give?
- Is the focal node the thing the diagram is actually about?
- Does the row order put talkers next to each other, or is the page full of
  lane routes?
- Is the `desc` a sentence a person who cannot see the image would find
  useful, or is it a restatement of the title?
- **Is the page full of hops?** A hop is the renderer being honest about a
  crossing it could not avoid, and a fan of eight edges out of one node
  crosses everything by geometry, not by a routing mistake. The fix is
  editorial: merge the parallel relationships into one labelled edge and put
  the breakdown in the markdown table. A component diagram is usually better
  at eight edges than at seventeen.
