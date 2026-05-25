#!/usr/bin/env bash
# Publish Serendipity to Open VSX under the serendipity namespace.
# VS Code Marketplace keeps publisher wicked-labs; Open VSX uses serendipity.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
OVSX_NAMESPACE="serendipity"

if [[ -z "${OVSX_PAT:-}" ]]; then
  echo "Set OVSX_PAT (from https://open-vsx.org/user-settings/tokens)" >&2
  exit 1
fi

ovsx create-namespace "$OVSX_NAMESPACE" -p "$OVSX_PAT" 2>/dev/null || true

cp package.json package.json.marketplace
node -e "
const fs = require('fs');
const pkg = JSON.parse(fs.readFileSync('package.json', 'utf8'));
pkg.publisher = process.argv[1];
fs.writeFileSync('package.json', JSON.stringify(pkg, null, 2) + '\n');
" "$OVSX_NAMESPACE"

vsce package --no-dependencies --allow-missing-repository
ovsx publish *.vsix -p "$OVSX_PAT"
mv package.json.marketplace package.json
rm -f *.vsix

echo "Published: https://open-vsx.org/extension/${OVSX_NAMESPACE}/wvsc-serendipity"
