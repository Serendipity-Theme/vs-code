#!/usr/bin/env bash
# Publish Serendipity VS Code extension to Open VSX.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ -z "${OVSX_PAT:-}" ]]; then
  echo "Set OVSX_PAT (from https://open-vsx.org/user-settings/tokens)" >&2
  exit 1
fi

vsce package --no-dependencies --allow-missing-repository
ovsx publish *.vsix -p "$OVSX_PAT"
echo "Published: https://open-vsx.org/extension/wicked-labs/wvsc-serendipity"
