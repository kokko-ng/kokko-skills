# kokko-env

Dev environment setup and maintenance: install the
[kokko-ng/kokko-devcontainer](https://github.com/kokko-ng/kokko-devcontainer)
template into a project, merge newer template changes into its devcontainer
config, and update Claude Code plugins to their latest marketplace versions.

```bash
/plugin install kokko-env@kokko-ng-kokko-cmds
```

## Skills

<!-- generated:skills start -->

| Skill | Purpose |
| ----- | ------- |
| `/devcontainer-setup [target-directory] [--ref <branch-or-tag>] [--no-up]` † | Install the kokko-ng/kokko-devcontainer template into a directory (defaults to the current one), with template answers that match that project, and bring the container up with dev |
| `/devcontainer-update [--check] [--ref <branch-or-tag>]` | Merge newer kokko-ng/kokko-devcontainer template changes into a project's template files (.devcontainer/, CLAUDE.md, the quality gate) and apply what can go live without a rebuild |
| `/plugins-update [--check] [--all] [<plugin@marketplace> ...]` † | Update Claude Code plugins to the latest marketplace versions, then prompt to run /reload-plugins |

† user-invoked only (`disable-model-invocation`) · ‡ runs forked, reports a summary

<!-- generated:skills end -->

`devcontainer-setup` is the first-time install and runs on the host: it
renders the cookiecutter template with answers read from the project and
starts the container with `dev`. `/devcontainer-update` is the follow-up for
a project that already has a `.devcontainer/`: it three-way merges the
template changes since the project last took it, then applies the config
live with the project's own `post-create.sh --config-only` and lists what
needs a `dev rebuild`.
