#!/usr/bin/env bash
# Publish Serendipity VS Code extension to Open VSX (wicked-labs namespace).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ -z "${OVSX_PAT:-}" ]]; then
  echo "Set OVSX_PAT (from https://open-vsx.org/user-settings/tokens)" >&2
  exit 1
fi

vsce package --no-dependencies --allow-missing-repository
VSIX="$(ls -1 *.vsix | head -1)"
ovsx publish "$VSIX" -p "$OVSX_PAT"
rm -f *.vsix

echo "Published: https://open-vsx.org/extension/wicked-labs/wvsc-serendipity"
