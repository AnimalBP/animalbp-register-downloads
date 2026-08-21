# AnimalBP Register 1.3.1-beta.20

This prerelease adds a visible desktop update check for future releases.

- Adds **Check for Updates…** to the AnimalBP Register menu on macOS and the
  Help menu on Windows.
- Corrects the native macOS application-menu name to AnimalBP Register.
- Checks this official public release feed without requiring an AnimalBP or
  Cloudflare sign-in and opens unsigned pilot updates as manual downloads.
- Keeps automatic download and installation limited to configured signed
  releases.
- Publishes matching macOS Apple silicon and Windows 64-bit beta.20 packages.

The macOS build is ad-hoc signed for package integrity, not signed with an Apple
Developer ID and not Apple-notarised. Windows is not Authenticode-signed.
Automatic in-app installation remains disabled for this unsigned pilot. Read
the installation warning in the repository README and verify the SHA-256 values
before opening a package.
