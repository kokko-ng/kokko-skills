---
name: c4-update
description: Update an existing C4 model to match current code changes.
argument-hint: '[system-id]'
allowed-tools: Agent, Bash, Read, Write, Glob, Grep
context: fork
background: false
---

# C4 Architecture Update

Update the existing hierarchical C4 model in `codemap/<system-id>/` based on
code changes. If no model exists, run `/kokko-viz:c4-map` first.

**Read the `c4` skill first:** `${CLAUDE_PLUGIN_ROOT}/skills/c4/SKILL.md`. It
holds the authoring rules every touched document must follow — mandatory
source-file hyperlinks and the ban on validation report files.

TEMPLATES (paste this absolute path into every brief):
!`echo "${CLAUDE_PLUGIN_ROOT}/skills/c4/references/c4-templates.md"`

DIAGRAMS (paste this one too):
!`echo "${CLAUDE_PLUGIN_ROOT}/skills/c4/references/insight-diagrams.md"`

RENDERER:
!`echo "${CLAUDE_PLUGIN_ROOT}/skills/c4/assets/insight-c4/render.py"`

Read the relevant section yourself whenever a step cites a
`c4-templates.md#...` or `insight-diagrams.md#...` anchor.

Diagrams are Insight-branded and generated from `<level>.c4.json` specs by
the renderer. Edit the spec, never the `.html`, `.svg` or `.png`. If the
model still holds `.puml` files, this run converts them — see
`c4-templates.md#migrating-a-plantuml-codemap` — and deletes them.

This skill runs forked: phase output stays here and the caller receives the
summary. Nobody can answer a question mid-run, so report and stop instead
of asking. Analysis and editing phases are `kokko-viz:c4-mapper` agents
(the `c4` skill preloaded, templates read from the TEMPLATES path in the
brief); mechanical checks are `kokko-viz:c4-checker` agents (read-only,
small model). Spawn both by name with the Agent tool; their model and
effort come from their own frontmatter.

## Orchestration

```text
Phase 1: Detect Changes -> Phase 2: Plan Updates -> Phase 3: Apply ->
Phase 4: Verify -> Phase 5: Finalize
```

Update order:

- Deletions: Component -> Container -> Context (bottom-up)
- Additions: Context -> Container -> Component (top-down)
- Modifications: Affected level + adjacent levels

---

## Phase 1: Change Detection

### Step 1A: Identify System

The system to update is `$1`. If an argument was given, use it as
`SYSTEM_ID` and verify `codemap/<SYSTEM_ID>/` exists — report the error and
stop if it does not. With no argument:

```bash
ls codemap/
```

- Exactly one entry → that is `SYSTEM_ID`.
- More than one → stop and list the systems, and say the run must be
  repeated with the system id as the argument. Never guess by taking the
  first.

```bash
echo "System ID: $SYSTEM_ID"
find codemap/$SYSTEM_ID -type f \( -name "*.md" -o -name "*.c4.json" -o -name "*.puml" \) | sort
```

### Step 1B: Analyze Changes

```bash
LAST_UPDATE=$(git log -1 --format="%H" -- codemap/)
git diff --name-status $LAST_UPDATE..HEAD -- . ':!codemap' ':!*.md' | head -50
```

### Step 1C: Categorize Changes

```yaml
Tool: Agent
Parameters:
  subagent_type: "kokko-viz:c4-mapper"
  description: "Detect C4 changes"
  prompt: |
    Analyze code changes and categorize by C4 level.

    TEMPLATES: <absolute path from above>
    EXISTING HIERARCHY: <from Step 1A>
    CHANGED FILES: <from Step 1B>

    GOALS:
    For each changed file:
    1. Determine C4 LEVEL: CONTEXT|CONTAINER|COMPONENT
    2. Determine CHANGE TYPE: ADDITION|DELETION|MODIFICATION|RENAME
    3. Identify CASCADE effects (parent/child impacts)

    OUTPUT:
    {
      "SYSTEM_ID": "...",
      "CHANGE_SUMMARY": {counts by level},
      "CHANGES": [<changes per c4-templates.md#change-detection-schema>],
      "STRUCTURAL_CHANGES": {
        "new_containers": [], "removed_containers": [],
        "new_components": [], "removed_components": [],
        "renamed_elements": []
      }
    }
```

Wait for Phase 1. If no changes detected, report and exit.

---

## Phase 2: Impact Analysis

```yaml
Tool: Agent
Parameters:
  subagent_type: "kokko-viz:c4-checker"
  description: "Plan C4 updates"
  prompt: |
    Create update execution plan.

    PHASE 1 OUTPUT: <insert>

    PLANNING RULES:
    1. DELETIONS (bottom-up): component -> container -> context
    2. MODIFICATIONS: affected level + adjacent levels
    3. ADDITIONS (top-down): context -> container -> component
    4. PARALLEL: Same-level operations can run in parallel

    OUTPUT:
    {
      "EXECUTION_PLAN": [
        {"step": N, "phase": "...", "depends_on": [], "tasks": [...]}
      ],
      "SUBAGENT_SPAWNS": {"sequential": [], "parallel_safe": []}
    }
```

---

## Phase 3: Apply Updates

### Step 3A: Deletions (Bottom-Up)

```bash
rm -rf <paths from execution plan>  # component -> container order
```

Update navigation links in parent files after deletions.

### Step 3B: Modifications

For each modified element, spawn a level-specific subagent:

```yaml
Tool: Agent
Parameters:
  subagent_type: "kokko-viz:c4-mapper"
  description: "Update C4 <level>"
  prompt: |
    Update <LEVEL> for modifications.

    TEMPLATES: <absolute path from above>
    DIAGRAMS: <absolute path from above>

    ELEMENT: <element-id>
    CURRENT STATE: <read existing .md and .c4.json>
    MODIFICATIONS: <changes from Phase 1>

    GOALS:
    - Update only changed aspects
    - Preserve unchanged content exactly
    - Update navigation if children added/removed
    - Ensure parent links correct

    OUTPUT: Full updated files (the .c4.json spec and the .md). Keep the
    existing row assignment unless the change makes it wrong; a stable row
    order keeps the diff on the diagram readable.
```

### Step 3C: Additions (Top-Down)

For new elements: create folder structure, spawn an analysis subagent
(like c4-map phases), then update the parent's drill-down table.

```bash
# New container
mkdir -p codemap/$SYSTEM_ID/containers/<new-id>/components
# New component
mkdir -p codemap/$SYSTEM_ID/containers/<container>/components/<new-id>
```

---

## Phase 4: Cross-Level Consistency

```yaml
Tool: Agent
Parameters:
  subagent_type: "kokko-viz:c4-checker"
  description: "Verify C4 consistency"
  prompt: |
    Verify cross-level consistency after updates.

    UPDATED FILES: <list>

    CHECKS:
    1. Container-Context: Folders match context.md table entries
    2. Component-Container: Folders match container.md table entries
    3. Navigation: All links resolve to existing files
    4. IDs: No duplicates, valid folder names

    OUTPUT:
    {
      "CONSISTENCY_PASSED": true/false,
      "ISSUES": [...],
      "FIXES_REQUIRED": [{"file": "...", "action": "...", "details": "..."}]
    }
```

---

## Phase 5: Finalization

1. **Apply consistency fixes:** Fix navigation links, remove orphan entries,
   add missing entries.
2. **Update timestamps:** Update `<!-- Last updated: YYYY-MM-DD -->` in
   modified files.
3. **Re-render** every modified diagram, and check the whole model:

   ```bash
   python3 "<RENDERER path from above>" codemap/$SYSTEM_ID/context.c4.json --png
   python3 "<RENDERER path from above>" 'codemap/**/*.c4.json' --check
   ```

   Every spec must report `ok`. A `FAIL` is fixed in the spec, usually by
   reordering rows, never by editing the rendered output.

4. **Update README:** Update `codemap/README.md` with timestamp and change
   summary.

5. **Source links:** any `.md` touched must hyperlink every source file or
   code element it names to the actual file, per
   `c4-templates.md#source-file-links` (repo-relative, resolves on GitHub).
   Fix bare-text file references in the sections you touch.

---

## Output Summary

```markdown
# C4 Update Complete

## Changes
- Files changed in codebase: X
- C4 levels affected: [list]

## Structural Changes
| Type | Element | Action |
| ---- | ------- | ------ |
| ADDITION | component:oauth | Created folder |
| DELETION | component:legacy | Removed folder |

## Files Modified
- Deletions / Modifications / Additions: [lists]

## Verification: PASSED/FAILED
```

On subagent failure, report which update failed and skip dependent updates.
