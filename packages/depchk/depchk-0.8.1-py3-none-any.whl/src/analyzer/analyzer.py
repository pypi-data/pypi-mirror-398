import json
from pathlib import Path
import sys
import traceback

from chalkbox.components.alert import Alert
from chalkbox.components.spinner import Spinner
from chalkbox.core.console import get_console
from chalkbox.logging.bridge import get_logger, setup_logging

from src.analyzer.cli import CLIHandler
from src.analyzer.reporter import ReportGenerator, create_json_response
from src.analyzer.resolver import Resolver
from src.analyzer.updater import FileUpdater
from src.core.models import AnalysisResult, ArgumentConfig, PackageReport

console = get_console()
logger = get_logger(__name__)


class PythonDepchecker:
    def __init__(self) -> None:
        self.cli_handler = CLIHandler()
        self.reporter = ReportGenerator()
        self.updater = FileUpdater()
        self.json_output = False
        self.verbose = False

    @staticmethod
    def setup_logging(verbose: bool = False, json_output: bool = False) -> None:
        if json_output:
            # JSON mode: suppress all logging
            level = "CRITICAL"
        elif verbose:
            # Verbose mode: show debug information
            level = "DEBUG"
        else:
            # Normal mode: only show errors
            level = "ERROR"

        setup_logging(
            level=level,
            show_time=False,
            show_path=False,
            show_level=False,
            rich_tracebacks=True,
        )

    async def analyze_dependencies(self, config_path: str, args: ArgumentConfig) -> AnalysisResult:
        target_python = getattr(args, "target_python", None)
        ignore_local_deps = getattr(args, "ignore_local_deps", False)

        if target_python and not args.json_output:
            console.print(
                f"[yellow]-> Target Python: {target_python} (overriding pyproject.toml)[/yellow]"
            )

        if ignore_local_deps and not args.json_output:
            console.print(
                "[yellow]-> Ignoring local path dependencies and their version constraints[/yellow]"
            )

        resolver = Resolver()

        # Check Python compatibility WITHOUT spinner!
        should_proceed, config_or_result = await resolver.check_python_compatibility_interactive(
            config_path, target_python, ignore_local_deps, args.json_output
        )

        if not should_proceed:
            # User declined or Python incompatibility detected
            return AnalysisResult(
                updates={},
                skipped={},
                report=[],
                summary={},
                aborted=True,
                python_version=config_or_result.get("python"),
                original_python=config_or_result.get("original_python"),
            )

        # Compatibility check passed, proceed with analysis
        with Spinner("Analyzing dependencies..."):
            result_dict = await resolver.analyze_project(
                config_path,
                target_python=target_python,
                config_data=config_or_result,
                ignore_local_deps=ignore_local_deps,
            )

        # Validate target Python against project Python if specified
        if target_python and result_dict.get("python"):
            original_python = result_dict.get("original_python")
            if original_python:
                warning_msg, _warning_type = self.cli_handler.compare_python_versions(
                    target_python, original_python
                )
                if warning_msg and not args.json_output:
                    console.print()
                    console.print(Alert.warning(warning_msg))

        report_entries = []
        for report_dict in result_dict.get("report", []):
            report_entries.append(PackageReport(**report_dict))

        # Collect major updates
        major_updates_list = [
            {
                "package": r.package,
                "current": r.current,
                "recommended": r.recommended,
                "version_jump": r.version_jump,
            }
            for r in report_entries
            if r.status == "update" and r.version_jump and "major" in r.version_jump.lower()
        ]

        summary = result_dict.get("summary", {})
        if major_updates_list:
            summary["major_updates"] = len(major_updates_list)

        result = AnalysisResult(
            updates=result_dict.get("updates", {}),
            skipped=result_dict.get("skipped", {}),
            report=report_entries,
            summary=summary,
            python_version=result_dict.get("python"),
            original_python=result_dict.get("original_python"),
            major_updates=major_updates_list if major_updates_list else None,
            current_version_warnings=result_dict.get("current_version_warnings", []),
            python_constraints=result_dict.get("python_constraints"),
        )

        return result

    async def run(self, argv: list[str] | None = None) -> None:
        parser = self.cli_handler.create_argument_parser(self.reporter.get_report_title())
        args_namespace = parser.parse_args(argv)

        args = ArgumentConfig(
            file=args_namespace.file,
            update_source_file=args_namespace.update_source_file,
            json_output=args_namespace.json,
            verbose=args_namespace.verbose,
            allow_prerelease=getattr(args_namespace, "allow_prerelease", False),
            target_python=getattr(args_namespace, "target_python", None),
            ignore_local_deps=getattr(args_namespace, "ignore_local_deps", False),
        )

        self.json_output = args.json_output
        self.verbose = args.verbose

        self.setup_logging(args.verbose, args.json_output)

        is_valid, error_msg = self.cli_handler.validate_flag_combinations(args_namespace)
        if not is_valid:
            if self.json_output:
                response = create_json_response(
                    status="error",
                    error_code="incompatible_flags",
                    error_message=error_msg,
                )
                print(json.dumps(response, indent=2))
            else:
                console.print(Alert.error(error_msg or "Invalid flag combination"))
            sys.exit(1)

        # Validate target Python version if specified
        if hasattr(args, "target_python") and args.target_python:
            is_valid, error_msg = self.cli_handler.validate_target_python(args.target_python)
            if not is_valid:
                if error_msg is None:
                    error_msg = "Invalid Python version"
                if not self.json_output:
                    console.print(Alert.error(error_msg))
                sys.exit(1)

        config_path = self.cli_handler.find_config_file(args.file, self.json_output)

        if not self.json_output:
            console.print(Alert.info(f"Analyzing: {config_path}"))

        try:
            result = await self.analyze_dependencies(str(config_path), args)

            if result.aborted:
                # User declined to proceed - exit silently
                sys.exit(0)

            self.reporter.print_report(result, args)

            if result.updates:
                python_constraints = result.python_constraints or {}

                with open(config_path) as f:
                    content = f.read()

                if args.update_source_file:
                    if args.json_output:
                        print(json.dumps({"updates_to_apply": result.updates}))
                    else:
                        if sys.stdin.isatty():
                            confirm = console.input(
                                f"\n[bold yellow]-> Apply {len(result.updates)}"
                                f" updates to {config_path}? (y/n): [/bold yellow]"
                            )
                            if confirm.lower() == "y":
                                await self.updater.apply_updates(
                                    str(config_path), result.updates, python_constraints, args
                                )
                            else:
                                if not self.json_output:
                                    console.print(Alert.warning("Updates cancelled"))
                        else:
                            # Non-interactive mode, auto-apply
                            if not self.json_output:
                                console.print(
                                    Alert.info(
                                        f"Applying {len(result.updates)}"
                                        f" updates (non-interactive mode)..."
                                    )
                                )
                            await self.updater.apply_updates(
                                str(config_path), result.updates, python_constraints, args
                            )
                else:
                    # Create updated file preview
                    updated_content, update_count = self.updater.generate_updated_content(
                        content, result.updates, python_constraints, args.verbose, args.json_output
                    )
                    updated_path = str(
                        Path(config_path).with_suffix(self.updater.get_updated_extension())
                    )

                    with open(updated_path, "w") as f:
                        f.write(updated_content)

                    if not self.json_output:
                        console.print()
                        console.print(
                            Alert.info(
                                f"Created {updated_path} with {update_count} proposed updates"
                            )
                        )
                        console.print(
                            "[yellow]i To apply these updates,"
                            " run with --update-source-file flag[/yellow]"
                        )

        except Exception as e:
            if args.verbose:
                traceback.print_exc()
            if not self.json_output:
                console.print(Alert.error(f"Error: {e}"))
            sys.exit(1)
