---
name: az-demo
description: Wake a demo or sandbox environment in Azure, keep it awake until a set time, put it back to sleep, or report what state it is in. Use when the user asks to make sure a demo is up and running, to stop an app scaling to zero, to keep something on until a time or for some hours, to set business-hours availability, or to spin resources down to save cost.
argument-hint: '<up|down|status> [<app or resource group>] [--until <time>] [--schedule "<days> <start>-<end> <timezone>"]'
---

# Azure Demo Power

Bring a demo environment up, hold it up for as long as it is needed, and
return it to its cheap state afterwards.

`$ARGUMENTS`:

| Argument | Meaning |
| -------- | ------- |
| `status` | Report each sleeping piece and whether the app answers. Changes nothing |
| `up` | Wake everything the app needs and confirm it answers |
| `down` | Return each piece to its baseline |
| `<app or resource group>` | What to act on. Default: the environment the repo's `CLAUDE.md` or deploy docs name |
| `--until <time>` | With `up`: go back down at this time ("22:00", "in 6 hours") |
| `--schedule "..."` | Recurring window, for example `"Mon-Fri 06:00-22:00 Australia/Sydney"` |

## Rules

- Act only on the environment named. Never on one the docs or the user call
  production or off limits.
- Pass `--subscription` on each command; do not switch the CLI's default
  subscription.
- `down` restores what was there before. It deletes nothing unless the
  request says delete, and then only resources the request names or this
  session created, after showing the list.
- A timed revert must not depend on this session, this machine, a local
  cron entry, or a sleep loop. If no mechanism below is available, say so and
  give the user the command and the time instead of promising it.

## 1. Find the pieces that sleep

```bash
az resource list -g <resource group> --subscription <subscription> \
  --query "[].{name:name,type:type}" -o table
```

| Resource | State | Up | Down |
| -------- | ----- | -- | ---- |
| Container App | `az containerapp show -n <app> -g <rg> --query "{min:properties.template.scale.minReplicas,max:properties.template.scale.maxReplicas,rules:properties.template.scale.rules[].name}"` | `az containerapp update -n <app> -g <rg> --min-replicas 1` | `--min-replicas 0` |
| AKS cluster | `az aks show -n <cluster> -g <rg> --query powerState.code -o tsv` | `az aks start -n <cluster> -g <rg> --no-wait` | `az aks stop -n <cluster> -g <rg> --no-wait` |
| AKS node pool with the autoscaler | `az aks nodepool show --cluster-name <cluster> -g <rg> -n <pool> --query "{min:minCount,max:maxCount,count:count}"` | `az aks nodepool update --cluster-name <cluster> -g <rg> -n <pool> --update-cluster-autoscaler --min-count 1 --max-count <max>` | same, `--min-count 0` |
| App Service | `az webapp show -n <app> -g <rg> --query state -o tsv` | `az webapp start -n <app> -g <rg>` | `az webapp stop -n <app> -g <rg>` |
| Azure SQL, serverless tier | `az sql db show -n <db> -s <server> -g <rg> --query "{status:status,autoPause:autoPauseDelay}"` | `az sql db update -n <db> -s <server> -g <rg> --auto-pause-delay -1` | restore the previous delay |
| PostgreSQL flexible server | `az postgres flexible-server show -n <server> -g <rg> --query state -o tsv` | `az postgres flexible-server start -n <server> -g <rg>` | `az postgres flexible-server stop -n <server> -g <rg>` |
| Virtual machine | `az vm show -d -n <vm> -g <rg> --query powerState -o tsv` | `az vm start -n <vm> -g <rg>` | `az vm deallocate -n <vm> -g <rg>` |

Wake things in dependency order (database, then cluster or backend, then
frontend) and put them down in reverse. Check the repo first for a power
mechanism of its own (a pipeline or workflow that starts and stops the
environment on a schedule): when there is one, drive that rather than
calling the resources directly, so the two do not fight.

## 2. `status`

Print the state of each piece, then request the app's health URL and report
the HTTP status. A `401` or a redirect to sign-in from an app behind Entra
sign-in counts as up.

## 3. `up`

1. Record the current setting of every piece you are about to change. That
   record is what `down` restores, and it goes in the report.
2. Apply the Up column.
3. Wait until it is real: the new Container App revision is running and
   healthy (a scale change creates a revision), the cluster reports
   `Running` and the workloads are ready, the database is online.
4. Request the health URL until it answers.

## 4. `--until` and `--schedule`

Pick the first mechanism that applies:

1. **The repo's own power schedule.** Change its window or run it with
   parameters, and say what to restore if the change is a one-off.
2. **Container Apps: a cron scale rule.** The platform scales to the wanted
   replicas inside the window and back to the minimum outside it:

   ```bash
   az containerapp update -n <app> -g <rg> --min-replicas 0 --max-replicas <max> \
     --scale-rule-name awake-window --scale-rule-type cron \
     --scale-rule-metadata timezone=<IANA zone> start="<cron>" end="<cron>" desiredReplicas=1
   ```

   The cron fields are minute, hour, day of month, month, day of week. A
   recurring weekday window is `start="0 6 * * 1-5"`, `end="0 22 * * 1-5"`.
   A one-off pins the day and month (`start="0 6 12 10 *"`), and the rule
   has to be removed afterwards or it fires again next year.

   Passing `--scale-rule-name` replaces the app's whole rule list with that
   one rule; the CLI cannot add a rule beside existing ones. When step 1
   showed the app already has rules (an HTTP concurrency rule, a queue
   rule), do not use the flags: export the app with
   `az containerapp show -o yaml`, add the cron rule to
   `properties.template.scale.rules` next to the others, and apply it with
   `az containerapp update --yaml <file>`. Compare the rule names before and
   after either way. `--min-replicas` and `--max-replicas` without a rule
   name leave the rules alone.
3. **Anything else: a scheduled pipeline in the project's own repo.** A
   GitHub Actions workflow or an Azure DevOps pipeline with a cron trigger
   that runs the Down command, using the credentials the repo's deploy
   pipeline already has. Schedules there are in UTC: convert, and state both
   times. This is a code change, so it goes through the repo's normal commit
   and review flow.

State the time zone you used whenever you state a time.

## 5. `down`

Apply the Down column, or the recorded settings from the last `up` when the
session has them. Then say what keeps costing money while the environment is
down: container registries, storage, non-serverless databases, App Service
plans, AKS disks and public IPs, provisioned AI throughput.

## 6. Report

One table: resource, before, after, confirmed. Then the health check
result, the revert mechanism and when it fires, and anything left running
on purpose.
