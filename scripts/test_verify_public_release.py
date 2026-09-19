"""Offline fixtures exercise publication failures seen in real releases."""

import copy
import hashlib
import io
import unittest
from unittest.mock import patch

from verify_public_release import ReleaseError, expected_assets, fetch, validate_release
from verify_web_demo import ANALYTICS_URL, WEBSITE_CATALOG, WebsiteAccessPending


class PublicReleaseTests(unittest.TestCase):
    def test_pinned_analytics_fetch_refuses_any_redirect_target_change(self):
        class Response(io.BytesIO):
            def __init__(self, final):
                super().__init__(b"synthetic bytes")
                self.final = final
            def geturl(self):
                return self.final
        for target in [ANALYTICS_URL.replace("static.cloudflareinsights.com", "foreign.invalid"),
                       ANALYTICS_URL + "?changed=1", ANALYTICS_URL + "/changed"]:
            with self.subTest(target=target):
                with patch("verify_public_release.urlopen", return_value=Response(target)):
                    with self.assertRaisesRegex(ReleaseError, "must not redirect"):
                        fetch(ANALYTICS_URL)
        with patch("verify_public_release.urlopen", return_value=Response(ANALYTICS_URL)):
            self.assertEqual(fetch(ANALYTICS_URL), b"synthetic bytes")

    def test_only_exact_known_catalog_access_redirect_is_reported_as_pending(self):
        class Response(io.BytesIO):
            def __init__(self, final):
                super().__init__(b"<html>login</html>")
                self.final = final
            def geturl(self):
                return self.final
        access = "https://animalbp.cloudflareaccess.com/cdn-cgi/access/login/animalbp.com?synthetic=not-retained"
        with patch("verify_public_release.urlopen", return_value=Response(access)):
            with self.assertRaises(WebsiteAccessPending) as caught:
                fetch(WEBSITE_CATALOG)
        self.assertNotIn("synthetic", str(caught.exception))
        for original, final in [
            ("https://app.animalbp.com/", access),
            (WEBSITE_CATALOG, access.replace("animalbp.cloudflareaccess.com", "foreign.invalid")),
            (WEBSITE_CATALOG, access.replace("/login/animalbp.com", "/unknown")),
        ]:
            with self.subTest(original=original, final=final):
                with patch("verify_public_release.urlopen", return_value=Response(final)):
                    self.assertEqual(fetch(original), b"<html>login</html>")

    def setUp(self):
        self.repo = "AnimalBP/animalbp-register-downloads"
        base = f"https://github.com/{self.repo}/releases"
        self.updater = ("version: 1.4.4\nfiles:\n"
                        "  - url: AnimalBP-Register-1.4.4-win-x64.exe\n"
                        "path: AnimalBP-Register-1.4.4-win-x64.exe\n").encode()
        self.contents = {name: name.encode() for name in expected_assets("1.4.4")}
        self.contents["latest.yml"] = self.updater
        self.checksums = "".join(f"{hashlib.sha256(data).hexdigest()}  {name}\n"
                                 for name, data in sorted(self.contents.items())).encode()
        self.release = {"tag_name": "v1.4.4", "draft": False, "prerelease": False,
                        "assets": [{"name": name, "digest": f"sha256:{hashlib.sha256(data).hexdigest()}"}
                                   for name, data in {**self.contents, "SHA256SUMS.txt": self.checksums}.items()]}
        links = f"{base}/latest\n{base}/tag/v1.4.4\n"
        self.documents = {
            "README.md": ("## Current release: 1.4.4\n" + links +
                          f"{base}/download/v1.4.4/AnimalBP-Register-1.4.4-mac-arm64.dmg\n" +
                          f"{base}/download/v1.4.4/SHA256SUMS.txt\n").encode(),
            "RELEASE-NOTES.md": ("# AnimalBP Register 1.4.4\n" + links).encode(),
            "SHA256SUMS.txt": self.checksums,
        }
        self.release["assets"].append({
            "name": "RELEASE-NOTES.md",
            "digest": "sha256:" + hashlib.sha256(self.documents["RELEASE-NOTES.md"]).hexdigest(),
        })

    def validate(self):
        return validate_release(self.repo, self.release, self.documents, self.checksums, self.updater)

    def test_complete_matching_release_passes(self):
        self.assertEqual(self.validate(), "1.4.4")

    def test_web_manifest_checksum_is_required_starting_at_145(self):
        self.assertNotIn("release-content.json", expected_assets("1.4.4"))
        for version in ("1.4.5", "1.5.0", "2.0.0"):
            with self.subTest(version=version):
                self.assertIn("release-content.json", expected_assets(version))
                self.assertEqual(len(expected_assets(version)), 7)

    def test_145_web_manifest_is_bound_by_root_checksums_release_checksums_and_api_digest(self):
        self.updater = self.updater.replace(b"1.4.4", b"1.4.5")
        self.contents = {name.replace("1.4.4", "1.4.5"): data.replace(b"1.4.4", b"1.4.5") for name, data in self.contents.items()}
        self.contents["release-content.json"] = b'{"reviewed":"web-content-fixture"}\n'
        self.checksums = "".join(f"{hashlib.sha256(data).hexdigest()}  {name}\n"
                                 for name, data in sorted(self.contents.items())).encode()
        self.documents = {name: data.replace(b"1.4.4", b"1.4.5") for name, data in self.documents.items()}
        self.documents["SHA256SUMS.txt"] = self.checksums
        self.release.update({"tag_name": "v1.4.5", "assets": [
            {"name": name, "digest": "sha256:" + hashlib.sha256(data).hexdigest()}
            for name, data in {**self.contents, "SHA256SUMS.txt": self.checksums,
                               "RELEASE-NOTES.md": self.documents["RELEASE-NOTES.md"]}.items()
        ]})
        self.assertEqual(self.validate(), "1.4.5")
        self.release["assets"] = [asset | ({"digest": "sha256:" + "f" * 64} if asset["name"] == "release-content.json" else {})
                                   for asset in self.release["assets"]]
        with self.assertRaisesRegex(ReleaseError, "GitHub asset digest differs.*release-content.json"):
            self.validate()

    def test_stale_root_listing_is_rejected(self):
        for name in ("README.md", "RELEASE-NOTES.md"):
            with self.subTest(name=name):
                before = self.documents[name]
                self.documents[name] = before.replace(b"1.4.4", b"1.4.1")
                with self.assertRaisesRegex(ReleaseError, "does not identify version"):
                    self.validate()
                self.documents[name] = before

    def test_stale_download_link_is_rejected_even_with_current_heading(self):
        self.documents["README.md"] += f"https://github.com/{self.repo}/releases/download/v1.4.1/old.dmg".encode()
        with self.assertRaisesRegex(ReleaseError, "stale download link"):
            self.validate()

    def test_stale_root_checksums_are_rejected(self):
        self.documents["SHA256SUMS.txt"] = b"old release checksums\n"
        with self.assertRaisesRegex(ReleaseError, "Root SHA256SUMS.txt differs"):
            self.validate()

    def test_missing_updater_assets_are_rejected(self):
        for name in ("latest.yml", "AnimalBP-Register-1.4.4-win-x64.exe.blockmap"):
            with self.subTest(name=name):
                release = copy.deepcopy(self.release)
                self.release["assets"] = [asset for asset in self.release["assets"] if asset["name"] != name]
                with self.assertRaisesRegex(ReleaseError, "Missing release assets"):
                    self.validate()
                self.release = release

    def test_changed_public_asset_digest_is_rejected(self):
        self.release["assets"][0]["digest"] = "sha256:" + "0" * 64
        with self.assertRaisesRegex(ReleaseError, "GitHub asset digest differs"):
            self.validate()

    def test_replaced_updater_content_is_rejected(self):
        self.updater = self.updater.replace(b"1.4.4", b"1.4.1")
        with self.assertRaisesRegex(ReleaseError, "Downloaded latest.yml differs"):
            self.validate()

    def test_internally_hashed_but_stale_updater_is_rejected(self):
        old = hashlib.sha256(self.updater).hexdigest()
        self.updater = self.updater.replace(b"version: 1.4.4", b"version: 1.4.1")
        new = hashlib.sha256(self.updater).hexdigest()
        self.checksums = self.checksums.replace(old.encode(), new.encode())
        self.documents["SHA256SUMS.txt"] = self.checksums
        for asset in self.release["assets"]:
            if asset["name"] == "latest.yml":
                asset["digest"] = "sha256:" + new
            if asset["name"] == "SHA256SUMS.txt":
                asset["digest"] = "sha256:" + hashlib.sha256(self.checksums).hexdigest()
        with self.assertRaisesRegex(ReleaseError, "latest.yml has a stale version"):
            self.validate()

    def test_automatic_mac_manifest_is_rejected(self):
        self.release["assets"].append({"name": "latest-mac.yml"})
        with self.assertRaisesRegex(ReleaseError, "Manual Mac distribution"):
            self.validate()

    def test_stale_release_notes_asset_is_rejected(self):
        for asset in self.release["assets"]:
            if asset["name"] == "RELEASE-NOTES.md":
                asset["digest"] = "sha256:" + hashlib.sha256(b"Old release notes").hexdigest()
        with self.assertRaisesRegex(ReleaseError, "RELEASE-NOTES.md asset differs"):
            self.validate()


if __name__ == "__main__":
    unittest.main()
