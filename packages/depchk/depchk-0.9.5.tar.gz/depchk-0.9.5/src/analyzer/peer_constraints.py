import re
from typing import Any

from chalkbox.logging.bridge import get_logger
from packaging.specifiers import InvalidSpecifier, SpecifierSet
from packaging.version import Version

from src.core.pypi_client import PyPIClient

logger = get_logger(__name__)


class PeerConstraintCollector:
    """Collects dependency constraints from project packages via PyPI requires_dist."""

    def __init__(self, pypi_client: PyPIClient) -> None:
        self.pypi_client = pypi_client

    async def collect_peer_constraints(
        self,
        dependencies: dict[str, Any],
        dev_dependencies: dict[str, Any],
    ) -> dict[str, list[dict[str, str]]]:
        """
        Collect peer dependency constraints from all project packages.

        Fetches requires_dist from PyPI for each dependency to build a map of
        which packages constrain which other packages."""
        peer_constraints: dict[str, list[dict[str, str]]] = {}

        all_deps = {**dependencies, **dev_dependencies}

        for pkg_name, spec in all_deps.items():
            # Skip local path dependencies
            if isinstance(spec, dict) and "path" in spec:
                continue

            # Get the current version spec
            current_spec = spec if isinstance(spec, str) else spec.get("version", "")
            if not current_spec:
                continue

            # Extract version from spec to fetch correct requires_dist
            version = self._extract_version(current_spec)
            if not version:
                continue

            try:
                json_info = await self.pypi_client.get_package_json_info(pkg_name, version)
                if "error" in json_info:
                    logger.debug(f"Could not fetch info for {pkg_name} {version}")
                    continue

                requires_dist = json_info.get("info", {}).get("requires_dist") or []

                for req in requires_dist:
                    parsed = self._parse_requires_dist(req)
                    if not parsed:
                        continue

                    req_name, constraint = parsed

                    normalized_name = self.pypi_client.normalize_name(req_name)

                    # Only track constraints on packages that are also in the project
                    if normalized_name not in [
                        self.pypi_client.normalize_name(n) for n in all_deps
                    ]:
                        continue

                    # Add to peer constraints
                    if normalized_name not in peer_constraints:
                        peer_constraints[normalized_name] = []

                    peer_constraints[normalized_name].append(
                        {
                            "dependent": pkg_name,
                            "constraint": constraint,
                            "spec": current_spec,
                        }
                    )
                    logger.debug(
                        f"Found peer constraint: {pkg_name} requires {req_name} {constraint}"
                    )

            except Exception as e:
                logger.debug(f"Failed to fetch requires_dist for {pkg_name}: {e}")

        return peer_constraints

    def check_conflicts(
        self,
        package: str,
        version: str,
        peer_constraints: dict[str, list[dict[str, str]]],
    ) -> list[dict[str, str]]:
        """Check if a package version conflicts with any peer constraints."""
        normalized = self.pypi_client.normalize_name(package)
        constraints = peer_constraints.get(normalized, [])

        conflicts = []
        for constraint_info in constraints:
            constraint = constraint_info["constraint"]

            if self._version_violates_constraint(version, constraint):
                conflicts.append(constraint_info)
                logger.debug(
                    f"Conflict: {version} violates {constraint} "
                    f"(required by {constraint_info['dependent']})"
                )

        return conflicts

    @staticmethod
    def _extract_version(spec: str) -> str | None:
        match = re.search(r"[\d.]+", spec)
        return match.group() if match else None

    @staticmethod
    def _parse_requires_dist(entry: str) -> tuple[str, str] | None:
        """Parse a requires_dist entry into (package_name, constraint).

        Handles formats like:
        - "mdformat>=0.7.5,<0.8.0"
        - "setuptools>=45"
        - "pytest~=6.0; extra == 'test'"
        - "package[extra]>=1.0"

        Ignores dependencies that are only for extras (e.g., test, dev)!
        """
        # Check for environment markers
        if ";" in entry:
            pkg_spec, marker = entry.split(";", 1)
            pkg_spec = pkg_spec.strip()
            marker = marker.strip().lower()

            # Skip if this is an extra-only dependency
            if "extra" in marker:
                return None
        else:
            pkg_spec = entry

        # Match package name (with optional extras) and constraint
        match = re.match(r"([a-zA-Z0-9_-]+)(?:\[[^\]]+\])?\s*(.*)", pkg_spec)
        if not match:
            return None

        name = match.group(1)
        constraint = match.group(2).strip()

        # If no constraint, it means any version
        if not constraint:
            return None  # Can't conflict if no constraint

        return name, constraint

    @staticmethod
    def _version_violates_constraint(version: str, constraint: str) -> bool:
        """Check if a version violates a PEP 440 constraint."""
        try:
            spec = SpecifierSet(constraint)
            ver = Version(version)
            return ver not in spec
        except (InvalidSpecifier, Exception) as e:
            logger.debug(f"Could not parse constraint '{constraint}': {e}")
            return False  # Can't determine, assume no conflict
