# AnimalBP Register desktop downloads

This public repository is the official download location for AnimalBP Register
desktop pilot builds. It contains release guidance and packaged application
files only. The cloud backend, customer records, credentials, databases,
environment configuration, and signing material are not included.

## Current pilot release

Version **1.3.1-beta.17** is available from the
[GitHub release page](https://github.com/AnimalBP/animalbp-register-downloads/releases/tag/v1.3.1-beta.17).

- [Download for macOS Apple silicon](https://github.com/AnimalBP/animalbp-register-downloads/releases/download/v1.3.1-beta.17/AnimalBP-Register-1.3.1-beta.17-mac-arm64.dmg)
- [Download for Windows 64-bit](https://github.com/AnimalBP/animalbp-register-downloads/releases/download/v1.3.1-beta.17/AnimalBP-Register-1.3.1-beta.17-win-x64.zip)
- [Download SHA-256 checksums](https://github.com/AnimalBP/animalbp-register-downloads/releases/download/v1.3.1-beta.17/SHA256SUMS.txt)

## Important pilot warning

These files are **unsigned pilot builds**. macOS Gatekeeper and Windows
SmartScreen may warn before the app opens. They are not signed or notarised
production installers. Download only from this repository and verify the
published SHA-256 checksum.

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
3. Because this pilot is unsigned, macOS may block the first launch. Only use
   the operating system's manual Open action if the checksum matches this
   release and the file came from this repository.

### Windows 64-bit

1. Download the ZIP and verify its SHA-256 checksum.
2. Extract the ZIP to a user-controlled folder.
3. Open **AnimalBP Register.exe** from the extracted folder.
4. Windows may show a SmartScreen warning because this pilot is unsigned.

Automatic in-app installation remains disabled until properly signed releases
are available.

