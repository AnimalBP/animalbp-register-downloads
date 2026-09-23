# AnimalBP Register 1.4.6

[Latest release](https://github.com/AnimalBP/animalbp-register-downloads/releases/latest)
· [1.4.6 downloads and checksums](https://github.com/AnimalBP/animalbp-register-downloads/releases/tag/v1.4.6)

## What's changed

- **Audit CSV downloads:** Choose Usage data, System log, or both before
  downloading. The dialog explains the 500-event limit and export scope.
  Existing visibility permissions and protection against spreadsheet formulas
  in exported values remain in place.
- **Cryovial registration:** Numbered sections separate culture and vial
  details, source and lineage, and storage. Freezer, rack, box and interactive
  position selection appear together. Storage changes clear incompatible
  positions with an explanation while preserving user-edited vial identifiers.
- **New account emails:** A shared professional invitation gives users and
  administrators clear sign-in details and first-password-change instructions.
  Temporary-password restrictions and account permissions are unchanged.
- **Unavailable-service screen:** The message names AnimalBP Register without
  calling the service a pilot or assuming the hosting Mac is offline. It gives
  users a clear retry and contact action.

The receiving-note chooser remains inside Receive goods, before Comments.
Usage remains the default Audit history view. No database migration is required
for this update.

## Versions and release status

Mac, direct Windows installers, browser and demo content use **1.4.6**. The
corresponding Microsoft Store package uses **1.4.6.0**. The demo uses the same
web bundle as the browser app.

**Release status, 23 September 2026 UTC:** Microsoft Store 1.4.6.0 is
published with the matching release notes. The 1.4.6 backend and web/demo are
live: readiness and data-preservation checks passed, and all 16 public web
files plus their runtime URLs and security headers match the reviewed build.
The GitHub files accompany this release. The sales website is being aligned
with these verified downloads; its existing Access protection is retained.

The exact direct Windows installer passed an isolated 1.4.0.0 → 1.4.6.0 upgrade,
preserving a synthetic user-data marker and starting with application outbound
traffic blocked. Shutdown and cleanup were verified. This exercises installer
replacement; live updater discovery/download and authenticated Windows
interactions remain unverified. An installed Windows test device is currently
unavailable, so native Microsoft Store update check, download and installation
also remain unverified on a user device.

## Installation and update channels

**Mac:** Distribution remains manual, ad-hoc signed and not Apple-notarized,
with automatic Mac updates disabled. Verify the checksum and follow the
English or Danish `READ ME FIRST.txt` installation guide included in the DMG.
Managed Macs may require IT approval.

**Windows from Microsoft Store:** Existing Settings and Help update controls
check and download through Microsoft, then wait for an explicit installation
action. Save unfinished forms before installing; Windows may close the app.
Open Microsoft Store remains available if a check fails. Version 1.4.6.0 is published in Microsoft Store; delivery can depend on
Store caching and the device.
Store installations do not use the EXE updater.

**Direct Windows installations:** The existing Check for Updates, Download
Update, and Restart and install flow uses matching `.exe`, `.blockmap` and
`latest.yml` assets. The separate per-user installer is not Authenticode-signed;
checksums verify file integrity rather than publisher identity. Organisation
policies may restrict installation.

Built from reviewed source commit `ba9fcfde1a052cb3941126010daf0e26cf8136b1`.
Use the `SHA256SUMS.txt` attached to the [1.4.6 release](https://github.com/AnimalBP/animalbp-register-downloads/releases/tag/v1.4.6)
to verify files. `release-content.json` pins the matching web build and shared
app/website download catalog for release verification. Earlier notes and assets
remain in [release history](https://github.com/AnimalBP/animalbp-register-downloads/releases).
