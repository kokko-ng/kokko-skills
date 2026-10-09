---
name: devcontainer-update
description: Merge newer kokko-ng/kokko-devcontainer template changes into this project's .devcontainer/ and apply what can go live without a rebuild.
argument-hint: '[--check] [--ref <branch-or-tag>] [--all]'
allowed-tools: Bash(git:*), Bash(bash:*), Bash(diff:*), Bash(cp:*), Bash(mkdir:*), Bash(rm:*), Bash(ls:*), Bash(find:*), Bash(cat:*), Bash(jq:*), Bash(uvx:*), Bash(devcontainer:*), Read, Write, Edit
disable-model-invocation: true
---

# Update the Devcontainer Config

Bring this project's `.devcontainer/` up to date with the
[kokko-ng/kokko-devcontainer](https://github.com/kokko-ng/kokko-devcontainer)
cookiecutter template, and apply everything that can take effect **without
rebuilding the container**. Run it inside the devcontainer or on the host.

The update is a three-way merge. The template is rendered twice with the
answers this project was generated with: once at the template version the
project last took, once at the new one. The difference between the two renders
is merged into the project's files, so the project's own edits survive.

`$ARGUMENTS`:

| Flag | Effect |
| ---- | ------ |
| `--check` | Report the drift and stop. Change nothing. |
| `--ref <branch-or-tag>` | Merge toward that template ref instead of `main`. |
| `--all` | Also merge the template's `CLAUDE.md` into the project's own. Off by default: most projects have rewritten theirs. |

## What goes live and what needs a rebuild

Applied live by `post-create.sh --config-only` (step 7):

- `.devcontainer/config/claude/**`: the settings merge (permission mode, plugin
  roster), the SessionStart hook, and `~/.claude/CLAUDE.md`, which it refreshes
  only when the live copy was not edited
- `.devcontainer/config/zsh/**` and `.devcontainer/config/starship/**`
- Global git configuration, and the Claude Code plugin roster (marketplaces
  registered, enabled plugins installed)

**Needs a rebuild**, which the user runs on the host with `dev rebuild`:

- `.devcontainer/Dockerfile` and `.devcontainer/devcontainer.json`
- `.devcontainer/firewall/` and `.devcontainer/init-host-*.sh`
- `.devcontainer/config/claude/managed-settings.json`: the policy is baked into
  the image, and once provisioning has locked sudo (the default) nothing in
  the container can replace it

Never claim a rebuild-only change is live. Report it in the rebuild list.

## Steps

Each Bash call starts a fresh shell, so the paths below are literal and every
command names them in full.

### 1. Preflight

```bash
git rev-parse --show-toplevel
git status --short -- .devcontainer DEVCONTAINER.md
ls .devcontainer/devcontainer.json .devcontainer/post-create.sh
ls /.dockerenv
```

`ls /.dockerenv` succeeding means you are inside a container.

- Run from the repo root; use it for every path below.
- **Uncommitted changes under `.devcontainer/` → stop and ask.** The merge base
  is the last commit that touched `.devcontainer/`, and the merge rewrites
  those files. Do not stash, do not tidy; ask the user to commit first, per the
  git rules in `CLAUDE.md`.
- No `.devcontainer/` at all → this is a first-time install. Say so and point
  at `/devcontainer-setup`, which runs on the host.

### 2. Fetch the template

```bash
rm -rf /tmp/kokko-devcontainer-upstream /tmp/kokko-devcontainer-renders
git clone https://github.com/kokko-ng/kokko-devcontainer /tmp/kokko-devcontainer-upstream
git -C /tmp/kokko-devcontainer-upstream checkout <ref>    # with --ref only
cat /tmp/kokko-devcontainer-upstream/VERSION
git -C /tmp/kokko-devcontainer-upstream log -1 --format='%h %ad %s' --date=short
```

A full clone, not `--depth=1`: step 4 needs the history. Clone failed (no
network, a firewall that does not allow GitHub, bad ref) → report the actual
error and stop. Do not fall back to a cached copy.

### 3. Recover the project's answers

`/tmp/kokko-devcontainer-upstream/cookiecutter.json` lists the answer keys.
Work out the value each had for this project from its files:

- `project_name`: the first line of `devcontainer.json`
- `python_version`: the `FROM` line in the `Dockerfile`
- `node_version`, `include_azure_cli`, `include_docker_in_docker`: the
  `features` block of `devcontainer.json`
- `include_azure_sql_driver`: whether the `Dockerfile` installs `msodbcsql18`
- `backend_src_dir`: `PYTHONPATH`; `frontend_dir`: `DEVCONTAINER_FRONTEND_DIR`;
  the ports: `forwardPorts`
- `include_copilot_cli`, `include_playwright`, `agent_sudo`,
  `network_firewall`, `git_user_name`, `git_user_email`: the `DEVCONTAINER_*`
  values in `containerEnv`; `cache_volume_scope`: the volume names in
  `mounts`; `container_memory_limit`: the fallback in the `--memory` run arg
- `claude_plugin_roster`, `claude_attribution`: `config/claude/settings.json`

A key with no evidence keeps the template default.

### 4. Render the old and the new template

The old render is the template as it stood when the project last took it: the
last upstream `main` commit before the project's latest `.devcontainer/`
commit.

```bash
git log -1 --format=%cI -- .devcontainer
git -C /tmp/kokko-devcontainer-upstream rev-list -1 --before=<that date> main
git -C /tmp/kokko-devcontainer-upstream worktree add /tmp/kokko-devcontainer-renders/base-tree <that commit>
ls /tmp/kokko-devcontainer-renders/base-tree/cookiecutter.json
```

Render both with the step 3 answers:

```bash
uvx cookiecutter /tmp/kokko-devcontainer-renders/base-tree --no-input -o /tmp/kokko-devcontainer-renders/old key=value ...
uvx cookiecutter /tmp/kokko-devcontainer-upstream --no-input -o /tmp/kokko-devcontainer-renders/new key=value ...
```

Each render writes a `<slug>/` folder named after the project; `<slug>` below
is that name. A base commit with no `cookiecutter.json` predates the template
(the project was copied from the repo's old top-level `.devcontainer/`). Then
the old version is `/tmp/kokko-devcontainer-renders/base-tree/.devcontainer`
itself, with no render: use that path wherever the steps below say
`/tmp/kokko-devcontainer-renders/old/<slug>/.devcontainer`.

Compare the old render with the project. Where they differ in ways that look
like wrong answers rather than local edits (a different Node version in the
feature block, a missing mount), fix the answers and render both again.

### 5. Report the drift

Diff the old render against the new one to see what upstream changed, and the
project against the old render to see what was customized here:

```bash
diff -ruq /tmp/kokko-devcontainer-renders/old/<slug>/.devcontainer /tmp/kokko-devcontainer-renders/new/<slug>/.devcontainer
diff -ruq /tmp/kokko-devcontainer-renders/old/<slug>/.devcontainer .devcontainer
```

Present a table before changing anything:

| File | Upstream change | Customized here | Live or rebuild |
| ---- | --------------- | --------------- | --------------- |
| `config/claude/CLAUDE.md` | 1 section added | no | live |
| `devcontainer.json` | new `runArgs` entry | yes | rebuild |

Then the upstream commits being pulled in, summarized in a few lines:

```bash
git -C /tmp/kokko-devcontainer-upstream log --oneline <base commit>..HEAD -- '{{cookiecutter.project_slug}}'
```

**Stop here if `--check`.**

If upstream changed nothing, say the config is already current and stop. Do
not run the refresh for the sake of it.

### 6. Merge

For every file under the new render's `.devcontainer/`, plus `DEVCONTAINER.md`
(and `CLAUDE.md` with `--all`):

```bash
git merge-file -p .devcontainer/<path> /tmp/kokko-devcontainer-renders/old/<slug>/.devcontainer/<path> /tmp/kokko-devcontainer-renders/new/<slug>/.devcontainer/<path>
```

`-p` prints the merged result, so review it and write it over the project file
yourself. A file this project never customized merges cleanly to the new
version; customizations survive. Show every conflict, say which side is the
upstream improvement and which the project's customization, and resolve it by
hand; when a conflict is genuinely ambiguous, present the options and a
recommendation and let the user pick.

- New upstream files are copied in.
- Files upstream removed are reported, not deleted: a project may depend on
  one.
- Leave `.devcontainer/certs/` and `.devcontainer/.host-git-identity` alone; the
  host fills them at build time.

Show `git diff --stat` and the interesting hunks when done.

### 7. Apply live

Inside the container:

```bash
bash .devcontainer/post-create.sh --config-only
```

On the host, when the container is running:

```bash
devcontainer exec --workspace-folder . bash .devcontainer/post-create.sh --config-only
```

This re-merges the bundled settings and plugin roster into
`~/.claude/settings.json` (keeping the user's own settings and any plugin they
explicitly disabled), re-registers the marketplaces, installs any newly
rostered plugin, refreshes `~/.claude/CLAUDE.md` when the live copy is
unmodified, re-applies the git configuration, and relinks the shell config. It
is idempotent, and every container start runs it too. Relay any `NOTE:` or
`WARNING:` lines it prints (an edited `~/.claude/CLAUDE.md` left alone, a
policy change that needs a rebuild).

### 8. Report

Report in the reply; do not write an update report file:

- The template version before (the base commit) and after (`VERSION` and
  commit), and the answers used
- Files updated, files merged with conflicts and how each was resolved, files
  upstream removed
- **What is live now** versus **what needs a rebuild**, explicitly
- Plugin changes: run `/plugins-update` next if plugin versions also moved, and
  `/reload-plugins` to load them into this session
- The rebuild command, if anything in the rebuild list changed, printed for
  the user to run on the host, never run from here (it replaces the running
  container; the volumes, and with them the sign-ins and Claude Code history,
  are kept):

  ```text
  dev rebuild <project>
  ```

Finally: `git -C /tmp/kokko-devcontainer-upstream worktree remove --force /tmp/kokko-devcontainer-renders/base-tree`,
then `rm -rf /tmp/kokko-devcontainer-upstream /tmp/kokko-devcontainer-renders`.

The changes are left uncommitted in the working tree for review. Do not commit
or push them; that is the user's call.
