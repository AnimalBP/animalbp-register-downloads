"""Offline fixtures retain release-manifest trust independently of served files."""

import base64
import copy
import hashlib
import json
import unittest
from unittest.mock import patch

import verify_web_demo as guard
from verify_web_demo import APP_CATALOG_ASSET, DEMO, WEB, WEBSITE_CATALOG, WebsiteAccessPending, WebAlignmentPending, WebCheckError, verify_index, verify_web_demo


# Synthetic request parameters only; no live challenge tokens are retained.
PRECURSOR = (b"<script>window.__CF$cv$params={r:'0123456789abcdef',t:'MTcwMDAwMDAwMA==',"
             b"u:'0123456789abcdef0123456789abcdef',ut:'" + b"a" * 43
             + b"-1700000000-1.2.1.1-" + b"b" * 107
             + b"',i:60};(function(){if(!document.body)return;var s=document.createElement('script');"
             b"s.src='/cdn-cgi/challenge-platform/scripts/precursor/main.js';"
             b"document.head.appendChild(s);})();</script>")


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
        html = ('<!doctype html><html><body><script src="./config.js"></script><link rel="stylesheet" href="./styles.css?v=1.4.5">'
                '<script type="module" src="./' + self.app_asset + '?ui=shared"></script></body>\n</html>\n').encode()
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
        self.assertEqual(result["html_readback"]["web"]["normalization"], "none")

    def add_precursor(self):
        for page in [WEB, DEMO]:
            script = PRECURSOR if page == WEB else PRECURSOR.replace(b"0123456789abcdef'", b"fedcba9876543210'")
            self.responses[page] = self.responses[page].replace(b"</body>", script + b"</body>")

    def test_exact_edge_bootstrap_retains_original_release_anchor_and_reports_raw_hashes(self):
        self.add_precursor()
        result = self.verify()
        for name, page in [("web", WEB), ("demo", DEMO)]:
            report = result["html_readback"][name]
            self.assertEqual(report["raw_sha256"], digest(self.responses[page]))
            self.assertNotEqual(report["raw_sha256"], report["normalized_sha256"])
            self.assertEqual(report["normalized_sha256"], self.manifest["web_index_sha256"])
            self.assertEqual(report["removed_bootstrap_count"], 1)
            self.assertEqual(report["removed_bytes"], len(PRECURSOR))
            self.assertEqual(report["normalization"], "cloudflare-precursor-bootstrap-v1")
        self.assertNotEqual(result["html_readback"]["web"]["raw_sha256"], result["html_readback"]["demo"]["raw_sha256"])
        self.assertEqual(result["runtime_assets_verified"], 5)
        self.assertEqual(result["runtime_urls_verified"], 8)

    def test_edge_normalization_does_not_relax_asset_or_actual_query_checks(self):
        self.add_precursor()
        for url in [WEB + "helper.js", WEB + "helper.js?ui=shared"]:
            with self.subTest(url=url):
                old = self.responses[url]
                self.responses[url] = b"unreviewed executable code"
                with self.assertRaisesRegex(WebCheckError, "differs.*content"):
                    self.verify()
                self.responses[url] = old

    def add_analytics(self):
        self.add_precursor()
        for page in [WEB, DEMO]:
            self.responses[page] = self.responses[page].replace(b"</body>\n</html>\n", guard._ANALYTICS_TAIL)

    def test_exact_reviewed_analytics_and_tail_restore_original_index(self):
        self.add_analytics()
        for page in [WEB, DEMO]:
            result = verify_index(self.responses[page], self.manifest["web_index_sha256"])
            self.assertEqual(result["removed_analytics_count"], 1)
            self.assertTrue(result["exact_analytics_tail_reconstructed"])
            self.assertEqual(result["normalization"], "cloudflare-precursor-and-analytics-v1")
            self.assertEqual(result["normalized_sha256"], self.manifest["web_index_sha256"])

    def test_second_observed_order_accepts_only_exact_analytics_newline_before_precursor(self):
        original = self.responses[WEB]
        served = original.replace(b"</body>", guard._ANALYTICS + b"\n" + PRECURSOR + b"</body>")
        result = verify_index(served, digest(original))
        self.assertEqual(result["edge_script_order"], "analytics-precursor")
        for gap in [b"", b"\n\n", b" ", b"<script>alert(1)</script>"]:
            with self.subTest(gap=gap):
                with self.assertRaises(WebCheckError):
                    verify_index(original.replace(b"</body>", guard._ANALYTICS + gap + PRECURSOR + b"</body>"), digest(original))

    def test_analytics_integrity_is_fetched_and_checked_separately_from_app_assets(self):
        self.add_analytics()
        body = b"synthetic analytics test bytes"
        self.responses[guard.ANALYTICS_URL] = body
        # Offline bytes have their own SRI; production pins remain literal.
        sri = "sha512-" + base64.b64encode(hashlib.sha512(body).digest()).decode()
        with patch.object(guard, "ANALYTICS_SRI", sri):
            result = self.verify()
        self.assertEqual(result["edge_analytics"]["status"], "integrity_verified")
        self.assertFalse(result["edge_analytics"]["account_activation_verified"])
        self.assertEqual(result["runtime_assets_verified"], 5)
        self.assertEqual(result["runtime_urls_verified"], 8)
        self.assertIn(guard.ANALYTICS_URL, self.requests)
        with self.assertRaisesRegex(WebCheckError, "reviewed SRI"):
            self.verify()

    def test_analytics_recognition_cannot_authorize_changed_runtime_query(self):
        self.add_analytics()
        body = b"synthetic analytics test bytes"
        self.responses[guard.ANALYTICS_URL] = body
        self.responses[WEB + "helper.js?ui=shared"] = b"changed runtime"
        sri = "sha512-" + base64.b64encode(hashlib.sha512(body).digest()).decode()
        with patch.object(guard, "ANALYTICS_SRI", sri):
            with self.assertRaisesRegex(WebCheckError, "Actual browser query URL differs"):
                self.verify()

    def test_analytics_allowance_rejects_unknown_script_token_sri_code_and_position(self):
        original = self.responses[WEB]
        self.add_analytics()
        served = self.responses[WEB]
        changes = [
            (b"0d712fc37bc2466db5fdc49650594205", b"0" * 32),
            (b"beacon.min.js/v31", b"other.min.js/v31"),
            (b"static.cloudflareinsights.com", b"evil.invalid"),
            (b"sha512-iIg7", b"sha512-AAAA"),
            (b'"spa":2', b'"spa":3'), (b'"r":1', b'"r":2'),
            (b'crossorigin="anonymous"', b'onload="alert(1)"'),
            (b"</body>\n</html>\n", b"</body>\n</html>\n\n"),
            (guard._ANALYTICS, guard._ANALYTICS * 2),
        ]
        for before, after in changes:
            with self.subTest(before=before):
                with self.assertRaises(WebCheckError):
                    verify_index(served.replace(before, after), digest(original))
        for changed in [served + b"<!-- extra -->", guard._ANALYTICS + served,
                        served.replace(PRECURSOR, b""),
                        served.replace(PRECURSOR, PRECURSOR + b"<script>alert(1)</script>")]:
            with self.assertRaises(WebCheckError):
                verify_index(changed, digest(original))

    def test_catalog_access_boundary_retains_verified_app_evidence_without_full_parity(self):
        original_fetch = self.fetch
        def protected_fetch(url):
            if url == WEBSITE_CATALOG:
                raise WebsiteAccessPending("Catalog requires authentication")
            return original_fetch(url)
        with self.assertRaises(WebsiteAccessPending) as caught:
            verify_web_demo(self.repo, self.release, protected_fetch)
        result = caught.exception.web_demo_result
        self.assertEqual(result["status"], "pending")
        self.assertFalse(result["parity_verified"])
        self.assertTrue(result["web_content_verified"])
        self.assertEqual(result["runtime_urls_verified"], 8)
        self.assertEqual(result["website_catalog"]["status"], "access_pending")

    def test_unknown_catalog_html_is_failure_not_an_access_exception(self):
        self.responses[WEBSITE_CATALOG] = b"<html>unrecognized page</html>"
        with self.assertRaises(WebCheckError) as caught:
            self.verify()
        result = caught.exception.web_demo_result
        self.assertEqual(result["status"], "failed")
        self.assertFalse(result["parity_verified"])
        self.assertTrue(result["web_content_verified"])
        self.assertEqual(result["website_catalog"]["status"], "failed")

    def test_unknown_injection_or_changed_application_html_still_fails(self):
        original = self.responses[WEB]
        for extra in [b"<script>alert(1)</script>", b"<img src=x onerror=alert(1)>", b"<!-- unknown addition -->"]:
            with self.subTest(extra=extra):
                served = original.replace(b"</body>", extra + PRECURSOR + b"</body>")
                with self.assertRaisesRegex(WebCheckError, "after exact edge normalization"):
                    verify_index(served, digest(original))
        changed = original.replace(b"<!doctype html>", b"<!doctype html>changed")
        with self.assertRaisesRegex(WebCheckError, "after exact edge normalization"):
            verify_index(changed.replace(b"</body>", PRECURSOR + b"</body>"), digest(original))

    def test_bootstrap_code_position_count_and_typed_parameters_are_fail_closed(self):
        original = self.responses[WEB]
        replacements = [
            (b"precursor/main.js", b"other/main.js"),
            (b"s.src='/cdn-cgi/", b"s.src='https://evil.invalid/cdn-cgi/"),
            (b"document.head.appendChild(s);", b"document.head.appendChild(s);alert(1);"),
            (b"<script>", b"<script nonce='anything'>"),
            (b"r:'0123456789abcdef'", b"r:'0123456789abcdef0'"),
            (b"u:'0123456789abcdef0123456789abcdef'", b"u:'wrong'"),
            (b"MTcwMDAwMDAwMA==", b"MTcwMDAwMDAwMQ=="),
            (b"-1700000000-", b"-17000000000-"),
            (b"-1.2.1.1-", b"-1.2.1.2-"),
            (b"a" * 43, b"a" * 44),
            (b"b" * 107, b"b" * 108),
            (b"b" * 107, b"b" * 106 + b"'"),
            (b"i:60", b"i:61"),
        ]
        for before, after in replacements:
            with self.subTest(before=before):
                with self.assertRaises(WebCheckError):
                    verify_index(original.replace(b"</body>", PRECURSOR.replace(before, after) + b"</body>"), digest(original))
        for served in [
            original.replace(b"</body>", PRECURSOR * 2 + b"</body>"),
            PRECURSOR + original,
            original + PRECURSOR,
            original.replace(b"</body>", PRECURSOR + b"\n</body>"),
            original.replace(b"</body>", PRECURSOR + b"</body>") + b"<script>alert(1)</script>",
            b"x" * (256 * 1024) + PRECURSOR + b"</body>\n</html>\n",
        ]:
            with self.subTest(served_tail=served[-60:]):
                with self.assertRaises(WebCheckError):
                    verify_index(served, digest(original))

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
        with self.assertRaisesRegex(WebCheckError, "Web/demo HTML differs"):
            self.verify()

    def test_beta_static_demo_and_foreign_api_configs_are_not_public_parity(self):
        for field, value in [("environment", "beta"), ("demoMode", True), ("apiBaseUrl", "https://api-beta.animalbp.com")]:
            with self.subTest(field=field):
                self.responses[WEB + "config.js"] = b"globalThis.ABP_CONFIG = Object.freeze(" + encode(self.config | {field: value}) + b");\n"
                with self.assertRaisesRegex(WebCheckError, "session-protected production"):
                    self.verify()


if __name__ == "__main__":
    unittest.main()
