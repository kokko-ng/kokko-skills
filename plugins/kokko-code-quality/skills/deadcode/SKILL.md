---
name: deadcode
description: Detect and remove dead code with vulture and ruff (Python), knip (JavaScript/TypeScript), or .NET analyzers. Use when the user asks to find unused code, delete unreachable branches, or clean up unused exports, imports, or dependencies. Trigger on "dead code", "unused code", "unreachable", "vulture", or "knip".
argument-hint: '[py|js|dotnet] [--report]'
---

# Dead Code Detection Skill

Detect unused code and remove it safely.

Languages present: !`bash "${CLAUDE_PLUGIN_ROOT}/scripts/detect-langs.sh" "${CLAUDE_PROJECT_DIR}"`

Follow `${CLAUDE_PLUGIN_ROOT}/references/check-workflow.md` (arguments,
tool selection, run-classify-fix loop, commits, report) with these deltas:

| Delta | Value |
| ----- | ----- |
| Tools | py: `uvx vulture` for unused functions and classes, plus ruff `--select F401,F841,ARG` when ruff is configured; js: knip (`npx --yes knip` when not installed); dotnet: the analyzers the solution references |
| Reference | `references/py-deadcode.md`, `references/js-deadcode.md`, `references/dotnet-deadcode.md` |
| Classify | verify each finding is genuinely unused before touching it: internal references, dynamic imports and reflection, framework conventions (DI, ORM, routes, fixtures), config-based registrations, entry points, plugin systems. Confirmed unused: remove. Reached dynamically: whitelist with a written reason |
| Priority | one finding at a time, never batched |
| Commit | one removal per commit: `chore(cleanup): remove unused <item>` |
| Done when | every finding removed or whitelisted with a justification; the analyzer runs clean |
