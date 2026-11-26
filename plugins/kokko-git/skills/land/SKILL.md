---
name: land
description: Commit, push, deploy to the repo's documented environment, verify the deployment, and merge to the default branch with a merge commit. Use when one request chains these, such as "commit, push, deploy", "push and deploy to the sandbox", "merge to main and deploy", or "merge to main when everything looks ok". For a commit and push with no deploy and no merge, use compush.
argument-hint: '[--env <name>] [--no-deploy] [--no-merge] [--pr-only]'
---

# Land

Take finished work the rest of the way: commit, push, deploy, verify, merge.
Run the stages the request covers, in the order this repo's pipeline needs
them, and stop at the first one that fails.

`$ARGUMENTS`:

| Flag | Effect |
| ---- | ------ |
| `--env <name>` | Deploy to this environment instead of the documented default |
| `--no-deploy` | Commit, push, and merge only |
| `--no-merge` | Commit, push, deploy, and verify; leave the branch unmerged |
| `--pr-only` | Open the pull request and stop before merging it |

Invoked from a sentence rather than a slash command, the sentence decides:
"hold off on deploying" is `--no-deploy`, "don't merge yet" is `--no-merge`.

## 1. Read how this repo ships

Before changing anything, find out, from the repo and not from memory:

- **Deploy path.** `CLAUDE.md` (a deploy section), then `DEPLOYMENT.md` and
  `docs/`, then the pipeline definitions (`.github/workflows/`,
  `azure-pipelines*.yml`, `pipelines/`). You need: the environment's name,
  what triggers a deploy (a push to a branch, a merge, a manually started
  pipeline, a script), the URL, and the health endpoint.
- **Off-limits environments.** Anything the docs or the user call
  production, or that another team deploys. This skill never deploys there,
  never asks for access to it, and never starts its pipeline. For such an
  environment the job ends at the merge, with a note of what its owner has
  to run.
- **Host and default branch.** See
  `${CLAUDE_PLUGIN_ROOT}/references/hosts.md` for telling GitHub from Azure
  DevOps and for every pull request and pipeline command below.
- **Test commands.** The ones the docs name; do not invent any.

When the deploy target is not documented and the request does not name one,
ask once with AskUserQuestion. Then write the answer into `CLAUDE.md` under
a `## Deploy` heading (environment, resource group or cluster, trigger,
URL, health endpoint), so the next run reads it instead of asking.

## 2. Commit and push

Read `${CLAUDE_PLUGIN_ROOT}/skills/compush/SKILL.md` and follow its steps:
the identity check, staging by explicit path, the secret scan, pre-commit,
Conventional Commits, one logical change per commit, and no force of any
kind. Push the current branch.

## 3. Gate before deploying

Run the repo's checks: pre-commit across the tree and the test suites the
docs name. When the request says time is short or to skip checks, run only
the tests that cover what changed, and list what was skipped in the report.

A red gate stops the run. Report the failing output. Deploy on red only
when this request says to.

## 4. Deploy

Use the documented path and nothing else; do not build a second way to
deploy.

- **A pipeline deploys on push to this branch.** The push in step 2 was the
  deploy. Find its run and follow it.
- **A pipeline deploys on merge to the default branch.** Merge first (step
  6), then follow the run and verify. The order becomes commit, push,
  merge, deploy, verify.
- **A pipeline is started by hand.** Start it on the pushed branch.
- **A script or CLI command deploys.** Run the documented command.

Follow the run to its end. A run that finishes failed or cancelled is a
failed deploy even when the app still answers, because the previous
revision is what is answering. Say so, with the run link.

Then confirm that what is live is this commit: compare the run's source
commit, the image tag, or the active revision against `git rev-parse HEAD`.

## 5. Verify the deployment

Verify in the deployed environment, not locally:

- The health endpoint answers, and the new revision is the one serving.
- The change itself works. Exercise the behavior this change touched: call
  the endpoint, or for a visible change drive the page with `playwright-cli`
  headless and look at the screenshots (desktop width, and mobile width
  when layout changed).
- The repo's deployed smoke or end-to-end suite passes, when it has one.
- The logs since the deploy show no new errors.

When sign-in blocks automated checks, verify what is reachable (health,
revision state, logs) and list what the user has to check by hand. Report as
verified only what you observed.

If verification fails, fix forward with a new commit and start again from
step 2. Where the environment is shared and now broken, roll back with the
documented mechanism first and say that you did.

## 6. Merge to the default branch

Skip this when the work is already on the default branch (the push was the
merge) or with `--no-merge`.

1. Open a pull request. Title: the Conventional Commit subject. Body: what
   changed, and what was verified and how.
2. Wait for its required checks.
3. Stop here with `--pr-only`.
4. Merge with a merge commit. Never squash, never rebase-merge, never force
   push, and never bypass a required review or a branch policy: when one
   blocks the merge, stop and report the pull request link.
5. Bring the local default branch up to date
   (`git switch <default>` then `git pull --ff-only`).
6. When the default branch has its own deploy pipeline, follow that run and
   repeat step 5's health and change checks against what it deployed.

Leave the source branch in place unless the host deletes it on merge.

## 7. Report

Keep it short: the commits made, where it was deployed with the run's
status and link, what was verified and how, what was not verified, the
state of the pull request or merge, and anything left for the user. When
the deploy docs turned out to be wrong, say which line.
