# Git Hosts: GitHub and Azure DevOps

Shared command reference for the kokko-git skills that open, check, and merge
pull requests or watch pipelines. This is a reference file, not a skill to
invoke.

## Which host

```bash
git remote get-url origin
```

| Remote URL contains | Host | CLI |
| ------------------- | ---- | --- |
| `github.com` | GitHub | `gh` |
| `dev.azure.com`, `ssh.dev.azure.com`, `visualstudio.com` | Azure DevOps | `az repos`, `az pipelines` |
| anything else | unknown | none: push the branch and give the user the URL |

A repo with two remotes (a GitHub mirror and an Azure DevOps origin, for
example) ships through the one its pipelines run on. Read the repo's
`CLAUDE.md` before assuming `origin`.

Azure DevOps commands need the `azure-devops` extension
(`az extension add --name azure-devops`). Inside a clone they detect the
organization, project, and repository from the remote. Outside one, or when
detection fails, pass `--org https://dev.azure.com/<org>` and
`--project <project>`. Commands that take a pull request `--id` accept `--org`
only, not `--project`.

## Default branch

```bash
git symbolic-ref --short refs/remotes/origin/HEAD
```

Strip the `origin/` prefix. If it errors, read the `HEAD branch:` line of
`git remote show origin`. Never assume `main`.

## Pull requests

| Step | GitHub | Azure DevOps |
| ---- | ------ | ------------ |
| Open | `gh pr create --base <default> --title "<subject>" --body "<body>"` | `az repos pr create --source-branch <branch> --target-branch <default> --title "<subject>" --description "<body>"` |
| State | `gh pr view <n> --json state,mergeable,reviewDecision` | `az repos pr show --id <n> --query "{status:status,merge:mergeStatus}"` |
| Checks | `gh pr checks <n> --watch` | `az repos pr policy list --id <n> --query "[].{policy:configuration.type.displayName,status:status}" -o table` |
| Merge | `gh pr merge <n> --merge` | `az repos pr update --id <n> --status completed --squash false --delete-source-branch false` |
| Merged PRs for a branch | `gh pr list --state merged --head <branch> --json number,title` | `az repos pr list --source-branch <branch> --status completed --query "[].{id:pullRequestId,title:title}"` |

Merge rules, on both hosts:

- Always a merge commit. Never `--squash`, `--rebase`, or
  `--squash true`: a squash rewrites the branch's commits into one and loses
  the per-change history.
- Never bypass a branch policy, a required review, or a failing required
  check. When one blocks the merge, stop and report the pull request link and
  what is outstanding.
- Checks still running: on GitHub add `--auto` to the merge so it completes
  when they pass. On Azure DevOps use
  `az repos pr update --id <n> --auto-complete true --squash false` and then
  poll `az repos pr show`.

## Pipelines

| Step | GitHub | Azure DevOps |
| ---- | ------ | ------------ |
| Runs for a branch | `gh run list --branch <branch> --limit 5` | `az pipelines runs list --branch <branch> --top 5 --query "[].{id:id,name:definition.name,status:status,result:result}" -o table` |
| Runs for a pull request | `gh pr checks <n>` | `az pipelines runs list --branch refs/pull/<n>/merge --top 5 -o table` |
| Start a run | `gh workflow run <workflow file> --ref <branch>` | `az pipelines run --id <definition id> --branch <branch>` |
| Follow a run | `gh run watch <run id> --exit-status` | `az pipelines runs show --id <run id> --query "{status:status,result:result}"`, polled until `status` is `completed` |
| Which commit ran | `gh run view <run id> --json headSha` | `az pipelines runs show --id <run id> --query sourceVersion -o tsv` |

A run that ends `failed`, `canceled`, or `partiallySucceeded` is not a pass,
whatever the deployed app is doing: report the status the host reports.
