"""Check an explicit release policy without treating an Access login as content.

The current production alias and a reviewed immutable deployment must both serve
the release-pinned catalog. The protected custom domain must retain its exact
Access boundary. No credentials or redirect-query contents enter the report.
"""

from dataclasses import dataclass
import hashlib
import json
import re
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from verify_web_demo import WEBSITE_CATALOG, WebCheckError, catalog_version, digest, require


SCHEMA = "animalbp-protected-website-policy-v1"
PRODUCTION_CATALOG = "https://animalbp-register-website.pages.dev/downloads.json"
ACCESS_LOGIN = "https://animalbp.cloudflareaccess.com/cdn-cgi/access/login/animalbp.com"
POLICY_KEYS = {"schema", "version", "catalog_sha256", "custom_catalog_url", "access_login_url", "access_login_kid",
               "access_redirect_path", "production_catalog_url", "reviewed_deployment"}
DEPLOYMENT_KEYS = {"id", "catalog_url", "source_repository", "source_commit"}
USER_AGENT = "AnimalBP-public-release-verifier"
MAX_CATALOG_BYTES = 64 * 1024


@dataclass(frozen=True)
class Readback:
    url: str
    status: int
    location: str | None
    body: bytes


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def read_without_redirect(url):
    """Anonymous GET only; never follow login or deployment redirects."""
    opener = build_opener(NoRedirect())
    request = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        response = opener.open(request, timeout=30)
    except HTTPError as error:
        response = error
    with response:
        locations = response.headers.get_all("Location", [])
        require(len(locations) <= 1, "Website response has ambiguous redirects")
        body = response.read(MAX_CATALOG_BYTES + 1) if response.status == 200 else b""
        require(len(body) <= MAX_CATALOG_BYTES, "Website catalog exceeds its size bound")
        return Readback(response.geturl(), response.status, locations[0] if locations else None, body)


def validate_policy(policy, version, expected_sha256):
    require(isinstance(policy, dict) and set(policy) == POLICY_KEYS and policy.get("schema") == SCHEMA,
            "Unsupported protected website policy")
    require(policy["version"] == version and policy["catalog_sha256"] == expected_sha256,
            "Protected website policy is stale for this release; review its version and catalog binding")
    require(re.fullmatch(r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)", version) is not None
            and re.fullmatch(r"[0-9a-f]{64}", expected_sha256) is not None, "Invalid protected release identity")
    require(policy["custom_catalog_url"] == WEBSITE_CATALOG and policy["access_login_url"] == ACCESS_LOGIN
            and policy["access_redirect_path"] == "/downloads.json"
            and policy["production_catalog_url"] == PRODUCTION_CATALOG,
            "Protected website policy cannot select another site, login or production alias")
    require(isinstance(policy["access_login_kid"], str)
            and re.fullmatch(r"[0-9a-f]{64}", policy["access_login_kid"]) is not None,
            "Protected website Access login kid is invalid")
    deployment = policy["reviewed_deployment"]
    require(isinstance(deployment, dict) and set(deployment) == DEPLOYMENT_KEYS,
            "Invalid reviewed website deployment binding")
    identifier = deployment.get("id")
    require(isinstance(identifier, str) and re.fullmatch(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}", identifier) is not None,
            "Reviewed website deployment ID is invalid")
    require(deployment["catalog_url"] == f"https://{identifier[:8]}.animalbp-register-website.pages.dev/downloads.json"
            and deployment["source_repository"] == "AnimalBP/animalbp-register-website"
            and isinstance(deployment["source_commit"], str)
            and re.fullmatch(r"[0-9a-f]{40}", deployment["source_commit"]) is not None,
            "Reviewed deployment URL or source provenance differs")


def verify_access(readback, policy):
    require(readback.url == WEBSITE_CATALOG and readback.status == 302,
            "Protected website must return the reviewed initial Access 302")
    location = readback.location
    require(isinstance(location, str) and len(location) <= 16 * 1024
            and not any(ord(char) < 32 for char in location), "Protected website has an invalid redirect")
    parsed = urlsplit(location)
    require(f"{parsed.scheme}://{parsed.netloc}{parsed.path}" == ACCESS_LOGIN and not parsed.fragment,
            "Protected website redirected to an unexpected login destination")
    try:
        query = parse_qs(parsed.query, keep_blank_values=True, strict_parsing=True)
    except ValueError as error:
        raise WebCheckError("Protected website Access query is invalid") from error
    require(set(query) == {"kid", "meta", "redirect_url"}
            and all(len(values) == 1 and values[0] for values in query.values())
            and query["kid"] == [policy["access_login_kid"]]
            and query["redirect_url"] == [policy["access_redirect_path"]]
            and len(query["kid"][0]) <= 256 and len(query["meta"][0]) <= 8192,
            "Protected website Access redirect shape or return path changed")
    return {"url": WEBSITE_CATALOG, "status": 302, "login_url_without_query": ACCESS_LOGIN,
            "return_path": policy["access_redirect_path"], "boundary_verified": True, "login_kid_verified": True,
            "redirect_followed": False, "query_tokens_retained": False}


def verify_protected_website(raw_expected, expected_sha256, version, fetch, *, policy, probe=read_without_redirect):
    """Explicit policy mode: never a fallback for arbitrary failures or HTML."""
    # fetch is the ordinary guard's anonymous fetch dependency. This mode uses
    # its own stricter no-redirect reader, with no route for a GitHub API token.
    validate_policy(policy, version, expected_sha256)
    require(digest(raw_expected) == expected_sha256 and catalog_version(raw_expected, "Release-pinned app catalog") == version,
            "Protected website policy lacks the published release catalog anchor")
    access = verify_access(probe(WEBSITE_CATALOG), policy)
    catalogs = []
    for role, url in (("current_production_alias", PRODUCTION_CATALOG),
                      ("reviewed_immutable_deployment", policy["reviewed_deployment"]["catalog_url"])):
        response = probe(url)
        require(response.url == url and response.status == 200 and response.location is None,
                f"{role} catalog must be directly public without redirects")
        require(len(response.body) <= MAX_CATALOG_BYTES and digest(response.body) == expected_sha256,
                f"{role} catalog differs from the release-pinned bytes")
        require(catalog_version(response.body, role) == version, f"{role} catalog version differs")
        catalogs.append({"role": role, "url": url, "status": 200, "sha256": expected_sha256,
                         "bytes": len(response.body)})
    return {"status": "protected_site_verified", "version": version,
            "policy_sha256": hashlib.sha256(json.dumps(policy, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
            "sha256": expected_sha256, "access": access, "catalogs": catalogs,
            "reviewed_deployment": policy["reviewed_deployment"],
            "current_production_alias_catalog_verified": True,
            "public_custom_domain_verified": False,
            "scope": "Expected Access boundary and release-pinned catalogs on the current production alias and reviewed deployment; authenticated custom-domain bytes are not verified"}
