---
name: upstream-fix
description: Carry the corrections made in this session back into the skill, plugin, or template that produced the flawed output, as a pull request with a version bump. Use when the user asks to fix a skill so a mistake does not happen again, to write a pull request against a skill or plugin repo for issues found in this session, or to push a local skill fix upstream.
argument-hint: '[<skill or plugin name>] [--repo <owner/name>] [--merge]'
---

# Upstream Fix

When a skill's output had to be corrected by hand, the correction is worth
more in the skill than in the one project where it was noticed. This skill
moves it there.

`$ARGUMENTS`: the skill or plugin to fix (default: the one whose output was
corrected in this session), `--repo <owner/name>` when its source repo is
not discoverable, and `--merge` to merge the pull request once its checks
pass. Without `--merge`, and without the request saying to merge, stop at
the open pull request.

## 1. List the corrections

Go back through this session and list each thing the user had to point out,
or that you had to repair by hand, in output the skill produced. For each
one write down:

- the symptom, as the user saw it;
- the cause inside the skill: a missing rule, a wrong template or default,
  a missing check, an instruction that reads two ways;
- whether it is general or belongs to this project only.

Leave out:

- **Project-specific preferences** (this client's wording, this repo's
  layout). Those belong in the project's `CLAUDE.md`; say so and offer to
  put them there.
- **Anything the user took back** later in the session.
- **Defects in the project's own content** that the skill did not cause.

If nothing general is left, say that and stop.

## 2. Find the source repo

In order: `--repo`; the marketplace the plugin was installed from
(`claude plugin list --json`, then `claude plugin marketplace list --json`
for that marketplace's source); the project's `skills-lock.json`; a `.git`
directory or source note inside the installed skill.

The installed copy under `~/.claude/plugins/` or `~/.claude/skills/` is not
the place to make the fix: the next update overwrites it. If the source
repo cannot be worked out, ask.

## 3. Get a clean clone

Use an existing clone when the machine has one and its working tree is
clean (fetch first; branch from the remote default branch, not from
whatever is checked out). Never build on someone's uncommitted work: with a
dirty tree, add a worktree or clone again next to it. Otherwise clone
beside the current project, not inside it.

```bash
gh repo view <owner/name> --json viewerPermission,visibility,defaultBranchRef
```

Without write permission, fork and open the pull request from the fork. A
fork of a private repo stays private. Never change the visibility of any
repo, original or fork.

Read the repo's `CONTRIBUTING.md` and `README.md` for its lint, tests,
commit conventions, and release flow before editing.

## 4. Make each correction general

For every correction, pick the strongest form that fits:

1. **A mechanical check**, when the defect can be detected: a lint rule, a
   renderer or validator check, a test. A check cannot be skimmed past.
2. **A fixed template or default**, when the skill's own starting material
   was the cause.
3. **A rule with its reason**, placed at the point where the skill makes
   that decision, with the failing case as a short example.

Keep the skill's structure and voice. Do not add a "lessons learned"
section, and do not paste the project's content into the skill: reduce the
failing case to a generic example with no client, person, or product names.

## 5. Prove it

Re-run the part of the skill that failed against the case from this
session, from the edited source, and confirm the defect is gone. Run the
repo's lint and tests. A correction you could not reproduce and re-check is
reported as unverified, not dropped silently.

## 6. Open the pull request

- A branch from the default branch; one commit per correction, in the
  repo's commit convention, under the identity its history uses.
- The version bump and changelog entry the repo's release flow asks for, in
  the same pull request. Use the repo's bump script or release skill when
  it has one.
- Pull request body: one line per correction, symptom then change, and how
  each was verified.

## 7. Merge, only when told to

With `--merge`, or when the request said to merge: wait for the checks,
merge with a merge commit (never a squash), confirm the release the repo's
flow publishes, then update the installed copy
(`claude plugin marketplace update <marketplace>` and
`claude plugin update <plugin@marketplace>`, or the skills tool the project
uses) and tell the user to run `/reload-plugins`.

## 8. Report

The pull request link, the corrections it carries, the ones left out and
why, the new version, and whether the installed copy has been updated.
