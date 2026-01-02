"""Tests for CLI interface."""

import re
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from testudos.cli import app
from testudos.config import TestudosConfig
from testudos.executor import TestResult
from testudos.runner import RunPlan, TestRunner
from testudos.versions import VersionResolutionError


def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from text."""
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


runner = CliRunner()


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project directory with pyproject.toml."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """[project]
name = "test-package"
requires-python = ">=3.11"
version = "0.1.0"

[tool.testudos]
test-command = "pytest"
"""
    )
    return tmp_path


@pytest.fixture
def mock_runner():
    """Create a mock TestRunner."""
    mock = MagicMock(spec=TestRunner)
    mock.versions = ["3.11", "3.12"]
    mock.config = TestudosConfig()
    mock.plan.return_value = RunPlan(
        versions=["3.11", "3.12"],
        test_command="pytest",
        test_args=[],
        working_dir=Path("."),
        parallel=False,
        max_jobs=None,
    )
    return mock


class TestRunCommand:
    """Tests for the run command."""

    def test_run_sequential_success(self, temp_project, mock_runner):
        """Test successful sequential test run."""
        mock_runner.run.return_value = {
            "3.11": TestResult(version="3.11", success=True, return_code=0, duration=1.0),
            "3.12": TestResult(version="3.12", success=True, return_code=0, duration=1.0),
        }

        with (
            patch("testudos.cli.check_uv_available", return_value=True),
            patch("testudos.cli.TestRunner", return_value=mock_runner),
        ):
            result = runner.invoke(app, ["run", str(temp_project)])

            assert result.exit_code == 0
            assert "3.11" in result.stdout
            assert "3.12" in result.stdout

    def test_run_sequential_failure(self, temp_project, mock_runner):
        """Test sequential run with test failure."""
        mock_runner.run.return_value = {
            "3.11": TestResult(version="3.11", success=True, return_code=0, duration=1.0),
            "3.12": TestResult(version="3.12", success=False, return_code=1, duration=1.0),
        }

        with (
            patch("testudos.cli.check_uv_available", return_value=True),
            patch("testudos.cli.TestRunner", return_value=mock_runner),
        ):
            result = runner.invoke(app, ["run", str(temp_project)])

            assert result.exit_code == 1
            assert "3.11" in result.stdout
            assert "3.12" in result.stdout

    def test_run_parallel_success(self, temp_project, mock_runner):
        """Test successful parallel test run."""
        mock_runner.config.parallel = False  # Ensure parallel comes from CLI flag
        mock_runner.plan.return_value = RunPlan(
            versions=["3.11", "3.12"],
            test_command="pytest",
            test_args=[],
            working_dir=Path("."),
            parallel=True,
            max_jobs=None,
        )

        with (
            patch("testudos.cli.check_uv_available", return_value=True),
            patch("testudos.cli.TestRunner", return_value=mock_runner),
            patch("testudos.cli._run_parallel_with_display") as mock_run,
        ):
            mock_run.return_value = {
                "3.11": TestResult(version="3.11", success=True, return_code=0, duration=1.0),
                "3.12": TestResult(version="3.12", success=True, return_code=0, duration=1.0),
            }

            result = runner.invoke(app, ["run", str(temp_project), "--parallel"])

            assert result.exit_code == 0
            mock_run.assert_called_once()

    def test_run_parallel_with_jobs(self, temp_project, mock_runner):
        """Test parallel run with custom job count."""
        mock_runner.config.max_jobs = None

        with (
            patch("testudos.cli.check_uv_available", return_value=True),
            patch("testudos.cli.TestRunner", return_value=mock_runner),
            patch("testudos.cli._run_parallel_with_display") as mock_run,
        ):
            mock_run.return_value = {
                "3.11": TestResult(version="3.11", success=True, return_code=0, duration=1.0),
                "3.12": TestResult(version="3.12", success=True, return_code=0, duration=1.0),
            }

            result = runner.invoke(app, ["run", str(temp_project), "-P", "-j", "2"])

            assert result.exit_code == 0

    def test_run_verbose(self, temp_project, mock_runner):
        """Test verbose output."""
        mock_runner.run.return_value = {
            "3.11": TestResult(version="3.11", success=True, return_code=0, duration=1.0),
        }
        mock_runner.versions = ["3.11"]

        with (
            patch("testudos.cli.check_uv_available", return_value=True),
            patch("testudos.cli.TestRunner", return_value=mock_runner),
        ):
            result = runner.invoke(app, ["run", str(temp_project), "--verbose"])

            assert result.exit_code == 0
            # Verbose should show test command
            assert "Test command:" in result.stdout or "pytest" in result.stdout

    def test_run_verbose_shows_failed_output(self, temp_project, mock_runner):
        """Test verbose mode shows output for failed tests in parallel mode."""
        mock_runner.versions = ["3.11"]
        mock_runner.config.parallel = False

        with (
            patch("testudos.cli.check_uv_available", return_value=True),
            patch("testudos.cli.TestRunner", return_value=mock_runner),
            patch("testudos.cli._run_parallel_with_display") as mock_run,
        ):
            mock_run.return_value = {
                "3.11": TestResult(
                    version="3.11",
                    success=False,
                    return_code=1,
                    duration=1.0,
                    output="test output",
                    error="test error",
                ),
            }

            result = runner.invoke(app, ["run", str(temp_project), "-P", "-v"])

            assert result.exit_code == 1
            # Should show failed output in verbose mode
            assert "Failed test output:" in result.stdout

    def test_run_specific_python_version(self, temp_project):
        """Test running with specific Python version."""
        mock_runner = MagicMock(spec=TestRunner)
        mock_runner.versions = ["3.12"]
        mock_runner.config = TestudosConfig()
        mock_runner.plan.return_value = RunPlan(
            versions=["3.12"],
            test_command="pytest",
            test_args=[],
            working_dir=Path("."),
            parallel=False,
            max_jobs=None,
        )
        mock_runner.run.return_value = {
            "3.12": TestResult(version="3.12", success=True, return_code=0, duration=1.0),
        }

        with (
            patch("testudos.cli.check_uv_available", return_value=True),
            patch("testudos.cli.TestRunner", return_value=mock_runner) as mock_class,
        ):
            result = runner.invoke(app, ["run", str(temp_project), "-p", "3.12"])

            assert result.exit_code == 0
            # Check that explicit versions were passed to TestRunner
            call_kwargs = mock_class.call_args.kwargs
            assert call_kwargs.get("explicit_versions") == ["3.12"]

    def test_run_multiple_python_versions(self, temp_project):
        """Test running with multiple specific Python versions."""
        mock_runner = MagicMock(spec=TestRunner)
        mock_runner.versions = ["3.11", "3.12"]
        mock_runner.config = TestudosConfig()
        mock_runner.plan.return_value = RunPlan(
            versions=["3.11", "3.12"],
            test_command="pytest",
            test_args=[],
            working_dir=Path("."),
            parallel=False,
            max_jobs=None,
        )
        mock_runner.run.return_value = {
            "3.11": TestResult(version="3.11", success=True, return_code=0, duration=1.0),
            "3.12": TestResult(version="3.12", success=True, return_code=0, duration=1.0),
        }

        with (
            patch("testudos.cli.check_uv_available", return_value=True),
            patch("testudos.cli.TestRunner", return_value=mock_runner),
        ):
            result = runner.invoke(app, ["run", str(temp_project), "-p", "3.11", "-p", "3.12"])

            assert result.exit_code == 0

    def test_run_uv_not_available(self, temp_project):
        """Test error when uv is not available."""
        with patch("testudos.cli.check_uv_available", return_value=False):
            result = runner.invoke(app, ["run", str(temp_project)])

            assert result.exit_code == 1
            assert "uv not found" in result.stdout

    def test_run_version_resolution_error(self, temp_project):
        """Test error during version resolution."""
        with (
            patch("testudos.cli.check_uv_available", return_value=True),
            patch(
                "testudos.cli.TestRunner",
                side_effect=VersionResolutionError("No compatible versions"),
            ),
        ):
            result = runner.invoke(app, ["run", str(temp_project)])

            assert result.exit_code == 1
            assert "No compatible versions" in result.stdout

    def test_run_no_versions_to_test(self, temp_project):
        """Test error when no versions to test."""
        mock_runner = MagicMock(spec=TestRunner)
        mock_runner.versions = []
        mock_runner.config = TestudosConfig()

        with (
            patch("testudos.cli.check_uv_available", return_value=True),
            patch("testudos.cli.TestRunner", return_value=mock_runner),
        ):
            result = runner.invoke(app, ["run", str(temp_project)])

            assert result.exit_code == 1
            assert "No Python versions to test" in result.stdout

    def test_run_fail_fast(self, temp_project, mock_runner):
        """Test fail-fast flag."""
        mock_runner.run.return_value = {
            "3.11": TestResult(version="3.11", success=True, return_code=0, duration=1.0),
        }
        mock_runner.versions = ["3.11"]

        with (
            patch("testudos.cli.check_uv_available", return_value=True),
            patch("testudos.cli.TestRunner", return_value=mock_runner),
        ):
            result = runner.invoke(app, ["run", str(temp_project), "--fail-fast"])

            assert result.exit_code == 0

    def test_run_no_fail_fast(self, temp_project, mock_runner):
        """Test no-fail-fast flag."""
        mock_runner.run.return_value = {
            "3.11": TestResult(version="3.11", success=True, return_code=0, duration=1.0),
        }
        mock_runner.versions = ["3.11"]

        with (
            patch("testudos.cli.check_uv_available", return_value=True),
            patch("testudos.cli.TestRunner", return_value=mock_runner),
        ):
            result = runner.invoke(app, ["run", str(temp_project), "--no-fail-fast"])

            assert result.exit_code == 0

    def test_run_dry_run(self, temp_project, mock_runner):
        """Test dry-run mode."""
        mock_runner.plan.return_value = RunPlan(
            versions=["3.11", "3.12"],
            test_command="pytest",
            test_args=[],
            working_dir=temp_project,
            parallel=False,
            max_jobs=None,
        )

        with patch("testudos.cli.TestRunner", return_value=mock_runner):
            result = runner.invoke(app, ["run", str(temp_project), "--dry-run"])

            assert result.exit_code == 0
            assert "Dry run mode" in result.stdout
            assert "Test Plan" in result.stdout
            assert "Commands that would be executed" in result.stdout


class TestVersionsCommand:
    """Tests for the versions command."""

    def test_versions_display(self, temp_project):
        """Test versions command displays version table."""
        with (
            patch(
                "testudos.cli.get_supported_python_versions",
                return_value=["3.11", "3.12", "3.13"],
            ),
            patch("testudos.cli.resolve_test_versions", return_value=["3.11", "3.12"]),
        ):
            result = runner.invoke(app, ["versions", str(temp_project)])

            assert result.exit_code == 0
            assert "3.11" in result.stdout
            assert "3.12" in result.stdout
            assert "3.13" in result.stdout
            assert "Will test:" in result.stdout

    def test_versions_error(self, temp_project):
        """Test versions command with resolution error."""
        with (
            patch(
                "testudos.cli.get_supported_python_versions",
                return_value=["3.11", "3.12"],
            ),
            patch(
                "testudos.cli.resolve_test_versions",
                side_effect=VersionResolutionError("Error resolving versions"),
            ),
        ):
            result = runner.invoke(app, ["versions", str(temp_project)])

            assert result.exit_code == 1
            assert "Error resolving versions" in result.stdout

    def test_versions_api_error(self, temp_project):
        """Test versions command when API fetch fails."""
        with patch(
            "testudos.cli.get_supported_python_versions",
            side_effect=Exception("API error"),
        ):
            result = runner.invoke(app, ["versions", str(temp_project)])

            assert result.exit_code == 1
            assert "Error fetching" in result.stdout or "API error" in result.stdout


class TestParallelProgressDisplay:
    """Tests for ParallelProgressDisplay class."""

    def test_progress_display_initialization(self):
        """Test progress display initialization."""
        from testudos.executor import TestStatus
        from testudos.ui import ParallelProgressDisplay

        display = ParallelProgressDisplay(["3.11", "3.12"])

        assert len(display.versions) == 2
        assert display.statuses["3.11"] == TestStatus.PENDING
        assert display.statuses["3.12"] == TestStatus.PENDING

    def test_progress_display_update(self):
        """Test updating progress display."""
        from testudos.executor import TestStatus
        from testudos.ui import ParallelProgressDisplay

        display = ParallelProgressDisplay(["3.11"])
        result = TestResult(version="3.11", success=True, return_code=0, duration=1.0)

        display.update("3.11", TestStatus.RUNNING, None)
        assert display.statuses["3.11"] == TestStatus.RUNNING

        display.update("3.11", TestStatus.PASSED, result)
        assert display.statuses["3.11"] == TestStatus.PASSED
        assert display.results["3.11"] == result

    def test_progress_display_render(self):
        """Test rendering progress display."""
        from testudos.executor import TestStatus
        from testudos.ui import ParallelProgressDisplay

        display = ParallelProgressDisplay(["3.11", "3.12"])
        display.update("3.11", TestStatus.RUNNING, None)

        table = display.render()

        assert table is not None
        assert table.title == "Test Progress"

    def test_progress_display_thread_safety(self):
        """Test thread-safe updates to progress display."""
        import threading

        from testudos.executor import TestStatus
        from testudos.ui import ParallelProgressDisplay

        display = ParallelProgressDisplay(["3.11", "3.12"])

        def update_status(version, status):
            display.update(version, status, None)

        threads = [
            threading.Thread(target=update_status, args=("3.11", TestStatus.RUNNING)),
            threading.Thread(target=update_status, args=("3.12", TestStatus.RUNNING)),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert display.statuses["3.11"] == TestStatus.RUNNING
        assert display.statuses["3.12"] == TestStatus.RUNNING


class TestDisplayResults:
    """Tests for display_results function."""

    def test_display_results_all_passed(self, capsys):
        """Test displaying results when all tests pass."""
        from testudos.ui import display_results

        results = {
            "3.11": TestResult(version="3.11", success=True, return_code=0, duration=1.5),
            "3.12": TestResult(version="3.12", success=True, return_code=0, duration=2.0),
        }

        display_results(results)
        captured = capsys.readouterr()

        assert "3.11" in captured.out
        assert "3.12" in captured.out
        assert "PASSED" in captured.out
        assert "2/2 passed" in captured.out

    def test_display_results_with_failures(self, capsys):
        """Test displaying results with failures."""
        from testudos.ui import display_results

        results = {
            "3.11": TestResult(version="3.11", success=True, return_code=0, duration=1.0),
            "3.12": TestResult(version="3.12", success=False, return_code=1, duration=1.0),
        }

        display_results(results)
        captured = capsys.readouterr()

        assert "PASSED" in captured.out
        assert "FAILED" in captured.out
        assert "1/2 passed" in captured.out

    def test_display_results_sorted_by_version(self, capsys):
        """Test that results are displayed sorted by version."""
        from testudos.ui import display_results

        results = {
            "3.13": TestResult(version="3.13", success=True, return_code=0, duration=1.0),
            "3.11": TestResult(version="3.11", success=True, return_code=0, duration=1.0),
            "3.12": TestResult(version="3.12", success=True, return_code=0, duration=1.0),
        }

        display_results(results)
        captured = capsys.readouterr()

        # Results should appear in order
        pos_11 = captured.out.find("3.11")
        pos_12 = captured.out.find("3.12")
        pos_13 = captured.out.find("3.13")

        assert pos_11 < pos_12 < pos_13


class TestAppCallback:
    """Tests for main app callback."""

    def test_help_message(self):
        """Test that help message is displayed correctly."""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "Testudos" in result.stdout
        assert "test harness" in result.stdout.lower()

    def test_run_help(self):
        """Test help for run command."""
        result = runner.invoke(app, ["run", "--help"])
        stdout = strip_ansi(result.stdout)

        assert result.exit_code == 0
        assert "run" in stdout.lower()
        assert "--parallel" in stdout
        assert "--verbose" in stdout
        assert "--dry-run" in stdout

    def test_versions_help(self):
        """Test help for versions command."""
        result = runner.invoke(app, ["versions", "--help"])

        assert result.exit_code == 0
        assert "versions" in result.stdout.lower()
