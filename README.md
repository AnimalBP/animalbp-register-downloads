# AnimalBP Register desktop downloads

This public repository is the official download location for AnimalBP Register
desktop pilot builds. It contains release guidance and packaged application
files only. The cloud backend, customer records, credentials, databases,
environment configuration, and signing material are not included.

## Current pilot release

Version **1.4.1** is available from the
[GitHub release page](https://github.com/AnimalBP/animalbp-register-downloads/releases).

- [Download for macOS Apple silicon](https://github.com/AnimalBP/animalbp-register-downloads/releases/download/untagged-2dc0e9491faf58ceaf1a/AnimalBP-Register-1.4.1-mac-arm64.dmg)
- [Download the Windows 64-bit per-user installer](https://apps.microsoft.com/detail/9NP93BBMMZ4S)

New Windows users should use the per-user installer. The Windows ZIP remains for
the one-time transition from beta.21 and earlier. The installer, its blockmap,
and `beta.yml` are published together so later complete Windows releases can be
downloaded from inside the app. Public macOS distribution continues to use only
the DMG. A Mac ZIP may be generated inside private CI for validation, but it is
not published as a user download.

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

1. Download the `.exe` installer and verify its SHA-256 checksum.
2. Run the installer. It installs only for the signed-in Windows user under
   Local AppData. It does not request Windows administrator access.
3. Windows may show a SmartScreen warning because this pilot is unsigned. An
   organisation may also block unsigned applications by policy.
4. In later releases, use **Check for Updates…** inside AnimalBP Register, then
   choose **Download Update** and **Restart and install**.

Beta.21 and earlier have a one-time transition because those versions only know
how to open the Windows ZIP. For the easiest transition, download and run the
beta.26 per-user installer directly from the release page. Once beta.26 is
installed, later complete Windows pilot releases can use the in-app updater.

The Windows updater verifies the downloaded installer against the SHA-512 value
in `beta.yml`. This detects corruption or a mismatch between the manifest and
installer, but it does not provide an authenticated publisher identity. Windows
remains unsigned until a code-signing certificate is added. macOS updates remain
manual until Developer ID signing and Apple notarisation are available.
