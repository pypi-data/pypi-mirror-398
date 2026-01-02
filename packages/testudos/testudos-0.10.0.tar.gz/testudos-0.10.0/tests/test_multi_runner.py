"""Tests for multi_runner module."""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from testudos.executor import TestResult, TestStatus
from testudos.multi_runner import MultiPackageRunner
from testudos.runner import RunOptions
from testudos.workspace import WorkspaceConfig


@pytest.fixture
def sample_packages(tmp_path: Path) -> list[Path]:
    """Create sample package directories with pyproject.toml files."""
    packages = []
    for name in ["pkg1", "pkg2", "pkg3"]:
        pkg_dir = tmp_path / name
        pkg_dir.mkdir()
        pyproject = pkg_dir / "pyproject.toml"
        pyproject.write_text(f"""
[project]
name = "{name}"
version = "1.0.0"
requires-python = ">=3.11"
""")
        packages.append(pkg_dir)
    return packages


@pytest.fixture
def workspace_config(sample_packages: list[Path]) -> WorkspaceConfig:
    """Create a workspace config from sample packages."""
    return WorkspaceConfig.from_paths(sample_packages[:2])  # Use 2 packages


class TestMultiPackageRunner:
    """Tests for MultiPackageRunner class."""

    def test_init(self, workspace_config: WorkspaceConfig) -> None:
        """Test MultiPackageRunner initialization."""
        runner = MultiPackageRunner(config=workspace_config)
        assert runner.config == workspace_config
        assert runner._initialized is False

    def test_packages_property(self, workspace_config: WorkspaceConfig) -> None:
        """Test packages property returns config packages."""
        runner = MultiPackageRunner(config=workspace_config)
        assert runner.packages == workspace_config.packages

    def test_get_all_versions(self, workspace_config: WorkspaceConfig) -> None:
        """Test get_all_versions returns versions for all packages."""
        runner = MultiPackageRunner(config=workspace_config)

        with patch("testudos.runner.resolve_test_versions") as mock_resolve:
            mock_resolve.return_value = ["3.11", "3.12"]
            versions = runner.get_all_versions()

        assert len(versions) == 2
        for pkg_versions in versions.values():
            assert pkg_versions == ["3.11", "3.12"]

    def test_get_package_versions(self, workspace_config: WorkspaceConfig) -> None:
        """Test get_package_versions for a specific package."""
        runner = MultiPackageRunner(config=workspace_config)
        pkg_name = workspace_config.packages[0].display_name

        with patch("testudos.runner.resolve_test_versions") as mock_resolve:
            mock_resolve.return_value = ["3.11", "3.12"]
            versions = runner.get_package_versions(pkg_name)

        assert versions == ["3.11", "3.12"]

    def test_get_package_versions_unknown_package(self, workspace_config: WorkspaceConfig) -> None:
        """Test get_package_versions raises for unknown package."""
        runner = MultiPackageRunner(config=workspace_config)

        with patch("testudos.runner.resolve_test_versions") as mock_resolve:
            mock_resolve.return_value = ["3.11"]
            # Initialize first
            runner._ensure_initialized()

        with pytest.raises(KeyError):
            runner.get_package_versions("nonexistent-package")

    @pytest.mark.asyncio
    async def test_run_all_async_parallel(self, workspace_config: WorkspaceConfig) -> None:
        """Test run_all_async runs packages in parallel."""
        runner = MultiPackageRunner(config=workspace_config)
        options = RunOptions(parallel=True)

        # Mock the TestRunner.run_async
        with patch("testudos.runner.resolve_test_versions") as mock_resolve:
            mock_resolve.return_value = ["3.11"]

            with patch.object(runner, "_run_package", new_callable=AsyncMock) as mock_run:
                mock_run.return_value = (
                    "pkg",
                    MagicMock(success=True, results={}),
                )

                await runner.run_all_async(options)

        assert mock_run.call_count == 2  # Two packages

    @pytest.mark.asyncio
    async def test_run_all_async_sequential(self, workspace_config: WorkspaceConfig) -> None:
        """Test run_all_async runs packages sequentially when configured."""
        workspace_config.parallel_packages = False
        runner = MultiPackageRunner(config=workspace_config)
        options = RunOptions(parallel=False)

        with patch("testudos.runner.resolve_test_versions") as mock_resolve:
            mock_resolve.return_value = ["3.11"]

            with patch.object(runner, "_run_package", new_callable=AsyncMock) as mock_run:
                mock_run.return_value = (
                    "pkg",
                    MagicMock(success=True, results={}),
                )

                await runner.run_all_async(options)

        assert mock_run.call_count == 2

    @pytest.mark.asyncio
    async def test_run_all_async_with_callback(self, workspace_config: WorkspaceConfig) -> None:
        """Test run_all_async calls status callback."""
        runner = MultiPackageRunner(config=workspace_config)
        options = RunOptions(parallel=True)

        callbacks_received: list[tuple] = []

        def callback(
            pkg_name: str,
            version: str,
            status: TestStatus,
            result: TestResult | None,
        ) -> None:
            callbacks_received.append((pkg_name, version, status))

        with patch("testudos.runner.resolve_test_versions") as mock_resolve:
            mock_resolve.return_value = ["3.11"]

            # Mock run_async to actually call the callback
            async def mock_run_async(options, on_status_change):
                if on_status_change:
                    on_status_change("3.11", TestStatus.RUNNING, None)
                    on_status_change(
                        "3.11",
                        TestStatus.PASSED,
                        TestResult(version="3.11", success=True, return_code=0),
                    )
                return {"3.11": TestResult(version="3.11", success=True, return_code=0)}

            with patch("testudos.runner.TestRunner.run_async", side_effect=mock_run_async):
                await runner.run_all_async(options, on_status_change=callback)

        # Should have received callbacks for both packages
        assert len(callbacks_received) >= 2

    @pytest.mark.asyncio
    async def test_run_all_async_respects_max_workers(self, sample_packages: list[Path]) -> None:
        """Test run_all_async respects max_package_workers."""
        # Use all 3 packages with max 1 worker
        config = WorkspaceConfig.from_paths(sample_packages, max_workers=1)
        runner = MultiPackageRunner(config=config)
        options = RunOptions(parallel=True)

        execution_order: list[str] = []
        running_count = 0
        max_concurrent = 0

        async def mock_run_package(name, ctx, opts, cb):
            nonlocal running_count, max_concurrent
            running_count += 1
            max_concurrent = max(max_concurrent, running_count)
            execution_order.append(f"start:{name}")
            await asyncio.sleep(0.01)  # Simulate some work
            execution_order.append(f"end:{name}")
            running_count -= 1
            return (name, MagicMock(success=True, results={}))

        with patch("testudos.runner.resolve_test_versions") as mock_resolve:
            mock_resolve.return_value = ["3.11"]

            with patch.object(runner, "_run_package", side_effect=mock_run_package):
                await runner.run_all_async(options)

        # With max_workers=1, max concurrent should be 1
        assert max_concurrent == 1

    def test_run_all_sync(self, workspace_config: WorkspaceConfig) -> None:
        """Test run_all synchronous wrapper."""
        runner = MultiPackageRunner(config=workspace_config)
        options = RunOptions(parallel=True)

        with patch("testudos.runner.resolve_test_versions") as mock_resolve:
            mock_resolve.return_value = ["3.11"]

            with patch.object(runner, "_run_package", new_callable=AsyncMock) as mock_run:
                mock_run.return_value = (
                    "pkg",
                    MagicMock(success=True, results={}),
                )

                result = runner.run_all(options)

        assert result is not None

    def test_explicit_versions_passed_to_runners(self, workspace_config: WorkspaceConfig) -> None:
        """Test that explicit_versions is passed to TestRunners."""
        explicit = ["3.11", "3.12"]
        runner = MultiPackageRunner(config=workspace_config, explicit_versions=explicit)

        with patch("testudos.runner.resolve_test_versions") as mock_resolve:
            mock_resolve.return_value = explicit
            runner._ensure_initialized()

        # Verify runners were created with explicit versions
        for ctx in runner._contexts.values():
            assert ctx.runner._explicit_versions == explicit
