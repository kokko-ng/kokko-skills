---
name: release
description: Bump the version across all files and open a pull request, merging it when told to; the repo's own release flow publishes. Use when the user asks to bump a version, cut or publish a release, or ship a new version of a repo, plugin, or skill.
argument-hint: '[patch|minor|major] [--version x.y.z] [--merge]'
allowed-tools: Bash(git:*), Bash(gh:*), Bash(az:*), Bash(bash:*), Bash(grep:*), Bash(jq:*), Read, Edit, Grep, Glob, AskUserQuestion
---

# Version Bump and Release

Increment the version, open a pull request for it, and merge it when
authorized. Publishing belongs to the repo's own release flow, which this
skill follows rather than replaces.

`$ARGUMENTS` sets the bump type (patch/minor/major, default patch) or an
explicit `--version x.y.z`. `--merge` authorizes merging the pull request once
its checks pass, without asking again; so does a request that says to merge
("bump a version and merge to main").

The repo may live on GitHub or Azure DevOps. The pull request, check, and
merge commands for both are in `${CLAUDE_PLUGIN_ROOT}/references/hosts.md`;
read it once and use the column for this repo's host.

## Steps

### 1. Read the repo's release flow

Read `CONTRIBUTING.md`, the release section of `README.md` or `CLAUDE.md`,
and the release workflow if there is one (`.github/workflows/release*.yml`,
a release stage in `azure-pipelines*.yml`). Note who publishes: a workflow
that fires after the merge, a manual tag, or nothing documented. That
decides step 6.

### 2. Detect current version

If the repo has a bump script, it owns the version locations — read the
current version from where it writes (for kokko-skills:
`jq -r '.plugins[0].version' .claude-plugin/marketplace.json`). Otherwise
check common locations: `pyproject.toml`, `package.json`, `*/__init__.py`
(`__version__`), `.claude-plugin/plugin.json`,
`.claude-plugin/marketplace.json`, `Cargo.toml`, `version.txt`/`VERSION`.

```bash
grep -rl '"version"' . --include="*.json"
grep -E "^version\s*=" pyproject.toml Cargo.toml
grep -rn "__version__" . --include="__init__.py"
git describe --tags --abbrev=0
```

### 3. Calculate new version

Semantic versioning: patch = Z+1 (fixes), minor = Y+1/Z=0 (features), major = X+1/Y=0/Z=0 (breaking).
When no bump type was given, read the unreleased commits
(`git log <last tag>..HEAD --oneline`) and take the largest they call for: a
`feat!` or `BREAKING CHANGE` means major, a `feat` means minor, anything else
patch.

### 4. Update every version reference

If `scripts/bump-version.sh` exists (it does in kokko-skills), use it — it
rewrites every plugin manifest and marketplace entry in lock-step and ends
with the sync check; do not grep-and-edit version strings by hand:

```bash
bash scripts/bump-version.sh X.Y.Z
```

Otherwise replace the old version in every file from step 2. Keep formats
consistent — no `v` prefix in files, `v` prefix on the git tag. Then verify:

```bash
git diff
```

### 5. Create the version-bump pull request

If the repo keeps a `CHANGELOG.md`, rename its `## Unreleased` heading to
`## X.Y.Z - YYYY-MM-DD` (or add an entry for X.Y.Z if there is none) so the
changelog ships in the same pull request as the bump.

Branch, commit, and push. Stage the modified files by explicit path from the
`git status` output — never `git add .` (it sweeps in untracked files). Word
the commit the way the repo's earlier release commits are worded, defaulting
to `chore: release X.Y.Z`:

```bash
git log --oneline -i --grep='release\|bump' -5
git checkout -b release-vX.Y.Z
git status --porcelain
git add <each modified file, named explicitly>
git commit -m "chore: release X.Y.Z"
git push -u origin release-vX.Y.Z
```

Open the pull request against the default branch with the host's CLI
(`gh pr create`, or `az repos pr create` on Azure DevOps), titled
"Release X.Y.Z".

### 6. Merge when authorized

Wait for the pull request's checks (`gh pr checks <n> --watch`, or
`az repos pr policy list --id <n>` on Azure DevOps). A failing check stops
the run: report it, do not merge.

- With `--merge`, or when the request said to merge: merge as soon as the
  checks pass.
- Otherwise confirm with AskUserQuestion first — show the pull request
  number, title, and check status, with options "Merge", "Wait", "Abort".

Merge with a merge commit, never a squash or a rebase:

```bash
gh pr merge <n> --merge
az repos pr update --id <n> --status completed --squash false --delete-source-branch false
```

Run the one line for this repo's host. A required review or a branch policy
that blocks the merge is not something to work around: stop and report the
pull request link.

### 7. Publish the way the repo publishes

- **A workflow publishes after the merge** (kokko-skills:
  `.github/workflows/release.yml` creates the `vX.Y.Z` release once CI
  succeeds on `main`). Do not run `gh release create` or push tags by hand.
  Watch the CI and release runs (`gh run list`, `gh run watch`) and confirm
  the release exists (`gh release view vX.Y.Z`). If the workflow did not
  fire, report why instead of publishing manually.
- **The documented flow is a manual tag or release.** Do exactly what the
  repo documents, after the merge, from the updated default branch.
- **Nothing is documented.** Stop at the merged bump and say that the repo
  has no publisher; do not invent one.

## Notes

- No emojis or attribution footers in commits or release notes.
- Version not found → search manually and add the file to the update set.
- A plugin or skill release only reaches a running session after the plugin
  is updated there (`/plugins-update`, then `/reload-plugins`).
