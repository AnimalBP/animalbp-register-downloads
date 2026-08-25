# AnimalBP Register 1.3.1-beta.26

This prerelease adds faster setup for similar laboratory storage locations.

- Adds a Duplicate action to Laboratory Setup for copying a fridge, freezer,
  incubator, archive, cryofreezer, or custom storage location.
- Copies room, type, custom location, and workflow visibility into a new
  editable form, with the next available unit number selected automatically.
- Keeps the duplicate as a separate storage identity and does not copy racks,
  samples, materials, or stored records.
- Retains secure user invitations, forced first-sign-in password replacement,
  view-only downloads, web-session controls, and optional unit numbers from
  beta.24 and beta.25.
- Retains the current-user Windows installer and verified in-app Windows update
  manifest introduced in beta.22.

The macOS build is ad-hoc signed for package integrity, not signed with an Apple
Developer ID and not Apple-notarised. Windows is not Authenticode-signed.
The Windows updater provides checksum integrity, not authenticated publisher
identity. Read the installation warning in the repository README and verify the
SHA-256 values before opening the first package.
