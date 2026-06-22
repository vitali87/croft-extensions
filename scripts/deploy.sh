#!/usr/bin/env bash
# Server-side publish (mirrors croft-docs' deploy.sh): pull the vetted
# manifests, rebuild + ed25519-sign the index, and publish to the Caddy
# docroot. Run on a timer; a transient failure leaves the previous index
# serving and the next tick retries.
#
#   SRC  the croft-extensions checkout (holds the private signing key)
#   PUB  the static dir Caddy serves at https://extensions.croft.software
set -euo pipefail

SRC="${CROFT_EXT_SRC:-/opt/croft-extensions-src}"
PUB="${CROFT_EXT_PUB:-/opt/croft-extensions}"
KEY="${CROFT_INDEX_KEY:-$SRC/croft-index.key}"

cd "$SRC"
git fetch --quiet origin main
git reset --hard --quiet origin/main

CROFT_INDEX_KEY="$KEY" ./scripts/build-index.sh

mkdir -p "$PUB"
install -m 644 index.json "$PUB/index.json"
install -m 644 index.json.sig "$PUB/index.json.sig"
install -m 644 index.html "$PUB/index.html"
rsync -a --delete extensions/ "$PUB/extensions/"
echo "published index ($(date -u +%FT%TZ))"
