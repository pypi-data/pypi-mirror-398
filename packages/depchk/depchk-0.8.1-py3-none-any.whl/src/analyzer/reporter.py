import json
from typing import Any, Literal

from chalkbox.components.section import Section
from chalkbox.core.console import get_console
from rich.panel import Panel
from rich.table import Table as RichTable

from src.core.models import AnalysisResult, ArgumentConfig, PackageReport

console = get_console()


def create_json_response(
    status: Literal["success", "error"],
    data: dict[str, Any] | None = None,
    error_code: str | None = None,
    error_message: str | None = None,
) -> dict[str, Any]:
    if status == "success":
        return {"status": "success", "data": data}
    return {
        "status": "error",
        "error": {"code": error_code, "message": error_message},
    }


class ReportGenerator:
    @staticmethod
    def get_report_title() -> str:
        return "Dependency Analysis Report"

    @staticmethod
    def get_next_steps() -> list[str]:
        return [
            "Run [bold yellow]poetry lock[/bold yellow] to update the lock file",
            "Run [bold yellow]poetry install[/bold yellow] to install the updated dependencies",
        ]

    def print_report(self, result: AnalysisResult, args: ArgumentConfig) -> None:
        if args.json_output:
            # Convert AnalysisResult to dict for JSON serialization
            data = {
                "updates": result.updates,
                "skipped": result.skipped,
                "summary": result.summary,
                "report": [
                    {
                        "package": r.package,
                        "current": r.current,
                        "status": r.status,
                        "recommended": r.recommended,
                        "reason": r.reason,
                        "python_constraint": r.python_constraint,
                    }
                    for r in result.report
                ],
            }
            if result.python_version:
                data["python"] = result.python_version
            if result.major_updates:
                data["major_updates"] = result.major_updates
            if result.python_constraints:
                data["python_constraints"] = result.python_constraints

            response = create_json_response(status="success", data=data)
            print(json.dumps(response, indent=2))
            return

        console.print()

        header_lines = [f"[bold cyan]{self.get_report_title()}[/bold cyan]"]
        if result.python_version:
            # Check if we have both original and target Python
            original_python = getattr(result, "original_python", None)
            if original_python:
                header_lines.append(
                    f"Project Python: {original_python} | Target Python: {result.python_version}"
                )
            else:
                header_lines.append(f"Python Version: {result.python_version}")

        console.print(
            Panel.fit(
                "\n".join(header_lines),
                border_style="cyan",
            )
        )

        current_version_warnings = getattr(result, "current_version_warnings", [])
        if current_version_warnings:
            console.print()
            console.print("[yellow bold]⚠ Warning: Non-existent versions detected[/yellow bold]\n")
            for warning in current_version_warnings:
                console.print(f"  [yellow]•[/yellow] {warning['package']}: {warning['message']}")
            console.print()

        if result.summary:
            console.print("[bold]Summary[/bold]\n")

            summary_items = []
            if "total" in result.summary:
                summary_items.append(("Total packages", str(result.summary.get("total", 0))))
            if "analyzed" in result.summary:
                summary_items.append(("Analyzed", str(result.summary.get("analyzed", 0))))

            updates_count = result.summary.get("updates", result.summary.get("updated", 0))
            summary_items.append(("Updates available", str(updates_count)))

            if result.summary.get("major_updates", 0) > 0:
                summary_items.append(
                    ("Major version updates", str(result.summary.get("major_updates", 0)))
                )

            summary_items.append(("Skipped", str(result.summary.get("skipped", 0))))

            for key, value in summary_items:
                style = "yellow"
                if key == "Major version updates":
                    style = "bold red"
                elif key == "Updates available":
                    style = "green"
                elif key == "Skipped":
                    style = "dim"
                console.print(f"  * {key}: [{style}]{value}[/{style}]")
            console.print()

        if result.updates:
            console.print("[bold]Recommended Updates[/bold]\n")

            # Check if any packages have Python constraints
            has_constraints = result.python_constraints and len(result.python_constraints) > 0

            table = RichTable(show_header=True, header_style="bold magenta")
            table.add_column("Package", style="cyan")
            table.add_column("Current", style="dim")
            table.add_column("->", style="dim", justify="center")
            table.add_column("Recommended", style="green")
            table.add_column("Python", style="blue", justify="center")
            if has_constraints:
                table.add_column("Constraint", style="magenta", justify="center")
            table.add_column("Risk", style="yellow", justify="center")

            report_map = {}
            for report_entry in result.report:
                # Use the package name as-is from the report (it already matches updates keys)
                if report_entry.status == "update":
                    report_map[report_entry.package] = report_entry

            for pkg, version in result.updates.items():
                display_pkg = pkg.replace("__dev", " [dim](dev)[/dim]")

                # Find report item using the exact package name
                report_item: PackageReport | None = report_map.get(pkg)
                current = report_item.current if report_item else "?"

                python_range = "?"
                if report_item:
                    if report_item.python_min and report_item.python_max:
                        python_range = f"{report_item.python_min}->{report_item.python_max}"
                    elif report_item.python_min:
                        python_range = f"{report_item.python_min}+"
                    elif report_item.python_max:
                        python_range = f"<={report_item.python_max}"

                # Check if this package has a constraint applied
                constraint_display = ""
                if has_constraints and report_item and report_item.python_constraint:
                    constraint_display = "[green]✓[/green]"

                # Format risk level with color
                risk_display = "?"
                if report_item and report_item.confidence_level:
                    risk_level = report_item.confidence_level
                    if risk_level == "HIGH":
                        risk_display = "[bold red]HIGH[/bold red]"
                    elif risk_level == "MEDIUM":
                        risk_display = "[yellow]MED[/yellow]"
                    elif risk_level == "LOW":
                        risk_display = "[green]LOW[/green]"
                    else:
                        risk_display = "[dim]?[/dim]"

                if has_constraints:
                    table.add_row(
                        display_pkg,
                        current,
                        "->",
                        version,
                        python_range,
                        constraint_display,
                        risk_display,
                    )
                else:
                    table.add_row(display_pkg, current, "->", version, python_range, risk_display)

            console.print(table)

            # Display Python constraint summary if any were applied
            if has_constraints and result.python_constraints:
                console.print()
                console.print("[bold magenta]Python Constraints Applied:[/bold magenta]")
                constraint_items = []
                for pkg, constraint in result.python_constraints.items():
                    # Find the report item to get the recommended version
                    report_item = report_map.get(pkg)
                    if report_item:
                        constraint_items.append((pkg, constraint, report_item.recommended))

                for pkg, constraint, recommended in constraint_items:
                    console.print(
                        f"  * [cyan]{pkg}[/cyan] [dim]{recommended}[/dim] will include "
                        f'[magenta]python = "{constraint}"[/magenta]'
                    )
                console.print(
                    "\n  [dim]These constraints ensure compatibility with your project's Python version.[/dim]"
                )

            high_risk_items = [
                r
                for r in result.report
                if r.status == "update" and r.confidence_level in ["HIGH", "MEDIUM"]
            ]
            if high_risk_items:
                console.print()
                console.print("[bold yellow]! Risk Factors:[/bold yellow]")
                for item in high_risk_items:
                    if item.risk_factors:
                        risk_color = "red" if item.confidence_level == "HIGH" else "yellow"
                        console.print(f"  * [{risk_color}]{item.package}[/{risk_color}]:")
                        for factor in item.risk_factors:
                            console.print(f"    - {factor}")

            console.print()

        if result.skipped:
            console.print(Section("> Skipped Packages"))
            for pkg, reason in result.skipped.items():
                display_pkg = pkg.replace("__dev", " [dim](dev)[/dim]")
                console.print(f"  * [cyan]{display_pkg}[/cyan]: [dim]{reason}[/dim]")
            console.print()

        if result.report and args.verbose:
            console.print("[bold]Detailed Report[/bold]\n")

            for _idx, item in enumerate(result.report[:20]):  # Show first 20 items
                pkg_display = item.package.replace("__dev", " [dim](dev)[/dim]")

                if item.status == "update":
                    console.print(
                        f"[+] [cyan]{pkg_display}[/cyan]: "
                        f"[dim]{item.current or '?'}[/dim]"
                        f" -> [green]{item.recommended or '?'}[/green]"
                    )
                elif item.status == "skip":
                    console.print(
                        f"[>] [cyan]{pkg_display}[/cyan]:"
                        f" [yellow]{item.reason or 'skipped'}[/yellow]"
                    )
                elif item.status == "current":
                    console.print(
                        f"[+] [cyan]{pkg_display}[/cyan]:"
                        f" [dim]up to date ({item.current or '?'})[/dim]"
                    )
                elif item.status == "vendor":
                    console.print(
                        f"[pkg] [cyan]{pkg_display}[/cyan]:" f" [dim]vendor dependency[/dim]"
                    )
                elif item.status == "error":
                    console.print(
                        f"[x] [cyan]{pkg_display}[/cyan]:" f" [red]{item.reason or 'error'}[/red]"
                    )

            if len(result.report) > 20:
                console.print(f"  [dim]... and {len(result.report) - 20} more[/dim]")
            console.print()
