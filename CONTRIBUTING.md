# Contributing to wpilib-labview

Contributions to wpilib-labview are welcome from all!

wpilib-labview is managed via [git](https://git-scm.com), with the canonical upstream
repository hosted on [GitHub](https://github.com/ni/wpilib-labview/).

wpilib-labview follows a pull-request model for development.  If you wish to
contribute, you will need to create a GitHub account, fork this project, push a
branch with your changes to your project, and then submit a pull request.

Please remember to sign off your commits (e.g., by using `git commit -s` if you
are using the command line client). This amends your git commit message with a line
of the form `Signed-off-by: Name Lastname <name.lastmail@emailaddress.com>`.
Please include all authors of any given commit into the commit message with
a `Signed-off-by` line. This indicates that you have read and signed the Developer
Certificate of Origin (see below) and are able to legally submit your code to
this repository.

See [GitHub's official documentation](https://help.github.com/articles/using-pull-requests/) for more details.

# Getting Started

- You need LabVIEW 2025 or later (see `MinimumSupportedLVVersion` in each add-on's
  `lvaddoninfo.json`) and Python 3.
- Fetch the native libraries for your platform and build its shim libraries:
  `python scripts/fetch_natives.py --platform windowsx86-64`, then
  `scripts/build-shims.sh windowsx86-64` from Git Bash with Visual Studio 2022 or later (see
  [README.md](README.md#native-libraries)).
- Point LabVIEW at the repository's add-ons by adding its `lvaddons` folder to
  `LVAddons.AdditionalLocations` in LabVIEW's configuration file (`LabVIEW.ini` on Windows,
  `labview.conf` on Linux), then restart LabVIEW.
- Save VIs in the oldest supported LabVIEW version, and don't commit per-machine files
  (`*.aliases`, `*.lvlps`, `*.UserState/`); `.gitignore` already excludes them.

# Testing

- `scripts/build-in-docker.sh` builds the Linux shim libraries in WPILib's containers and the
  archives in the same container CI uses (it needs Docker and a POSIX shell, such as Git Bash on
  Windows). It also runs `scripts/check_repo.py`, which checks the repository rules CI enforces.
- The shim libraries in `src/` have no automated tests; exercise changes to them on a Systemcore
  robot, and check that each library exports what its `.exports` file lists.
- Test changes to the APIs on a Systemcore robot with a project created from the
  FRC robot project template.

# Developer Certificate of Origin (DCO)

   Developer's Certificate of Origin 1.1

   By making a contribution to this project, I certify that:

   (a) The contribution was created in whole or in part by me and I
       have the right to submit it under the open source license
       indicated in the file; or

   (b) The contribution is based upon previous work that, to the best
       of my knowledge, is covered under an appropriate open source
       license and I have the right under that license to submit that
       work with modifications, whether created in whole or in part
       by me, under the same open source license (unless I am
       permitted to submit under a different license), as indicated
       in the file; or

   (c) The contribution was provided directly to me by some other
       person who certified (a), (b) or (c) and I have not modified
       it.

   (d) I understand and agree that this project and the contribution
       are public and that a record of the contribution (including all
       personal information I submit with it, including my sign-off) is
       maintained indefinitely and may be redistributed consistent with
       this project or the open source license(s) involved.

(taken from [developercertificate.org](https://developercertificate.org/))

See [LICENSE](https://github.com/ni/wpilib-labview/blob/main/LICENSE)
for details about how wpilib-labview is licensed.
