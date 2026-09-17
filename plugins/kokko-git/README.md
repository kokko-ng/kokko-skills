# kokko-git

Git workflow skills: commit+push in one step, branch pruning, releases, and
syncing with the base branch. The janitor lives in its own repo:
[kokko-ng/kokko-janitor-skill](https://github.com/kokko-ng/kokko-janitor-skill).

```bash
/plugin install kokko-git@kokko-ng-kokko-cmds
```

## Skills

<!-- generated:skills start -->

| Skill | Purpose |
| ----- | ------- |
| `/compush [files] [--message "msg"]` † | Stage, commit (Conventional Commits), and push one logical change |
| `/prune [local\|remote\|merged\|<days>]` † | Find and safely delete stale local/remote branches with confirmation |
| `/release [patch\|minor\|major] [--version x.y.z]` † | Bump version across all files and open/merge a PR; the Release workflow publishes |
| `/sync [base-branch] [--strategy merge\|rebase]` † | Pull latest base branch and merge/rebase it into the current branch |

† user-invoked only (`disable-model-invocation`) · ‡ runs forked, reports a summary

<!-- generated:skills end -->

## Notes

`/release` never publishes a GitHub release itself: in this repo the
Release workflow is the sole publisher once CI succeeds on `main`. In repos
with a `scripts/bump-version.sh` (like kokko-skills), `/release` uses it
instead of editing version strings by hand.

Force pushes and remote branch deletions are printed for you to run; none
of these skills runs one itself.
