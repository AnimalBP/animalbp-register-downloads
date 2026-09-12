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
WEBSITE_CATALOG = "https://animalbp.com/downloads.json"
APP_CATALOG_ASSET = "assets/desktop-downloads.json"
STABLE_VERSION = r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)"


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
    require(APP_CATALOG_ASSET in assets, "Release manifest must pin the shared desktop download catalog")
    require(app == f"app-{version}-{assets[app][:12]}.js", "Release application filename must match its content hash")
    require(manifest.get("shared_content_sha256") == digest(json.dumps(dict(sorted(assets.items())), separators=(",", ":")).encode()),
            "Release runtime content digest is invalid")
    for field in ["web_config_sha256", "web_index_sha256"]:
        value = manifest.get(field)
        require(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value), f"Invalid {field}")


def catalog_version(raw, label):
    catalog = json_object(raw, label)
    platforms = catalog.get("platforms")
    require(catalog.get("schema") == 1 and isinstance(platforms, list) and len(platforms) == 2
            and all(isinstance(item, dict) for item in platforms), f"{label} has an invalid platform catalog")
    platforms = {item.get("id"): item for item in platforms}
    require(set(platforms) == {"macos", "windows"}, f"{label} must contain exactly Mac and Windows")
    mac, windows = platforms["macos"], platforms["windows"]
    title = mac.get("title")
    match = re.fullmatch(r"Mac · (" + STABLE_VERSION + r")", title) if isinstance(title, str) else None
    require(match is not None, f"{label} must identify one stable Mac version")
    version = match[1]
    base = "https://github.com/AnimalBP/animalbp-register-downloads/releases"
    require(mac.get("url") == f"{base}/download/v{version}/AnimalBP-Register-{version}-mac-arm64.dmg",
            f"{label} Mac title and official installer URL must agree")
    require(windows.get("title") == "Windows"
            and windows.get("url") == "https://apps.microsoft.com/detail/9NP93BBMMZ4S?mode=direct",
            f"{label} must preserve truthful Microsoft Store availability")
    notes, links = catalog.get("notes"), catalog.get("links")
    require(isinstance(notes, list) and len(notes) >= 3 and all(isinstance(note, str) for note in notes)
            and isinstance(links, list) and all(isinstance(link, dict) for link in links)
            and any(link.get("url") == f"{base}/tag/v{version}" for link in links),
            f"{label} must include complete installation notes and matching release notes")
    serialized = json.dumps(catalog)
    for pattern in [r"/releases/(?:download|tag)/v([^\s/\"'<>]+)",
                    r"AnimalBP-Register-([^\s/\"'<>]+?)-(?:mac|win)-"]:
        require(all(found == version for found in re.findall(pattern, serialized)),
                f"{label} contains mixed release versions")
    return version


def verify_website_catalog(raw_expected, expected_sha256, version, fetch):
    require(digest(raw_expected) == expected_sha256,
            "Application catalog differs from its release-pinned digest")
    require(catalog_version(raw_expected, "Release-pinned app catalog") == version,
            "Release-pinned app catalog has the wrong release version")
    public_bytes = fetch(WEBSITE_CATALOG)
    public_version = catalog_version(public_bytes, "Public website catalog")
    if tuple(map(int, public_version.split("."))) < tuple(map(int, version.split("."))):
        raise WebAlignmentPending(f"GitHub {version} is published; website downloads are {public_version}. "
                                  "Website publication/cache propagation is pending alignment, not verified parity.")
    require(public_version == version, "Public website catalog is ahead of the latest stable release")
    require(digest(public_bytes) == expected_sha256,
            "Same-version website catalog differs from the release-pinned app catalog")
    return {"status": "passed", "version": version, "url": WEBSITE_CATALOG, "sha256": expected_sha256}


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
    website_catalog = verify_website_catalog(bodies[APP_CATALOG_ASSET], manifest["assets"][APP_CATALOG_ASSET], version, fetch)
    return {"status": "passed", "version": version, "parity_verified": True,
            "release_manifest_asset_id": asset["id"], "release_manifest_sha256": digest(raw_manifest),
            "shared_content_sha256": manifest["shared_content_sha256"],
            "runtime_assets_verified": len(bodies), "runtime_urls_verified": sum(map(len, urls.values())),
            "website_catalog": website_catalog,
            "scope": "Public web/demo bytes and website catalog only; no demo session, backend or Store acceptance inferred"}
