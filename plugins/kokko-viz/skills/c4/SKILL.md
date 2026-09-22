---
name: c4
description: Authoring rules and shared templates for C4 architecture and codemap documents - Insight-branded diagrams rendered from JSON specs, mandatory source-file hyperlinks, no validation report files, template and diagram conventions. Use when the user asks to generate, update, or verify C4 models, architecture diagrams, or codemap documentation. Trigger on "C4", "codemap", "architecture diagram", or any /c4-map, /c4-update, or /c4-verify run.
---

# C4 Authoring Skill

The rules every generated C4 or codemap document must follow, and the shared
templates the `/c4-map`, `/c4-update` and `/c4-verify` commands write from.

Read this before writing or editing anything under `codemap/`, and whenever a
command below cites a `c4-templates.md#...` or `insight-diagrams.md#...`
anchor.

## Rules

### 1. Source file links are mandatory

Every source file, module, class, or other code element named in a generated
`.md` MUST be a markdown hyperlink to the actual file it refers to. Never bare
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
```

The renderer is vendored into the model at `codemap/.insight-c4/` so the repo
regenerates without this plugin; the plugin copy is upstream.

**Never hand-edit a generated `.html`, `.svg` or `.png`.** Edit the spec and
re-run; a hand edit is lost on the next run and puts the figure off brand.
A rendered file whose spec is newer is stale and must be regenerated. The
renderer owns colour, type, the connector grammar and the 4px grid, so a
diagram that renders clean is on brand by construction.

Full grammar, spec schema and budget: `references/insight-diagrams.md`.

### 5. No PlantUML

This skill used to emit C4-PlantUML. It does not any more, and a `.puml`
under `codemap/` is a migration leftover, not a second supported format.
`/c4-verify` converts one and deletes it. Do not add a `.puml`, do not
vendor `C4-PlantUML`, and do not reach for `plantuml` when the renderer is
missing a feature — extend the renderer or the spec.

## Templates and schemas

Two reference files hold the shared material. Read the section an instruction
cites rather than the whole file.

`references/insight-diagrams.md` — the visual contract:

| Anchor | Contents |
| ------ | -------- |
| `#c4-to-insight` | Which Insight treatment each C4 element takes, and the icon rule |
| `#spec-schema` | The `.c4.json` schema, field by field, with row-design guidance |
| `#running-it` | The renderer's CLI and flags |
| `#budget` | Node, edge, zone and accent ceilings, and the one deviation from upstream |
| `#what-the-renderer-guarantees` | What you do not have to check |
| `#icons` | Azure and Fabric icon slugs and where the packs live |

`references/c4-templates.md` — the document contract:

| Anchor | Contents |
| ------ | -------- |
| `#output-structure` | The `codemap/` folder layout |
| `#markdown-templates` | `context.md`, `container.md`, `component.md` skeletons |
| `#json-output-schemas` | Phase output and validation issue schemas |
| `#search-strategies` | How to detect external systems, containers, components |
| `#source-file-links` | Rule 1 in full, with a worked relative-path example |
| `#navigation-link-patterns` | Parent links and drill-down table format |
| `#rendering` | Renderer invocation, staleness, and the PlantUML migration |
| `#error-handling` | Phase and validation failure responses |

The files live next to this skill at `${CLAUDE_SKILL_DIR}/references/`; the
commands below pass their absolute paths into every agent brief.

## Commands and agents

| Skill | Purpose |
| ----- | ------- |
| `/kokko-viz:c4-map` | Build a C4 model from scratch (context, containers, components) |
| `/kokko-viz:c4-update` | Bring an existing model in line with code changes |
| `/kokko-viz:c4-verify` | Check an existing model against the code and fix what is wrong |

All three run forked, so their phase output stays out of the caller's
conversation, and they delegate to two plugin agents: `kokko-viz:c4-mapper`
(analysis and edits, with this skill preloaded) and `kokko-viz:c4-checker`
(read-only mechanical re-checks on a small model). Invoked directly rather
than through a command, follow the same rules and the same output
structure.
