import re
from typing import Any

from chalkbox.logging.bridge import get_logger

logger = get_logger(__name__)


class RiskAssessor:
    @staticmethod
    def parse_version(version_spec: str) -> tuple[int, int, int] | None:
        # Remove operators (^, ~, >=, etc.)
        clean_version = re.sub(r"^[\^~>=<]+", "", version_spec)

        # Extract version numbers
        match = re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", clean_version)
        if match:
            major = int(match.group(1))
            minor = int(match.group(2))
            patch = int(match.group(3)) if match.group(3) else 0
            return major, minor, patch

        return None

    @staticmethod
    def detect_version_jump(current_version: str, new_version: str) -> str:
        current = RiskAssessor.parse_version(current_version)
        new = RiskAssessor.parse_version(new_version)

        if not current or not new:
            return "unknown"

        curr_major, curr_minor, curr_patch = current
        new_major, new_minor, new_patch = new

        if new_major > curr_major:
            return "major"
        elif new_minor > curr_minor:
            return "minor"
        elif new_patch > curr_patch:
            return "patch"

        return "unknown"

    @staticmethod
    def calculate_jump_magnitude(current_version: str, new_version: str) -> int:
        current = RiskAssessor.parse_version(current_version)
        new = RiskAssessor.parse_version(new_version)

        if not current or not new:
            return 0

        curr_major, curr_minor, curr_patch = current
        new_major, new_minor, new_patch = new

        # Weight: major jumps count heavily, minor moderately, patch lightly
        major_diff = (new_major - curr_major) * 100
        minor_diff = (new_minor - curr_minor) * 10
        patch_diff = new_patch - curr_patch

        return max(0, major_diff + minor_diff + patch_diff)

    @staticmethod
    def is_python_requirement_broad(requires_python: str | None) -> bool:
        if not requires_python:
            return True  # No requirement = very broad

        # Extract minimum version
        match = re.search(r">=\s*(\d+)\.(\d+)", requires_python)
        if match:
            major = int(match.group(1))
            minor = int(match.group(2))

            # Python 3.6 and 3.7 are old; supporting them is "broad"
            if major == 3 and minor <= 7:
                return True

        return False

    @staticmethod
    def assess_risk(
        current_version: str,
        new_version: str,
        requires_python: str | None,
        python_max: str | None,
        tested_versions: list[str],
        project_python: str,
    ) -> dict[str, Any]:
        risk_score = 0
        risk_factors = []

        # 1. Version jump analysis
        jump_type = RiskAssessor.detect_version_jump(current_version, new_version)
        magnitude = RiskAssessor.calculate_jump_magnitude(current_version, new_version)

        if jump_type == "major":
            risk_score += 3
            risk_factors.append(f"Major version jump ({current_version} → {new_version})")
            if magnitude > 100:  # More than 1 major version
                risk_score += 1
                risk_factors.append("Multiple major versions skipped")
        elif jump_type == "minor":
            risk_score += 2
            risk_factors.append(f"Minor version jump ({current_version} → {new_version})")
            if magnitude > 50:  # More than 5 minor versions
                risk_score += 1
                risk_factors.append("Many minor versions skipped")
        elif jump_type == "patch":
            # Patch updates are generally safe
            pass

        # 2. Python compatibility analysis
        if RiskAssessor.is_python_requirement_broad(requires_python):
            risk_score += 2
            risk_factors.append(f"Broad Python requirement ({requires_python or 'not specified'})")

        # 3. Classifier validation
        if tested_versions:
            # Extract project's Python version
            project_py_match = re.search(r"(\d+)\.(\d+)", project_python)
            if project_py_match:
                project_py_version = f"{project_py_match.group(1)}.{project_py_match.group(2)}"

                if project_py_version not in tested_versions:
                    risk_score += 2
                    risk_factors.append(
                        f"Project Python {project_py_version}"
                        f" not in tested versions {tested_versions}"
                    )
        else:
            # No classifiers = less certainty
            risk_score += 1
            risk_factors.append("No Python version classifiers found")

        # 4. Upper bound check
        if not python_max:
            risk_score += 1
            risk_factors.append("No maximum Python version specified")

        # Determine risk level
        if risk_score >= 5:
            level = "HIGH"
        elif risk_score >= 3:
            level = "MEDIUM"
        else:
            level = "LOW"

        return {
            "level": level,
            "score": risk_score,
            "factors": risk_factors,
            "version_jump": jump_type,
            "magnitude": magnitude,
        }
