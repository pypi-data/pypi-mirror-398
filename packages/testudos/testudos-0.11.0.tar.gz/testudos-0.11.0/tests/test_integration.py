"""Integration tests for testudos.

These tests verify end-to-end functionality using actual test projects.
"""

import subprocess

import pytest


@pytest.fixture
def sample_package(tmp_path):
    """Create a sample Python package for testing."""
    # Create package structure
    pkg_dir = tmp_path / "sample_pkg"
    pkg_dir.mkdir()

    # Create pyproject.toml
    pyproject = pkg_dir / "pyproject.toml"
    pyproject.write_text(
        """[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "sample-package"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = []

[project.optional-dependencies]
dev = ["pytest>=7.0.0"]

[tool.hatch.build.targets.wheel]
packages = ["src/sample_pkg"]

[tool.testudos]
test-command = "pytest"
test-args = ["-v"]
"""
    )

    # Create source directory
    src_dir = pkg_dir / "src" / "sample_pkg"
    src_dir.mkdir(parents=True)

    # Create __init__.py
    init_file = src_dir / "__init__.py"
    init_file.write_text('"""Sample package for testing."""\n\n__version__ = "0.1.0"\n')

    # Create a simple module
    module_file = src_dir / "calculator.py"
    module_file.write_text(
        '''"""Simple calculator module."""


def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b


def subtract(a: int, b: int) -> int:
    """Subtract b from a."""
    return a - b


def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b


def divide(a: float, b: float) -> float:
    """Divide a by b."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
'''
    )

    # Create tests directory
    tests_dir = pkg_dir / "tests"
    tests_dir.mkdir()

    # Create simple test file that doesn't require imports
    test_file = tests_dir / "test_simple.py"
    test_file.write_text(
        '''"""Simple tests that don't require package imports."""


def test_basic_math():
    """Test basic math operations."""
    assert 2 + 3 == 5
    assert 5 - 3 == 2
    assert 2 * 3 == 6
    assert 6 / 2 == 3.0


def test_string_operations():
    """Test string operations."""
    assert "hello" + " world" == "hello world"
    assert "test".upper() == "TEST"
    assert len("hello") == 5


def test_list_operations():
    """Test list operations."""
    lst = [1, 2, 3]
    assert len(lst) == 3
    assert lst[0] == 1
    lst.append(4)
    assert len(lst) == 4
'''
    )

    return pkg_dir


@pytest.fixture
def failing_package(tmp_path):
    """Create a package with failing tests."""
    pkg_dir = tmp_path / "failing_pkg"
    pkg_dir.mkdir()

    # Create pyproject.toml
    pyproject = pkg_dir / "pyproject.toml"
    pyproject.write_text(
        """[project]
name = "failing-package"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = []

[project.optional-dependencies]
dev = ["pytest>=7.0.0"]
"""
    )

    # Create source
    src_dir = pkg_dir / "src" / "failing_pkg"
    src_dir.mkdir(parents=True)
    (src_dir / "__init__.py").write_text("")

    # Create tests directory
    tests_dir = pkg_dir / "tests"
    tests_dir.mkdir()

    # Create failing test
    test_file = tests_dir / "test_failing.py"
    test_file.write_text(
        '''"""Failing test."""


def test_that_fails():
    """This test always fails."""
    assert False, "This test is designed to fail"
'''
    )

    return pkg_dir


class TestVersionResolutionIntegration:
    """Integration tests for version resolution."""

    def test_resolve_versions_from_project(self, sample_package):
        """Test resolving versions from a real project."""
        from testudos.versions import resolve_test_versions

        versions = resolve_test_versions(sample_package / "pyproject.toml")

        # Should include at least 3.11
        assert "3.11" in versions
        # Should be a list of version strings
        assert all(isinstance(v, str) for v in versions)
        # Should be sorted
        assert versions == sorted(versions, key=lambda v: tuple(map(int, v.split("."))))

    def test_parse_requires_python(self, sample_package):
        """Test parsing requires-python from project."""
        from testudos.versions import parse_requires_python

        specifier = parse_requires_python(sample_package / "pyproject.toml")

        # Should match >=3.11
        assert "3.11.0" in specifier
        assert "3.12.0" in specifier
        assert "3.10.0" not in specifier


class TestConfigIntegration:
    """Integration tests for configuration loading."""

    def test_load_config_from_project(self, sample_package):
        """Test loading config from a real project."""
        from testudos.config import TestudosConfig

        config = TestudosConfig.from_pyproject(sample_package / "pyproject.toml")

        assert config.test_command == "pytest"
        assert config.test_args == ["-v"]

    def test_config_defaults(self, tmp_path):
        """Test config defaults when no tool.testudos section."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """[project]
name = "test"
requires-python = ">=3.11"
"""
        )

        from testudos.config import TestudosConfig

        config = TestudosConfig.from_pyproject(pyproject)

        assert config.test_command == "pytest"
        assert config.test_args == []
        assert config.parallel is False


class TestExecutorIntegration:
    """Integration tests for test execution."""

    @pytest.mark.skipif(
        subprocess.run(["which", "uv"], capture_output=True).returncode != 0,
        reason="uv not available",
    )
    def test_run_tests_on_sample_package(self, sample_package):
        """Test running actual tests on sample package."""
        from testudos.executor import run_single_test

        result = run_single_test(
            version="3.11",
            test_command="pytest",
            test_args=["-v"],
            working_dir=sample_package,
            capture_output=True,
        )

        # Tests should pass
        assert result.success is True
        assert result.return_code == 0
        assert result.duration is not None
        assert result.duration > 0

    @pytest.mark.skipif(
        subprocess.run(["which", "uv"], capture_output=True).returncode != 0,
        reason="uv not available",
    )
    def test_run_failing_tests(self, failing_package):
        """Test running tests that fail."""
        from testudos.executor import run_single_test

        result = run_single_test(
            version="3.11",
            test_command="pytest",
            test_args=["-v"],
            working_dir=failing_package,
            capture_output=True,
        )

        # Tests should fail
        assert result.success is False
        assert result.return_code != 0

    @pytest.mark.skipif(
        subprocess.run(["which", "uv"], capture_output=True).returncode != 0,
        reason="uv not available",
    )
    def test_sequential_execution(self, sample_package):
        """Test sequential test execution."""
        from testudos.executor import run_tests_sequential
        from testudos.versions import resolve_test_versions

        versions = resolve_test_versions(sample_package / "pyproject.toml")[:2]  # Limit to 2

        results = run_tests_sequential(
            versions=versions,
            test_command="pytest",
            test_args=["-v"],
            working_dir=sample_package,
            fail_fast=True,
            capture_output=True,
        )

        # All should pass
        assert all(r.success for r in results.values())
        assert len(results) == len(versions)

    @pytest.mark.skipif(
        subprocess.run(["which", "uv"], capture_output=True).returncode != 0,
        reason="uv not available",
    )
    async def test_parallel_execution(self, sample_package):
        """Test parallel test execution."""
        from testudos.executor import run_tests_parallel_async
        from testudos.versions import resolve_test_versions

        versions = resolve_test_versions(sample_package / "pyproject.toml")[:2]  # Limit to 2

        results = await run_tests_parallel_async(
            versions=versions,
            test_command="pytest",
            test_args=["-v"],
            working_dir=sample_package,
            max_concurrent=2,
        )

        # All should pass
        assert all(r.success for r in results.values())
        assert len(results) == len(versions)


class TestCLIIntegration:
    """Integration tests for CLI commands."""

    @pytest.mark.skipif(
        subprocess.run(["which", "uv"], capture_output=True).returncode != 0,
        reason="uv not available",
    )
    def test_cli_versions_command(self, sample_package):
        """Test CLI versions command on real project."""
        from typer.testing import CliRunner

        from testudos.cli import app

        runner = CliRunner()
        result = runner.invoke(app, ["versions", str(sample_package)])

        assert result.exit_code == 0
        assert "Will test:" in result.stdout
        assert "3.11" in result.stdout


class TestCachingIntegration:
    """Integration tests for caching functionality."""

    def test_version_caching(self, tmp_path):
        """Test that version data is cached."""
        from datetime import timedelta
        from unittest.mock import Mock, patch

        from testudos.versions import (
            CacheConfig,
            _save_cache,
            get_supported_python_versions,
            set_cache_config,
        )

        # Set up temporary cache config
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        config = CacheConfig(
            cache_dir=cache_dir,
            cache_file=cache_dir / "endoflife.json",
            ttl=timedelta(hours=24),
        )
        set_cache_config(config)

        try:
            # Mock API response
            mock_response = Mock()
            mock_response.json.return_value = [
                {"cycle": "3.12", "eol": False},
                {"cycle": "3.11", "eol": False},
            ]
            mock_response.raise_for_status = Mock()

            with patch("httpx.get", return_value=mock_response) as mock_get:
                # First call should hit API
                versions1 = get_supported_python_versions(use_cache=False)
                assert mock_get.call_count == 1

                # Save to cache
                _save_cache(versions1)

                # Second call should use cache
                versions2 = get_supported_python_versions(use_cache=True)
                assert mock_get.call_count == 1  # Still 1, no new call

                assert versions1 == versions2
        finally:
            # Reset to default config
            set_cache_config(CacheConfig.default())

    def test_offline_fallback(self, tmp_path):
        """Test that offline fallback works."""
        from datetime import timedelta
        from unittest.mock import patch

        import httpx

        from testudos.versions import (
            CacheConfig,
            get_supported_python_versions,
            set_cache_config,
        )

        # Set up temporary cache config
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        config = CacheConfig(
            cache_dir=cache_dir,
            cache_file=cache_dir / "endoflife.json",
            ttl=timedelta(hours=24),
        )
        set_cache_config(config)

        try:
            # Mock API failure
            with (
                patch("httpx.get", side_effect=httpx.NetworkError("Network error")),
                pytest.warns(UserWarning, match="bundled fallback"),
            ):
                versions = get_supported_python_versions(use_cache=False)

                # Should return fallback versions
                assert isinstance(versions, list)
                assert len(versions) > 0
                assert "3.11" in versions or "3.12" in versions
        finally:
            # Reset to default config
            set_cache_config(CacheConfig.default())


class TestErrorHandlingIntegration:
    """Integration tests for error handling."""

    def test_missing_pyproject(self, tmp_path):
        """Test error when pyproject.toml is missing."""
        from testudos.versions import VersionResolutionError, resolve_test_versions

        with pytest.raises(VersionResolutionError, match="not found"):
            resolve_test_versions(tmp_path / "nonexistent.toml")

    def test_missing_requires_python(self, tmp_path):
        """Test error when requires-python is missing."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("[project]\nname = 'test'\n")

        from testudos.versions import VersionResolutionError, resolve_test_versions

        with pytest.raises(VersionResolutionError, match="not specified"):
            resolve_test_versions(pyproject)

    def test_no_compatible_versions(self, tmp_path):
        """Test error when no compatible versions."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """[project]
name = "test"
requires-python = ">=3.99"
"""
        )

        from testudos.versions import VersionResolutionError, resolve_test_versions

        with pytest.raises(VersionResolutionError, match="No Python versions found"):
            resolve_test_versions(pyproject)
