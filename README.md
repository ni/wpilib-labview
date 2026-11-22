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

The add-ons call native libraries from WPILib and REV, which are not committed here.
[`natives.json`](natives.json) pins each one by Maven coordinates, version, and sha256, and
[`scripts/fetch_natives.py`](scripts/fetch_natives.py) downloads the right ones into each
add-on's `resource` folder. To work from a clone:

```bash
python scripts/fetch_natives.py --platform windowsx86-64
```

To move to new WPILib or REV versions, change the versions in `natives.json`, then run
`python scripts/fetch_natives.py --update-hashes` to record the new hashes.

Notes:

- On Systemcore, the robot image already provides `wpiutil`, so the `linuxsystemcore` package
  doesn't include it.
- REVlib's `REVLibWpi` uses the HAL in the wpilib add-on, so the robot program has to initialize
  the HAL (`HAL_Init.vi`) before it calls REVlib VIs.
- REV doesn't publish Windows arm64 libraries, so the `windowsarm64` package has no REV libraries.

## Not done yet

- **NI shim libraries.** NetworkTables and REVlib also call two NI-built libraries,
  `FRC_NetworkTablesLV` and `FRC_REVLibLV`, which aren't in the packages yet. Until they are,
  those VIs can't load their libraries.
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

[`.github/workflows/build.yml`](.github/workflows/build.yml) checks the repository, builds the
package for every platform, signs the packages on every build except pull requests, and publishes
them as a release for `v*` tags. To build a package locally:

```bash
python scripts/check_repo.py
python scripts/package.py --platform linuxsystemcore --version 0.0.0-dev
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

BSD-3-Clause; see [LICENSE](LICENSE). The native libraries in the packages come with their own
licenses; see [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md).
