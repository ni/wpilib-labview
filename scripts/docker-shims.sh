#!/bin/sh
# Build a Linux platform's shim libraries in WPILib's build container for it (docker/wpilib-*),
# as WPILib's own CI does: the Systemcore cross-compiler for linuxsystemcore, the native compiler
# of the same image for linuxx86-64, and the arm64 cross-compiler for linuxarm64.
#
#   scripts/docker-shims.sh <linux platform>
set -eu

platform="$1"
case "$platform" in
    linuxsystemcore | linuxx86-64) image=wpilib-systemcore ;;
    linuxarm64) image=wpilib-aarch64 ;;
    *) echo "not a Linux platform: $platform" >&2; exit 1 ;;
esac

root="$(cd "$(dirname "$0")/.." && pwd)"
# Git Bash on Windows: don't rewrite /src, and give Docker the Windows form of the path
export MSYS_NO_PATHCONV=1
mount="$(cd "$root" && { pwd -W 2>/dev/null || pwd; })"

docker build -t "wpilib-labview-$image" "$root/docker/$image"
docker run --rm \
    --user "$(id -u):$(id -g)" \
    -e HOME=/tmp \
    -v "$mount:/src" -w /src \
    "wpilib-labview-$image" \
    sh scripts/build-shims.sh "$platform"
