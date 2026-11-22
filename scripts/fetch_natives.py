#!/usr/bin/env python3
"""Download the pinned native libraries in natives.json into the add-ons' resource folders.

Each artifact is a Maven zip from WPILib or REV. The zip is verified against the sha256 in
natives.json, then its shared libraries (no JNI, debug, or import libraries) are extracted into
lvaddons/<addon>/1/resource/, and its license files into lvaddons/<addon>/1/resource/notices/.

    python scripts/fetch_natives.py --platform windowsx86-64
    python scripts/fetch_natives.py --update-hashes      # after changing versions in natives.json
"""

import argparse
import hashlib
import json
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "natives.json"
CACHE = ROOT / "build" / "cache"
LIB_SUFFIXES = (".so", ".dll", ".dylib")
NOTICE_NAMES = ("license", "notice", "thirdpartynotices")


def load_manifest():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def artifact_url(manifest, art, platform):
    base = manifest["repositories"][art["repository"]].rstrip("/")
    group = art["group"].replace(".", "/")
    name, version = art["name"], art["version"]
    return f"{base}/{group}/{name}/{version}/{name}-{version}-{platform}.zip"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        return dest
    tmp = dest.with_suffix(".part")
    print(f"  downloading {url}")
    with urllib.request.urlopen(url, timeout=300) as resp, open(tmp, "wb") as out:
        shutil.copyfileobj(resp, out)
    tmp.replace(dest)
    return dest


def cached_zip(manifest, art, platform):
    return download(artifact_url(manifest, art, platform),
                    CACHE / f"{art['name']}-{art['version']}-{platform}.zip")


def is_library(name):
    base = name.rsplit("/", 1)[-1]
    return (
        "/shared/" in name
        and base.endswith(LIB_SUFFIXES)
        and "jni" not in base.lower()
    )


def is_notice(name):
    base = name.rsplit("/", 1)[-1].lower()
    return "/" not in name.strip("/") and base.startswith(NOTICE_NAMES)


def fetch(manifest, platform, lvaddons):
    if platform not in manifest["platforms"]:
        sys.exit(f"unknown platform {platform}; expected one of {manifest['platforms']}")
    for art in manifest["artifacts"]:
        if platform not in art["platforms"]:
            continue
        expected = art["sha256"].get(platform)
        if not expected:
            sys.exit(f"{art['name']} {platform}: no sha256 in natives.json; run --update-hashes")
        zpath = cached_zip(manifest, art, platform)
        actual = sha256(zpath)
        if actual != expected:
            zpath.unlink()
            sys.exit(f"{art['name']} {platform}: sha256 {actual} doesn't match natives.json ({expected})")
        resource = lvaddons / art["addon"] / "1" / "resource"
        notices = resource / "notices" / art["name"]
        with zipfile.ZipFile(zpath) as z:
            libs = [n for n in z.namelist() if is_library(n)]
            if not libs:
                sys.exit(f"{art['name']} {platform}: no shared libraries in {zpath.name}")
            for n in libs:
                target = resource / n.rsplit("/", 1)[-1]
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(z.read(n))
                print(f"  {art['addon']}/1/resource/{target.name}")
            for n in z.namelist():
                if is_notice(n):
                    notices.mkdir(parents=True, exist_ok=True)
                    (notices / n.rsplit("/", 1)[-1]).write_bytes(z.read(n))


def clean(lvaddons):
    for resource in lvaddons.glob("*/1/resource"):
        for f in resource.iterdir():
            if f.is_file() and (f.suffix in LIB_SUFFIXES or ".so." in f.name):
                f.unlink()
        shutil.rmtree(resource / "notices", ignore_errors=True)


def update_hashes(manifest):
    for art in manifest["artifacts"]:
        art["sha256"] = {p: sha256(cached_zip(manifest, art, p)) for p in art["platforms"]}
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"updated {MANIFEST.name}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--platform", help="platform to fetch, e.g. linuxsystemcore or windowsx86-64")
    ap.add_argument("--lvaddons", type=Path, default=ROOT / "lvaddons",
                    help="lvaddons directory to fill (default: the repository's)")
    ap.add_argument("--update-hashes", action="store_true",
                    help="download every artifact and record its sha256 in natives.json")
    args = ap.parse_args()

    manifest = load_manifest()
    if args.update_hashes:
        update_hashes(manifest)
        return
    if not args.platform:
        ap.error("--platform is required")
    clean(args.lvaddons)
    fetch(manifest, args.platform, args.lvaddons)


if __name__ == "__main__":
    main()
