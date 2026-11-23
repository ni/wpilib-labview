#!/usr/bin/env python3
"""Print the version to build: wpilib-labview versions track the WPILib release it's built
against, natives.json's wpilibVersion.

    python3 scripts/version.py
        On a tag: the tag without its "v", which must be v<wpilibVersion>; otherwise it fails.
        Otherwise: <wpilibVersion>-<commits>-g<hash>, like WPILib's development builds, where
        <commits> counts the commits since the v<wpilibVersion> tag (or since the start).

The tag comes from --tag, or from GITHUB_REF in GitHub Actions.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True,
                                   stderr=subprocess.DEVNULL).strip()


def development_version(wpilib):
    try:
        try:
            commits = git("rev-list", "--count", f"v{wpilib}..HEAD")
        except subprocess.CalledProcessError:
            commits = git("rev-list", "--count", "HEAD")
        return f"{wpilib}-{commits}-g{git('rev-parse', '--short', 'HEAD')}"
    except (OSError, subprocess.CalledProcessError):
        return f"{wpilib}-dev"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tag", help="the release tag being built (default: from GITHUB_REF)")
    args = ap.parse_args()

    wpilib = json.loads((ROOT / "natives.json").read_text(encoding="utf-8"))["wpilibVersion"]
    tag = args.tag
    ref = os.environ.get("GITHUB_REF", "")
    if tag is None and ref.startswith("refs/tags/"):
        tag = ref[len("refs/tags/"):]
    if tag:
        if tag != f"v{wpilib}":
            sys.exit(f"tag {tag} doesn't match natives.json's wpilibVersion {wpilib}: "
                     f"wpilib-labview releases are tagged v<wpilibVersion>")
        print(wpilib)
    else:
        print(development_version(wpilib))


if __name__ == "__main__":
    main()
