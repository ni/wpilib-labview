# wpilib-labview

LabVIEW APIs for WPILib and FRC vendor libraries on Systemcore, as LabVIEW add-ons.

| Add-on | What it is |
|---|---|
| [`lvaddons/wpilib`](lvaddons/wpilib) | The LabVIEW WPILib: Systemcore (`MRC`) wrappers, NetworkTables, the WPI robot framework, palettes, and the FRC project templates |
| [`lvaddons/REVlib`](lvaddons/REVlib) | LabVIEW wrappers for REV Robotics' REVLib (SPARK motor controllers) |
| [`lvaddons/systemcore-deploy`](lvaddons/systemcore-deploy) | The development-machine side of deploying a LabVIEW project to a Systemcore robot with `git push`. The robot side is in [ni/systemcore-labview](https://github.com/ni/systemcore-labview). |

## Installing

The [WPILib installer](https://github.com/wpilibsuite/WPILibInstaller-Avalonia) is meant to
install these add-ons along with the rest of WPILib, the way it installs AdvantageScope; until it
does, install them by hand from a release.

Releases track WPILib: `v2027.0.0-alpha-8` has the add-ons for WPILib 2027.0.0-alpha-8, built
against its libraries, and `v2027.0.0-alpha-8.1`, `.2`, ... are later releases built against the
same WPILib. Alpha and beta releases are marked as prereleases. Each release has one
archive per platform, with the same names in every release:

| Platform | Archive |
|---|---|
| Windows x64 | `wpilib-labview-win-x64.zip` |
| Windows arm64 | `wpilib-labview-win-arm64.zip` |
| Linux x64 | `wpilib-labview-linux-x64.zip` |
| Linux arm64 | `wpilib-labview-linux-arm64.zip` |
| macOS (Intel and Apple silicon) | `wpilib-labview-mac-universal.tar.gz` |
| Systemcore | `wpilib-labview-systemcore.zip`, which robots get with [systemcore-labview](https://github.com/ni/systemcore-labview) |

Each archive holds `lvaddons/` (one folder per add-on), the license and third-party notices, and
`VERSION`. To install one, extract it and either:

- copy the folders in its `lvaddons/` into LabVIEW's add-ons folder (`C:\Program Files\NI\LVAddons`
  on Windows, `/Library/Application Support/National Instruments/LVAddons/` on macOS,
  `/usr/local/natinst/share/lvaddons/` on Linux), or
- add the path of its `lvaddons/` folder to `LVAddons.AdditionalLocations` in LabVIEW's
  configuration file (LabVIEW 2024 Q1 and later),

then restart LabVIEW.

`SHA256SUMS` lists every archive's hash, and each file has a `.sigstore.json` file next to it: its
signed build provenance. To check one with the [GitHub CLI](https://cli.github.com/):

```bash
gh attestation verify wpilib-labview-win-x64.zip --repo ni/wpilib-labview \
  --bundle wpilib-labview-win-x64.zip.sigstore.json
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

To move to a new WPILib release, change `wpilibVersion` in `natives.json` (WPILib's own libraries
use `"version": "wpilib"`); for REV or MrcLib, change their versions. Then run
`python scripts/fetch_natives.py --update-hashes` to record the new hashes.

To release, run the **Build** workflow on `main` with **Release** checked (Actions » Build » Run
workflow). It tags the commit `v<wpilibVersion>`, or `v<wpilibVersion>.<n>` if that WPILib version
has been released before, builds it and publishes the release ([`scripts/version.py`](scripts/version.py)
picks the tag; CI refuses any other). Merging to `main` doesn't release anything. Builds between
releases are versioned `<release>-<commits>-g<hash>`, like WPILib's, for example
`2027.0.0-alpha-8-1-g4de9574`.

Notes:

- On Systemcore, the robot image already provides `wpiutil`, `MrcLib`, and the libraries that `wpiHal`
  and `wpimath` load (`ntcore`, `wpinet`, `datalog`, `telemetry`, `tunables`), so
  `wpilib-labview-systemcore.zip` doesn't include them; the desktop archives do. (`MrcLib`'s Systemcore
  build on Maven is only a stub to link the shims against.)
- The desktop archives also carry the robot's libraries: the wpilib and REVlib add-ons have a
  `1/systemcore/` folder with the libraries and notices `wpilib-labview-systemcore.zip` has in their
  place, and `1/systemcore/desktop-files`, which lists the desktop files they replace. When the
  deploy tool sends an add-on to a robot, it sends those instead of the desktop libraries, so the
  robot gets the add-on exactly as `wpilib-labview-systemcore.zip` has it.
- REVlib's `REVLibWpi` uses the HAL in the wpilib add-on, so the robot program has to initialize
  the HAL (`HAL_Init.vi`) before it calls REVlib VIs.
- REV doesn't publish Windows arm64 libraries, so `wpilib-labview-win-arm64.zip` has no REV libraries,
  and its `FRC_REVLibLV` returns "not implemented" for every call.

## Not done yet

- **Examples** for Systemcore are still to be written.
- **A Dashboard project template.**
- **The Swerve subsystem template** is still being brought over.
- **Differential drive** (Arcade and Tank) VIs for Systemcore motor controllers.
- **macOS and Linux desktop** archives are built but untested.

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
- The **archives** build in [`docker/Dockerfile`](docker/Dockerfile).

[`scripts/build-in-docker.sh`](scripts/build-in-docker.sh) builds the Linux shims, checks the
repository rules, and builds the archive for every platform, and their `SHA256SUMS`, into
`build/dist/`. Windows and macOS archives include their shims only if `scripts/build-shims.sh` has
built them:

```bash
scripts/build-in-docker.sh
```

[`.github/workflows/build.yml`](.github/workflows/build.yml) builds every platform's shims, then
runs that script, signs the archives on every build except pull requests, and publishes them as
a release when run with **Release** (or for a pushed `v*` tag).

The shims call LabVIEW's C API, declared by the LabVIEW 2026 Q3 `cintools` headers in
[`src/cintools`](src/cintools).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

BSD-3-Clause; see [LICENSE](LICENSE), except the LabVIEW `cintools` headers in
[`src/cintools`](src/cintools), which keep NI's notice. The native libraries in the archives come
with their own licenses; see [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md).
