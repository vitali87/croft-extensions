#!/usr/bin/env python3
"""Generate index.json from the vetted manifests under extensions/.

The index is a pure, deterministic function of the manifest files: each entry
carries the fields croft needs to display the extension (id/name/description),
gate it (api_version), fetch it (manifest_url) and verify it (sha256 of the
manifest bytes). No timestamp is written, so an unchanged set of manifests
produces byte-identical output (and therefore a stable signature).

Usage:  build-index.py <repo-root> [base-url]
Writes: <repo-root>/index.json
"""

from __future__ import annotations

import hashlib
import json
import sys
import tomllib
from pathlib import Path

DEFAULT_BASE_URL = "https://extensions.croft.software"
SCHEMA_VERSION = 1


def build(root: Path, base_url: str) -> dict:
    extensions = []
    for manifest_path in sorted(root.glob("extensions/*/extension.toml")):
        raw = manifest_path.read_bytes()
        meta = tomllib.loads(raw.decode("utf-8"))
        ext_id = meta["id"]
        extensions.append(
            {
                "id": ext_id,
                "name": meta["name"],
                "description": meta.get("description", ""),
                "version": str(meta.get("version", "1.0.0")),
                "api_version": int(meta["api_version"]),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "manifest_url": f"{base_url}/extensions/{ext_id}/extension.toml",
            }
        )
    return {"schema": SCHEMA_VERSION, "extensions": extensions}


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("usage: build-index.py <repo-root> [base-url]")
    root = Path(sys.argv[1]).resolve()
    base_url = (sys.argv[2] if len(sys.argv) > 2 else DEFAULT_BASE_URL).rstrip("/")
    index = build(root, base_url)
    out = root / "index.json"
    # Deterministic: sorted keys, compact separators, trailing newline.
    out.write_text(
        json.dumps(index, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n",
        encoding="utf-8",
    )
    print(f"wrote {out} ({len(index['extensions'])} extensions)")


if __name__ == "__main__":
    main()
