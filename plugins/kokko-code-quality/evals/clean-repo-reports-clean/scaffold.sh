#!/usr/bin/env bash
# A committed Python project with nothing for a security scanner to flag.
set -euo pipefail
git config --global user.email "eval@example.com"
git config --global user.name "eval"
git config --global init.defaultBranch main
git init -q .
mkdir -p app
cat > pyproject.toml <<'TOML'
[project]
name = "fixture"
version = "0.1.0"
requires-python = ">=3.11"
TOML
cat > app/__init__.py <<'PY'
PY
cat > app/math.py <<'PY'
def add(a: int, b: int) -> int:
    """Return the sum of two integers."""
    return a + b


def clamp(value: int, low: int, high: int) -> int:
    """Clamp value into the inclusive range [low, high]."""
    return max(low, min(value, high))
PY
git add -- pyproject.toml app/__init__.py app/math.py
git commit -q -m "chore: eval fixture"
