"""Offline fixtures retain release-manifest trust independently of served files."""

import copy
import hashlib
import json
import unittest

from verify_web_demo import DEMO, WEB, WebAlignmentPending, WebCheckError, verify_web_demo


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
        files = {"app.js": app, self.app_asset: app, "helper.js": b"export const value = 1;\n", "styles.css": b"body { color: green; }"}
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
                          WEB + "config.js": self.config_bytes, WEB + "release-content.json": self.raw_manifest}
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
        self.assertEqual(result["runtime_assets_verified"], 4)
        self.assertEqual(result["runtime_urls_verified"], 7)
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
