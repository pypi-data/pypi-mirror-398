import asyncio
from dataclasses import dataclass
import re
import time
from typing import Any, Literal
from urllib.parse import urljoin

import aiohttp
from chalkbox.logging.bridge import get_logger
from packaging.specifiers import SpecifierSet
from packaging.version import InvalidVersion, Version

logger = get_logger(__name__)

FileType = Literal["wheel", "sdist", "unknown"]


@dataclass
class VersionCandidate:
    version: str
    filename: str
    file_type: FileType
    requires_python: str | None = None
    has_metadata: bool = False
    yanked: bool = False
    upload_time: str | None = None
    url: str | None = None  # Download URL
    metadata_url: str | None = None  # Metadata URL
    python_min: str | None = None  # Minimum Python version from classifiers/metadata
    python_max: str | None = None  # Maximum Python version from classifiers

    def is_wheel(self) -> bool:
        return self.file_type == "wheel"

    def is_prerelease(self) -> bool:
        return any(x in self.version for x in ["a", "b", "rc", "dev", "pre"])


@dataclass
class CacheEntry:
    data: Any
    timestamp: float
    ttl: float = 3600  # 1 hour default

    def is_expired(self) -> bool:
        return time.time() - self.timestamp > self.ttl


class PyPIClient:
    def __init__(
        self, index_url: str = "https://pypi.org/", cache_ttl: int = 3600, max_concurrent: int = 4
    ):
        self.index_url = index_url.rstrip("/") + "/"
        self.simple_url = urljoin(self.index_url, "simple/")
        self.cache_ttl = cache_ttl
        self.max_concurrent = max_concurrent
        self.cache: dict[str, CacheEntry] = {}
        self.semaphore = asyncio.Semaphore(max_concurrent)

    @staticmethod
    def normalize_name(name: str) -> str:
        return re.sub(r"[-_.]+", "-", name).lower()

    async def get_project_metadata(self, package_name: str) -> dict[str, Any]:
        normalized = self.normalize_name(package_name)
        cache_key = f"simple:{normalized}"

        if cache_key in self.cache:
            entry = self.cache[cache_key]
            if not entry.is_expired():
                logger.debug(f"Cache hit for {package_name}")
                result: dict[str, Any] = entry.data
                return result

        url = urljoin(self.simple_url, f"{normalized}/")
        headers = {"Accept": "application/vnd.pypi.simple.v1+json", "User-Agent": "depcheck/1.0"}

        async with self.semaphore, aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=headers) as response:
                    if response.status == 404:
                        logger.error(f"Package {package_name} not found")
                        return {"error": f"Package {package_name} not found"}

                    response.raise_for_status()

                    # Check if we got JSON
                    content_type = response.headers.get("Content-Type", "")
                    if "json" in content_type or "application/vnd.pypi.simple" in content_type:
                        data = await response.json()
                        logger.debug(
                            f"Got JSON response for {package_name}:"
                            f" {list(data.keys()) if isinstance(data, dict) else type(data)}"
                        )
                    else:
                        # Fallback to parsing HTML if JSON not available
                        logger.warning(
                            f"JSON not available for {package_name}"
                            f" (Content-Type: {content_type}), falling back to HTML"
                        )
                        text = await response.text()
                        data = self._parse_simple_html(text, normalized)

                    # Ensure data is a dictionary with 'files' list
                    if not isinstance(data, dict):
                        logger.error(f"Unexpected response format for {package_name}: {type(data)}")
                        return {"error": f"Invalid response format: {type(data)}", "files": []}

                    if "files" not in data:
                        # Handle PEP 691 format where files might be under different key
                        data["files"] = data.get("urls", [])

                    # Cache the result
                    self.cache[cache_key] = CacheEntry(data, time.time(), self.cache_ttl)
                    return data

            except aiohttp.ClientError as e:
                logger.error(f"Failed to fetch {package_name}: {e}")
                return {"error": str(e)}

    @staticmethod
    def _parse_simple_html(html: str, package_name: str) -> dict[str, Any]:
        """Parse Simple API HTML fallback (basic implementation)."""

        files: list[dict[str, Any]] = []
        link_pattern = r'<a[^>]*href="([^"]+)"[^>]*>([^<]+)</a>'

        for match in re.finditer(link_pattern, html):
            url, filename = match.groups()
            files.append({"filename": filename, "url": url, "hashes": {}})

        return {"name": package_name, "files": files}

    async def get_file_metadata(self, metadata_url: str) -> str | None:
        """Fetch PEP 658 Core Metadata from a .metadata URL."""
        cache_key = f"metadata:{metadata_url}"

        if cache_key in self.cache:
            entry = self.cache[cache_key]
            if not entry.is_expired():
                content: str | None = entry.data
                return content

        async with self.semaphore, aiohttp.ClientSession() as session:
            try:
                async with session.get(metadata_url) as response:
                    response.raise_for_status()
                    content = await response.text()

                    self.cache[cache_key] = CacheEntry(content, time.time(), self.cache_ttl)
                    return content

            except aiohttp.ClientError as e:
                logger.error(f"Failed to fetch metadata from {metadata_url}: {e}")
                return None

    def extract_versions_from_files(self, files: list[dict[str, Any]]) -> list[VersionCandidate]:
        candidates = []

        for file_info in files:
            filename = file_info.get("filename", "")
            url = file_info.get("url", "")

            version = self._extract_version_from_filename(filename)
            if not version:
                continue

            metadata_url = None
            has_metadata = False

            # Check for various metadata formats
            # PEP 658: data-dist-info-metadata indicates metadata is available at URL + .metadata
            # It can be either a boolean True or a dict with hash
            if (
                file_info.get("data-dist-info-metadata")
                or file_info.get("core-metadata")
                or file_info.get("data-core-metadata")
            ):
                base_url = file_info.get("url", "")
                if base_url:
                    metadata_url = base_url + ".metadata"
                    has_metadata = True

            file_type: FileType = "unknown"
            if filename.endswith(".whl"):
                file_type = "wheel"
            elif filename.endswith((".tar.gz", ".zip")):
                file_type = "sdist"

            candidate = VersionCandidate(
                version=version,
                filename=filename,
                url=url,
                metadata_url=metadata_url,
                has_metadata=has_metadata,
                file_type=file_type,
                requires_python=file_info.get("requires-python"),
            )

            candidates.append(candidate)

        return candidates

    @staticmethod
    def _extract_version_from_filename(filename: str) -> str | None:
        """
        Extract version from a distribution filename.

        Simple pattern for wheels: name-version-pyXX-none-any.whl
        Simple pattern for sdist: name-version.tar.gz
        """

        # Wheel pattern - also handle versions like "2004d"
        wheel_pattern = r"-([0-9]+[0-9a-zA-Z\.\+\-]*?)-(?:py|cp)"
        match = re.search(wheel_pattern, filename)
        if match:
            return match.group(1)

        # Sdist pattern (before .tar.gz or .zip) - also handle non-standard versions
        sdist_pattern = r"-([0-9]+[0-9a-zA-Z\.\+\-]*?)(?:\.tar\.gz|\.zip)"
        match = re.search(sdist_pattern, filename)
        if match:
            return match.group(1)

        # Fallback: try to extract anything that looks like a version
        version_pattern = r"-([0-9]+[0-9a-zA-Z\.\+\-]*?)(?:-|\.tar\.gz|\.zip|\.whl)"
        match = re.search(version_pattern, filename)
        if match:
            return match.group(1)

        return None

    async def get_package_versions(
        self, package_name: str, python_constraint: str | None = None
    ) -> list[VersionCandidate]:
        project_data = await self.get_project_metadata(package_name)

        if "error" in project_data:
            logger.error(f"Failed to get metadata for {package_name}: {project_data['error']}")
            return []

        files = project_data.get("files", [])
        candidates = self.extract_versions_from_files(files)

        # Filter by python_constraint if provided
        if python_constraint:
            try:
                # Parse the project's Python constraint (e.g., ">=3.8.1,<3.9")
                project_spec = SpecifierSet(python_constraint)

                # Filter candidates based on Python compatibility
                filtered = []
                for c in candidates:
                    if not c.requires_python:
                        # No Python requirement - assume compatible
                        filtered.append(c)
                    else:
                        try:
                            # Parse the package's Python requirement (e.g., ">=3.10")
                            pkg_spec = SpecifierSet(c.requires_python)

                            # Check if package supports the ENTIRE project Python range
                            test_versions = []
                            for minor in range(6, 21):  # Python 3.6 to 3.20 (future-proof)
                                for patch in [0, 5, 10, 15, 20]:
                                    test_versions.append(Version(f"3.{minor}.{patch}"))

                            # Find all Python versions in project's range
                            project_versions = [v for v in test_versions if v in project_spec]

                            if not project_versions:
                                # Empty project range (shouldn't happen) - conservative include
                                filtered.append(c)
                                continue

                            # Check if package supports the MINIMUM Python version in project's range
                            # This ensures the package works for ALL supported Python versions
                            min_project_version = min(project_versions)
                            supports_minimum = min_project_version in pkg_spec

                            if supports_minimum:
                                filtered.append(c)
                            else:
                                logger.debug(
                                    f"Package {c.filename} incompatible: requires {c.requires_python}, "
                                    f"but project minimum is Python {min_project_version}."
                                )
                        except Exception as e:
                            logger.debug(
                                f"Could not parse requires_python '{c.requires_python}': {e}"
                            )
                            # If we can't parse, include it to be safe
                            filtered.append(c)
                candidates = filtered
            except Exception as e:
                logger.warning(f"Failed to filter by python_constraint: {e}")

        def safe_version_key(_candidate: VersionCandidate) -> Version:
            try:
                return Version(_candidate.version)
            except InvalidVersion:
                # For invalid versions, return a version that sorts last
                return Version("0.0.0")

        candidates.sort(key=safe_version_key, reverse=True)

        # Group by version and prefer wheels with metadata
        version_map = {}
        for candidate in candidates:
            if candidate.version not in version_map:
                version_map[candidate.version] = candidate
            else:
                # Prefer wheel with metadata > wheel > sdist with metadata > sdist
                current = version_map[candidate.version]
                if self._should_replace_candidate(current, candidate):
                    version_map[candidate.version] = candidate

        return list(version_map.values())

    @staticmethod
    def _should_replace_candidate(current: VersionCandidate, new: VersionCandidate) -> bool:
        # Scoring: wheel+metadata=4, wheel=3, sdist+metadata=2, sdist=1
        def score(c: VersionCandidate) -> int:
            s = 0
            if c.is_wheel():
                s += 2
            if c.has_metadata:
                s += 2
            return s

        return score(new) > score(current)

    async def get_package_json_info(
        self, package_name: str, version: str | None = None
    ) -> dict[str, Any]:
        normalized = self.normalize_name(package_name)

        cache_key = f"json:{normalized}:{version or 'latest'}"

        # Check cache (longer TTL for classifiers since they change rarely)
        if cache_key in self.cache:
            entry = self.cache[cache_key]
            if not entry.is_expired():
                logger.debug(f"Cache hit for JSON info {package_name}")
                cached_data: dict[str, Any] = entry.data
                return cached_data

        if version:
            url = f"https://pypi.org/pypi/{normalized}/{version}/json"
        else:
            url = f"https://pypi.org/pypi/{normalized}/json"

        headers = {
            "User-Agent": "depchk/1.0 (+https://github.com/bulletinmybeard/depchk)",
            "Accept": "application/vnd.pypi.simple.v1+json, application/json",
        }

        async with (
            self.semaphore,
            aiohttp.ClientSession() as session,
            session.get(url, headers=headers) as response,
        ):
            if response.status == 404:
                logger.warning(
                    f"Package {package_name} version {version or 'latest'} not found on PyPI"
                )
                return {"error": "not_found"}

            response.raise_for_status()
            json_data: dict[str, Any] = await response.json()

            # Cache with 24-hour TTL
            self.cache[cache_key] = CacheEntry(json_data, time.time(), 86400)
            return json_data

    @staticmethod
    def extract_python_versions_from_classifiers(classifiers: list[str]) -> dict[str, Any]:
        python_versions = []

        # Look for "Programming Language :: Python :: X.Y" classifiers
        for classifier in classifiers:
            match = re.search(r"Programming Language :: Python :: (\d+)\.(\d+)", classifier)
            if match:
                major, minor = match.groups()
                python_versions.append(f"{major}.{minor}")

        # Sort versions
        def version_tuple(v: str) -> tuple[int, ...]:
            parts = v.split(".")
            return tuple(int(p) for p in parts)

        if python_versions:
            python_versions.sort(key=version_tuple)
            return {
                "tested_versions": python_versions,
                "min_version": python_versions[0],
                "max_version": python_versions[-1],
            }

        return {"tested_versions": [], "min_version": None, "max_version": None}
