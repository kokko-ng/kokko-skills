# kokko-ai-config

AI configuration upkeep. One skill audits CLAUDE.md and README files against
the actual codebase (forked, so the command runs and link checks stay out of
your conversation). The other takes the corrections you had to make to a
skill's output in a session and carries them back into that skill's own
repo as a pull request, so the same mistake is not made again.

```bash
/plugin install kokko-ai-config@kokko-ng-kokko-cmds
```

## Skills

<!-- generated:skills start -->

| Skill | Purpose |
| ----- | ------- |
| `/upstream-fix [<skill or plugin name>] [--repo <owner/name>] [--merge]` | Carry the corrections made in this session back into the skill, plugin, or template that produced the flawed output, as a pull request with a version bump |
| `/verify-docs [claude-md\|readme\|<path>]` ‡ | Audit CLAUDE.md or README.md against the codebase and fix inaccuracies |

† user-invoked only (`disable-model-invocation`) · ‡ runs forked, reports a summary

<!-- generated:skills end -->

## Notes

`/upstream-fix` edits the skill's source repo, never the installed copy,
prefers a mechanical check over a prose rule, and stops at the open pull
request unless told to merge. It never changes a repo's visibility.

`/prune-docs` has been removed; see the changelog.
