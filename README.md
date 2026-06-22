# croft-extensions

The vetted extension index for [croft](https://croft.software). This repo is the
**source of truth**; a CI job publishes a signed index to
`https://extensions.croft.software`, which croft fetches to populate the
**Available** tier of its Extensions panel.

croft is a **vetted-only, no-marketplace** host: nothing is self-published.
Every extension here was reviewed and merged by the maintainer. There is no
runtime sandbox because there is nothing untrusted to sandbox.

## Layout

```
extensions/<id>/extension.toml   # one vetted manifest per extension (source of truth)
scripts/build-index.py           # generate index.json from the manifests (deterministic)
scripts/build-index.sh           # build-index.py + ed25519-sign the result
scripts/gen-keypair.sh           # one-time: generate the signing keypair
.woodpecker.yml                  # CI: build, sign, publish to the host
```

A croft extension is **just an `extension.toml` manifest**. The actual server
(MCP sidecar, LSP, DAP) is provisioned at runtime by croft via `npm`/`uvx`/`pip`,
so this repo ships no binaries.

## How the index is served

1. CI regenerates `index.json` from the manifests (sha256 of each manifest is
   recorded in the index).
2. CI signs `index.json` with the ed25519 private key (the `croft_index_key`
   secret) -> `index.json.sig`.
3. CI publishes `index.json`, `index.json.sig`, and `extensions/` to
   `https://extensions.croft.software` (a static dir on the VPS).
4. croft fetches `index.json` + `.sig`, verifies the signature against the
   public key baked into the binary, caches it, and on install fetches the
   named manifest and verifies its sha256 against the signed index.

`raw.githubusercontent`-style git-host file URLs are deliberately **not** used:
they are per-IP rate-limited, which breaks users behind shared NAT/VPN.

## One-time setup (signing key)

```bash
./scripts/gen-keypair.sh                 # prints the 32-byte public key hex
```

- Store the private key (`croft-index.key`) as the CI secret `croft_index_key`.
  Never commit it (`.gitignore` covers `*.key`).
- Give the printed public-key hex to the maintainer to bake into croft as
  `INDEX_PUBLIC_KEY`. Until that is done, croft ignores the remote index and
  shows only its bundled catalog (fail-closed).

## Adding / vetting an extension

1. Open a PR adding `extensions/<id>/extension.toml`.
2. Review checklist (the whole point of "vetted"):
   - **Identity:** `id` is unique and stable; `name`/`description` are accurate.
   - **Provisioning:** the `provision` package (`npm`/`uvx` name + version) is
     the genuine upstream package, pinned to an exact version.
   - **Capabilities:** what the server can touch (network / spawn / file writes)
     is understood and acceptable. Note keyless vs. credentialed.
   - **api_version:** matches a version current croft understands.
3. Merge. CI republishes the signed index; croft picks it up within its cache
   TTL (or immediately on a manual refresh).

## Local dry run

```bash
./scripts/gen-keypair.sh /tmp/test.key
CROFT_INDEX_KEY=/tmp/test.key ./scripts/build-index.sh
# verify locally:
openssl pkeyutl -verify -pubin \
  -inkey <(openssl pkey -in /tmp/test.key -pubout) \
  -rawin -in index.json -sigfile index.json.sig
```
