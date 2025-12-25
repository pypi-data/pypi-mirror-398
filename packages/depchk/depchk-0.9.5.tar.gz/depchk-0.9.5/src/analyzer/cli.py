import argparse
from importlib.metadata import version
from pathlib import Path
import re
import sys
import tomllib
from typing import Any

from chalkbox.core.console import get_console
from chalkbox.logging.bridge import get_logger

logger = get_logger(__name__)
console = get_console()


class CLIHandler:
    def __init__(self, config_filename: str = "pyproject.toml") -> None:
        self.config_filename = config_filename

    def create_argument_parser(self, description: str) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            description=description,
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

        parser.add_argument(
            "--version",
            action="version",
            version=f"%(prog)s {version('depchk')}",
        )

        parser.add_argument(
            "file",
            nargs="?",
            help=f"Path to {self.config_filename} (defaults to current directory)",
        )
        parser.add_argument(
            "--update-source-file",
            action="store_true",
            help=f"Update the {self.config_filename} file with recommended versions",
        )
        parser.add_argument("--json", action="store_true", help="Output results as JSON")
        parser.add_argument("--verbose", action="store_true", help="Show debug information")

        self.add_custom_arguments(parser)

        return parser

    @staticmethod
    def add_custom_arguments(parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--allow-prerelease",
            action="store_true",
            help="Include pre-release versions in analysis",
        )
        parser.add_argument(
            "--target-python",
            type=str,
            default=None,
            help="Target Python version for analysis (overrides pyproject.toml), e.g., '^3.13'",
        )
        parser.add_argument(
            "--ignore-local-deps",
            action="store_true",
            help="Ignore local path dependencies and their version constraints",
        )
        parser.add_argument(
            "--skip-python-constraints",
            action="store_true",
            help="Skip automatic Python constraint application (default: apply constraints)",
        )

    @staticmethod
    def validate_flag_combinations(args: argparse.Namespace) -> tuple[bool, str | None]:
        if args.json and args.verbose:
            return False, "--json and --verbose are mutually exclusive"
        return True, None

    @staticmethod
    def validate_target_python(target_python: str) -> tuple[bool, str | None]:
        match = re.search(r"(\d+)\.(\d+)", target_python)
        if not match:
            return False, f"Invalid Python version format: {target_python}"

        major = int(match.group(1))
        minor = int(match.group(2))

        # Python version status mapping (source: https://devguide.python.org/versions/)
        # Last updated: October 2025
        #
        # Status definitions:
        # - feature: Pre-release, accepting new features (packages may already support it)
        # - pre-release: Beta/RC phase, no new features
        # - bugfix: Stable release, accepts bug fixes
        # - security: Maintenance mode, security fixes only
        # - end-of-life: No longer supported
        python_status = {
            (3, 15): "feature",  # PEP 790 - Feature phase until 2026-05
            (3, 14): "bugfix",  # PEP 745 - Released 2025-10-07, bugfix until 2026-10
            (3, 13): "bugfix",  # PEP 719 - Released 2024-10-07, bugfix until 2025-10
            (3, 12): "security",  # PEP 693 - Released 2023-10-02, security until 2028-10
            (3, 11): "security",  # PEP 664 - Released 2022-10-24, security until 2027-10
            (3, 10): "security",  # PEP 619 - Released 2021-10-04, security until 2026-10
            (3, 9): "security",  # PEP 596 - Released 2020-10-05, security until 2025-10
            (3, 8): "end-of-life",  # PEP 569 - EOL 2024-10-07
            (3, 7): "end-of-life",  # PEP 537 - EOL 2023-06-27
        }

        min_python = (3, 8)
        max_python = (3, 15)

        version_tuple = (major, minor)

        if version_tuple < min_python:
            return (
                False,
                f"Python {major}.{minor} is too old"
                f" (minimum supported: {min_python[0]}.{min_python[1]})",
            )

        if version_tuple > max_python:
            return (
                False,
                f"Python {major}.{minor} is not yet released or supported.\n"
                f"Latest supported: {max_python[0]}.{max_python[1]}"
                f" ({python_status.get(max_python, 'unknown')} phase)\n"
                f"Supported range: {min_python[0]}.{min_python[1]} -"
                f" {max_python[0]}.{max_python[1]}",
            )

        status = python_status.get(version_tuple)
        if not status:
            # Version number exists but not in our map - likely future version
            return (
                False,
                f"Python {major}.{minor} is not tracked in our support matrix.\n"
                f"Supported range: {min_python[0]}.{min_python[1]} -"
                f" {max_python[0]}.{max_python[1]}",
            )

        return True, None

    @staticmethod
    def compare_python_versions(
        target_python: str, project_python: str
    ) -> tuple[str | None, str | None]:
        target_match = re.search(r"(\d+)\.(\d+)", target_python)
        if not target_match:
            return None, None

        target_major = int(target_match.group(1))
        target_minor = int(target_match.group(2))
        target_tuple = (target_major, target_minor)

        # Parse project Python requirement (handles various formats)
        # Examples: "^3.12", ">=3.9,<3.13", ">=3.10", "~3.11"

        # Extract minimum version (>=, ^, ~)
        min_match = re.search(r"(?:>=|[\^~])(\d+)\.(\d+)", project_python)
        if min_match:
            min_major = int(min_match.group(1))
            min_minor = int(min_match.group(2))
            min_tuple = (min_major, min_minor)
        else:
            min_tuple = None

        # Extract maximum version (<)
        max_match = re.search(r"<(\d+)\.(\d+)", project_python)
        if max_match:
            max_major = int(max_match.group(1))
            max_minor = int(max_match.group(2))
            max_tuple = (max_major, max_minor)
        else:
            max_tuple = None

        # Check if target is below minimum
        if min_tuple and target_tuple < min_tuple:
            return (
                f"Target Python {target_major}.{target_minor} is BELOW project's"
                f" minimum requirement (>={min_tuple[0]}.{min_tuple[1]}).\n"
                f"Recommended packages may not work with your project!",
                "below_minimum",
            )

        # Check if target is at or above maximum
        if max_tuple and target_tuple >= max_tuple:
            return (
                f"Target Python {target_major}.{target_minor} is AT OR ABOVE project's"
                f" maximum limit (<{max_tuple[0]}.{max_tuple[1]}).\n"
                f"Recommended packages may not be compatible with your project's"
                f" Python constraint!",
                "above_maximum",
            )

        return None, None

    def find_config_file(self, file_arg: str | None = None, json_output: bool = False) -> Path:
        if file_arg:
            config_path = Path(file_arg)
        else:
            # Look in current and parent directories
            for path in [Path.cwd(), Path.cwd().parent]:
                candidate = path / self.config_filename
                if candidate.exists():
                    config_path = candidate
                    break
            else:
                if not json_output:
                    console.print(
                        f"[red]Error: Could not find {self.config_filename}"
                        " in current or parent directory[/red]"
                    )
                sys.exit(1)

        if not config_path.exists():
            if not json_output:
                console.print(
                    f"[red]Error: {self.config_filename} not found at {config_path}[/red]"
                )
            sys.exit(1)

        return config_path.resolve()

    @staticmethod
    async def load_config_file(path: Path) -> dict[str, Any]:
        with open(path, "rb") as f:
            return tomllib.load(f)
