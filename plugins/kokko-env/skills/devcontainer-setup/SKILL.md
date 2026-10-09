---
name: devcontainer-setup
description: Install the kokko-ng/kokko-devcontainer template into a directory (defaults to the current one), with template answers that match that project, and bring the container up with dev. Runs on the host, first-time install only; use /devcontainer-update for a project that already has a .devcontainer/.
argument-hint: '[target-directory] [--ref <branch-or-tag>] [--no-up]'
disable-model-invocation: true
---

# Devcontainer Setup Skill

Install [kokko-ng/kokko-devcontainer](https://github.com/kokko-ng/kokko-devcontainer)
into a project: render its cookiecutter template with answers that match what
the project actually is, copy the result in, and start the container with
`dev`, the template's host command.

This is the **first-time install**. Use `/devcontainer-update` instead when the
project already has a `.devcontainer/` and the job is to merge newer template
changes into it.

Run this on the **host** (macOS), not inside a devcontainer. The template
assumes Colima as the Docker runtime and `dev` (linked from a clone of
kokko-devcontainer) as the launcher; `dev` sizes and starts Colima itself.

Each Bash call starts a fresh shell, so a variable set in one command is gone
in the next. Below, `<target>` stands for the absolute target path and
`<slug>` for the project slug the template derives; write the real values into
every command.

## Arguments

`$ARGUMENTS`:

| Argument | Effect |
| -------- | ------ |
| `[target-directory]` | Where to install. Defaults to the current working directory. |
| `--ref <branch-or-tag>` | Render the template from that ref instead of `main`. |
| `--no-up` | Install the files, then stop. Do not build or start the container. |

## Steps

### 1. Preflight

```bash
ls -la <target>
ls -la <target>/.devcontainer 2>/dev/null && echo "ALREADY HAS .devcontainer"
git -C <target> rev-parse --show-toplevel 2>/dev/null || echo "NOT A GIT REPO"
[ -f /.dockerenv ] && echo "INSIDE A CONTAINER" || echo "on the host"
```

Stop and ask when any of these is true:

- **The target is a folder of projects, not a project.** The default target is
  the current directory, and a `~/code`-style parent directory passes every
  other check here while being the wrong answer: one shared container across
  ten unrelated projects. Suspect this when the target itself has no project
  markers (`pyproject.toml`, `package.json`, `*.csproj`, `go.mod`, `src/`) but
  two or more of its subdirectories do. Confirm the intended project before
  copying anything.
- **The target directory does not exist.** Do not invent a path. But when the
  user has explicitly named a new directory ("a new folder called `sandbox/`"),
  that *is* the confirmation: create it, `git init` it, and say so in the
  report.
- **`.devcontainer/` already exists.** This skill would overwrite it. Report
  what is there and recommend `/devcontainer-update`, which merges instead.
- **Inside a container.** The build has to happen on the host. Say so and stop.
- **Target is not a git repo.** Not fatal, but without a repo there is no
  history to recover from, and `/devcontainer-update` later needs the commit
  that installed `.devcontainer/` as its merge base. For a directory this
  skill just created, `git init` it rather than merely reporting the gap; for
  a pre-existing directory, say so and let the user decide.

Then check the host toolchain (report what is missing; do not install anything
without asking):

```bash
command -v dev colima docker devcontainer uv gh jq claude || true
dev guide
```

`dev guide` shows the VM size `dev` will use on this Mac, whether the shared
Claude Code token is in the Keychain, and which containers exist. Missing
tooling maps to:

```bash
brew install colima docker devcontainer uv gh jq
```

No `dev` means kokko-devcontainer is not cloned and linked on this Mac. Its
`prompts/setup.md` is the procedure (clone to `~/code/kokko-devcontainer`,
`ln -sfn ~/code/kokko-devcontainer/bin/dev ~/.local/bin/dev`); offer it rather
than improvising. Do not start or resize Colima by hand: `dev` sizes the VM
from the Mac's RAM, and an existing VM disk can never shrink.

### 2. Choose the template answers

The template is parameterized by cookiecutter answers (its `cookiecutter.json`
lists every key). Read the project and choose the answers below from evidence;
do not assume the defaults fit:

| Answer | Evidence | Default |
| ------ | -------- | ------- |
| `project_name` | `pyproject.toml` / `package.json` name, else the folder name. The slug derived from it names the container (`<slug>-dev`). | `My Project` |
| `python_version` | `requires-python`, `.python-version`. One of `3.14`, `3.13`, `3.12`; only `3.14` is digest-pinned. | `3.14` |
| `node_version` | `engines` in `package.json`, `.nvmrc`. One of `22`, `24`, `20`. | `22` |
| `backend_src_dir` | Where the Python package lives; it becomes `PYTHONPATH`. | `src` |
| `frontend_dir` | The directory holding the frontend `package.json`. | `ui` |
| `backend_port` / `frontend_port` | Ports in app config, compose files, the Vite config. | `8000` / `5173` |
| `include_azure_cli` | Any Azure usage (SDKs, `az` in scripts, bicep/terraform). | `yes` |
| `include_azure_sql_driver` | pyodbc or Azure SQL only; it is a slow image layer. | `yes` |
| `include_playwright` | Playwright in the dependencies, or a browser UI to test. | `yes` |
| `include_docker_in_docker` | Something builds containers inside the devcontainer. `yes` makes the container privileged, so ask before choosing it. | `no` |

Leave the remaining keys (`include_copilot_cli`, `claude_plugin_roster`,
`agent_sudo`, `network_firewall`, `cache_volume_scope`,
`container_memory_limit`, `git_user_name`, `git_user_email`) at their defaults
unless the user asks: they are security and identity choices, not facts about
the project.

Evidence to read: `pyproject.toml`, `package.json`, `uv.lock`,
`requirements.txt`, `*.csproj`, the presence of `src/`/`app/`/`ui/`/`frontend/`,
existing port numbers in config or compose files, and any `.env.example`.
Where the right value is genuinely ambiguous (a monorepo with three candidate
frontends, say), ask rather than guessing.

**Greenfield target.** An empty directory has none of that evidence. Do not
infer a stack from the directory name. Set `project_name`, keep the layout and
port defaults (harmless until the directory has content), and ask once, in a
single question, which of the optional pieces to keep: the Azure CLI, the ODBC
driver, Playwright, Docker-in-Docker. Say in the report that the defaults were
kept for want of evidence.

### 3. Render the template

```bash
rm -rf /tmp/kokko-devcontainer-render
uvx cookiecutter gh:kokko-ng/kokko-devcontainer --no-input -o /tmp/kokko-devcontainer-render \
  project_name="<name>" python_version=<x.y> backend_src_dir=<dir> frontend_dir=<dir> ...
# with --ref: add --checkout <ref>
ls -A /tmp/kokko-devcontainer-render/<slug>
```

Pass every answer from step 2 as `key=value`. The template's pre-generation
hook rejects an invalid answer before writing anything: report its message,
fix the answer, and render again. The post-generation hook prints generic next
steps (`code .`) that do not apply here; relay any `NOTE:` lines it prints
(Docker-in-Docker, an unpinned Python image) in the report.

A failed render (no network, bad ref) means report the actual error and stop.
Never hand-write a `.devcontainer/` as a fallback.

### 4. Copy it in

```bash
cp -R /tmp/kokko-devcontainer-render/<slug>/.devcontainer <target>/.devcontainer
```

- `DEVCONTAINER.md`: copy it when the project has none; otherwise name it as
  skipped.
- `CLAUDE.md`: copy it when the project has none. When the project has its
  own, merge the generated sections into it rather than overwriting, and show
  what was added.
- `.gitignore`: append the generated entries the project's file lacks (`.env`,
  Claude Code worktrees, Playwright artifacts, ...); copy it when the project
  has none.

Do **not** touch the project's `README.md`.

### 5. Bring the container up

Skip this whole step with `--no-up`, and say clearly that nothing was built.

```bash
dev ls
dev up <target>
```

`dev up` starts the Colima VM if needed (sized for this Mac), builds and starts
the container without opening a shell, and fills the shared sign-ins it can
copy from the Mac. The first build takes a few minutes; the full log is
`$TMPDIR/dev-<folder>.log`. On a Mac with under 16 GB, `dev` runs one
devcontainer at a time and stops any other running one first: when `dev ls`
shows another container running, say so and ask before starting.

Failure handling:

- `not starting the VM`: macOS is short of free memory and `dev` had no
  terminal to confirm in. Report it; the user can close apps or run
  `DEV_FORCE=1 dev up <target>` themselves.
- `devcontainer up failed`: `dev` prints the tail of the log. Report the
  failing step. If Docker is unreachable while Colima says it is running,
  check the VM disk first (`colima ssh -- df -h /`): a full disk kills the
  daemon while `colima status` still looks healthy.
- A post-create step failed: the container is still usable. Report which step,
  and that the config can be re-applied in place with
  `bash .devcontainer/post-create.sh --config-only`.

Then confirm it before reporting success:

```bash
docker ps --format '{{.Names}}\t{{.Status}}'
```

### 6. Report

Report in the reply; do not write a setup report file:

- Target directory, the template ref rendered, and whether the directory was
  created and `git init`ed as part of this run
- Every template answer with the evidence behind it, and on a greenfield
  target which defaults were kept for want of evidence
- Files copied, merged, and skipped
- Host state worth knowing: the VM size from `dev guide`, and any container
  `dev up` stopped
- Container status as verified by `docker ps`, or not built and why
- What the user still runs in a terminal, because each opens a browser or
  needs a keypress: `dev auth <target>` once per Mac if `dev guide` showed no
  Claude Code token, then `dev claude <target>` to open Claude Code in the
  container, signed in, in Auto mode
- That the new files are left uncommitted for review. Do not commit or push
  them; that is the user's call. Once committed, that commit is the merge base
  `/devcontainer-update` uses.

Finally: `rm -rf /tmp/kokko-devcontainer-render`.

## Afterwards

- `/devcontainer-update` merges later template changes into this project.
- `/plugins-update` moves the installed Claude Code plugins to their published
  versions.
- Claude Code runs in Auto mode by default (`permissions.defaultMode` in
  `.devcontainer/config/claude/settings.json`); the deny-list policy in
  `managed-settings.json` is baked into the image and cannot be overridden
  from inside the container.
