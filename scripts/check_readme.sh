#!/usr/bin/env bash
# Guard checks for the profile README. Used by .github/workflows/readme-check.yml
# and runnable locally:  bash scripts/check_readme.sh
set -uo pipefail
cd "$(dirname "$0")/.."
XMLLINT="${XMLLINT:-xmllint}"
fail=0

echo "▶ conflict markers in README.md"
if grep -nE '^(<<<<<<<|=======|>>>>>>>)' README.md; then
  echo "✗ merge-conflict markers found (lines above)"; fail=1
else
  echo "✓ none"
fi

echo "▶ local asset paths referenced from README.md"
missing=0
while IFS= read -r p; do
  if [ ! -f "$p" ]; then echo "✗ missing: $p"; missing=1; fi
done < <(grep -oE '\./assets/[A-Za-z0-9._/-]+' README.md | sort -u)
[ "$missing" -eq 0 ] && echo "✓ all present" || fail=1

echo "▶ xmllint on assets/*.svg"
bad=0
for f in assets/*.svg; do
  "$XMLLINT" --noout "$f" || { echo "✗ $f"; bad=1; }
done
[ "$bad" -eq 0 ] && echo "✓ all well-formed" || fail=1

exit "$fail"
