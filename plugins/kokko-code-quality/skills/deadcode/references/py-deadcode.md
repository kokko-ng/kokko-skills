# Python Dead Code Detection with Vulture

## Tool selection

Nothing is installed into the project. In order (see the shared
`references/check-workflow.md`):

1. vulture already a dev dependency or pre-commit hook: `uv run vulture`.
2. Otherwise `uvx vulture`, as below.
3. `[tool.ruff]` configured: add `uv run ruff check --select F401,F841,ARG .`
   for unused imports, locals, and arguments (ruff never finds unused
   functions or classes, which is vulture's job).

## Commands

```bash
# Run dead code analysis
uvx vulture . --exclude .venv,venv,node_modules,__pycache__

# Specific directories
uvx vulture src/ lib/

# With whitelist
uvx vulture . vulture_whitelist.py --exclude .venv
```

## Verification Checklist

For each item detected, **thoroughly verify** it is truly unused:

**Cross-check references:**

- All internal imports across the codebase
- Dynamic imports (`importlib`, `__import__`)
- Entry points in `pyproject.toml` or `setup.py`
- Config-based registries and plugin systems
- Decorator registrations
- Metaprogramming patterns

**Check for indirect usage:**

- Reflection: `getattr()`, `globals()`, `locals()`
- String-based access: `eval()`, `exec()`
- Framework magic (Django models, FastAPI routes, pytest fixtures)
- CLI command definitions
- Template references

## Removal Process

**Only if absolutely certain the code is unused:**

1. Remove the dead code
2. Create a separate commit:

   ```bash
   git add <the files you edited>
   git commit -m "chore(cleanup): remove unused <function_name>"
   ```

## Handle One Item at a Time

Do NOT batch deletions. Process one finding at a time to maintain
traceability and safety.

## Whitelist for False Positives

Create a whitelist file for code used but not detected:

```python
# vulture_whitelist.py
from mymodule import used_by_framework  # noqa: F401
used_by_framework  # Mark as used
```

## Commit Format

```text
chore(cleanup): remove unused <function_name>
```

## Error Recovery

| Issue | Resolution |
| ----- | ---------- |
| Import errors | Check all import paths |
| False positive | Add to whitelist |

## Final Quality Gate

```bash
uvx vulture . vulture_whitelist.py --exclude .venv
```
