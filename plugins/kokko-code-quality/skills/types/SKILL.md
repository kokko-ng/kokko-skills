---
name: types
description: Strengthen type safety with mypy or pyright (Python), tsc (TypeScript), or nullable reference analyzers (.NET). Use when the user asks to add type annotations, fix type errors, or tighten type-checker configuration. Trigger on "type errors", "type annotations", "mypy", "tsc", or "strict null checks".
argument-hint: '[py|js|dotnet] [--report]'
---

# Type Checking Skill

Detect and fix type errors with the language's type checker.

Languages present: !`bash "${CLAUDE_PLUGIN_ROOT}/scripts/detect-langs.sh" "${CLAUDE_PROJECT_DIR}"`

Follow `${CLAUDE_PLUGIN_ROOT}/references/check-workflow.md` (arguments,
tool selection, run-classify-fix loop, commits, report) with these deltas:

| Delta | Value |
| ----- | ----- |
| Tools | py: the checker the repo configures (mypy or pyright), else `uvx mypy`; js: `npx tsc --noEmit` against the project's tsconfig; dotnet: nullable reference analyzers through `dotnet build` |
| Reference | `references/py-types.md`, `references/js-types.md`, `references/dotnet-types.md` |
| Classify | every error is fixed by making the code satisfy the checker, grouped by error code; `Any`, `any`, `object`, and `dynamic` only where unavoidable, scoped narrowly, with a comment saying why |
| Priority | errors that hide other errors first (missing imports, wrong signatures), then by file |
| Commit | `fix(types): resolve <error_code> in <file>` |
| Done when | zero errors with strict settings; annotations accurate; no type escape without a documented justification |
