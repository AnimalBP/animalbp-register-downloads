"""Verify web/demo against the manifest pinned by a public GitHub release asset.

The caller first validates root/release SHA256SUMS and GitHub asset digests.
The served web manifest is never accepted as its own trust anchor.
"""

import hashlib
from html.parser import HTMLParser
import json
from pathlib import PurePosixPath
import re
from urllib.parse import urljoin, urlsplit


WEB = "https://app.animalbp.com/"
DEMO = WEB + "?demo=1"
MANIFEST_NAME = "release-content.json"


class WebCheckError(ValueError):
    pass


class WebAlignmentPending(WebCheckError):
    pass


def require(condition, message):
    if not condition:
        raise WebCheckError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def json_object(data, label):
    try:
        value = json.loads(data)
    except (UnicodeError, json.JSONDecodeError) as error:
        raise WebCheckError(f"{label} must be valid JSON") from error
    require(isinstance(value, dict), f"{label} must be an object")
    return value


class Resources(HTMLParser):
    def __init__(self, html, page):
        super().__init__()
        self.page = page
        self.scripts, self.resources = [], []
        self.feed(html.decode("utf-8"))

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "script" and attrs.get("src"):
            self.scripts.append(urljoin(self.page, attrs["src"]))
        if tag == "link" and attrs.get("href") and attrs.get("rel") in {"stylesheet", "icon"}:
            self.resources.append(urljoin(self.page, attrs["href"]))


def validate_manifest(manifest, version):
    require(manifest.get("schema_version") == 1 and manifest.get("scope") == "public-web-and-demo",
            "Unsupported release content manifest schema/scope")
    require(manifest.get("version") == version and manifest.get("environment") == "production",
            "Release content manifest must identify the published stable production version")
    require(manifest.get("demo_entry_path") == "/?demo=1" and manifest.get("demo_uses_shared_web_bundle") is True,
            "Release content manifest must bind the demo to the shared production bundle")
    assets = manifest.get("assets")
    require(isinstance(assets, dict) and 2 <= len(assets) <= 128, "Invalid release runtime asset list")
    for name, checksum in assets.items():
        require(isinstance(name, str) and re.fullmatch(r"[A-Za-z0-9_./-]+", name)
                and not PurePosixPath(name).is_absolute() and ".." not in PurePosixPath(name).parts,
                "Unsafe release runtime asset path")
        require(isinstance(checksum, str) and re.fullmatch(r"[0-9a-f]{64}", checksum), "Invalid release runtime checksum")
    app = manifest.get("app_asset")
    require(isinstance(app, str) and app in assets and "styles.css" in assets,
            "Release manifest must identify the loaded application and stylesheet")
    require(app == f"app-{version}-{assets[app][:12]}.js", "Release application filename must match its content hash")
    require(manifest.get("shared_content_sha256") == digest(json.dumps(dict(sorted(assets.items())), separators=(",", ":")).encode()),
            "Release runtime content digest is invalid")
    for field in ["web_config_sha256", "web_index_sha256"]:
        value = manifest.get(field)
        require(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value), f"Invalid {field}")


def verify_web_demo(repo, release, fetch):
    require(repo == "AnimalBP/animalbp-register-downloads", "Web parity is bound to the official downloads repository")
    tag = release.get("tag_name", "")
    match = re.fullmatch(r"v((?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*))", tag)
    require(match is not None and release.get("draft") is False and release.get("prerelease") is False,
            "Web parity requires a published stable release")
    version = match[1]
    matches = [asset for asset in release.get("assets", []) if asset.get("name") == MANIFEST_NAME]
    if not matches and tuple(map(int, version.split("."))) < (1, 4, 5):
        return {"status": "legacy_not_configured", "version": version, "parity_verified": False,
                "reason": "This historical release predates the release-pinned web manifest"}
    require(len(matches) == 1, "Stable releases from 1.4.5 require exactly one release-content.json asset")
    asset = matches[0]
    require(type(asset.get("id")) is int and asset["id"] > 0 and asset.get("state") == "uploaded", "Release content asset is not a completed upload")
    release_url = f"https://github.com/{repo}/releases/download/{tag}/{MANIFEST_NAME}"
    raw_manifest = fetch(release_url)
    require(asset.get("size") == len(raw_manifest) and asset.get("digest") == "sha256:" + digest(raw_manifest),
            "Release content bytes differ from the GitHub asset size/digest")
    manifest = json_object(raw_manifest, "Release content manifest")
    validate_manifest(manifest, version)
    web, demo = fetch(WEB), fetch(DEMO)
    web_page, demo_page = Resources(web, WEB), Resources(demo, DEMO)
    require(web_page.scripts == demo_page.scripts and WEB + "config.js" in web_page.scripts,
            "Normal web and demo must load the same configuration and scripts")
    config_bytes = fetch(WEB + "config.js")
    match = re.fullmatch(rb"globalThis\.ABP_CONFIG = Object\.freeze\((.*)\);\s*", config_bytes, flags=re.DOTALL)
    require(match is not None, "Public config is not a generated ABP_CONFIG object")
    config = json_object(match[1], "Public config")
    require(config.get("environment") == "production" and config.get("demoMode") is False
            and config.get("apiBaseUrl") == "https://api.animalbp.com", "Public demo must use the session-protected production application")
    if config.get("version") != version:
        raise WebAlignmentPending(f"GitHub {version} is published; web/demo is {config.get('version')}. "
                                  "An approved early GitHub release window is pending deployment alignment, not verified parity.")
    require(digest(config_bytes) == manifest["web_config_sha256"], "Public config differs from the release-pinned content manifest")
    require(digest(web) == manifest["web_index_sha256"] and digest(demo) == manifest["web_index_sha256"],
            "Web/demo HTML differs from the release-pinned content manifest")
    require(any(urlsplit(url).path == "/" + manifest["app_asset"] for url in web_page.scripts),
            "Public HTML does not load the release-pinned application")
    require(json_object(fetch(WEB + MANIFEST_NAME), "Served content manifest") == manifest,
            "Served content manifest differs from its release asset; it cannot authorize changed web bytes")
    bodies, urls = {}, {name: {WEB + name} for name in manifest["assets"]}
    for name, checksum in manifest["assets"].items():
        bodies[name] = fetch(WEB + name)
        require(digest(bodies[name]) == checksum, f"Public runtime asset differs from release content: {name}")
    referenced = [*web_page.scripts, *web_page.resources]
    for name, body in bodies.items():
        if name.endswith(".js"):
            imports = re.findall(r"\b(?:from\s*|import\s*\(\s*)[\"'](\.[^\"']+)[\"']|^\s*import\s*[\"'](\.[^\"']+)[\"']", body.decode("utf-8"), re.MULTILINE)
            referenced.extend(urljoin(WEB + name, left or right) for left, right in imports)
    for url in referenced:
        parsed = urlsplit(url)
        require(parsed.scheme == "https" and parsed.netloc == "app.animalbp.com" and not parsed.fragment,
                "Public runtime references must remain on the application origin")
        name = parsed.path.removeprefix("/")
        if name == "config.js":
            require(url == WEB + "config.js", "All entry points must load the same config.js")
            continue
        require(name in urls, "Loaded runtime asset is missing from the release-pinned manifest")
        urls[name].add(url)
    for name, variants in urls.items():
        for url in variants - {WEB + name}:
            require(digest(fetch(url)) == manifest["assets"][name], f"Actual browser query URL differs from release content: {name}")
    return {"status": "passed", "version": version, "parity_verified": True,
            "release_manifest_asset_id": asset["id"], "release_manifest_sha256": digest(raw_manifest),
            "shared_content_sha256": manifest["shared_content_sha256"],
            "runtime_assets_verified": len(bodies), "runtime_urls_verified": sum(map(len, urls.values())),
            "scope": "Public web/demo bytes only; no demo session, backend or Store acceptance inferred"}
