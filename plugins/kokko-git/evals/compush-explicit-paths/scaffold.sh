#!/usr/bin/env bash
# A pushed repo with one tracked change and one untracked scratch file. The
# bare "origin" lives beside the workspace so the push has somewhere to go.
set -euo pipefail
git config --global user.email "eval@example.com"
git config --global user.name "eval"
git config --global init.defaultBranch main
git init -q .
mkdir -p src
cat > src/app.py <<'PY'
def greet(name: str) -> str:
    return "Hello, " + name
PY
printf '# fixture\n' > README.md
git add -- README.md src/app.py
git commit -q -m "chore: eval fixture"
git init -q --bare ../origin.git
git remote add origin ../origin.git
git push -q -u origin main
cat > src/app.py <<'PY'
def greet(name: str) -> str:
    return f"Hello, {name}!"
PY
printf 'scratch\n' > scratch.tmp
