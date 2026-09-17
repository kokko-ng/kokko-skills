# kokko-infra

Azure infrastructure skills for keeping an eye on a subscription: costs
with anomaly analysis, and a daily activity/health summary. Both drive the
`az` CLI, which must be installed and logged in, and confirm the
subscription before running anything.

```bash
/plugin install kokko-infra@kokko-ng-kokko-cmds
```

## Skills

<!-- generated:skills start -->

| Skill | Purpose |
| ----- | ------- |
| `/az-costs [daily\|weekly\|<resource-group>]` † | Break down Azure subscription costs with anomaly and optimization analysis |
| `/az-status [subscription-id] [--days N]` † | Generate a daily Azure subscription activity and health summary |

† user-invoked only (`disable-model-invocation`) · ‡ runs forked, reports a summary

<!-- generated:skills end -->
