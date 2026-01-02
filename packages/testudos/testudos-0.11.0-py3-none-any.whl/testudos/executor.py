"""Test execution for testudos.

This module handles running tests across multiple Python versions
using uv's isolated environment feature.

Security Note:
    All command arguments are passed as a list to subprocess.run() without
    shell=True, which prevents shell injection attacks. The validation
    functions below add additional safety by rejecting potentially
    dangerous input patterns.
"""

import asyncio
import re
import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

# Import coverage utilities
from testudos.coverage import (
    get_coverage_data_path,
)
from testudos.python_version import InvalidPythonVersionError, PythonVersion


class CommandValidationError(ValueError):
    """Raised when command validation fails."""

    pass


# Pattern for safe command names (alphanumeric, hyphen, underscore, dots, forward slash)
SAFE_COMMAND_PATTERN = re.compile(r"^[a-zA-Z0-9._/-]+$")

# Pattern for safe arguments (no shell metacharacters that could cause issues)
# Allow common characters but reject potentially dangerous ones
DANGEROUS_ARG_PATTERN = re.compile(r"[`$]|\$\(|;\s*[a-zA-Z]|&&|\|\|")


def validate_version(version: str) -> str:
    """Validate a Python version string.

    Args:
        version: Version string like "3.11" or "3.12"

    Returns:
        The validated version string

    Raises:
        CommandValidationError: If the version is invalid
    """
    try:
        pv = PythonVersion.parse(version)
        return str(pv)
    except InvalidPythonVersionError as e:
        raise CommandValidationError(f"Invalid Python version '{version}': {e}") from e


def validate_test_command(command: str) -> str:
    """Validate a test command name.

    Args:
        command: Command name like "pytest" or "python"

    Returns:
        The validated command string

    Raises:
        CommandValidationError: If the command contains invalid characters
    """
    if not command:
        raise CommandValidationError("Test command cannot be empty")

    if not SAFE_COMMAND_PATTERN.match(command):
        raise CommandValidationError(
            f"Test command '{command}' contains invalid characters. "
            "Only alphanumeric, dots, hyphens, underscores, and forward slashes are allowed."
        )

    return command


def validate_test_arg(arg: str) -> str:
    """Validate a single test argument.

    Args:
        arg: A command-line argument

    Returns:
        The validated argument

    Raises:
        CommandValidationError: If the argument contains dangerous patterns
    """
    if DANGEROUS_ARG_PATTERN.search(arg):
        raise CommandValidationError(
            f"Test argument '{arg}' contains potentially dangerous characters. "
            "Shell metacharacters like $, `, &&, ||, and command substitution are not allowed."
        )

    return arg


def validate_test_args(args: list[str]) -> list[str]:
    """Validate a list of test arguments.

    Args:
        args: List of command-line arguments

    Returns:
        The validated argument list

    Raises:
        CommandValidationError: If any argument is invalid
    """
    return [validate_test_arg(arg) for arg in args]


class TestStatus(Enum):
    """Status of a test run."""

    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"


@dataclass
class TestResult:
    """Result of running tests for a single Python version.

    Attributes:
        version: The Python version that was tested
        success: Whether the tests passed
        return_code: The exit code from the test command
        output: Captured stdout from the test run (if captured)
        error: Captured stderr from the test run (if captured)
        duration: How long the test took in seconds (if measured)
    """

    version: str
    success: bool
    return_code: int
    output: str | None = None
    error: str | None = None
    duration: float | None = None


def check_uv_available() -> bool:
    """Check if uv is available on the system.

    Returns:
        True if uv is available, False otherwise
    """
    try:
        result = subprocess.run(
            ["uv", "--version"],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def _build_test_command(
    version: str,
    test_command: str,
    test_args: list[str],
    working_dir: Path | None = None,
    coverage: bool = False,
    coverage_source: list[str] | None = None,
) -> list[str]:
    """Build the uv run command for a specific Python version.

    All inputs are validated before building the command to prevent
    injection attacks, even though subprocess.run() without shell=True
    is already safe against shell injection.

    Args:
        version: Python version (e.g., "3.11")
        test_command: Test command to run (e.g., "pytest")
        test_args: Additional arguments for the test command
        working_dir: Working directory (optional, for setting --directory)
        coverage: Whether to run with coverage collection
        coverage_source: Source directories for coverage (default: ["src"])

    Returns:
        List of command arguments

    Raises:
        CommandValidationError: If any input fails validation
    """
    # Validate all inputs
    validated_version = validate_version(version)
    validated_command = validate_test_command(test_command)
    validated_args = validate_test_args(test_args)

    cmd = [
        "uv",
        "run",
        "--isolated",
        f"--python={validated_version}",
    ]

    if working_dir:
        cmd.extend(["--directory", str(working_dir)])

    if coverage:
        # Run tests through coverage
        coverage_data_file = get_coverage_data_path(working_dir or Path("."), version)
        source_dirs = coverage_source if coverage_source else ["src"]

        cmd.extend(
            [
                "coverage",
                "run",
                f"--data-file={coverage_data_file}",
                f"--source={','.join(source_dirs)}",
                "--branch",
                "-m",
                validated_command,
            ]
        )
    else:
        cmd.append(validated_command)

    cmd.extend(validated_args)

    return cmd


def run_single_test(
    version: str,
    test_command: str,
    test_args: list[str],
    working_dir: Path | None = None,
    capture_output: bool = False,
    timeout: float | None = None,
    coverage: bool = False,
    coverage_source: list[str] | None = None,
) -> TestResult:
    """Run tests for a single Python version.

    Args:
        version: Python version to test (e.g., "3.11")
        test_command: Test command to run (e.g., "pytest")
        test_args: Additional arguments for the test command
        working_dir: Working directory for test execution
        capture_output: Whether to capture stdout/stderr
        timeout: Timeout in seconds (None = no timeout)
        coverage: Whether to run with coverage collection
        coverage_source: Source directories for coverage

    Returns:
        TestResult with the outcome
    """
    cmd = _build_test_command(
        version,
        test_command,
        test_args,
        working_dir,
        coverage=coverage,
        coverage_source=coverage_source,
    )

    start_time = time.time()
    try:
        result = subprocess.run(
            cmd,
            capture_output=capture_output,
            text=True,
            cwd=working_dir,
            timeout=timeout,
        )
        duration = time.time() - start_time

        return TestResult(
            version=version,
            success=result.returncode == 0,
            return_code=result.returncode,
            output=result.stdout if capture_output else None,
            error=result.stderr if capture_output else None,
            duration=duration,
        )
    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        return TestResult(
            version=version,
            success=False,
            return_code=-1,
            error=f"Test timed out after {timeout} seconds",
            duration=duration,
        )
    except FileNotFoundError:
        duration = time.time() - start_time
        return TestResult(
            version=version,
            success=False,
            return_code=-1,
            error="uv not found. Install from https://docs.astral.sh/uv/",
            duration=duration,
        )


async def run_single_test_async(
    version: str,
    test_command: str,
    test_args: list[str],
    working_dir: Path | None = None,
    timeout: float | None = None,
    coverage: bool = False,
    coverage_source: list[str] | None = None,
) -> TestResult:
    """Run tests for a single Python version asynchronously.

    Uses asyncio.create_subprocess_exec() for non-blocking subprocess execution.
    Output is always captured to avoid interleaving when running multiple tests.

    Args:
        version: Python version to test (e.g., "3.11")
        test_command: Test command to run (e.g., "pytest")
        test_args: Additional arguments for the test command
        working_dir: Working directory for test execution
        timeout: Timeout in seconds (None = no timeout)
        coverage: Whether to run with coverage collection
        coverage_source: Source directories for coverage

    Returns:
        TestResult with the outcome
    """
    cmd = _build_test_command(
        version,
        test_command,
        test_args,
        working_dir,
        coverage=coverage,
        coverage_source=coverage_source,
    )

    start_time = time.time()
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=working_dir,
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            # Kill the process on timeout
            proc.kill()
            await proc.wait()
            duration = time.time() - start_time
            return TestResult(
                version=version,
                success=False,
                return_code=-1,
                error=f"Test timed out after {timeout} seconds",
                duration=duration,
            )

        duration = time.time() - start_time

        return TestResult(
            version=version,
            success=proc.returncode == 0,
            return_code=proc.returncode or 0,
            output=stdout.decode() if stdout else None,
            error=stderr.decode() if stderr else None,
            duration=duration,
        )
    except FileNotFoundError:
        duration = time.time() - start_time
        return TestResult(
            version=version,
            success=False,
            return_code=-1,
            error="uv not found. Install from https://docs.astral.sh/uv/",
            duration=duration,
        )


def run_tests_sequential(
    versions: list[str],
    test_command: str,
    test_args: list[str],
    working_dir: Path | None = None,
    fail_fast: bool = True,
    capture_output: bool = False,
    timeout: float | None = None,
    coverage: bool = False,
    coverage_source: list[str] | None = None,
) -> dict[str, TestResult]:
    """Run tests sequentially on each Python version.

    Args:
        versions: List of Python versions to test
        test_command: Test command to run (e.g., "pytest")
        test_args: Additional arguments for the test command
        working_dir: Working directory for test execution
        fail_fast: Stop immediately when a test fails (default: True)
        capture_output: Whether to capture stdout/stderr (default: False)
        timeout: Timeout in seconds per version (None = no timeout)
        coverage: Whether to run with coverage collection
        coverage_source: Source directories for coverage

    Returns:
        Dictionary mapping version to TestResult
    """
    results: dict[str, TestResult] = {}

    for version in versions:
        result = run_single_test(
            version=version,
            test_command=test_command,
            test_args=test_args,
            working_dir=working_dir,
            capture_output=capture_output,
            timeout=timeout,
            coverage=coverage,
            coverage_source=coverage_source,
        )
        results[version] = result

        if fail_fast and not result.success:
            # Stop on first failure
            break

    return results


async def run_tests_parallel_async(
    versions: list[str],
    test_command: str,
    test_args: list[str],
    working_dir: Path | None = None,
    max_concurrent: int | None = None,
    on_status_change: Callable[[str, TestStatus, TestResult | None], None] | None = None,
    timeout: float | None = None,
    coverage: bool = False,
    coverage_source: list[str] | None = None,
) -> dict[str, TestResult]:
    """Run tests in parallel across Python versions using asyncio.

    Uses asyncio for concurrent subprocess execution with lower overhead
    than threading. Progress can be tracked via the callback.

    Args:
        versions: List of Python versions to test
        test_command: Test command to run (e.g., "pytest")
        test_args: Additional arguments for the test command
        working_dir: Working directory for test execution
        max_concurrent: Maximum number of concurrent tests (default: number of versions)
        on_status_change: Optional callback for status updates.
            Called with (version, status, result) where result is None for
            PENDING/RUNNING status and TestResult for PASSED/FAILED.
        timeout: Timeout in seconds per version (None = no timeout)
        coverage: Whether to run with coverage collection
        coverage_source: Source directories for coverage

    Returns:
        Dictionary mapping version to TestResult
    """
    results: dict[str, TestResult] = {}

    if not versions:
        return results

    # Initialize all versions as pending
    if on_status_change:
        for version in versions:
            on_status_change(version, TestStatus.PENDING, None)

    # Semaphore to limit concurrency
    semaphore = asyncio.Semaphore(max_concurrent or len(versions))

    async def run_with_semaphore(version: str) -> tuple[str, TestResult]:
        async with semaphore:
            # Notify that we're starting
            if on_status_change:
                on_status_change(version, TestStatus.RUNNING, None)

            try:
                result = await run_single_test_async(
                    version=version,
                    test_command=test_command,
                    test_args=test_args,
                    working_dir=working_dir,
                    timeout=timeout,
                    coverage=coverage,
                    coverage_source=coverage_source,
                )
            except Exception as e:
                # Handle unexpected errors
                result = TestResult(
                    version=version,
                    success=False,
                    return_code=-1,
                    error=str(e),
                )

            # Notify completion
            if on_status_change:
                status = TestStatus.PASSED if result.success else TestStatus.FAILED
                on_status_change(version, status, result)

            return version, result

    # Run all tests concurrently
    tasks = [run_with_semaphore(v) for v in versions]
    task_results = await asyncio.gather(*tasks)

    # Convert to dictionary
    for version, result in task_results:
        results[version] = result

    return results


class ExecutorError(Exception):
    """Raised when test execution fails."""

    pass
