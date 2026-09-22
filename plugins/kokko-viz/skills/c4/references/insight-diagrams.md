# Insight C4 Diagrams Reference

Every diagram in a `codemap/` is drawn in the Insight Enterprises design
system, from a JSON spec, by the renderer bundled with this skill. This file
is the contract: how a C4 element becomes an Insight node, what the spec
accepts, and what the renderer guarantees so you do not have to check it.

Read `#spec-schema` before writing a spec and `#c4-to-insight` before choosing
a node kind. The rest is reference.

---

## Why a spec and not hand-drawn SVG

The `insight-diagram-design` skill is the source of the visual language, and it
says plainly: *"For anything beyond a handful of nodes, do not hand-type the
SVG. Write a short Python generator ... Rebuilding after a fix then takes one
command, two figures in the same document share exact geometry, and the checks
can run on every iteration."*

A codemap is twenty-odd figures that must share exact geometry and be
regenerated whenever the code moves, so the generator is the only workable
form. `assets/insight-c4/render.py` **is** that generator, with the tokens in
`tokens.py` and the band layout and orthogonal router in `layout.py`. You write
the model; it owns the drawing.

**Never hand-edit a generated `.html`, `.svg` or `.png`.** Edit the spec and
re-run. A hand edit is lost on the next run and puts the figure off brand.

---

## Running it

```bash
R="${CLAUDE_PLUGIN_ROOT}/skills/c4/assets/insight-c4/render.py"

python3 "$R" codemap/<system>/context.c4.json --png      # one diagram
python3 "$R" 'codemap/**/*.c4.json' --png                # the whole model
python3 "$R" 'codemap/**/*.c4.json' --check              # checks only, writes nothing
```

| Flag | Effect |
| ---- | ------ |
| *(none)* | writes `<name>.html` (the Insight page) and `<name>.svg` beside the spec |
| `--png` | also rasterises; Playwright if the repo has it (real Inter), else `rsvg-convert` or `magick` (Arial fallback) |
| `--scale N` | PNG scale: 2 for documents and screens, 3 for print |
| `--no-svg` | skip the standalone SVG |
| `--icons DIR` | icon pack directory; auto-discovered from the `insight-diagram-design` skill otherwise |
| `--check` | run the checks and exit non-zero on a geometry failure |

It is pure standard library. Only `--png` shells out.

Exit code is non-zero when a connector runs behind a node it does not
terminate on, or a label mask lands on a node. Everything else prints as a
warning: over budget, more than two focal nodes, a coordinate off the 4px
grid, an Azure service with no official icon.

---

## C4 to Insight

The C4 notation does not survive contact with an editorial design system, and
it should not: C4's shapes carry no information that the label does not. What
carries the information here is the **treatment**.

| C4 element | `kind` | Icon? | Notes |
| ---------- | ------ | ----- | ----- |
| `Person` | `input` | no | Tag `PERSON`. People are never focal. |
| `System` (the one in scope) | `focal` | no | At context level, the system the map is about. |
| `System` (sibling in scope) | `backend` | no | |
| `System_Ext` | `external` | **yes** if Azure or Fabric | Tag with the service class: `PAAS`, `SAAS`, `IDP`, `LLM`. |
| `Container` (application) | `backend` | yes if it *is* an Azure resource | `focal` in its own container diagram only. |
| `ContainerDb` | `store` | yes (`sql-database`, `cosmos-db`, …) | Tag `DB`. |
| `ContainerQueue` | `store`, `dashed` edges | yes | |
| `Container_Ext` | `external` | yes if Azure | |
| `Component` | `backend` | no | Code modules are not Azure resources; they carry no icon. |
| `System_Boundary` / `Container_Boundary` | `zones[]` entry | — | Three zones maximum. |
| trust or network boundary | `zones[]` with `"security": true` | — | Dashed accent wash. |
| `Rel` | `edges[]` entry | — | See the edge table below. |
| something deleted or under review | `retired` | no | Greyed, dashed, no tag box. |

**Focal discipline.** Exactly one node is `focal` on most diagrams: the element
the diagram is *about*. Two at the very most. The accent is editorial, not a
highlighter — a context diagram with five magenta boxes says nothing.

**Icons are mandatory on Azure and Fabric nodes**, per the
`insight-diagram-design` skill, and forbidden everywhere else. A component,
a person, a browser, a third-party SaaS and an on-premises system carry no
icon. Never substitute a generic glyph for a missing one; the renderer warns
and draws the node plain, which is the correct outcome.

Match the icon by service, not by nickname: Cognitive Search is `ai-search`,
Form Recognizer is `document-intelligence`, AI Studio is `ai-foundry`.

| Relationship | `kind` | `dashed` |
| ------------ | ------ | -------- |
| call between two things you own | `default` | no |
| the headline path the diagram exists to show | `accent` | no |
| HTTP or API call out to an external system | `link` | no |
| optional, async, fallback, return, or a shared-code relationship with no call path | either | yes |

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
| focal nodes | 2 | Pick the one the diagram is about. |
| zones | 3 | More than three reads as a swimlane, which is a different diagram. |
| arrow label | 14 characters, uppercase | Put the detail in the `.md`, not on the line. |

The renderer warns above 16 nodes. A context diagram with 20 external systems
is a signal that the externals want grouping — "Azure AI services" as one node
with the detail in the markdown table beats twenty boxes nobody reads.

Raising the ceiling is the one deliberate deviation from the upstream budget.
Everything else — one accent, no shadows, no rainbow, the 4px grid, the six
connector rules — is applied unchanged.

---

## Spec schema

One file per diagram, named `<level>.c4.json`, beside the `.md` it illustrates:
`context.c4.json`, `container.c4.json`, `component.c4.json`.

```json
{
  "level": "context",
  "title": "System Context — OCIO AI Gateway",
  "subtitle": "General Chat and the Procurement Assistant",
  "eyebrow": "C4 context · Insight",
  "desc": "Who uses the two assistants and which external services they call.",
  "preset": "fit",

  "rows": [
    ["public_servant", "buyer", "ocio_admin"],
    ["gc", "proc"],
    ["aoai", "search", "blob"]
  ],

  "nodes": {
    "public_servant": { "name": "Public Servant", "tag": "PERSON", "kind": "input" },
    "gc": {
      "name": "General Chat",
      "sublabel": "FastAPI · 8000",
      "tag": "API",
      "kind": "focal",
      "href": "../src/backend/general-chat/"
    },
    "aoai": {
      "name": "Azure OpenAI",
      "sublabel": "gpt-5-mini",
      "tag": "PAAS",
      "kind": "external",
      "icon": "azure-openai"
    }
  },

  "zones": [
    { "label": "Azure mode", "members": ["aoai", "search", "blob"] }
  ],

  "edges": [
    { "from": "public_servant", "to": "gc", "label": "HTTPS + SSE" },
    { "from": "gc", "to": "aoai", "label": "COMPLETION", "kind": "link" },
    { "from": "gc", "to": "proc", "label": "SHARED PKG", "dashed": true }
  ]
}
```

### Fields

| Key | Required | Meaning |
| --- | -------- | ------- |
| `level` | yes | `context`, `container` or `component`. Drives the default eyebrow. |
| `title` | yes | The page H1. Not drawn inside the SVG. |
| `desc` | yes | One sentence, in content terms. Becomes the SVG `<desc>`, which is what a screen reader reads. |
| `subtitle` | no | A line of mono under the title. |
| `eyebrow` | no | Defaults to `C4 <level> · Insight`. |
| `preset` | no | `fit` (default), `doc-inline`, `doc-wide`, `slide-16x9`, `slide-4x3`, `print-a4-landscape`. Use `fit` unless the figure has a fixed home. |
| `rows` | yes | Ordered top to bottom; each is a list of node ids. **Every node must appear in exactly one row.** |
| `nodes` | yes | Map of id to `{name, sublabel, tag, kind, icon, href, width}`. |
| `zones` | no | `{label, members, security, labelAlign}`. Up to three. |
| `edges` | no | `{from, to, label, kind, dashed}`. |

### Node fields

| Key | Meaning |
| --- | ------- |
| `name` | Human-readable label, Inter 600. Wraps to two lines, then truncates — keep it short. |
| `sublabel` | Technology, port, SKU or index name. Geist Mono. This is where `FastAPI · 8000` goes, not in the name. |
| `tag` | The type tag in the corner box, uppercase, ten characters or fewer: `API`, `SPA`, `DB`, `PAAS`, `PERSON`, `PKG`. |
| `kind` | One of the eight treatments in the table above. |
| `icon` | Azure or Fabric icon slug, e.g. `container-apps`, `ai-search`, `lakehouse`. Azure and Fabric nodes only. |
| `href` | Optional link. In a codemap this points at the source directory or the child `.md`, so the HTML page is navigable. Repo-relative, from the diagram's own folder. |
| `width` | Override the automatic width. Allowed: 120, 140, 160, 180, 200, 240. |

### Row design

Rows are the whole layout language, and a good row assignment is most of a
good diagram. The convention that reads best top to bottom:

| Level | Rows |
| ----- | ---- |
| Context | actors → the systems in scope → external services (grouped in a zone) |
| Container | actors → the SPA or entry point → services → data stores → external services |
| Component | the entry component (API, router) → the layers it calls → shared infrastructure |

Put nodes that talk to each other in adjacent rows. An edge spanning more than
one row is routed out to a side lane, which is correct but visually louder
than a short hop — if several edges do it, the rows are in the wrong order.

---

## What the renderer guarantees

You do not need to check these; they hold by construction, and `--check`
proves the ones that are checkable.

- **Colour and type.** Insight semantic roles only, from `tokens.py`. Harmony
  is the one accent, Vision blue is reserved for `link` edges, node text is
  Inter, technical text is Geist Mono.
- **The six connector rules.** Every bend is a quarter arc at `r=8`; no
  diagonals; labels sit on an opaque paper mask 14px clear of the stroke;
  connectors on a shared edge are fanned at `L·k/(N+1)`, at least 12px apart;
  parallel runs are 16px apart; a horizontal run that crosses another route's
  vertical gets a hop.
- **Rule 5, structurally.** Every connector runs in a *gutter* (the empty band
  between two rows) or a *side lane* (an empty column outside the widest row),
  so nothing can pass behind a node that is not its endpoint. `--check` still
  asserts it.
- **Z-order.** Background, zones, arrows, nodes, legend — so a mask can never
  be clipped by a node drawn after it. Zone labels are placed at whichever
  point on the zone's top edge no connector crosses, and the gutter above a
  zoned row is grown so that band is clear.
- **The 4px grid** on every coordinate, size and font size.
- **Accessibility.** `role="img"`, `aria-labelledby`, a `<title>` as the first
  child and a `<desc>`, ids prefixed with the diagram slug, and a `<title>` on
  every node group.
- **Single file.** Inline SVG, inlined icons (with per-instance id prefixes so
  two copies of one icon cannot collide), no external asset but the Google
  Fonts stylesheet, no script.
- **The legend** is a strip below the diagram, covering every treatment used
  and nothing else.

---

## Output per level

```text
codemap/<system>/
  context.c4.json     the model — the source of record, this is what you edit
  context.html        the Insight page (open in a browser, paste into a deck)
  context.svg         standalone SVG
  context.png         raster, at scale 2 — this is what the .md embeds
  context.md          the document
```

The `.md` embeds the PNG and links the HTML:

```markdown
## Diagram

[![System Context](./context.png)](./context.html)

Drawn in the Insight design system from [`context.c4.json`](./context.c4.json).
Regenerate with `python3 <render.py> codemap/<system>/context.c4.json --png`.
```

A `.png` is stale when its `.c4.json` is newer. The spec is the source of
record; the three rendered files are build output.

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
`https://learn.microsoft.com/azure/architecture/icons/`, copy the file into the
skill's `assets/azure-icons/` unmodified, and use its slug. Never recolour,
crop or approximate one — Microsoft's terms forbid it and the renderer's
warning is the honest answer.

---

## Checks the renderer cannot make

Run these by eye on the rendered PNG before calling a diagram done:

- Would any two nodes merge into one? Two boxes that always travel together
  are one box.
- Does every edge carry information the layout does not already give?
- Is the focal node the thing the diagram is actually about?
- Does the row order put talkers next to each other, or is the page full of
  lane routes?
- Is the `desc` a sentence a person who cannot see the image would find
  useful, or is it a restatement of the title?
