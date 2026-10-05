# Python Documentation with Interrogate and Pydocstyle

## Tool selection

Nothing is installed into the project. In order (see the shared
`references/check-workflow.md`):

1. interrogate or pydocstyle already dev dependencies: `uv run <tool>`.
2. `[tool.ruff]` configured: `uv run ruff check --select D --config 'lint.pydocstyle.convention="google"' .`
   reports every missing or malformed docstring (the `D` family is
   pydocstyle) without touching the repo's ruff config.
3. Otherwise `uvx interrogate` and `uvx pydocstyle`, as below.

## Commands

### Coverage Analysis

```bash
# Check coverage with verbose output
uvx interrogate -v <target_dir> --fail-under 100

# Generate badge
uvx interrogate <target_dir> --generate-badge /tmp/docstring-badge
```

### Style Check

```bash
uvx pydocstyle <target_dir> --convention=google
```

## Key Error Codes

- D100: Missing docstring in public module
- D101: Missing docstring in public class
- D102: Missing docstring in public method
- D103: Missing docstring in public function
- D107: Missing docstring in `__init__`

## Processing Order

Work through files in this order:

1. Public API functions and classes
2. Complex functions (high cyclomatic complexity)
3. Entry points and orchestration code
4. Utility functions and helpers
5. Private methods and internal functions

## Docstring Standards (Google-style)

**For functions:**

```python
def function_name(param1: str, param2: int) -> bool:
    """Short one-line summary ending with period.

    Longer description if needed. Explain the purpose,
    not the implementation.

    Args:
        param1: Description of first parameter.
        param2: Description of second parameter.

    Returns:
        Description of return value.

    Raises:
        ValueError: When param2 is negative.
    """
```

**For classes:**

```python
class ClassName:
    """Short one-line summary.

    Longer description of the class purpose and usage.

    Attributes:
        attr1: Description of attribute.
        attr2: Description of attribute.
    """
```

## Validation

After fixing each file (use `uv run` instead of `uvx` when the tool is a
project dependency, Tool selection step 1):

```bash
uvx interrogate -v <file.py>
uvx pydocstyle <file.py> --convention=google
```

## Commit Format

```text
docs(<module>): add docstrings to <file>
```

## Error Handling

| Issue | Resolution |
| ----- | ---------- |
| D100 in `__init__.py` | Add module-level docstring at top of file |
| D107 false positive | Add simple docstring or configure exception |
| Style conflicts | Standardize on Google style |

## Final Quality Gate

```bash
uvx interrogate -v <target_dir> --fail-under 100
uvx pydocstyle <target_dir> --convention=google
```
