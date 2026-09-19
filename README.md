# AnimalBP Register desktop downloads

Official desktop installers, release notes, and checksums for AnimalBP Register.
The browser app is available at [app.animalbp.com](https://app.animalbp.com/).

## Current release: 1.4.5

Version 1.4.5 adds Microsoft Store update controls inside the Windows app,
separates Audit history into Usage and System log, improves project cryovial
selection, and keeps errors visible above open forms. The released Mac, Windows
and browser interfaces use version 1.4.5; Microsoft Store represents the same
version as 1.4.5.0.

- [Latest release and downloads](https://github.com/AnimalBP/animalbp-register-downloads/releases/latest)
- [Mac 1.4.5 installer — Apple silicon](https://github.com/AnimalBP/animalbp-register-downloads/releases/download/v1.4.5/AnimalBP-Register-1.4.5-mac-arm64.dmg)
- [Windows — Microsoft Store](https://apps.microsoft.com/detail/9NP93BBMMZ4S)
- [1.4.5 release notes and all assets](https://github.com/AnimalBP/animalbp-register-downloads/releases/tag/v1.4.5)
- [1.4.5 SHA-256 checksums](https://github.com/AnimalBP/animalbp-register-downloads/releases/download/v1.4.5/SHA256SUMS.txt)

**Release status, 19 September 2026 UTC:** GitHub 1.4.5 and Microsoft Store
1.4.5.0 are published. All nine public GitHub assets have passed download and
checksum verification. The backend and browser/demo have been deployed as 1.4.5;
the backend passed readiness and data-preservation checks. Final automated
web/demo content verification remains in progress.

The website's 1.4.5 deployment and download catalog are verified. Its existing
Cloudflare Access sign-in remains in place. The authenticated website was
checked for the Mac 1.4.5 choice, installation guidance and Microsoft Store
destination.

An installed Windows test device is currently unavailable. The package and
listing are verified, and an isolated direct-installer upgrade passed, but the
native Microsoft Store in-app check/download/install interaction has not yet
been verified on an installed Windows device.

## Installation and updates

**Mac:** Verify the DMG checksum, open it, and follow the English or Danish
`READ ME FIRST.txt` guide to copy AnimalBP Register to Applications. This release
is ad-hoc signed, without an Apple Developer ID signature or Apple notarization.
If macOS blocks it only because the developer cannot be verified, follow the
guide's **Open Anyway** steps. Do not override a malware or damaged-package
warning. Managed Macs may require IT approval. Updates remain manual; automatic
Mac updates are disabled.

**Windows from Microsoft Store:** In 1.4.5, use **Check for updates** in Settings
or Help to check Microsoft's available updates, download them through Microsoft,
and choose when to install. Save unfinished forms first; Windows may close the
app during installation. **Open Microsoft Store** remains available if a check
fails. Earlier installed versions can obtain 1.4.5 through Microsoft Store;
availability on a particular computer can depend on Store rollout and caching.

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
commit `5b782350a38208d2c2629f621ffcce5c385e0838`. Check the version-specific `SHA256SUMS.txt`
before opening a downloaded installer. The release-pinned `release-content.json`
also binds the public app/demo and website download catalog to their reviewed
content; labels alone do not establish publication or acceptance.
