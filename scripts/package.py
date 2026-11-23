#!/usr/bin/env python3
"""Build the add-on archive for one platform into build/dist/.

Each archive holds lvaddons/ (the add-ons as tracked in git, with the platform's native libraries
from natives.json and the shim libraries from scripts/build-shims.sh in their resource folders),
LICENSE, THIRD-PARTY-NOTICES.md, and VERSION. Its name doesn't include the version, so the same
name is in every release, as the WPILib installer expects of the tools it bundles:

    windowsx86-64    wpilib-labview-win-x64.zip
    windowsarm64     wpilib-labview-win-arm64.zip
    linuxx86-64      wpilib-labview-linux-x64.zip
    linuxarm64       wpilib-labview-linux-arm64.zip
    osxuniversal     wpilib-labview-mac-universal.tar.gz
    linuxsystemcore  wpilib-labview-systemcore.zip     (installed on robots by systemcore-labview)

Archives are reproducible: file modes come from git, and every timestamp is the commit's.

Build archives with scripts/build-in-docker.sh, which runs this in the build container; Linux
archives need its strip tools.

    python3 scripts/package.py --platform linuxsystemcore --version 2027.0.0-alpha-7
"""

import argparse
import gzip
import shutil
import subprocess
import sys
import tarfile
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import fetch_natives  # noqa: E402

ASSETS = {
    "windowsx86-64": "wpilib-labview-win-x64.zip",
    "windowsarm64": "wpilib-labview-win-arm64.zip",
    "linuxx86-64": "wpilib-labview-linux-x64.zip",
    "linuxarm64": "wpilib-labview-linux-arm64.zip",
    "osxuniversal": "wpilib-labview-mac-universal.tar.gz",
    "linuxsystemcore": "wpilib-labview-systemcore.zip",
}


def tracked_modes(prefix):
    """{path: mode} for the files git tracks under prefix; executables are 0o755, others 0o644."""
    out = subprocess.check_output(["git", "-C", str(ROOT), "ls-files", "-s", "-z", prefix])
    modes = {}
    for entry in filter(None, out.decode("utf-8").split("\0")):
        info, path = entry.split("\t", 1)
        modes[path] = 0o755 if info.split()[0] == "100755" else 0o644
    return modes


def commit_time():
    return int(subprocess.check_output(["git", "-C", str(ROOT), "log", "-1", "--format=%ct"], text=True))


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


def write_zip(out, files, mtime):
    stamp = max(mtime, 315532800)  # zip timestamps start in 1980
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for name, path, mode in files:
            info = zipfile.ZipInfo(name, date_time=time.gmtime(stamp)[:6])
            info.create_system = 3  # Unix, so the mode below is honored when extracting
            info.external_attr = (0o100000 | mode) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, path.read_bytes())


def write_tar_gz(out, files, mtime):
    with open(out, "wb") as f, gzip.GzipFile(fileobj=f, mode="wb", mtime=mtime, filename="") as gz, \
            tarfile.open(fileobj=gz, mode="w", format=tarfile.PAX_FORMAT) as tar:
        for name, path, mode in files:
            info = tarfile.TarInfo(name)
            info.size, info.mode, info.mtime = path.stat().st_size, mode, mtime
            with open(path, "rb") as data:
                tar.addfile(info, data)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--platform", required=True, choices=sorted(ASSETS))
    ap.add_argument("--version", required=True, help="written to VERSION; see scripts/version.py")
    ap.add_argument("--require-shims", action="store_true",
                    help="fail if the platform's shim libraries haven't been built")
    args = ap.parse_args()

    stage = ROOT / "build" / "stage" / args.platform
    shutil.rmtree(stage, ignore_errors=True)
    modes = tracked_modes("lvaddons")
    for rel in sorted(modes):
        dest = stage / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel, dest)
    fetch_natives.fetch(fetch_natives.load_manifest(), args.platform, stage / "lvaddons")
    add_shims(args.platform, stage / "lvaddons", args.require_shims)
    if args.platform.startswith("linux"):
        strip_debug_info(stage / "lvaddons")
    for name in ("LICENSE", "THIRD-PARTY-NOTICES.md"):
        shutil.copy2(ROOT / name, stage / name)
    (stage / "VERSION").write_text(args.version + "\n", encoding="utf-8")

    files = []
    for path in sorted(p for p in stage.rglob("*") if p.is_file()):
        name = path.relative_to(stage).as_posix()
        files.append((name, path, modes.get(name, 0o644)))

    dist = ROOT / "build" / "dist"
    dist.mkdir(parents=True, exist_ok=True)
    out = dist / ASSETS[args.platform]
    (write_tar_gz if out.name.endswith(".tar.gz") else write_zip)(out, files, commit_time())
    print(f"{out.relative_to(ROOT)} ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
