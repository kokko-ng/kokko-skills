# Python Security Analysis with Bandit

## Tool selection

Nothing is installed into the project. In order (see the shared
`references/check-workflow.md`):

1. `[tool.ruff]` configured: ruff's `S` family is flake8-bandit and reports
   the same tests as `S<number>` (bandit's `B<number>`):
   `uv run ruff check --select S .` (do not edit the repo's ruff config).
2. bandit already a dev dependency or pre-commit hook: `uv run bandit`.
3. Otherwise run it ephemerally: `uvx bandit`, as in the commands below.

## Commands

```bash
# Medium and high severity only (recommended)
uvx bandit -r . -ll --exclude .venv,venv,node_modules

# Full scan with all severities
uvx bandit -r . -f screen --exclude .venv,venv,node_modules

# Specific directories
uvx bandit -r src/ lib/
```

## Common Issues and Fixes

| Test ID | Issue | Fix |
| ------- | ----- | --- |
| B303/B304 | Insecure hash (MD5/SHA1) | Use `hashlib.sha256()` or `blake2b` |
| B102 | `exec()` usage | Remove or sandbox execution |
| B602-B607 | Shell injection risk | Remove `shell=True`, use args list |
| B301 | Pickle deserialization | Use JSON or safe serializer |
| B108 | Hardcoded temp directory | Use `tempfile` module |
| B105 | Hardcoded password | Move to environment variable or secret manager |
| B403 | Import pickle | Consider safer alternatives |
| B410 | `yaml.load()` | Use `yaml.safe_load()` |
| B501 | `verify=False` in requests | Enable cert validation |
| B608 | SQL injection | Use parameterized queries |

## Classification

For each finding, classify as:

- **TRUE_POSITIVE** - Fix now
- **NEEDS_REFACTOR** - Create safer abstraction then fix
- **FALSE_POSITIVE** - Justify and suppress locally
- **ACCEPT_RISK** - Open tracking issue with rationale

## Suppression Pattern

Use narrowest suppression with explanation:

```python
password = os.environ["DB_PASSWORD"]  # nosec B105 - loaded from environment
```

## Validation

After each fix:

```bash
uvx bandit -r <affected_path> -ll
```

## Commit Format

```text
fix(security): mitigate <TestID> in <symbol>
```

## Final Quality Gate

```bash
uvx bandit -r . --exclude .venv,venv -ll
uv run pre-commit run --all-files   # when the repo has a .pre-commit-config.yaml
```
