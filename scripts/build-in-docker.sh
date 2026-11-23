#!/bin/sh
# Check the repository and build the archive for every platform in natives.json, inside the
# build container (docker/Dockerfile). The archives and their SHA256SUMS land in build/dist/.
#
#   scripts/build-in-docker.sh [version]      # version defaults to scripts/version.py's
#
# The Linux shim libraries are built first, in WPILib's containers (scripts/docker-shims.sh).
# Windows and macOS shims can't be built in a container; archives for those platforms get them
# from build/shims/ if scripts/build-shims.sh has built them there.
#
#   SHIMS_PREBUILT=1   use the shims already in build/shims/ (CI builds them in parallel jobs)
#   REQUIRE_SHIMS=1    fail if any platform's shims are missing
set -eu

version="${1:-}"
root="$(cd "$(dirname "$0")/.." && pwd)"
image=wpilib-labview-build

if [ "${SHIMS_PREBUILT:-0}" != 1 ]; then
    for platform in linuxsystemcore linuxx86-64 linuxarm64; do
        "$root/scripts/docker-shims.sh" "$platform"
    done
fi

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
    -e REQUIRE_SHIMS="${REQUIRE_SHIMS:-0}" \
    -v "$mount:/src" -w /src \
    "$image" \
    sh -euc '
        python3 scripts/check_repo.py
        if [ -z "$VERSION" ]; then VERSION="$(python3 scripts/version.py)"; fi
        echo "version $VERSION"
        require=""
        if [ "$REQUIRE_SHIMS" = 1 ]; then require=--require-shims; fi
        rm -rf build/dist
        for platform in $(python3 -c "import json; print(\" \".join(json.load(open(\"natives.json\"))[\"platforms\"]))"); do
            python3 scripts/package.py --platform "$platform" --version "$VERSION" $require
        done
        cd build/dist && sha256sum -- * > SHA256SUMS && cat SHA256SUMS
    '
