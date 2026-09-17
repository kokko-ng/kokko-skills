---
name: complexity
description: Measure and reduce code complexity with ruff's mccabe rule or radon (Python), ESLint complexity rules (JavaScript/TypeScript), or .NET analyzers. Use when the user asks to find overly complex code, lower cyclomatic complexity, or refactor tangled functions. Trigger on "complexity", "cyclomatic", "too complex", or "simplify this module".
argument-hint: '[py|js|dotnet] [--report]'
---

# Complexity Analysis Skill

Identify high-complexity code and refactor it safely.

Languages present: !`bash "${CLAUDE_PLUGIN_ROOT}/scripts/detect-langs.sh" "${CLAUDE_PROJECT_DIR}"`

Follow `${CLAUDE_PLUGIN_ROOT}/references/check-workflow.md` (arguments,
tool selection, run-classify-fix loop, commits, report) with these deltas:

| Delta | Value |
| ----- | ----- |
| Tools | py: ruff `--select C901,PLR09` when ruff is configured, plus `uvx radon` for grades and the maintainability index; js: the ESLint `complexity` rule; dotnet: the analyzers the solution references |
| Reference | `references/py-complexity.md`, `references/js-complexity.md`, `references/dotnet-complexity.md` |
| Classify | a finding is a function above the reference's threshold; nothing is suppressed, it is refactored or left with a reason |
| Priority | worst grade first, then change frequency (git history), then business criticality |
| Tactics | extract function, guard clauses, dictionary or object dispatch, decompose conditionals; one tactic per commit, and the reference lists more |
| Commit | `refactor(complexity): reduce complexity in <symbol>` |
| Done when | no function above the threshold; further change would be churn |
