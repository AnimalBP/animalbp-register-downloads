# AnimalBP Register 1.4.5

[Latest release](https://github.com/AnimalBP/animalbp-register-downloads/releases/latest)
· [1.4.5 downloads and checksums](https://github.com/AnimalBP/animalbp-register-downloads/releases/tag/v1.4.5)

## Workflow improvements

- **Windows Store updates:** Check for updates from Settings or Help. The Store
  edition discovers updates through Microsoft, downloads them and waits for your
  explicit installation action. Save unfinished forms before installing; Windows
  may close the app. Open Microsoft Store remains available if a check fails.
- **Audit history:** Usage is the default view for material, aliquot, cryovial,
  project, document and physical storage actions. System log contains sign-ins,
  password resets, credential changes and administration. Existing records and
  visibility permissions are retained. CSV export includes both views and
  clearly states its 500-event limit.
- **Project cryovials:** Use selected vials requires at least one selected vial.
  Cancel sits beside that button, and the corner X closes the picker. Dismissing
  an unconfirmed selection restores No cryovial used and explains the change.
  Canceling edits preserves an already accepted selection.
- **Visible messages:** Errors and confirmations remain above open forms and
  nested dialogs. Errors stay visible for ten seconds and can be dismissed.
- **Demo and support:** The deployed 1.4.5 demo uses the same bundle and version
  as the 1.4.5 browser app. Feedback and support include application and
  interface versions, platform, environment and demo status. Demo feedback opens an email draft for
  review and sending; opening the draft does not send it.
- **Consistent downloads:** The website takes release labels,
  installation guidance and the app download catalog from one version source.
  Public content verification compares their exact released bytes, including
  the website catalog.

The receiving-note chooser remains inside Receive goods, before Comments,
matching the browser form. No database migration is required for this update.
The matching backend was deployed before the new web interface, so Usage
filtering applies before the server's result limit.

## Versions and distribution

Mac, direct Windows installers and the deployed web/demo interface use **1.4.5**. The
corresponding Microsoft Store package uses **1.4.5.0**.

**Release status, 19 September 2026 UTC:** GitHub 1.4.5 and Microsoft Store
1.4.5.0 are published. The Store package and listing match this release, and all
nine public GitHub assets passed download and checksum verification. The backend
and browser/demo are deployed as 1.4.5. Backend readiness, existing business data
and attachments were verified; no schema migration or credential rotation was
performed. The web/demo application content matches the release-pinned
manifest across 13 assets and 20 runtime URLs. Observed Cloudflare additions
were checked separately against reviewed script bytes and integrity values.

The website's 1.4.5 deployment and catalog are verified. Existing Cloudflare
Access protection remains in place. The authenticated website was checked for
the Mac 1.4.5 installer, manual installation guidance and actual Microsoft Store
destination.

An installed Windows test device is currently unavailable. The isolated direct
Windows installer upgrade passed, but actual native Microsoft Store update
check, download and installation remain unverified on an installed device.
These limits are separate from the published package and listing.

Mac distribution remains manual, ad-hoc signed and not Apple-notarized, with
automatic Mac updates disabled. Store packages use Microsoft's update service
and never the EXE updater. Direct Windows installations retain the separate
EXE updater with matching `.exe`, `.blockmap` and `latest.yml` assets.

Built from reviewed source commit `5b782350a38208d2c2629f621ffcce5c385e0838`.
Use the `SHA256SUMS.txt` attached to the [1.4.5 release](https://github.com/AnimalBP/animalbp-register-downloads/releases/tag/v1.4.5)
to verify files. `release-content.json` pins the corresponding production web
build and shared app/website catalog. Earlier notes and assets remain in
[release history](https://github.com/AnimalBP/animalbp-register-downloads/releases).
