#!/bin/sh
# Check the repository and build the package for every platform in natives.json, inside the
# build container (docker/Dockerfile). The packages land in build/dist/.
#
#   scripts/build-in-docker.sh [version]      # version defaults to 0.0.0-dev
set -eu

version="${1:-0.0.0-dev}"
root="$(cd "$(dirname "$0")/.." && pwd)"
image=wpilib-labview-build

# Git Bash on Windows: don't rewrite /src, and give Docker the Windows form of the path
export MSYS_NO_PATHCONV=1
mount="$(cd "$root" && { pwd -W 2>/dev/null || pwd; })"

docker build -t "$image" "$root/docker"

# Run as the calling user so build/ isn't owned by root; trust the mounted checkout for git.
docker run --rm \
    --user "$(id -u):$(id -g)" \
    -e HOME=/tmp \
    -e GIT_CONFIG_COUNT=1 -e GIT_CONFIG_KEY_0=safe.directory -e GIT_CONFIG_VALUE_0='*' \
    -e VERSION="$version" \
    -v "$mount:/src" -w /src \
    "$image" \
    sh -euc '
        python3 scripts/check_repo.py
        for platform in $(python3 -c "import json; print(\" \".join(json.load(open(\"natives.json\"))[\"platforms\"]))"); do
            python3 scripts/package.py --platform "$platform" --version "$VERSION"
        done
    '
