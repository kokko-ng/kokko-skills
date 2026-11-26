---
name: worklog
description: Write up the work done in one or more repos over a date range, from git history, as plain text ready for a timesheet. Use when the user asks for a timesheet entry, a "what I did" or "what was done" summary, a weekly write-up, or a non-technical account of recent work.
argument-hint: '[<range such as "this week" or 2026-09-07..2026-09-11>] [--repos <dir>...] [--per day|week|blocks:<n>] [--sentences <n>] [--technical]'
allowed-tools: Bash(git:*), Bash(gh:*), Bash(ls:*), Bash(date:*), Read
---

# Work Log

Turn git history into a short written account of what was done, in the
shape a consulting timesheet wants. The output is text in the reply. This
skill writes no file and changes nothing.

`$ARGUMENTS`:

| Argument | Default | Meaning |
| -------- | ------- | ------- |
| range | Monday of this week to today | Dates to cover: "this week", "last week", "yesterday", or `from..to` |
| `--repos <dir>...` | the current repo | Repos to read. A directory that is not a repo stands for every repo directly inside it |
| `--per` | `day` | One entry per `day`, one per `week`, or `blocks:<n>` for n entries of similar size in time order, not tied to dates |
| `--sentences <n>` | 3 | Sentences per entry |
| `--technical` | off | Allow technical terms; the default is plain language |

Anything the request spells out wins over these defaults: a sentence or
bullet count, a layout, an audience, or a fact to include ("worked with the
client's architect on feasibility those three days").

## Steps

### 1. Resolve the range and the author

```bash
date +%Y-%m-%d
git config user.email
git config user.name
```

Work out the first and last day of the range from today's date. The author
is the configured email. If that finds nothing while the repo has commits
by the same name under another address, use the name instead and say so.

### 2. Collect the history

In each repo:

```bash
git log --all --no-merges --author="<email>" \
  --since="<from> 00:00" --until="<to> 23:59" \
  --date=format:'%Y-%m-%d %a' --format='%ad | %s' --stat
git status --short
```

`--all` matters: it includes local branches that were never pushed and
branches in other worktrees, which is where the current week's work
usually sits. `git status` shows work in progress that has no commit yet;
count it under today.

When a commit subject does not say what the change was for, read the commit
(`git show --stat <sha>`, then the diff of the files that matter) rather
than paraphrasing the subject.

To cover every repo the user has pushed to, not just local clones, ask the
host:

```bash
gh api user --jq .login
gh search commits --author=<login> --author-date=<from>..<to> --limit 200 --json repository,commit
```

### 3. Group

- `day`: by author date. A day inside the range with no commits gets no
  entry; list such days at the end so the user can fill them in. Never
  spread one day's work over empty days to make the week look even.
- `week`: one entry per calendar week.
- `blocks:<n>`: order the work in time, then cut it into n pieces of similar
  size along its natural seams (a feature, a fix series, a deployment).

Within a group, merge commits that belong to one piece of work. Ten commits
on one feature are one sentence, not ten.

### 4. Write

Each entry says what was achieved and why it mattered to the project, in
the past tense, without "I".

- Plain language by default. Describe the outcome ("users can now download
  the files a reply cites") rather than the mechanism ("added a blob SAS
  endpoint"). Name a technology only when the reader would know it.
- Never include commit hashes, branch names, file paths, pull request
  numbers, or times of day.
- Only what the history supports. Do not invent meetings, reviews, people,
  or hours. A fact the user supplied in the request goes in as they gave it.
- Do not inflate: a one-line fix is not "a comprehensive overhaul".
- Exactly the number of sentences asked for, per entry.

Layout for `day`, plain text so it pastes anywhere:

```text
Mon 7 Sep
<sentence>. <sentence>. <sentence>.

Tue 8 Sep
...
```

With several repos, write one entry per day per project, the project name
on the heading line.

### 5. Close

After the entries, in one or two lines: the days in the range with no
commits, and how thin the evidence was when it was thin ("Wednesday rests
on two commits"). Nothing else.
