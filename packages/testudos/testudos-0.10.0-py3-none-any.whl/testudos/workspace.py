"""Workspace and multi-package support for testudos.

This module provides data structures and utilities for testing multiple
packages in a workspace or monorepo setup.
"""

from __future__ import annotations

import sys

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib  # type: ignore[import-not-found]
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from testudos.executor import TestResult


@dataclass
class PackageSpec:
    """Specification for a single package in a workspace.

    Attributes:
        path: Absolute path to the package directory
        name: Display name for the package (derived from pyproject.toml or path)
    """

    path: Path
    name: str | None = None

    def __post_init__(self) -> None:
        """Ensure path is absolute and derive name if not provided."""
        self.path = self.path.resolve()
        if self.name is None:
            self.name = self._derive_name()

    def _derive_name(self) -> str:
        """Derive package name from pyproject.toml or directory name."""
        pyproject_path = self.path / "pyproject.toml"
        if pyproject_path.exists():
            try:
                with open(pyproject_path, "rb") as f:
                    data = tomllib.load(f)
                # Try [project].name first (PEP 621)
                project_name = data.get("project", {}).get("name")
                if project_name:
                    return str(project_name)
                # Fallback to [tool.poetry].name for Poetry projects
                poetry_name = data.get("tool", {}).get("poetry", {}).get("name")
                if poetry_name:
                    return str(poetry_name)
            except Exception:
                pass
        # Fallback to directory name
        return self.path.name

    @property
    def display_name(self) -> str:
        """Short name for display purposes."""
        return self.name or self.path.name

    @property
    def pyproject_path(self) -> Path:
        """Path to the package's pyproject.toml."""
        return self.path / "pyproject.toml"

    def has_pyproject(self) -> bool:
        """Check if the package has a pyproject.toml file."""
        return self.pyproject_path.exists()


@dataclass
class PackageResult:
    """Results for a single package across all Python versions.

    Attributes:
        package: The package specification
        results: Dictionary mapping version string to TestResult
    """

    package: PackageSpec
    results: dict[str, TestResult] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        """Whether all tests passed for this package."""
        if not self.results:
            return False
        return all(r.success for r in self.results.values())

    @property
    def total_duration(self) -> float:
        """Total duration of all test runs for this package."""
        return sum(r.duration or 0 for r in self.results.values())

    @property
    def passed_count(self) -> int:
        """Number of versions that passed."""
        return sum(1 for r in self.results.values() if r.success)

    @property
    def failed_count(self) -> int:
        """Number of versions that failed."""
        return sum(1 for r in self.results.values() if not r.success)

    def get_failed_output(self) -> str:
        """Get formatted output for failed tests.

        Returns:
            Formatted string with failure details for each failed version
        """
        lines: list[str] = []
        for version, result in sorted(self.results.items()):
            if not result.success:
                lines.append(f"\n{'=' * 60}")
                lines.append(f"Package: {self.package.display_name}")
                lines.append(f"Python {version}")
                lines.append("=" * 60)
                if result.output:
                    lines.append(result.output)
                if result.error:
                    lines.append(result.error)
        return "\n".join(lines)


@dataclass
class WorkspaceResult:
    """Aggregated results for all packages in a workspace.

    Attributes:
        package_results: Dictionary mapping package name to PackageResult
    """

    package_results: dict[str, PackageResult] = field(default_factory=dict)

    @property
    def all_passed(self) -> bool:
        """Whether all packages passed all tests."""
        if not self.package_results:
            return False
        return all(pr.success for pr in self.package_results.values())

    @property
    def total_packages(self) -> int:
        """Total number of packages."""
        return len(self.package_results)

    @property
    def passed_packages(self) -> int:
        """Number of packages where all tests passed."""
        return sum(1 for pr in self.package_results.values() if pr.success)

    @property
    def failed_packages(self) -> int:
        """Number of packages with at least one failure."""
        return sum(1 for pr in self.package_results.values() if not pr.success)

    @property
    def total_duration(self) -> float:
        """Total duration across all packages."""
        return sum(pr.total_duration for pr in self.package_results.values())

    def get_summary(self) -> dict[str, int]:
        """Get a summary of results.

        Returns:
            Dictionary with counts of passed/failed packages and versions
        """
        total_versions = 0
        passed_versions = 0
        failed_versions = 0

        for pr in self.package_results.values():
            total_versions += len(pr.results)
            passed_versions += pr.passed_count
            failed_versions += pr.failed_count

        return {
            "total_packages": self.total_packages,
            "passed_packages": self.passed_packages,
            "failed_packages": self.failed_packages,
            "total_versions": total_versions,
            "passed_versions": passed_versions,
            "failed_versions": failed_versions,
        }


@dataclass
class WorkspaceConfig:
    """Configuration for multi-package testing.

    Attributes:
        packages: List of package specifications to test
        parallel_packages: Whether to run packages in parallel
        max_package_workers: Maximum number of packages to test concurrently
    """

    packages: list[PackageSpec] = field(default_factory=list)
    parallel_packages: bool = True
    max_package_workers: int | None = None

    @classmethod
    def from_paths(
        cls,
        paths: list[Path],
        parallel: bool = True,
        max_workers: int | None = None,
    ) -> WorkspaceConfig:
        """Create configuration from explicit paths.

        Args:
            paths: List of paths to package directories
            parallel: Whether to run packages in parallel
            max_workers: Maximum concurrent packages

        Returns:
            WorkspaceConfig instance

        Raises:
            ValueError: If any path doesn't exist or isn't a directory
        """
        packages: list[PackageSpec] = []
        for path in paths:
            resolved = path.resolve()
            if not resolved.exists():
                raise ValueError(f"Package path does not exist: {path}")
            if not resolved.is_dir():
                raise ValueError(f"Package path is not a directory: {path}")
            packages.append(PackageSpec(path=resolved))

        return cls(
            packages=packages,
            parallel_packages=parallel,
            max_package_workers=max_workers,
        )

    @classmethod
    def auto_discover(
        cls,
        root: Path,
        exclude_patterns: list[str] | None = None,
        parallel: bool = True,
        max_workers: int | None = None,
    ) -> WorkspaceConfig:
        """Auto-discover packages in a directory.

        Searches for directories containing pyproject.toml files.
        Excludes common non-package directories like .git, node_modules, etc.

        Args:
            root: Root directory to search
            exclude_patterns: Additional directory names to exclude
            parallel: Whether to run packages in parallel
            max_workers: Maximum concurrent packages

        Returns:
            WorkspaceConfig with discovered packages
        """
        root = root.resolve()
        exclude = {".git", ".hg", ".svn", "node_modules", "venv", ".venv", "__pycache__"}
        if exclude_patterns:
            exclude.update(exclude_patterns)

        packages: list[PackageSpec] = []
        for pyproject in root.rglob("pyproject.toml"):
            pkg_dir = pyproject.parent

            # Skip if any parent directory is excluded
            if any(
                part.startswith(".") or part in exclude for part in pkg_dir.relative_to(root).parts
            ):
                continue

            # Skip the root itself if it has a pyproject.toml (that's not a package discovery)
            if pkg_dir == root:
                continue

            packages.append(PackageSpec(path=pkg_dir))

        # Sort by path for consistent ordering
        packages.sort(key=lambda p: p.path)

        return cls(
            packages=packages,
            parallel_packages=parallel,
            max_package_workers=max_workers,
        )

    def validate(self) -> list[str]:
        """Validate the workspace configuration.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors: list[str] = []

        if not self.packages:
            errors.append("No packages specified")

        for pkg in self.packages:
            if not pkg.path.exists():
                errors.append(f"Package path does not exist: {pkg.path}")
            elif not pkg.has_pyproject():
                errors.append(f"Package has no pyproject.toml: {pkg.path}")

        # Check for duplicate names
        names = [pkg.display_name for pkg in self.packages]
        seen: set[str] = set()
        for name in names:
            if name in seen:
                errors.append(f"Duplicate package name: {name}")
            seen.add(name)

        if self.max_package_workers is not None and self.max_package_workers < 1:
            errors.append("max_package_workers must be at least 1")

        return errors
