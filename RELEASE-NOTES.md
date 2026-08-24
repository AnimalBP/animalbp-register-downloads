# AnimalBP Register 1.3.1-beta.21

This prerelease fixes desktop startup cases where AnimalBP Register was running
but its main window did not appear.

- Registers the Electron window-visibility handler before loading the desktop
  interface so the initial show event cannot be missed.
- Explicitly reveals the main window after loading as a safe fallback.
- Restores, shows, and focuses an existing hidden or minimized window when the
  application is opened again.
- Adds regression tests for initial loading, early show events, minimized
  windows, and destroyed-window handling.
- Publishes matching macOS Apple silicon and Windows 64-bit beta.21 packages.

The macOS build is ad-hoc signed for package integrity, not signed with an Apple
Developer ID and not Apple-notarised. Windows is not Authenticode-signed.
Automatic in-app installation remains disabled for this unsigned pilot. Read
the installation warning in the repository README and verify the SHA-256 values
before opening a package.
