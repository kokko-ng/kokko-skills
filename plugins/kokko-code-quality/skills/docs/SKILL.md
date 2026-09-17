---
name: docs
description: Check and improve documentation coverage with ruff's pydocstyle rules or interrogate (Python), eslint-plugin-jsdoc (JavaScript/TypeScript), or XML doc comments (.NET). Use when the user asks to add docstrings, audit doc coverage, or fix docstring formatting. Trigger on "docstrings", "documentation coverage", "jsdoc", or "xml docs".
argument-hint: '[py|js|dotnet] [--report]'
---

# Documentation Coverage Skill

Ensure every public API has documentation in the language's convention.

Languages present: !`bash "${CLAUDE_PLUGIN_ROOT}/scripts/detect-langs.sh" "${CLAUDE_PROJECT_DIR}"`

Follow `${CLAUDE_PLUGIN_ROOT}/references/check-workflow.md` (arguments,
tool selection, run-classify-fix loop, commits, report) with these deltas:

| Delta | Value |
| ----- | ----- |
| Tools | py: ruff `--select D` with the Google convention when ruff is configured, else `uvx interrogate` plus `uvx pydocstyle`; js: eslint-plugin-jsdoc when configured (otherwise propose it and audit public exports by hand); dotnet: `CS1591` warnings through `dotnet build` |
| Reference | `references/py-docs.md` (Google style), `references/js-docs.md` (JSDoc), `references/dotnet-docs.md` (XML) |
| Classify | a finding is a public symbol without documentation, or a docstring that breaks the convention; both are fixed, never suppressed |
| Priority | public API first, then complex functions, entry points, utilities, private symbols last |
| Commit | `docs(<module>): add docs to <file>` |
| Done when | 100% coverage on public APIs, zero style violations, one consistent format per language |
