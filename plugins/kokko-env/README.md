# kokko-env

Dev environment setup and maintenance: install the
[kokko-ng/kokko-devcontainer](https://github.com/kokko-ng/kokko-devcontainer)
starter into a project, refresh the devcontainer config inside a running
container, and update Claude Code plugins to their latest marketplace
versions.

```bash
/plugin install kokko-env@kokko-ng-kokko-cmds
```

## Skills

<!-- generated:skills start -->

| Skill | Purpose |
| ----- | ------- |
| `/devcontainer-setup [target-directory] [--ref <branch-or-tag>] [--docs] [--no-up]` † | Install the kokko-ng/kokko-devcontainer starter into a directory (defaults to the current one), tailor it to that project, and bring the container up |
| `/devcontainer-update [--check] [--ref <branch-or-tag>] [--all]` † | Refresh this project's devcontainer config from kokko-ng/kokko-devcontainer and apply it to the running container without a rebuild |
| `/plugins-update [--check] [--all] [<plugin@marketplace> ...]` † | Update Claude Code plugins to the latest marketplace versions, then prompt to run /reload-plugins |

† user-invoked only (`disable-model-invocation`) · ‡ runs forked, reports a summary

<!-- generated:skills end -->

`devcontainer-setup` is the first-time install and runs on the host;
`/devcontainer-update` is the follow-up for a project that already has a
`.devcontainer/`. It applies config by re-running the project's own
`post-create.sh --config-only`; a `.devcontainer/` copied before that flag
existed needs updating first, and the skill detects this and says so.
