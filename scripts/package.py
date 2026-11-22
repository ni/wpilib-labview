#!/usr/bin/env python3
"""Build the add-on package for one platform: build/dist/wpilib-labview-<version>-<platform>.zip

The zip holds lvaddons/ (the add-ons as tracked in git, with the platform's native libraries from
natives.json and the shim libraries from scripts/build-shims.sh in their resource folders),
LICENSE, and THIRD-PARTY-NOTICES.md. Unzip it into a
LabVIEW add-ons location (for example ~/natinst/lvaddons on Systemcore).

Build packages with scripts/build-in-docker.sh, which runs this in the build container; Linux
packages need its strip tools.

    python3 scripts/package.py --platform linuxsystemcore --version 0.1.0
"""

import argparse
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import fetch_natives  # noqa: E402


def tracked_files(prefix):
    out = subprocess.check_output(["git", "-C", str(ROOT), "ls-files", "-z", prefix])
    return [p for p in out.decode("utf-8").split("\0") if p]


STRIP_BY_MACHINE = {0x3E: "strip", 0xB7: "aarch64-linux-gnu-strip"}  # ELF e_machine: x86-64, aarch64


def strip_debug_info(lvaddons):
    """Remove debug info from Linux libraries; WPILib's desktop builds keep it (hundreds of MB)."""
    for lib in sorted(lvaddons.glob("*/1/resource/*.so")):
        machine = int.from_bytes(lib.read_bytes()[18:20], "little")
        tool = STRIP_BY_MACHINE.get(machine)
        strip = shutil.which(tool) if tool else None
        if not strip:
            sys.exit(f"no {tool or f'strip for ELF machine {machine:#x}'} to strip {lib.name}; "
                     "build with scripts/build-in-docker.sh")
        before = lib.stat().st_size
        subprocess.run([strip, "--strip-debug", str(lib)], check=True)
        if lib.stat().st_size != before:
            print(f"  stripped {lib.name}: {before // 1024} KB -> {lib.stat().st_size // 1024} KB")


def add_shims(platform, lvaddons, require):
    """Copy the shim libraries built by scripts/build-shims.sh for this platform into the add-ons."""
    shims = ROOT / "build" / "shims" / f"shims-{platform}"
    libs = sorted(p for p in shims.glob("*/1/resource/*") if p.is_file()) if shims.is_dir() else []
    if not libs:
        if require:
            sys.exit(f"no shim libraries in {shims.relative_to(ROOT)}; build them with scripts/build-shims.sh")
        print(f"  warning: no shim libraries for {platform}; NetworkTables and REVlib VIs won't load")
        return
    for lib in libs:
        dest = lvaddons / lib.relative_to(shims)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(lib, dest)
        print(f"  {lib.relative_to(shims).as_posix()}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--platform", required=True)
    ap.add_argument("--version", required=True)
    ap.add_argument("--require-shims", action="store_true",
                    help="fail if the platform's shim libraries haven't been built")
    args = ap.parse_args()

    stage = ROOT / "build" / "stage" / args.platform
    shutil.rmtree(stage, ignore_errors=True)
    for rel in tracked_files("lvaddons"):
        dest = stage / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel, dest)
    fetch_natives.fetch(fetch_natives.load_manifest(), args.platform, stage / "lvaddons")
    add_shims(args.platform, stage / "lvaddons", args.require_shims)
    if args.platform.startswith("linux"):
        strip_debug_info(stage / "lvaddons")
    for name in ("LICENSE", "THIRD-PARTY-NOTICES.md"):
        shutil.copy2(ROOT / name, stage / name)

    dist = ROOT / "build" / "dist"
    dist.mkdir(parents=True, exist_ok=True)
    out = dist / f"wpilib-labview-{args.version}-{args.platform}.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(p for p in stage.rglob("*") if p.is_file()):
            z.write(f, f.relative_to(stage).as_posix())
    print(f"{out.relative_to(ROOT)} ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
