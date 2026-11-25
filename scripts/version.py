#!/usr/bin/env python3
"""Print the version to build: wpilib-labview versions track the WPILib release it's built
against, natives.json's wpilibVersion.

    python3 scripts/version.py
        On a tag: the tag without its "v". It must be v<wpilibVersion>, or v<wpilibVersion>.<n>
        for the n-th later release built against the same WPILib; otherwise it fails.
        Otherwise: <release>-<commits>-g<hash>, like WPILib's development builds, where <release>
        is the newest release of this wpilibVersion that HEAD contains (wpilibVersion if none) and
        <commits> counts the commits since it.

    python3 scripts/version.py --next-tag
        The tag that releases HEAD: v<wpilibVersion>, or v<wpilibVersion>.<n+1> once
        v<wpilibVersion> (n = 0) or v<wpilibVersion>.<n> exists. Fails if HEAD is already released.

The tag comes from --tag, or from GITHUB_REF in GitHub Actions.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True,
                                   stderr=subprocess.DEVNULL).strip()


def release_number(tag, wpilib):
    """n for a release tag of this WPILib version (v<wpilib> is 0, v<wpilib>.<n> is n), else None."""
    m = re.fullmatch(rf"v{re.escape(wpilib)}(?:\.([1-9][0-9]*))?", tag)
    return int(m.group(1) or 0) if m else None


def release_tags(wpilib):
    tags = git("tag", "--list", f"v{wpilib}", f"v{wpilib}.*").split()
    return {tag: n for tag in tags if (n := release_number(tag, wpilib)) is not None}


def development_version(wpilib):
    try:
        contained = [(n, tag) for tag, n in release_tags(wpilib).items()
                     if subprocess.run(["git", "-C", str(ROOT), "merge-base", "--is-ancestor", tag, "HEAD"],
                                       stderr=subprocess.DEVNULL).returncode == 0]
        if contained:
            _, tag = max(contained)
            base, commits = tag[1:], git("rev-list", "--count", f"{tag}..HEAD")
        else:
            base, commits = wpilib, git("rev-list", "--count", "HEAD")
        return f"{base}-{commits}-g{git('rev-parse', '--short', 'HEAD')}"
    except (OSError, subprocess.CalledProcessError):
        return f"{wpilib}-dev"


def next_tag(wpilib):
    tags = release_tags(wpilib)
    released = set(git("tag", "--points-at", "HEAD").split()) & set(tags)
    if released:
        sys.exit(f"HEAD is already released as {', '.join(sorted(released))}")
    if not tags:
        return f"v{wpilib}"
    return f"v{wpilib}.{max(tags.values()) + 1}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tag", help="the release tag being built (default: from GITHUB_REF)")
    ap.add_argument("--next-tag", action="store_true", help="print the tag that releases HEAD")
    args = ap.parse_args()

    wpilib = json.loads((ROOT / "natives.json").read_text(encoding="utf-8"))["wpilibVersion"]
    if args.next_tag:
        print(next_tag(wpilib))
        return
    tag = args.tag
    ref = os.environ.get("GITHUB_REF", "")
    if tag is None and ref.startswith("refs/tags/"):
        tag = ref[len("refs/tags/"):]
    if tag:
        if release_number(tag, wpilib) is None:
            sys.exit(f"tag {tag} doesn't match natives.json's wpilibVersion {wpilib}: wpilib-labview "
                     f"releases are tagged v<wpilibVersion> or v<wpilibVersion>.<n>")
        print(tag[1:])
    else:
        print(development_version(wpilib))

if __name__ == "__main__":
    main()
