#!/usr/bin/env bash
# Bump Serendipity + Sequoia in zed-industries/extensions after theme PRs merge.
set -euo pipefail

SERENDIPITY_THEME_PR="https://github.com/meocoder31099/Serendipity-Theme-Zed/pull/5"
SEQUOIA_THEME_PR="https://github.com/HarshNarayanJha/zed-sequoia-theme/pull/1"
EXTENSIONS_FORK="https://github.com/michael-andreuzza/extensions.git"
BRANCH="update-serendipity-sequoia-themes"
WORKDIR="${TMPDIR:-/tmp}/zed-extensions-publish"

need() {
  command -v "$1" >/dev/null 2>&1 || { echo "Missing required command: $1" >&2; exit 1; }
}

need git
need gh
need npm

expected_version() {
  local repo="$1"
  gh api "repos/${repo}/contents/extension.toml" --jq '.content' | base64 -d \
    | awk -F'"' '/^version = / { print $2; exit }'
}

if [[ "${1:-}" == "--check" ]]; then
  ser="$(expected_version meocoder31099/Serendipity-Theme-Zed)"
  seq="$(expected_version HarshNarayanJha/zed-sequoia-theme)"
  echo "Serendipity extension.toml on upstream main: ${ser}"
  echo "Sequoia extension.toml on upstream main: ${seq}"
  if [[ "$ser" == "1.1.0" && "$seq" == "1.32.0" ]]; then
    echo "Theme PRs appear merged. Run without --check to refresh the registry PR."
    exit 0
  fi
  echo "Still waiting for theme PRs to merge:"
  echo "  ${SERENDIPITY_THEME_PR}"
  echo "  ${SEQUOIA_THEME_PR}"
  exit 1
fi

rm -rf "$WORKDIR"
git clone --depth 1 --branch "$BRANCH" "$EXTENSIONS_FORK" "$WORKDIR" 2>/dev/null \
  || { git clone --depth 1 "$EXTENSIONS_FORK" "$WORKDIR" && cd "$WORKDIR" && git checkout -b "$BRANCH"; }

cd "$WORKDIR"
git submodule update --init extensions/serendipity extensions/sequoia

(
  cd extensions/serendipity
  git fetch origin main
  git checkout origin/main
)
(
  cd extensions/sequoia
  git fetch origin main
  git checkout origin/main
)

ser_ver="$(cat extensions/serendipity/extension.toml | awk -F'"' '/^version = / { print $2; exit }')"
seq_ver="$(cat extensions/sequoia/extension.toml | awk -F'"' '/^version = / { print $2; exit }')"

python3 - <<PY
from pathlib import Path
import re
path = Path("extensions.toml")
text = path.read_text()
ser_ver = "${ser_ver}"
seq_ver = "${seq_ver}"
text = re.sub(
    r"(\\[serendipity\\]\\n(?:.*\\n)*?version = \")[^\"]+(\")",
    lambda m: m.group(1) + ser_ver + m.group(2),
    text,
    count=1,
)
text = re.sub(
    r"(\\[sequoia\\]\\n(?:.*\\n)*?version = \")[^\"]+(\")",
    lambda m: m.group(1) + seq_ver + m.group(2),
    text,
    count=1,
)
path.write_text(text)
PY

npm install --silent
npm run sort-extensions

git add extensions.toml extensions/serendipity extensions/sequoia
git commit -m "Update Serendipity (${ser_ver}) and Sequoia (${seq_ver}) theme extensions" || true
git push -u origin "$BRANCH"

if gh pr view --repo michael-andreuzza/extensions "$BRANCH" >/dev/null 2>&1; then
  gh pr ready "$BRANCH" --repo michael-andreuzza/extensions || true
  gh pr view "$BRANCH" --repo michael-andreuzza/extensions --web
else
  gh pr create --repo michael-andreuzza/extensions --head "$BRANCH" --base main \
    --title "Update Serendipity (1.1.0) and Sequoia (1.32.0) theme extensions" \
    --body-file - <<EOF
## Summary

- **Serendipity Themes** \`1.0.0\` → \`1.1.0\` — refreshed palette from [Serendipity-Theme/vs-code](https://github.com/Serendipity-Theme/vs-code)
- **Sequoia** \`1.31.0\` → \`1.32.0\` — refreshed palette + light variants from [Sequoia-Theme/vs-code](https://github.com/Sequoia-Theme/vs-code)

## Upstream theme PRs (must be merged first)

- ${SERENDIPITY_THEME_PR}
- ${SEQUOIA_THEME_PR}

## Test plan

- [ ] Submodule commits resolve on upstream theme repos
- [ ] \`extension.toml\` versions match \`extensions.toml\`
- [ ] Install both extensions as dev extensions in Zed and verify theme selector entries
EOF
fi

echo "Registry PR ready: https://github.com/michael-andreuzza/extensions/pulls"
