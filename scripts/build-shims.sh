#!/bin/sh
# Build the shim libraries (src/) for one platform into
# build/shims/shims-<platform>/<add-on>/1/resource/.
#
#   scripts/build-shims.sh <platform>
#
# Fetches the pinned headers and libraries first (scripts/fetch_natives.py --build-deps).
# Linux platforms build in WPILib's containers; use scripts/docker-shims.sh. Windows builds with the
# newest Visual Studio installed, 2022 or later (run from Git Bash), macOS with Xcode.
set -eu

platform="$1"
# Windows-form paths under Git Bash, so CMake and Python get paths they understand
root="$(cd "$(dirname "$0")/.." && { pwd -W 2>/dev/null || pwd; })"
deps="$root/build/deps/$platform"
obj="$root/build/shim-obj/$platform"
out="$root/build/shims/shims-$platform"

case "$platform" in
    linuxsystemcore) set -- -DCMAKE_TOOLCHAIN_FILE="$root/cmake/linuxsystemcore.cmake" ;;
    linuxarm64) set -- -DCMAKE_TOOLCHAIN_FILE="$root/cmake/linuxarm64.cmake" ;;
    linuxx86-64) set -- ;;
    windowsx86-64) set -- -A x64 ;;
    windowsarm64) set -- -A ARM64 ;;
    osxuniversal) set -- -DCMAKE_OSX_ARCHITECTURES="x86_64;arm64" ;;
    *) echo "unknown platform: $platform" >&2; exit 1 ;;
esac

"${PYTHON:-python3}" "$root/scripts/fetch_natives.py" --build-deps "$platform"
rm -rf "$obj" "$out"
cmake -S "$root/src" -B "$obj" -DCMAKE_BUILD_TYPE=Release -DDEPS="$deps" \
    -DCMAKE_INSTALL_PREFIX="$out" "$@"
cmake --build "$obj" --config Release --parallel
cmake --install "$obj" --config Release
