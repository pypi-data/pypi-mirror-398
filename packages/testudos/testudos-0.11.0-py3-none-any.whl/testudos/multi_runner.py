"""Multi-package test runner for testudos.

This module provides the MultiPackageRunner class that orchestrates
test execution across multiple packages, supporting parallel execution
at both the package and Python version levels.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from testudos.executor import TestResult, TestStatus
from testudos.runner import RunOptions, TestRunner
from testudos.workspace import (
    PackageResult,
    PackageSpec,
    WorkspaceConfig,
    WorkspaceResult,
)

if TYPE_CHECKING:
    pass


# Type alias for the multi-package status callback
# Signature: (package_name, version, status, result)
PackageStatusCallback = Callable[[str, str, TestStatus, TestResult | None], None]


@dataclass
class PackageRunContext:
    """Context for a single package test run.

    Holds the package specification, its TestRunner, and resolved versions.
    """

    package: PackageSpec
    runner: TestRunner
    versions: list[str]


class MultiPackageRunner:
    """Orchestrates test execution across multiple packages.

    This class manages running tests for multiple packages, optionally
    in parallel. Each package gets its own TestRunner instance, preserving
    the isolation of the single-package behavior.

    Example:
        config = WorkspaceConfig.from_paths([Path("./pkg1"), Path("./pkg2")])
        runner = MultiPackageRunner(config)
        results = await runner.run_all_async(RunOptions(parallel=True))
    """

    def __init__(
        self,
        config: WorkspaceConfig,
        explicit_versions: list[str] | None = None,
    ) -> None:
        """Initialize the multi-package runner.

        Args:
            config: Workspace configuration with packages and parallelism settings
            explicit_versions: Optional list of Python versions to test for all packages
        """
        self.config = config
        self._explicit_versions = explicit_versions
        self._contexts: dict[str, PackageRunContext] = {}
        self._initialized = False

    def _ensure_initialized(self) -> None:
        """Lazily initialize TestRunners for all packages."""
        if self._initialized:
            return

        for pkg in self.config.packages:
            runner = TestRunner(
                project_path=pkg.path,
                explicit_versions=self._explicit_versions,
            )
            self._contexts[pkg.display_name] = PackageRunContext(
                package=pkg,
                runner=runner,
                versions=runner.versions,
            )

        self._initialized = True

    @property
    def packages(self) -> list[PackageSpec]:
        """Get the list of packages to test."""
        return self.config.packages

    def get_package_versions(self, package_name: str) -> list[str]:
        """Get the Python versions that will be tested for a package.

        Args:
            package_name: Name of the package

        Returns:
            List of version strings

        Raises:
            KeyError: If package is not found
        """
        self._ensure_initialized()
        return self._contexts[package_name].versions

    def get_all_versions(self) -> dict[str, list[str]]:
        """Get all Python versions for all packages.

        Returns:
            Dictionary mapping package name to list of versions
        """
        self._ensure_initialized()
        return {name: ctx.versions for name, ctx in self._contexts.items()}

    async def run_all_async(
        self,
        options: RunOptions,
        on_status_change: PackageStatusCallback | None = None,
    ) -> WorkspaceResult:
        """Run tests for all packages asynchronously.

        Args:
            options: Run options (parallel, jobs, etc.)
            on_status_change: Optional callback for status updates.
                Called with (package_name, version, status, result).

        Returns:
            WorkspaceResult with results for all packages
        """
        self._ensure_initialized()

        if self.config.parallel_packages:
            return await self._run_packages_parallel(options, on_status_change)
        else:
            return await self._run_packages_sequential(options, on_status_change)

    async def _run_packages_parallel(
        self,
        options: RunOptions,
        on_status_change: PackageStatusCallback | None,
    ) -> WorkspaceResult:
        """Run packages in parallel.

        Uses an asyncio semaphore to limit concurrent packages.
        """
        max_workers = self.config.max_package_workers or len(self._contexts)
        semaphore = asyncio.Semaphore(max_workers)

        async def run_single_package(
            name: str,
            ctx: PackageRunContext,
        ) -> tuple[str, PackageResult]:
            async with semaphore:
                return await self._run_package(name, ctx, options, on_status_change)

        # Create tasks for all packages
        tasks = [run_single_package(name, ctx) for name, ctx in self._contexts.items()]

        # Run all packages concurrently
        results = await asyncio.gather(*tasks)

        # Build workspace result
        return WorkspaceResult(package_results={name: result for name, result in results})

    async def _run_packages_sequential(
        self,
        options: RunOptions,
        on_status_change: PackageStatusCallback | None,
    ) -> WorkspaceResult:
        """Run packages sequentially."""
        package_results: dict[str, PackageResult] = {}

        for name, ctx in self._contexts.items():
            _, result = await self._run_package(name, ctx, options, on_status_change)
            package_results[name] = result

        return WorkspaceResult(package_results=package_results)

    async def _run_package(
        self,
        name: str,
        ctx: PackageRunContext,
        options: RunOptions,
        on_status_change: PackageStatusCallback | None,
    ) -> tuple[str, PackageResult]:
        """Run tests for a single package.

        Args:
            name: Package name
            ctx: Package run context with runner and versions
            options: Run options
            on_status_change: Optional callback

        Returns:
            Tuple of (package_name, PackageResult)
        """

        # Create a package-scoped callback that prefixes with package name
        def package_callback(
            version: str,
            status: TestStatus,
            result: TestResult | None,
        ) -> None:
            if on_status_change:
                on_status_change(name, version, status, result)

        # Run tests using the package's TestRunner
        results = await ctx.runner.run_async(
            options=options,
            on_status_change=package_callback,
        )

        return name, PackageResult(package=ctx.package, results=results)

    def run_all(
        self,
        options: RunOptions,
        on_status_change: PackageStatusCallback | None = None,
    ) -> WorkspaceResult:
        """Synchronous wrapper for run_all_async.

        Args:
            options: Run options
            on_status_change: Optional callback

        Returns:
            WorkspaceResult with results for all packages
        """
        return asyncio.run(self.run_all_async(options, on_status_change))


class MultiPackageRunnerError(Exception):
    """Raised when multi-package test execution fails."""

    pass
