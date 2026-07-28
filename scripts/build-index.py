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
import html
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


REPO_URL = "https://github.com/vitali87/croft-extensions"

PAGE_CSS = """
:root { color-scheme: dark; }
* { box-sizing: border-box; }
body { margin: 0; background: #1e222e; color: #c8cdd8;
  font: 16px/1.6 ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif; }
.wrap { max-width: 760px; margin: 0 auto; padding: 64px 24px 96px; }
h1 { font-size: 30px; margin: 0 0 6px; color: #f0f2f6; letter-spacing: -0.01em; }
.tag { color: #8b93a7; margin: 0 0 28px; }
.lead { color: #aab2c5; border-left: 3px solid #2dd4bf; padding: 2px 0 2px 16px; margin: 0 0 36px; }
a { color: #2dd4bf; text-decoration: none; }
a:hover { text-decoration: underline; }
.count { color: #8b93a7; font-size: 13px; text-transform: uppercase;
  letter-spacing: 0.08em; margin: 0 0 14px; }
.ext { background: #252a38; border: 1px solid #313747; border-radius: 12px;
  padding: 18px 20px; margin: 0 0 14px; }
.ext h2 { font-size: 18px; margin: 0 0 2px; color: #f0f2f6; }
.id { font-family: ui-monospace, "SF Mono", Menlo, monospace; font-size: 12.5px;
  color: #2dd4bf; }
.ext p { margin: 8px 0 0; color: #aab2c5; }
.meta { margin: 10px 0 0; font-size: 12.5px; color: #6f7689;
  font-family: ui-monospace, "SF Mono", Menlo, monospace; }
footer { margin-top: 44px; padding-top: 22px; border-top: 1px solid #313747;
  color: #6f7689; font-size: 13.5px; }
code { font-family: ui-monospace, "SF Mono", Menlo, monospace; color: #c8cdd8;
  background: #313747; padding: 1px 6px; border-radius: 5px; font-size: 13px; }
""".strip()


def render_html(index: dict, base_url: str) -> str:
    """A human-facing landing page rendered from the SAME data croft reads.
    Pure HTML (no JS, no external assets), regenerated on every publish so it
    can never drift from index.json. croft never reads this; it's for browsers."""
    e = html.escape
    cards = []
    for ext in index["extensions"]:
        cards.append(
            f'    <div class="ext">\n'
            f'      <h2>{e(ext["name"])} <span class="id">{e(ext["id"])}</span></h2>\n'
            f"      <p>{e(ext['description'])}</p>\n"
            f'      <p class="meta">v{e(ext["version"])} · api {ext["api_version"]} · '
            f'<a href="{e(ext["manifest_url"])}">manifest</a></p>\n'
            f"    </div>"
        )
    n = len(index["extensions"])
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>croft extensions</title>
<style>{PAGE_CSS}</style>
</head>
<body>
  <div class="wrap">
    <h1>croft extensions</h1>
    <p class="tag">The vetted extension index for <a href="https://croft.software">croft</a>.</p>
    <p class="lead">This is a signed index, not a marketplace. Every extension here was
      reviewed and merged by the maintainer. croft fetches
      <a href="{e(base_url)}/index.json"><code>/index.json</code></a>, verifies its
      ed25519 signature against a key baked into the binary, then offers these under
      the Extensions panel's <strong>Available</strong> tier.</p>
    <p class="count">{n} extension{"" if n == 1 else "s"}</p>
{chr(10).join(cards)}
    <footer>
      Add one by opening a pull request against
      <a href="{REPO_URL}">the croft-extensions repo</a>.
      The index is rebuilt, signed, and published automatically on merge.
    </footer>
  </div>
</body>
</html>
"""


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
    # Human landing page (served at /, so the bare domain isn't a 404).
    (root / "index.html").write_text(render_html(index, base_url), encoding="utf-8")
    print(f"wrote {out} + index.html ({len(index['extensions'])} extensions)")


if __name__ == "__main__":
    main()
