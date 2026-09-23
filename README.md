# AnimalBP Register desktop downloads

Official desktop installers, release notes, and checksums for AnimalBP Register.
The browser app is available at [app.animalbp.com](https://app.animalbp.com/).

## Current release: 1.4.6

Version 1.4.6 adds a choice of Usage data, System log, or both for audit CSV
downloads; groups cryovial registration into numbered sections; improves new
account invitation emails; and replaces the outdated pilot wording on the
unavailable-service screen. Mac, direct Windows, browser and demo content use
version 1.4.6; Microsoft Store represents the same version as 1.4.6.0.

- [Latest release and downloads](https://github.com/AnimalBP/animalbp-register-downloads/releases/latest)
- [Mac 1.4.6 installer — Apple silicon](https://github.com/AnimalBP/animalbp-register-downloads/releases/download/v1.4.6/AnimalBP-Register-1.4.6-mac-arm64.dmg)
- [Windows — Microsoft Store](https://apps.microsoft.com/detail/9NP93BBMMZ4S)
- [1.4.6 release notes and all assets](https://github.com/AnimalBP/animalbp-register-downloads/releases/tag/v1.4.6)
- [1.4.6 SHA-256 checksums](https://github.com/AnimalBP/animalbp-register-downloads/releases/download/v1.4.6/SHA256SUMS.txt)

**Release status, 23 September 2026 UTC:** Microsoft Store 1.4.6.0 is
published with the matching release notes. The 1.4.6 backend and web/demo are
live: readiness and data-preservation checks passed, and all 16 public web
files plus their runtime URLs and security headers match the reviewed build.
The GitHub files accompany this release. The sales website now serves the matching download catalog and links; its
existing Cloudflare Access protection is retained.

An isolated direct Windows installer upgrade from 1.4.0.0 to 1.4.6.0 passed,
including preservation of a synthetic user-data marker, application startup
with outbound traffic blocked, and cleanup. An installed Windows test device
is currently unavailable. Native Microsoft Store update check/download/install,
the direct app's live updater delivery and authenticated Windows interactions
remain unverified on a user device.

## Installation and updates

**Mac:** Verify the DMG checksum, open it, and follow the English or Danish
`READ ME FIRST.txt` guide to copy AnimalBP Register to Applications. This release
is ad-hoc signed, without an Apple Developer ID signature or Apple notarization.
If macOS blocks it only because the developer cannot be verified, follow the
guide's **Open Anyway** steps. Do not override a malware or damaged-package
warning. Managed Macs may require IT approval. Updates remain manual; automatic
Mac updates are disabled.

**Windows from Microsoft Store:** Use **Check for updates** in Settings
or Help to check Microsoft's available updates, download them through Microsoft,
and choose when to install. Save unfinished forms first; Windows may close the
app during installation. **Open Microsoft Store** remains available if a check
fails. Earlier installed versions can obtain the update through Microsoft Store
after Microsoft approves and distributes it; availability on a particular
computer can depend on Store rollout and caching.

**Windows installed directly from GitHub:** Use the separate 64-bit per-user
installer and the app's existing **Check for Updates**, **Download Update**, and
**Restart and install** flow. This channel requires the matching `.exe`,
`.blockmap`, and `latest.yml`. It is not the Store package. The direct installer
is not Authenticode-signed; checksums verify integrity rather than publisher
identity. Organisation policies may restrict installation.

Desktop and browser clients connect to the same service. These downloads contain
application code, not customer databases, backend credentials, or server signing
material. Historical releases remain available for traceability.

## Release provenance

The release packages and matching web content are built from reviewed source
commit `ba9fcfde1a052cb3941126010daf0e26cf8136b1`. Check the version-specific `SHA256SUMS.txt`
before opening a downloaded installer. The release-pinned `release-content.json`
also binds the public app/demo and website download catalog to their reviewed
content; labels alone do not establish publication or acceptance.
