# Public release checklist

Use one stable version for Mac, Windows, release information, and download
links. Windows Store adds the fourth version component: for example, **1.4.4**
corresponds to **1.4.4.0**.

## Before publication

- Verify the source version and release manifest, and build every desktop
  package from the same reviewed source commit. Record that commit and the CI
  run for each package.
- Verify the packaged app versions, platform identities, signatures, archive
  integrity, and checksums. Confirm the intended form and file-selection flow.
- Prepare the version-specific GitHub release and its complete approved asset
  set. Direct Windows updates require the matching `.exe`, `.blockmap`, and
  `latest.yml`; manual Mac distribution must not publish an automatic-update
  manifest.
- Update the public repository's `README.md`, `RELEASE-NOTES.md`, and
  `SHA256SUMS.txt` together. Their versions and download links must match the
  release, and the root checksum file must match the checksum asset attached
  to that release.
- From 1.4.5, publish `release-content.json` from the reviewed production app
  build and include its hash in both checksum files. Its shared assets must
  include `assets/desktop-downloads.json`. The existing daily/release guard
  verifies public web/demo bytes and `https://animalbp.com/downloads.json`
  against this release-pinned app catalog; the website cannot authorize its
  own changed content by serving a matching version label.
- Cloudflare may append its Precursor security bootstrap to the HTML response.
  The guard accepts only the reviewed literal bootstrap immediately before the
  final closing body, once, with bounded request fields and its fixed same-origin
  script path. It removes only that recognized addition for comparison with the
  original release-pinned HTML digest. Reports retain both raw and normalized
  hashes. Any changed bootstrap, extra HTML or script, or changed application
  asset still fails; runtime and query URL hashes remain mandatory. This checks
  application content, not the dynamically served Cloudflare security script.
  Do not disable Cloudflare protections or weaken CSP to make this check pass.
- Upload the matching Windows Store package and copy the reviewed Store
  release notes into Partner Center. Save, reload, and compare the saved notes
  with the reviewed text. Record the submission ID, package version, and actual
  certification/publication status.

## Publication and acceptance

- Publish only verified assets. Preserve earlier versioned releases as
  historical records; a corrective binary needs a new shared version.
- The owner has approved GitHub publication before Microsoft Store approval
  for this release. Clearly record each channel's status on the release page.
  This exception does not make the Store package available or complete Store
  acceptance.
- Keep the production website chooser on the previous verified release until
  the matching Store release is ready. Then promote the matching website
  change, verify its displayed version and final download links, and check the
  generated download catalog.
  A coherent older website catalog during this publication window reports
  `PENDING` (exit 2), without a parity pass. Changed same-version content, mixed
  versions or a website version ahead of GitHub fail verification. Rerun the
  existing workflow after deployment/cache propagation completes.
- After Store approval and rollout, update a computer with the earlier
  Store-installed app. Verify its package version, Store signature, retained
  workspace access, and receiving-note interaction. A successful package
  upload is not an installed-app acceptance result.
- Read the public GitHub release and root documents back after publication.
  Download the public assets to verify their checksums, check that the latest
  release route selects the intended stable release, and confirm Store notes
  and package availability. Record all outstanding items explicitly before
  calling the release complete.

Mac updates remain manual under the approved ad-hoc signing and
non-notarization policy. Store-installed Windows apps update through Microsoft
Store; direct Windows installations use the separate in-app updater.
