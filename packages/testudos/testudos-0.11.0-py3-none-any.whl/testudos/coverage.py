"""Coverage collection and aggregation for testudos.

This module provides functionality for collecting test coverage data
across multiple Python versions and combining them into unified reports.

The coverage workflow:
1. Run tests with coverage for each Python version
2. Store coverage data per version in .testudos/coverage/
3. Combine all coverage data into a single file
4. Generate reports in requested formats
"""

import asyncio
import json
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path


class CoverageError(Exception):
    """Raised when coverage operations fail."""

    pass


class CoverageNotAvailableError(CoverageError):
    """Raised when coverage.py is not installed."""

    pass


# Default directory for coverage data storage
COVERAGE_DIR = ".testudos/coverage"


@dataclass
class CoverageSummary:
    """Summary of coverage data.

    Attributes:
        covered_lines: Number of lines covered by tests
        total_lines: Total number of executable lines
        percent_covered: Coverage percentage (0-100)
        covered_branches: Number of branches covered (if branch coverage enabled)
        total_branches: Total number of branches (if branch coverage enabled)
        missing_lines: Lines not covered (file -> list of line numbers)
    """

    covered_lines: int
    total_lines: int
    percent_covered: float
    covered_branches: int | None = None
    total_branches: int | None = None
    missing_lines: dict[str, list[int]] = field(default_factory=dict)

    @property
    def missed_lines(self) -> int:
        """Number of lines not covered."""
        return self.total_lines - self.covered_lines


@dataclass
class CoverageResult:
    """Result of a coverage operation.

    Attributes:
        success: Whether the operation succeeded
        summary: Coverage summary data (if available)
        report_paths: Paths to generated reports (format -> path)
        error: Error message (if operation failed)
        data_file: Path to the coverage data file
    """

    success: bool
    summary: CoverageSummary | None = None
    report_paths: dict[str, Path] = field(default_factory=dict)
    error: str | None = None
    data_file: Path | None = None


def check_coverage_available() -> bool:
    """Check if coverage.py is available.

    Returns:
        True if coverage is available, False otherwise
    """
    try:
        result = subprocess.run(
            ["coverage", "--version"],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def get_coverage_data_path(working_dir: Path, version: str) -> Path:
    """Get the path for storing coverage data for a specific Python version.

    Args:
        working_dir: Project working directory
        version: Python version (e.g., "3.11")

    Returns:
        Path to the coverage data file
    """
    coverage_dir = working_dir / COVERAGE_DIR
    coverage_dir.mkdir(parents=True, exist_ok=True)
    return coverage_dir / f".coverage.{version}"


def get_combined_coverage_path(working_dir: Path) -> Path:
    """Get the path for the combined coverage data file.

    Args:
        working_dir: Project working directory

    Returns:
        Path to the combined coverage data file
    """
    coverage_dir = working_dir / COVERAGE_DIR
    coverage_dir.mkdir(parents=True, exist_ok=True)
    return coverage_dir / ".coverage.combined"


def build_coverage_test_args(
    version: str,
    test_command: str,
    test_args: list[str],
    working_dir: Path,
    source_dirs: list[str] | None = None,
) -> list[str]:
    """Build the command arguments for running tests with coverage.

    This constructs a command like:
        uv run --isolated --python=X.Y coverage run --source=src -m pytest ...

    Args:
        version: Python version (e.g., "3.11")
        test_command: Original test command (e.g., "pytest")
        test_args: Additional test arguments
        working_dir: Project working directory
        source_dirs: Directories to measure coverage for (default: ["src"])

    Returns:
        List of command arguments
    """
    coverage_data_file = get_coverage_data_path(working_dir, version)
    source = source_dirs if source_dirs else ["src"]

    # Build coverage run command
    cmd = [
        "uv",
        "run",
        "--isolated",
        f"--python={version}",
        "--directory",
        str(working_dir),
        "coverage",
        "run",
        f"--data-file={coverage_data_file}",
        f"--source={','.join(source)}",
        "--branch",  # Enable branch coverage
        "-m",  # Run as module
        test_command,
    ]
    cmd.extend(test_args)

    return cmd


async def run_coverage_combine(
    working_dir: Path,
    data_files: list[Path],
) -> CoverageResult:
    """Combine multiple coverage data files into one.

    This uses coverage combine to merge data from multiple Python versions.

    Args:
        working_dir: Project working directory
        data_files: List of coverage data files to combine

    Returns:
        CoverageResult with the combined data file path
    """
    if not data_files:
        return CoverageResult(
            success=False,
            error="No coverage data files to combine",
        )

    # Filter to only existing files
    existing_files = [f for f in data_files if f.exists()]
    if not existing_files:
        return CoverageResult(
            success=False,
            error="No coverage data files found. Did tests run with coverage?",
        )

    combined_path = get_combined_coverage_path(working_dir)

    # Remove existing combined file if present
    if combined_path.exists():
        combined_path.unlink()

    # Copy all data files to a temp location with sequential names
    # coverage combine expects files to be in the same directory
    working_dir / COVERAGE_DIR

    try:
        # Run coverage combine
        proc = await asyncio.create_subprocess_exec(
            "coverage",
            "combine",
            f"--data-file={combined_path}",
            *[str(f) for f in existing_files],
            cwd=working_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown error"
            return CoverageResult(
                success=False,
                error=f"Failed to combine coverage: {error_msg}",
            )

        return CoverageResult(
            success=True,
            data_file=combined_path,
        )

    except FileNotFoundError:
        return CoverageResult(
            success=False,
            error="coverage command not found. Install with: pip install coverage",
        )


async def generate_coverage_report(
    working_dir: Path,
    data_file: Path,
    formats: list[str],
    fail_under: float | None = None,
) -> CoverageResult:
    """Generate coverage reports in specified formats.

    Args:
        working_dir: Project working directory
        data_file: Path to coverage data file
        formats: List of report formats (term, html, xml, json, lcov)
        fail_under: Minimum coverage percentage (optional)

    Returns:
        CoverageResult with report paths and summary
    """
    if not data_file.exists():
        return CoverageResult(
            success=False,
            error=f"Coverage data file not found: {data_file}",
        )

    report_paths: dict[str, Path] = {}
    summary: CoverageSummary | None = None

    for fmt in formats:
        result = await _generate_single_report(working_dir, data_file, fmt, fail_under)
        if not result.success:
            return result
        if result.report_paths:
            report_paths.update(result.report_paths)
        if result.summary:
            summary = result.summary

    # If no terminal format requested, get summary via JSON
    if summary is None:
        summary = await _get_coverage_summary(working_dir, data_file)

    # Check fail-under threshold
    if fail_under is not None and summary is not None:
        if summary.percent_covered < fail_under:
            return CoverageResult(
                success=False,
                summary=summary,
                report_paths=report_paths,
                error=f"Coverage {summary.percent_covered:.1f}% is below threshold {fail_under}%",
                data_file=data_file,
            )

    return CoverageResult(
        success=True,
        summary=summary,
        report_paths=report_paths,
        data_file=data_file,
    )


async def _generate_single_report(
    working_dir: Path,
    data_file: Path,
    fmt: str,
    fail_under: float | None = None,
) -> CoverageResult:
    """Generate a single coverage report.

    Args:
        working_dir: Project working directory
        data_file: Path to coverage data file
        fmt: Report format
        fail_under: Minimum coverage percentage (optional)

    Returns:
        CoverageResult with report path
    """
    coverage_dir = working_dir / COVERAGE_DIR
    report_paths: dict[str, Path] = {}
    summary: CoverageSummary | None = None

    cmd = ["coverage"]

    if fmt in ("term", "term-missing"):
        cmd.append("report")
        if fmt == "term-missing":
            cmd.append("--show-missing")
    elif fmt == "html":
        cmd.append("html")
        html_dir = coverage_dir / "htmlcov"
        cmd.extend(["--directory", str(html_dir)])
        report_paths["html"] = html_dir / "index.html"
    elif fmt == "xml":
        cmd.append("xml")
        xml_path = coverage_dir / "coverage.xml"
        cmd.extend(["-o", str(xml_path)])
        report_paths["xml"] = xml_path
    elif fmt == "json":
        cmd.append("json")
        json_path = coverage_dir / "coverage.json"
        cmd.extend(["-o", str(json_path)])
        report_paths["json"] = json_path
    elif fmt == "lcov":
        cmd.append("lcov")
        lcov_path = coverage_dir / "coverage.lcov"
        cmd.extend(["-o", str(lcov_path)])
        report_paths["lcov"] = lcov_path
    else:
        return CoverageResult(
            success=False,
            error=f"Unknown coverage format: {fmt}",
        )

    cmd.extend([f"--data-file={data_file}"])

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=working_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            error_msg = stderr.decode() if stderr else stdout.decode()
            return CoverageResult(
                success=False,
                error=f"Failed to generate {fmt} report: {error_msg}",
            )

        # Parse terminal output for summary
        if fmt in ("term", "term-missing"):
            summary = _parse_coverage_report(stdout.decode())

        return CoverageResult(
            success=True,
            summary=summary,
            report_paths=report_paths,
        )

    except FileNotFoundError:
        return CoverageResult(
            success=False,
            error="coverage command not found. Install with: pip install coverage",
        )


async def _get_coverage_summary(working_dir: Path, data_file: Path) -> CoverageSummary | None:
    """Get coverage summary from a data file.

    Args:
        working_dir: Project working directory
        data_file: Path to coverage data file

    Returns:
        CoverageSummary or None if failed
    """
    try:
        proc = await asyncio.create_subprocess_exec(
            "coverage",
            "json",
            f"--data-file={data_file}",
            "-o",
            "-",  # Output to stdout
            cwd=working_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            return None

        data = json.loads(stdout.decode())
        totals = data.get("totals", {})

        return CoverageSummary(
            covered_lines=totals.get("covered_lines", 0),
            total_lines=totals.get("num_statements", 0),
            percent_covered=totals.get("percent_covered", 0.0),
            covered_branches=totals.get("covered_branches"),
            total_branches=totals.get("num_branches"),
        )

    except (FileNotFoundError, json.JSONDecodeError):
        return None


def _parse_coverage_report(output: str) -> CoverageSummary | None:
    """Parse coverage report output to extract summary.

    Args:
        output: Coverage report terminal output

    Returns:
        CoverageSummary or None if parsing failed
    """
    # Look for the TOTAL line in the report
    # Format: TOTAL    1234    567    89%
    # Or with branches: TOTAL    1234    567    890    123    89%
    total_pattern = r"^TOTAL\s+(\d+)\s+(\d+)(?:\s+(\d+)\s+(\d+))?\s+(\d+)%"

    for line in output.split("\n"):
        match = re.match(total_pattern, line)
        if match:
            groups = match.groups()
            total_lines = int(groups[0])
            missed_lines = int(groups[1])
            covered_lines = total_lines - missed_lines

            # Check for branch coverage
            if groups[2] is not None and groups[3] is not None:
                total_branches = int(groups[2])
                missed_branches = int(groups[3])
                covered_branches = total_branches - missed_branches
            else:
                total_branches = None
                covered_branches = None

            percent = int(groups[4])

            return CoverageSummary(
                covered_lines=covered_lines,
                total_lines=total_lines,
                percent_covered=float(percent),
                covered_branches=covered_branches,
                total_branches=total_branches,
            )

    return None


def clean_coverage_data(working_dir: Path) -> None:
    """Remove all coverage data files.

    Args:
        working_dir: Project working directory
    """
    coverage_dir = working_dir / COVERAGE_DIR
    if coverage_dir.exists():
        shutil.rmtree(coverage_dir)


def list_coverage_data_files(working_dir: Path) -> list[Path]:
    """List all version-specific coverage data files.

    Args:
        working_dir: Project working directory

    Returns:
        List of coverage data file paths
    """
    coverage_dir = working_dir / COVERAGE_DIR
    if not coverage_dir.exists():
        return []

    # Match .coverage.X.Y pattern (version-specific files)
    return sorted(
        f for f in coverage_dir.glob(".coverage.*") if re.match(r"\.coverage\.\d+\.\d+", f.name)
    )
