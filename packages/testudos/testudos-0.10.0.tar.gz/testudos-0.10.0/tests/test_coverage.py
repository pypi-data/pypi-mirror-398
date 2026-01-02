"""Tests for coverage collection and aggregation."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from testudos.coverage import (
    COVERAGE_DIR,
    CoverageResult,
    CoverageSummary,
    _parse_coverage_report,
    check_coverage_available,
    clean_coverage_data,
    get_combined_coverage_path,
    get_coverage_data_path,
    list_coverage_data_files,
)


class TestCoveragePaths:
    """Tests for coverage path utilities."""

    def test_get_coverage_data_path(self, tmp_path):
        """Test coverage data path generation."""
        path = get_coverage_data_path(tmp_path, "3.11")
        assert path == tmp_path / COVERAGE_DIR / ".coverage.3.11"

    def test_get_coverage_data_path_creates_directory(self, tmp_path):
        """Test that coverage directory is created."""
        get_coverage_data_path(tmp_path, "3.12")
        assert (tmp_path / COVERAGE_DIR).exists()

    def test_get_combined_coverage_path(self, tmp_path):
        """Test combined coverage path generation."""
        path = get_combined_coverage_path(tmp_path)
        assert path == tmp_path / COVERAGE_DIR / ".coverage.combined"


class TestListCoverageDataFiles:
    """Tests for listing coverage data files."""

    def test_list_empty_directory(self, tmp_path):
        """Test listing when no coverage directory exists."""
        files = list_coverage_data_files(tmp_path)
        assert files == []

    def test_list_coverage_files(self, tmp_path):
        """Test listing version-specific coverage files."""
        coverage_dir = tmp_path / COVERAGE_DIR
        coverage_dir.mkdir(parents=True)

        # Create some coverage files
        (coverage_dir / ".coverage.3.11").touch()
        (coverage_dir / ".coverage.3.12").touch()
        (coverage_dir / ".coverage.combined").touch()  # Should not be included

        files = list_coverage_data_files(tmp_path)
        assert len(files) == 2
        assert coverage_dir / ".coverage.3.11" in files
        assert coverage_dir / ".coverage.3.12" in files


class TestCleanCoverageData:
    """Tests for cleaning coverage data."""

    def test_clean_coverage_data(self, tmp_path):
        """Test cleaning coverage directory."""
        coverage_dir = tmp_path / COVERAGE_DIR
        coverage_dir.mkdir(parents=True)
        (coverage_dir / ".coverage.3.11").touch()
        (coverage_dir / ".coverage.3.12").touch()

        clean_coverage_data(tmp_path)

        assert not coverage_dir.exists()

    def test_clean_nonexistent_directory(self, tmp_path):
        """Test cleaning when directory doesn't exist."""
        # Should not raise
        clean_coverage_data(tmp_path)


class TestCheckCoverageAvailable:
    """Tests for coverage availability check."""

    @patch("testudos.coverage.subprocess.run")
    def test_coverage_available(self, mock_run):
        """Test when coverage is available."""
        mock_run.return_value = MagicMock(returncode=0)
        assert check_coverage_available() is True

    @patch("testudos.coverage.subprocess.run")
    def test_coverage_not_available(self, mock_run):
        """Test when coverage is not available."""
        mock_run.side_effect = FileNotFoundError()
        assert check_coverage_available() is False


class TestParseCoverageReport:
    """Tests for coverage report parsing."""

    def test_parse_simple_report(self):
        """Test parsing a simple coverage report."""
        output = """
Name                 Stmts   Miss  Cover
----------------------------------------
src/module.py           50     10    80%
src/other.py            30      5    83%
----------------------------------------
TOTAL                   80     15    81%
"""
        summary = _parse_coverage_report(output)
        assert summary is not None
        assert summary.total_lines == 80
        assert summary.missed_lines == 15
        assert summary.covered_lines == 65
        assert summary.percent_covered == 81.0

    def test_parse_report_with_branches(self):
        """Test parsing report with branch coverage."""
        output = """
Name                 Stmts   Miss Branch BrPart  Cover
--------------------------------------------------------
src/module.py           50     10     20      5    75%
--------------------------------------------------------
TOTAL                   50     10     20      5    75%
"""
        summary = _parse_coverage_report(output)
        assert summary is not None
        assert summary.total_lines == 50
        assert summary.missed_lines == 10
        assert summary.total_branches == 20
        assert summary.covered_branches == 15

    def test_parse_empty_report(self):
        """Test parsing empty report."""
        summary = _parse_coverage_report("")
        assert summary is None

    def test_parse_report_no_total(self):
        """Test parsing report without TOTAL line."""
        output = """
Name                 Stmts   Miss  Cover
----------------------------------------
src/module.py           50     10    80%
"""
        summary = _parse_coverage_report(output)
        assert summary is None


class TestCoverageSummary:
    """Tests for CoverageSummary dataclass."""

    def test_missed_lines_property(self):
        """Test missed_lines property calculation."""
        summary = CoverageSummary(
            covered_lines=80,
            total_lines=100,
            percent_covered=80.0,
        )
        assert summary.missed_lines == 20

    def test_summary_with_branches(self):
        """Test summary with branch coverage."""
        summary = CoverageSummary(
            covered_lines=80,
            total_lines=100,
            percent_covered=80.0,
            covered_branches=15,
            total_branches=20,
        )
        assert summary.covered_branches == 15
        assert summary.total_branches == 20


class TestCoverageResult:
    """Tests for CoverageResult dataclass."""

    def test_success_result(self):
        """Test successful coverage result."""
        summary = CoverageSummary(
            covered_lines=80,
            total_lines=100,
            percent_covered=80.0,
        )
        result = CoverageResult(
            success=True,
            summary=summary,
            data_file=Path(".coverage"),
        )
        assert result.success
        assert result.summary is not None
        assert result.error is None

    def test_failure_result(self):
        """Test failed coverage result."""
        result = CoverageResult(
            success=False,
            error="Coverage collection failed",
        )
        assert not result.success
        assert result.error == "Coverage collection failed"
        assert result.summary is None


class TestCoverageConfig:
    """Tests for coverage configuration loading."""

    @pytest.fixture
    def temp_pyproject(self, tmp_path):
        """Create a temporary pyproject.toml for testing."""

        def _create(config_content: str = ""):
            pyproject = tmp_path / "pyproject.toml"
            content = "[project]\nname = 'test'\n"
            if config_content:
                content += "\n[tool.testudos]\n" + config_content
            pyproject.write_text(content)
            return pyproject

        return _create

    def test_default_coverage_config(self):
        """Test default coverage configuration values."""
        from testudos.config import TestudosConfig

        config = TestudosConfig()

        assert config.coverage is False
        assert config.coverage_combine is True
        assert config.coverage_report == ["term"]
        assert config.coverage_fail_under is None

    def test_load_coverage_config(self, temp_pyproject):
        """Test loading coverage configuration."""
        from testudos.config import TestudosConfig

        config_content = """
coverage = true
coverage-combine = true
coverage-report = ["html", "xml"]
coverage-fail-under = 80
"""
        pyproject = temp_pyproject(config_content)
        config = TestudosConfig.from_pyproject(pyproject)

        assert config.coverage is True
        assert config.coverage_combine is True
        assert config.coverage_report == ["html", "xml"]
        assert config.coverage_fail_under == 80


class TestCoverageConfigValidation:
    """Tests for coverage configuration validation."""

    @pytest.fixture
    def temp_pyproject(self, tmp_path):
        """Create a temporary pyproject.toml for testing."""

        def _create(config_content: str = ""):
            pyproject = tmp_path / "pyproject.toml"
            content = "[project]\nname = 'test'\n"
            if config_content:
                content += "\n[tool.testudos]\n" + config_content
            pyproject.write_text(content)
            return pyproject

        return _create

    def test_invalid_coverage_report_format(self, temp_pyproject):
        """Test that invalid report format raises error."""
        from testudos.config import ConfigValidationError, TestudosConfig

        config_content = 'coverage-report = ["invalid_format"]'
        pyproject = temp_pyproject(config_content)

        with pytest.raises(ConfigValidationError) as exc_info:
            TestudosConfig.from_pyproject(pyproject)

        assert "invalid_format" in str(exc_info.value)

    def test_invalid_coverage_fail_under_negative(self, temp_pyproject):
        """Test that negative fail-under raises error."""
        from testudos.config import ConfigValidationError, TestudosConfig

        config_content = "coverage-fail-under = -10"
        pyproject = temp_pyproject(config_content)

        with pytest.raises(ConfigValidationError) as exc_info:
            TestudosConfig.from_pyproject(pyproject)

        assert "between 0 and 100" in str(exc_info.value)

    def test_invalid_coverage_fail_under_over_100(self, temp_pyproject):
        """Test that fail-under over 100 raises error."""
        from testudos.config import ConfigValidationError, TestudosConfig

        config_content = "coverage-fail-under = 150"
        pyproject = temp_pyproject(config_content)

        with pytest.raises(ConfigValidationError) as exc_info:
            TestudosConfig.from_pyproject(pyproject)

        assert "between 0 and 100" in str(exc_info.value)

    def test_valid_coverage_report_formats(self, temp_pyproject):
        """Test all valid report formats."""
        from testudos.config import TestudosConfig

        for fmt in ["term", "term-missing", "html", "xml", "json", "lcov"]:
            config_content = f'coverage-report = ["{fmt}"]'
            pyproject = temp_pyproject(config_content)
            config = TestudosConfig.from_pyproject(pyproject)
            assert config.coverage_report == [fmt]
