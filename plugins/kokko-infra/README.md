# kokko-infra

Azure skills for the demo and sandbox environments a project runs in: let a
person in, and control when the environment is awake. Both drive the `az`
CLI, which must be installed and logged in. They pass `--subscription`
explicitly instead of switching the CLI's default, act only on the
environment named, and never on one the repo's docs call production.

```bash
/plugin install kokko-infra@kokko-ng-kokko-cmds
```

## Skills

<!-- generated:skills start -->

| Skill | Purpose |
| ----- | ------- |
| `/az-access <email>... [to <app, resource group, or project>] [as <role>]` | Give a person access to a deployed Azure app, a resource group, or an Azure DevOps project, confirm the grant, and draft the note to send them |
| `/az-demo <up\|down\|status> [<app or resource group>] [--until <time>] [--schedule "<days> <start>-<end> <timezone>"]` | Wake a demo or sandbox environment in Azure, keep it awake until a set time, put it back to sleep, or report what state it is in |

† user-invoked only (`disable-model-invocation`) · ‡ runs forked, reports a summary

<!-- generated:skills end -->

## Notes

`/az-access` finds which layer is refusing a person (tenant membership, the
app's sign-in assignment, roles inside the app, Azure RBAC, Azure DevOps)
and grants at that layer only, then drafts the note to send them.

`/az-demo` records what it changes so `down` restores it. A timed revert
(`--until`, `--schedule`) runs in Azure or in the project's own pipelines,
never on the machine the session is on.

`/az-costs` and `/az-status` have been removed; see the changelog.
