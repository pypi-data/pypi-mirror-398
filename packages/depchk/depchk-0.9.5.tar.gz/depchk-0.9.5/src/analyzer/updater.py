from pathlib import Path

from chalkbox.components.alert import Alert
from chalkbox.components.section import Section
from chalkbox.core.console import get_console
from chalkbox.logging.bridge import get_logger
import tomlkit

from src.analyzer.reporter import ReportGenerator
from src.core.models import ArgumentConfig

console = get_console()
logger = get_logger(__name__)


class FileUpdater:
    @staticmethod
    def get_backup_extension() -> str:
        return ".backup.toml"

    @staticmethod
    def get_updated_extension() -> str:
        return ".updated.toml"

    def generate_updated_content(
        self,
        content: str,
        updates: dict[str, str],
        python_constraints: dict[str, str] | None = None,
        verbose: bool = False,
        json_output: bool = False,
    ) -> tuple[str, int]:
        """
        Generate updated pyproject.toml content using tomlkit for safe AST-based updates.

        This preserves comments, formatting, and structure while updating version specs.
        """
        # Parse TOML with tomlkit to preserve formatting
        doc = tomlkit.parse(content)
        update_count = 0

        # Navigate to Poetry dependencies sections
        try:
            poetry_section = doc.get("tool", {}).get("poetry", {})

            for pkg, new_version in updates.items():
                # Handle __dev suffix
                actual_pkg = pkg.replace("__dev", "")

                updated_this_pkg = False

                # Check regular dependencies
                if "dependencies" in poetry_section:
                    deps = poetry_section["dependencies"]
                    if actual_pkg in deps:
                        old_value = deps[actual_pkg]

                        # Extract old version string safely
                        if isinstance(old_value, dict):
                            if "version" in old_value:
                                old_version_str = old_value["version"]
                            elif "git" in old_value or "path" in old_value:
                                # Git or path dependency - extract tag/branch as version hint
                                old_version_str = old_value.get(
                                    "tag", old_value.get("branch", "(non-versioned)")
                                )
                            else:
                                old_version_str = "(unknown)"
                        else:
                            old_version_str = old_value

                        new_python: str | None = None
                        if python_constraints and pkg in python_constraints:
                            new_python = python_constraints[pkg]

                        # Skip constraints for local path dependencies
                        if (
                            isinstance(old_value, dict)
                            and "path" in old_value
                            and pkg in (python_constraints or {})
                        ):
                            logger.debug(
                                f"Skipping Python constraint for local dependency: {actual_pkg}"
                            )
                            new_python = None

                        if isinstance(old_value, dict) and "version" in old_value:
                            old_value["version"] = new_version

                            if new_python:
                                if "python" in old_value:
                                    if not json_output:
                                        console.print(
                                            f"[yellow]Note: {actual_pkg} has existing Python "
                                            f"constraint '{old_value['python']}', preserving it[/yellow]"
                                        )
                                else:
                                    old_value["python"] = new_python
                                    if verbose and not json_output:
                                        console.print(
                                            f"  [dim]Added Python constraint to {actual_pkg}: {new_python}[/dim]"
                                        )
                        else:
                            if new_python:
                                deps[actual_pkg] = {"version": new_version, "python": new_python}
                                if verbose and not json_output:
                                    console.print(
                                        f"  [dim]Converted {actual_pkg} to table format with "
                                        f"Python constraint: {new_python}[/dim]"
                                    )
                            else:
                                deps[actual_pkg] = new_version

                        update_count += 1
                        updated_this_pkg = True

                        if verbose and not json_output:
                            self._log_update(
                                actual_pkg, new_version, old_version_str, "dependencies"
                            )

                # Check dev dependencies
                if (
                    "group" in poetry_section
                    and "dev" in poetry_section["group"]
                    and "dependencies" in poetry_section["group"]["dev"]
                ):
                    dev_deps = poetry_section["group"]["dev"]["dependencies"]
                    if actual_pkg in dev_deps:
                        old_value = dev_deps[actual_pkg]

                        # Extract old version string safely
                        if isinstance(old_value, dict):
                            if "version" in old_value:
                                old_version_str = old_value["version"]
                            elif "git" in old_value or "path" in old_value:
                                old_version_str = old_value.get(
                                    "tag", old_value.get("branch", "(non-versioned)")
                                )
                            else:
                                old_version_str = "(unknown)"
                        else:
                            old_version_str = old_value

                        # Handle inline table format
                        if isinstance(old_value, dict) and "version" in old_value:
                            old_value["version"] = new_version
                        else:
                            dev_deps[actual_pkg] = new_version
                        if not updated_this_pkg:  # Only count once
                            update_count += 1
                            updated_this_pkg = True

                        if verbose and not json_output:
                            self._log_update(
                                actual_pkg, new_version, old_version_str, "dev-dependencies"
                            )

                # Also check old-style dev-dependencies section
                if "dev-dependencies" in poetry_section:
                    dev_deps = poetry_section["dev-dependencies"]
                    if actual_pkg in dev_deps:
                        old_value = dev_deps[actual_pkg]

                        # Extract old version string safely
                        if isinstance(old_value, dict):
                            if "version" in old_value:
                                old_version_str = old_value["version"]
                            elif "git" in old_value or "path" in old_value:
                                old_version_str = old_value.get(
                                    "tag", old_value.get("branch", "(non-versioned)")
                                )
                            else:
                                old_version_str = "(unknown)"
                        else:
                            old_version_str = old_value

                        # Handle inline table format
                        if isinstance(old_value, dict) and "version" in old_value:
                            old_value["version"] = new_version
                        else:
                            dev_deps[actual_pkg] = new_version
                        if not updated_this_pkg:  # Only count once
                            update_count += 1

                        if verbose and not json_output:
                            self._log_update(
                                actual_pkg, new_version, old_version_str, "dev-dependencies"
                            )

        except Exception as e:
            console.print(Alert.error(f"Failed to parse TOML with tomlkit: {e}"))

        # Convert back to string (preserves formatting and comments)
        updated_content = tomlkit.dumps(doc)
        return updated_content, update_count

    @staticmethod
    def _log_update(pkg: str, new_version: str, old_value: str, section: str) -> None:
        console.print(f"  [dim]Updated {pkg} in [{section}]: {old_value} -> {new_version}[/dim]")

    async def apply_updates(
        self,
        config_path: str,
        updates: dict[str, str],
        python_constraints: dict[str, str] | None,
        args: ArgumentConfig,
    ) -> None:
        with open(config_path) as f:
            content = f.read()

        updated, update_count = self.generate_updated_content(
            content, updates, python_constraints, args.verbose, args.json_output
        )

        backup_path = str(Path(config_path).with_suffix(self.get_backup_extension()))
        with open(backup_path, "w") as f:
            f.write(content)
        if not args.json_output:
            console.print(Alert.info(f"Created backup: {backup_path}"))

        with open(config_path, "w") as f:
            f.write(updated)

        if not args.json_output:
            console.print(Alert.success(f"Updated {config_path} ({update_count} changes)"))

            console.print()
            console.print(Section("Next Steps"))
            next_steps = ReportGenerator.get_next_steps()
            for i, step in enumerate(next_steps, 1):
                console.print(f"  {i}. {step}")
            console.print(
                f"  {len(next_steps) + 1}. If something goes wrong,"
                f" restore from: [cyan]{backup_path}[/cyan]"
            )
