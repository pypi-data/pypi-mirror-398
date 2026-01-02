"""Test runner orchestration for testudos.

This module provides a high-level TestRunner class that orchestrates
test execution across multiple Python versions, abstracting the details
of version resolution, execution strategy, and result collection.
"""

import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from testudos.config import TestudosConfig
from testudos.executor import (
    TestResult,
    TestStatus,
    run_tests_parallel_async,
    run_tests_sequential,
)
from testudos.versions import resolve_test_versions


@dataclass
class RunOptions:
    """Options for a test run.

    Attributes:
        parallel: Whether to run tests in parallel
        max_jobs: Maximum number of parallel jobs (None = number of versions)
        fail_fast: Stop on first failure (sequential mode only)
        verbose: Show verbose output
        dry_run: Only show what would be executed, don't run tests
        timeout: Timeout in seconds per Python version (None = no timeout)
        coverage: Whether to collect coverage data
        coverage_source: Source directories for coverage measurement
    """

    parallel: bool = False
    max_jobs: int | None = None
    fail_fast: bool = True
    verbose: bool = False
    dry_run: bool = False
    timeout: float | None = None
    coverage: bool = False
    coverage_source: list[str] | None = None


@dataclass
class RunPlan:
    """A planned test run before execution.

    This represents what will be executed, useful for dry-run mode
    and for displaying information to the user.

    Attributes:
        versions: Python versions that will be tested
        test_command: The test command to run
        test_args: Additional arguments for the test command
        working_dir: Working directory for test execution
        parallel: Whether tests will run in parallel
        max_jobs: Maximum parallel jobs
        timeout: Timeout in seconds per Python version (None = no timeout)
        coverage: Whether coverage collection is enabled
        coverage_source: Source directories for coverage
        commands: List of shell commands that will be executed
    """

    versions: list[str]
    test_command: str
    test_args: list[str]
    working_dir: Path
    parallel: bool
    max_jobs: int | None
    timeout: float | None = None
    coverage: bool = False
    coverage_source: list[str] | None = None
    commands: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Generate the commands that will be executed."""
        if not self.commands:
            self.commands = [self._build_command(version) for version in self.versions]

    def _build_command(self, version: str) -> str:
        """Build the command string for a given version."""
        cmd_parts = [
            "uv",
            "run",
            "--isolated",
            f"--python={version}",
            "--directory",
            str(self.working_dir),
        ]

        if self.coverage:
            # Add coverage wrapping
            from testudos.coverage import get_coverage_data_path

            coverage_data_file = get_coverage_data_path(self.working_dir, version)
            source_dirs = self.coverage_source if self.coverage_source else ["src"]
            cmd_parts.extend(
                [
                    "coverage",
                    "run",
                    f"--data-file={coverage_data_file}",
                    f"--source={','.join(source_dirs)}",
                    "--branch",
                    "-m",
                ]
            )

        cmd_parts.append(self.test_command)
        cmd_parts.extend(self.test_args)
        return " ".join(cmd_parts)


class TestRunner:
    """Orchestrates test execution across multiple Python versions.

    This class provides a high-level interface for running tests,
    handling version resolution, configuration loading, and execution
    strategy selection.

    Example:
        runner = TestRunner(project_path=Path("."))
        results = runner.run(RunOptions(parallel=True))
    """

    def __init__(
        self,
        project_path: Path,
        config: TestudosConfig | None = None,
        explicit_versions: list[str] | None = None,
    ) -> None:
        """Initialize the test runner.

        Args:
            project_path: Path to the project directory
            config: Optional pre-loaded configuration (loads from pyproject.toml if None)
            explicit_versions: Optional list of specific versions to test
        """
        self.project_path = project_path
        self.pyproject_path = project_path / "pyproject.toml"
        self._explicit_versions = explicit_versions

        # Load configuration if not provided
        if config is None:
            self._config = TestudosConfig.from_pyproject(self.pyproject_path)
        else:
            self._config = config

        self._resolved_versions: list[str] | None = None

    @property
    def config(self) -> TestudosConfig:
        """Get the loaded configuration."""
        return self._config

    @property
    def versions(self) -> list[str]:
        """Get the resolved Python versions to test.

        Raises:
            VersionResolutionError: If version resolution fails
        """
        if self._resolved_versions is None:
            explicit = self._explicit_versions or self._config.python_versions
            self._resolved_versions = resolve_test_versions(
                pyproject_path=self.pyproject_path,
                explicit_versions=explicit,
            )
        return self._resolved_versions

    def plan(self, options: RunOptions | None = None) -> RunPlan:
        """Create a plan for the test run.

        Args:
            options: Run options (uses defaults if None)

        Returns:
            RunPlan describing what will be executed
        """
        options = options or RunOptions()

        # Determine effective settings
        parallel = options.parallel or self._config.parallel
        max_jobs = options.max_jobs if options.max_jobs is not None else self._config.max_jobs
        timeout = options.timeout if options.timeout is not None else self._config.timeout
        coverage = options.coverage or self._config.coverage
        coverage_source = options.coverage_source

        return RunPlan(
            versions=self.versions,
            test_command=self._config.test_command,
            test_args=self._config.test_args,
            working_dir=self.project_path,
            parallel=parallel,
            max_jobs=max_jobs,
            timeout=timeout,
            coverage=coverage,
            coverage_source=coverage_source,
        )

    def run(
        self,
        options: RunOptions | None = None,
        on_status_change: Callable[[str, TestStatus, TestResult | None], None] | None = None,
    ) -> dict[str, TestResult]:
        """Run tests across all resolved Python versions.

        Args:
            options: Run options (uses defaults if None)
            on_status_change: Optional callback for parallel execution status updates

        Returns:
            Dictionary mapping version string to TestResult
        """
        options = options or RunOptions()
        plan = self.plan(options)

        if options.dry_run:
            # In dry-run mode, return empty results
            return {}

        if plan.parallel:
            return asyncio.run(
                run_tests_parallel_async(
                    versions=plan.versions,
                    test_command=plan.test_command,
                    test_args=plan.test_args,
                    working_dir=plan.working_dir,
                    max_concurrent=plan.max_jobs,
                    on_status_change=on_status_change,
                    timeout=plan.timeout,
                    coverage=plan.coverage,
                    coverage_source=plan.coverage_source,
                )
            )
        else:
            return run_tests_sequential(
                versions=plan.versions,
                test_command=plan.test_command,
                test_args=plan.test_args,
                working_dir=plan.working_dir,
                fail_fast=options.fail_fast,
                capture_output=False,
                timeout=plan.timeout,
                coverage=plan.coverage,
                coverage_source=plan.coverage_source,
            )

    async def run_async(
        self,
        options: RunOptions | None = None,
        on_status_change: Callable[[str, TestStatus, TestResult | None], None] | None = None,
    ) -> dict[str, TestResult]:
        """Run tests asynchronously across all resolved Python versions.

        This method uses asyncio for parallel execution, providing better
        resource utilization than the thread-based run() method.

        Args:
            options: Run options (uses defaults if None)
            on_status_change: Optional callback for status updates

        Returns:
            Dictionary mapping version string to TestResult
        """
        options = options or RunOptions()
        plan = self.plan(options)

        if options.dry_run:
            return {}

        if plan.parallel:
            return await run_tests_parallel_async(
                versions=plan.versions,
                test_command=plan.test_command,
                test_args=plan.test_args,
                working_dir=plan.working_dir,
                max_concurrent=plan.max_jobs,
                on_status_change=on_status_change,
                timeout=plan.timeout,
                coverage=plan.coverage,
                coverage_source=plan.coverage_source,
            )
        else:
            # For sequential execution, use the sync version
            # (async would provide no benefit here)
            return run_tests_sequential(
                versions=plan.versions,
                test_command=plan.test_command,
                test_args=plan.test_args,
                working_dir=plan.working_dir,
                fail_fast=options.fail_fast,
                capture_output=False,
                timeout=plan.timeout,
                coverage=plan.coverage,
                coverage_source=plan.coverage_source,
            )
