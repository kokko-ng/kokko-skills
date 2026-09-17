#!/usr/bin/env bash
# Generate the per-plugin skill tables in README.md and each plugin README
# from the skills' own frontmatter, so the tables can never drift from what
# the plugins actually ship.
#
# A README opts in with a marker pair; everything between the markers is
# replaced:
#
#   <!-- generated:skills:<plugin> start -->   (root README, one per plugin)
#   <!-- generated:skills start -->            (a plugin's own README)
#   ...
#   <!-- generated:skills end -->
#
# Usage: bash scripts/gen-readme-tables.sh          # rewrite in place
#        bash scripts/gen-readme-tables.sh --check  # exit 1 when out of date (CI)
set -euo pipefail

CHECK=0
[ "${1:-}" = "--check" ] && CHECK=1
FAIL=0

fm_value() { # <file> <key> -> scalar value, quotes stripped
  awk -v key="$2" '
    NR==1 {if ($0=="---") {fm=1; next} else exit}
    fm && $0=="---" {exit}
    fm && index($0, key ":")==1 {
      v = substr($0, length(key) + 2); sub(/^[[:space:]]+/, "", v)
      if (v ~ /^'\''.*'\''$/ || v ~ /^".*"$/) v = substr(v, 2, length(v) - 2)
      print v; exit }' "$1"
}

# table <plugin_dir> -> markdown table of the plugin's skills
table() {
  local plugin_dir="$1" f name hint desc invoke marks
  echo "| Skill | Purpose |"
  echo "| ----- | ------- |"
  for f in "$plugin_dir"/skills/*/SKILL.md; do
    [ -f "$f" ] || continue
    name=$(fm_value "$f" name)
    hint=$(fm_value "$f" argument-hint)
    desc=$(fm_value "$f" description)
    # Trigger guidance belongs in the frontmatter, not the README: keep the
    # first sentence only.
    desc=$(printf '%s' "$desc" | sed -E 's/\. .*$//; s/\.$//')
    invoke="/$name"
    [ -n "$hint" ] && invoke="$invoke $hint"
    # A literal | inside a table cell is a column break, even in a code span.
    invoke="${invoke//|/\\|}"
    desc="${desc//|/\\|}"
    marks=""
    [ "$(fm_value "$f" disable-model-invocation)" = "true" ] && marks="$marks †"
    [ "$(fm_value "$f" context)" = "fork" ] && marks="$marks ‡"
    echo "| \`$invoke\`${marks} | $desc |"
  done
  echo
  echo "† user-invoked only (\`disable-model-invocation\`) · ‡ runs forked, reports a summary"
}

# render <readme> <plugin_dir> <start_marker>
render() {
  local readme="$1" plugin_dir="$2" start="$3" end='<!-- generated:skills end -->' tmp
  tmp=$(mktemp)
  awk -v start="$start" -v end="$end" -v tbl="$(table "$plugin_dir")" '
    index($0, start)==1 { print; print ""; print tbl; print ""; skipping=1; next }
    skipping && index($0, end)==1 { skipping=0 }
    !skipping { print }' "$readme" > "$tmp"
  if ! cmp -s "$tmp" "$readme"; then
    if [ "$CHECK" -eq 1 ]; then
      echo "ERROR: $readme is out of date for $plugin_dir (run: bash scripts/gen-readme-tables.sh)"
      diff "$readme" "$tmp" | head -20 | sed 's/^/  /'
      FAIL=1
    else
      cp "$tmp" "$readme"
      echo "updated $readme ($plugin_dir)"
    fi
  fi
  rm -f "$tmp"
}

for plugin_dir in plugins/*/; do
  plugin_dir="${plugin_dir%/}"
  plugin=$(basename "$plugin_dir")
  if grep -q "<!-- generated:skills:$plugin start -->" README.md; then
    render README.md "$plugin_dir" "<!-- generated:skills:$plugin start -->"
  fi
  if [ -f "$plugin_dir/README.md" ] && grep -q '<!-- generated:skills start -->' "$plugin_dir/README.md"; then
    render "$plugin_dir/README.md" "$plugin_dir" "<!-- generated:skills start -->"
  fi
done

if [ "$FAIL" -eq 0 ]; then
  [ "$CHECK" -eq 1 ] && echo "README skill tables are current"
fi
exit "$FAIL"
