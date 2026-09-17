# Contributing

## Developing locally

Add your checkout as a local marketplace and install plugins straight from
it:

```text
/plugin marketplace add /path/to/kokko-skills
/plugin install kokko-notifications@kokko-ng-kokko-cmds
```

Claude Code copies the plugin at install time, so edits to the checkout do
not appear in a running session automatically. The reliable reload path is
to remove and re-add:

```text
/plugin uninstall kokko-notifications@kokko-ng-kokko-cmds
/plugin marketplace update kokko-ng-kokko-cmds
/plugin install kokko-notifications@kokko-ng-kokko-cmds
```

then restart Claude Code (or run `/reload-plugins` where available) so hooks
and skills are re-read.

For hook behavior you rarely need an installed plugin at all:
`tests/hooks/run-tests.sh` exercises the hook scripts directly from the
working tree.

Run `pre-commit install` once after cloning so the lint suite runs as a git
pre-commit hook; `pre-commit run --all-files` covers the whole tree on
demand (see Local checks below).

## Versioning policy: lock-step

All eight plugins share one version number. Every release bumps every
`plugins/*/.claude-plugin/plugin.json` and every entry in
`.claude-plugin/marketplace.json` to the same `x.y.z` together, even for
plugins that did not change. This is deliberate: one number to reason about,
and `release.yml` refuses to publish if the marketplace entries disagree.

`scripts/check-marketplace-sync.sh` (run in CI) asserts that each marketplace
entry matches its plugin manifest (name, version, description) and that every
`plugins/*/` directory is listed in the marketplace.

## Adding a plugin, skill, or agent

1. Create `plugins/<name>/` with a `.claude-plugin/plugin.json` manifest.
   Every user-facing capability is a skill in `skills/<skill>/SKILL.md`
   (frontmatter: `name`, `description`, and `argument-hint` whenever the
   body reads `$ARGUMENTS`; `disable-model-invocation: true` for anything
   with side effects the user should trigger; `context: fork` plus
   `background: false` for long orchestrations that should hand back a
   summary). Legacy `commands/` are still read but not used here. Agents go
   in `agents/<agent>.md` (`name`, `description`, and only model aliases,
   never dated ids). Hooks go in `hooks/` with a `hooks/hooks.json`. Rely
   on directory convention; do not add explicit `skills`/`agents` arrays to
   the manifest.
2. Add a matching entry to `.claude-plugin/marketplace.json` (same name,
   version, and description as the manifest). CI fails if either side is
   missing or out of sync.
3. Hook scripts must be executable and start with `#!/bin/bash`; CI checks
   that every `hooks.json` command resolves to an existing executable file.
4. README tables are generated: add the marker pair
   (`<!-- generated:skills start -->` / `<!-- generated:skills end -->`,
   or `<!-- generated:skills:<plugin> start -->` in the root README) and
   run `bash scripts/gen-readme-tables.sh`. CI fails when a table is stale.
5. `scripts/lint-prompts.sh` checks frontmatter completeness,
   pseudo-placeholders, cited reference paths, allowed-tools coverage of
   fenced bash, forked skills that try to ask questions, and agent
   frontmatter. Run it before pushing.

## Evals

`plugins/<plugin>/evals/<case>/` holds `claude plugin eval` cases: a
`case.yaml` (prompt, turn and time caps, graders) and a `scaffold.sh` that
builds the throwaway git repo the case runs in (it runs in a fresh
workspace with a temporary HOME, so it sets its own git identity). They are
the behavioral regression net for the prompts; the mechanical linter cannot
tell whether a rewritten skill still refuses to `git add .`.

Run one plugin's suite locally (it spends API credit on your own account):

```bash
claude plugin eval plugins/kokko-git --trust-plugin --scaffold \
  --allow-tools Bash Write Edit --no-publish --ablation none
```

`.github/workflows/evals.yml` runs every suite weekly and on demand when
the `ANTHROPIC_API_KEY` repository secret exists, with a cost ceiling; it
is deliberately not part of the per-PR CI. Results land under
`evals/results/`, which is ignored.

## Release flow

1. `/release` (kokko-git) bumps the version in all plugin manifests and the
   marketplace via `scripts/bump-version.sh <x.y.z>` (which ends by running
   the sync check), then opens and merges a PR to `main`. Update
   [CHANGELOG.md](CHANGELOG.md) with an entry for the new version as part of
   the same PR.
2. CI runs on `main` (pre-commit, hook tests, plugin validation, prompt
   lint, README table check, sync check).
3. When CI succeeds, `.github/workflows/release.yml` fires via `workflow_run`
   and creates the `v<version>` GitHub release. It is the sole publisher;
   never run `gh release create` by hand. `workflow_dispatch` with an
   explicit tag exists for recovery.

## Local checks

```bash
pre-commit run --all-files          # lint (shellcheck, markdownlint, hygiene)
bash tests/hooks/run-tests.sh       # hook behavior tests
bash scripts/lint-prompts.sh        # skill and agent prompt lint
bash scripts/gen-readme-tables.sh --check
bash scripts/check-marketplace-sync.sh
claude plugin validate plugins/<name>
```

## Shared infrastructure

[kokko-ng/kokko-janitor-skill](https://github.com/kokko-ng/kokko-janitor-skill)
carries copies of the release workflow, the evals workflow, the marketplace
sync script, the prompt linter, and the pre-commit config. This repo holds
the reference copies; when changing any of them, keep the two repos
convergent.
