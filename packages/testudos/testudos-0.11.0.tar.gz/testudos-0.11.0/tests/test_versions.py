"""Tests for version resolution."""

import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest
from packaging.specifiers import SpecifierSet

from testudos.versions import (
    CacheConfig,
    VersionResolutionError,
    get_supported_python_versions,
    parse_requires_python,
    resolve_test_versions,
    set_cache_config,
)


@pytest.fixture
def mock_api_response():
    """Mock response from endoflife.date API."""
    return [
        {"cycle": "3.13", "eol": False},
        {"cycle": "3.12", "eol": False},
        {"cycle": "3.11", "eol": "2027-10-01"},
        {"cycle": "3.10", "eol": "2026-10-04"},
        {"cycle": "3.9", "eol": "2025-10-05"},
        {"cycle": "3.8", "eol": "2024-10-07"},  # Already EOL
    ]


@pytest.fixture
def temp_pyproject(tmp_path):
    """Create a temporary pyproject.toml for testing."""

    def _create(requires_python: str | None = ">=3.11"):
        pyproject = tmp_path / "pyproject.toml"
        content = "[project]\n"
        if requires_python:
            content += f'requires-python = "{requires_python}"\n'
        pyproject.write_text(content)
        return pyproject

    return _create


@pytest.fixture
def temp_cache_config(tmp_path):
    """Create a temporary cache configuration for testing."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    config = CacheConfig(
        cache_dir=cache_dir,
        cache_file=cache_dir / "endoflife.json",
        ttl=timedelta(hours=24),
    )
    set_cache_config(config)
    yield config
    # Reset to default after test
    set_cache_config(CacheConfig.default())


class TestGetSupportedPythonVersions:
    """Tests for get_supported_python_versions."""

    def test_fetch_from_api(self, mock_api_response, temp_cache_config):
        """Test fetching versions from API."""
        with patch("httpx.get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_api_response
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            versions = get_supported_python_versions(use_cache=False)

            # Should include 3.9, 3.10, 3.11, 3.12, 3.13 (all non-EOL)
            # 3.8 is EOL (date in the past)
            assert "3.13" in versions
            assert "3.12" in versions
            assert "3.11" in versions
            assert "3.10" in versions

    def test_fallback_on_api_failure(self, temp_cache_config):
        """Test fallback to bundled versions when API fails."""
        with patch("httpx.get", side_effect=Exception("Network error")):
            with pytest.warns(UserWarning, match="bundled fallback"):
                versions = get_supported_python_versions(use_cache=False)
                assert isinstance(versions, list)
                assert len(versions) > 0

    def test_cache_saving(self, mock_api_response, temp_cache_config):
        """Test that successful API calls save to cache."""
        with patch("httpx.get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_api_response
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            versions = get_supported_python_versions(use_cache=False)

            # Check cache file was created
            assert temp_cache_config.cache_file.exists()
            cache_data = json.loads(temp_cache_config.cache_file.read_text())
            assert "timestamp" in cache_data
            assert "versions" in cache_data
            assert cache_data["versions"] == versions

    def test_cache_loading(self, temp_cache_config):
        """Test loading from valid cache."""
        cached_versions = ["3.11", "3.12", "3.13"]
        cache_data = {
            "timestamp": datetime.now().isoformat(),
            "versions": cached_versions,
        }
        temp_cache_config.cache_file.write_text(json.dumps(cache_data))

        # Should load from cache without hitting API
        with patch("httpx.get") as mock_get:
            versions = get_supported_python_versions(use_cache=True)
            assert versions == cached_versions
            mock_get.assert_not_called()

    def test_expired_cache_refetch(self, temp_cache_config, mock_api_response):
        """Test that expired cache triggers refetch."""
        # Create expired cache
        old_timestamp = (datetime.now() - timedelta(hours=25)).isoformat()
        cache_data = {
            "timestamp": old_timestamp,
            "versions": ["3.10"],
        }
        temp_cache_config.cache_file.write_text(json.dumps(cache_data))

        with patch("httpx.get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_api_response
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            versions = get_supported_python_versions(use_cache=True)

            # Should have fetched from API (not returned cached ["3.10"])
            assert "3.12" in versions
            mock_get.assert_called_once()


class TestParseRequiresPython:
    """Tests for parse_requires_python."""

    def test_parse_valid_specifier(self, temp_pyproject):
        """Test parsing valid requires-python."""
        pyproject = temp_pyproject(">=3.11")
        specifier = parse_requires_python(pyproject)

        assert isinstance(specifier, SpecifierSet)
        assert "3.11.0" in specifier
        assert "3.12.0" in specifier
        assert "3.10.0" not in specifier

    def test_complex_specifier(self, temp_pyproject):
        """Test parsing complex version specifier."""
        pyproject = temp_pyproject(">=3.10,<3.13")
        specifier = parse_requires_python(pyproject)

        assert "3.10.0" in specifier
        assert "3.11.0" in specifier
        assert "3.12.0" in specifier
        assert "3.13.0" not in specifier
        assert "3.9.0" not in specifier

    def test_missing_file(self):
        """Test error when pyproject.toml doesn't exist."""
        with pytest.raises(VersionResolutionError, match="not found"):
            parse_requires_python("nonexistent.toml")

    def test_missing_requires_python(self, temp_pyproject):
        """Test error when requires-python is not specified."""
        pyproject = temp_pyproject(requires_python=None)

        with pytest.raises(VersionResolutionError, match="not specified"):
            parse_requires_python(pyproject)


class TestResolveTestVersions:
    """Tests for resolve_test_versions."""

    def test_basic_resolution(self, temp_pyproject):
        """Test basic version resolution."""
        pyproject = temp_pyproject(">=3.11")

        with patch(
            "testudos.versions.get_supported_python_versions",
            return_value=["3.10", "3.11", "3.12", "3.13"],
        ):
            versions = resolve_test_versions(pyproject)

            # Should only include versions >= 3.11
            assert "3.11" in versions
            assert "3.12" in versions
            assert "3.13" in versions
            assert "3.10" not in versions

    def test_explicit_versions_override(self, temp_pyproject):
        """Test that explicit versions override auto-detection."""
        pyproject = temp_pyproject(">=3.11")

        versions = resolve_test_versions(pyproject, explicit_versions=["3.10", "3.12"])

        # Should use explicit versions, ignoring requires-python
        assert versions == ["3.10", "3.12"]

    def test_explicit_versions_sorted(self, temp_pyproject):
        """Test that explicit versions are sorted."""
        pyproject = temp_pyproject(">=3.11")

        versions = resolve_test_versions(pyproject, explicit_versions=["3.13", "3.11", "3.12"])

        # Should be sorted
        assert versions == ["3.11", "3.12", "3.13"]

    def test_explicit_versions_validation(self, temp_pyproject):
        """Test that invalid explicit versions raise an error."""
        pyproject = temp_pyproject(">=3.11")

        with pytest.raises(VersionResolutionError, match="Invalid Python version"):
            resolve_test_versions(pyproject, explicit_versions=["3.11", "invalid"])

    def test_no_compatible_versions(self, temp_pyproject):
        """Test error when no compatible versions found."""
        pyproject = temp_pyproject(">=3.20")

        with patch(
            "testudos.versions.get_supported_python_versions",
            return_value=["3.10", "3.11", "3.12"],
        ):
            with pytest.raises(VersionResolutionError, match="No Python versions found"):
                resolve_test_versions(pyproject)

    def test_narrow_range(self, temp_pyproject):
        """Test resolution with narrow version range."""
        pyproject = temp_pyproject(">=3.11,<3.13")

        with patch(
            "testudos.versions.get_supported_python_versions",
            return_value=["3.10", "3.11", "3.12", "3.13"],
        ):
            versions = resolve_test_versions(pyproject)

            assert versions == ["3.11", "3.12"]
            assert "3.10" not in versions
            assert "3.13" not in versions
