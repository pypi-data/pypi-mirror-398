"""Tests for test execution."""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from testudos.executor import (
    TestResult,
    TestStatus,
    _build_test_command,
    check_uv_available,
    run_single_test,
    run_single_test_async,
    run_tests_parallel_async,
    run_tests_sequential,
)


class TestTestResult:
    """Tests for TestResult dataclass."""

    def test_success_result(self):
        """Test creating a successful result."""
        result = TestResult(
            version="3.11",
            success=True,
            return_code=0,
        )

        assert result.version == "3.11"
        assert result.success is True
        assert result.return_code == 0
        assert result.output is None
        assert result.error is None

    def test_failure_result(self):
        """Test creating a failed result."""
        result = TestResult(
            version="3.12",
            success=False,
            return_code=1,
            output="test output",
            error="test error",
        )

        assert result.version == "3.12"
        assert result.success is False
        assert result.return_code == 1
        assert result.output == "test output"
        assert result.error == "test error"


class TestCheckUvAvailable:
    """Tests for check_uv_available."""

    def test_uv_available(self):
        """Test when uv is available."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            assert check_uv_available() is True

    def test_uv_not_available(self):
        """Test when uv is not available."""
        with patch("subprocess.run", side_effect=FileNotFoundError):
            assert check_uv_available() is False

    def test_uv_returns_error(self):
        """Test when uv returns non-zero exit code."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1)
            assert check_uv_available() is False


class TestBuildTestCommand:
    """Tests for _build_test_command."""

    def test_basic_command(self):
        """Test building a basic test command."""
        cmd = _build_test_command(
            version="3.11",
            test_command="pytest",
            test_args=[],
        )

        assert cmd == ["uv", "run", "--isolated", "--python=3.11", "pytest"]

    def test_command_with_args(self):
        """Test building command with test arguments."""
        cmd = _build_test_command(
            version="3.12",
            test_command="pytest",
            test_args=["-v", "--tb=short"],
        )

        assert cmd == [
            "uv",
            "run",
            "--isolated",
            "--python=3.12",
            "pytest",
            "-v",
            "--tb=short",
        ]

    def test_command_with_working_dir(self):
        """Test building command with working directory."""
        cmd = _build_test_command(
            version="3.11",
            test_command="pytest",
            test_args=[],
            working_dir=Path("/path/to/project"),
        )

        assert "--directory" in cmd
        assert "/path/to/project" in cmd

    def test_custom_test_command(self):
        """Test with custom test command."""
        cmd = _build_test_command(
            version="3.11",
            test_command="python",
            test_args=["-m", "unittest", "discover"],
        )

        assert cmd == [
            "uv",
            "run",
            "--isolated",
            "--python=3.11",
            "python",
            "-m",
            "unittest",
            "discover",
        ]


class TestRunSingleTest:
    """Tests for run_single_test."""

    def test_successful_run(self):
        """Test successful test run."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="test output",
                stderr="",
            )

            result = run_single_test(
                version="3.11",
                test_command="pytest",
                test_args=[],
                capture_output=True,
            )

            assert result.success is True
            assert result.return_code == 0
            assert result.version == "3.11"
            mock_run.assert_called_once()

    def test_failed_run(self):
        """Test failed test run."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="",
                stderr="test failed",
            )

            result = run_single_test(
                version="3.11",
                test_command="pytest",
                test_args=[],
                capture_output=True,
            )

            assert result.success is False
            assert result.return_code == 1

    def test_uv_not_found(self):
        """Test when uv is not found."""
        with patch("subprocess.run", side_effect=FileNotFoundError):
            result = run_single_test(
                version="3.11",
                test_command="pytest",
                test_args=[],
            )

            assert result.success is False
            assert result.return_code == -1
            assert "uv not found" in result.error

    def test_capture_output_disabled(self):
        """Test with output capture disabled."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            result = run_single_test(
                version="3.11",
                test_command="pytest",
                test_args=[],
                capture_output=False,
            )

            assert result.output is None
            assert result.error is None


class TestRunTestsSequential:
    """Tests for run_tests_sequential."""

    def test_all_pass(self):
        """Test when all versions pass."""
        with patch("testudos.executor.run_single_test") as mock_run:
            mock_run.side_effect = [
                TestResult(version="3.11", success=True, return_code=0),
                TestResult(version="3.12", success=True, return_code=0),
                TestResult(version="3.13", success=True, return_code=0),
            ]

            results = run_tests_sequential(
                versions=["3.11", "3.12", "3.13"],
                test_command="pytest",
                test_args=[],
            )

            assert len(results) == 3
            assert all(r.success for r in results.values())

    def test_one_fails_fail_fast(self):
        """Test fail-fast behavior when one version fails."""
        with patch("testudos.executor.run_single_test") as mock_run:
            mock_run.side_effect = [
                TestResult(version="3.11", success=True, return_code=0),
                TestResult(version="3.12", success=False, return_code=1),
                # 3.13 should not be called
            ]

            results = run_tests_sequential(
                versions=["3.11", "3.12", "3.13"],
                test_command="pytest",
                test_args=[],
                fail_fast=True,
            )

            assert len(results) == 2
            assert results["3.11"].success is True
            assert results["3.12"].success is False
            assert "3.13" not in results

    def test_one_fails_continue(self):
        """Test continuing after failure when fail_fast=False."""
        with patch("testudos.executor.run_single_test") as mock_run:
            mock_run.side_effect = [
                TestResult(version="3.11", success=True, return_code=0),
                TestResult(version="3.12", success=False, return_code=1),
                TestResult(version="3.13", success=True, return_code=0),
            ]

            results = run_tests_sequential(
                versions=["3.11", "3.12", "3.13"],
                test_command="pytest",
                test_args=[],
                fail_fast=False,
            )

            assert len(results) == 3
            assert results["3.11"].success is True
            assert results["3.12"].success is False
            assert results["3.13"].success is True

    def test_empty_versions(self):
        """Test with empty versions list."""
        results = run_tests_sequential(
            versions=[],
            test_command="pytest",
            test_args=[],
        )

        assert results == {}

    def test_passes_working_dir(self):
        """Test that working directory is passed correctly."""
        with patch("testudos.executor.run_single_test") as mock_run:
            mock_run.return_value = TestResult(version="3.11", success=True, return_code=0)
            working_dir = Path("/test/path")

            run_tests_sequential(
                versions=["3.11"],
                test_command="pytest",
                test_args=["-v"],
                working_dir=working_dir,
            )

            mock_run.assert_called_once_with(
                version="3.11",
                test_command="pytest",
                test_args=["-v"],
                working_dir=working_dir,
                capture_output=False,
                timeout=None,
                coverage=False,
                coverage_source=None,
            )


class TestTestStatus:
    """Tests for TestStatus enum."""

    def test_status_values(self):
        """Test that all status values exist."""
        assert TestStatus.PENDING.value == "pending"
        assert TestStatus.RUNNING.value == "running"
        assert TestStatus.PASSED.value == "passed"
        assert TestStatus.FAILED.value == "failed"


class TestRunSingleTestAsync:
    """Tests for run_single_test_async."""

    async def test_successful_run(self):
        """Test successful async test run."""
        # Create mock process
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(b"test output", b""))

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            result = await run_single_test_async(
                version="3.11",
                test_command="pytest",
                test_args=[],
            )

            assert result.success is True
            assert result.return_code == 0
            assert result.version == "3.11"
            assert result.output == "test output"

    async def test_failed_run(self):
        """Test failed async test run."""
        mock_proc = MagicMock()
        mock_proc.returncode = 1
        mock_proc.communicate = AsyncMock(return_value=(b"", b"test failed"))

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            result = await run_single_test_async(
                version="3.11",
                test_command="pytest",
                test_args=[],
            )

            assert result.success is False
            assert result.return_code == 1
            assert result.error == "test failed"

    async def test_uv_not_found(self):
        """Test when uv is not found."""
        with patch("asyncio.create_subprocess_exec", side_effect=FileNotFoundError):
            result = await run_single_test_async(
                version="3.11",
                test_command="pytest",
                test_args=[],
            )

            assert result.success is False
            assert result.return_code == -1
            assert "uv not found" in result.error

    async def test_captures_duration(self):
        """Test that duration is captured correctly."""
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(b"", b""))

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            result = await run_single_test_async(
                version="3.11",
                test_command="pytest",
                test_args=[],
            )

            assert result.duration is not None
            assert result.duration >= 0


class TestRunTestsParallelAsync:
    """Tests for run_tests_parallel_async."""

    async def test_all_pass(self):
        """Test when all versions pass."""
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(b"passed", b""))

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            results = await run_tests_parallel_async(
                versions=["3.11", "3.12", "3.13"],
                test_command="pytest",
                test_args=[],
            )

            assert len(results) == 3
            assert all(r.success for r in results.values())
            assert "3.11" in results
            assert "3.12" in results
            assert "3.13" in results

    async def test_one_fails(self):
        """Test when one version fails."""
        call_count = 0

        async def mock_communicate():
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                return (b"", b"failed")
            return (b"passed", b"")

        def create_mock_proc(*args, **kwargs):
            mock_proc = MagicMock()
            # Use a unique call_count per invocation
            version = args[3] if len(args) > 3 else ""
            if "3.12" in version:
                mock_proc.returncode = 1
                mock_proc.communicate = AsyncMock(return_value=(b"", b"failed"))
            else:
                mock_proc.returncode = 0
                mock_proc.communicate = AsyncMock(return_value=(b"passed", b""))
            return mock_proc

        with patch("asyncio.create_subprocess_exec", side_effect=create_mock_proc):
            results = await run_tests_parallel_async(
                versions=["3.11", "3.12", "3.13"],
                test_command="pytest",
                test_args=[],
            )

            # All versions should be tested (no fail-fast in parallel)
            assert len(results) == 3
            assert results["3.11"].success is True
            assert results["3.12"].success is False
            assert results["3.13"].success is True

    async def test_empty_versions(self):
        """Test with empty versions list."""
        results = await run_tests_parallel_async(
            versions=[],
            test_command="pytest",
            test_args=[],
        )

        assert results == {}

    async def test_max_concurrent(self):
        """Test that max_concurrent limits concurrent execution."""
        # Track concurrent execution
        concurrent_count = 0
        max_concurrent_seen = 0

        async def controlled_communicate():
            nonlocal concurrent_count, max_concurrent_seen
            concurrent_count += 1
            max_concurrent_seen = max(max_concurrent_seen, concurrent_count)
            await asyncio.sleep(0.05)  # Small delay to test concurrency
            concurrent_count -= 1
            return (b"passed", b"")

        def create_mock_proc(*args, **kwargs):
            mock_proc = MagicMock()
            mock_proc.returncode = 0
            mock_proc.communicate = controlled_communicate
            return mock_proc

        with patch("asyncio.create_subprocess_exec", side_effect=create_mock_proc):
            results = await run_tests_parallel_async(
                versions=["3.11", "3.12", "3.13", "3.14"],
                test_command="pytest",
                test_args=[],
                max_concurrent=2,  # Limit to 2 concurrent
            )

            assert len(results) == 4
            # Should never exceed 2 concurrent
            assert max_concurrent_seen <= 2

    async def test_status_callback(self):
        """Test that status callback is called correctly."""
        status_updates = []

        def track_status(version, status, result):
            status_updates.append((version, status, result))

        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(b"passed", b""))

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            await run_tests_parallel_async(
                versions=["3.11"],
                test_command="pytest",
                test_args=[],
                on_status_change=track_status,
            )

        # Should have PENDING, RUNNING, and PASSED updates
        statuses = [s[1] for s in status_updates]
        assert TestStatus.PENDING in statuses
        assert TestStatus.RUNNING in statuses
        assert TestStatus.PASSED in statuses

    async def test_handles_exception(self):
        """Test that exceptions in tests are handled gracefully."""
        call_count = 0

        def create_mock_proc(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise RuntimeError("Unexpected error")
            mock_proc = MagicMock()
            mock_proc.returncode = 0
            mock_proc.communicate = AsyncMock(return_value=(b"passed", b""))
            return mock_proc

        with patch("asyncio.create_subprocess_exec", side_effect=create_mock_proc):
            results = await run_tests_parallel_async(
                versions=["3.11", "3.12", "3.13"],
                test_command="pytest",
                test_args=[],
            )

            # All versions should have results
            assert len(results) == 3
            assert results["3.11"].success is True
            assert results["3.12"].success is False
            assert "Unexpected error" in results["3.12"].error
            assert results["3.13"].success is True

    async def test_passes_working_dir(self):
        """Test that working directory is passed correctly."""
        captured_cwd = None

        def create_mock_proc(*args, **kwargs):
            nonlocal captured_cwd
            captured_cwd = kwargs.get("cwd")
            mock_proc = MagicMock()
            mock_proc.returncode = 0
            mock_proc.communicate = AsyncMock(return_value=(b"passed", b""))
            return mock_proc

        with patch("asyncio.create_subprocess_exec", side_effect=create_mock_proc):
            await run_tests_parallel_async(
                versions=["3.11"],
                test_command="pytest",
                test_args=[],
                working_dir=Path("/test/path"),
            )

            assert captured_cwd == Path("/test/path")

    async def test_captures_output(self):
        """Test that output is captured in parallel mode."""
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(b"captured stdout", b"captured stderr"))

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            results = await run_tests_parallel_async(
                versions=["3.11"],
                test_command="pytest",
                test_args=[],
            )

            assert results["3.11"].output == "captured stdout"
            assert results["3.11"].error == "captured stderr"
