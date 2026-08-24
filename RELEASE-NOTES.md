# AnimalBP Register 1.3.1-beta.22

This prerelease adds a fee-free, no-admin Windows installation and update path.

- Adds a one-click Windows installer fixed to the signed-in user's Local AppData
  profile, with no machine-wide option or elevation helper.
- Adds opt-in Windows update downloads from complete official GitHub releases.
- Verifies each in-app Windows download against the SHA-512 value in `beta.yml`
  before offering restart and installation.
- Rejects update manifests whose version does not exactly match the selected
  official release, and explicitly prevents downgrade installation.
- Retains the Windows ZIP for the one-time transition from beta.21 and earlier.
- Keeps macOS pilot updates as manual DMG downloads until Apple Developer ID
  signing and notarisation are available.
- Retains the beta.21 desktop window-visibility correction.

The macOS build is ad-hoc signed for package integrity, not signed with an Apple
Developer ID and not Apple-notarised. Windows is not Authenticode-signed.
The Windows updater provides checksum integrity, not authenticated publisher
identity. Read the installation warning in the repository README and verify the
SHA-256 values before opening the first package.
