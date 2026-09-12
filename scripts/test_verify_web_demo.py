"""Offline fixtures retain release-manifest trust independently of served files."""

import copy
import hashlib
import json
import unittest

from verify_web_demo import APP_CATALOG_ASSET, DEMO, WEB, WEBSITE_CATALOG, WebAlignmentPending, WebCheckError, verify_web_demo


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encode(value):
    return json.dumps(value, separators=(",", ":")).encode()


class WebDemoTests(unittest.TestCase):
    def setUp(self):
        self.repo = "AnimalBP/animalbp-register-downloads"
        self.version = "1.4.5"
        app = b"import {value} from './helper.js?ui=shared';\n"
        self.app_asset = f"app-{self.version}-{digest(app)[:12]}.js"
        release_base = "https://github.com/AnimalBP/animalbp-register-downloads/releases"
        self.catalog = {
            "schema": 1,
            "platforms": [
                {"id": "macos", "title": "Mac · " + self.version,
                 "url": f"{release_base}/download/v{self.version}/AnimalBP-Register-{self.version}-mac-arm64.dmg"},
                {"id": "windows", "title": "Windows", "url": "https://apps.microsoft.com/detail/9NP93BBMMZ4S?mode=direct"},
            ],
            "notes": ["Windows offers the version currently approved by Microsoft.",
                      f"Open AnimalBP-Register-{self.version}-mac-arm64.dmg.", "Manual Mac installation."],
            "links": [{"url": "https://support.apple.com/en-gb/102445", "label": "Apple guidance"},
                      {"url": f"{release_base}/tag/v{self.version}", "label": "Release notes"}],
        }
        self.catalog_bytes = encode(self.catalog)
        files = {"app.js": app, self.app_asset: app, "helper.js": b"export const value = 1;\n", "styles.css": b"body { color: green; }",
                 APP_CATALOG_ASSET: self.catalog_bytes}
        self.config = {"version": self.version, "environment": "production", "demoMode": False, "apiBaseUrl": "https://api.animalbp.com"}
        self.config_bytes = b"globalThis.ABP_CONFIG = Object.freeze(" + encode(self.config) + b");\n"
        html = ('<script src="./config.js"></script><link rel="stylesheet" href="./styles.css?v=1.4.5">'
                '<script type="module" src="./' + self.app_asset + '?ui=shared"></script>').encode()
        assets = {name: digest(body) for name, body in sorted(files.items())}
        self.manifest = {
            "schema_version": 1, "scope": "public-web-and-demo", "version": self.version, "environment": "production",
            "demo_entry_path": "/?demo=1", "demo_uses_shared_web_bundle": True, "app_asset": self.app_asset,
            "assets": assets, "shared_content_sha256": digest(encode(assets)),
            "web_config_sha256": digest(self.config_bytes), "web_index_sha256": digest(html),
        }
        self.raw_manifest = encode(self.manifest)
        self.release_url = f"https://github.com/{self.repo}/releases/download/v{self.version}/release-content.json"
        self.release = {"tag_name": "v" + self.version, "draft": False, "prerelease": False,
                        "assets": [{"name": "release-content.json", "id": 12345, "state": "uploaded",
                                    "size": len(self.raw_manifest), "digest": "sha256:" + digest(self.raw_manifest)}]}
        self.responses = {self.release_url: self.raw_manifest, WEB: html, DEMO: html,
                          WEB + "config.js": self.config_bytes, WEB + "release-content.json": self.raw_manifest,
                          WEBSITE_CATALOG: self.catalog_bytes}
        self.responses.update({WEB + name: body for name, body in files.items()})
        self.responses.update({WEB + self.app_asset + "?ui=shared": app,
                               WEB + "styles.css?v=1.4.5": files["styles.css"],
                               WEB + "helper.js?ui=shared": files["helper.js"]})
        self.requests = []

    def fetch(self, url):
        self.requests.append(url)
        return self.responses[url]

    def verify(self):
        return verify_web_demo(self.repo, self.release, self.fetch)

    def test_legacy_release_missing_the_manifest_is_explicitly_unverified_without_web_requests(self):
        self.release.update({"tag_name": "v1.4.4", "assets": []})
        result = self.verify()
        self.assertEqual(result["status"], "legacy_not_configured")
        self.assertFalse(result["parity_verified"])
        self.assertEqual(self.requests, [])

    def test_a_new_release_cannot_silently_skip_a_missing_manifest(self):
        self.release["assets"] = []
        with self.assertRaisesRegex(WebCheckError, "require exactly one"):
            self.verify()

    def test_published_content_and_actual_browser_query_urls_match_the_release_anchor(self):
        result = self.verify()
        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["release_manifest_asset_id"], 12345)
        self.assertEqual(result["release_manifest_sha256"], digest(self.raw_manifest))
        self.assertEqual(result["runtime_assets_verified"], 5)
        self.assertEqual(result["runtime_urls_verified"], 8)
        self.assertEqual(result["website_catalog"], {"status": "passed", "version": self.version,
                         "url": WEBSITE_CATALOG, "sha256": digest(self.catalog_bytes)})
        self.assertIn(WEBSITE_CATALOG, self.requests)
        self.assertFalse(any("/auth/" in url or "#demo=" in url for url in self.requests))

    def test_release_download_must_match_its_api_digest_and_size(self):
        for field, value in [("digest", "sha256:" + "f" * 64), ("size", 0), ("state", "new"), ("id", True)]:
            with self.subTest(field=field):
                original = copy.deepcopy(self.release)
                self.release["assets"][0][field] = value
                with self.assertRaises(WebCheckError):
                    self.verify()
                self.release = original

    def test_a_served_manifest_cannot_authorize_different_web_bytes(self):
        forged = copy.deepcopy(self.manifest)
        forged["assets"]["helper.js"] = digest(b"changed helper")
        self.responses[WEB + "release-content.json"] = encode(forged)
        self.responses[WEB + "helper.js"] = b"changed helper"
        with self.assertRaisesRegex(WebCheckError, "cannot authorize changed web bytes"):
            self.verify()

    def test_changed_runtime_with_unchanged_labels_and_manifest_is_rejected(self):
        self.responses[WEB + "helper.js"] = b"old helper with the same 1.4.5 label"
        with self.assertRaisesRegex(WebCheckError, "Public runtime asset differs"):
            self.verify()

    def test_the_actual_import_query_variant_is_verified(self):
        self.responses[WEB + "helper.js?ui=shared"] = b"old CDN query variant"
        with self.assertRaisesRegex(WebCheckError, "Actual browser query URL differs"):
            self.verify()

    def test_an_early_github_publication_is_pending_alignment_not_parity_pass(self):
        self.config["version"] = "1.4.4"
        self.responses[WEB + "config.js"] = b"globalThis.ABP_CONFIG = Object.freeze(" + encode(self.config) + b");\n"
        with self.assertRaisesRegex(WebAlignmentPending, "pending deployment alignment"):
            self.verify()

    def test_older_consistent_website_catalog_is_pending_after_github_publication(self):
        self.responses[WEBSITE_CATALOG] = self.catalog_bytes.replace(b"1.4.5", b"1.4.4")
        with self.assertRaisesRegex(WebAlignmentPending, "website downloads are 1.4.4.*pending alignment"):
            self.verify()

    def test_same_version_website_text_changes_are_failures_not_pending(self):
        changed = copy.deepcopy(self.catalog)
        changed["notes"][2] = "Unreviewed instructions with the same version"
        self.responses[WEBSITE_CATALOG] = encode(changed)
        with self.assertRaisesRegex(WebCheckError, "Same-version website catalog differs") as caught:
            self.verify()
        self.assertNotIsInstance(caught.exception, WebAlignmentPending)

    def test_updating_both_public_catalogs_cannot_override_the_release_pinned_hash(self):
        changed = encode(self.catalog | {"extra": "unreviewed content"})
        self.responses[WEB + APP_CATALOG_ASSET] = changed
        self.responses[WEBSITE_CATALOG] = changed
        with self.assertRaisesRegex(WebCheckError, "Public runtime asset differs.*desktop-downloads"):
            self.verify()

    def test_mixed_website_versions_are_failures_not_an_early_publication_window(self):
        changed = copy.deepcopy(self.catalog)
        changed["notes"][1] = "Open AnimalBP-Register-1.4.4-mac-arm64.dmg."
        self.responses[WEBSITE_CATALOG] = encode(changed)
        with self.assertRaisesRegex(WebCheckError, "mixed release versions") as caught:
            self.verify()
        self.assertNotIsInstance(caught.exception, WebAlignmentPending)

    def test_a_website_version_ahead_of_github_is_not_classified_as_early_github_publication(self):
        self.responses[WEBSITE_CATALOG] = self.catalog_bytes.replace(b"1.4.5", b"1.4.6")
        with self.assertRaisesRegex(WebCheckError, "ahead of the latest stable") as caught:
            self.verify()
        self.assertNotIsInstance(caught.exception, WebAlignmentPending)

    def test_manifest_cannot_omit_the_app_catalog_and_silently_skip_website_parity(self):
        del self.manifest["assets"][APP_CATALOG_ASSET]
        self.manifest["shared_content_sha256"] = digest(encode(self.manifest["assets"]))
        raw = encode(self.manifest)
        self.release["assets"][0].update({"size": len(raw), "digest": "sha256:" + digest(raw)})
        self.responses[self.release_url] = self.responses[WEB + "release-content.json"] = raw
        with self.assertRaisesRegex(WebCheckError, "must pin the shared desktop download catalog"):
            self.verify()

    def test_website_store_candidate_label_is_not_accepted_as_catalog_parity(self):
        changed = copy.deepcopy(self.catalog)
        changed["platforms"][1]["title"] = "Windows · 1.4.5"
        self.responses[WEBSITE_CATALOG] = encode(changed)
        with self.assertRaisesRegex(WebCheckError, "truthful Microsoft Store availability"):
            self.verify()

    def test_demo_cannot_load_a_different_application(self):
        self.responses[DEMO] += b"<script src='./old-demo.js'></script>"
        with self.assertRaisesRegex(WebCheckError, "same configuration and scripts"):
            self.verify()

    def test_beta_static_demo_and_foreign_api_configs_are_not_public_parity(self):
        for field, value in [("environment", "beta"), ("demoMode", True), ("apiBaseUrl", "https://api-beta.animalbp.com")]:
            with self.subTest(field=field):
                self.responses[WEB + "config.js"] = b"globalThis.ABP_CONFIG = Object.freeze(" + encode(self.config | {field: value}) + b");\n"
                with self.assertRaisesRegex(WebCheckError, "session-protected production"):
                    self.verify()


if __name__ == "__main__":
    unittest.main()
