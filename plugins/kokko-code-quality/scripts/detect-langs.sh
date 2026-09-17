#!/usr/bin/env bash
# Print the languages present in a project, one per line (py, js, dotnet).
#
# Every kokko-code-quality check skill runs this through inline
# preprocessing, so language detection lives in exactly one place instead of
# six byte-identical prose blocks. A `languages` list in the project's
# .kokko.json replaces detection outright.
#
# Usage: detect-langs.sh [project-dir]
#   The project directory is the argument, else $CLAUDE_PROJECT_DIR, else the
#   current directory. The skill text tells the model what to do when this
#   prints "none detected" (detect by hand from the project files).
set -euo pipefail

dir="${1:-${CLAUDE_PROJECT_DIR:-$PWD}}"
cd "$dir" 2>/dev/null || { echo "none detected (cannot enter $dir)"; exit 0; }

if [ -f .kokko.json ] && command -v jq >/dev/null 2>&1; then
  configured=$(jq -r '(.languages // []) | .[]' .kokko.json 2>/dev/null || true)
  if [ -n "$configured" ]; then
    printf '%s\n' "$configured" | sed 's/$/ (from .kokko.json)/'
    exit 0
  fi
fi

found=0
if [ -f pyproject.toml ] || [ -f setup.py ]; then echo "py"; found=1; fi
if [ -f package.json ] || [ -f tsconfig.json ]; then echo "js"; found=1; fi
if [ -n "$(git ls-files -- '*.csproj' '*.sln' 2>/dev/null)" ] \
  || ls ./*.sln ./*.csproj >/dev/null 2>&1; then
  echo "dotnet"; found=1
fi
[ "$found" -eq 1 ] || echo "none detected"
