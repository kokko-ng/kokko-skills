# Python Complexity Analysis with Radon

## Tool selection

Nothing is installed into the project. In order (see the shared
`references/check-workflow.md`):

1. `[tool.ruff]` configured: `uv run ruff check --select C901,PLR09 .`
   reports functions over the mccabe threshold (10) plus too many branches,
   arguments, and statements, without touching the repo's ruff config.
2. radon already a dev dependency: `uv run radon`.
3. Otherwise `uvx radon`, as below. Ruff has no maintainability index, so
   radon `mi` still runs for that signal.

## Commands

```bash
# Cyclomatic complexity (A=best, F=worst)
uvx radon cc -s -a . --exclude "venv/*,.venv/*"

# Maintainability Index (100=best, 0=worst)
uvx radon mi -s . --exclude "venv/*,.venv/*"

# Halstead metrics (optional, for detailed analysis)
uvx radon hal . --exclude "venv/*,.venv/*"
```

## Thresholds

Target functions/classes with:

- Complexity grade >= C (or numeric > 10)
- Maintainability Index < 65

## Prioritization

Rank by:

1. Worst grade (F, E, D first)
2. Frequency of change (`git log -p --follow <file>`)
3. Business criticality

## Refactor Tactics

Apply one tactic at a time:

- **Extract Function/Method** - Break out cohesive blocks
- **Decompose Conditionals** - Use strategy maps, dict dispatch, guard clauses
- **Remove Duplication** - DRY or inline trivial indirections
- **Simplify Boolean Logic** - Early returns, De Morgan's laws
- **Replace Deep Nesting** - Fail-fast exits, extract methods
- **Clarify Names** - Rename unclear variables/functions
- **Isolate Side Effects** - Separate pure logic from I/O
- **Reduce Parameters** - Introduce dataclass or typed object
- **Split Large Classes** - Single Responsibility Principle

## Validation

After each micro-change:

```bash
uvx radon cc -s <target_file>
uvx radon mi -s <target_file>
```

## Commit Format

```text
refactor(complexity): reduce complexity in <symbol> (C->B)
```

## When to Stop

- Complexity <= B grade
- Maintainability Index >= 70
- Further changes risk unnecessary churn

## Hard Cases

If complexity resists decomposition:

- Introduce a decision table or data-driven structure
- Split algorithm into phases (parse -> transform -> emit)
- Accept temporary adapter layer while migrating callers

## Final Quality Gate

```bash
uvx radon cc -s -a .
uvx radon mi -s .
uv run pre-commit run --all-files   # when the repo has a .pre-commit-config.yaml
```
