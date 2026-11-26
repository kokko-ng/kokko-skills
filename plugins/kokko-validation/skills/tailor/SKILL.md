---
name: tailor
description: Instantiate the aesthetics master prompt for the current repo and save it to prompts/. Use when the user wants a screenshot-driven UI review-and-fix prompt tailored to this codebase, to run unattended over every page and theme.
argument-hint: '[aesthetics] [hints such as the frontend directory or theme names]'
---

# Tailor Skill

Turn the generic aesthetics master prompt into a repo-specific prompt file.
The template is deliberately generic — full of `{{PLACEHOLDER}}` tokens
and optional blocks — and the entire point is to modify it to fit THIS
repo: fill every placeholder from what the codebase actually contains,
cut blocks that do not apply, and add repo-specific detail the template
could not know.

## Template

`${CLAUDE_PLUGIN_ROOT}/skills/tailor/references/aesthetics.md`: a
screenshot-driven visual review and fix pass that takes its design
judgement from the impeccable plugin. It starts with a `TAILORING NOTES`
comment: the full placeholder manifest (with the expected source for each
value) plus its optional blocks. Read it first — it is the authoritative
checklist.

`aesthetics` is the only template. The local-validation,
deployed-validation, and azure-deploy templates have been removed: for
shipping a change use `/land` (kokko-git), and for working through review
comments use `/feedback`.

## Workflow

### 1. Resolve the argument

`$ARGUMENTS` may start with the word `aesthetics`; whatever else it holds
is hints (the frontend directory, theme names, pages to leave out). If its
first word names one of the removed templates, say that the template is
gone and what replaced it, and stop.

### 2. Inspect the repo

Determine, from the code and configuration (not by guessing):

- App name; backend and frontend frameworks, directories, start
  commands, local URLs and ports
- The frontend source directory (`{{FRONTEND_DIR}}`)
- Every routed page with its route and its source file (the target the
  prompt hands to impeccable), including the authentication pages
- The page states worth a screenshot at desktop and at mobile width
- The app's themes
- The type-check command — confirm it actually exists in package.json /
  pyproject / Makefile; do not invent one
- Whether `PRODUCT.md` and `DESIGN.md` exist (the prompt runs without
  them; note their absence in the generation header)

### 3. Resolve placeholders

Fill EVERY placeholder in the template's manifest. Sources, in order:
user-supplied hints in `$ARGUMENTS`, then repo inspection. If a value is
genuinely unknowable, ask the user rather than inventing one.

Never write secret VALUES into the output file. The tailored prompt gets
committed to the repo.

### 4. Adapt, don't just substitute

- Delete optional blocks that do not apply (`<!-- OPTIONAL: name -->` ...
  `<!-- END OPTIONAL: name -->`) together with every line elsewhere tagged
  `[name]`; strip the tags from what you keep.
- Expand generics with repo detail: real desktop and mobile page states,
  each page with its route and source file.
- Keep the template's autonomous-work framing, defect-ledger mechanism,
  blocker rules, and completion checklist.
- The prompt is screenshot-driven by design: keep its browser automation
  on the **Playwright CLI**, never the Playwright MCP server — preserve its
  "Browser Automation -- Playwright CLI" section and its `playwright-cli`
  references. Its design judgement comes from the impeccable plugin
  (`impeccable@impeccable`, marketplace `pbakaus/impeccable`): keep the
  "Design Engine -- impeccable" section, the per-page `/impeccable audit`
  and `/impeccable critique` review, and the fix routing through
  impeccable's refine commands as written, and do not add hand-written
  defect categories beyond its rendered cross-check. If impeccable is not
  installed where you are tailoring, say so in the report with its install
  commands.
- Keep git usage safe: staging must name explicit file paths (never
  `git add .` or bare directory adds); no history rewrites; nothing force.

### 5. Save

Write to `prompts/aesthetics.md` in the repo root (create `prompts/` if
needed; add a qualifier such as `prompts/aesthetics-admin.md` when the repo
has more than one frontend). Fill `{{PROGRESS_FILE}}` with the output path
plus a `-progress` suffix (e.g. `prompts/aesthetics-progress.md`). If a
file with the same purpose already exists, update it in place rather than
creating a near-duplicate.

Start the file with a short generation-header comment: source template,
date, and a table of every placeholder value chosen — it makes future
re-tailoring a diff instead of a redo.

### 6. Verify the output

Mechanical checks before reporting — all must be clean:

- `grep -n '{{' prompts/<file>.md` returns nothing (no unresolved
  placeholders)
- Grepping for `TAILORING NOTES`, `OPTIONAL:`, and each `[tag]` named in
  the template's manifest returns nothing (no template scaffolding left)
- Every command the prompt tells its agent to run exists in this repo:
  the type-check script is defined, the start commands and directories
  are real, referenced routes and source files exist
- No secret values anywhere in the file

### 7. Report

Report: the file written, every placeholder value chosen and its source,
blocks removed or kept, sections expanded, and any values that need the
user's confirmation before the prompt is run.

## Running the result

Run the tailored prompt directly (paste it or `@prompts/<file>.md`). To make
another pass, run it again in a fresh session: each pass resumes from the
prompt's defect ledger, so fixed items are skipped and blocked ones get
revisited. Stop when a pass finds nothing new.
