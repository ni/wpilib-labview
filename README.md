# wpilib-labview

LabVIEW APIs for WPILib and FRC vendor libraries on Systemcore, as LabVIEW add-ons.

| Add-on | What it is |
|---|---|
| [`lvaddons/wpilib`](lvaddons/wpilib) | The LabVIEW WPILib: Systemcore (`MRC`) wrappers, NetworkTables, the WPI robot framework, palettes, and the FRC project templates |
| [`lvaddons/REVlib`](lvaddons/REVlib) | LabVIEW wrappers for REV Robotics' REVLib (SPARK motor controllers) |
| [`lvaddons/systemcore-deploy`](lvaddons/systemcore-deploy) | The development-machine side of deploying a LabVIEW project to a Systemcore robot with `git push`. The robot side is in [ni/systemcore-labview](https://github.com/ni/systemcore-labview). |

## Installing

Each release has one package per platform, `wpilib-labview-<version>-<platform>.zip`. Unzip it
into a LabVIEW add-ons location, or into any folder listed in `LVAddons.AdditionalLocations` in
LabVIEW's configuration file, and restart LabVIEW. On Systemcore the add-ons live in
`~/natinst/lvaddons`.

| Platform | Package |
|---|---|
| Systemcore | `linuxsystemcore` |
| Windows | `windowsx86-64`, `windowsarm64` |
| Linux | `linuxx86-64`, `linuxarm64` |
| macOS | `osxuniversal` |

Each package has a `.sigstore.json` file next to it: its signed build provenance. To check a
package with the [GitHub CLI](https://cli.github.com/):

```bash
gh attestation verify wpilib-labview-<version>-<platform>.zip --repo ni/wpilib-labview \
  --bundle wpilib-labview-<version>-<platform>.zip.sigstore.json
```

## Native libraries

The add-ons call two kinds of native libraries, neither of which is committed here:

- **WPILib and REV libraries** (`wpiHal`, `ntcoreffi`, `MrcLib`, `REVLibDriver`, and others).
  [`natives.json`](natives.json) pins each one by Maven coordinates, version, and sha256, and
  [`scripts/fetch_natives.py`](scripts/fetch_natives.py) downloads the right ones into each
  add-on's `resource` folder.
- **The shim libraries** `FRC_NetworkTablesLV` (wpilib) and `FRC_REVLibLV` (REVlib), which adapt
  those libraries to LabVIEW. Their source is in [`src/`](src); see [Building](#building).

Every download, including the headers and libraries the shims build against, is fetched over
HTTPS with certificate verification and checked against its pinned sha256 before it's used; a
mismatch deletes it and stops the build.

To work from a clone, fetch a platform's libraries, then build its shims:

```bash
python scripts/fetch_natives.py --platform windowsx86-64
scripts/build-shims.sh windowsx86-64      # from Git Bash, with Visual Studio 2022 or later
```

To move to new WPILib or REV versions, change the versions in `natives.json`, then run
`python scripts/fetch_natives.py --update-hashes` to record the new hashes.

Notes:

- On Systemcore, the robot image already provides `wpiutil` and `MrcLib`, so the
  `linuxsystemcore` package doesn't include them. (`MrcLib`'s Systemcore build on Maven is only a
  stub to link the shims against.)
- REVlib's `REVLibWpi` uses the HAL in the wpilib add-on, so the robot program has to initialize
  the HAL (`HAL_Init.vi`) before it calls REVlib VIs.
- REV doesn't publish Windows arm64 libraries, so the `windowsarm64` package has no REV libraries,
  and its `FRC_REVLibLV` returns "not implemented" for every call.

## Not done yet

- **Examples** for Systemcore are still to be written.
- **A Dashboard project template.**
- **The Swerve subsystem template** is still being brought over.
- **Differential drive** (Arcade and Tank) VIs for Systemcore motor controllers.
- **macOS and Linux desktop** packages are built but untested.

## The bootstrap deploy key

`systemcore-deploy` ships with a default SSH key pair (`vi.lib/systemcore-deploy/team-key/`) so a
team can deploy to a new robot without any setup. The private key is public on purpose. It's a
convenience, not a protection: a team secures its robots by installing its own key and removing
the bootstrap key. See [SECURITY.md](SECURITY.md).

## Building

Builds run in containers wherever the platform allows, the same way in CI and locally, and the
container images are pinned by digest:

- The **shim libraries** for Linux build in WPILib's own build containers
  ([`docker/wpilib-systemcore`](docker/wpilib-systemcore),
  [`docker/wpilib-aarch64`](docker/wpilib-aarch64)) with
  [`scripts/docker-shims.sh`](scripts/docker-shims.sh). Windows (Visual Studio 2022 or later) and
  macOS (Xcode) shims build on those systems with [`scripts/build-shims.sh`](scripts/build-shims.sh).
- The **packages** build in [`docker/Dockerfile`](docker/Dockerfile).

[`scripts/build-in-docker.sh`](scripts/build-in-docker.sh) builds the Linux shims, checks the
repository rules, and builds the package for every platform into `build/dist/`. Windows and macOS
packages include their shims only if `scripts/build-shims.sh` has built them:

```bash
scripts/build-in-docker.sh 0.0.0-dev
```

[`.github/workflows/build.yml`](.github/workflows/build.yml) builds every platform's shims, then
runs that script, signs the packages on every build except pull requests, and publishes them as
a release for `v*` tags.

The shims call LabVIEW's C API, declared by the LabVIEW 2026 Q3 `cintools` headers in
[`src/cintools`](src/cintools).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

BSD-3-Clause; see [LICENSE](LICENSE), except the LabVIEW `cintools` headers in
[`src/cintools`](src/cintools), which keep NI's notice. The native libraries in the packages come
with their own licenses; see [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md).
