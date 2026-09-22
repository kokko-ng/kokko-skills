# kokko-skills

My Claude Code plugin marketplace for day-to-day work.
Install individual plugins or all of them.

## Installation

```bash
/plugin marketplace add kokko-ng/kokko-skills
```

The marketplace ID stays `kokko-ng-kokko-cmds` (the repository was named
kokko-cmds until 2026-09-15), so existing installs and their
`plugin@marketplace` keys keep working unchanged.

Then install the plugins you want:

```bash
/plugin install kokko-notifications@kokko-ng-kokko-cmds
/plugin install kokko-git@kokko-ng-kokko-cmds
/plugin install kokko-validation@kokko-ng-kokko-cmds
/plugin install kokko-code-quality@kokko-ng-kokko-cmds
/plugin install kokko-viz@kokko-ng-kokko-cmds
/plugin install kokko-infra@kokko-ng-kokko-cmds
/plugin install kokko-ai-config@kokko-ng-kokko-cmds
/plugin install kokko-env@kokko-ng-kokko-cmds
```

Everything here is a skill: invoke one as `/name`, or as `/plugin:name`
when a built-in or another plugin claims the same short name. Skills marked
† in the tables below only run when you invoke them; skills marked ‡ run in
a forked context and hand back a summary, so a long orchestration never
fills your conversation.

## Which workflow when

The plugins compose into a few end-to-end flows. The janitor and multipass
live in [kokko-ng/kokko-janitor-skill](https://github.com/kokko-ng/kokko-janitor-skill)
and drive the check skills here by name.

| When | Run | Plugins |
| ---- | --- | ------- |
| Starting a project | `devcontainer-setup` on the host, then `/plugins-update` inside the container | kokko-env |
| Every commit | `/compush`; `/sync` before opening a PR; `/check` when pre-commit is red | kokko-git, kokko-code-quality |
| Before a feature is done | `/spec` writes the stories, `tailor local` writes the validation prompt, `/kokko-janitor:multipass 2 prompts/local-validation.md` runs it to convergence | kokko-code-quality, kokko-validation, kokko-janitor |
| Shipping | `tailor azure-deploy`, then `tailor deployed`, each run through multipass; `/release` when green | kokko-validation, kokko-git |
| Weekly hygiene | `/prune`, `/cruft`, `/deps-update` | kokko-git, kokko-code-quality |
| Deep clean | `/kokko-janitor:janitor --dry-run` to see what would change, `--hold` to fix in worktrees and review the branches, `--resume` to merge | kokko-janitor, kokko-code-quality |
| One check, one language | `/security py`, `/types js`, `/deadcode`, ... (`--report` for findings only) | kokko-code-quality |
| Understanding a codebase | `/audit`, `/debt`, `/perf`, `/c4-map` | kokko-code-quality, kokko-viz |
| Keeping docs honest | `/verify-docs`, `/prune-docs`, `/c4-verify` | kokko-ai-config, kokko-viz |
| Azure | `/az-status`, `/az-costs` | kokko-infra |

## Per-repo configuration

An optional `.kokko.json` at a repository's root steers the check skills
and the janitor without retyping flags. Every key is optional, unknown keys
are ignored, and an explicit flag always wins over the file.

```json
{
  "languages": ["py", "js"],
  "checks": ["security", "types", "complexity", "deadcode", "docs", "architecture"],
  "excludes": ["*/generated/*"],
  "tools": {"py": {"security": "ruff", "docs": "ruff"}},
  "janitor": {"top": 3, "max_rounds": 1, "candidate_loc": 400, "candidate_defs": 30}
}
```

| Key | Read by | Meaning |
| --- | ------- | ------- |
| `languages` | check skills, janitor | Replaces language detection |
| `checks` | janitor | Lint checks to run |
| `excludes` | check skills, hotspot ranker | Extra path globs to skip |
| `tools` | check skills | Preferred tool per language and check |
| `janitor.top`, `janitor.max_rounds` | janitor | Design candidates to judge, convergence rounds |
| `janitor.candidate_loc`, `janitor.candidate_defs` | hotspot ranker | Absolute god-module thresholds |

## Versioning

All eight plugins version in lock-step: every release bumps every plugin (and
every marketplace entry) to the same version, even ones that did not change.
See [CONTRIBUTING.md](CONTRIBUTING.md).

## Environment variables

kokko-notifications plays its sounds through `hooks/utils/play-sound.sh`
and honors:

| Environment Variable | Default | Purpose |
| -------------------- | ------- | ------- |
| `KOKKO_SOUNDS` | `on` | Set to `off` to mute all hook sounds |
| `KOKKO_SOUND_VOLUME` | `1.0` | afplay gain multiplier (macOS); `1.0` = system default |

## Plugins

### kokko-notifications

Sound notifications: a completion chime when a turn ends, and a distinct
attention sound when Claude is waiting on you. See
[plugins/kokko-notifications/README.md](plugins/kokko-notifications/README.md).

| Hook | Purpose |
| ---- | ------- |
| `stop-notification` | Plays the completion sound when Claude finishes a turn |
| `notification` | Plays the attention sound on a permission prompt, a question, or idle waiting |

### kokko-git

Git workflow skills. See [plugins/kokko-git/README.md](plugins/kokko-git/README.md).

<!-- generated:skills:kokko-git start -->

| Skill | Purpose |
| ----- | ------- |
| `/compush [files] [--message "msg"]` † | Stage, commit (Conventional Commits), and push one logical change |
| `/prune [local\|remote\|merged\|<days>]` † | Find and safely delete stale local/remote branches with confirmation |
| `/release [patch\|minor\|major] [--version x.y.z]` † | Bump version across all files and open/merge a PR; the Release workflow publishes |
| `/sync [base-branch] [--strategy merge\|rebase]` † | Pull latest base branch and merge/rebase it into the current branch |

† user-invoked only (`disable-model-invocation`) · ‡ runs forked, reports a summary

<!-- generated:skills end -->

### kokko-validation

Generic master-prompt templates (local validation, deployed validation,
Azure deployment, aesthetics) and a skill that tailors them to the repo. See
[plugins/kokko-validation/README.md](plugins/kokko-validation/README.md).

<!-- generated:skills:kokko-validation start -->

| Skill | Purpose |
| ----- | ------- |
| `/tailor <local\|deployed\|azure-deploy\|aesthetics> [hints such as resource group or app name]` | Instantiate a generic validation/deployment master prompt for the current repo and save it to prompts/ |

† user-invoked only (`disable-model-invocation`) · ‡ runs forked, reports a summary

<!-- generated:skills end -->

### kokko-code-quality

Analysis skills and the six check skills (security, types, complexity,
deadcode, docs, architecture) the janitor drives. The checks share one
workflow, use the tools a repo already configures (ruff first for Python),
run specialist tools ephemerally rather than adding dependencies, and take
`--report` for findings-only runs. See
[plugins/kokko-code-quality/README.md](plugins/kokko-code-quality/README.md).

Claude Code ships a built-in `/review` (pull-request review); the
whole-codebase review here is `/audit` so the two never collide.

<!-- generated:skills:kokko-code-quality start -->

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

### kokko-viz

C4 architecture diagrams, generated and verified by two plugin agents with
the `c4` authoring rules preloaded. See
[plugins/kokko-viz/README.md](plugins/kokko-viz/README.md).

<!-- generated:skills:kokko-viz start -->

| Skill | Purpose |
| ----- | ------- |
| `/c4-map [target-directory]` ‡ | Generate a hierarchical C4 architecture map (context/containers/components) from a codebase |
| `/c4-update [system-id]` ‡ | Update an existing C4 model to match current code changes |
| `/c4-verify [system-id]` ‡ | Verify C4 diagrams against the codebase and auto-fix discrepancies |
| `/c4` | Authoring rules and shared templates for C4 architecture and codemap documents - Insight-branded diagrams rendered from JSON specs, mandatory source-file hyperlinks, no validation report files, template and diagram conventions |

† user-invoked only (`disable-model-invocation`) · ‡ runs forked, reports a summary

<!-- generated:skills end -->

### kokko-infra

Azure subscription cost and status reports. See
[plugins/kokko-infra/README.md](plugins/kokko-infra/README.md).

<!-- generated:skills:kokko-infra start -->

| Skill | Purpose |
| ----- | ------- |
| `/az-costs [daily\|weekly\|<resource-group>]` † | Break down Azure subscription costs with anomaly and optimization analysis |
| `/az-status [subscription-id] [--days N]` † | Generate a daily Azure subscription activity and health summary |

† user-invoked only (`disable-model-invocation`) · ‡ runs forked, reports a summary

<!-- generated:skills end -->

### kokko-ai-config

Keep CLAUDE.md and README files small and truthful. See
[plugins/kokko-ai-config/README.md](plugins/kokko-ai-config/README.md).

<!-- generated:skills:kokko-ai-config start -->

| Skill | Purpose |
| ----- | ------- |
| `/prune-docs [claude-md\|readme\|<path>] [--target-lines N]` | Trim CLAUDE.md or README.md to the essentials under a line target |
| `/verify-docs [claude-md\|readme\|<path>]` ‡ | Audit CLAUDE.md or README.md against the codebase and fix inaccuracies |

† user-invoked only (`disable-model-invocation`) · ‡ runs forked, reports a summary

<!-- generated:skills end -->

### kokko-env

Set up a dev environment, then keep it current without rebuilding it. See
[plugins/kokko-env/README.md](plugins/kokko-env/README.md).

<!-- generated:skills:kokko-env start -->

| Skill | Purpose |
| ----- | ------- |
| `/devcontainer-setup [target-directory] [--ref <branch-or-tag>] [--docs] [--no-up]` † | Install the kokko-ng/kokko-devcontainer starter into a directory (defaults to the current one), tailor it to that project, and bring the container up |
| `/devcontainer-update [--check] [--ref <branch-or-tag>] [--all]` † | Refresh this project's devcontainer config from kokko-ng/kokko-devcontainer and apply it to the running container without a rebuild |
| `/plugins-update [--check] [--all] [<plugin@marketplace> ...]` † | Update Claude Code plugins to the latest marketplace versions, then prompt to run /reload-plugins |

† user-invoked only (`disable-model-invocation`) · ‡ runs forked, reports a summary

<!-- generated:skills end -->

`devcontainer-setup` is the first-time install and runs on the host;
`/devcontainer-update` is the follow-up for a project that already has a
`.devcontainer/`, applied by re-running the project's own
`post-create.sh --config-only`. A `.devcontainer/` copied before that flag
existed needs updating first; the skill detects this and says so.
