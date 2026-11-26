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
when a built-in or another plugin claims the same short name, or just ask
in plain words: every skill not marked † can be picked up by Claude from a
request that matches its description. Skills marked † in the tables below
only run when you invoke them; skills marked ‡ run in a forked context and
hand back a summary, so a long orchestration never fills your conversation.

## Which workflow when

The plugins compose into a few end-to-end flows. Linting, type checking,
dead-code, dependency, and secret checks live in each repo's pre-commit
config rather than in a skill.

| When | Run | Plugins |
| ---- | --- | ------- |
| Starting a project | `devcontainer-setup` on the host, then `/plugins-update` inside the container | kokko-env |
| Every commit | "commit and push" or `/compush`; `/sync` to catch up with the base branch | kokko-git |
| Shipping a change | "commit, push, deploy" or `/land`: commit, push, deploy to the documented environment, verify, merge with a merge commit | kokko-git |
| Feedback arrives | `/feedback <file or folder>`: ledger, skip what is done, fix and verify the rest | kokko-validation |
| Before a demo | `/az-demo up --until 22:00`; `/az-access <email>` for whoever needs to get in | kokko-infra |
| A UI pass | `/tailor` writes the aesthetics prompt; run it, then again in a fresh session until a pass finds nothing new | kokko-validation |
| Releasing | `/release [--merge]` | kokko-git |
| Friday | `/worklog` for the timesheet; `/prune` for stale branches and worktrees | kokko-git |
| Understanding a codebase | `/c4-map --eli5`; `--export <dir>` to copy it into a notes vault | kokko-viz |
| Keeping docs honest | `/verify-docs`, `/c4-verify` | kokko-ai-config, kokko-viz |
| A skill got it wrong | `/upstream-fix`: the session's corrections become a pull request on the skill's repo | kokko-ai-config |

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

Git workflow skills, on GitHub and Azure DevOps. See
[plugins/kokko-git/README.md](plugins/kokko-git/README.md).

<!-- generated:skills:kokko-git start -->

| Skill | Purpose |
| ----- | ------- |
| `/compush [files] [--message "msg"]` | Stage, commit (Conventional Commits), and push one logical change |
| `/land [--env <name>] [--no-deploy] [--no-merge] [--pr-only]` | Commit, push, deploy to the repo's documented environment, verify the deployment, and merge to the default branch with a merge commit |
| `/prune [local\|remote\|merged\|worktrees\|<days>] [--repos <dir>...]` † | Find and safely delete stale branches and worktrees, in one repo or several, with confirmation |
| `/release [patch\|minor\|major] [--version x.y.z] [--merge]` | Bump the version across all files and open a pull request, merging it when told to; the repo's own release flow publishes |
| `/sync [base-branch] [--strategy merge\|rebase]` | Pull latest base branch and merge/rebase it into the current branch |
| `/worklog [<range such as "this week" or 2026-09-07..2026-09-11>] [--repos <dir>...] [--per day\|week\|blocks:<n>] [--sentences <n>] [--technical]` | Write up the work done in one or more repos over a date range, from git history, as plain text ready for a timesheet |

† user-invoked only (`disable-model-invocation`) · ‡ runs forked, reports a summary

<!-- generated:skills end -->

### kokko-validation

Work through feedback with a ledger, and tailor an aesthetics master prompt
to the repo. The aesthetics prompt reviews and fixes the UI through the
[impeccable](https://github.com/pbakaus/impeccable) plugin
(`impeccable@impeccable`), which it needs installed. See
[plugins/kokko-validation/README.md](plugins/kokko-validation/README.md).

<!-- generated:skills:kokko-validation start -->

| Skill | Purpose |
| ----- | ------- |
| `/feedback [<file, folder, or pasted text>...] [--ledger <path>] [--plan-only]` | Turn a batch of feedback into a ledger of discrete items, skip the ones already done, then fix and verify each of the rest |
| `/tailor [aesthetics] [hints such as the frontend directory or theme names]` | Instantiate the aesthetics master prompt for the current repo and save it to prompts/ |

† user-invoked only (`disable-model-invocation`) · ‡ runs forked, reports a summary

<!-- generated:skills end -->

### kokko-viz

C4 architecture diagrams, generated and verified by two plugin agents with
the `c4` authoring rules preloaded. See
[plugins/kokko-viz/README.md](plugins/kokko-viz/README.md).

<!-- generated:skills:kokko-viz start -->

| Skill | Purpose |
| ----- | ------- |
| `/c4-map [target-directory] [--eli5] [--export <dir>]` ‡ | Generate a hierarchical C4 architecture map (context/containers/components) from a codebase |
| `/c4-update [system-id] [--eli5] [--export <dir>]` ‡ | Update an existing C4 model to match current code changes |
| `/c4-verify [system-id] [--eli5] [--export <dir>]` ‡ | Verify C4 diagrams against the codebase and auto-fix discrepancies |
| `/c4` | Authoring rules and shared templates for C4 architecture and codemap documents - strict C4 element and relationship labels, Insight-branded diagrams rendered from JSON specs, mandatory source-file hyperlinks, no validation report files, template and diagram conventions |

† user-invoked only (`disable-model-invocation`) · ‡ runs forked, reports a summary

<!-- generated:skills end -->

### kokko-infra

Access and power control for Azure demo and sandbox environments. See
[plugins/kokko-infra/README.md](plugins/kokko-infra/README.md).

<!-- generated:skills:kokko-infra start -->

| Skill | Purpose |
| ----- | ------- |
| `/az-access <email>... [to <app, resource group, or project>] [as <role>]` | Give a person access to a deployed Azure app, a resource group, or an Azure DevOps project, confirm the grant, and draft the note to send them |
| `/az-demo <up\|down\|status> [<app or resource group>] [--until <time>] [--schedule "<days> <start>-<end> <timezone>"]` | Wake a demo or sandbox environment in Azure, keep it awake until a set time, put it back to sleep, or report what state it is in |

† user-invoked only (`disable-model-invocation`) · ‡ runs forked, reports a summary

<!-- generated:skills end -->

### kokko-ai-config

Keep CLAUDE.md and README files truthful, and carry a session's corrections
back into the skill that needed them. See
[plugins/kokko-ai-config/README.md](plugins/kokko-ai-config/README.md).

<!-- generated:skills:kokko-ai-config start -->

| Skill | Purpose |
| ----- | ------- |
| `/upstream-fix [<skill or plugin name>] [--repo <owner/name>] [--merge]` | Carry the corrections made in this session back into the skill, plugin, or template that produced the flawed output, as a pull request with a version bump |
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
| `/devcontainer-update [--check] [--ref <branch-or-tag>]` | Merge newer kokko-ng/kokko-devcontainer template changes into a project's template files (.devcontainer/, CLAUDE.md, the quality gate) and apply what can go live without a rebuild |
| `/plugins-update [--check] [--all] [<plugin@marketplace> ...]` † | Update Claude Code plugins to the latest marketplace versions, then prompt to run /reload-plugins |

† user-invoked only (`disable-model-invocation`) · ‡ runs forked, reports a summary

<!-- generated:skills end -->

`devcontainer-setup` is the first-time install and runs on the host;
`/devcontainer-update` is the follow-up for a project that already has a
`.devcontainer/`: it merges the template changes since the project last took
it and applies the config live with the project's own
`post-create.sh --config-only`.
