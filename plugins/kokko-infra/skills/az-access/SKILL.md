---
name: az-access
description: Give a person access to a deployed Azure app, a resource group, or an Azure DevOps project, confirm the grant, and draft the note to send them. Use when the user asks to give, grant, or add someone's access, or to fix an access-denied, RBAC-denied, or "needs approval" error that someone hit on a demo or sandbox.
argument-hint: '<email>... [to <app, resource group, or project>] [as <role>]'
---

# Azure Access

Let the named people into the named thing, at the layer that is keeping
them out, and no further.

`$ARGUMENTS` (or the request) gives: who (one or more email addresses), the
target (an app or its URL, a resource group, a subscription, an Azure DevOps
project), and optionally the role.

## Rules

- Only the people named, only the target named. No group-wide, tenant-wide,
  or subscription-wide grant as a shortcut to a narrower one.
- Smallest scope and lowest role that does the job. `Owner`, and admin
  roles inside an app, only when the request says so in those words.
- Never grant into, or probe, an environment the docs or the user call
  production or off limits.
- When the CLI is refused (403, `Authorization_RequestDenied`, an
  interactive sign-in is needed), do not look for another route. Give the
  user the exact command to run themselves (`! <command>` in the prompt),
  then carry on once they say it is done.

## 1. Pin down the target

```bash
az account show --query "{subscription:name,tenant:tenantId,user:user.name}"
```

The CLI's default subscription is often not the one the target lives in.
Find the resource first (the repo's `CLAUDE.md` or deploy docs name the
resource group; otherwise `az resource list --name <name>` across
`az account list`), then pass `--subscription` on each command rather than
switching the default with `az account set`.

When the target or the role is still ambiguous after that, ask once.

## 2. Find the layer that refuses them

A person can be stopped at several layers. Check them in this order, and
grant only where the check shows a gap.

| Layer | Check | A gap looks like |
| ----- | ----- | ---------------- |
| Tenant membership | `az ad user list --filter "mail eq '<email>' or userPrincipalName eq '<email>'"` | Empty result |
| App sign-in (Easy Auth with assignment required) | `az containerapp auth show` or `az webapp auth show` for the client id, then `az ad sp show --id <client id> --query "{id:id,required:appRoleAssignmentRequired,roles:appRoles[].{value:value,id:id}}"` | `required` is true and the person is not in `appRoleAssignedTo` |
| Roles inside the app | The repo's docs: an admin table, an allow-list setting, an app role | The person signs in but sees a denied page or a reduced view |
| Azure RBAC | `az role assignment list --assignee <object id> --scope <scope> --include-inherited` | No assignment that covers what they need |
| Azure DevOps | `az devops user show --user <email> --org <org url>` | Not found, or found without membership of the project's groups |

### Tenant: invite a guest

```bash
az rest --method post --url https://graph.microsoft.com/v1.0/invitations \
  --body '{"invitedUserEmailAddress":"<email>","inviteRedirectUrl":"<app url>","sendInvitationMessage":true}' \
  --query "{id:invitedUser.id,status:status}"
```

The `id` returned is the object id the later grants need. The person cannot
sign in until they redeem the invitation, so say that in the note.

### App sign-in: assign them to the enterprise application

```bash
az rest --method get \
  --url "https://graph.microsoft.com/v1.0/servicePrincipals/<sp object id>/appRoleAssignedTo" \
  --query "value[].{who:principalDisplayName,role:appRoleId}" -o table
az rest --method post \
  --url "https://graph.microsoft.com/v1.0/servicePrincipals/<sp object id>/appRoleAssignedTo" \
  --body '{"principalId":"<user object id>","resourceId":"<sp object id>","appRoleId":"<role id>"}'
```

`<role id>` is the id of the app role that matches what was asked for. An
app that defines no roles takes the default access id,
`00000000-0000-0000-0000-000000000000`.

### Roles inside the app

Follow what the repo documents, and nothing else: its admin API, its seed
script, its setting. If the docs do not say how a role is granted, read the
code that checks the role before changing any data, and say what you found.

### Azure RBAC

```bash
az role assignment create --assignee-object-id <object id> \
  --assignee-principal-type User --role "<role>" --scope "<scope>"
```

Without a named role: `Reader` to look, `Contributor` to work. Scope it to
the resource group unless the request names something wider.

### Azure DevOps

```bash
az devops user add --email-id <email> --license-type express --org <org url>
az devops security group list --project <project> --org <org url> \
  --query "graphGroups[].{name:displayName,descriptor:descriptor}" -o table
az devops security group membership add --group-id <descriptor> --member-id <email> --org <org url>
```

`express` is the Basic licence, which repos and pipelines need;
`stakeholder` covers boards only. Groups: Readers, Contributors, or Project
Administrators, the lowest that fits.

## 3. Confirm

Read each grant back with the listing command for its layer. A guest whose
invitation is still pending counts as granted but not yet usable. You cannot
sign in as them, so report what was confirmed (the grant exists) apart from
what was not (that their sign-in works).

## 4. Draft the note

A short plain-text message the user can paste and send:

- the link;
- which account to sign in with, and that a guest must accept the invitation
  email first;
- what they can now do;
- that the first load can take a minute, when the app scales to zero.

No resource ids, no role ids, nothing about how the grant was made.

## 5. Report

One table: person, layer, what was granted, confirmed or not. Then the
note. Then anything the user has to run or decide.
