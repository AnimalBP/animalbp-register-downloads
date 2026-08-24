# Security

Do not post customer data, account credentials, device tokens, database files,
private keys, or other sensitive information in a public report.

For a suspected security issue, contact AnimalBP privately through the support
channel provided with your pilot invitation. Include the application version,
operating system, and a concise reproduction that contains no customer records.

The SHA-256 values attached to each release allow users to detect a corrupted
or substituted first download. The beta.22 Windows updater additionally checks
the downloaded installer against the SHA-512 value in `beta.yml`. Because the
manifest and installer are both unsigned release assets, this is an integrity
check and not authenticated publisher identity. The beta.22 macOS ad-hoc signature checks internal
bundle consistency, but it does not establish an Apple Developer identity or
notarisation. Windows is not Authenticode-signed. This pilot must not be treated
as a trusted signed or notarised production application.
