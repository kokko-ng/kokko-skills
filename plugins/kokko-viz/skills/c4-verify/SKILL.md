---
name: c4-verify
description: Verify C4 diagrams against the codebase and auto-fix discrepancies.
argument-hint: '[system-id]'
allowed-tools: Agent, Bash, Read, Write, Glob, Grep
context: fork
background: false
---

# C4 Architecture Verification

Validate accuracy and completeness of the C4 map in `codemap/<system-id>/`
against the actual codebase, then apply fixes. Run `/kokko-viz:c4-map` first if
no model exists.

**Read the `c4` skill first:** `${CLAUDE_PLUGIN_ROOT}/skills/c4/SKILL.md`. Its
authoring rules are what this command verifies against — mandatory source-file
hyperlinks and the ban on validation report files.

TEMPLATES (paste this absolute path into every brief):
!`echo "${CLAUDE_PLUGIN_ROOT}/skills/c4/references/c4-templates.md"`

DIAGRAMS (paste this one too):
!`echo "${CLAUDE_PLUGIN_ROOT}/skills/c4/references/insight-diagrams.md"`

RENDERER: the model vendors its own copy at `codemap/.insight-c4/render.py`
(see `c4-templates.md#rendering`). Refresh it from the plugin before use:
!`echo "cp ${CLAUDE_PLUGIN_ROOT}/skills/c4/assets/insight-c4/*.py codemap/.insight-c4/"`

Read the relevant section yourself whenever a check cites a
`c4-templates.md#...` or `insight-diagrams.md#...` anchor.

Diagrams are Insight-branded and generated from `<level>.c4.json` specs.
A `.puml` or a `.c4-plantuml/` directory under `codemap/` is a migration
leftover: convert it per `c4-templates.md#migrating-a-plantuml-codemap` and
delete it. That conversion is a structural fix, so it runs in Phase 4A.

This skill runs forked: check output stays here and the caller receives the
summary. Nobody can answer a question mid-run, so report and stop instead
of asking. Judgment checks, synthesis, and edits are `kokko-viz:c4-mapper`
agents (the `c4` skill preloaded, templates read from the TEMPLATES path in
the brief); mechanical re-checks are `kokko-viz:c4-checker` agents
(read-only, small model). Spawn both by name with the Agent tool; their
model and effort come from their own frontmatter.

## Orchestration

```text
Phase 1: Prep -> Phase 2: Parallel Verification (5 checks) -> Phase 3: Synthesis
-> Phase 4: Apply Fixes -> Phase 5: Re-Verify -> Phase 6: Finalize
```

---

## Phase 1: Preparation

The system to verify is `$1`. If an argument was given, use it as
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
find codemap/$SYSTEM_ID -type f \
  \( -name "*.md" -o -name "*.c4.json" -o -name "*.png" -o -name "*.html" \
     -o -name "*.svg" -o -name "*.puml" \) | sort
```

---

## Phase 2: Parallel Verification

Checks 1-4 need judgment: launch them as four parallel
`kokko-viz:c4-mapper` agents in a single message. Each receives
`SYSTEM_ID`, the Phase 1 file listing, and the TEMPLATES path, and outputs
JSON with `check_type`, a score, `findings`, and `issues` (per
c4-templates.md#validation-issue-schema, which the agent reads itself).

**1. Completeness** (`score: X/3`): All deployable units have folders; all
major modules documented; all integrations in context.c4.json.
Search: Glob `**/Dockerfile`, `**/docker-compose.yml`; Grep `class \w+`,
`import.*azure`.

**2. Accuracy** (`score: X% verified`): Documented deps match code imports;
tech labels match pyproject.toml/package.json; elements in correct parent
folders; names match actual module/class names; every `href` on a spec node
points at a path that exists.
Search: read the `edges` in each `.c4.json`, Grep imports, verify file paths
exist. An edge with no import, call or config behind it is an issue, and so
is an import path the diagram does not show.

**3. Hierarchy** (`score: X/5`): Each level has a .c4.json + .md; no orphans/empty
containers; diagram elements match folders; navigation links resolve; folder
names match diagram IDs; every source file or code element named in a `.md`
is a hyperlink to the actual file that resolves on GitHub (per
`c4-templates.md#source-file-links`) — bare-text file references are issues.

**4. Diagram Quality** (`score: X/5`): every level has a `<level>.c4.json`
that the renderer accepts; node `kind` matches the C4 element per
`insight-diagrams.md#c4-to-insight`; every Azure or Fabric node carries its
official icon and no other node carries one; exactly one `focal` node, two at
the most; within budget (16 nodes, 24 edges, 3 zones) and not sparse; no
orphan nodes. Run the renderer's own checks as part of this:

```bash
python3 codemap/.insight-c4/render.py 'codemap/'"$SYSTEM_ID"'/**/*.c4.json' --check
```

**5. Render Pairing** is deterministic, so run it yourself rather than
spawning a subagent. Each level's `.md` pairs with a same-named spec and
three rendered files, every rendered file has a spec behind it, and a
rendered file is stale when its spec is newer:

```bash
cd codemap/$SYSTEM_ID
find . -name "*.md" | while read -r md; do
  b="${md%.md}"
  for ext in c4.json html svg png; do [ -f "$b.$ext" ] || echo "missing: $b.$ext"; done
done
for ext in html svg png; do
  find . -name "*.$ext" | while read -r f; do
    [ -f "${f%.$ext}.c4.json" ] || echo "orphan: $f"
  done
done
find . -name "*.c4.json" | while read -r spec; do
  b="${spec%.c4.json}"
  for ext in html svg png; do
    [ -f "$b.$ext" ] && [ "$spec" -nt "$b.$ext" ] && echo "stale: $b.$ext"
  done
done
find . -name "*.puml" -o -name ".c4-plantuml" | sed 's/^/plantuml_leftover: /'
cd - >/dev/null
```

Record its output as the fifth check's findings (`missing`, `orphan`,
`stale`, `plantuml_leftover`). On a fresh clone every file looks stale by
mtime, so confirm against commit dates before acting.

Wait for all four agents to complete.

---

## Phase 3: Synthesis

```yaml
Tool: Agent
Parameters:
  subagent_type: "kokko-viz:c4-mapper"
  description: "Synthesize verification"
  prompt: |
    Synthesize findings from all five verification checks.

    TEMPLATES: <absolute path from above>

    OUTPUTS:
    - Completeness / Accuracy / Hierarchy / Diagram Quality / Render Pairing: <insert each>

    GOALS:
    1. INTERSECTIONS: same issue from multiple checks = higher confidence
    2. CONFLICTS: contradictory findings
    3. ROOT CAUSE: multiple issues from one cause
    4. PRIORITIZE: severity, frequency, cascade impact, structural first

    FIX ORDER: structural (folders, PlantUML conversion) -> diagrams
    (.c4.json specs) -> docs (md) -> navigation (links) -> renders

    OUTPUT:
    {
      "synthesis_summary": {total_issues, intersections, conflicts, root_causes},
      "intersections": [...], "conflicts": [...], "root_causes": [...],
      "prioritized_issues": [...],
      "correction_plan": {
        "phase_1_structural": [...], "phase_2_diagrams": [...],
        "phase_3_documentation": [...], "phase_4_navigation": [...],
        "phase_5_renders": [...]
      }
    }
```

---

## Phase 4: Apply Fixes

Execute `correction_plan` in order.

**4A. Structural:** `mkdir -p <paths>` for missing folders; `rm -rf <paths>`
for orphans. Convert any `.puml` to a `<level>.c4.json` per
`c4-templates.md#migrating-a-plantuml-codemap`, then delete the `.puml` and
the `.c4-plantuml/` directory — never leave both formats in the tree.

**4B. Diagrams:** for each fix, spawn a `kokko-viz:c4-mapper` agent given
the file path, current content, the TEMPLATES path, and the fixes from the
plan; it returns the complete updated file.

**4C. Documentation:** for missing docs, spawn a `kokko-viz:c4-mapper`
agent (like a c4-map phase); for link fixes, edit markdown directly.

**4D. Navigation:** fix broken links and drill-down tables.

**4E. Renders:** regenerate every stale or missing output:

```bash
python3 codemap/.insight-c4/render.py 'codemap/'"$SYSTEM_ID"'/**/*.c4.json' --png
```

---

## Phase 5: Re-Verification

```yaml
Tool: Agent
Parameters:
  subagent_type: "kokko-viz:c4-checker"
  description: "Re-verify fixes"
  prompt: |
    Verify fixes were applied correctly.

    FIXES APPLIED: <list>

    CHECKS:
    1. Structural: folders exist, required files present
    2. Diagrams: every .c4.json parses and the renderer reports ok
    3. Navigation: links resolve
    4. Renders: html/svg/png exist for every spec and are not stale

    OUTPUT:
    {
      "verification_passed": true/false,
      "fixes_confirmed": [...], "fixes_failed": [...],
      "overall_status": "PASS|PARTIAL|FAIL"
    }
```

---

## Phase 6: Finalization

**6A. Re-render the whole model, and let the renderer's checks run:**

```bash
python3 codemap/.insight-c4/render.py 'codemap/**/*.c4.json' --png
```

**6B. Report the results IN YOUR REPLY — do NOT write a verification
document.** Never create `VERIFICATION.md`, a report file, or any other
validation artifact in the repo. Deliver the summary as a message:

```markdown
## C4 Verification

| Metric | Value |
| ------ | ----- |
| Completeness | X/3 |
| Accuracy | X% |
| Hierarchy | X/5 |
| Diagram Quality | X/5 |
| Render Pairing | X missing, Y stale |
| Issues Found / Fixed | N / M |

Corrections applied: [list by phase]
Remaining issues: [list any unfixed]
```

**6C.** Update `codemap/README.md` with the verification timestamp (this is
the only file 6B–6C may touch).

---

## Output Summary

```markdown
# C4 Verification Complete

## Status: PASS/PARTIAL/FAIL

## Scores
- Completeness: X/3 | Accuracy: X% | Hierarchy: X/5 | Diagram Quality: X/5
- Render Pairing: X missing, Y stale, Z orphan

## Synthesis
- Issues found: X | Intersections: Y | Root causes: Z

## Fixes Applied
- Structural / Diagrams / Documentation / Navigation / Renders: [counts]
```

Notes: on agent failure, continue other checks and note incomplete
verification; list irreconcilable conflicts for human decision; on fix failure,
continue independent fixes and report partial success.
