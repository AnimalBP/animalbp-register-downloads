# AnimalBP Register desktop downloads

Official desktop installers, release notes, and checksums for AnimalBP Register.
The browser app is available at [app.animalbp.com](https://app.animalbp.com/).

## Current release: 1.4.7

Version 1.4.7 improves project material exposure, makes optional search filters
clearer, and adds complete inventory and audit exports with selectable history
periods and original document files. Mac, direct Windows, web and demo use
1.4.7; Microsoft Store represents the same version as 1.4.7.0.

- [Latest release and downloads](https://github.com/AnimalBP/animalbp-register-downloads/releases/latest)
- [Mac 1.4.7 installer — Apple silicon](https://github.com/AnimalBP/animalbp-register-downloads/releases/download/v1.4.7/AnimalBP-Register-1.4.7-mac-arm64.dmg)
- [Windows — Microsoft Store](https://apps.microsoft.com/detail/9NP93BBMMZ4S)
- [1.4.7 release notes and all assets](https://github.com/AnimalBP/animalbp-register-downloads/releases/tag/v1.4.7)
- [1.4.7 SHA-256 checksums](https://github.com/AnimalBP/animalbp-register-downloads/releases/download/v1.4.7/SHA256SUMS.txt)

The exact direct Windows installer passed an isolated 1.4.0.0 to 1.4.7.0
upgrade, preserving a synthetic user-data marker, starting with outbound traffic
blocked, and completing shutdown and cleanup. Installed Mac and Windows beta
acceptance covered project switching, optional filters, exports and original
file links in native Excel. Final Store delivery and the direct Windows live
updater flow remain separate post-publication checks.

## Inventory documents

Select **Include original documentation in a ZIP**, then use **Extract All**
before opening `Inventory.xlsx`. Keep the extracted workbook beside its
`documentation` folder. Relative workbook links open the included original files;
the Documents sheet and HTML index also list them. A workbook downloaded without
the original documents cannot open attachments offline.

## Installation and updates

**Mac:** Verify the DMG checksum, open it, and follow the English or Danish
`READ ME FIRST.txt` guide to copy AnimalBP Register to Applications. This release
is ad-hoc signed and not Apple-notarized. Updates remain manual and automatic
Mac updates are disabled. Managed Macs may require IT approval.

**Windows from Microsoft Store:** Use **Check for updates** in Settings or Help
to check Microsoft's available updates, download them through Microsoft, and
choose when to install. Save unfinished forms first; Windows may close the app
during installation. **Open Microsoft Store** remains available if a check fails.
Availability on a particular computer can depend on Store rollout and caching.

**Windows installed directly from GitHub:** The separate 64-bit per-user
installer uses the existing **Check for Updates**, **Download Update**, and
**Restart and install** flow. This channel requires matching `.exe`, `.blockmap`,
and `latest.yml` files and is separate from the Store package. The direct
installer is not Authenticode-signed; checksums verify file integrity.

Desktop and browser clients connect to the same service. Downloads contain
application code, not customer records or backend credentials. Historical
releases remain available for traceability.

## Release provenance

Packages and matching web content come from reviewed source commit
`daf0e401a9d3b3890cd134c3cc3d63538e7131c8`. Verify `SHA256SUMS.txt` before opening an installer.
The release-pinned `release-content.json` binds the matching web/demo bundle and
shared application/website download catalog to reviewed content.
