---
name: architecture
description: Enforce architectural layering and import rules with import-linter (Python) or dependency-cruiser (JavaScript/TypeScript). Use when the user asks to enforce architecture, check layering, define import contracts, or fix dependency-direction violations. Trigger on "architecture check", "layer violations", "import rules", "import-linter", or "dependency-cruiser".
argument-hint: '[py|js] [--report]'
---

# Architecture Enforcement Skill

Detect and fix architectural violations (dependency direction, coupling,
cycles, layering) with a contract-based analyzer. Python and
JavaScript/TypeScript only: if .NET is requested or detected, say it is not
supported here and continue with the supported languages.

Languages present: !`bash "${CLAUDE_PLUGIN_ROOT}/scripts/detect-langs.sh" "${CLAUDE_PROJECT_DIR}"`

Follow `${CLAUDE_PLUGIN_ROOT}/references/check-workflow.md` (arguments,
tool selection, run-classify-fix loop, commits, report) with these deltas:

| Delta | Value |
| ----- | ----- |
| Tools | py: import-linter (`uvx --from import-linter lint-imports` when not installed); js: dependency-cruiser (`npx --yes -p dependency-cruiser depcruise` when not installed) |
| Reference | `references/py-architecture.md`, `references/js-architecture.md` |
| Config | the contract file is the deliverable of this check: when none exists, bootstrap one from the reference after reading the real package layout, and say in the report that it was created |
| Classify | CYCLE: extract the shared module or introduce an interface. FORBIDDEN_IMPORT: move the import to an allowed layer or restructure. LAYER_VIOLATION: invert the dependency or introduce an abstraction. COUPLING: extract shared types |
| Priority | cycles first, then layer breaches, then forbidden imports |
| Commit | `refactor(architecture): <description>` |
| Done when | zero violations from the analyzer; no circular dependencies; every layer boundary enforced |
