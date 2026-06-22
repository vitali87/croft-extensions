#!/usr/bin/env bash
# Generate the ed25519 signing keypair for the croft extension index.
# Run this ONCE, on the machine that will hold the CI signing secret.
#
#   The PRIVATE key never enters git and never leaves your control. Store it as
#   the CI secret `croft_index_key` (and a backup somewhere safe).
#   The PUBLIC key (the 32-byte hex this prints) is baked into croft as
#   `INDEX_PUBLIC_KEY` so the client can verify a signed index.
set -euo pipefail

OUT="${1:-croft-index.key}"
if [[ -e "$OUT" ]]; then
  echo "refusing to overwrite existing key: $OUT" >&2
  exit 1
fi

openssl genpkey -algorithm ed25519 -out "$OUT"
chmod 600 "$OUT"

echo "private key written: $OUT"
echo "  -> KEEP SECRET. Never commit. Store as CI secret 'croft_index_key'."
echo
echo -n "public key (bake into croft INDEX_PUBLIC_KEY): "
openssl pkey -in "$OUT" -pubout -outform DER | tail -c 32 | xxd -p -c 32
