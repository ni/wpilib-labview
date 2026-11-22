#!/usr/bin/env python3
"""Check repository rules that CI enforces.

- No native binaries or per-machine LabVIEW files are tracked (natives come from natives.json).
- Each add-on has a valid lvaddoninfo.json whose AddonName matches its folder.
- natives.json pins a sha256 for every artifact zip it lists (platforms, link-only platforms, and
  headers), so every download is verified before use.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FORBIDDEN = re.compile(r"\.(so|dll|dylib|exe|lib|pdb)$|\.so\.\d|\.(aliases|lvlps|lvprojstate)$|\.UserState/", re.I)


def main():
    errors = []
    tracked = subprocess.check_output(["git", "-C", str(ROOT), "ls-files", "-z"]).decode("utf-8").split("\0")
    for path in filter(None, tracked):
        if FORBIDDEN.search(path):
            errors.append(f"{path}: native binaries and per-machine LabVIEW files must not be committed")

    addons = sorted(p for p in (ROOT / "lvaddons").iterdir() if p.is_dir())
    if not addons:
        errors.append("lvaddons/ has no add-ons")
    for addon in addons:
        info = addon / "1" / "lvaddoninfo.json"
        try:
            data = json.loads(info.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            errors.append(f"{info.relative_to(ROOT)}: {e}")
            continue
        if data.get("AddonName") != addon.name:
            errors.append(f"{info.relative_to(ROOT)}: AddonName {data.get('AddonName')!r} isn't {addon.name!r}")
        for key in ("ApiVersion", "MinimumSupportedLVVersion"):
            if not data.get(key):
                errors.append(f"{info.relative_to(ROOT)}: missing {key}")

    manifest = json.loads((ROOT / "natives.json").read_text(encoding="utf-8"))
    names = {a.name for a in addons}
    for art in manifest["artifacts"]:
        label = f"natives.json {art['name']}"
        if art["addon"] not in names:
            errors.append(f"{label}: add-on {art['addon']!r} doesn't exist")
        if art["repository"] not in manifest["repositories"]:
            errors.append(f"{label}: unknown repository {art['repository']!r}")
        platforms = art["platforms"] + art.get("link_platforms", [])
        for platform in platforms:
            if platform not in manifest["platforms"]:
                errors.append(f"{label}: unknown platform {platform!r}")
        pinned = platforms + (["headers"] if art.get("headers") else [])
        for classifier in pinned:
            if not re.fullmatch(r"[0-9a-f]{64}", art["sha256"].get(classifier, "")):
                errors.append(f"{label}: no sha256 for {classifier}")
        extra = set(art["sha256"]) - set(pinned)
        if extra:
            errors.append(f"{label}: sha256 for unlisted classifier(s) {sorted(extra)}")

    for e in errors:
        print(f"::error::{e}")
    if errors:
        sys.exit(1)
    print(f"OK: {len(addons)} add-ons, {len(manifest['artifacts'])} pinned native artifacts")


if __name__ == "__main__":
    main()
