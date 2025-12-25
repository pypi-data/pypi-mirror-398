from chalkbox.logging.bridge import get_logger
from packaging.specifiers import SpecifierSet
from packaging.version import Version

logger = get_logger(__name__)


class PythonConstraintCalculator:
    @staticmethod
    def needs_constraint(
        package_requires_python: str | None,
        project_python_constraint: str,
    ) -> bool:
        if not package_requires_python:
            return False

        try:
            pkg_spec = SpecifierSet(package_requires_python)
            proj_spec = SpecifierSet(project_python_constraint)

            pkg_upper = _extract_upper_bound(pkg_spec)
            proj_upper = _extract_upper_bound(proj_spec)
            proj_lower = _extract_lower_bound(proj_spec)

            # Check if there's actual overlap between ranges
            # If pkg_upper <= proj_lower, there's no overlap (impossible constraint)
            if pkg_upper and Version(pkg_upper) <= Version(proj_lower):
                logger.debug(
                    f"No overlap: package upper ({pkg_upper}) <= project lower ({proj_lower})"
                )
                return False

            # Only need a constraint if package upper < project upper
            if pkg_upper and proj_upper:
                return Version(pkg_upper) < Version(proj_upper)

            return False

        except Exception as e:
            logger.debug(f"Failed to parse Python constraints: {e}")
            return False

    @staticmethod
    def calculate_constraint(
        package_requires_python: str,
        project_python_constraint: str,
    ) -> str | None:
        try:
            pkg_spec = SpecifierSet(package_requires_python)
            proj_spec = SpecifierSet(project_python_constraint)

            pkg_lower = _extract_lower_bound(pkg_spec)
            proj_lower = _extract_lower_bound(proj_spec)
            lower = max(Version(pkg_lower), Version(proj_lower))

            pkg_upper = _extract_upper_bound(pkg_spec)
            proj_upper = _extract_upper_bound(proj_spec)

            # If either upper bound is None, use a very high version as default
            if pkg_upper is None and proj_upper is None:
                return f">={lower}"
            if pkg_upper is None:
                upper = Version(proj_upper)  # type: ignore[arg-type]
            elif proj_upper is None:
                upper = Version(pkg_upper)
            else:
                upper = min(Version(pkg_upper), Version(proj_upper))

            # Validate that the constraint is possible (lower < upper)
            if lower >= upper:
                logger.debug(f"Impossible constraint: lower ({lower}) >= upper ({upper}), skipping")
                return None

            return f">={lower},<{upper}"

        except Exception as e:
            logger.warning(f"Failed to calculate constraint intersection: {e}")
            return None


def _extract_upper_bound(spec: SpecifierSet) -> str | None:
    """Extract upper bound from SpecifierSet (e.g., '<4.0' → '4.0')."""
    for s in spec:
        if s.operator in ("<", "<="):
            return str(s.version)
    return None


def _extract_lower_bound(spec: SpecifierSet) -> str:
    """Extract lower bound from SpecifierSet (e.g., '>=3.9' → '3.9')."""
    for s in spec:
        if s.operator in (">=", ">"):
            return str(s.version)
    return "3.8"
