# kokko-code-quality

Analysis skills (technical debt, performance, whole-codebase review, specs,
cruft, dependencies) and the six check skills that fix one quality
dimension each across Python, JavaScript/TypeScript, and .NET.

```bash
/plugin install kokko-code-quality@kokko-ng-kokko-cmds
```

## Skills

<!-- generated:skills start -->

| Skill | Purpose |
| ----- | ------- |
| `/architecture [py\|js] [--report]` | Enforce architectural layering and import rules with import-linter (Python) or dependency-cruiser (JavaScript/TypeScript) |
| `/audit [target]` | Perform a direct, no-nonsense code review with a clear merge verdict |
| `/check` | Run pre-commit until it passes, fixing every issue without skipping hooks |
| `/complexity [py\|js\|dotnet] [--report]` | Measure and reduce code complexity with ruff's mccabe rule or radon (Python), ESLint complexity rules (JavaScript/TypeScript), or .NET analyzers |
| `/cruft [dry-run\|auto\|gitignore-only\|<pattern>]` † | Find and remove repository cruft not covered by .gitignore, with confirmation |
| `/deadcode [py\|js\|dotnet] [--report]` | Detect and remove dead code with vulture and ruff (Python), knip (JavaScript/TypeScript), or .NET analyzers |
| `/debt [target]` | Deep-read a target to identify technical debt and build a remediation roadmap |
| `/deps-update [package\|critical\|major\|minor]` † | Interactively update outdated dependencies with validation between each |
| `/docs [py\|js\|dotnet] [--report]` | Check and improve documentation coverage with ruff's pydocstyle rules or interrogate (Python), eslint-plugin-jsdoc (JavaScript/TypeScript), or XML doc comments (.NET) |
| `/emojis [target]` † | Remove emojis from source files while preserving code functionality |
| `/perf [target] [--focus database\|api\|frontend\|backend\|memory]` | Identify performance bottlenecks across a target and recommend prioritized fixes |
| `/security [py\|js\|dotnet] [--report]` | Run security analysis and fix findings with ruff's bandit rules or bandit (Python), eslint-plugin-security plus npm audit (JavaScript/TypeScript), or SecurityCodeScan (.NET) |
| `/spec [target] [--output filename]` | Generate a test specification documenting all testable user stories |
| `/types [py\|js\|dotnet] [--report]` | Strengthen type safety with mypy or pyright (Python), tsc (TypeScript), or nullable reference analyzers (.NET) |
| `/verify-no-mocks [target]` | Scan production code for mock/stub/dummy data and unconfigured integrations |
| `/verify-spec [spec-file]` | Validate a spec.md for structure, completeness, and alignment with the codebase |

† user-invoked only (`disable-model-invocation`) · ‡ runs forked, reports a summary

<!-- generated:skills end -->

Claude Code ships a built-in `/review` (pull-request review); the
whole-codebase review here is `/audit` so the two never collide. Module
splitting is the janitor's `design` skill (metric evidence, judge panel,
apply gates), not a skill here.

## The check skills

`security`, `types`, `complexity`, `deadcode`, `docs`, and `architecture`
share one workflow, `references/check-workflow.md`; each SKILL.md is the
table of what differs (tools per language, how findings are classified,
the commit format, the definition of done). Language detection is one
script, `scripts/detect-langs.sh`, run through inline preprocessing.

- **Use what the repo has.** A check never adds a dependency to the
  project. It uses the tool the repo already configures, then ruff's rule
  families when ruff is configured (`S`, `C901`, `F401`/`ARG`, `D`), and
  otherwise runs the specialist tool ephemerally (`uvx bandit`,
  `npx --yes knip`). A tool worth keeping is proposed in the report.
- **`--report`** runs the analyzer and reports classified findings without
  editing, committing, or installing anything. The janitor's `--dry-run`
  relies on it.
- **`.kokko.json`** at the repo root can pin `languages`, `excludes`, and a
  preferred tool per language and check (`tools.py.security: "ruff"`).
  Flags win over the file.
- **Clean is a result.** A check that finds nothing reports clean and
  commits nothing; it never relaxes configuration to manufacture work.

The janitor (kokko-janitor-skill) runs all six in parallel git worktrees
and merges the results.
