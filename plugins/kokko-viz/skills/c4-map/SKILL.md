---
name: c4-map
description: Generate a hierarchical C4 architecture map (context/containers/components) from a codebase.
argument-hint: '[target-directory] [--eli5] [--export <dir>]'
allowed-tools: Agent, Bash, Read, Write, Glob, Grep
context: fork
background: false
---

# C4 Architecture Mapping

Map the codebase architecture as a hierarchical C4 model
(Context -> Containers -> Components). No existing model required.
`$0`, when given and not a flag, is the directory to map (default when
empty, or when the first argument starts with `--`: the current project
root) — scope every search to it and state it in every phase prompt below.

Two optional flags may appear anywhere in `$ARGUMENTS` (rule 7 of the `c4`
skill): `--eli5` adds the plain-language companion, and `--export <dir>`
copies the finished model to `<dir>/<system-id>/`.

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
schema 2 `<level>.c4.json` per `insight-diagrams.md#spec-schema`.

Every diagram follows the C4 labelling semantics in
`insight-diagrams.md#c4-semantics` (rule 5 of the `c4` skill), and the
renderer refuses one that does not. So every phase collects what a label
needs as it goes: each element's C4 type, its technology (containers and
components), a one-sentence description and whether the team owns it; each
relationship's direction, a verb phrase ending on its preposition, and its
technology or protocol. A shared library, package or SDK is not a container
and gets no box.

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
    2. Define system boundary (what this team owns) and purpose
    3. Find people (auth patterns, API consumers, user roles)
    4. Map external software systems: what the system calls or is called
       by and the team does not own (SDK imports, env vars, HTTP clients).
       An owned data store hosted in the cloud is a container, not external.
    5. Identify preliminary containers: applications and data stores that
       must run for the system to work. List shared libraries, packages,
       SDKs and message buses under NOT_CONTAINERS instead.
    6. Write each element's description as one sentence ending in a full
       stop, and each relationship as a verb phrase ending on its
       preposition (insight-diagrams.md#c4-semantics)

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
    1. Validate it is a C4 container: an application or data store with its
       own runtime boundary (insight-diagrams.md#what-is-and-is-not-a-container).
       A SPA and the server that serves it are two; a library is none.
    2. Identify its technology for the [Container: ...] line: language and
       framework, or the store and what it is (PostgreSQL 16 database schema)
    3. Map inter-container communication: a verb-phrase label and the
       technology or protocol of every relationship (JSON/HTTPS, SQL/TLS)
    4. Identify preliminary components within each
    5. Validate external system boundaries: external means not owned

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
    1. Validate it is a C4 component: related functionality behind a
       well-defined interface, not a folder, package or utility module
    2. Identify its technology for the [Component: ...] line (the framework
       construct: FastAPI router, Spring bean, React context)
    3. Identify internal dependencies (same container) with labels
    4. Identify cross-container dependencies with labels and technology
    5. Map component interfaces/contracts

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
    6. C4 semantics: every element has its type, technology (containers and
       components) and description, every relationship its label and, with
       a container, its technology; no library or package is a container;
       one name per element across levels (insight-diagrams.md#lint-rules)

    TEMPLATES: <absolute path from above>
    OUTPUT:
    {
      "VALIDATION_PASSED": true/false,
      "ISSUES": [<issues per c4-templates.md#validation-issue-schema>],
      "FINAL_STRUCTURE": {corrected model}
    }
```

If validation still reports errors, stop here and report them in the
summary; do not generate files. Warnings alone do not stop the run.

---

## Phase 5: File Generation

Using `FINAL_STRUCTURE` from Phase 4.

**Source links are mandatory:** every source file, module, or code element
named in any generated `.md` must be a markdown hyperlink to the actual file,
per `c4-templates.md#source-file-links` — repo-relative so it resolves on
GitHub. Verify each link target exists before writing it.

### Step 0: Vendor the renderer

The repo must be able to regenerate its own diagrams without this plugin
installed, so the renderer is copied in beside the model:

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

| Folder | Files | C4 diagram (`level`) |
| ------ | ----- | -------------------- |
| `<system>/` | `context.c4.json`, `context.md` | System Context (`context`) |
| `<system>/` | `containers.c4.json`, `containers.md` | Container (`container`) |
| `containers/<id>/` | `container.c4.json`, `container.md` | Component diagram of that container (`component`) |
| `components/<id>/` | `component.c4.json`, `component.md` | Component diagram focused on that component (`component`) |

Per diagram, as `insight-diagrams.md#diagram-types-and-files` sets out: the
boundaries its scope requires (a container diagram's software system
boundary; a component diagram's container boundary inside its system
boundary), every element with `type`, `technology` where required and a
one-sentence `description`, every edge with a verb-phrase `label` and the
`technology` its endpoints require, every non-common acronym in `acronyms`,
at most one `focus`, official Azure or Fabric icons on every Azure or Fabric
node and on nothing else, 16 nodes maximum. An element and a relationship
are written identically in every spec they appear in. Give each node an
`href` to its source directory or child document so the HTML page is
navigable. Copy the shape from `assets/insight-c4/examples/` under the
`c4` skill.

Each markdown file must include a parent navigation link, a drill-down table
to children, and a `<!-- Last updated: YYYY-MM-DD -->` timestamp.

### Step 3: Render

```bash
python3 codemap/.insight-c4/render.py 'codemap/**/*.c4.json' --png
python3 codemap/.insight-c4/lint.py 'codemap/**/*.svg'
```

Every spec must report `ok` and every SVG must lint `ok`. A
`FAIL (C4 rules)` lists each broken rule by id (`N3`, `L5`, `S3`, ...;
`insight-diagrams.md#lint-rules`) and is fixed in the spec from the code, by
adding the missing technology, rewriting the label or moving the element.
A `FAIL (layout)` is fixed by changing the row order. Never edit the
output. `review` findings, budget warnings and missing icons are reported to
the user, not silently accepted.

### Step 4: Write README

Create `codemap/README.md` with entry point to `<system-id>/context.md`.

### Step 5: Plain-language companion (with `--eli5`)

Write `codemap/<system-id>/eli5.md` from `FINAL_STRUCTURE` and the documents
just written, per `c4-templates.md#eli5-companion`, and add the
`[Plain-language version](./eli5.md)` line to `context.md`. It reuses the
rendered `.png` files, so it comes after Step 3.

### Step 6: Confirm

```bash
find codemap -type f | sort
```

### Step 7: Export (with `--export <dir>`)

Only when every spec rendered `ok` and validation passed: copy the model to
`<dir>/<system-id>/` per `c4-templates.md#export`. A failed run exports
nothing.

---

## Output Summary

```markdown
# C4 Mapping Complete

## System: <system-id>

## Structure Generated
- System context and container diagrams: 2
- Containers: X containers (component diagram each)
- Components: Y components
- Not containers (libraries, packages, buses): [list, and where they are described]

## Files Created
- Total files: N (specs: X, markdown: Y, rendered: Z)

## Diagram Checks
- Renderer: all ok / N failures
- C4 lint: all ok / violations by rule id (e.g. `N3 x2, L5 x1`)
- Review findings and warnings: [rule id and file each; budget, missing icons, ...]

## Entry Point
`codemap/<system-id>/context.md`

## Optional Outputs
- Plain-language companion: `codemap/<system-id>/eli5.md` / not requested
- Export: `<dir>/<system-id>/` (N files) / not requested

## Validation
- Status: PASSED/FAILED
- Issues: [list if any]
```

If any phase fails, report it and do not proceed to dependent phases.
