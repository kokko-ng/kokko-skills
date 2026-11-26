# C4 Architecture Templates Reference

Shared document templates and patterns for the `/kokko-viz:c4-map`,
`/kokko-viz:c4-update`, and `/kokko-viz:c4-verify` skills. This is a
reference file, not a skill to invoke.

Diagrams are covered by its sibling, `insight-diagrams.md`: the C4 semantics
(element types, labels, titles, the key), the `.c4.json` spec schema, the
renderer and the lint rules. This file covers the folders, the markdown and
the phase JSON.

---

## Output Structure

```text
codemap/
├── README.md
├── .insight-c4/                 # vendored renderer and linter (not browsed)
└── <system-id>/
    ├── context.c4.json          # System Context diagram: the source of record
    ├── context.html             # Insight page   ┐
    ├── context.svg              # standalone SVG ├ generated, never hand-edited
    ├── context.png              # raster @2x     ┘
    ├── context.md
    ├── containers.c4.json       # Container diagram for the system
    ├── containers.{html,svg,png}
    ├── containers.md
    ├── eli5.md                  # optional plain-language companion (#eli5-companion)
    └── containers/
        └── <container-id>/
            ├── container.c4.json        # Component diagram for this container
            ├── container.{html,svg,png}
            ├── container.md
            └── components/
                └── <component-id>/
                    ├── component.c4.json  # Component diagram focused on one component
                    ├── component.{html,svg,png}
                    └── component.md
```

Which C4 diagram each spec is, and its scope rules:
`insight-diagrams.md#diagram-types-and-files`. A shared library, package or
SDK gets no folder: it is not a container, and its code is described on the
components that use it.

A `.puml` file here, or a `codemap/.c4-plantuml/` library, is a leftover;
convert it per `#migrating-a-plantuml-codemap`. A `.c4.json` without
`"schema": 2` is a schema 1 spec; upgrade it per
`insight-diagrams.md#upgrading-a-schema-1-spec`.

---

## Markdown Templates

Each document's H1 names what it documents; the image alt text is the
diagram's title.

### context.md

```markdown
# System Context diagram for [System Name]

<!-- Last updated: YYYY-MM-DD -->

[System description: what it does and for whom]

## Diagram

[![System Context diagram for [System Name]](./context.png)](./context.html)

Drawn in the Insight design system from [`context.c4.json`](./context.c4.json).

## People

| Person | Description |
|--------|-------------|
| [Name] | [Description] |

## External Software Systems

| System | Description | How the system uses it |
|--------|-------------|------------------------|
| [Name] | [Description] | [Relationship label] |

## Drill Down

[Container diagram for [System Name]](./containers.md)
```

### containers.md

```markdown
# Container diagram for [System Name]

<!-- Last updated: YYYY-MM-DD -->

**Parent:** [System Context](./context.md)

## Diagram

[![Container diagram for [System Name]](./containers.png)](./containers.html)

Drawn in the Insight design system from [`containers.c4.json`](./containers.c4.json).

## Containers

| Container | Kind | Technology | Description | Details |
|-----------|------|------------|-------------|---------|
| [Name] | Application / Data store | [Technology] | [Description] | [View](./containers/<id>/container.md) |

## Relationships

| From | To | Description | Technology |
|------|----|-------------|------------|
| [Source] | [Target] | [Verb phrase] | [Protocol] |
```

### container.md

```markdown
# Container: [Container Name]

<!-- Last updated: YYYY-MM-DD -->

**Parent:** [Container diagram](../../containers.md)
**System:** [System Context](../../context.md)

[Container description] `[Container: Technology]`

## Diagram

[![Component diagram for [System Name] - [Container Name]](./container.png)](./container.html)

Drawn in the Insight design system from [`container.c4.json`](./container.c4.json).

## Technology

| Aspect | Value |
|--------|-------|
| Framework | [Framework] |
| Runtime | [Runtime] |

## Dependencies

- External systems: [List]
- Containers: [List, with the protocol of each]

## Drill Down - Components

| Component | Technology | Responsibility | Details |
|-----------|------------|----------------|---------|
| [Name] | [Technology] | [Desc] | [View](./components/<id>/component.md) |
```

### component.md

```markdown
# Component: [Component Name]

<!-- Last updated: YYYY-MM-DD -->

**Parent:** [Container Name](../../container.md)
**System:** [System Context](../../../../context.md)

[Component description] `[Component: Technology]`

## Diagram

[![Component diagram for [System Name] - [Container Name]](./component.png)](./component.html)

Drawn in the Insight design system from [`component.c4.json`](./component.c4.json).
Focus: [Component Name] and its direct relationships.

## Responsibility

[Detailed responsibility]

## Dependencies

- Internal: [Same-container components]
- Cross-Container: [Other containers, with the protocol of each]
```

---

## Diagrams

The visual and semantic contract lives in `insight-diagrams.md`. The things
every phase needs from it:

- **C4 meaning** (`insight-diagrams.md#c4-semantics`): a container is an
  application or data store that runs; a shared library, package, SDK or
  message bus is not one; owned hosted data stores are containers; anything
  the team does not own is external.
- **Labels**: every element has a name, a `type`, a `technology`
  (containers and components only) and a one-sentence `description`; every
  relationship has a verb-phrase `label` ending on its preposition and, with
  a container or across a container boundary, a `technology`.
- **The spec schema** (`insight-diagrams.md#spec-schema`). A phase that
  produces a diagram produces a schema 2 `<level>.c4.json`, not SVG and not
  PlantUML. The title, the treatments and the key are derived; there is
  nothing to choose.

Budget per diagram: 16 nodes, 24 edges, one focus, 3 boundaries. Over 16
nodes, split the level.

---

## JSON Output Schemas

Every element in a phase output carries the fields its spec needs, so the
file phase writes specs without guessing.

### Context Phase Output

```json
{
  "SYSTEM_ID": "kebab-case-id",
  "SYSTEM_NAME": "Human Readable Name",
  "SYSTEM_DESCRIPTION": "One sentence, ending in a full stop.",
  "EXTERNAL_SYSTEMS": [
    {"id": "string", "name": "string", "description": "One sentence.",
     "relationship": "Verb phrase ending on its preposition", "evidence": "file:line"}
  ],
  "PEOPLE": [
    {"id": "string", "name": "string", "description": "One sentence.",
     "relationship": "Verb phrase ending on its preposition"}
  ],
  "PRELIMINARY_CONTAINERS": [
    {"id": "string", "name": "string", "kind": "application|data store|queue",
     "evidence": "file:line"}
  ],
  "NOT_CONTAINERS": [
    {"name": "string", "why": "shared library|package|message bus|...", "used_by": ["container-id"]}
  ]
}
```

### Container Phase Output

```json
{
  "SYSTEM_ID": "from-context",
  "CONTAINERS": [
    {
      "id": "string",
      "name": "string",
      "technology": "Language and framework, or the store and what it is",
      "store": false,
      "description": "One sentence, ending in a full stop.",
      "source_path": "path/",
      "external_deps": ["external-id"],
      "container_deps": ["container-id"],
      "PRELIMINARY_COMPONENTS": [
        {"id": "string", "name": "string", "path": "path/"}
      ]
    }
  ],
  "CONTAINER_RELATIONSHIPS": [
    {"from": "id", "to": "id", "label": "Verb phrase ending on its preposition",
     "technology": "JSON/HTTPS", "evidence": "file:line"}
  ]
}
```

### Component Phase Output

```json
{
  "SYSTEM_ID": "from-context",
  "COMPONENTS_BY_CONTAINER": {
    "container-id": [
      {
        "id": "string",
        "name": "string",
        "parent_container": "container-id",
        "technology": "Framework construct, e.g. FastAPI router",
        "description": "One sentence, ending in a full stop.",
        "source_path": "path/",
        "internal_deps": [{"to": "component-id", "label": "Verb phrase ending on its preposition"}],
        "cross_container_deps": [{"to": "container-or-system-id", "label": "Verb phrase", "technology": "SQL/TLS"}]
      }
    ]
  }
}
```

### Validation Issue Schema

```json
{
  "id": "ISSUE-001",
  "severity": "error|warning|info",
  "category": "completeness|accuracy|hierarchy|diagram|c4_rules|image_pairing",
  "rule": "N3",
  "description": "string",
  "location": "file/path",
  "fix": "How to resolve"
}
```

`rule` is the lint rule id from `insight-diagrams.md#lint-rules` for a
`c4_rules` issue (`spec` or `layout` for a renderer finding without one),
and is omitted otherwise.

### Change Detection Schema

```json
{
  "id": "change-001",
  "type": "ADDITION|DELETION|MODIFICATION|RENAME",
  "level": "CONTEXT|CONTAINER|COMPONENT",
  "affected_element": {"id": "string", "current_path": "...", "source_path": "..."},
  "description": "string",
  "cascade_up": true,
  "cascade_down": false,
  "priority": "high|medium|low"
}
```

---

## Source File Links

Every source file, module, or code element mentioned in a generated `.md`
document must be a markdown hyperlink to the actual file it refers to, never
bare text like `market_research_agent/db.py`. Use repo-relative paths from
the document's own location, so the links resolve when browsing the repo on
GitHub:

```markdown
<!-- from codemap/<system-id>/containers/<container>/container.md -->
| Component | Source |
|-----------|--------|
| Database layer | [`db.py`](../../../../market_research_agent/db.py) |
```

Compute the relative prefix from the document's depth. Verify every link
target exists on disk before writing it. To point at a specific line, use an
absolute GitHub blob URL derived from `git remote get-url origin` and the
default branch (`https://github.com/<owner>/<repo>/blob/<branch>/<path>#L<n>`),
only for line anchors; plain file references stay repo-relative.

## Navigation Link Patterns

| From | Parent Link | Example |
| ---- | ----------- | ------- |
| `containers.md` | `./context.md` | Go to system context |
| `container.md` | `../../containers.md` | Go to the container diagram |
| `component.md` | `../../container.md` | Go to parent container |

### Drill-Down Table Format

```markdown
| Element | Description | Details |
|---------|-------------|---------|
| [Name] | [Desc] | [View](./path/to/file.md) |
```

---

## Rendering

The renderer and linter are vendored into the model at `codemap/.insight-c4/`,
so the repo regenerates and checks its own diagrams with no plugin installed:

```bash
python3 codemap/.insight-c4/render.py 'codemap/**/*.c4.json' --png   # whole model
python3 codemap/.insight-c4/render.py codemap/<system>/context.c4.json --png
python3 codemap/.insight-c4/render.py 'codemap/**/*.c4.json' --check # checks only
python3 codemap/.insight-c4/lint.py 'codemap/**/*.svg'               # re-check the output
```

Refresh the vendored copy from the plugin whenever the plugin updates:

```bash
cp "${CLAUDE_PLUGIN_ROOT}/skills/c4/assets/insight-c4/"*.py codemap/.insight-c4/
```

The plugin copy is upstream. Fix the renderer there, never in the vendored
copy.

`--check` exits non-zero when a spec breaks a C4 rule or is malformed, when
the layout would mislead (a connector behind a node, a label on a node or off
the canvas, a boundary round a non-member), or when two diagrams of one
system disagree; see `insight-diagrams.md#running-it`. `lint.py` exits
non-zero when a rendered SVG breaks a rule, which catches hand edits and
stale output. Run both before every commit that touches a spec.

PNG needs a rasteriser. The renderer tries Playwright from the repo's own
`node_modules` first (true Inter), then `rsvg-convert`, then `magick` (both
fall back to Arial, which is the documented system substitute). With none of
them, the HTML and SVG are still written and the PNG step reports itself.

**Staleness:** a `.html`, `.svg` or `.png` older than its `.c4.json` is stale.
Compare commit dates rather than mtimes on a fresh clone, where checkout order
makes everything look stale.

### Migrating a PlantUML codemap

An older model has `.puml` files and a `codemap/.c4-plantuml/` library.
Convert it:

1. Read each `.puml` and translate it to a schema 2 `<level>.c4.json`. The
   macros carry the C4 type (`Person`, `System`, `System_Ext`, `Container`,
   `ContainerDb`, `Component`) and their arguments the name, technology and
   description; `Rel()` calls become edges, rewritten as verb phrases with
   the protocol in `technology`. The title is derived; `SHOW_LEGEND()` has no
   equivalent, because the renderer always emits the key.
2. Assign rows. This is the one judgment call: PlantUML had no layout, so the
   row order is new information. `insight-diagrams.md#row-design` gives the
   convention per level.
3. Render, check and lint, then `rm` the `.puml` and the `codemap/.c4-plantuml/`
   directory.
4. Update every `.md` diagram section and `codemap/README.md`.

Do not keep both formats. Two sources of record diverge within a week.

---

## ELI5 Companion

`codemap/<system-id>/eli5.md` is an optional plain-language walkthrough of
one system, for a reader who has never seen the code and may not be an
engineer. A run writes it when asked with `--eli5`, and from then on every
update and verification run keeps it current, because a companion that
disagrees with the model is worse than none.

```markdown
# [System Name], explained simply

<!-- Last updated: YYYY-MM-DD -->

[Technical view](./context.md)

## What it is for

[Two or three sentences: who uses it and what they get from it.]

![System context](./context.png)

## The parts

![Containers](./containers.png)

| Part | What it does |
|------|--------------|
| [[Container name]](./containers/<container-id>/container.md) | [One sentence, in everyday words] |

## What happens when [the main thing a user does]

1. [Step, naming each part in bold as it comes into play]

## Where the information lives

[What is stored, where, and for how long, without product names where a
plain word will do.]

## What it relies on

[The outside systems from the context level, one line each.]

## Words you will hear

| Term | Meaning |
|------|---------|
```

Rules:

- **Only what the model says.** Every part, flow, and dependency comes from
  the specs and documents at the three levels. The companion adds no fact of
  its own and names no part the model does not have.
- **Every container appears** in "The parts", linked to its `container.md`,
  under the system's Container diagram (`containers.png`).
  One to three flows, the ones a newcomer would ask about first.
- **Plain words.** Short sentences. An analogy only where it makes a part
  clearer, never as decoration. No code identifiers, file names, or class
  names in the prose: a reader who wants those follows the link to the
  technical view. (That also keeps the companion clear of the source-link
  rule, which applies to any file it does name.)
- **Embeds, not new diagrams.** Reuse the rendered `.png` files by relative
  path. The companion has no spec of its own.
- `context.md` links to it on the line under its title:
  `[Plain-language version](./eli5.md)`.

---

## Export

`--export <dir>` copies a finished model somewhere outside the repo for
reading: a notes vault, a shared folder, a handover pack. The repo's
`codemap/` stays the source of record; the export is a copy that the next
export replaces.

1. Run it last, after rendering and every check have passed.
2. The destination is `<dir>/<system-id>/`. Create `<dir>` if only its last
   segment is missing. Refuse a `<dir>` inside the repo's own `codemap/`.
3. Replace that one folder wholesale, so documents for elements that no
   longer exist do not linger. Touch nothing else in `<dir>`.
4. Copy the documents and the rasters only, keeping the folder layout so
   links between documents and image embeds still resolve:

   ```bash
   rm -rf "<dir>/<system-id>"
   mkdir -p "<dir>/<system-id>"
   rsync -a --prune-empty-dirs --include='*/' --include='*.md' --include='*.png' \
     --exclude='*' "codemap/<system-id>/" "<dir>/<system-id>/"
   ```

   Without `rsync`, copy the same set with `find` and `cp`. The specs, the
   `.html` and `.svg` renders, and the vendored renderer stay behind.
5. In the copy only, rewrite every link that points outside the codemap (the
   source-file links) to an absolute URL on the default branch, since a
   relative path means nothing outside the repo:

   | Remote | URL form |
   | ------ | -------- |
   | GitHub | `https://github.com/<owner>/<repo>/blob/<branch>/<path>` |
   | Azure DevOps | `https://dev.azure.com/<org>/<project>/_git/<repo>?path=/<path>&version=GB<branch>` |
   | none | No link: leave the path as inline code |

   Links between codemap documents stay relative.
6. Add one line under the title of the exported `context.md`:
   `Exported from <repo> at <short sha> on YYYY-MM-DD. Edit it in the repo, not here.`
7. Never `git add` the export from the source repo, and do not commit in the
   destination: what happens to a vault or a shared folder is the user's
   call.

---

## Error Handling

### Phase Failure Response

- Report which phase failed and why
- Stop before any phase that depends on it, since it would run on missing
  input
- Suggest resolution steps

### Validation Failure Response

- List all error-severity issues first, each C4 rule finding with its id
- Proceed when only warnings remain; on any error, stop before writing
  files and report the errors in the summary
- Flag items requiring manual review, including every `review` finding
