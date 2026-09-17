#!/usr/bin/env bash
# A committed Python project with three deliberate bandit findings. No ruff
# config, so the skill must reach for the scanner ephemerally (uvx) rather
# than adding it to the project.
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
dependencies = ["pyyaml"]
TOML
cat > app/__init__.py <<'PY'
PY
cat > app/runner.py <<'PY'
import subprocess


def run(command: str) -> int:
    """Run a shell command and return its exit code."""
    return subprocess.call(command, shell=True)
PY
cat > app/config.py <<'PY'
import hashlib

import yaml


def load(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.load(f)


def fingerprint(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()
PY
git add -- pyproject.toml app/__init__.py app/runner.py app/config.py
git commit -q -m "chore: eval fixture"
