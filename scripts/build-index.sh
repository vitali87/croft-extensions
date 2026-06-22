#!/usr/bin/env bash
# Build and sign the extension index.
#
#   1. Regenerate index.json from the vetted manifests (deterministic).
#   2. Sign index.json with the ed25519 private key -> index.json.sig
#      (raw 64-byte signature, which croft verifies with `ring`).
#
# Requires the env var CROFT_INDEX_KEY to point at the ed25519 private key
# (the CI secret). The key never appears on the command line or in git.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
KEY="${CROFT_INDEX_KEY:?set CROFT_INDEX_KEY to the ed25519 private key path}"
BASE_URL="${CROFT_INDEX_BASE_URL:-https://extensions.croft.software}"

python3 "$ROOT/scripts/build-index.py" "$ROOT" "$BASE_URL"
openssl pkeyutl -sign -inkey "$KEY" -rawin -in "$ROOT/index.json" -out "$ROOT/index.json.sig"

echo "signed: $ROOT/index.json.sig ($(wc -c < "$ROOT/index.json.sig") bytes)"
