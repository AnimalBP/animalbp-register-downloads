# AnimalBP Register 1.3.1-beta.18

This prerelease corrects the macOS packaging defect in beta.17 that caused
Gatekeeper to report the downloaded application as damaged.

- Applies a complete ad-hoc signature to the macOS application and every nested
  Electron component.
- Verifies the app from both the mounted DMG and extracted ZIP with strict,
  deep code-signature checks before publication.
- Retains the beta.17 desktop security model, remembered-device rotation,
  encrypted view-only snapshot, and server-side device revocation.
- Publishes matching macOS Apple silicon and Windows 64-bit beta.18 packages.

The macOS build is ad-hoc signed for package integrity, not signed with an Apple
Developer ID and not Apple-notarised. Windows is not Authenticode-signed.
Automatic in-app installation remains disabled. Read the installation warning
in the repository README and verify the SHA-256 values before opening a package.
