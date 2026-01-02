"""UI components for testudos.

This module provides the display and progress components for the CLI,
including Rich-based tables and live progress displays.
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console
from rich.table import Table
from rich.text import Text

from testudos.coverage import CoverageSummary
from testudos.executor import TestResult, TestStatus

if TYPE_CHECKING:
    from testudos.workspace import PackageSpec, WorkspaceResult

# Rich console for formatted output
console = Console()


class ParallelProgressDisplay:
    """Manages the live display for parallel test execution.

    This class uses Rich's Live display to show real-time progress
    of parallel test execution with spinners and status updates.
    """

    def __init__(self, versions: list[str]) -> None:
        """Initialize the progress display.

        Args:
            versions: List of Python versions being tested
        """
        self.versions = versions
        self.statuses: dict[str, TestStatus] = {v: TestStatus.PENDING for v in versions}
        self.results: dict[str, TestResult | None] = {v: None for v in versions}
        self._lock = threading.Lock()

    def update(self, version: str, status: TestStatus, result: TestResult | None) -> None:
        """Update the status for a specific version.

        Args:
            version: Python version
            status: New status
            result: Test result (for completed tests)
        """
        with self._lock:
            self.statuses[version] = status
            self.results[version] = result

    def render(self) -> Table:
        """Render the current progress as a Rich Table.

        Returns:
            Rich Table with current status of all versions
        """
        table = Table(title="Test Progress", show_header=True)
        table.add_column("Python Version", style="cyan", width=16)
        table.add_column("Status", width=30)

        with self._lock:
            for version in sorted(self.versions, key=lambda v: tuple(map(int, v.split(".")))):
                status = self.statuses[version]
                result = self.results[version]

                if status == TestStatus.PENDING:
                    status_text = Text("○ Pending", style="dim")
                elif status == TestStatus.RUNNING:
                    # Use a spinner character for running tests
                    status_text = Text("⠋ Running...", style="yellow")
                elif status == TestStatus.PASSED:
                    duration = f" ({result.duration:.1f}s)" if result and result.duration else ""
                    status_text = Text(f"✓ Passed{duration}", style="green")
                else:  # FAILED
                    duration = f" ({result.duration:.1f}s)" if result and result.duration else ""
                    status_text = Text(f"✗ Failed{duration}", style="red")

                table.add_row(version, status_text)

        return table


class MultiPackageProgressDisplay:
    """Manages the live display for multi-package parallel test execution.

    Shows progress for multiple packages, with each package showing
    aggregate status across its Python versions.

    Attributes:
        packages: List of package specifications being tested
        show_versions: Whether to show individual version status (expanded view)
    """

    def __init__(
        self,
        packages: list[PackageSpec],
        show_versions: bool = False,
    ) -> None:
        """Initialize the multi-package progress display.

        Args:
            packages: List of package specifications being tested
            show_versions: Whether to show individual versions (default: collapsed)
        """
        self.packages = packages
        self.show_versions = show_versions
        # Nested status: package_name -> version -> status
        self.statuses: dict[str, dict[str, TestStatus]] = {}
        self.results: dict[str, dict[str, TestResult | None]] = {}
        self._lock = threading.Lock()

        # Initialize for each package
        for pkg in packages:
            self.statuses[pkg.display_name] = {}
            self.results[pkg.display_name] = {}

    def register_versions(self, package_name: str, versions: list[str]) -> None:
        """Register the Python versions being tested for a package.

        Args:
            package_name: Name of the package
            versions: List of version strings to be tested
        """
        with self._lock:
            if package_name not in self.statuses:
                self.statuses[package_name] = {}
                self.results[package_name] = {}
            for v in versions:
                self.statuses[package_name][v] = TestStatus.PENDING
                self.results[package_name][v] = None

    def update(
        self,
        package_name: str,
        version: str,
        status: TestStatus,
        result: TestResult | None,
    ) -> None:
        """Update the status for a specific package/version combination.

        Args:
            package_name: Name of the package
            version: Python version string
            status: New test status
            result: Test result (for completed tests)
        """
        with self._lock:
            if package_name not in self.statuses:
                self.statuses[package_name] = {}
                self.results[package_name] = {}
            self.statuses[package_name][version] = status
            self.results[package_name][version] = result

    def render(self) -> Table:
        """Render the current progress as a Rich Table.

        Returns:
            Rich Table with current status of all packages/versions
        """
        if self.show_versions:
            return self._render_expanded()
        return self._render_collapsed()

    def _render_collapsed(self) -> Table:
        """Render collapsed view (one row per package with aggregate status)."""
        table = Table(title="Multi-Package Test Progress", show_header=True)
        table.add_column("Package", style="cyan", width=30)
        table.add_column("Progress", width=15)
        table.add_column("Status", width=25)

        with self._lock:
            for pkg in self.packages:
                pkg_name = pkg.display_name
                pkg_statuses = self.statuses.get(pkg_name, {})

                # Calculate aggregate status
                total = len(pkg_statuses)
                running = sum(1 for s in pkg_statuses.values() if s == TestStatus.RUNNING)
                passed = sum(1 for s in pkg_statuses.values() if s == TestStatus.PASSED)
                failed = sum(1 for s in pkg_statuses.values() if s == TestStatus.FAILED)
                pending = sum(1 for s in pkg_statuses.values() if s == TestStatus.PENDING)

                # Progress text
                if total == 0:
                    progress = Text("...", style="dim")
                else:
                    done = passed + failed
                    progress = Text(f"{done}/{total}")

                # Status text with appropriate styling
                if failed > 0:
                    status_text = Text(f"✗ {failed} failed", style="red")
                elif running > 0:
                    status_text = Text(f"⠋ Running ({running})...", style="yellow")
                elif pending > 0 and passed > 0:
                    status_text = Text(f"✓ {passed} passed, {pending} pending", style="yellow")
                elif pending == total and total > 0:
                    status_text = Text("○ Pending", style="dim")
                elif total == 0:
                    status_text = Text("○ Initializing...", style="dim")
                else:
                    status_text = Text(f"✓ All {passed} passed", style="green")

                table.add_row(pkg_name, progress, status_text)

        return table

    def _render_expanded(self) -> Table:
        """Render expanded view with individual version status per package."""
        table = Table(title="Multi-Package Test Progress", show_header=True)
        table.add_column("Package", style="cyan", width=25)
        table.add_column("Version", style="cyan", width=10)
        table.add_column("Status", width=25)

        with self._lock:
            for pkg in self.packages:
                pkg_name = pkg.display_name
                pkg_statuses = self.statuses.get(pkg_name, {})
                pkg_results = self.results.get(pkg_name, {})

                versions = sorted(
                    pkg_statuses.keys(),
                    key=lambda v: tuple(map(int, v.split("."))),
                )

                for i, version in enumerate(versions):
                    status = pkg_statuses[version]
                    result = pkg_results.get(version)

                    # Package name only on first row for this package
                    pkg_cell = pkg_name if i == 0 else ""

                    # Status text (same format as ParallelProgressDisplay)
                    if status == TestStatus.PENDING:
                        status_text = Text("○ Pending", style="dim")
                    elif status == TestStatus.RUNNING:
                        status_text = Text("⠋ Running...", style="yellow")
                    elif status == TestStatus.PASSED:
                        duration = (
                            f" ({result.duration:.1f}s)" if result and result.duration else ""
                        )
                        status_text = Text(f"✓ Passed{duration}", style="green")
                    else:  # FAILED
                        duration = (
                            f" ({result.duration:.1f}s)" if result and result.duration else ""
                        )
                        status_text = Text(f"✗ Failed{duration}", style="red")

                    table.add_row(pkg_cell, version, status_text)

                # Add empty row between packages for visual separation
                if pkg != self.packages[-1] and versions:
                    table.add_row("", "", "")

        return table


def display_results(
    results: dict[str, TestResult],
    *,
    wall_clock_time: float | None = None,
) -> None:
    """Display test results in a formatted table.

    Args:
        results: Dictionary mapping version to TestResult
        wall_clock_time: Actual elapsed wall-clock time (for parallel runs)
    """
    table = Table(title="Test Results")
    table.add_column("Python Version", style="cyan")
    table.add_column("Status")
    table.add_column("Duration", justify="right")

    for version in sorted(results.keys(), key=lambda v: tuple(map(int, v.split(".")))):
        result = results[version]
        if result.success:
            status = "[green]PASSED[/green]"
        else:
            status = f"[red]FAILED[/red] (exit code: {result.return_code})"
        duration = f"{result.duration:.1f}s" if result.duration else "-"
        table.add_row(version, status, duration)

    console.print(table)

    # Summary
    passed = sum(1 for r in results.values() if r.success)
    total = len(results)
    # Use wall-clock time if provided, otherwise sum individual durations
    if wall_clock_time is not None:
        total_duration = wall_clock_time
    else:
        total_duration = sum(r.duration or 0 for r in results.values())
    console.print(f"\n[bold]Summary:[/bold] {passed}/{total} passed in {total_duration:.1f}s")


def display_versions_table(supported: list[str], test_versions: list[str]) -> None:
    """Display a table showing Python versions and their compatibility.

    Args:
        supported: List of all supported Python versions
        test_versions: List of versions that will be tested
    """
    table = Table(title="Python Versions")
    table.add_column("Version", style="cyan")
    table.add_column("Supported", justify="center")
    table.add_column("Compatible", justify="center")
    table.add_column("Will Test", justify="center", style="bold")

    for version in supported:
        is_compatible = version in test_versions
        table.add_row(
            version,
            "[green]✓[/green]",
            "[green]✓[/green]" if is_compatible else "[red]✗[/red]",
            "[green]✓[/green]" if is_compatible else "",
        )

    console.print(table)
    console.print(f"\n[bold]Will test:[/bold] {', '.join(test_versions)}")


def print_error(message: str) -> None:
    """Print an error message.

    Args:
        message: Error message to display
    """
    console.print(f"[red]Error:[/red] {message}")


def print_info(message: str) -> None:
    """Print an info message.

    Args:
        message: Info message to display
    """
    console.print(message)


def display_coverage_summary(summary: CoverageSummary) -> None:
    """Display coverage summary in a formatted table.

    Args:
        summary: Coverage summary data
    """
    table = Table(title="Coverage Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")

    table.add_row("Lines covered", str(summary.covered_lines))
    table.add_row("Lines total", str(summary.total_lines))
    table.add_row("Lines missed", str(summary.missed_lines))

    # Show branch coverage if available
    if summary.total_branches is not None:
        table.add_row("Branches covered", str(summary.covered_branches or 0))
        table.add_row("Branches total", str(summary.total_branches))

    # Coverage percentage with color coding
    percent = summary.percent_covered
    if percent >= 80:
        percent_style = "green"
    elif percent >= 60:
        percent_style = "yellow"
    else:
        percent_style = "red"

    table.add_row(
        "Coverage",
        Text(f"{percent:.1f}%", style=percent_style),
    )

    console.print(table)


def display_coverage_reports(report_paths: dict[str, Path]) -> None:
    """Display paths to generated coverage reports.

    Args:
        report_paths: Dictionary mapping format to report path
    """
    if not report_paths:
        return

    console.print("\n[bold]Coverage Reports:[/bold]")
    for fmt, path in sorted(report_paths.items()):
        console.print(f"  {fmt}: {path}")


def display_multi_package_results(workspace_result: WorkspaceResult) -> None:
    """Display test results for multiple packages in a formatted table.

    Args:
        workspace_result: WorkspaceResult containing all package results
    """
    table = Table(title="Multi-Package Test Results")
    table.add_column("Package", style="cyan")
    table.add_column("Versions", justify="center")
    table.add_column("Passed", justify="center")
    table.add_column("Failed", justify="center")
    table.add_column("Duration", justify="right")
    table.add_column("Status")

    for pkg_name in sorted(workspace_result.package_results.keys()):
        pkg_result = workspace_result.package_results[pkg_name]

        total = len(pkg_result.results)
        passed = pkg_result.passed_count
        failed = pkg_result.failed_count
        duration = f"{pkg_result.total_duration:.1f}s"

        if pkg_result.success:
            status = "[green]PASSED[/green]"
        else:
            status = "[red]FAILED[/red]"

        table.add_row(
            pkg_name,
            str(total),
            f"[green]{passed}[/green]" if passed > 0 else "0",
            f"[red]{failed}[/red]" if failed > 0 else "0",
            duration,
            status,
        )

    console.print(table)

    # Summary
    summary = workspace_result.get_summary()
    console.print(
        f"\n[bold]Summary:[/bold] "
        f"{summary['passed_packages']}/{summary['total_packages']} packages passed, "
        f"{summary['passed_versions']}/{summary['total_versions']} version tests passed "
        f"in {workspace_result.total_duration:.1f}s"
    )
