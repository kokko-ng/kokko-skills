---
name: prune
description: Find and safely delete stale branches and worktrees, in one repo or several, with confirmation.
argument-hint: '[local|remote|merged|worktrees|<days>] [--repos <dir>...]'
allowed-tools: Bash(git:*), Bash(gh:*), Bash(az:*), Bash(grep:*), Bash(date:*), Bash(ls:*), AskUserQuestion
disable-model-invocation: true
---

# Git Branch and Worktree Cleanup

Find and remove stale branches and worktrees safely. `$ARGUMENTS` scopes the
run: `local`, `remote`, `merged`, `worktrees`, or an age threshold in days
(default 30). With no scope word, cover branches and worktrees both.

## Which repos

- Default: the repo the session is in.
- `--repos <dir>...`: each named directory. A directory that is not itself
  a repo stands for every repo directly inside it.
- When the session's directory is not a repo, treat it the same way: every
  child directory that has a `.git`.

```bash
ls -d */.git
```

With more than one repo, run steps 1 to 3 in each with `git -C <repo>`,
build one report with a Repo column, and ask once in step 4. A repo that
fails a step (no remote, detached HEAD, not reachable) is reported and
skipped; it does not stop the others.

## Process

### 1. Fetch latest state

```bash
git fetch --all --prune
```

### 2. Categorize branches

Resolve the default branch first — never hardcode `main` (`git branch
--merged main` errors outright on a `master`/`trunk` repo):

```bash
git symbolic-ref --short refs/remotes/origin/HEAD
git remote show origin
```

The first command prints `origin/<base>` — strip the `origin/` prefix. If it
errors, take the `HEAD branch:` line from the second, and fall back to `main`
only if both fail. Use the result as `<base>` everywhere below.

```bash
# Merged into the default branch (safe to delete)
git branch --merged <base> | grep -v "main\|master\|\*"
git branch -r --merged origin/<base> | grep -v "main\|master\|HEAD"

# Orphaned (remote gone)
git branch -vv | grep ': gone]'
```

For the age check, print the cutoff epoch (default 30 days; substitute the
`$ARGUMENTS` threshold when one was given), then list every branch's age and
report the ones whose unix timestamp is below the cutoff:

```bash
date -d "30 days ago" +%s 2>/dev/null || date -v-30d +%s
git for-each-ref --sort=committerdate \
  --format='%(refname:short) %(committerdate:unix) %(committerdate:relative)' refs/heads/
```

**Squash-merge caveat:** `git branch --merged` misses squash-merged
branches, so treat its output as a lower bound. A repo that only ever merges
with merge commits does not have the problem; one that other people merge
into may. The `: gone]` orphan check usually catches such branches after the
remote branch is deleted. To confirm a suspected-stale branch, ask the host
whether a merged pull request exists for it (GitHub, then Azure DevOps — run
the one for this repo's remote):

```bash
gh pr list --state merged --head <branch> --json number,title
az repos pr list --source-branch <branch> --status completed --query "[].{id:pullRequestId,title:title}"
```

### 3. Categorize worktrees

A linked worktree keeps its branch checked out, so `git branch -d` refuses
that branch until the worktree is gone. List them, and list the entries
whose directory no longer exists:

```bash
git worktree list --porcelain
git worktree prune --dry-run
```

For each linked worktree (every entry after the first), look at its state
from inside it:

```bash
git -C <worktree path> status --porcelain
git -C <worktree path> log --oneline @{upstream}..HEAD
```

| State | Recommendation |
| ----- | -------------- |
| Clean, branch merged into `<base>` or its remote gone | Remove, then delete the branch |
| Clean, branch unmerged but fully pushed | Keep unless older than the age threshold; then offer removal (the branch stays on the remote) |
| Uncommitted changes, or commits not pushed anywhere | Keep. Report what is in it; never offer it under a bulk option |
| Directory missing (shown by the dry run) | Prune the stale entry |

The second command errors when the branch has no upstream; that means
nothing was ever pushed, which is the third row.

### 4. Report

Show two tables: branches (Branch | Status | Last Commit | Age |
Recommendation) and worktrees (Path | Branch | State | Recommendation).

### 5. Confirm with AskUserQuestion

Present what is recommended for deletion and let the user choose. Options:
"Delete all merged", "Delete all orphaned", "Remove clean merged worktrees",
"Select individually", "Skip" (leave out an option with nothing behind it).

### 6. Execute approved deletions

Worktrees first, so their branches become deletable:

```bash
git worktree remove <worktree path>   # refuses on a dirty worktree — that refusal is a finding
git worktree prune
git branch -d branch-name             # refuses on unmerged work — that refusal is a finding
```

Run only these yourself. Never `git worktree remove --force`, never
`git branch -D`, and never `git push origin --delete`: the first discards
uncommitted work, `-D` discards a branch's unmerged commits (and its reflog
with them), and a remote deletion cannot be undone from here. For worktrees
and branches the plain commands refuse, and for remote deletions the user
approved, print the exact commands for the user to run themselves in a
terminal:

```text
# Approved but must be run by you (this command never runs these itself):
git worktree remove --force <path>    # worktree with uncommitted changes
git branch -D <branch>                # unmerged local branch
git push origin --delete <branch>     # remote branch
```

### 7. Summarize

Report counts of removed worktrees, deleted local branches, and kept
branches and worktrees, per repo when there was more than one. Optionally
`git gc` to reclaim space.

## Safety Rules

- Never delete the default branch, master, or the current branch, and never
  remove the main worktree or the one the session is running in.
- Never run `git worktree remove --force`, `git branch -D`, or
  `git push origin --delete` yourself — print approved force and remote
  deletions for the user to run (see step 6).
- Always show what will be deleted before doing it.
- Skip branches and worktrees with unpushed commits unless the user confirms.
