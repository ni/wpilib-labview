#!/usr/bin/env python3
"""Build the add-on package for one platform: build/dist/wpilib-labview-<version>-<platform>.zip

The zip holds lvaddons/ (the add-ons as tracked in git, with the platform's native libraries from
natives.json in their resource folders), LICENSE, and THIRD-PARTY-NOTICES.md. Unzip it into a
LabVIEW add-ons location (for example ~/natinst/lvaddons on Systemcore).

    python scripts/package.py --platform linuxsystemcore --version 0.1.0
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


def strip_debug_info(lvaddons):
    """Remove debug info from Linux libraries; WPILib's desktop builds keep it (hundreds of MB)."""
    strip = shutil.which("strip")
    if not strip:
        print("  warning: no strip; Linux libraries keep their debug info")
        return
    for lib in sorted(lvaddons.glob("*/1/resource/*.so")):
        before = lib.stat().st_size
        result = subprocess.run([strip, "--strip-debug", str(lib)], capture_output=True, text=True)
        if result.returncode:
            print(f"  warning: couldn't strip {lib.name}: {result.stderr.strip()}")
        elif lib.stat().st_size != before:
            print(f"  stripped {lib.name}: {before // 1024} KB -> {lib.stat().st_size // 1024} KB")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--platform", required=True)
    ap.add_argument("--version", required=True)
    args = ap.parse_args()

    stage = ROOT / "build" / "stage" / args.platform
    shutil.rmtree(stage, ignore_errors=True)
    for rel in tracked_files("lvaddons"):
        dest = stage / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel, dest)
    fetch_natives.fetch(fetch_natives.load_manifest(), args.platform, stage / "lvaddons")
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
