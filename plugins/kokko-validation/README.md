# kokko-validation

Two skills for the stretch between "it works" and "the client is happy with
it".

`/feedback` takes a batch of feedback (a meeting transcript, an email, a
Word or Excel file, screenshots, an in-app feedback board), turns it into
discrete items in one cumulative ledger, marks the ones the product already
satisfies, and then fixes and verifies the rest one by one. Batches overlap;
the ledger is what stops an ask being done twice or lost.

`/tailor` instantiates the aesthetics master prompt for the current repo: a
screenshot-driven visual review and fix pass, meant to run unattended over
every page, state, and theme. The agent drives the browser with the
Playwright CLI, since visual defects cannot be judged by assertions, and
takes its design judgement from the
[impeccable](https://github.com/pbakaus/impeccable) plugin, which must be
installed where the prompt runs: `/impeccable audit` and
`/impeccable critique` review each page against the screenshots, and
impeccable's refine commands (`polish`, `layout`, `typeset`, `adapt`,
`clarify`, ...) make the fixes, inside the prompt's frontend-only scope.

```bash
/plugin install kokko-validation@kokko-ng-kokko-cmds
# The aesthetics prompt also needs impeccable:
/plugin marketplace add pbakaus/impeccable
/plugin install impeccable@impeccable
```

## Skills

<!-- generated:skills start -->

| Skill | Purpose |
| ----- | ------- |
| `/feedback [<file, folder, or pasted text>...] [--ledger <path>] [--plan-only]` | Turn a batch of feedback into a ledger of discrete items, skip the ones already done, then fix and verify each of the rest |
| `/tailor [aesthetics] [hints such as the frontend directory or theme names]` | Instantiate the aesthetics master prompt for the current repo and save it to prompts/ |

† user-invoked only (`disable-model-invocation`) · ‡ runs forked, reports a summary

<!-- generated:skills end -->

## Notes

The feedback ledger defaults to `docs/feedback-ledger.md` and is committed
with the code, so it holds requirements, not correspondence: no names, no
quoted emails.

The tailored aesthetics prompt keeps its state in
`prompts/aesthetics-progress.md`, so running it again in a fresh session
resumes where the last pass stopped. The template lives in
`skills/tailor/references/aesthetics.md`.

The local-validation, deployed-validation, and azure-deploy templates have
been removed; see the changelog. `/land` (kokko-git) covers shipping and
verifying a change.
