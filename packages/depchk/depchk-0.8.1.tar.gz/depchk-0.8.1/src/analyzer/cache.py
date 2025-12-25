from collections.abc import Callable
from datetime import datetime, timedelta
import json
from pathlib import Path
import re
from typing import Any

from chalkbox.logging.bridge import get_logger
from packaging.version import Version

from src.core.pypi_client import PyPIClient

logger = get_logger(__name__)


class VersionCache:
    def __init__(self, pypi_client: PyPIClient) -> None:
        self.pypi_client = pypi_client

    async def build_cache(
        self,
        pyproject_path: str,
        packages: dict[str, str],
        python_req: str,
        vendor_constraints: dict[str, Any],
        target_python: str | None = None,
        convert_poetry_to_pep440_func: Callable[[str], str] | None = None,
    ) -> dict[str, Any]:
        if target_python:
            py_version = re.search(r"(\d+\.\d+)", target_python)
            py_suffix = f"-py{py_version.group(1)}" if py_version else ""
            cache_filename = f".depchk-cache{py_suffix}.json"
        else:
            cache_filename = ".depchk-cache.json"

        cache_path = Path(pyproject_path).parent / cache_filename

        # Check if cache exists and is fresh
        if cache_path.exists():
            try:
                with open(cache_path) as f:
                    cache: dict[str, Any] = json.load(f)
                # Check cache freshness (24 hours) AND Python version match
                cache_time = datetime.fromisoformat(cache.get("timestamp", "2000-01-01"))
                cached_python = cache.get("python_version", "")
                if datetime.now() - cache_time < timedelta(hours=24):
                    if cached_python == python_req:
                        return cache
                    else:
                        logger.debug(
                            f"Cache invalidated: Python version changed "
                            f"({cached_python} -> {python_req})"
                        )
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}")

        # Build new cache for the packages we're analyzing
        # Convert Poetry Python constraint to PEP 440 for filtering
        if convert_poetry_to_pep440_func:
            pep440_constraint = convert_poetry_to_pep440_func(python_req)
        else:
            pep440_constraint = python_req

        cache = {
            "timestamp": datetime.now().isoformat(),
            "python_version": python_req,
            "packages": {},
            "vendor_constraints": vendor_constraints.get("packages", {}),
        }

        # Get all available versions for each package being analyzed
        # Filter by Python compatibility to ensure cache only contains compatible versions
        for pkg_name in packages:
            try:
                versions = await self.pypi_client.get_package_versions(
                    pkg_name, python_constraint=pep440_constraint
                )
                stable_versions = [v.version for v in versions if not v.is_prerelease()]

                if stable_versions:
                    cache["packages"][pkg_name] = {
                        "current": packages[pkg_name],
                        "available": stable_versions,
                        "latest": stable_versions[0],
                    }
            except Exception as e:
                logger.warning(f"Failed to cache versions for {pkg_name}: {e}")

        try:
            with open(cache_path, "w") as f:
                json.dump(cache, f, indent=2)
            logger.debug(f"Saved version cache to {cache_path}")
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")

        return cache

    @staticmethod
    def validate_versions(
        updates: dict[str, str],
        cache: dict[str, Any],
        find_closest_lower_func: Callable[[str, list[str]], str | None],
    ) -> dict[str, str]:
        validated = {}
        corrections = []

        for pkg, suggested in updates.items():
            # Extract version and operator
            match = re.search(r"([\^~>=<]*)([0-9.]+)", suggested)
            if not match:
                validated[pkg] = suggested
                continue

            operator = match.group(1) or "^"
            version = match.group(2)

            # Check if package is in cache
            if pkg not in cache.get("packages", {}):
                validated[pkg] = suggested
                continue

            available = cache["packages"][pkg].get("available", [])
            if not available:
                validated[pkg] = suggested
                continue

            # Validate version exists using normalized comparison
            # "23.0" and "23.0.0" are semantically equivalent
            try:
                target_v = Version(version)
                available_versions = [Version(v) for v in available]
                version_exists = target_v in available_versions
            except Exception:
                # Fallback to string comparison if parsing fails
                version_exists = version in available

            if version_exists:
                validated[pkg] = suggested
            else:
                # Find closest lower version
                closest = find_closest_lower_func(version, available)
                if closest:
                    corrected = f"{operator}{closest}"
                    validated[pkg] = corrected
                    corrections.append(f"{pkg}: {suggested} -> {corrected}")
                    logger.debug(f"Corrected {pkg}: {version} doesn't exist, using {closest}")
                else:
                    # Use latest
                    latest = cache["packages"][pkg]["latest"]
                    validated[pkg] = f"{operator}{latest}"
                    corrections.append(f"{pkg}: {suggested} -> {operator}{latest}")
                    logger.debug(f"Corrected {pkg}: using latest {latest}")

        return validated

    @staticmethod
    def validate_current_versions(
        dependencies: dict[str, str], cache: dict[str, Any]
    ) -> list[dict[str, str]]:
        warnings = []

        for pkg, spec in dependencies.items():
            # Skip local path dependencies
            if isinstance(spec, dict):
                continue

            # Extract version from spec (e.g., "^0.118.5" -> "0.118.5")
            match = re.search(r"([\^~>=<]*)([0-9.]+)", spec)
            if not match:
                continue

            operator = match.group(1)
            version = match.group(2)

            # Skip range-only constraints (< or > without ^ or ~)
            # These don't specify a single version to validate
            if operator in ("<", ">", "<=", ">=") and "^" not in spec and "~" not in spec:
                continue

            # Check if package is in cache
            if pkg not in cache.get("packages", {}):
                continue

            available = cache["packages"][pkg].get("available", [])
            if not available:
                continue

            # Check if current version exists
            # Use Version objects for comparison since "23.0" and "23.0.0" are equivalent
            try:
                current_v = Version(version)
                available_versions = [Version(v) for v in available]

                # Check if version exists (normalized comparison)
                if current_v in available_versions:
                    continue

                # Don't warn if version is older than our cache window
                oldest_cached = min(available_versions)
                if current_v < oldest_cached:
                    continue

                warnings.append(
                    {
                        "package": pkg,
                        "version": spec,
                        "extracted_version": version,
                        "message": f"Current version '{spec}' does not exist on PyPI",
                    }
                )
                logger.debug(f"{pkg}: Current version {version} not found on PyPI")
            except Exception as e:
                logger.debug(f"Could not compare versions for {pkg}: {e}")

        return warnings
