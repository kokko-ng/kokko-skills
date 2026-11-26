# kokko-git

Git workflow skills: commit and push in one step, landing work through
deploy and merge, releases, syncing with the base branch, pruning branches
and worktrees, and timesheet write-ups from history. The skills that open
pull requests or watch pipelines work on GitHub (`gh`) and on Azure DevOps
(`az repos`, `az pipelines`).

```bash
/plugin install kokko-git@kokko-ng-kokko-cmds
```

## Skills

<!-- generated:skills start -->

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

## Notes

`/compush`, `/land`, `/sync`, `/release` and `/worklog` can be invoked by
Claude, so a plain request ("commit and push", "commit, push, deploy",
"bump a version", "write up this week for my timesheet") reaches them
without the slash command. `/prune` deletes things and stays user-invoked.

`/land` reads how the repo ships from its `CLAUDE.md` (a `## Deploy`
section), its deploy docs, and its pipelines. When the target is not
written down it asks once and records the answer there. It never deploys to
an environment the docs call production or off limits.

Every merge these skills make is a merge commit: never a squash, never a
rebase-merge. `/release` merges without asking only with `--merge` or when
the request said to merge.

`/release` never publishes a GitHub release itself where a workflow does: in
this repo the Release workflow is the sole publisher once CI succeeds on
`main`. In repos with a `scripts/bump-version.sh` (like kokko-skills),
`/release` uses it instead of editing version strings by hand.

Force pushes, forced worktree removals, and remote branch deletions are
printed for you to run; none of these skills runs one itself.

The GitHub and Azure DevOps command pairs the skills share live in
`references/hosts.md`.
