---
name: c4-verify
description: Verify C4 diagrams against the codebase and auto-fix discrepancies.
argument-hint: '[system-id] [--eli5] [--export <dir>]'
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
A `.puml` under `codemap/`, or the `codemap/.c4-plantuml/` library, is a
migration leftover: convert it per `c4-templates.md#migrating-a-plantuml-codemap` and
delete it. A `.c4.json` without `"schema": 2` is a schema 1 spec the
renderer refuses: upgrade it per
`insight-diagrams.md#upgrading-a-schema-1-spec`. A model with no
`containers.c4.json` is missing its Container diagram. All three are
structural fixes, so they run in Phase 4A.

What this skill verifies the diagrams against is the C4 labelling semantics
(rule 5 of the `c4` skill, `insight-diagrams.md#c4-semantics`) and the 36
C4 lint rules (`insight-diagrams.md#lint-rules`). Every diagram finding is
reported with its rule id; `n/a` rules (L7, S2, S5, S6) belong to diagram
types this skill does not draw.

This skill runs forked: check output stays here and the caller receives the
summary. Nobody can answer a question mid-run, so report and stop instead
of asking. Judgment checks, synthesis, and edits are `kokko-viz:c4-mapper`
agents (the `c4` skill preloaded, templates read from the TEMPLATES path in
the brief); mechanical re-checks are `kokko-viz:c4-checker` agents
(read-only, small model). Spawn both by name with the Agent tool; their
model and effort come from their own frontmatter.

## Orchestration

```text
Phase 1: Prep -> Phase 2: Parallel Verification (6 checks) -> Phase 3: Synthesis
-> Phase 4: Apply Fixes -> Phase 5: Re-Verify -> Phase 6: Finalize
```

---

## Phase 1: Preparation

The system to verify is `$0`, unless `$0` starts with `--`: the flags
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

**2. Accuracy** (`score: X% verified`): Documented deps match code imports;
tech labels match pyproject.toml/package.json; elements in correct parent
folders; names match actual module/class names; every `href` on a spec node
points at a path that exists.
Search: read the `edges` in each `.c4.json`, Grep imports, verify file paths
exist. An edge with no import, call or config behind it is an issue, and so
is an import path the diagram does not show.

**3. Hierarchy** (`score: X/6`): Each level has a .c4.json + .md; no orphans/empty
containers; diagram elements match folders; navigation links resolve; folder
names match diagram IDs; every source file or code element named in a `.md`
is a hyperlink to the actual file that resolves on GitHub (per
`c4-templates.md#source-file-links`) — bare-text file references are issues.

**4. Diagram Quality** (`score: X/6`), the judgment half of the C4 rules
(`insight-diagrams.md#checks-the-renderer-cannot-make`): every element is at
the right level of abstraction (no library, package, folder or team drawn
as a container or component; data stores drawn as containers); `type`,
`external` and `store` match the code and its ownership; every
`technology` matches the manifests and infrastructure; every relationship
label starts with a verb and matches the arrow's direction; every Azure or
Fabric node carries its official icon and no other node carries one; within
budget (16 nodes, 24 edges, 3 boundaries) and not sparse. Report each
finding with the rule id it falls under (S7, N7, N3, L3, ...).

**5. Render Pairing** is deterministic, so run it yourself rather than
spawning a subagent.

**6. C4 Rules** is deterministic too, so run it yourself: the renderer's
checks on every spec (including the cross-diagram rules X1-X3, which need
the whole system in one run) and the linter on every rendered SVG:

```bash
python3 codemap/.insight-c4/render.py 'codemap/'"$SYSTEM_ID"'/**/*.c4.json' --check
python3 codemap/.insight-c4/lint.py 'codemap/'"$SYSTEM_ID"'/**/*.svg' --json
```

Record every finding as an issue with `category: "c4_rules"` and its `rule`
id (per `c4-templates.md#validation-issue-schema`), `error` for a failing
finding and `info` for a `review` one. Score it as the number of distinct
rules violated and the number of violations.

For render pairing, each level's `.md` pairs with a same-named spec and
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
find . -name "*.puml" | sed 's/^/plantuml_leftover: /'
find . -name "*.c4.json" -exec grep -L '"schema": *2' {} + | sed 's/^/schema_1: /'
[ -f containers.c4.json ] || echo "missing: ./containers.c4.json"
cd - >/dev/null
ls -d codemap/.c4-plantuml 2>/dev/null | sed 's/^/plantuml_leftover: /'
```

Record its output as the fifth check's findings (`missing`, `orphan`,
`stale`, `plantuml_leftover`, `schema_1`). On a fresh clone every file
looks stale by mtime, so confirm against commit dates before acting.

Wait for all four agents to complete.

---

## Phase 3: Synthesis

```yaml
Tool: Agent
Parameters:
  subagent_type: "kokko-viz:c4-mapper"
  description: "Synthesize verification"
  prompt: |
    Synthesize findings from all six verification checks.

    TEMPLATES: <absolute path from above>

    OUTPUTS:
    - Completeness / Accuracy / Hierarchy / Diagram Quality / Render Pairing /
      C4 Rules: <insert each>

    GOALS:
    1. INTERSECTIONS: same issue from multiple checks = higher confidence
    2. CONFLICTS: contradictory findings
    3. ROOT CAUSE: multiple issues from one cause
    4. PRIORITIZE: severity, frequency, cascade impact, structural first

    FIX ORDER: structural (folders, PlantUML conversion, schema 1 upgrade,
    a missing containers.c4.json) -> diagrams (.c4.json specs, including
    every C4 rule finding, keeping its rule id) -> docs (md) -> navigation
    (links) -> renders

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
the `codemap/.c4-plantuml/` directory — never leave both formats in the tree.
Upgrade every schema 1 spec per
`insight-diagrams.md#upgrading-a-schema-1-spec` (from the code: nothing is
inferred), and write the missing `containers.c4.json` and `containers.md`.

**4B. Diagrams:** for each fix, spawn a `kokko-viz:c4-mapper` agent given
the file path, current content, the TEMPLATES and DIAGRAMS paths, and the
fixes from the plan with their rule ids; it returns the complete updated
file. A rule finding is fixed from the code: the missing technology read
from the manifest, the label rewritten as the verb phrase the code does,
the library removed and its relationship moved to the containers that use
it. A fix to an element or relationship that appears on several diagrams is
applied to every one of them (X1, X3).

**4C. Documentation:** for missing docs, spawn a `kokko-viz:c4-mapper`
agent (like a c4-map phase); for link fixes, edit markdown directly.

**4D. Navigation:** fix broken links and drill-down tables.

**4E. Renders:** regenerate every stale or missing output:

```bash
python3 codemap/.insight-c4/render.py 'codemap/'"$SYSTEM_ID"'/**/*.c4.json' --png
```

---

## Phase 5: Re-Verification

The C4 rule and render checks are deterministic, so run them yourself: the
Phase 2 check-6 commands (every spec reports `ok` from `render.py --check`
and every SVG `ok` from `lint.py`, with no error finding left) and the
check-5 pairing snippet (no `missing`, `orphan`, `stale`,
`plantuml_leftover` or `schema_1` lines). Spawn the checker only for the
structural and navigation checks, which need the markdown read:

```yaml
Tool: Agent
Parameters:
  subagent_type: "kokko-viz:c4-checker"
  description: "Re-verify fixes"
  prompt: |
    Verify fixes were applied correctly.

    FIXES APPLIED: <list>

    CHECKS:
    1. Structural: folders exist, required files present, drill-down
       tables match the folders that exist
    2. Navigation: links resolve

    OUTPUT:
    {
      "verification_passed": true/false,
      "fixes_confirmed": [...], "fixes_failed": [...],
      "overall_status": "PASS|PARTIAL|FAIL"
    }
```

Combine its result with your own two checks: the run passes only when all
three pass. A `review` finding never fails the run but is listed in the
report with its rule id.

---

## Phase 6: Finalization

**6A. Re-render the whole model, and let the renderer's checks run:**

```bash
python3 codemap/.insight-c4/render.py 'codemap/**/*.c4.json' --png
python3 codemap/.insight-c4/lint.py 'codemap/**/*.svg'
```

**6B. Report the results in your reply.** Per rule 2 of the c4 skill, no
`VERIFICATION.md`, report file, or other validation artifact goes into the
repo. Deliver the summary as a message:

```markdown
## C4 Verification

| Metric | Value |
| ------ | ----- |
| Completeness | X/3 |
| Accuracy | X% |
| Hierarchy | X/6 |
| Diagram Quality | X/6 |
| Render Pairing | X missing, Y stale |
| C4 Rules | N violations of R rules found, M fixed |
| Issues Found / Fixed | N / M |

C4 rule violations, by rule id:

| Rule | File | Finding | Status |
| ---- | ---- | ------- | ------ |
| N3 | `containers/api/container.c4.json` | element 'api' states no technology | fixed |

Corrections applied: [list by phase]
Remaining issues: [list any unfixed, each C4 finding with its rule id]
Review findings: [rule id, file, finding]
```

**6C.** Update `codemap/README.md` with the verification timestamp (this is
the only file 6B–6C may touch).

**6D. Plain-language companion.** `codemap/<SYSTEM_ID>/eli5.md` is part of
the model, not an orphan: never delete it as one. When it exists, or
`--eli5` was given, check it against the corrected model per
`c4-templates.md#eli5-companion` (every container present and linked, no
part the model lacks, flows that still match the edges) and rewrite what
is out of step. Count what changed under Documentation in the summary.

**6E. Export.** With `--export <dir>`, and only when the status is PASS or
PARTIAL with no render failures, copy the model to `<dir>/<SYSTEM_ID>/` per
`c4-templates.md#export`. This writes outside the repo and is the one
exception to 6C's limit.

---

## Output Summary

```markdown
# C4 Verification Complete

## Status: PASS/PARTIAL/FAIL

## Scores
- Completeness: X/3 | Accuracy: X% | Hierarchy: X/6 | Diagram Quality: X/6
- Render Pairing: X missing, Y stale, Z orphan
- C4 Rules: N violations found, M fixed, K remaining [rule ids]

## Synthesis
- Issues found: X | Intersections: Y | Root causes: Z

## Fixes Applied
- Structural / Diagrams / Documentation / Navigation / Renders: [counts]
```

Notes: on agent failure, continue other checks and note incomplete
verification; list irreconcilable conflicts for human decision; on fix failure,
continue independent fixes and report partial success.
