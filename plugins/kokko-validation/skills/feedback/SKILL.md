---
name: feedback
description: Turn a batch of feedback into a ledger of discrete items, skip the ones already done, then fix and verify each of the rest. Use when the user asks to action, act on, or address feedback from a meeting transcript, an email or chat message, a Word or Excel file, screenshots, or an in-app feedback board.
argument-hint: '[<file, folder, or pasted text>...] [--ledger <path>] [--plan-only]'
---

# Feedback

Feedback arrives in overlapping batches: a review call, then an email that
restates half of it, then a spreadsheet with six new rows among forty old
ones. This skill keeps one ledger so that every ask is done once, checked
once, and never lost.

`$ARGUMENTS`: the sources (files, a folder, or text pasted with the
request), `--ledger <path>` to use a ledger other than the default, and
`--plan-only` to stop once the ledger is written.

## 1. Read every source in full

- Word and PDF files, transcripts (`.vtt`, `.txt`), spreadsheets (every
  sheet, with comments and any status column), images and screenshots, and
  every file in a folder that was named.
- An in-app feedback board: through the API or table the repo documents.

Read a transcript from start to end. Decisions and asks are scattered
through it, and a keyword search misses the ones phrased as a passing
remark.

## 2. Extract the items

One item is one change that can be verified by itself. For each:

| Field | Content |
| ----- | ------- |
| ID | `F-001`, counting on from the ledger's last id |
| Ask | One plain sentence stating what should be true afterwards |
| Where | The page, component, endpoint, or document it concerns |
| Source | A short label: "review call, 14 Sep" |
| Type | bug, change, copy, question, or out of scope |

Split an ask that bundles two changes. Merge two phrasings of one ask. A
remark with no ask in it is not an item. Copy changes keep the wording
exactly as given.

The ledger is committed with the code, so write asks as requirements, not
quotations: no names of people, no pasted correspondence, no paths to files
outside the repo. If the repo's `CLAUDE.md` restricts what may be committed
about the engagement, follow it. If you cannot tell, keep the ledger at an
ignored path and say so.

## 3. Write the ledger

Default path `docs/feedback-ledger.md`; reuse an existing ledger if the repo
already has one. It is cumulative: new batches append to it.

```markdown
| ID | Ask | Where | Source | Type | Status | Evidence |
| -- | --- | ----- | ------ | ---- | ------ | -------- |
```

Status is one of: open, done, already done, needs decision, blocked, out of
scope.

## 4. Find what is already done

Before changing anything, check every new item against:

1. the ledger: an earlier item with the same ask;
2. the code as it stands: read the component, run the behavior;
3. the history: `git log --grep` and recent commits to that area.

Where the product already does what is asked, mark the item already done,
put the commit or file in Evidence, and leave the code alone. Then report
the split before starting work: how many items, how many new, how many
already done.

## 5. Settle what needs a decision

Mark an item needs decision when it is ambiguous, contradicts another item
or an earlier decision, goes against the design system, or adds scope or
running cost. Put all of them to the user in one round of AskUserQuestion.
Do not resolve a contradiction by picking a side silently. Everything else
proceeds without waiting.

With `--plan-only`, stop here and report the ledger.

## 6. Do the work

Group the open items by area and make the smallest change that satisfies
each. Add nothing that was not asked for. Commit per item or per tight
group, with the ledger ids in the commit body.

## 7. Verify each item

- Behavior changed: a test that fails without the change and passes with
  it.
- Anything visible: look at it. Run the app, capture the page with
  `playwright-cli` headless at the state concerned (desktop width, and
  mobile width where layout is involved), and read the screenshot. The same
  defect elsewhere in the app is part of the item: fix every instance, not
  the one in the screenshot.
- Copy: the text on the page matches the wording given, character for
  character.

Write what you observed into Evidence and set the item to done only then.
When every item is finished, run the full test suite and pre-commit once,
and confirm nothing that worked before has stopped working.

## 8. Report

The ledger's table for this batch, then what is blocked or awaiting the
user. If the request also said to commit, push, deploy, or merge, continue
with those steps now (the `land` skill in kokko-git, where installed).
