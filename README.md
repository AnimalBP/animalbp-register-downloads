# AnimalBP Register desktop downloads

This public repository is the official download location for AnimalBP Register
desktop pilot builds. It contains release guidance and packaged application
files only. The cloud backend, customer records, credentials, databases,
environment configuration, and signing material are not included.

## Current pilot release

Version **1.3.1-beta.20** is available from the
[GitHub release page](https://github.com/AnimalBP/animalbp-register-downloads/releases/tag/v1.3.1-beta.20).

- [Download for macOS Apple silicon](https://github.com/AnimalBP/animalbp-register-downloads/releases/download/v1.3.1-beta.20/AnimalBP-Register-1.3.1-beta.20-mac-arm64.dmg)
- [Download for Windows 64-bit](https://github.com/AnimalBP/animalbp-register-downloads/releases/download/v1.3.1-beta.20/AnimalBP-Register-1.3.1-beta.20-win-x64.zip)
- [Download SHA-256 checksums](https://github.com/AnimalBP/animalbp-register-downloads/releases/download/v1.3.1-beta.20/SHA256SUMS.txt)

## Important pilot warning

These are **pilot builds**. The macOS application has a complete ad-hoc
signature so its application bundle and nested Electron components can be
verified as internally consistent. It does not have an Apple Developer ID
signature and is not Apple-notarised. Windows is not Authenticode-signed.
Gatekeeper and SmartScreen may therefore still request manual approval. Download
only from this repository and verify the published SHA-256 checksum.

The desktop application connects to the same protected AnimalBP cloud service
as the browser application. It does not contain a PostgreSQL database or a copy
of customer records. Remembered sign-in uses a rotating server-revocable device
credential protected by macOS Keychain or Windows operating-system credential
protection. The password is not stored by the desktop application.

If the connection is lost, an encrypted, time-limited local snapshot may be
shown in view-only mode. Changes cannot be entered or queued until the secure
connection returns.

## Installation

### macOS Apple silicon

1. Download the DMG and verify its SHA-256 checksum.
2. Open the DMG and drag **AnimalBP Register** to Applications.
3. Because this pilot is not Apple-notarised, macOS may block the first launch.
   Only use Finder's manual Open action or **Open Anyway** in Privacy & Security
   if the checksum matches this release and the file came from this repository.

### Windows 64-bit

1. Download the ZIP and verify its SHA-256 checksum.
2. Extract the ZIP to a user-controlled folder.
3. Open **AnimalBP Register.exe** from the extracted folder.
4. Windows may show a SmartScreen warning because this pilot is unsigned.

Beta.20 can check this public repository for a newer pilot and open its manual
download. Automatic in-app installation remains disabled for unsigned pilot
builds until properly signed releases are available.
