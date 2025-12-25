from collections.abc import Callable
from pathlib import Path
import re
import tomllib
from typing import Any

from chalkbox.logging.bridge import get_logger

logger = get_logger(__name__)


class ConstraintCollector:
    @staticmethod
    def extract_version(spec: str) -> str:
        match = re.search(r"[\d.]+", spec)
        return match.group() if match else "0"

    async def collect_vendor_constraints(
        self, pyproject_path: str, dependencies: dict[str, Any], dev_dependencies: dict[str, Any]
    ) -> dict[str, Any]:
        """Collect local path dependency constraints to establish version ceilings."""
        packages: dict[str, str] = {}
        python_constraint: str | None = None

        vendor_constraints: dict[str, Any] = {"packages": packages, "python": python_constraint}

        all_deps = {**dependencies, **dev_dependencies}
        vendor_paths = []

        for name, spec in all_deps.items():
            if isinstance(spec, dict) and "path" in spec:
                vendor_path = Path(pyproject_path).parent / spec["path"]
                if vendor_path.exists():
                    vendor_paths.append((name, vendor_path))

        if not vendor_paths:
            return vendor_constraints

        for _vendor_name, vendor_path in vendor_paths:
            constraints = await self.get_vendor_constraints(vendor_path)

            # Merge constraints, using most restrictive version
            for pkg, version_spec in constraints.items():
                if pkg == "python":
                    # Track Python requirement
                    current_python = vendor_constraints.get("python")
                    if current_python is None:
                        vendor_constraints["python"] = version_spec
                    elif isinstance(current_python, str) and version_spec < current_python:
                        # Use more restrictive Python version
                        vendor_constraints["python"] = version_spec
                else:
                    # For packages, use most restrictive
                    packages_dict = vendor_constraints["packages"]
                    if isinstance(packages_dict, dict):
                        if pkg not in packages_dict:
                            packages_dict[pkg] = version_spec
                        else:
                            # Compare and use lower version
                            existing = self.extract_version(packages_dict[pkg])
                            new = self.extract_version(version_spec)
                            if new < existing:
                                packages_dict[pkg] = version_spec

        return vendor_constraints

    @staticmethod
    async def get_vendor_constraints(vendor_path: Path) -> dict[str, str]:
        pyproject_path = vendor_path / "pyproject.toml"
        if not pyproject_path.exists():
            return {}

        try:
            with open(pyproject_path, "rb") as f:
                vendor_data = tomllib.load(f)

            poetry = vendor_data.get("tool", {}).get("poetry", {})
            deps = poetry.get("dependencies", {})
            deps.update(poetry.get("dev-dependencies", {}))
            if "group" in poetry:
                deps.update(poetry.get("group", {}).get("dev", {}).get("dependencies", {}))

            result = {}
            for k, v in deps.items():
                if isinstance(v, str):
                    result[k] = v
            return result

        except Exception as e:
            logger.warning(f"Failed to read vendor {vendor_path}: {e}")
            return {}

    @staticmethod
    def version_satisfies_constraint(
        version: str, constraint: str, extract_version_func: Callable[[str], str]
    ) -> bool:
        constraint_ver = extract_version_func(constraint)

        # For ^ operator, version must be less than next major
        if constraint.startswith("^"):
            major = constraint_ver.split(".")[0]
            next_major = str(int(major) + 1)
            return version < next_major + ".0.0"

        # For ~ operator, version must be less than next minor
        if constraint.startswith("~"):
            parts = constraint_ver.split(".")
            if len(parts) >= 2:
                major, minor = parts[0], parts[1]
                next_minor = f"{major}.{int(minor) + 1}.0"
                return version < next_minor

        # Simple comparison
        return version <= constraint_ver
