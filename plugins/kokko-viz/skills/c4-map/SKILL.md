---
name: c4-map
description: Generate a hierarchical C4 architecture map (context/containers/components) from a codebase.
argument-hint: '[target-directory]'
allowed-tools: Agent, Bash, Read, Write, Glob, Grep
context: fork
background: false
---

# C4 Architecture Mapping

Map the codebase architecture as a hierarchical C4 model
(Context -> Containers -> Components). No existing model required.
`$1`, when given, is the directory to map (default when empty: the current
project root) — scope every search to it and state it in every phase prompt
below.

## Orchestration

```text
Phase 1: Context -> Phase 2: Containers -> Phase 3: Components ->
Phase 4: Synthesis -> Phase 5: Files
```

Each level depends on the previous. Execute sequentially, passing outputs
forward. This skill runs forked: the phase outputs stay in this context and
the caller receives only the summary at the end. Nobody can answer a
question mid-run, so report and stop instead of asking.

Every phase below is a `kokko-viz:c4-mapper` agent (spawn it by that name
with the Agent tool). It has the `c4` skill preloaded, so it knows the
authoring rules, and it reads the template sections a brief cites by
itself; the brief only needs the TEMPLATES path below and the inputs from
earlier phases. The agents' model and effort come from their own
frontmatter, so nothing here pins a model.

**Read the `c4` skill first:** `${CLAUDE_PLUGIN_ROOT}/skills/c4/SKILL.md`. It
holds the authoring rules every generated document must follow — mandatory
source-file hyperlinks and the ban on validation report files — and indexes the
shared templates.

TEMPLATES (paste this absolute path into every brief):
!`echo "${CLAUDE_PLUGIN_ROOT}/skills/c4/references/c4-templates.md"`

DIAGRAMS (paste this one too):
!`echo "${CLAUDE_PLUGIN_ROOT}/skills/c4/references/insight-diagrams.md"`

RENDERER:
!`echo "${CLAUDE_PLUGIN_ROOT}/skills/c4/assets/insight-c4/render.py"`

Read the relevant section of those files yourself whenever a step below cites
a `c4-templates.md#...` or `insight-diagrams.md#...` anchor. Output structure:
see `c4-templates.md#output-structure`.

Diagrams are Insight-branded and generated from JSON specs by the renderer —
there is no PlantUML here. A phase that produces a diagram produces a
`<level>.c4.json` per `insight-diagrams.md#spec-schema`.

---

## Phase 1: System Context

```yaml
Tool: Agent
Parameters:
  subagent_type: "kokko-viz:c4-mapper"
  description: "Map C4 system context"
  prompt: |
    Map SYSTEM CONTEXT level (C4 Level 1).

    GOALS:
    1. Identify system name, create kebab-case SYSTEM_ID
    2. Define system boundary and purpose
    3. Find actors (auth patterns, API consumers, user roles)
    4. Map external systems (SDK imports, env vars, HTTP clients)
    5. Identify preliminary containers (deployable units)

    SEARCH:
    - Glob: **/*.env*, **/pyproject.toml, **/package.json
    - Grep: "requests\.", "httpx\.", "import.*azure", "import.*aws"
    - Check docker-compose.yml for external services

    TEMPLATES: <absolute path from above>
    DIAGRAMS: <absolute path from above>
    OUTPUT: JSON matching c4-templates.md#context-phase-output (read that section)
```

Wait for Phase 1. Store: `SYSTEM_ID`, `EXTERNAL_SYSTEMS`, `PRELIMINARY_CONTAINERS`.

---

## Phase 2: Containers

```yaml
Tool: Agent
Parameters:
  subagent_type: "kokko-viz:c4-mapper"
  description: "Map C4 containers"
  prompt: |
    Map CONTAINER level (C4 Level 2).

    CONTEXT FROM PHASE 1:
    - SYSTEM_ID: <insert>
    - EXTERNAL_SYSTEMS: <insert>
    - PRELIMINARY_CONTAINERS: <insert>

    GOALS:
    For each preliminary container:
    1. Validate it's a distinct deployable unit
    2. Identify technology stack (framework, runtime)
    3. Map inter-container communication (protocols)
    4. Identify preliminary components within each
    5. Validate external system boundaries

    SEARCH:
    - Glob: **/Dockerfile, **/docker-compose.yml, **/main.py
    - Grep: "FastAPI", "Express", "Flask"
    - Analyze directory structure per container

    TEMPLATES: <absolute path from above>
    DIAGRAMS: <absolute path from above>
    OUTPUT: JSON matching c4-templates.md#container-phase-output (read that section)
```

Wait for Phase 2. Store: `CONTAINERS` (with `PRELIMINARY_COMPONENTS`),
`CONTAINER_RELATIONSHIPS`.

---

## Phase 3: Components

```yaml
Tool: Agent
Parameters:
  subagent_type: "kokko-viz:c4-mapper"
  description: "Map C4 components"
  prompt: |
    Map COMPONENT level (C4 Level 3).

    CONTEXT FROM PHASE 2:
    - SYSTEM_ID: <insert>
    - CONTAINERS: <insert full array>

    GOALS:
    For each component in each container:
    1. Validate coherent module with clear responsibility
    2. Identify internal dependencies (same container)
    3. Identify cross-container dependencies
    4. Map component interfaces/contracts

    SEARCH:
    - Read __init__.py or index.ts for exports
    - Grep: "class \w+"
    - Analyze import statements

    TEMPLATES: <absolute path from above>
    DIAGRAMS: <absolute path from above>
    OUTPUT: JSON matching c4-templates.md#component-phase-output (read that section)
```

Wait for Phase 3. Store: `COMPONENTS_BY_CONTAINER`.

---

## Phase 4: Synthesis

```yaml
Tool: Agent
Parameters:
  subagent_type: "kokko-viz:c4-mapper"
  description: "Synthesize C4 model"
  prompt: |
    Validate cross-level consistency before file generation.

    PHASE OUTPUTS:
    - Phase 1 (Context): <insert>
    - Phase 2 (Containers): <insert>
    - Phase 3 (Components): <insert>

    VALIDATION CHECKS:
    1. ID Consistency: Every element traces to parent level
    2. Relationship Consistency: Dependencies match imports
    3. Coverage Gaps: Missing elements, empty containers
    4. Naming Conflicts: Duplicate IDs, invalid folder names
    5. Structural Issues: Empty containers, deep nesting

    TEMPLATES: <absolute path from above>
    OUTPUT:
    {
      "VALIDATION_PASSED": true/false,
      "ISSUES": [<issues per c4-templates.md#validation-issue-schema>],
      "FINAL_STRUCTURE": {corrected model}
    }
```

If validation fails with errors, report to user before proceeding.

---

## Phase 5: File Generation

Using `FINAL_STRUCTURE` from Phase 4.

**Source links are mandatory:** every source file, module, or code element
named in any generated `.md` must be a markdown hyperlink to the actual file,
per `c4-templates.md#source-file-links` — repo-relative so it resolves on
GitHub. Verify each link target exists before writing it.

### Step 0: Vendor the renderer

The repo must be able to regenerate its own diagrams without this plugin
installed, so the renderer is copied in beside the model — exactly as the
C4-PlantUML library used to be:

```bash
mkdir -p codemap/.insight-c4
cp "${CLAUDE_PLUGIN_ROOT}/skills/c4/assets/insight-c4/"*.py codemap/.insight-c4/
cp "${CLAUDE_PLUGIN_ROOT}/skills/c4/assets/insight-c4/README.md" codemap/.insight-c4/ 2>/dev/null || true
python3 codemap/.insight-c4/render.py --help >/dev/null && echo "renderer ok"
```

The plugin copy is upstream; the vendored copy is a build tool, not a place
to fix things. Re-copy it whenever the plugin updates.

Nothing else to provision: the renderer is pure standard library and finds
the official Azure and Fabric icon packs from the `insight-diagram-design`
skill by itself. If that skill is not installed, Azure nodes render without
icons and the renderer says so — report it rather than substituting a glyph.

### Step 1: Create Folders

```bash
SYSTEM_ID="<from FINAL_STRUCTURE>"
mkdir -p codemap/$SYSTEM_ID/containers
for CONTAINER_ID in <containers>; do
  mkdir -p codemap/$SYSTEM_ID/containers/$CONTAINER_ID/components
  for COMPONENT_ID in <components>; do
    mkdir -p codemap/$SYSTEM_ID/containers/$CONTAINER_ID/components/$COMPONENT_ID
  done
done
```

### Step 2: Write Files

Write the spec and the document at each level. Markdown skeletons are in
`c4-templates.md#markdown-templates`; the spec schema and the row conventions
are in `insight-diagrams.md#spec-schema`.

| Level | Files |
| ----- | ----- |
| System | `context.c4.json`, `context.md` |
| Container | `container.c4.json`, `container.md` |
| Component | `component.c4.json`, `component.md` |

Per diagram: one `focal` node (the element the diagram is about), official
Azure or Fabric icons on every Azure or Fabric node and on nothing else,
boundaries as zones, 16 nodes maximum. Give each node an `href` to its source
directory or child document so the HTML page is navigable.

Each markdown file must include a parent navigation link, a drill-down table
to children, and a `<!-- Last updated: YYYY-MM-DD -->` timestamp.

### Step 3: Render

```bash
python3 codemap/.insight-c4/render.py 'codemap/**/*.c4.json' --png
```

Every spec must report `ok`. A `FAIL` is a geometry problem — a connector
behind a node, or a label mask on a node — and it is fixed by changing the
spec (usually the row order), never by editing the output. Warnings about
budget or a missing icon are reported to the user, not silently accepted.

### Step 4: Write README

Create `codemap/README.md` with entry point to `<system-id>/context.md`.

### Step 5: Confirm

```bash
find codemap -type f | sort
```

---

## Output Summary

```markdown
# C4 Mapping Complete

## System: <system-id>

## Structure Generated
- Context level: 1 diagram
- Containers: X containers
- Components: Y components

## Files Created
- Total files: N (specs: X, markdown: Y, rendered: Z)

## Diagram Checks
- Renderer: all ok / N failures
- Warnings: [budget, missing icons, ...]

## Entry Point
`codemap/<system-id>/context.md`

## Validation
- Status: PASSED/FAILED
- Issues: [list if any]
```

If any phase fails, report it and do not proceed to dependent phases.
