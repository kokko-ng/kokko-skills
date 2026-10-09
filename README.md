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

The plugins compose into a few end-to-end flows. Linting, type checking,
dead-code, dependency, and secret checks live in each repo's pre-commit
config rather than in a skill.

| When | Run | Plugins |
| ---- | --- | ------- |
| Starting a project | `devcontainer-setup` on the host, then `/plugins-update` inside the container | kokko-env |
| Every commit | `/compush`; `/sync` before opening a PR; `pre-commit run --all-files` when a hook fails | kokko-git |
| Before a feature is done | `tailor local` writes the validation prompt; run it, then run it again in a fresh session until a pass finds nothing new | kokko-validation |
| Shipping | `tailor azure-deploy`, then `tailor deployed`, each run the same way; `/release` when green | kokko-validation, kokko-git |
| Weekly hygiene | `/prune` | kokko-git |
| Understanding a codebase | `/c4-map` | kokko-viz |
| Keeping docs honest | `/verify-docs`, `/prune-docs`, `/c4-verify` | kokko-ai-config, kokko-viz |
| Azure | `/az-status`, `/az-costs` | kokko-infra |

## Versioning

All seven plugins version in lock-step: every release bumps every plugin (and
every marketplace entry) to the same version, even ones that did not change.
See [CONTRIBUTING.md](CONTRIBUTING.md).

## Environment variables

kokko-notifications plays its sounds through `hooks/utils/play-sound.sh`
and honors:

| Environment Variable | Default | Purpose |
| -------------------- | ------- | ------- |
| `KOKKO_SOUNDS` | `on` | Set to `off` to mute all hook sounds |
| `KOKKO_SOUND_EVENTS` | all | Comma-separated sound types to play: `completion`, `attention` |
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
| `/devcontainer-setup [target-directory] [--ref <branch-or-tag>] [--no-up]` † | Install the kokko-ng/kokko-devcontainer template into a directory (defaults to the current one), with template answers that match that project, and bring the container up with dev |
| `/devcontainer-update [--check] [--ref <branch-or-tag>] [--all]` † | Merge newer kokko-ng/kokko-devcontainer template changes into this project's .devcontainer/ and apply what can go live without a rebuild |
| `/plugins-update [--check] [--all] [<plugin@marketplace> ...]` † | Update Claude Code plugins to the latest marketplace versions, then prompt to run /reload-plugins |

† user-invoked only (`disable-model-invocation`) · ‡ runs forked, reports a summary

<!-- generated:skills end -->

`devcontainer-setup` is the first-time install and runs on the host;
`/devcontainer-update` is the follow-up for a project that already has a
`.devcontainer/`: it merges the template changes since the project last took
it and applies the config live with the project's own
`post-create.sh --config-only`.
