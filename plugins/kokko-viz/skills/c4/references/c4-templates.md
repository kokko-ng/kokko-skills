# C4 Architecture Templates Reference

Shared document templates and patterns for the `/kokko-viz:c4-map`,
`/kokko-viz:c4-update`, and `/kokko-viz:c4-verify` commands. This is a
reference file, not a command.

Diagrams are covered by its sibling, `insight-diagrams.md`: the Insight
design grammar, the `.c4.json` spec schema and the renderer. This file covers
the folders, the markdown and the phase JSON.

---

## Output Structure

```text
codemap/
├── README.md
├── .insight-c4/                 # vendored renderer (not browsed)
└── <system-id>/
    ├── context.c4.json          # the model — the source of record
    ├── context.html             # Insight page   ┐
    ├── context.svg              # standalone SVG ├ generated, never hand-edited
    ├── context.png              # raster @2x     ┘
    ├── context.md
    └── containers/
        └── <container-id>/
            ├── container.c4.json
            ├── container.{html,svg,png}
            ├── container.md
            └── components/
                └── <component-id>/
                    ├── component.c4.json
                    ├── component.{html,svg,png}
                    └── component.md
```

There is no `.c4-plantuml/` directory and no `.puml` file. See `#rendering`.

---

## Markdown Templates

### context.md

```markdown
# System Context: [System Name]

<!-- Last updated: YYYY-MM-DD -->

[System description]

## Diagram

[![System Context](./context.png)](./context.html)

Drawn in the Insight design system from [`context.c4.json`](./context.c4.json).

## Actors

| Actor | Description |
|-------|-------------|
| [Name] | [Description] |

## External Systems

| System | Type | Description |
|--------|------|-------------|
| [Name] | [Type] | [Description] |

## Drill Down - Containers

| Container | Technology | Description | Details |
|-----------|------------|-------------|---------|
| [Name] | [Tech] | [Desc] | [View](./containers/<id>/container.md) |
```

### container.md

```markdown
# Container: [Container Name]

<!-- Last updated: YYYY-MM-DD -->

**Parent:** [System Context](../../context.md)

[Container description]

## Diagram

[![Container](./container.png)](./container.html)

Drawn in the Insight design system from [`container.c4.json`](./container.c4.json).

## Technology

| Aspect | Value |
|--------|-------|
| Framework | [Framework] |
| Runtime | [Runtime] |

## Dependencies

- External: [List external systems]
- Containers: [List container dependencies]

## Drill Down - Components

| Component | Responsibility | Details |
|-----------|----------------|---------|
| [Name] | [Desc] | [View](./components/<id>/component.md) |
```

### component.md

```markdown
# Component: [Component Name]

<!-- Last updated: YYYY-MM-DD -->

**Parent:** [Container Name](../../container.md)
**System:** [System Context](../../../../context.md)

[Component description]

## Diagram

[![Component](./component.png)](./component.html)

Drawn in the Insight design system from [`component.c4.json`](./component.c4.json).

## Responsibility

[Detailed responsibility]

## Dependencies

- Internal: [Same container dependencies]
- Cross-Container: [Other container dependencies]
```

---

## Diagrams

The visual contract lives in `insight-diagrams.md`. The two things every
phase needs from it:

- **Which treatment a C4 element takes** — `insight-diagrams.md#c4-to-insight`.
  `Person` is `input`, `System_Ext` is `external` and carries its official
  Azure or Fabric icon, `ContainerDb` is `store`, a `Component` is `backend`
  and carries no icon, a boundary is a zone, and exactly one node per diagram
  is `focal`.
- **The spec schema** — `insight-diagrams.md#spec-schema`. A phase that
  produces a diagram produces a `<level>.c4.json`, not SVG and not PlantUML.

Budget per diagram: 16 nodes, 24 edges, 2 accent elements, 3 zones, arrow
labels of 14 uppercase characters or fewer. Over 16 nodes, split the level.

---

## JSON Output Schemas

### Context Phase Output

```json
{
  "SYSTEM_ID": "kebab-case-id",
  "SYSTEM_NAME": "Human Readable Name",
  "SYSTEM_DESCRIPTION": "Description",
  "EXTERNAL_SYSTEMS": [
    {"id": "string", "name": "string", "type": "string", "evidence": "file:line"}
  ],
  "ACTORS": [
    {"id": "string", "name": "string", "description": "string"}
  ],
  "PRELIMINARY_CONTAINERS": [
    {"id": "string", "name": "string", "type": "Application|Database|Queue"}
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
      "technology": "string",
      "description": "string",
      "source_path": "path/",
      "external_deps": ["external-id"],
      "container_deps": ["container-id"],
      "PRELIMINARY_COMPONENTS": [
        {"id": "string", "name": "string", "path": "path/"}
      ]
    }
  ],
  "CONTAINER_RELATIONSHIPS": [
    {"from": "id", "to": "id", "protocol": "SQL|HTTP|gRPC", "description": "string"}
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
        "source_path": "path/",
        "responsibility": "string",
        "internal_deps": ["component-id"],
        "cross_container_deps": []
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
  "category": "completeness|accuracy|hierarchy|diagram|image_pairing",
  "description": "string",
  "location": "file/path",
  "fix": "How to resolve"
}
```

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

## Search Strategies

### External System Detection

```text
Glob: **/*.env*, **/config.*, **/settings.*
Grep: "requests\.", "httpx\.", "import.*azure", "import.*aws"
Check: docker-compose.yml for external services
```

### Container Detection

```text
Glob: **/Dockerfile, **/docker-compose.yml, **/main.py, **/app.py
Grep: "FastAPI", "Express", "Flask", "if __name__"
Check: Directory structure for deployable units
```

### Component Detection

```text
Glob: **/__init__.py, **/index.ts
Grep: "class \w+", "def \w+", "export"
Check: Package/module structure under each container
```

---

## Source File Links

Every source file, module, or code element mentioned in a generated `.md`
document MUST be a markdown hyperlink to the actual file it refers to — never
bare text like `market_research_agent/db.py`. Use repo-relative paths from the
document's own location, so the links resolve when browsing the repo on
GitHub:

```markdown
<!-- from codemap/<system-id>/containers/<container>/component.md -->
| Component | Source |
|-----------|--------|
| Database layer | [`db.py`](../../../../market_research_agent/db.py) |
```

Compute the relative prefix from the document's depth. Verify every link
target exists on disk before writing it. To point at a specific line, use an
absolute GitHub blob URL derived from `git remote get-url origin` and the
default branch (`https://github.com/<owner>/<repo>/blob/<branch>/<path>#L<n>`)
— only for line anchors; plain file references stay repo-relative.

## Navigation Link Patterns

| From Level | Parent Link | Example |
| ---------- | ----------- | ------- |
| Container | `../../context.md` | Go to system context |
| Component | `../../container.md` | Go to parent container |

### Drill-Down Table Format

```markdown
| Element | Description | Details |
|---------|-------------|---------|
| [Name] | [Desc] | [View](./path/to/file.md) |
```

---

## Rendering

The renderer is vendored into the model at `codemap/.insight-c4/`, so the
repo regenerates its own diagrams with no plugin installed:

```bash
python3 codemap/.insight-c4/render.py 'codemap/**/*.c4.json' --png   # whole model
python3 codemap/.insight-c4/render.py codemap/<system>/context.c4.json --png
python3 codemap/.insight-c4/render.py 'codemap/**/*.c4.json' --check # checks only
```

Refresh the vendored copy from the plugin whenever the plugin updates:

```bash
cp "${CLAUDE_PLUGIN_ROOT}/skills/c4/assets/insight-c4/"*.py codemap/.insight-c4/
```

The plugin copy is upstream. Fix the renderer there, never in the vendored
copy.

`--check` exits non-zero when a connector runs behind a node it does not
terminate on or a label mask lands on a node; everything else it finds prints
as a warning. Run it before every commit that touches a spec.

PNG needs a rasteriser. The renderer tries Playwright from the repo's own
`node_modules` first (true Inter), then `rsvg-convert`, then `magick` (both
fall back to Arial, which is the documented system substitute). With none of
them, the HTML and SVG are still written and the PNG step reports itself.

**Staleness:** a `.html`, `.svg` or `.png` older than its `.c4.json` is stale.
Compare commit dates rather than mtimes on a fresh clone, where checkout order
makes everything look stale.

### Migrating a PlantUML codemap

An older model has `.puml` files and a `.c4-plantuml/` library. Convert it:

1. Read each `.puml` and translate it to a `<level>.c4.json` — the macros map
   one to one onto node kinds (`insight-diagrams.md#c4-to-insight`), and the
   `Rel()` calls onto edges. The title becomes `title`; `SHOW_LEGEND()` has no
   equivalent, the renderer always emits a legend.
2. Assign rows. This is the one judgment call: PlantUML had no layout, so the
   row order is new information. `insight-diagrams.md#row-design` gives the
   convention per level.
3. Render, check, then `rm` the `.puml` and the `.c4-plantuml/` directory.
4. Update every `.md` diagram section and `codemap/README.md`.

Do not keep both formats. Two sources of record diverge within a week.

---

## Error Handling

### Phase Failure Response

- Report which phase failed and why
- Do NOT proceed to dependent phases
- Suggest resolution steps

### Validation Failure Response

- List all error-severity issues first
- Offer to proceed with warnings only
- Flag items requiring manual review
