# AnimalBP Register 1.4.4

[Latest release](https://github.com/AnimalBP/animalbp-register-downloads/releases/latest)
· [1.4.4 downloads and checksums](https://github.com/AnimalBP/animalbp-register-downloads/releases/tag/v1.4.4)

## Matching document upload form

- The desktop **Receive goods** form now shows **Receiving note (optional)**
  before **Comments**, in the same place as the online form.
- **Choose File** selects a PDF or supported image before registration. The
  selected file is attached to package 1 after the receipt is registered.
- Replaces the desktop checkbox and the separate bottom **Upload attachment**
  action. Cancelling the file picker keeps an existing choice; closing the
  receipt form discards it.
- If the optional attachment upload fails, the receipt stays registered. Use
  **Upload document** on package 1 to retry the attachment.
- The desktop uses the protected native file picker. Local file paths and
  transfer credentials remain outside the app view.

Existing workspaces and recorded data remain available. This correction does
not migrate the database. Historical information that was not recorded is not
inferred or invented.

## Versions and updates

Mac and direct Windows installers use **1.4.4**; the matching Microsoft Store
package uses **1.4.4.0**. Microsoft Store distribution requires Microsoft's
certification and rollout. See this release's GitHub page for verified channel
status; GitHub publication alone does not make a Store update available.

Mac distribution remains manual, ad-hoc signed, and not Apple-notarized, with
automatic Mac updates disabled. Store-installed Windows apps update through
Microsoft Store. Direct Windows installations use the in-app updater and the
matching `.exe`, `.blockmap`, and `latest.yml` release assets.

Built from source commit `d2bcdb509870db301b44f45b71790f28220712ea`.
Use the `SHA256SUMS.txt` attached to the [1.4.4 release](https://github.com/AnimalBP/animalbp-register-downloads/releases/tag/v1.4.4)
to verify downloaded files. Earlier release notes and assets remain available
in [release history](https://github.com/AnimalBP/animalbp-register-downloads/releases).
