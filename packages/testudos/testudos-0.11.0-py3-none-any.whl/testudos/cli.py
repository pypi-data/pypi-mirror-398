"""CLI entry point for testudos.

This module provides the command-line interface for testudos,
built using typer with rich output formatting.
"""

import asyncio
import time
from pathlib import Path
from typing import Annotated

import typer
from rich.live import Live
from rich.table import Table

from testudos.coverage import (
    CoverageResult,
    check_coverage_available,
    clean_coverage_data,
    generate_coverage_report,
    get_combined_coverage_path,
    list_coverage_data_files,
    run_coverage_combine,
)
from testudos.executor import (
    ExecutorError,
    TestResult,
    TestStatus,
    check_uv_available,
)
from testudos.multi_runner import MultiPackageRunner
from testudos.runner import RunOptions, RunPlan, TestRunner
from testudos.ui import (
    MultiPackageProgressDisplay,
    ParallelProgressDisplay,
    console,
    display_coverage_reports,
    display_coverage_summary,
    display_multi_package_results,
    display_results,
    display_versions_table,
    print_error,
    print_info,
)
from testudos.versions import (
    VersionResolutionError,
    get_supported_python_versions,
    resolve_test_versions,
)
from testudos.workspace import WorkspaceConfig, WorkspaceResult

# Create the typer app
app = typer.Typer(
    name="testudos",
    help="Testudos - Multi-Python version test harness",
    add_completion=False,
)


def _display_dry_run(plan: RunPlan) -> None:
    """Display what would be executed in dry-run mode.

    Args:
        plan: The run plan to display
    """
    console.print("[bold]Dry run mode - no tests will be executed[/bold]\n")

    # Summary table
    table = Table(title="Test Plan")
    table.add_column("Setting", style="cyan")
    table.add_column("Value")

    table.add_row("Python versions", ", ".join(plan.versions))
    table.add_row("Test command", plan.test_command)
    table.add_row("Test args", " ".join(plan.test_args) if plan.test_args else "(none)")
    table.add_row("Working directory", str(plan.working_dir))
    table.add_row("Execution mode", "parallel" if plan.parallel else "sequential")
    if plan.parallel and plan.max_jobs:
        table.add_row("Max parallel jobs", str(plan.max_jobs))
    table.add_row("Timeout", f"{plan.timeout}s per version" if plan.timeout else "disabled")
    table.add_row("Coverage", "enabled" if plan.coverage else "disabled")

    console.print(table)

    # Commands that would be executed
    console.print("\n[bold]Commands that would be executed:[/bold]")
    for cmd in plan.commands:
        console.print(f"  [dim]$[/dim] {cmd}")


async def _run_parallel_with_display_async(
    runner: TestRunner,
    options: RunOptions,
) -> dict[str, TestResult]:
    """Run tests in parallel with a live progress display using asyncio.

    Uses asyncio for test execution and a background task for display updates,
    eliminating the nested threading model used in the sync version.

    Args:
        runner: The test runner instance
        options: Run options

    Returns:
        Dictionary of test results
    """
    progress = ParallelProgressDisplay(runner.versions)

    def on_status_change(version: str, status: TestStatus, result: TestResult | None) -> None:
        progress.update(version, status, result)

    # Run with live display
    with Live(progress.render(), console=console, refresh_per_second=10) as live:
        # Flag to signal when tests are complete
        tests_complete = asyncio.Event()

        async def update_display() -> None:
            """Background task to update the display periodically."""
            while not tests_complete.is_set():
                live.update(progress.render())
                await asyncio.sleep(0.1)

        # Start display updates in background
        display_task = asyncio.create_task(update_display())

        try:
            # Run tests asynchronously
            results = await runner.run_async(
                options=options,
                on_status_change=on_status_change,
            )
        finally:
            # Signal display task to stop and wait for it
            tests_complete.set()
            await display_task

        # Final update
        live.update(progress.render())

    return results


def _run_parallel_with_display(
    runner: TestRunner,
    options: RunOptions,
) -> dict[str, TestResult]:
    """Run tests in parallel with a live progress display.

    This is a synchronous wrapper around the async implementation.

    Args:
        runner: The test runner instance
        options: Run options

    Returns:
        Dictionary of test results
    """
    return asyncio.run(_run_parallel_with_display_async(runner, options))


async def _run_multi_package_with_display_async(
    multi_runner: MultiPackageRunner,
    options: RunOptions,
    show_versions: bool = False,
) -> WorkspaceResult:
    """Run tests for multiple packages with a live progress display.

    Args:
        multi_runner: The multi-package runner instance
        options: Run options
        show_versions: Whether to show individual version status

    Returns:
        WorkspaceResult with all package results
    """
    packages = multi_runner.packages
    progress = MultiPackageProgressDisplay(packages, show_versions=show_versions)

    # Register versions for each package before starting
    for pkg in packages:
        try:
            versions = multi_runner.get_package_versions(pkg.display_name)
            progress.register_versions(pkg.display_name, versions)
        except Exception:
            # Will be handled during execution
            pass

    def on_status_change(
        package_name: str,
        version: str,
        status: TestStatus,
        result: TestResult | None,
    ) -> None:
        progress.update(package_name, version, status, result)

    # Run with live display
    with Live(progress.render(), console=console, refresh_per_second=10) as live:
        # Flag to signal when tests are complete
        tests_complete = asyncio.Event()

        async def update_display() -> None:
            """Background task to update the display periodically."""
            while not tests_complete.is_set():
                live.update(progress.render())
                await asyncio.sleep(0.1)

        # Start display updates in background
        display_task = asyncio.create_task(update_display())

        try:
            # Run tests asynchronously
            results = await multi_runner.run_all_async(
                options=options,
                on_status_change=on_status_change,
            )
        finally:
            # Signal display task to stop and wait for it
            tests_complete.set()
            await display_task

        # Final update
        live.update(progress.render())

    return results


def _run_multi_package_with_display(
    multi_runner: MultiPackageRunner,
    options: RunOptions,
    show_versions: bool = False,
) -> WorkspaceResult:
    """Run tests for multiple packages with a live progress display.

    This is a synchronous wrapper around the async implementation.

    Args:
        multi_runner: The multi-package runner instance
        options: Run options
        show_versions: Whether to show individual version status

    Returns:
        WorkspaceResult with all package results
    """
    return asyncio.run(_run_multi_package_with_display_async(multi_runner, options, show_versions))


async def _handle_coverage_reporting_async(
    working_dir: Path,
    versions: list[str],
    report_formats: list[str],
    fail_under: float | None,
    combine: bool,
) -> bool:
    """Handle coverage combining and reporting after tests complete.

    Args:
        working_dir: Project working directory
        versions: Python versions that were tested
        report_formats: Report formats to generate
        fail_under: Minimum coverage percentage
        combine: Whether to combine coverage data

    Returns:
        True if coverage check passed, False if failed
    """
    from testudos.coverage import get_coverage_data_path

    # Get coverage data files
    data_files = [get_coverage_data_path(working_dir, v) for v in versions]
    existing_files = [f for f in data_files if f.exists()]

    if not existing_files:
        print_error("No coverage data files found")
        return False

    # Combine coverage if multiple versions or if explicitly requested
    if combine and len(existing_files) > 1:
        print_info("[bold]Combining coverage data...[/bold]")
        combine_result = await run_coverage_combine(working_dir, existing_files)
        if not combine_result.success:
            print_error(f"Failed to combine coverage: {combine_result.error}")
            return False
        data_file = combine_result.data_file
    else:
        # Use the first (or only) coverage file
        data_file = existing_files[0]

    if data_file is None:
        print_error("No coverage data file available")
        return False

    # Generate reports
    print_info("[bold]Generating coverage report...[/bold]")
    report_result = await generate_coverage_report(
        working_dir, data_file, report_formats, fail_under
    )

    if report_result.summary:
        print_info("")
        display_coverage_summary(report_result.summary)

    if report_result.report_paths:
        display_coverage_reports(report_result.report_paths)

    if not report_result.success:
        print_error(report_result.error or "Coverage check failed")
        return False

    return True


def _handle_coverage_reporting(
    working_dir: Path,
    versions: list[str],
    report_formats: list[str],
    fail_under: float | None,
    combine: bool,
) -> bool:
    """Synchronous wrapper for coverage reporting.

    Args:
        working_dir: Project working directory
        versions: Python versions that were tested
        report_formats: Report formats to generate
        fail_under: Minimum coverage percentage
        combine: Whether to combine coverage data

    Returns:
        True if coverage check passed, False if failed
    """
    return asyncio.run(
        _handle_coverage_reporting_async(working_dir, versions, report_formats, fail_under, combine)
    )


@app.command()
def run(
    path: Annotated[
        Path,
        typer.Argument(
            help="Path to the Python package to test",
            exists=True,
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
        ),
    ] = Path("."),
    package: Annotated[
        list[Path] | None,
        typer.Option(
            "--package",
            "-k",
            help="Additional package path(s) to test (can be repeated for multi-package testing)",
            exists=True,
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
        ),
    ] = None,
    discover: Annotated[
        bool,
        typer.Option(
            "--discover",
            "-d",
            help="Auto-discover and test all packages (directories with pyproject.toml) under path",
        ),
    ] = False,
    python: Annotated[
        list[str] | None,
        typer.Option(
            "--python",
            "-p",
            help="Python version(s) to test (can be repeated)",
        ),
    ] = None,
    fail_fast: Annotated[
        bool,
        typer.Option(
            "--fail-fast/--no-fail-fast",
            "-f/-F",
            help="Stop immediately when a test fails (sequential mode only)",
        ),
    ] = True,
    parallel: Annotated[
        bool,
        typer.Option(
            "--parallel",
            "-P",
            help="Run tests in parallel across Python versions",
        ),
    ] = False,
    jobs: Annotated[
        int | None,
        typer.Option(
            "--jobs",
            "-j",
            help="Maximum number of parallel jobs (default: number of versions)",
            min=1,
        ),
    ] = None,
    parallel_packages: Annotated[
        bool,
        typer.Option(
            "--parallel-packages/--no-parallel-packages",
            help="Run packages in parallel (default: True when multiple packages)",
        ),
    ] = True,
    package_jobs: Annotated[
        int | None,
        typer.Option(
            "--package-jobs",
            "-J",
            help="Maximum number of packages to test in parallel",
            min=1,
        ),
    ] = None,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-v",
            help="Show verbose output (version details in multi-package mode)",
        ),
    ] = False,
    quiet: Annotated[
        bool,
        typer.Option(
            "--quiet",
            "-q",
            help="Suppress detailed output for failed tests",
        ),
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            "-n",
            help="Show what would be executed without running tests",
        ),
    ] = False,
    coverage: Annotated[
        bool,
        typer.Option(
            "--coverage",
            "-c",
            help="Collect test coverage data",
        ),
    ] = False,
    coverage_report: Annotated[
        list[str] | None,
        typer.Option(
            "--coverage-report",
            help="Coverage report format(s): term, term-missing, html, xml, json, lcov",
        ),
    ] = None,
    coverage_fail_under: Annotated[
        float | None,
        typer.Option(
            "--coverage-fail-under",
            help="Fail if coverage percentage is below this threshold",
            min=0,
            max=100,
        ),
    ] = None,
    timeout: Annotated[
        float | None,
        typer.Option(
            "--timeout",
            "-t",
            help="Timeout in seconds per Python version test run",
            min=0.1,
        ),
    ] = None,
    no_timeout: Annotated[
        bool,
        typer.Option(
            "--no-timeout",
            help="Disable timeout (overrides config file setting)",
        ),
    ] = False,
) -> None:
    """Run tests across multiple Python versions.

    This command runs your test suite using uv's isolated environments
    for each Python version, ensuring clean test execution.

    Single package examples:
        testudos run
        testudos run ./my-package
        testudos run --python 3.11 --python 3.12
        testudos run --parallel --jobs 4

    Multi-package examples:
        testudos run --package ./pkg1 --package ./pkg2
        testudos run . --package ./other-pkg
        testudos run --package ./pkg1 --package ./pkg2 --parallel-packages
        testudos run --package ./pkg1 --package ./pkg2 --package-jobs 2

    Auto-discover packages in a directory:
        testudos run ./monorepo --discover
        testudos run --discover --parallel-packages

    Other options:
        testudos run --dry-run
        testudos run --coverage --coverage-report html
    """
    # Handle auto-discovery mode
    if discover:
        discovered_config = WorkspaceConfig.auto_discover(path)
        if not discovered_config.packages:
            print_error(f"No packages found under {path}")
            raise typer.Exit(1)

        # Check uv is available (skip for dry-run)
        if not dry_run and not check_uv_available():
            print_error("uv not found. Install from [link]https://docs.astral.sh/uv/[/link]")
            raise typer.Exit(1)

        discovered_paths = [pkg.path for pkg in discovered_config.packages]
        # Determine effective timeout for multi-package
        mp_timeout = None if no_timeout else timeout
        _run_multi_package(
            paths=discovered_paths,
            python_versions=python,
            parallel=parallel,
            jobs=jobs,
            parallel_packages=parallel_packages,
            package_jobs=package_jobs,
            fail_fast=fail_fast,
            verbose=verbose,
            quiet=quiet,
            dry_run=dry_run,
            timeout=mp_timeout,
            coverage=coverage,
            coverage_report=coverage_report,
            coverage_fail_under=coverage_fail_under,
        )
        return

    # Collect all package paths
    all_paths = [path]
    if package:
        all_paths.extend(package)

    # Check uv is available (skip for dry-run)
    if not dry_run and not check_uv_available():
        print_error("uv not found. Install from [link]https://docs.astral.sh/uv/[/link]")
        raise typer.Exit(1)

    # Route to multi-package or single-package mode
    if len(all_paths) > 1:
        # Determine effective timeout for multi-package
        mp_timeout = None if no_timeout else timeout
        _run_multi_package(
            paths=all_paths,
            python_versions=python,
            parallel=parallel,
            jobs=jobs,
            parallel_packages=parallel_packages,
            package_jobs=package_jobs,
            fail_fast=fail_fast,
            verbose=verbose,
            quiet=quiet,
            dry_run=dry_run,
            timeout=mp_timeout,
            coverage=coverage,
            coverage_report=coverage_report,
            coverage_fail_under=coverage_fail_under,
        )
        return

    # Single package mode (existing behavior)
    # Create the test runner
    try:
        runner = TestRunner(
            project_path=path,
            explicit_versions=python,
        )
    except Exception as e:
        print_error(f"Loading config: {e}")
        raise typer.Exit(1)

    # Resolve versions
    try:
        test_versions = runner.versions
    except VersionResolutionError as e:
        print_error(str(e))
        raise typer.Exit(1)

    if not test_versions:
        print_error("No Python versions to test")
        raise typer.Exit(1)

    # Determine coverage settings
    enable_coverage = coverage or runner.config.coverage
    report_formats = coverage_report if coverage_report else runner.config.coverage_report
    fail_under = (
        coverage_fail_under
        if coverage_fail_under is not None
        else runner.config.coverage_fail_under
    )

    # Determine timeout setting
    # --no-timeout explicitly disables, --timeout sets value, otherwise use config
    effective_timeout: float | None = None
    if no_timeout:
        effective_timeout = None
    elif timeout is not None:
        effective_timeout = timeout
    else:
        effective_timeout = runner.config.timeout

    # Check coverage is available if enabled
    if enable_coverage and not dry_run and not check_coverage_available():
        print_error(
            "coverage not found. Install with: pip install coverage\n"
            "Or add coverage to your project dependencies."
        )
        raise typer.Exit(1)

    # Create run options
    options = RunOptions(
        parallel=parallel or runner.config.parallel,
        max_jobs=jobs if jobs is not None else runner.config.max_jobs,
        fail_fast=fail_fast,
        verbose=verbose,
        dry_run=dry_run,
        timeout=effective_timeout,
        coverage=enable_coverage,
    )

    # Get the execution plan
    plan = runner.plan(options)

    # Handle dry-run mode
    if dry_run:
        _display_dry_run(plan)
        return

    # Display versions being tested
    mode = "parallel" if options.parallel else "sequential"
    print_info(f"[bold]Testing Python versions:[/bold] {', '.join(test_versions)} ({mode})")
    if enable_coverage:
        print_info("[bold]Coverage:[/bold] enabled")
    if effective_timeout:
        print_info(f"[bold]Timeout:[/bold] {effective_timeout}s per version")
    if verbose:
        test_args = " ".join(runner.config.test_args)
        print_info(f"[dim]Test command:[/dim] {runner.config.test_command} {test_args}")
        print_info(f"[dim]Working directory:[/dim] {path}")
        if options.parallel and options.max_jobs:
            print_info(f"[dim]Max parallel jobs:[/dim] {options.max_jobs}")
    print_info("")

    # Run tests
    try:
        start_time = time.monotonic()
        if options.parallel:
            results = _run_parallel_with_display(runner, options)
        else:
            results = runner.run(options)
        wall_clock_time = time.monotonic() - start_time
    except ExecutorError as e:
        print_error(str(e))
        raise typer.Exit(1)

    # Display results
    print_info("")
    display_results(results, wall_clock_time=wall_clock_time)

    # Show captured output for failed tests in parallel mode (unless --quiet)
    if options.parallel and not quiet:
        failed_results = [r for r in results.values() if not r.success]
        if failed_results:
            console.print("\n[bold red]Failed test output:[/bold red]")
            for result in failed_results:
                console.print(f"\n[bold]Python {result.version}:[/bold]")
                if result.output:
                    console.print(result.output)
                if result.error:
                    console.print(f"[red]{result.error}[/red]")

    # Handle coverage reporting
    coverage_failed = False
    if enable_coverage and all(r.success for r in results.values()):
        print_info("")
        coverage_success = _handle_coverage_reporting(
            path, test_versions, report_formats, fail_under, runner.config.coverage_combine
        )
        if not coverage_success:
            coverage_failed = True

    # Exit with error if any tests failed or coverage check failed
    if not all(r.success for r in results.values()) or coverage_failed:
        raise typer.Exit(1)


def _run_multi_package(
    paths: list[Path],
    python_versions: list[str] | None,
    parallel: bool,
    jobs: int | None,
    parallel_packages: bool,
    package_jobs: int | None,
    fail_fast: bool,
    verbose: bool,
    quiet: bool,
    dry_run: bool,
    timeout: float | None,
    coverage: bool,
    coverage_report: list[str] | None,
    coverage_fail_under: float | None,
) -> None:
    """Run tests for multiple packages.

    Args:
        paths: List of package paths to test
        python_versions: Explicit Python versions to test
        parallel: Whether to run versions in parallel within each package
        jobs: Max parallel version jobs per package
        parallel_packages: Whether to run packages in parallel
        package_jobs: Max parallel package jobs
        fail_fast: Stop on first failure (sequential mode only)
        verbose: Show verbose output
        quiet: Suppress detailed output for failed tests
        dry_run: Only show what would be executed
        timeout: Timeout in seconds per version (None = no timeout)
        coverage: Enable coverage collection
        coverage_report: Coverage report formats
        coverage_fail_under: Minimum coverage threshold
    """
    # Create workspace config
    try:
        workspace_config = WorkspaceConfig.from_paths(
            paths=paths,
            parallel=parallel_packages,
            max_workers=package_jobs,
        )
    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)

    # Validate workspace
    errors = workspace_config.validate()
    if errors:
        for error in errors:
            print_error(error)
        raise typer.Exit(1)

    # Create multi-package runner
    try:
        multi_runner = MultiPackageRunner(
            config=workspace_config,
            explicit_versions=python_versions,
        )
    except Exception as e:
        print_error(f"Initializing multi-package runner: {e}")
        raise typer.Exit(1)

    # Check coverage availability if enabled
    if coverage and not dry_run and not check_coverage_available():
        print_error(
            "coverage not found. Install with: pip install coverage\n"
            "Or add coverage to your project dependencies."
        )
        raise typer.Exit(1)

    # Create run options
    options = RunOptions(
        parallel=parallel,
        max_jobs=jobs,
        fail_fast=fail_fast,
        verbose=verbose,
        dry_run=dry_run,
        timeout=timeout,
        coverage=coverage,
    )

    # Handle dry-run mode
    if dry_run:
        _display_multi_package_dry_run(multi_runner, options, timeout=timeout)
        return

    # Display packages being tested
    pkg_names = [pkg.display_name for pkg in workspace_config.packages]
    pkg_mode = "parallel" if parallel_packages else "sequential"
    version_mode = "parallel" if parallel else "sequential"

    print_info(f"[bold]Testing {len(pkg_names)} packages:[/bold] {', '.join(pkg_names)}")
    print_info(f"[bold]Mode:[/bold] packages={pkg_mode}, versions={version_mode}")
    if coverage:
        print_info("[bold]Coverage:[/bold] enabled")
    if timeout:
        print_info(f"[bold]Timeout:[/bold] {timeout}s per version")
    if verbose:
        if parallel_packages and package_jobs:
            print_info(f"[dim]Max parallel packages:[/dim] {package_jobs}")
        if parallel and jobs:
            print_info(f"[dim]Max parallel versions per package:[/dim] {jobs}")
    print_info("")

    # Run tests with live display
    try:
        workspace_result = _run_multi_package_with_display(
            multi_runner, options, show_versions=verbose
        )
    except Exception as e:
        print_error(f"Test execution failed: {e}")
        raise typer.Exit(1)

    # Display results
    print_info("")
    display_multi_package_results(workspace_result)

    # Show captured output for failed tests (unless --quiet)
    if not quiet:
        for pkg_name, pkg_result in workspace_result.package_results.items():
            if not pkg_result.success:
                failed_output = pkg_result.get_failed_output()
                if failed_output:
                    console.print(f"\n[bold red]Failed output for {pkg_name}:[/bold red]")
                    console.print(failed_output)

    # Handle per-package coverage reporting
    coverage_failed = False
    if coverage and workspace_result.all_passed:
        print_info("\n[bold]Coverage Reports:[/bold]")
        for pkg_name, pkg_result in workspace_result.package_results.items():
            pkg_path = pkg_result.package.path
            versions = list(pkg_result.results.keys())

            # Determine report formats from first package's config (or use defaults)
            report_formats = coverage_report if coverage_report else ["term"]
            fail_under = coverage_fail_under

            print_info(f"\n[cyan]{pkg_name}:[/cyan]")
            success = _handle_coverage_reporting(
                pkg_path, versions, report_formats, fail_under, combine=True
            )
            if not success:
                coverage_failed = True

    # Exit with error if any tests failed or coverage check failed
    if not workspace_result.all_passed or coverage_failed:
        raise typer.Exit(1)


def _display_multi_package_dry_run(
    multi_runner: MultiPackageRunner,
    options: RunOptions,
    timeout: float | None = None,
) -> None:
    """Display what would be executed in multi-package dry-run mode.

    Args:
        multi_runner: The multi-package runner
        options: Run options
        timeout: Timeout in seconds per version
    """
    console.print("[bold]Dry run mode - no tests will be executed[/bold]\n")

    # Summary
    packages = multi_runner.packages
    console.print(f"[bold]Packages to test:[/bold] {len(packages)}")
    console.print(
        f"[bold]Package parallelism:[/bold] "
        f"{'parallel' if multi_runner.config.parallel_packages else 'sequential'}"
    )
    if multi_runner.config.max_package_workers:
        console.print(
            f"[bold]Max parallel packages:[/bold] {multi_runner.config.max_package_workers}"
        )
    console.print(
        f"[bold]Version parallelism:[/bold] {'parallel' if options.parallel else 'sequential'}"
    )
    if options.max_jobs:
        console.print(f"[bold]Max parallel versions:[/bold] {options.max_jobs}")
    console.print(f"[bold]Timeout:[/bold] {f'{timeout}s per version' if timeout else 'disabled'}")
    console.print("")

    # Per-package details
    for pkg in packages:
        console.print(f"[bold cyan]{pkg.display_name}[/bold cyan]")
        console.print(f"  Path: {pkg.path}")
        try:
            versions = multi_runner.get_package_versions(pkg.display_name)
            console.print(f"  Versions: {', '.join(versions)}")
        except Exception as e:
            console.print(f"  [red]Error resolving versions: {e}[/red]")
        console.print("")


@app.command()
def versions(
    path: Annotated[
        Path,
        typer.Argument(
            help="Path to the Python package",
            exists=True,
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
        ),
    ] = Path("."),
) -> None:
    """Show Python versions that would be tested.

    Displays a table showing which Python versions are supported
    and which are compatible with the package's requires-python.

    Example:
        testudos versions
        testudos versions ./my-package
    """
    pyproject_path = path / "pyproject.toml"

    # Get supported versions
    try:
        supported = get_supported_python_versions()
    except Exception as e:
        print_error(f"Fetching supported versions: {e}")
        raise typer.Exit(1)

    # Get versions that would be tested
    try:
        test_versions = resolve_test_versions(pyproject_path)
    except VersionResolutionError as e:
        print_error(str(e))
        raise typer.Exit(1)

    display_versions_table(supported, test_versions)


# Coverage subcommand group
coverage_app = typer.Typer(
    name="coverage",
    help="Coverage data management commands",
)
app.add_typer(coverage_app, name="coverage")


@coverage_app.command("combine")
def coverage_combine(
    path: Annotated[
        Path,
        typer.Argument(
            help="Path to the Python package",
            exists=True,
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
        ),
    ] = Path("."),
) -> None:
    """Combine coverage data from multiple Python versions.

    This command combines coverage data files generated by running
    tests with --coverage across multiple Python versions.

    Example:
        testudos coverage combine
        testudos coverage combine ./my-package
    """
    if not check_coverage_available():
        print_error("coverage not found. Install with: pip install coverage")
        raise typer.Exit(1)

    data_files = list_coverage_data_files(path)
    if not data_files:
        print_error("No coverage data files found. Run tests with --coverage first.")
        raise typer.Exit(1)

    print_info(f"[bold]Found {len(data_files)} coverage data file(s)[/bold]")
    for f in data_files:
        print_info(f"  {f.name}")

    async def do_combine() -> CoverageResult:
        return await run_coverage_combine(path, data_files)

    result = asyncio.run(do_combine())

    if result.success:
        print_info(f"\n[green]Combined coverage data:[/green] {result.data_file}")
    else:
        print_error(result.error or "Failed to combine coverage data")
        raise typer.Exit(1)


@coverage_app.command("report")
def coverage_report_cmd(
    path: Annotated[
        Path,
        typer.Argument(
            help="Path to the Python package",
            exists=True,
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
        ),
    ] = Path("."),
    format: Annotated[
        list[str],
        typer.Option(
            "--format",
            "-f",
            help="Report format(s): term, term-missing, html, xml, json, lcov",
        ),
    ] = ["term"],
    fail_under: Annotated[
        float | None,
        typer.Option(
            "--fail-under",
            help="Fail if coverage percentage is below this threshold",
            min=0,
            max=100,
        ),
    ] = None,
) -> None:
    """Generate coverage report from collected data.

    Generates a coverage report from the combined coverage data.
    If no combined data exists, uses the most recent version-specific data.

    Example:
        testudos coverage report
        testudos coverage report --format html --format xml
        testudos coverage report --fail-under 80
    """
    if not check_coverage_available():
        print_error("coverage not found. Install with: pip install coverage")
        raise typer.Exit(1)

    # Try to find coverage data
    combined_path = get_combined_coverage_path(path)
    if combined_path.exists():
        data_file = combined_path
        print_info(f"[bold]Using combined coverage data:[/bold] {data_file}")
    else:
        data_files = list_coverage_data_files(path)
        if not data_files:
            print_error("No coverage data found. Run tests with --coverage first.")
            raise typer.Exit(1)
        data_file = data_files[-1]  # Use most recent
        print_info(f"[bold]Using coverage data:[/bold] {data_file}")

    async def do_report() -> CoverageResult:
        return await generate_coverage_report(path, data_file, format, fail_under)

    result = asyncio.run(do_report())

    if result.summary:
        print_info("")
        display_coverage_summary(result.summary)

    if result.report_paths:
        display_coverage_reports(result.report_paths)

    if not result.success:
        print_error(result.error or "Coverage check failed")
        raise typer.Exit(1)


@coverage_app.command("clean")
def coverage_clean(
    path: Annotated[
        Path,
        typer.Argument(
            help="Path to the Python package",
            exists=True,
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
        ),
    ] = Path("."),
) -> None:
    """Remove all coverage data files.

    Removes the .testudos/coverage directory and all coverage data.

    Example:
        testudos coverage clean
        testudos coverage clean ./my-package
    """
    from testudos.coverage import COVERAGE_DIR

    coverage_dir = path / COVERAGE_DIR
    if not coverage_dir.exists():
        print_info("No coverage data to clean")
        return

    clean_coverage_data(path)
    print_info(f"[green]Cleaned coverage data from:[/green] {coverage_dir}")


@app.callback()
def main() -> None:
    """Testudos - Multi-Python version test harness.

    A testing harness for Python packages using uv's isolated environments.
    It automatically determines which Python versions to test based on
    currently supported versions and your package's requires-python setting.
    """
    pass


if __name__ == "__main__":
    app()
