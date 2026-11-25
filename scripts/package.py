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

The desktop archives also carry the robot's libraries: each add-on version with native libraries
gets a systemcore/ folder holding the files the Systemcore archive has in their place (libraries
and notices, at the same paths), and systemcore/desktop-files listing the desktop files they
replace. When the deploy tool (systemcore-deploy) sends an add-on to a robot, it sends those in
place of the desktop libraries, so the robot gets the add-on as the Systemcore archive has it.

The desktop archives leave out the robot-only files (ROBOT_ONLY: Tools menu entries that only work in
the robot's own LabVIEW) and their lines in the menu order files.

Archives are reproducible: file modes come from git, and every timestamp is the commit's.

Build archives with scripts/build-in-docker.sh, which runs this in the build container; every
archive needs its strip tools, since every archive has Linux libraries (the desktop ones carry the
robot's).

    python3 scripts/package.py --platform linuxsystemcore --version 2027.0.0-alpha-8
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

# Files only the Systemcore archive gets. LabVIEW lists every VI in an add-on's project folder in its
# Tools menu, so the only way to keep a robot-only menu entry off desktops is to leave its VI out.
ROBOT_ONLY = ("lvaddons/systemcore-deploy/1/project/Systemcore/Use the Robot Image's Add-ons.vi",)


def drop_robot_only(stage):
    """Remove the robot-only files from a desktop archive's stage, and their entries from the menu
    order file (<folder>/<folder>.txt), with a separator the removal would leave at its end."""
    for rel in ROBOT_ONLY:
        path = stage / rel
        path.unlink()
        menu = path.parent / f"{path.parent.name}.txt"
        if menu.is_file():
            lines = [line for line in menu.read_text(encoding="utf-8").splitlines() if line != path.name]
            while lines and lines[-1] == "-":
                lines.pop()
            menu.write_bytes("".join(line + "\n" for line in lines).encode("utf-8"))


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


def files_under(root):
    return {p.relative_to(root) for p in root.rglob("*") if p.is_file()} if root.is_dir() else set()


def add_natives(platform, lvaddons, require_shims):
    """Put the platform's libraries, shims and notices in the add-ons; return the files added."""
    before = files_under(lvaddons)
    fetch_natives.fetch(fetch_natives.load_manifest(), platform, lvaddons)
    add_shims(platform, lvaddons, require_shims)
    if platform.startswith("linux"):
        strip_debug_info(lvaddons)
    return files_under(lvaddons) - before


ROBOT = "linuxsystemcore"
ROBOT_LIBS = "systemcore"


def add_robot_libraries(lvaddons, desktop_files, require_shims):
    """Give each add-on version with native libraries a systemcore/ folder: the robot's libraries
    and notices at the paths the Systemcore archive has them, and desktop-files, the files they
    replace (see the docstring)."""
    robot = lvaddons.parent.parent / f"{lvaddons.parent.name}-robot"
    shutil.rmtree(robot, ignore_errors=True)
    print(f"  the robot's libraries ({ROBOT}):")
    robot_files = add_natives(ROBOT, robot, require_shims)
    replaced = {}
    for rel in desktop_files | robot_files:
        replaced.setdefault(Path(*rel.parts[:2]), set())
    for rel in desktop_files:
        replaced[Path(*rel.parts[:2])].add(Path(*rel.parts[2:]).as_posix())
    for rel in robot_files:
        dest = lvaddons / rel.parts[0] / rel.parts[1] / ROBOT_LIBS / Path(*rel.parts[2:])
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(robot / rel, dest)
    for version, paths in sorted(replaced.items()):
        listing = lvaddons / version / ROBOT_LIBS / "desktop-files"
        listing.parent.mkdir(parents=True, exist_ok=True)
        listing.write_text("".join(f"{p}\n" for p in sorted(paths)), encoding="utf-8", newline="\n")
    shutil.rmtree(robot)


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
    desktop_files = add_natives(args.platform, stage / "lvaddons", args.require_shims)
    if args.platform != ROBOT:
        drop_robot_only(stage)
        add_robot_libraries(stage / "lvaddons", desktop_files, args.require_shims)
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
