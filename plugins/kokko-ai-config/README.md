# kokko-ai-config

AI configuration management: keep CLAUDE.md and README files small and
truthful. One skill trims them to the essentials, the other audits them
against the actual codebase (forked, so the command runs and link checks
stay out of your conversation).

```bash
/plugin install kokko-ai-config@kokko-ng-kokko-cmds
```

## Skills

<!-- generated:skills start -->

| Skill | Purpose |
| ----- | ------- |
| `/prune-docs [claude-md\|readme\|<path>] [--target-lines N]` | Trim CLAUDE.md or README.md to the essentials under a line target |
| `/verify-docs [claude-md\|readme\|<path>]` ‡ | Audit CLAUDE.md or README.md against the codebase and fix inaccuracies |

† user-invoked only (`disable-model-invocation`) · ‡ runs forked, reports a summary

<!-- generated:skills end -->
