import re
from typing import Any

from chalkbox.logging.bridge import get_logger
from packaging.specifiers import SpecifierSet

from src.analyzer.cache import VersionCache
from src.analyzer.compatibility import CompatibilityChecker
from src.analyzer.constraints import ConstraintCollector
from src.analyzer.python_constraint import PythonConstraintCalculator
from src.analyzer.risk import RiskAssessor
from src.core.pypi_client import PyPIClient

logger = get_logger(__name__)


class Resolver:
    def __init__(self) -> None:
        self.pypi_client = PyPIClient()
        self.cache_manager = VersionCache(self.pypi_client)
        self.compatibility_checker = CompatibilityChecker()
        self.constraint_collector = ConstraintCollector()
        self.python_constraint_calc = PythonConstraintCalculator()

    async def check_python_compatibility_interactive(
        self,
        pyproject_path: str,
        target_python: str | None = None,
        ignore_local_deps: bool = False,
        json_output: bool = False,
    ) -> tuple[bool, dict[str, Any]]:
        return await self.compatibility_checker.check_python_compatibility_interactive(
            pyproject_path, target_python, ignore_local_deps, json_output
        )

    async def analyze_project(
        self,
        pyproject_path: str,
        target_python: str | None = None,
        config_data: dict[str, Any] | None = None,
        ignore_local_deps: bool = False,
    ) -> dict[str, Any]:
        if not config_data:
            raise ValueError("config_data is required")

        python_req = config_data["python_req"]
        original_python_req = config_data["original_python_req"]
        dependencies = config_data["dependencies"]
        dev_dependencies = config_data["dev_dependencies"]

        # PHASE 1: Collect local dependency constraints (skip if ignoring)
        vendor_constraints: dict[str, dict[str, str] | str | None]
        if ignore_local_deps:
            vendor_constraints = {"packages": {}, "python": None}
        else:
            vendor_constraints = await self.constraint_collector.collect_vendor_constraints(
                pyproject_path, dependencies, dev_dependencies
            )

        # Collect all packages to analyze
        important_packages: dict[str, str] = {}

        for name, spec in dependencies.items():
            if isinstance(spec, dict) and "path" in spec:
                continue  # Skip vendor/local path dependencies
            important_packages[name] = spec if isinstance(spec, str) else spec.get("version", "")

        # Add dev dependencies
        for name, spec in dev_dependencies.items():
            if name not in important_packages:
                important_packages[name] = (
                    spec if isinstance(spec, str) else spec.get("version", "")
                )

        # Build version cache for validation
        version_cache = await self.cache_manager.build_cache(
            pyproject_path,
            important_packages,
            python_req,
            vendor_constraints,
            target_python,
            convert_poetry_to_pep440_func=self.compatibility_checker.convert_poetry_to_pep440,
        )

        # Convert Poetry Python constraint to PEP 440 for PyPI client
        # (e.g., "^3.9.0" -> ">=3.9.0,<4.0.0")
        pep440_python_constraint = self.compatibility_checker.convert_poetry_to_pep440(python_req)

        # Get latest versions
        updates = {}
        for pkg_name, current_spec in important_packages.items():
            try:
                # Filter versions by Python compatibility
                # Pass the full python constraint (converted to PEP 440) to ensure
                # we only get package versions compatible with the ENTIRE Python range
                versions = await self.pypi_client.get_package_versions(
                    pkg_name, python_constraint=pep440_python_constraint
                )

                # Find best compatible version
                for v in versions[:10]:
                    if v.is_prerelease():
                        continue

                    # Check local dependency constraint
                    vendor_packages = vendor_constraints.get("packages")
                    if (
                        vendor_packages
                        and isinstance(vendor_packages, dict)
                        and pkg_name in vendor_packages
                    ):
                        vendor_limit = vendor_packages[pkg_name]
                        if not self.constraint_collector.version_satisfies_constraint(
                            v.version, vendor_limit, self._extract_version
                        ):
                            logger.debug(
                                f"Skipping {pkg_name} {v.version}:"
                                f" exceeds local dependency constraint {vendor_limit}"
                            )
                            continue

                    # Found a good version (Python compatibility checked by PyPI client)
                    operator = (
                        "^"
                        if current_spec.startswith("^")
                        else "~"
                        if current_spec.startswith("~")
                        else "^"
                    )
                    new_spec = f"{operator}{v.version}"

                    # Extract current version for comparison
                    current_version = self._extract_version(current_spec)

                    # Only add to updates if version actually changed
                    if v.version != current_version:
                        updates[pkg_name] = new_spec

                    break

            except Exception as e:
                logger.warning(f"Failed to check {pkg_name}: {e}")

        # All updates that passed PyPI validation, version constraints, and Python compatibility
        # are considered safe
        validation: dict[str, list[str] | dict[str, str]] = {
            "safe": list(updates.keys()),
            "unsafe": {},
        }

        # Validate current versions (warn about non-existent)
        current_version_warnings = []
        if version_cache and version_cache.get("packages"):
            all_deps = {**dependencies, **dev_dependencies}
            current_version_warnings = self.cache_manager.validate_current_versions(
                all_deps, version_cache
            )

        updates = self.cache_manager.validate_versions(
            updates, version_cache, self._find_closest_lower
        )

        final_updates = {}
        for pkg in validation.get("safe", []):
            if pkg in updates:
                final_updates[pkg] = updates[pkg]

        classifier_data: dict[str, dict[str, Any]] = {}
        for pkg_name in final_updates:
            try:
                # Extract version from update spec
                version_match = re.search(r"[\d.]+", final_updates[pkg_name])
                if version_match:
                    version = version_match.group()
                    json_info = await self.pypi_client.get_package_json_info(pkg_name, version)
                    if "error" not in json_info:
                        classifiers = json_info.get("info", {}).get("classifiers", [])
                        requires_python = json_info.get("info", {}).get("requires_python")
                        py_versions = self.pypi_client.extract_python_versions_from_classifiers(
                            classifiers
                        )
                        classifier_data[pkg_name] = {
                            "requires_python": requires_python,
                            "python_min": py_versions["min_version"],
                            "python_max": py_versions["max_version"],
                            "tested_versions": py_versions["tested_versions"],
                        }
            except Exception as e:
                logger.warning(f"Failed to fetch classifiers for {pkg_name}: {e}")

        python_constraints: dict[str, str] = {}
        for pkg_name in final_updates:
            if pkg_name in classifier_data:
                cd = classifier_data[pkg_name]
                requires_python = cd.get("requires_python")

                # Check if requires_python has an upper bound
                has_upper_bound = False
                if requires_python:
                    try:
                        spec = SpecifierSet(requires_python)
                        for s in spec:
                            if s.operator in ("<", "<="):
                                has_upper_bound = True
                                break
                    except Exception as e:
                        logger.debug(f"Failed to parse requires_python '{requires_python}': {e}")

                # If requires_python not available OR missing upper bound, construct from classifiers
                if (
                    (not requires_python or not has_upper_bound)
                    and cd.get("python_min")
                    and cd.get("python_max")
                ):
                    python_min = cd["python_min"]
                    python_max_str = cd["python_max"]
                    # python_max from classifiers is the highest TESTED version (e.g., "3.13")
                    # This means "supports up to and including 3.13" → "<3.14" in specifiers
                    try:
                        major, minor = python_max_str.split(".")
                        next_minor = int(minor) + 1
                        upper_bound = f"{major}.{next_minor}"
                        constructed = f">={python_min},<{upper_bound}"
                        logger.debug(
                            f"Constructed requires_python for {pkg_name} from classifiers: "
                            f"{constructed} (API had: {requires_python})"
                        )
                        requires_python = constructed
                    except (ValueError, AttributeError):
                        logger.debug(f"Could not parse python_max for {pkg_name}: {python_max_str}")
                        requires_python = None

                if requires_python and self.python_constraint_calc.needs_constraint(
                    requires_python, pep440_python_constraint
                ):
                    constraint = self.python_constraint_calc.calculate_constraint(
                        requires_python, pep440_python_constraint
                    )
                    # Only add constraint if calculation succeeded (None means impossible/invalid)
                    if constraint:
                        python_constraints[pkg_name] = constraint
                        logger.debug(f"Package {pkg_name} needs Python constraint: {constraint}")

        report = []
        for pkg_name, current_spec in important_packages.items():
            if pkg_name in final_updates:
                # Calculate risk assessment
                risk_info = {
                    "level": "UNKNOWN",
                    "score": 0,
                    "factors": [],
                    "version_jump": "unknown",
                }
                if pkg_name in classifier_data:
                    cd = classifier_data[pkg_name]
                    risk_info = RiskAssessor.assess_risk(
                        current_version=current_spec,
                        new_version=final_updates[pkg_name],
                        requires_python=cd.get("requires_python"),
                        python_max=cd.get("python_max"),
                        tested_versions=cd.get("tested_versions", []),
                        project_python=python_req,
                    )

                report.append(
                    {
                        "package": pkg_name,
                        "current": current_spec,
                        "status": "update",
                        "recommended": final_updates[pkg_name],
                        "reason": None,
                        "confidence_level": risk_info["level"],
                        "python_min": classifier_data.get(pkg_name, {}).get("python_min"),
                        "python_max": classifier_data.get(pkg_name, {}).get("python_max"),
                        "version_jump": risk_info["version_jump"],
                        "risk_factors": risk_info["factors"],
                        "requires_python": classifier_data.get(pkg_name, {}).get("requires_python"),
                        "python_constraint": python_constraints.get(pkg_name),
                    }
                )
            elif pkg_name in validation.get("unsafe", {}):
                # Type narrow: unsafe is dict[str, str]
                unsafe_dict: dict[str, str] = validation["unsafe"]  # type: ignore[assignment]
                report.append(
                    {
                        "package": pkg_name,
                        "current": current_spec,
                        "status": "skip",
                        "recommended": None,
                        "reason": unsafe_dict[pkg_name],
                        "confidence_level": "UNKNOWN",
                        "python_min": None,
                        "python_max": None,
                        "version_jump": "unknown",
                        "risk_factors": [],
                    }
                )
            else:
                # Package is up to date
                report.append(
                    {
                        "package": pkg_name,
                        "current": current_spec,
                        "status": "current",
                        "recommended": current_spec,
                        "reason": "Already at latest compatible version",
                        "confidence_level": "LOW",
                        "python_min": None,
                        "python_max": None,
                        "version_jump": "unknown",
                        "risk_factors": [],
                    }
                )

        return {
            "python": python_req,
            "original_python": original_python_req if target_python else None,
            "updates": final_updates,
            "skipped": validation.get("unsafe", {}),
            "report": report,
            "summary": {
                "analyzed": len(important_packages),
                "updated": len(final_updates),
                "skipped": len(validation.get("unsafe", {})),
            },
            "current_version_warnings": current_version_warnings,
            "python_constraints": python_constraints,
        }

    @staticmethod
    def _extract_version(spec: str) -> str:
        match = re.search(r"[\d.]+", spec)
        return match.group() if match else "0"

    @staticmethod
    def _find_closest_lower(target: str, versions: list[str]) -> str | None:
        def parse_numeric_version(v: str) -> tuple[int, ...] | None:
            parts = v.split(".")
            # Only accept strictly numeric segments to avoid ValueError
            if not parts or not all(p.isdigit() for p in parts):
                return None
            return tuple(int(p) for p in parts)

        target_t = parse_numeric_version(target)
        if target_t is None:
            # Log instead of pass
            logger.debug("Invalid target version (non-numeric): %s", target)
            return None

        lower: list[tuple[str, tuple[int, ...]]] = []
        for v in versions:
            v_t = parse_numeric_version(v)
            if v_t is None:
                logger.debug("Skipping invalid version (non-numeric): %s", v)
                continue
            if v_t < target_t:
                lower.append((v, v_t))

        if not lower:
            return None

        lower.sort(key=lambda x: x[1], reverse=True)
        return lower[0][0]
