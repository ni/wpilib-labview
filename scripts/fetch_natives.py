#!/usr/bin/env python3
"""Download the pinned artifacts in natives.json: native libraries for the add-ons, and the
headers and libraries that the shim libraries (src/) build against.

Every artifact is a Maven zip from WPILib or REV, fetched over HTTPS with certificate
verification and checked against the sha256 in natives.json before anything is extracted. A
mismatch deletes the download and stops.

    python scripts/fetch_natives.py --platform windowsx86-64
        Shared libraries into lvaddons/<addon>/1/resource/, license files into
        lvaddons/<addon>/1/resource/notices/<artifact>/.
    python scripts/fetch_natives.py --build-deps linuxsystemcore
        Headers into build/deps/<platform>/include/ and the libraries to link against into
        build/deps/<platform>/lib/, for scripts/build-shims.sh.
    python scripts/fetch_natives.py --update-hashes
        After changing versions in natives.json: download everything and record the hashes.

WPILib's own libraries use "version": "wpilib", which is natives.json's wpilibVersion: the WPILib
release that wpilib-labview tracks (see scripts/version.py).
"""

import argparse
import hashlib
import json
import shutil
import ssl
import sys
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "natives.json"
CACHE = ROOT / "build" / "cache"
LIB_SUFFIXES = (".so", ".dll", ".dylib")
LINK_SUFFIXES = LIB_SUFFIXES + (".lib",)
NOTICE_NAMES = ("license", "notice", "thirdpartynotices")
HEADERS = "headers"


def load_manifest():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def classifiers(art):
    """Every zip an artifact pins: packaged platforms, link-only platforms, and headers."""
    return art["platforms"] + art.get("link_platforms", []) + ([HEADERS] if art.get("headers") else [])


def artifact_version(manifest, art):
    """An artifact's version; "wpilib" means the manifest's wpilibVersion, as in vendordep JSON."""
    return manifest["wpilibVersion"] if art["version"] == "wpilib" else art["version"]


def artifact_url(manifest, art, classifier):
    base = manifest["repositories"][art["repository"]].rstrip("/")
    group = art["group"].replace(".", "/")
    name, version = art["name"], artifact_version(manifest, art)
    return f"{base}/{group}/{name}/{version}/{name}-{version}-{classifier}.zip"


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
    if not url.startswith("https://"):
        sys.exit(f"refusing to download over anything but HTTPS: {url}")
    tmp = dest.with_suffix(".part")
    print(f"  downloading {url}")
    context = ssl.create_default_context()  # verifies the server's certificate and host name
    with urllib.request.urlopen(url, timeout=300, context=context) as resp, open(tmp, "wb") as out:
        shutil.copyfileobj(resp, out)
    tmp.replace(dest)
    return dest


def cached_zip(manifest, art, classifier):
    return download(artifact_url(manifest, art, classifier),
                    CACHE / f"{art['name']}-{artifact_version(manifest, art)}-{classifier}.zip")


def verified_zip(manifest, art, classifier):
    """The artifact's zip, downloaded if needed and checked against its pinned sha256."""
    expected = art["sha256"].get(classifier)
    if not expected:
        sys.exit(f"{art['name']} {classifier}: no sha256 in natives.json; run --update-hashes")
    zpath = cached_zip(manifest, art, classifier)
    actual = sha256(zpath)
    if actual != expected:
        zpath.unlink()
        sys.exit(f"{art['name']} {classifier}: sha256 {actual} doesn't match natives.json ({expected})")
    return zpath


def basename(name):
    return name.rsplit("/", 1)[-1]


def is_library(name, suffixes=LIB_SUFFIXES):
    base = basename(name)
    return "/shared/" in name and base.endswith(suffixes) and "jni" not in base.lower()


def is_notice(name):
    return "/" not in name.strip("/") and basename(name).lower().startswith(NOTICE_NAMES)


def safe_member(name):
    """A zip member's path, refusing absolute paths and '..' so nothing lands outside the target."""
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or ":" in path.parts[0]:
        sys.exit(f"unsafe path in zip: {name}")
    return path


def fetch(manifest, platform, lvaddons):
    if platform not in manifest["platforms"]:
        sys.exit(f"unknown platform {platform}; expected one of {manifest['platforms']}")
    for art in manifest["artifacts"]:
        if platform not in art["platforms"]:
            continue
        zpath = verified_zip(manifest, art, platform)
        resource = lvaddons / art["addon"] / "1" / "resource"
        notices = resource / "notices" / art["name"]
        with zipfile.ZipFile(zpath) as z:
            libs = [n for n in z.namelist() if is_library(n)]
            if not libs:
                sys.exit(f"{art['name']} {platform}: no shared libraries in {zpath.name}")
            for n in libs:
                target = resource / basename(n)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(z.read(n))
                print(f"  {art['addon']}/1/resource/{target.name}")
            for n in z.namelist():
                if is_notice(n):
                    notices.mkdir(parents=True, exist_ok=True)
                    (notices / basename(n)).write_bytes(z.read(n))


def fetch_build_deps(manifest, platform, dest):
    if platform not in manifest["platforms"]:
        sys.exit(f"unknown platform {platform}; expected one of {manifest['platforms']}")
    shutil.rmtree(dest, ignore_errors=True)
    include, lib = dest / "include", dest / "lib"
    include.mkdir(parents=True)
    lib.mkdir(parents=True)
    for art in manifest["artifacts"]:
        if art.get("headers"):
            with zipfile.ZipFile(verified_zip(manifest, art, HEADERS)) as z:
                for info in z.infolist():
                    path = safe_member(info.filename)
                    if info.is_dir() or path.parts[0] == "META-INF":
                        continue
                    target = include.joinpath(*path.parts)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(z.read(info))
            print(f"  include/  <- {art['name']} headers")
        if platform in art["platforms"] + art.get("link_platforms", []):
            with zipfile.ZipFile(verified_zip(manifest, art, platform)) as z:
                for n in z.namelist():
                    if is_library(n, LINK_SUFFIXES):
                        (lib / basename(n)).write_bytes(z.read(n))
                        print(f"  lib/{basename(n)}")


def clean(lvaddons):
    for resource in lvaddons.glob("*/1/resource"):
        for f in resource.iterdir():
            if f.is_file() and (f.suffix in LIB_SUFFIXES or ".so." in f.name):
                f.unlink()
        shutil.rmtree(resource / "notices", ignore_errors=True)


def update_hashes(manifest):
    for art in manifest["artifacts"]:
        art["sha256"] = {c: sha256(cached_zip(manifest, art, c)) for c in classifiers(art)}
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"updated {MANIFEST.name}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--platform", help="fetch the add-ons' libraries for a platform, e.g. windowsx86-64")
    mode.add_argument("--build-deps", metavar="PLATFORM", help="fetch what the shims build against")
    mode.add_argument("--update-hashes", action="store_true",
                      help="download every artifact and record its sha256 in natives.json")
    ap.add_argument("--lvaddons", type=Path, default=ROOT / "lvaddons",
                    help="lvaddons directory to fill (default: the repository's)")
    args = ap.parse_args()

    manifest = load_manifest()
    if args.update_hashes:
        update_hashes(manifest)
    elif args.build_deps:
        fetch_build_deps(manifest, args.build_deps, ROOT / "build" / "deps" / args.build_deps)
    else:
        clean(args.lvaddons)
        fetch(manifest, args.platform, args.lvaddons)


if __name__ == "__main__":
    main()
