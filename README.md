# AnimalBP Register desktop downloads

Official desktop installers, release notes, and checksums for AnimalBP Register.
The browser app is available at [app.animalbp.com](https://app.animalbp.com/).

## Current release: 1.4.4

Version 1.4.4 puts **Receiving note (optional)** and **Choose File** inside the
Receive goods form, before Comments, matching the online form. Select the PDF
or supported image before registration; it is attached to package 1 after the
receipt is registered.

- [Latest release and downloads](https://github.com/AnimalBP/animalbp-register-downloads/releases/latest)
- [Mac 1.4.4 installer — Apple silicon](https://github.com/AnimalBP/animalbp-register-downloads/releases/download/v1.4.4/AnimalBP-Register-1.4.4-mac-arm64.dmg)
- [Windows — Microsoft Store](https://apps.microsoft.com/detail/9NP93BBMMZ4S)
- [1.4.4 release notes and all assets](https://github.com/AnimalBP/animalbp-register-downloads/releases/tag/v1.4.4)
- [1.4.4 SHA-256 checksums](https://github.com/AnimalBP/animalbp-register-downloads/releases/download/v1.4.4/SHA256SUMS.txt)

The Mac app version is **1.4.4** and the matching Microsoft Store package version
is **1.4.4.0**. Store availability follows Microsoft's certification and rollout;
publishing a GitHub release does not publish a Store update. The release page
records each channel's verified publication status.

## Installation and updates

**Mac:** Download the DMG, verify its checksum, open it, and follow the English
or Danish `READ ME FIRST.txt` guide to copy AnimalBP Register to Applications.
The app is ad-hoc signed for package integrity, without an Apple Developer ID
signature or Apple notarization. If macOS blocks it only because the developer
cannot be verified, follow the guide's **Open Anyway** steps. Do not override a
malware or damaged-package warning. Managed Macs may require IT approval.
Mac updates are installed manually; automatic Mac updates are disabled.

**Windows from Microsoft Store:** Install and update through Microsoft Store.
The Store-installed app uses Store-managed updates. Use Microsoft Store's
Library to check for an available update.

**Windows installed directly from GitHub:** The release page provides a separate
64-bit per-user installer. This channel uses **Check for Updates**, **Download
Update**, and **Restart and install** in the app. A complete stable update
includes the `.exe`, its `.blockmap`, and `latest.yml`. The direct installer is
not Authenticode-signed; the update checksum verifies file integrity, not the
publisher's identity. Organisation policies may restrict its installation.

Existing workspaces and recorded data remain available. Desktop and browser
clients connect to the same service. These downloads contain application code,
not customer databases, backend credentials, or server signing material.

## Release provenance

The 1.4.4 Mac and Windows packages are built from reviewed source commit
`d2bcdb509870db301b44f45b71790f28220712ea`. Check the version-specific
`SHA256SUMS.txt` attached to the release before opening a downloaded installer.
Earlier releases remain available as historical records; use the latest stable
release for a new installation.
