#!/usr/bin/env python3
"""Read-only guard for public GitHub release files; does not infer Store status."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


STABLE_TAG = re.compile(r"v((?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*))")
REPOSITORY = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")


class ReleaseError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ReleaseError(message)


def expected_assets(version: str) -> set[str]:
    prefix = f"AnimalBP-Register-{version}"
    return {
        f"{prefix}-mac-arm64.dmg", f"{prefix}-mac-arm64.zip",
        f"{prefix}-win-x64.exe", f"{prefix}-win-x64.exe.blockmap",
        f"{prefix}-win-x64.zip", "latest.yml",
    }


def checksum_entries(content: bytes) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in content.decode("utf-8").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  ([A-Za-z0-9_.-]+)", line)
        require(match is not None, "SHA256SUMS.txt has an invalid entry")
        digest, name = match.groups()
        require(name not in result, f"Duplicate checksum entry: {name}")
        result[name] = digest
    return result


def yaml_values(text: str, key: str) -> list[str]:
    """Read plain/quoted scalar fields from electron-builder's small manifest."""
    values = re.findall(rf"^\s*(?:-\s*)?{re.escape(key)}:\s*([^\r\n]+)\s*$", text, re.M)
    return [value.strip().strip("\"'") for value in values]


def validate_release(repo: str, release: dict, documents: dict[str, bytes],
                     release_checksums: bytes, updater: bytes) -> str:
    require(not release.get("draft") and not release.get("prerelease"),
            "The latest release must be published and stable")
    match = STABLE_TAG.fullmatch(release.get("tag_name", ""))
    require(match is not None, "The latest release tag must be vMAJOR.MINOR.PATCH")
    version = match.group(1)
    base = f"https://github.com/{repo}/releases"
    tag_url = f"{base}/tag/v{version}"
    download_base = f"{base}/download/v{version}/"
    for filename in ("README.md", "RELEASE-NOTES.md"):
        text = documents[filename].decode("utf-8")
        heading = (f"## Current release: {version}" if filename == "README.md"
                   else f"# AnimalBP Register {version}")
        require(heading in text.splitlines(), f"{filename} does not identify version {version}")
        require(f"{base}/latest" in text, f"{filename} is missing the latest-release link")
        require(tag_url in text, f"{filename} is missing the exact release link")
        for url in re.findall(r"https://[^\s)<>]+", text):
            if url.startswith(f"{base}/download/"):
                require(url.startswith(download_base), f"{filename} has a stale download link: {url}")
                require(url[len(download_base):] in expected_assets(version) | {"SHA256SUMS.txt"},
                        f"{filename} links an unexpected release asset: {url}")
            elif url.startswith(f"{base}/tag/"):
                require(url == tag_url, f"{filename} has a stale release link: {url}")
    readme = documents["README.md"].decode("utf-8")
    require(f"{download_base}AnimalBP-Register-{version}-mac-arm64.dmg" in readme,
            "README.md is missing the current Mac installer link")
    require(f"{download_base}SHA256SUMS.txt" in readme,
            "README.md is missing the current checksum link")

    items = release.get("assets", [])
    assets = {item["name"]: item for item in items}
    require(len(assets) == len(items), "The release contains duplicate asset names")
    required = expected_assets(version) | {"SHA256SUMS.txt", "RELEASE-NOTES.md"}
    require(required <= assets.keys(), f"Missing release assets: {sorted(required - assets.keys())}")
    require("latest-mac.yml" not in assets,
            "Manual Mac distribution must not publish latest-mac.yml")
    require(documents["SHA256SUMS.txt"] == release_checksums,
            "Root SHA256SUMS.txt differs from the published release checksum file")
    checksums = checksum_entries(release_checksums)
    require(set(checksums) == expected_assets(version),
            "SHA256SUMS.txt must cover exactly the six current public files")
    for name, digest in checksums.items():
        require(assets[name].get("digest") == f"sha256:{digest}",
                f"GitHub asset digest differs from SHA256SUMS.txt: {name}")
    require(assets["SHA256SUMS.txt"].get("digest") ==
            f"sha256:{hashlib.sha256(release_checksums).hexdigest()}",
            "Published SHA256SUMS.txt content differs from its GitHub asset digest")
    require(assets["RELEASE-NOTES.md"].get("digest") ==
            f"sha256:{hashlib.sha256(documents['RELEASE-NOTES.md']).hexdigest()}",
            "Published RELEASE-NOTES.md asset differs from the root release notes")
    require(hashlib.sha256(updater).hexdigest() == checksums["latest.yml"],
            "Downloaded latest.yml differs from its published checksum")
    manifest = updater.decode("utf-8")
    installer = f"AnimalBP-Register-{version}-win-x64.exe"
    require(yaml_values(manifest, "version") == [version], "latest.yml has a stale version")
    require(yaml_values(manifest, "path") == [installer], "latest.yml has an incorrect installer path")
    require(yaml_values(manifest, "url") == [installer], "latest.yml has an incorrect installer URL")
    return version


def fetch(url: str, token: str | None = None) -> bytes:
    headers = {"User-Agent": "AnimalBP-public-release-verifier"}
    if token:
        require(url.startswith("https://api.github.com/"), "API token restricted to GitHub API")
        headers.update({"Authorization": f"Bearer {token}",
                        "Accept": "application/vnd.github+json",
                        "X-GitHub-Api-Version": "2022-11-28"})
    with urlopen(Request(url, headers=headers), timeout=30) as response:
        data = response.read(2_000_001)
    require(len(data) <= 2_000_000, "Release metadata exceeds the size limit")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", "AnimalBP/animalbp-register-downloads"))
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        require(REPOSITORY.fullmatch(args.repo) is not None, "Invalid owner/repository")
        release = json.loads(fetch(f"https://api.github.com/repos/{args.repo}/releases/latest",
                                   os.environ.get("GITHUB_TOKEN")))
        tag = release.get("tag_name", "")
        require(STABLE_TAG.fullmatch(tag) is not None, "Invalid stable release tag")
        base = f"https://github.com/{args.repo}/releases/download/{tag}/"
        documents = {name: (args.root / name).read_bytes()
                     for name in ("README.md", "RELEASE-NOTES.md", "SHA256SUMS.txt")}
        # Public downloads use no API token, including redirects to asset storage.
        version = validate_release(args.repo, release, documents,
                                   fetch(base + "SHA256SUMS.txt"), fetch(base + "latest.yml"))
        print(f"PASS: GitHub {version} documents, six asset digests, and Windows updater agree.")
        print("Microsoft Store publication and installed-app acceptance require separate evidence.")
        return 0
    except (ReleaseError, OSError, HTTPError, URLError, KeyError, TypeError,
            UnicodeError, json.JSONDecodeError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
