<!--
TAILORING NOTES (for the /tailor skill -- delete this entire comment in the tailored output)

Placeholders. Every {{...}} must be resolved. Sources, in order: user hints,
repo inspection, then ask the user. Never invent values.

  APP_NAME                    Application name
  PROGRESS_FILE               Defect ledger path, e.g. prompts/aesthetics-progress.md
  FRONTEND_FRAMEWORK / FRONTEND_START_COMMAND / FRONTEND_URL
  BACKEND_FRAMEWORK / BACKEND_START_COMMAND / BACKEND_URL
  THEMES                      Theme list, e.g. "dark, light" (single-theme apps: delete the theming block)
  TYPE_CHECK_COMMAND          Command(s) that must pass with zero errors
  DESKTOP_STATES              Real page/state list to screenshot at 1280px (enumerate from the router)
  MOBILE_STATES               Real page/state list to screenshot at 375px

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

| ID         | Value                                        |
| ---------- | -------------------------------------------- |
| `frontend` | {{FRONTEND_FRAMEWORK}} on `{{FRONTEND_URL}}` |
| `backend`  | {{BACKEND_FRAMEWORK}} on `{{BACKEND_URL}}`   |
| `tool`     | Playwright CLI (`playwright-cli`)            |
| `ledger`   | `{{PROGRESS_FILE}}`                          |
| [theming] `themes` | {{THEMES}}                           |

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

---

## Primary Goal

Work autonomously to identify and fix every visual and UI defect in the
locally running application. Use the Playwright CLI to screenshot every page,
state, and interactive component; fix each defect; re-screenshot to confirm.

Completion is defined solely by the checklist in the "Completion, Blockers &
Stopping" section at the end of this prompt -- nothing else.

---

## Defect Ledger -- Read First, Update Always

`{{PROGRESS_FILE}}` is the single source of truth for progress. Conversation
memory does not survive context compaction or fresh-context passes
(multipass); this file does.

- **On start:** if the file exists, read it and resume from the first
  screenshot pass or defect not marked done. If it does not exist, create it
  with one line per screenshot pass (viewport x theme), all `pending`.
- **Pass format:** `P-01 | pending / done | viewport/theme | short note`.
- **Defect format:** `D-014 | open / fixed / blocked | page + state | viewport/theme | short note`
  -- append a line the moment a defect is spotted; flip it to `fixed` only
  after the confirming re-screenshot.
- Every line starts with an ID of letters, a hyphen, and digits (`P-01`,
  `D-014`): the kokko-janitor progress-guard hook counts open items by that
  shape and ignores lines without one.
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
for the affected pages.

[theming] Repeat full coverage once per theme in {{THEMES}}. Before each
theme's pass, switch to it with the app's theme switcher and confirm it is
applied globally before taking any screenshots.

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

## Defect Categories to Inspect

For every screenshot, inspect and fix defects in the following categories:

### Visibility

- Text invisible or near-invisible due to insufficient contrast against its background
- Elements unintentionally hidden behind other elements
- Overflow: content clipped or cut off without indication
- Transparent backgrounds revealing unintended layers
- White or light flashes during transitions or page load

### Layout & Alignment

- Warped, stretched, or squashed elements (images, avatars, icons, buttons)
- Misaligned items within a row or column
- Elements overflowing their containers and breaking adjacent layout
- Inconsistent spacing (gaps, padding, margins) between similar elements
- Grid or flex layout collapsing incorrectly at any breakpoint

### Typography

- Text overflow without ellipsis or wrapping
- Line height causing text overlap
- Font weight or size inconsistencies across similar elements
- Truncated labels missing a tooltip or accessible alternative

### Interactive States

- Buttons or inputs with no visible focus ring
- Hover states absent or broken
- Disabled states indistinguishable from enabled states
- Loading spinners or skeletons not centered or sized correctly

### Accessibility Quick Wins

- Images missing meaningful alt text
- Icon-only buttons missing an accessible label (aria-label)
- Form inputs missing an associated label
- Keyboard tab order that skips or traps focus on the inspected page

<!-- OPTIONAL: theming -->

### Theme Integrity (per theme in {{THEMES}})

- Hard-coded colors from another theme visible (e.g. white backgrounds or
  black text in dark theme, and vice versa)
- Borders or dividers invisible against the theme background
- Input placeholder text invisible or too faint
- Scrollbar styles inconsistent with the theme
- Elements that do not respond to the theme toggle at all
- Theme switching transitions cleanly with no visual artefacts

<!-- END OPTIONAL: theming -->

### Responsive Behaviour

- Sidebar or navigation not collapsing correctly on narrow viewports
- Input elements or action buttons falling off screen on mobile
- Images or media overflowing their container on small screens
- Touch targets smaller than 44px on mobile

---

## Work Cycle

1. Screenshot all states at 1280px, then at 375px
   [theming] -- repeating per theme in {{THEMES}}.
2. Log every defect found in `{{PROGRESS_FILE}}` as you go.
3. For each defect: locate the component or style in the frontend source,
   apply a targeted fix (CSS class correction, style override, component
   structure adjustment), let hot-reload pick it up, and re-screenshot the
   same state, viewport, and theme to confirm. Do not move on until the fix
   is visually confirmed and the ledger updated.
4. Final pass: re-screenshot all states at both viewports to confirm zero
   remaining defects and no regressions from the fixes.
   [theming] Repeat the final pass in every theme.
5. Run `{{TYPE_CHECK_COMMAND}}` -- it must pass with zero errors.

**Stuck rule:** after 3 failed fix attempts on the same defect, record what
you tried in `{{PROGRESS_FILE}}`, mark it `blocked`, move on, and revisit
blocked defects at the end.

---

## Constraints

Fixes stay within frontend visuals: templates, styles, CSS classes, and
component structure. Application logic, API calls, backend code, `spec.md`
and other specification documents, and the behaviour of authentication,
data handling, and WebSockets stay as they are -- this pass changes how the
app looks, not what it does. A defect whose fix would need any of them is
marked `blocked` (see below).

---

## Completion, Blockers & Stopping

**Definition of done -- every box checked:**

- [ ] Every page and state has been screenshotted at 1280px and 375px
- [ ] [theming] Full coverage was repeated in every theme in {{THEMES}}
- [ ] Every defect found is `fixed` in `{{PROGRESS_FILE}}`, each confirmed by
      a follow-up screenshot in the affected state, viewport, and theme
- [ ] The final full pass shows zero remaining defects
- [ ] `{{TYPE_CHECK_COMMAND}}` passes with zero errors
- [ ] `{{PROGRESS_FILE}}` is up to date with no `open` defects or `pending` passes

Context is compacted automatically and `{{PROGRESS_FILE}}` carries state
across passes, so neither the length of the defect list nor remaining
context limits how far a pass can get. Work through the checklist until it
is met.

**The only valid reasons to mark a defect `blocked` instead of fixing it:**

- The fix would require changing application logic, backend code, or specs
  (out of scope here -- log it for a separate task)
- A design decision that belongs to a human (e.g. two plausible intended
  layouts and no way to tell which is right)
- The stuck rule (3 failed fix attempts) fired

Stop only when every pass is complete and every defect is `fixed`, or the
only remaining defects are `blocked`. Then report: what was fixed, and every
blocker from `{{PROGRESS_FILE}}` with what was tried. Never claim a defect is
fixed without the confirming screenshot.
