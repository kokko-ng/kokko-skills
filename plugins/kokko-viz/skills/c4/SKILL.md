---
name: c4
description: Authoring rules and shared templates for C4 architecture and codemap documents - strict C4 element and relationship labels, Insight-branded diagrams rendered from JSON specs, mandatory source-file hyperlinks, no validation report files, template and diagram conventions. Use when the user asks to generate, update, or verify C4 models, architecture diagrams, or codemap documentation. Trigger on "C4", "codemap", "architecture diagram", or any /c4-map, /c4-update, or /c4-verify run.
---

# C4 Authoring Skill

The rules every generated C4 or codemap document must follow, and the shared
templates the `/c4-map`, `/c4-update` and `/c4-verify` skills write from.

Read this before writing or editing anything under `codemap/`, and whenever a
skill below cites a `c4-templates.md#...` or `insight-diagrams.md#...`
anchor.

## Rules

### 1. Source file links are mandatory

Every source file, module, class, or other code element named in a generated
`.md` must be a markdown hyperlink to the actual file it refers to. Never bare
text like `src/db.py`.

- Use **repo-relative paths** computed from the document's own location, so the
  link resolves when browsing the repo on GitHub.
- **Verify the link target exists on disk before writing it.** A confident link
  to a file that was renamed is worse than no link.
- Line anchors are the one exception to repo-relative: to point at a specific
  line, use an absolute GitHub blob URL derived from `git remote get-url origin`
  and the default branch. Plain file references stay repo-relative.

Full detail and a worked example: `references/c4-templates.md#source-file-links`.

This rule is also a verification check — `/c4-verify` treats a bare-text file
reference as a hierarchy issue and fixes it.

### 2. Never write validation or verification reports into the repo

Report verification results **in the reply message**. Do not create
`VERIFICATION.md`, a report file, an audit log, or any other validation artifact
in the repository. The only file a verification run may write outside the
diagrams it is fixing is the timestamp in `codemap/README.md`.

### 3. Every document carries navigation and a timestamp

Each generated `.md` includes a parent navigation link, a drill-down table to
its children, and a `<!-- Last updated: YYYY-MM-DD -->` comment. Links must
resolve; drill-down tables must match the folders that actually exist.

### 4. Diagrams are Insight-branded, and generated — never hand-drawn

Every diagram is drawn in the Insight Enterprises design system by the
renderer bundled with this skill, from a JSON spec you author:

```text
<level>.c4.json   the model — the source of record, the only file you edit
<level>.html      the Insight page
<level>.svg       standalone SVG
<level>.png       raster at scale 2 — what the .md embeds
```

```bash
python3 codemap/.insight-c4/render.py 'codemap/**/*.c4.json' --png
python3 codemap/.insight-c4/lint.py 'codemap/**/*.svg'
```

The renderer and its linter are vendored into the model at
`codemap/.insight-c4/` so the repo regenerates and checks its diagrams
without this plugin; the plugin copy is upstream.

**Never hand-edit a generated `.html`, `.svg` or `.png`.** Edit the spec and
re-run; a hand edit is lost on the next run and puts the figure off brand.
A rendered file whose spec is newer is stale and must be regenerated. The
renderer owns colour, type, the connector grammar, the 4px grid, the title
and the key, so a diagram that renders clean is on brand and labelled the
C4 way by construction.

Full grammar, spec schema and budget: `references/insight-diagrams.md`.

### 5. Every diagram follows the C4 model's labelling semantics

C4 states its notation rules as recommendations and shows a house style in
its examples; here both are mandatory, and the renderer refuses a spec that
breaks one. In brief (full rules: `references/insight-diagrams.md#c4-semantics`):

- **Element types mean something.** `Person` uses the system. `Software
  System` delivers value and is owned by one team; everything the team does
  not own is `"external": true`, whoever hosts it. `Container` is an
  application or a data store that must run for the system to work. Data
  stores are containers; a shared library, package, SDK, module or message
  bus is not, and gets no box. `Component` is functionality behind an
  interface inside one container, not a folder or package. Code-level
  elements are not drawn here.
- **Every element label** reads name, `[Type: technology]`, description:
  `Planner API`, `[Container: Python 3.12, FastAPI]`, `Serves recipes and
  meal plans.` People and software systems carry no technology; containers
  and components always do. The description is one sentence ending in a full
  stop, never a generic term like "business logic".
- **Every relationship** is one way and labelled with a sentence-case verb
  phrase that reads source, label, target and ends on its preposition
  ("Makes API requests to"), never "Uses". A relationship with a container,
  or across a container boundary, states its technology (`JSON/HTTPS`); a
  context diagram and a line with a person state none.
- **Boundaries** carry the enclosed element's name and type:
  `Recipe Planner [Software System]`.
- **Titles** read `<Diagram type> diagram for <scope>` and are derived by the
  renderer: `System Context diagram for Recipe Planner`, `Container diagram
  for Recipe Planner`, `Component diagram for Recipe Planner - Planner API`.
- **Every diagram has a key** explaining every shape, colour, border and line
  style, arrowhead, icon and acronym it uses; the renderer generates it.
- **Diagrams agree.** An element and a relationship read the same on every
  diagram they appear on.

Verification checks the 36 C4 lint rules by id
(`references/insight-diagrams.md#lint-rules`) with `render.py --check` on the
specs and `lint.py` on the rendered SVGs, and reports each violation with its
rule id.

### 6. No PlantUML

A `.puml` under `codemap/` is a leftover from an older codemap format, not a
second supported format. `/c4-verify` converts one and deletes it. Do not
add a `.puml`, do not vendor `C4-PlantUML`, and do not reach for `plantuml`
when the renderer is missing a feature — extend the renderer or the spec.

### 7. Two optional outputs: a plain-language companion and an export

Both are asked for with a flag on `/c4-map`, `/c4-update` or `/c4-verify`,
or by a request that says as much ("an ELI5 version", "put the codemap in
my vault").

- `--eli5` writes `codemap/<system-id>/eli5.md`, a walkthrough for a reader
  who is not an engineer. It is derived from the model and says nothing the
  model does not. Once it exists it is part of the model: every later run
  keeps it in step, with or without the flag. Template and rules:
  `references/c4-templates.md#eli5-companion`.
- `--export <dir>` copies the finished documents and images to
  `<dir>/<system-id>/` for reading outside the repo, with source-file links
  rewritten to absolute URLs. The repo stays the source of record. Steps:
  `references/c4-templates.md#export`.

## Templates and schemas

Two reference files hold the shared material. Read the section an instruction
cites rather than the whole file.

`references/insight-diagrams.md` — the visual contract:

| Anchor | Contents |
| ------ | -------- |
| `#c4-semantics` | Element types, what is and is not a container, external, boundaries, element and relationship labels, titles, the key |
| `#diagram-types-and-files` | Which C4 diagram each spec is, and the scope rules per level |
| `#c4-to-insight` | How each element's Insight treatment is derived, and the icon rule |
| `#spec-schema` | The schema 2 `.c4.json`, field by field, with row-design guidance |
| `#upgrading-a-schema-1-spec` | Turning an older spec into one the renderer accepts |
| `#running-it` | The renderer's and linter's CLI, statuses and flags |
| `#lint-rules` | The 36 C4 lint rules by id, and who checks each |
| `#budget` | Node, edge, boundary, accent and label ceilings |
| `#what-the-renderer-guarantees` | What you do not have to check |
| `#checks-the-renderer-cannot-make` | The judgment half of the lint rules |
| `#icons` | Azure and Fabric icon slugs and where the packs live |

`references/c4-templates.md` — the document contract:

| Anchor | Contents |
| ------ | -------- |
| `#output-structure` | The `codemap/` folder layout and which diagram each spec is |
| `#markdown-templates` | `context.md`, `containers.md`, `container.md`, `component.md` skeletons |
| `#json-output-schemas` | Phase output and validation issue schemas |
| `#source-file-links` | Rule 1 in full, with a worked relative-path example |
| `#navigation-link-patterns` | Parent links and drill-down table format |
| `#rendering` | Renderer invocation, staleness, and the PlantUML migration |
| `#eli5-companion` | The optional plain-language `eli5.md`: skeleton and rules |
| `#export` | Copying a finished model out of the repo with `--export` |
| `#error-handling` | Phase and validation failure responses |

The files live next to this skill at `${CLAUDE_SKILL_DIR}/references/`; the
skills below pass their absolute paths into every agent brief.

## Skills and agents

| Skill | Purpose |
| ----- | ------- |
| `/kokko-viz:c4-map` | Build a C4 model from scratch (context, containers, components) |
| `/kokko-viz:c4-update` | Bring an existing model in line with code changes |
| `/kokko-viz:c4-verify` | Check an existing model against the code and fix what is wrong |

All three run forked, so their phase output stays out of the caller's
conversation, and they delegate to two plugin agents: `kokko-viz:c4-mapper`
(analysis and edits, with this skill preloaded) and `kokko-viz:c4-checker`
(read-only mechanical re-checks on a small model). Invoked directly rather
than through one of these skills, follow the same rules and the same output
structure.
