# Shared Check Workflow

Every kokko-code-quality check skill (`security`, `types`, `complexity`,
`deadcode`, `docs`, `architecture`) runs this workflow. A skill's own
SKILL.md supplies only its deltas: the tools per language, how findings are
classified, the commit format, and what "done" means. Read this once, then
the language reference the skill names.

## Arguments

`$ARGUMENTS` may carry:

- a language: `py`/`python`, `js`/`javascript`/`typescript`/`ts`, or
  `dotnet`/`csharp`/`cs`. When given, check only that language.
- `--report`: run the analyzer and report its findings, classified as the
  skill directs. Edit nothing, commit nothing, install nothing. The
  janitor's `--dry-run` relies on this mode.

## 1. Languages

The skill's "Languages present" line comes from `scripts/detect-langs.sh`,
which honors a `languages` list in the repo's `.kokko.json` and otherwise
detects Python (`pyproject.toml` or `setup.py`), JavaScript/TypeScript
(`package.json` or `tsconfig.json`), and .NET (`*.csproj` or `*.sln`). If
the line reads `none detected`, run the same detection yourself from the
project root. Run the full workflow once per language, and name every
language in the report, including any skipped because the skill does not
support it.

## 2. Tools: use what the repo already has

Running a check must not change the project's dependencies. Pick the tool
in this order, and say in the report which one ran and why:

1. **A configured preference.** `.kokko.json` may name one per language and
   check: `{"tools": {"py": {"security": "ruff"}}}`.
2. **What the repo already runs.** A tool present in
   `.pre-commit-config.yaml`, `pyproject.toml` (a `[tool.<name>]` table or
   the dev dependencies), `package.json` devDependencies, or the solution's
   analyzer references is the tool the maintainers chose. Use it with the
   repo's own configuration.
3. **Ruff, when the repo configures it.** A `[tool.ruff]` table or a
   `ruff.toml` makes ruff the Python linter of record, and its rule families
   cover several checks without a second tool:

   | Check | Ruff rules |
   | ----- | ---------- |
   | `security` | `S` (flake8-bandit, the same tests as bandit) |
   | `complexity` | `C901` (mccabe) and `PLR09` (too many branches, arguments, statements) |
   | `deadcode` | `F401`, `F841`, `ARG` (unused imports, locals, arguments) |
   | `docs` | `D` (pydocstyle) |

   Enable a family for one run with `--select`; never edit the repo's ruff
   config to do it (that is a project change the user did not ask for;
   propose it in the report). Ruff does not find unused functions (vulture)
   or compute a maintainability index (radon), so those specialist tools
   still run for what ruff cannot see.
4. **A specialist tool, ephemerally.** When none of the above applies, run
   the tool without installing it into the project: `uvx <tool>` for
   Python, `npx --yes <tool>` for JavaScript, `dotnet build` with the
   analyzers the solution already references. Never `uv add`,
   `pip install`, `npm install -D`, or `dotnet add package` to run a check.
   If the tool is worth keeping, the report proposes the permanent
   configuration for the user to adopt.

## 3. Run, classify, fix

1. Run the analyzer with the reference's command, scoped to source
   (exclude virtualenvs, `node_modules`, build output, and the `excludes`
   globs from `.kokko.json`).
2. Classify every finding as the skill's table says. A false positive gets
   the narrowest suppression the tool offers, with a written justification;
   never a blanket disable, never a relaxed threshold.
3. Fix findings one at a time in the skill's priority order, re-running the
   analyzer on the affected file after each fix.
4. Keep behavior identical: the repo's tests must pass after every fix. Run
   the test command at the end (`uv run pytest`, `npm test`,
   `dotnet test`).

`--report` stops after step 2.

## 4. Commit

Small logical commits, one concern each, in the skill's message format.
Stage explicit file paths only: never `git add .`, `-A`, or a directory
add; they sweep in untracked files. Never stash, reset, restore, or
otherwise clear working-tree state; a dirty tree that is not yours means
stop and report.

## 5. Report

Per language: the tool that ran and why it was chosen, findings by
classification, what was fixed (commits), what was suppressed and why, what
remains and why, and the final analyzer result. A clean run is a valid
result: report clean, commit nothing, and never manufacture work or relax
configuration to create findings.
