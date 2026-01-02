"""Tests for configuration loading."""

import pytest

from testudos.config import TestudosConfig


@pytest.fixture
def temp_pyproject(tmp_path):
    """Create a temporary pyproject.toml for testing."""

    def _create(config_content: str = ""):
        pyproject = tmp_path / "pyproject.toml"
        content = "[project]\nname = 'test'\n"
        if config_content:
            content += "\n[tool.testudos]\n" + config_content
        pyproject.write_text(content)
        return pyproject

    return _create


class TestTestudosConfig:
    """Tests for TestudosConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = TestudosConfig()

        assert config.python_versions is None
        assert config.test_command == "pytest"
        assert config.test_args == []
        assert config.parallel is False
        assert config.max_jobs is None

    def test_load_from_nonexistent_file(self):
        """Test loading from nonexistent file returns defaults."""
        config = TestudosConfig.from_pyproject("nonexistent.toml")

        assert config.python_versions is None
        assert config.test_command == "pytest"

    def test_load_from_file_without_tool_section(self, temp_pyproject):
        """Test loading from file without [tool.testudos] section."""
        pyproject = temp_pyproject()
        config = TestudosConfig.from_pyproject(pyproject)

        assert config.python_versions is None
        assert config.test_command == "pytest"

    def test_load_python_versions(self, temp_pyproject):
        """Test loading python-versions from config."""
        pyproject = temp_pyproject('python-versions = ["3.11", "3.12"]')
        config = TestudosConfig.from_pyproject(pyproject)

        assert config.python_versions == ["3.11", "3.12"]

    def test_load_test_command(self, temp_pyproject):
        """Test loading test-command from config."""
        pyproject = temp_pyproject('test-command = "python -m unittest"')
        config = TestudosConfig.from_pyproject(pyproject)

        assert config.test_command == "python -m unittest"

    def test_load_test_args(self, temp_pyproject):
        """Test loading test-args from config."""
        pyproject = temp_pyproject('test-args = ["-v", "--tb=short"]')
        config = TestudosConfig.from_pyproject(pyproject)

        assert config.test_args == ["-v", "--tb=short"]

    def test_load_parallel(self, temp_pyproject):
        """Test loading parallel flag from config."""
        pyproject = temp_pyproject("parallel = true")
        config = TestudosConfig.from_pyproject(pyproject)

        assert config.parallel is True

    def test_load_max_jobs(self, temp_pyproject):
        """Test loading max-jobs from config."""
        pyproject = temp_pyproject("max-jobs = 4")
        config = TestudosConfig.from_pyproject(pyproject)

        assert config.max_jobs == 4

    def test_load_full_config(self, temp_pyproject):
        """Test loading complete configuration."""
        config_content = """
python-versions = ["3.11", "3.12", "3.13"]
test-command = "pytest"
test-args = ["-v", "--cov=mypackage"]
parallel = true
max-jobs = 3
"""
        pyproject = temp_pyproject(config_content)
        config = TestudosConfig.from_pyproject(pyproject)

        assert config.python_versions == ["3.11", "3.12", "3.13"]
        assert config.test_command == "pytest"
        assert config.test_args == ["-v", "--cov=mypackage"]
        assert config.parallel is True
        assert config.max_jobs == 3

    def test_get_effective_max_jobs_default(self):
        """Test get_effective_max_jobs with no max-jobs set."""
        config = TestudosConfig()

        assert config.get_effective_max_jobs(4) == 4
        assert config.get_effective_max_jobs(2) == 2

    def test_get_effective_max_jobs_explicit(self):
        """Test get_effective_max_jobs with explicit max-jobs."""
        config = TestudosConfig(max_jobs=2)

        assert config.get_effective_max_jobs(4) == 2
        assert config.get_effective_max_jobs(10) == 2
