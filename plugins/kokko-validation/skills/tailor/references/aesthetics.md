<!--
TAILORING NOTES (for the /tailor skill -- delete this entire comment in the tailored output)

Placeholders. Every {{...}} must be resolved. Sources, in order: user hints,
repo inspection, then ask the user. Never invent values.

  APP_NAME                    Application name
  PROGRESS_FILE               Defect ledger path, e.g. prompts/aesthetics-progress.md
  FRONTEND_FRAMEWORK / FRONTEND_START_COMMAND / FRONTEND_URL
  FRONTEND_DIR                Repo-relative frontend source directory, e.g. frontend/src
                              (Core Definitions and the final impeccable detector scan)
  BACKEND_FRAMEWORK / BACKEND_START_COMMAND / BACKEND_URL
  THEMES                      Theme list, e.g. "dark, light" (single-theme apps: delete the theming blocks)
  TYPE_CHECK_COMMAND          Command(s) that must pass with zero errors
  DESKTOP_STATES              Real page/state list to screenshot at 1280px (enumerate from the router):
                              one entry per page with its route and source file, then its states
  MOBILE_STATES               Real page/state list to screenshot at 375px, same shape

Give the authentication pages their source files as well, e.g.
"Login page (src/pages/Login.tsx), empty form": impeccable commands take
the page's source file as their target.

Design engine. The prompt hands design judgement to the impeccable plugin
(impeccable@impeccable, marketplace pbakaus/impeccable). Keep the
"Design Engine -- impeccable" section, the review step, and the fix routing
as written: tailoring fills placeholders and repo detail, it does not swap
the engine or hand-write defect categories back in. Record in the generation
header whether PRODUCT.md and DESIGN.md exist; the prompt runs without them.

Optional blocks. Delete the whole block when it does not apply, together
with every line elsewhere tagged with the block name in brackets, e.g.
"[theming]" (at the start of the line, list item, or table row). When the
block applies, keep the line and strip just the tag.

  theming       App has more than one theme.
  registration  App has self-service user registration.

No {{...}} token, no [tag] marker, and none of these notes may remain in the
tailored output.
-->

# {{APP_NAME}} -- Aesthetics & UI Fix Prompt

## Core Definitions

| ID         | Value                                                                  |
| ---------- | ---------------------------------------------------------------------- |
| `frontend` | {{FRONTEND_FRAMEWORK}} on `{{FRONTEND_URL}}`, source in `{{FRONTEND_DIR}}` |
| `backend`  | {{BACKEND_FRAMEWORK}} on `{{BACKEND_URL}}`                             |
| `tool`     | Playwright CLI (`playwright-cli`)                                      |
| `design`   | impeccable skill (`/impeccable <command> [target]`, plugin `impeccable@impeccable`) |
| `ledger`   | `{{PROGRESS_FILE}}`                                                    |
| [theming] `themes` | {{THEMES}}                                                     |

---

## Browser Automation -- Playwright CLI

`playwright-cli` in this prompt means the Playwright command-line interface,
driven from the shell: ad-hoc Node scripts using the `playwright` package,
`.spec` files run with `npx playwright test`, or
`npx playwright screenshot <url> <out.png>`. All navigation, snapshots, and
screenshots go through it, because a script can be re-run unchanged for the
confirming re-screenshot of each fix. The Playwright MCP server and its
`mcp__playwright__*` / `browser_*` tools are not used, even when they are
connected.

- Set the viewport explicitly in the script for the 1280px (desktop) and
  375px (mobile) passes.
- If Playwright is not installed, add it first
  (`npm i -D @playwright/test && npx playwright install chromium`).
- Save screenshots outside the repository (the session scratchpad when there
  is one, otherwise a temp directory), named
  `<page>-<state>-<width>[-<theme>].png`, and cite the file name in the
  ledger.
- impeccable's references sometimes prefer the harness's own browser tool.
  Here those steps go through playwright-cli as well: the coverage
  screenshots are the evidence you hand to impeccable, and any page an
  impeccable command needs to open, inspect, or inject a script into is
  opened by a playwright-cli script.

---

## Design Engine -- impeccable

Design judgement in this prompt -- what counts as a defect, how severe it
is, and how to fix it well -- comes from the impeccable skill. This prompt
owns coverage, the ledger, scope, and the definition of done; impeccable owns
the review and the craft of each fix.

### Prerequisite

impeccable must be installed and loaded in this session: `/impeccable` is
among the available skills and `claude plugin list` shows
`impeccable@impeccable` (kokko-devcontainer containers preinstall it). If it
is missing, install it:

```text
/plugin marketplace add pbakaus/impeccable
/plugin install impeccable@impeccable
```

(from a shell: `claude plugin marketplace add pbakaus/impeccable`, then
`claude plugin install impeccable@impeccable`). The skill and its hooks load
only in a new session, so after installing, record the install in the
ledger's session log and stop; the next session resumes from the ledger.
Without impeccable, do not fall back to hand-judged review.

### Setup -- once per session

1. Run impeccable's Setup step once, from the repo root:
   `"<impeccable skill dir>/scripts/impeccable" context`, where the skill dir
   is the folder holding impeccable's `SKILL.md`. It loads `PRODUCT.md`,
   `DESIGN.md`, and the matching surface brief. Do not rerun it later in the
   session. Act on what it reports:
   - **No PRODUCT.md or DESIGN.md:** proceed. This pass refines the
     incumbent interface, and impeccable lets a narrow refinement proceed on
     the incumbent implementation without blocking on `init`; the running
     app, its tokens, and its components are the visual authority. Do not
     run `/impeccable init` or `/impeccable document` here -- both interview
     the user and write project documents. Recommend them in the final
     report instead.
   - **`CONTEXT_STALE`:** note it in the session log; do not repair it
     (impeccable never repairs drift as a side effect of a design task).
   - **`MANUAL_DETECTOR_REQUIRED`:** no detector hook is active, so the
     manual detector runs below replace it.
   - **Launcher failure:** follow impeccable's "Launcher unavailable"
     fallback (read the existing `PRODUCT.md` / `DESIGN.md` directly) and
     note it in the session log.
2. Run `/impeccable hooks status` and note in the session log whether the
   design detector hook is active. Leave its setting as you find it.
3. Before the first UI edit, read impeccable's craft floor
   (`reference/craft-floor.md` in the skill dir), as its Setup requires. It
   applies to every fix in this pass.

### The design detector hook

When the hook is active, every Edit/Write on a UI file returns the
detector's findings automatically, and a deeper pass runs when you stop.
When it is not active, run the detector yourself after each fix batch:
`"<impeccable skill dir>/scripts/impeccable" detect --json <edited files>`.
Either way:

- A finding on code you just changed is part of the current fix: resolve it
  before the confirming screenshot.
- A finding that predates your edit and is not the defect in hand becomes a
  new ledger defect with source `hook` or `detector`.
- Triage false positives the way impeccable's `hooks` reference says: only
  the narrowest `ignore-value` with the evidence in `--reason`, never
  `ignore-file` or `ignore-rule` (those are the user's call), and never an
  ignore to push a fix through. Log every ignore you add in the session log.

### Commands this prompt uses

| Role     | Commands                                                                 | Used for |
| -------- | ------------------------------------------------------------------------ | -------- |
| Evaluate | `audit`, `critique`                                                      | Finding defects, once per page |
| Fix      | `polish`, `layout`, `typeset`, `adapt`, `clarify`, `harden`, `quieter`, `colorize`, `optimize` | Fixing logged defects, inside the Constraints below |
| Not used | `init`, `document`, `shape`, `craft`, `extract`, `bolder`, `overdrive`, `delight`, `animate`, `distill`, `onboard`, `live`, `generate` | Interviews, new work, redesign, new content, or interactive variant picking -- outside a defect-fix pass |

A finding whose suggested command is in the last row gets the nearest Fix
command instead when its fix stays inside the Constraints (a missing
`prefers-reduced-motion` alternative goes through `polish`, not `animate`).
When it needs the new work that command exists for, log it `blocked` (needs
a design decision) and name the suggested command.

### Running impeccable unattended

Some impeccable commands stop to ask the user: critique's closing questions,
polish and clarify before changing factual copy. This prompt answers them in
advance:

- **Priority:** P0, then P1, then P2, then concrete P3 defects; within a
  severity, the pages users reach first.
- **Scope:** every defect the Review step logs, inside the Constraints.
  Anything outside them is logged `blocked`, not changed.
- **Direction:** refinement, not redesign. Keep the incumbent identity,
  tone, palette, type, and copy ("refinement preserves; redesign
  replaces"). A finding that only a new direction would fix is `blocked`
  for a human.
- **Copy:** fix unclear labels, missing accessible names, and broken error
  or empty-state wording; leave factual claims, product terms, and legal
  text alone and log them `blocked`.

End each critique with `Questions skipped: answered in advance by the
aesthetics prompt` and carry on. Audit's and critique's closing offers to run
the recommended commands are not a stopping point either: the ledger and the
Work Cycle below decide what runs next.

### Bounded passes and the definition of done

impeccable verifies in bounded passes: one batched inspection, one batch of
fixes, at most one confirming round, then stop. That bound applies to every
single impeccable run in this prompt: an audit or critique inspects once,
and a fix invocation inspects once, fixes its defects in one batch, and
confirms with at most one more round. No run loops on its own.

The definition of done is still the checklist at the end of this prompt:
the ledger decides whether another bounded run is needed (a defect still
`open` after a run gets another attempt, up to the stuck rule's three).
Re-running audit or critique to chase a higher score is not part of this
pass.

---

## Primary Goal

Work autonomously to identify and fix every visual and UI defect in the
locally running application. playwright-cli screenshots every page, state,
and interactive component; impeccable's `audit` and `critique` review each
page against that evidence; impeccable's refine commands fix each logged
defect; a re-screenshot confirms each fix.

Completion is defined solely by the checklist in the "Completion, Blockers &
Stopping" section at the end of this prompt -- nothing else.

---

## Defect Ledger -- Read First, Update Always

`{{PROGRESS_FILE}}` is the single source of truth for progress. Conversation
memory does not survive context compaction or a fresh session; this file
does. impeccable's own critique snapshots under `.impeccable/critique/` are
its archive, not this pass's progress.

- **On start:** if the file exists, read it and resume from the first
  screenshot pass, page review, or defect not marked done. If it does not
  exist, create it with one line per screenshot pass (viewport x theme) and
  one line per page to review, all `pending`.
- **Pass format:** `P-01 | pending / done | viewport/theme | short note`.
- **Review format:** `R-03 | pending / done | page (source file) | audit NN/20, critique NN/max | short note`
  (critique's maximum drops below 40 when it scores a heuristic `n/a`).
- **Defect format:**
  `D-014 | open / fixed / blocked | page + state | viewport/theme | P0-P3 | source: rule | command | short note`
  -- `source` is `audit`, `critique`, `detector`, `hook`, or `cross-check`;
  `rule` is what the finding cites (detector rule id, audit dimension,
  heuristic, or cross-check item, e.g. `audit: a11y contrast`,
  `detector: side-tab`, `critique: H4 consistency`); `command` is the
  impeccable command that fixes it. Append a line the moment a defect is
  verified; flip it to `fixed` only after the confirming re-screenshot.
- Every line starts with an ID of letters, a hyphen, and digits (`P-01`,
  `R-03`, `D-014`), so open items can be counted by that shape.
- **Observations:** taste-level P3 notes and critique's "questions to
  consider" go as plain bullets (no ID) under an `## Observations` section.
  They are for a human and do not block completion.
- **Update immediately**, never in batches. Append one line to a
  `## Session log` section at the bottom of the file each pass.

---

## Application Setup -- Local

Both servers must be running before any visual testing begins:

```bash
# Backend
{{BACKEND_START_COMMAND}}

# Frontend
{{FRONTEND_START_COMMAND}}
```

Verify the application loads at `{{FRONTEND_URL}}` before starting.

---

## Screenshot Coverage

Screenshot every state listed below at desktop (1280px wide) and mobile
(375px wide). If the layout has tablet-specific breakpoints, add a 768px pass
for the affected pages. Capture interactive components in their hover,
focus, open, and disabled states where the page has them. Each page below
names its source file: that path is the target you pass to impeccable.

<!-- OPTIONAL: theming -->

Repeat full coverage once per theme in {{THEMES}}. Before each theme's pass,
switch to it with the app's theme switcher and confirm it is applied
globally before taking any screenshots.

<!-- END OPTIONAL: theming -->

### Authentication Pages

- Login page (empty form)
- Login page with validation errors (submit empty form)
- [registration] Register page (empty form)
- [registration] Register page with validation errors

### Main Application -- Desktop (1280px)

{{DESKTOP_STATES}}

### Main Application -- Mobile (375px)

{{MOBILE_STATES}}

---

## Review -- impeccable audit and critique per page

Work through the `R-` lines once the screenshot passes are done. For each
page:

1. Gather the page's screenshots from every pass, 1280px and 375px.
   [theming] Include every theme in {{THEMES}}.
2. Run `/impeccable audit <page source file>`: technical checks across
   accessibility, performance, theming, responsive design, and
   implementation integrity, with the detector. It documents; it does not
   fix.
3. Run `/impeccable critique <page source file>`: design review with
   heuristic scores, cognitive load, personas, and the detector as its
   second assessment. When it asks for browser inspection, brief its
   assessments to use the screenshots you already have and playwright-cli
   for anything more; its in-page detector overlay is optional (inject it
   from a playwright-cli script, or report it skipped).
4. Verify each finding against the screenshots and the source before logging
   it; drop confirmed false positives. Log as `D-` lines every verified P0,
   P1, and P2 finding, plus any P3 that is a concrete break (it matches the
   cross-check below), each with its source, rule, and suggested command.
   Other P3 notes go to Observations.
5. Walk the rendered cross-check below over the page's screenshots and log
   what it finds with source `cross-check`.
6. Mark the `R-` line `done` with both scores.

### Rendered cross-check

`audit` and `critique` read source and judge design; a few defects show only
in the rendered app, in a particular state, or in motion. Check every
screenshot for:

- Elements hidden behind or overlapping others: stacking and z-index faults,
  sticky headers or footers covering content, popovers clipped by a parent
- Transparent or missing backgrounds letting unintended layers show through
  (menus, dropdowns, dialogs, toasts)
- A white or unstyled flash on page load or route change
- Distorted media: stretched or squashed images, avatars, or icons
- Lines of text colliding (line height too tight for the face or for
  wrapped content)
- Truncated text with no tooltip or other way to read the full value
- Loading spinners or skeletons off-centre or sized wrongly for the content
  they stand in for
- Hover, focus, and disabled states that look identical to the default
  state on screen

<!-- OPTIONAL: theming -->

### Theme cross-check (per theme in {{THEMES}})

- Borders, dividers, and input outlines invisible against the theme
  background (non-text contrast under 3:1)
- Elements that keep another theme's colors or ignore the theme toggle
- Theme switching that leaves artefacts: a flash, half-switched regions, or
  colors that update only after a reload

<!-- END OPTIONAL: theming -->

---

## Fixing -- through impeccable's refine commands

Take pages in order of their worst open defect, P0 first. Within a page,
group the open defects by command and fix each group with one invocation,
`/impeccable <command> <page source file>`, naming the defect IDs and notes
in the request so the command's playbook works on exactly those defects. A
defect that is a one-line local fix (a missing `aria-label`, a wrong token)
may be edited directly, still following that command's reference and the
craft floor.

Use the finding's suggested command when it names one. For findings without
one (cross-check, hook, detector), route by kind:

| Defect kind                                                                                   | Command    |
| --------------------------------------------------------------------------------------------- | ---------- |
| Contrast, interactive states, token or theme drift, inconsistency, browser surfaces (selection, scrollbars, focus rings) | `polish`   |
| Spacing, alignment, grouping, hierarchy, stacking, rhythm                                     | `layout`   |
| Type scale, weight, line height, measure, font loading                                        | `typeset`  |
| Breakpoints, narrow-viewport overflow, navigation collapse, touch targets                     | `adapt`    |
| Unclear labels, missing accessible names, error and empty-state wording                       | `clarify`  |
| Text overflow, long or missing content, presentation of existing loading, error, and empty states | `harden`   |
| Visual noise, overstimulating color or motion                                                 | `quieter`  |
| Semantic color lost within the existing palette                                               | `colorize` |
| Image sizing, layout shift, expensive animation                                               | `optimize` |

---

## Work Cycle

1. Setup: confirm the impeccable prerequisite, run its Setup once, and start
   the app.
2. Screenshot all states at 1280px, then at 375px.
   [theming] Repeat per theme in {{THEMES}}.
   Mark each `P-` line `done` as its pass completes.
3. Review each page (`R-` lines) with `audit`, `critique`, and the rendered
   cross-check, logging every defect in `{{PROGRESS_FILE}}` as you go.
4. For each page's open defects: run the matching impeccable command (see
   Fixing), let hot-reload pick up the change, resolve the hook or detector
   findings on what you changed, and re-screenshot the same state,
   viewport, and theme to confirm. Do not move on until the fix is visually
   confirmed and the ledger updated.
5. Final pass: re-screenshot all states at both viewports and walk the
   rendered cross-check again, then run the detector once over the
   frontend: `"<impeccable skill dir>/scripts/impeccable" detect --json {{FRONTEND_DIR}}`.
   [theming] Repeat the final screenshots in every theme.
   Log anything new and fix it, then repeat the final pass only for the
   pages those fixes touched.
6. Run `{{TYPE_CHECK_COMMAND}}` -- it must pass with zero errors.

**Stuck rule:** after 3 failed fix attempts on the same defect (one
impeccable run that leaves it open counts as one attempt), record what you
tried in `{{PROGRESS_FILE}}`, mark it `blocked`, move on, and revisit
blocked defects at the end.

---

## Constraints

Fixes stay within frontend visuals: templates, styles, CSS classes, design
tokens, and component structure. Application logic, API calls, backend code,
`spec.md` and other specification documents, and the behaviour of
authentication, data handling, and WebSockets stay as they are -- this pass
changes how the app looks, not what it does. A defect whose fix would need
any of them is marked `blocked` (see below).

impeccable's commands run inside the same limits:

- A refine command may restyle and restructure markup; it does not add
  features, change behaviour or data flow, rewrite factual copy, or replace
  the visual identity.
- `harden` and `optimize` stay on the presentation side: wrapping,
  overflow, how existing loading, error, and empty states look, image and
  animation cost. New error handling, validation, or data loading is out of
  scope.
- `PRODUCT.md` and `DESIGN.md` are read, never written, in this pass.
  impeccable's own state under `.impeccable/` (critique snapshots, detector
  config) may change as its commands require; never edit it by hand.

---

## Completion, Blockers & Stopping

**Definition of done -- every box checked:**

- [ ] impeccable's context was loaded this session (or its launcher fallback
      is recorded in the session log)
- [ ] Every page and state has been screenshotted at 1280px and 375px
- [ ] [theming] Full coverage was repeated in every theme in {{THEMES}}
- [ ] Every page's `R-` line is `done`, with its audit and critique scores
- [ ] Every defect found is `fixed` in `{{PROGRESS_FILE}}`, each confirmed by
      a follow-up screenshot in the affected state, viewport, and theme
- [ ] The final full pass shows zero remaining defects, and the final
      detector scan has no finding that is not fixed or logged
- [ ] `{{TYPE_CHECK_COMMAND}}` passes with zero errors
- [ ] `{{PROGRESS_FILE}}` is up to date with no `open` defects and no
      `pending` passes or reviews

Context is compacted automatically and `{{PROGRESS_FILE}}` carries state
across passes, so neither the length of the defect list nor remaining
context limits how far a pass can get. Work through the checklist until it
is met.

**The only valid reasons to mark a defect `blocked` instead of fixing it:**

- The fix would require changing application logic, backend code, or specs
  (out of scope here -- log it for a separate task)
- A design decision that belongs to a human: two plausible intended layouts
  and no way to tell which is right, a finding only a redesign or a "not
  used" command would fix, or a change to factual copy
- The stuck rule (3 failed fix attempts) fired

Stop only when every pass and review is complete and every defect is
`fixed`, or the only remaining defects are `blocked`. Then report: what was
fixed, every blocker from `{{PROGRESS_FILE}}` with what was tried and the
impeccable command it would need, the Observations, any detector ignores you
added, and -- when the repo has no `PRODUCT.md` or `DESIGN.md` -- a
recommendation to run `/impeccable init` and `/impeccable document` before
the next pass. Never claim a defect is fixed without the confirming
screenshot.
