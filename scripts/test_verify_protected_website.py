"""Fail-closed policy tests; all redirects and credentials are synthetic."""

from email.message import Message
from functools import partial
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.parse import urlencode

import test_verify_web_demo as web_fixtures
from verify_web_demo import WEBSITE_CATALOG, WebCheckError, digest, verify_web_demo
from verify_protected_website import (ACCESS_LOGIN, MAX_CATALOG_BYTES, PRODUCTION_CATALOG,
                                    NoRedirect, Readback, read_without_redirect, verify_protected_website)


class ProtectedWebsiteTests(unittest.TestCase):
    def setUp(self):
        fixture = web_fixtures.WebDemoTests(); fixture.setUp()
        self.web_fixture = fixture
        self.body = fixture.catalog_bytes
        self.policy = json.loads((Path(__file__).resolve().parents[1] / "website-verification-policy.json").read_text())
        self.policy["catalog_sha256"] = digest(self.body)
        self.policy["access_login_kid"] = "a" * 64
        self.deployment = self.policy["reviewed_deployment"]["catalog_url"]
        self.login = ACCESS_LOGIN + "?" + urlencode({"kid": "a" * 64, "meta": "synthetic-meta-do-not-retain", "redirect_url": "/downloads.json"})
        self.responses = {
            WEBSITE_CATALOG: Readback(WEBSITE_CATALOG, 302, self.login, b""),
            PRODUCTION_CATALOG: Readback(PRODUCTION_CATALOG, 200, None, self.body),
            self.deployment: Readback(self.deployment, 200, None, self.body),
        }
        self.calls = []

    def probe(self, url):
        self.calls.append(url)
        return self.responses[url]

    def verify(self, *, version="1.4.5", expected=None):
        def no_general_fetch(*args):
            self.fail("Protected mode must use the explicit no-redirect anonymous reader")
        return verify_protected_website(self.body, expected or digest(self.body), version, no_general_fetch,
                                        policy=self.policy, probe=self.probe)

    def test_three_way_verification_reports_protection_not_public_custom_content(self):
        result = self.verify()
        self.assertEqual(self.calls, [WEBSITE_CATALOG, PRODUCTION_CATALOG, self.deployment])
        self.assertEqual(result["status"], "protected_site_verified")
        self.assertTrue(result["current_production_alias_catalog_verified"])
        self.assertFalse(result["public_custom_domain_verified"])
        self.assertFalse(result["access"]["redirect_followed"])
        self.assertFalse(result["access"]["query_tokens_retained"])
        serialized = json.dumps(result)
        self.assertNotIn("a" * 64, serialized)
        self.assertNotIn("synthetic-meta", serialized)
        self.assertIn("authenticated custom-domain bytes are not verified", result["scope"])

    def test_integrated_guard_keeps_web_parity_but_never_claims_public_custom_domain_parity(self):
        fixture = self.web_fixture
        verifier = partial(verify_protected_website, policy=self.policy, probe=self.probe)
        result = verify_web_demo(fixture.repo, fixture.release, fixture.fetch, website_verifier=verifier)
        self.assertEqual(result["status"], "passed_with_protected_website")
        self.assertFalse(result["parity_verified"])
        self.assertTrue(result["public_web_demo_parity_verified"])
        self.assertFalse(result["public_custom_domain_verified"])
        self.assertNotIn(WEBSITE_CATALOG, fixture.requests)

    def test_integrated_failure_retains_web_evidence_without_policy_or_parity_pass(self):
        fixture = self.web_fixture
        self.responses[PRODUCTION_CATALOG] = Readback(PRODUCTION_CATALOG, 200, None, b"unexpected bytes")
        verifier = partial(verify_protected_website, policy=self.policy, probe=self.probe)
        with self.assertRaises(WebCheckError) as caught:
            verify_web_demo(fixture.repo, fixture.release, fixture.fetch, website_verifier=verifier)
        partial_result = caught.exception.web_demo_result
        self.assertEqual(partial_result["status"], "failed")
        self.assertFalse(partial_result["parity_verified"])
        self.assertTrue(partial_result["web_content_verified"])

    def test_future_release_or_digest_needs_a_new_reviewed_policy_before_network(self):
        for options in ({"version": "1.4.6"}, {"expected": "0" * 64}):
            with self.subTest(options=options), self.assertRaisesRegex(WebCheckError, "stale"):
                self.verify(**options)
            self.assertEqual(self.calls, [])

    def test_policy_cannot_redirect_to_other_origins_or_unreviewed_sources(self):
        mutations = [
            ("custom_catalog_url", "https://other.invalid/downloads.json"),
            ("production_catalog_url", self.deployment),
            ("access_login_url", "https://other.cloudflareaccess.com/login"),
            ("access_redirect_path", "/"),
            ("access_login_kid", "invalid-app-id"),
            ("schema", "ignored-mode"),
        ]
        for key, value in mutations:
            original = self.policy[key]; self.policy[key] = value
            with self.subTest(key=key), self.assertRaises(WebCheckError): self.verify()
            self.policy[key] = original
        for key, value in (("catalog_url", "https://other.invalid/downloads.json"),
                           ("source_repository", "other/website"), ("source_commit", "main"), ("id", "latest")):
            original = self.policy["reviewed_deployment"][key]; self.policy["reviewed_deployment"][key] = value
            with self.subTest(key=key), self.assertRaises(WebCheckError): self.verify()
            self.policy["reviewed_deployment"][key] = original
        self.policy["fallback"] = True
        with self.assertRaises(WebCheckError): self.verify()
        self.assertEqual(self.calls, [])

    def test_only_initial_302_is_accepted_even_if_other_response_has_right_bytes(self):
        for status in (200, 301, 303, 307, 308, 401, 403, 404, 500):
            self.responses[WEBSITE_CATALOG] = Readback(WEBSITE_CATALOG, status, self.login, self.body)
            with self.subTest(status=status), self.assertRaisesRegex(WebCheckError, "initial Access 302"):
                self.verify()
        self.assertEqual(set(self.calls), {WEBSITE_CATALOG})

    def test_wrong_login_return_path_fragment_duplicate_or_missing_query_is_refused(self):
        locations = [
            self.login.replace("animalbp.cloudflareaccess.com", "animalbp.cloudflareaccess.com.evil.invalid"),
            self.login.replace("https:", "http:"), self.login.replace("/login/animalbp.com", "/login/other.invalid"),
            self.login + "#fragment", self.login + "&redirect_url=%2Fdownloads.json",
            self.login.replace("%2Fdownloads.json", "https%3A%2F%2Fevil.invalid"),
            self.login.replace("%2Fdownloads.json", "%2Fother.json"),
            ACCESS_LOGIN + "?redirect_url=%2Fdownloads.json", self.login + "&extra=1",
            self.login.replace("a" * 64, ""), self.login.replace("a" * 64, "b" * 64), self.login + "\r\nX-Evil: yes",
            self.login.replace("synthetic-meta-do-not-retain", "a" * 8193),
        ]
        for location in locations:
            self.responses[WEBSITE_CATALOG] = Readback(WEBSITE_CATALOG, 302, location, b"")
            with self.subTest(location_shape=location.split("?")[0]), self.assertRaises(WebCheckError): self.verify()
        self.assertEqual(set(self.calls), {WEBSITE_CATALOG})

    def test_old_immutable_deployment_cannot_hide_changed_current_production_alias(self):
        self.responses[PRODUCTION_CATALOG] = Readback(PRODUCTION_CATALOG, 200, None, self.body + b" ")
        with self.assertRaisesRegex(WebCheckError, "current_production_alias.*differs"): self.verify()
        self.assertEqual(self.calls, [WEBSITE_CATALOG, PRODUCTION_CATALOG])

    def test_each_catalog_requires_exact_bytes_direct_200_and_no_login_html(self):
        for url in (PRODUCTION_CATALOG, self.deployment):
            for response in (Readback(url, 302, self.login, b""), Readback(url, 200, None, b"<html>Access login</html>"),
                             Readback(url, 200, self.login, self.body), Readback(url + "?changed", 200, None, self.body),
                             Readback(url, 503, None, self.body), Readback(url, 200, None, b"a" * (MAX_CATALOG_BYTES + 1))):
                old = self.responses[url]; self.responses[url] = response
                with self.subTest(url=url, status=response.status), self.assertRaises(WebCheckError): self.verify()
                self.responses[url] = old

    def test_release_catalog_anchor_is_checked_before_requests(self):
        self.body += b" "
        with self.assertRaises(WebCheckError): self.verify(expected=self.policy["catalog_sha256"])
        self.assertEqual(self.calls, [])

    def test_transport_does_not_follow_redirect_or_read_login_body_or_add_auth(self):
        headers = Message(); headers["Location"] = self.login
        class ForbiddenBody(io.BytesIO):
            def read(self, *args): raise AssertionError("Access body must not be read")
        response = HTTPError(WEBSITE_CATALOG, 302, "Found", headers, ForbiddenBody())
        captured = {}
        class Opener:
            def open(self, request, timeout):
                captured.update(headers=dict(request.header_items()), url=request.full_url, timeout=timeout)
                raise response
        def build(handler):
            self.assertIsInstance(handler, NoRedirect)
            self.assertIsNone(handler.redirect_request(None, None, 302, "", None, self.login))
            return Opener()
        with patch("verify_protected_website.build_opener", build):
            result = read_without_redirect(WEBSITE_CATALOG)
        self.assertEqual(result.body, b"")
        self.assertEqual(result.status, 302)
        self.assertEqual(captured["headers"], {"User-agent": "AnimalBP-public-release-verifier"})
        self.assertEqual(captured["url"], WEBSITE_CATALOG)

    def test_transport_refuses_ambiguous_location_headers(self):
        headers = Message(); headers["Location"] = self.login; headers["Location"] = self.login
        response = HTTPError(WEBSITE_CATALOG, 302, "Found", headers, io.BytesIO())
        class Opener:
            def open(self, *args, **kwargs): raise response
        with patch("verify_protected_website.build_opener", return_value=Opener()), self.assertRaisesRegex(WebCheckError, "ambiguous"):
            read_without_redirect(WEBSITE_CATALOG)


if __name__ == "__main__": unittest.main()
