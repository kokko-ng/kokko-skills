---
name: security
description: Run security analysis and fix findings with ruff's bandit rules or bandit (Python), eslint-plugin-security plus npm audit (JavaScript/TypeScript), or SecurityCodeScan (.NET). Use when the user asks for a security scan, a vulnerability audit, or fixes for insecure patterns and vulnerable dependencies. Trigger on "security scan", "vulnerabilities", "bandit", "npm audit", or "CVE".
argument-hint: '[py|js|dotnet] [--report]'
---

# Security Analysis Skill

Detect and fix security vulnerabilities with the language's security
analyzer.

Languages present: !`bash "${CLAUDE_PLUGIN_ROOT}/scripts/detect-langs.sh" "${CLAUDE_PROJECT_DIR}"`

Follow `${CLAUDE_PLUGIN_ROOT}/references/check-workflow.md` (arguments,
tool selection, run-classify-fix loop, commits, report) with these deltas:

| Delta | Value |
| ----- | ----- |
| Tools | py: ruff `--select S` when ruff is configured, else `uvx bandit`; js: eslint-plugin-security when configured plus `npm audit`; dotnet: `dotnet list package --vulnerable` plus the security analyzers the solution references |
| Reference | `references/py-security.md`, `references/js-security.md`, `references/dotnet-security.md` |
| Classify | TRUE_POSITIVE: fix now. NEEDS_REFACTOR: build the safer abstraction first, then fix. FALSE_POSITIVE: suppress narrowly with a written justification. ACCEPT_RISK: record the rationale in the report |
| Priority | High, then Medium, then Low |
| Commit | `fix(security): mitigate <issue> in <file>` (`fix` is the Conventional Commits type; `security` is not one) |
| Done when | zero high findings; every medium finding fixed or documented; no suppression without a justification |
