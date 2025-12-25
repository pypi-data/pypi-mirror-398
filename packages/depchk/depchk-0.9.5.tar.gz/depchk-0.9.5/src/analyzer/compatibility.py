from pathlib import Path
import re
import tomllib
from typing import Any

from chalkbox.logging.bridge import get_logger
from packaging.specifiers import SpecifierSet
from packaging.version import Version

from src.utils.prompt import PromptHandler

logger = get_logger(__name__)


class CompatibilityChecker:
    @staticmethod
    def parse_python_version(version_spec: str) -> tuple[int, int]:
        match = re.search(r"(\d+)\.(\d+)", version_spec)
        if match:
            return int(match.group(1)), int(match.group(2))
        return (3, 8)  # Default fallback

    @staticmethod
    def convert_poetry_to_pep440(python_spec: str) -> str:
        """
        Convert Poetry Python constraint to PEP 440 specifier.

        Examples:
            ^3.9.0      -> >=3.9.0,<4.0.0
            ^3.12       -> >=3.12.0,<4.0.0
            ~3.11       -> >=3.11.0,<3.12.0
            3.9         -> >=3.9.0,<4.0.0 (bare version treated as caret)
            >=3.9,<3.13 -> >=3.9,<3.13 (unchanged)
        """
        spec_str = python_spec

        # Handle Poetry caret operator (^)
        if python_spec.startswith("^"):
            # ^3.9.0 means >=3.9.0,<4.0.0
            match = re.search(r"\^(\d+)\.(\d+)", python_spec)
            if match:
                major, minor = match.groups()
                next_major = int(major) + 1
                spec_str = f">={major}.{minor}.0,<{next_major}.0.0"

        # Handle Poetry tilde operator (~)
        elif python_spec.startswith("~"):
            # ~3.11 means >=3.11.0,<3.12.0
            match = re.search(r"~(\d+)\.(\d+)", python_spec)
            if match:
                major, minor = match.groups()
                next_minor = int(minor) + 1
                spec_str = f">={major}.{minor}.0,<{major}.{next_minor}.0"

        # Handle bare version (e.g., "3.9" or "3.9.0") - treat like caret
        elif re.match(r"^\d+\.\d+(\.\d+)?$", python_spec):
            match = re.match(r"^(\d+)\.(\d+)", python_spec)
            if match:
                major, minor = match.groups()
                next_major = int(major) + 1
                spec_str = f">={major}.{minor}.0,<{next_major}.0.0"

        return spec_str

    @staticmethod
    def get_latest_compatible_python(python_spec: str) -> str:
        """
        Get the latest compatible Python version from a Poetry constraint.

        Examples:
            ^3.9.0      -> 3.13 (latest stable < 4.0)
            >=3.9,<3.13 -> 3.12
            ~3.11       -> 3.11 (same minor, latest patch)
            >=3.10      -> 3.13 (latest stable)
        """
        # Available Python versions (source: https://devguide.python.org/versions/)
        # As of October 2025
        available_versions = ["3.8", "3.9", "3.10", "3.11", "3.12", "3.13", "3.14"]

        # Convert Poetry constraint to PEP 440 specifier
        spec_str = CompatibilityChecker.convert_poetry_to_pep440(python_spec)

        # Try to parse as PEP 440 specifier
        try:
            spec = SpecifierSet(spec_str)

            # Find latest compatible version
            compatible = []
            for v in available_versions:
                try:
                    if Version(v) in spec:
                        compatible.append(v)
                except Exception:
                    continue

            if compatible:
                return compatible[-1]  # Return latest
        except Exception as e:
            logger.debug(f"Failed to parse Python spec '{python_spec}': {e}")

        # Fallback: extract first version number found
        match = re.search(r"(\d+)\.(\d+)", python_spec)
        if match:
            return match.group(1) + "." + match.group(2)

        return "3.9"  # Safe default fallback

    async def check_python_compatibility_interactive(
        self,
        pyproject_path: str,
        target_python: str | None = None,
        ignore_local_deps: bool = False,
        json_output: bool = False,
    ) -> tuple[bool, dict[str, Any]]:
        with open(pyproject_path, "rb") as f:
            pyproject_data = tomllib.load(f)

        poetry = pyproject_data.get("tool", {}).get("poetry", {})
        dependencies = poetry.get("dependencies", {})
        dev_dependencies = poetry.get("dev-dependencies", {})
        if not dev_dependencies and "group" in poetry:
            dev_dependencies = poetry.get("group", {}).get("dev", {}).get("dependencies", {})
        python_req = dependencies.pop("python", "^3.8")

        original_python_req = python_req
        if target_python:
            python_req = target_python

        # Python Version Pre-Check (skip if ignoring local deps)
        if ignore_local_deps:
            python_compat = {"action": "continue", "message": "+ Skipping local dependency checks"}
        else:
            python_compat = await self.check_python_compatibility(
                pyproject_path, dependencies, dev_dependencies, python_req
            )

        # Handle the compatibility check result
        if python_compat["action"] == "abort":
            return (
                False,
                {
                    "aborted": True,
                    "reason": python_compat["message"],
                    "python": python_req,
                    "original_python": original_python_req if target_python else None,
                    "vendor_python": python_compat.get("vendor_python"),
                },
            )
        elif python_compat["action"] == "prompt":
            # Interactive prompt for user (no spinner running)
            if not self.prompt_python_upgrade(python_compat):
                return (
                    False,
                    {
                        "aborted": True,
                        "reason": "Analysis cancelled by user",
                        "python": python_req,
                        "original_python": original_python_req if target_python else None,
                        "vendor_python": python_compat.get("vendor_python"),
                    },
                )
        elif python_compat["action"] == "info" and not json_output:
            print(f"\n{python_compat['message']}\n")

        # User approved or no conflict - proceed with analysis
        return (
            True,
            {
                "pyproject_data": pyproject_data,
                "python_req": python_req,
                "original_python_req": original_python_req,
                "dependencies": dependencies,
                "dev_dependencies": dev_dependencies,
                "target_python": target_python,
            },
        )

    async def check_python_compatibility(
        self,
        pyproject_path: str,
        dependencies: dict[str, Any],
        dev_dependencies: dict[str, Any],
        main_python: str,
    ) -> dict[str, Any]:
        """Check Python version compatibility between main project and local path dependencies."""
        vendor_pythons = []

        all_deps = {**dependencies, **dev_dependencies}
        for name, spec in all_deps.items():
            if isinstance(spec, dict) and "path" in spec:
                vendor_path = Path(pyproject_path).parent / spec["path"]
                vendor_python = await self.get_vendor_python(vendor_path)
                if vendor_python:
                    vendor_pythons.append((name, vendor_python))

        if not vendor_pythons:
            return {
                "action": "continue",
                "message": "+ No local path dependencies found",
                "effective_python": main_python,
            }

        main_ver = self.parse_python_version(main_python)

        # Find the most restrictive (highest) vendor Python version
        max_vendor = None
        max_vendor_ver = main_ver

        for vendor_name, vendor_python in vendor_pythons:
            vendor_ver = self.parse_python_version(vendor_python)
            if vendor_ver > max_vendor_ver:
                max_vendor_ver = vendor_ver
                max_vendor = (vendor_name, vendor_python)

        # Check if all vendors have the same Python requirement
        all_same = len({vp for _, vp in vendor_pythons}) == 1

        if max_vendor:
            # Local dependency requires higher Python than main project
            vendor_list = ", ".join([f"{n}: {p}" for n, p in vendor_pythons])
            return {
                "action": "prompt",
                "message": f"! Local dependency '{max_vendor[0]}' requires Python"
                f" {max_vendor[1]}, but main project has {main_python}",
                "details": f"Local dependency Python requirements: {vendor_list}",
                "main_python": main_python,
                "vendor_python": max_vendor[1],
                "effective_python": max_vendor[1],
                "prompt": f"\nThe dependency resolution will target Python"
                f" {max_vendor[1]} to satisfy local dependency requirements."
                f"\nThis means some packages may require features"
                f" only available in Python {max_vendor_ver}+."
                f"\n\nDo you want to proceed? (y/n): ",
            }
        elif all_same and vendor_pythons[0][1] == main_python:
            # All versions match perfectly
            return {
                "action": "info",
                "message": "+ Python versions aligned:"
                f" main project and all local dependencies use Python {main_python}",
                "effective_python": main_python,
            }
        else:
            # Main project has higher Python than local dependencies (this is fine)
            return {
                "action": "info",
                "message": (
                    "  Main project Python"
                    f" {main_python} is compatible with all local dependency requirements"
                ),
                "effective_python": main_python,
            }

    @staticmethod
    async def get_vendor_python(vendor_path: Path) -> str | None:
        pyproject_path = vendor_path / "pyproject.toml"
        if not pyproject_path.exists():
            return None

        try:
            with open(pyproject_path, "rb") as f:
                vendor_data: dict[str, Any] = tomllib.load(f)

            poetry = vendor_data.get("tool", {}).get("poetry", {})
            deps = poetry.get("dependencies", {})
            python_req: str | None = deps.get("python")
            return python_req

        except Exception as e:
            logger.warning(f"Failed to read vendor Python from {vendor_path}: {e}")
            return None

    @staticmethod
    def prompt_python_upgrade(python_compat: dict[str, Any]) -> bool:
        return PromptHandler.prompt_with_fallback(python_compat, default_action="continue")
