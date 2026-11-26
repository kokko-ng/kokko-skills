---
name: c4-update
description: Update an existing C4 model to match current code changes. Use when the user asks to bring a codemap or its C4 diagrams up to date, optionally adding a plain-language version or copying the result to a notes vault.
argument-hint: '[system-id] [--eli5] [--export <dir>]'
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

RENDERER: the model vendors its own copy at `codemap/.insight-c4/render.py`
(see `c4-templates.md#rendering`). Refresh it from the plugin before use:
!`echo "cp ${CLAUDE_PLUGIN_ROOT}/skills/c4/assets/insight-c4/*.py codemap/.insight-c4/"`

Read the relevant section yourself whenever a step cites a
`c4-templates.md#...` or `insight-diagrams.md#...` anchor.

Diagrams are Insight-branded and generated from `<level>.c4.json` specs by
the renderer. Edit the spec, never the `.html`, `.svg` or `.png`. If the
model still holds `.puml` files, this run converts them — see
`c4-templates.md#migrating-a-plantuml-codemap` — and deletes them. A spec
without `"schema": 2` no longer renders: every spec this run touches is
upgraded per `insight-diagrams.md#upgrading-a-schema-1-spec`, and a model
with no `containers.c4.json` gains one (`c4-templates.md#output-structure`).

Every spec written or edited follows the C4 labelling semantics in
`insight-diagrams.md#c4-semantics`: element `type`, `technology` and
one-sentence `description`, verb-phrase relationship `label` with its
`technology`, the boundaries the level's scope requires, and the same
wording for an element or relationship on every diagram it appears on. A
new dependency on a shared library is not a new container.

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

The system to update is `$0`, unless `$0` starts with `--`: the flags
`--eli5` and `--export <dir>` (rule 7 of the `c4` skill) may appear anywhere
in `$ARGUMENTS` and are not a system id. If a system id was given, use it as
`SYSTEM_ID` and verify `codemap/<SYSTEM_ID>/` exists — report the error and
stop if it does not. With no system id:

```bash
ls codemap/
```

- Exactly one entry → that is `SYSTEM_ID`.
- More than one → stop and list the systems, and say the run must be
  repeated with the system id as the argument. Never guess by taking the
  first.

Each Bash call starts a fresh shell, so `$SYSTEM_ID` set in one command is
empty in the next: write the resolved id into every command below that uses
it.

```bash
echo "System ID: $SYSTEM_ID"
find codemap/$SYSTEM_ID -type f \( -name "*.md" -o -name "*.c4.json" -o -name "*.puml" \) | sort
```

### Step 1B: Analyze Changes

The baseline is the last commit that touched `codemap/`:

```bash
LAST_UPDATE=$(git log -1 --format="%H" -- codemap/)
if [ -n "$LAST_UPDATE" ]; then
  git diff --name-status "$LAST_UPDATE"..HEAD -- . ':!codemap' ':!*.md'
else
  echo "no baseline: codemap/ has never been committed"
  git ls-files -- . ':!codemap' ':!*.md'
fi
```

Pass the whole list to Step 1C; do not truncate it. When it is long, group
it by top-level directory in the brief rather than dropping entries. With no
baseline, every tracked file is a candidate, so Step 1C compares the existing
model against the current code instead of against a diff.

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

Order the Phase 1 `CHANGES` into an execution plan yourself, by the update
order above: the order follows from each change's type and level, so it
needs no agent. Operations on the same level are independent and can run as
parallel agents in Phase 3.

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
    order keeps the diff on the diagram readable. Every element and edge you
    add or change carries its full C4 label (insight-diagrams.md#c4-semantics);
    when you rename or relabel an element or relationship, list every other
    spec it appears in so they are changed to match (rules X1, X3).
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
    1. Container-System: Folders match containers.md table entries
    2. Component-Container: Folders match container.md table entries
    3. Navigation: All links resolve to existing files
    4. IDs: No duplicates, valid folder names
    5. C4 rules: run
       python3 codemap/.insight-c4/render.py 'codemap/<SYSTEM_ID>/**/*.c4.json' --check
       and record every finding with its rule id (N3, L5, X1, ...)

    OUTPUT:
    {
      "CONSISTENCY_PASSED": true/false,
      "ISSUES": [...],
      "C4_VIOLATIONS": [{"file": "...", "rule": "N3", "severity": "error|review", "message": "..."}],
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
   python3 codemap/.insight-c4/render.py <each modified .c4.json> --png
   python3 codemap/.insight-c4/render.py 'codemap/**/*.c4.json' --check
   python3 codemap/.insight-c4/lint.py 'codemap/**/*.svg'
   ```

   Every spec and every SVG must report `ok`. A `FAIL (C4 rules)` or a lint
   finding is fixed in the spec from the code, by the rule it names; a
   `FAIL (layout)` by reordering rows; never by editing the rendered output.
   The `--check` run covers the whole model so the cross-diagram rules
   (X1-X3) see every diagram.

4. **Update README:** Update `codemap/README.md` with timestamp and change
   summary.

5. **Source links:** any `.md` touched must hyperlink every source file or
   code element it names to the actual file, per
   `c4-templates.md#source-file-links` (repo-relative, resolves on GitHub).
   Fix bare-text file references in the sections you touch.

6. **Plain-language companion:** when `codemap/<SYSTEM_ID>/eli5.md` exists,
   or `--eli5` was given, bring it in line with the updated model per
   `c4-templates.md#eli5-companion`: parts added or removed, flows that
   changed, the timestamp. A model that changed while its companion did not
   is an inconsistency this run must not leave behind.

7. **Export:** with `--export <dir>`, and only when verification passed,
   copy the model to `<dir>/<SYSTEM_ID>/` per `c4-templates.md#export`.

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

## Optional Outputs
- Plain-language companion: updated / created / none
- Export: `<dir>/<system-id>/` / not requested

## Verification: PASSED/FAILED
- C4 rules: all ok / violations by rule id and file
- Review findings: [rule id and file each]
```

On subagent failure, report which update failed and skip dependent updates.
