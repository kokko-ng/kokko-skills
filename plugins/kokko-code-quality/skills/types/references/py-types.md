# Python Type Checking with mypy

## Tool selection

Nothing is installed into the project. In order (see the shared
`references/check-workflow.md`):

1. The checker the repo configures (`[tool.mypy]` or `[tool.pyright]`,
   a pre-commit hook, a dev dependency): `uv run mypy` or `uv run pyright`
   with the repo's own settings.
2. Otherwise `uvx mypy`, as below.

Missing type stubs are supplied ephemerally too, never added to the
project during a check:

```bash
uvx --with types-requests --with types-PyYAML mypy .
```

Propose the `types-*` packages in the report if the user wants them
permanent.

## Commands

```bash
# Run type check
uvx mypy . --exclude venv --exclude .venv --exclude node_modules

# Specific directories
uvx mypy src/ tests/
```

## Common Errors and Fixes

| Error Code | Description | Fix |
| ---------- | ----------- | --- |
| `[assignment]` | Incompatible types | Fix type or add proper annotation |
| `[arg-type]` | Argument type mismatch | Fix argument or update signature |
| `[return-value]` | Return type mismatch | Fix return or annotation |
| `[name-defined]` | Name not defined | Import missing type or fix typo |
| `[attr-defined]` | Attribute not defined | Add attribute or fix access |
| `[union-attr]` | Access on Optional | Add None check or use `assert` |
| `[no-untyped-def]` | Missing annotations | Add param and return types |
| `[import]` | Cannot find module | Install stubs or add to ignore list |
| `[misc]` | Various issues | Read message carefully |

## Handle External Dependencies

Add to `pyproject.toml`:

```toml
[tool.mypy]
ignore_missing_imports = true

# Or ignore specific packages
[[tool.mypy.overrides]]
module = ["some_package.*", "another_package"]
ignore_missing_imports = true
```

## Configure Strictness

Add to `pyproject.toml`:

```toml
[tool.mypy]
python_version = "3.12"  # set to the project's minimum supported Python
strict = true
warn_return_any = true
warn_unused_ignores = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
no_implicit_optional = true
```

## Avoiding `Any` Types

Avoid `Any` unless it is genuinely unavoidable.

**Instead of `Any`, use:**

- `object` - for truly unknown types that you won't access
- `TypeVar` - for generic functions preserving type relationships
- `Union[X, Y]` - when value can be one of several types
- `Protocol` - for structural typing (duck typing with safety)
- `Callable[..., T]` - for functions with unknown parameters
- `dict[str, object]` - instead of `dict[str, Any]`

**If `Any` is unavoidable:**

- Add a comment explaining why
- Limit scope as much as possible
- Consider wrapping in a function with proper types at boundaries

## Validation

After each fix:

```bash
uv run mypy path/to/file.py
```

## Commit Format

```text
fix(types): resolve mypy errors in <module>
```

## Final Quality Gate

```bash
uv run mypy . --exclude venv
```
