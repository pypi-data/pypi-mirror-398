"""Tests for PythonVersion type."""

import pytest

from testudos.python_version import (
    InvalidPythonVersionError,
    PythonVersion,
    validate_version_list,
    version_strings,
)


class TestPythonVersion:
    """Tests for PythonVersion dataclass."""

    def test_create_valid_version(self):
        """Test creating a valid PythonVersion."""
        version = PythonVersion(3, 11)
        assert version.major == 3
        assert version.minor == 11

    def test_str_representation(self):
        """Test string representation."""
        version = PythonVersion(3, 12)
        assert str(version) == "3.12"

    def test_with_patch(self):
        """Test with_patch method."""
        version = PythonVersion(3, 11)
        assert version.with_patch() == "3.11.0"
        assert version.with_patch(5) == "3.11.5"

    def test_negative_major_raises_error(self):
        """Test that negative major version raises error."""
        with pytest.raises(InvalidPythonVersionError, match="non-negative"):
            PythonVersion(-1, 11)

    def test_negative_minor_raises_error(self):
        """Test that negative minor version raises error."""
        with pytest.raises(InvalidPythonVersionError, match="non-negative"):
            PythonVersion(3, -1)


class TestPythonVersionParse:
    """Tests for PythonVersion.parse method."""

    def test_parse_simple_version(self):
        """Test parsing a simple version string."""
        version = PythonVersion.parse("3.11")
        assert version.major == 3
        assert version.minor == 11

    def test_parse_version_with_patch(self):
        """Test parsing a version with patch component."""
        version = PythonVersion.parse("3.11.5")
        assert version.major == 3
        assert version.minor == 11
        # Patch is ignored

    def test_parse_version_with_whitespace(self):
        """Test parsing version with surrounding whitespace."""
        version = PythonVersion.parse("  3.12  ")
        assert version.major == 3
        assert version.minor == 12

    def test_parse_empty_string_raises_error(self):
        """Test that empty string raises error."""
        with pytest.raises(InvalidPythonVersionError, match="empty"):
            PythonVersion.parse("")

    def test_parse_single_component_raises_error(self):
        """Test that single component raises error."""
        with pytest.raises(InvalidPythonVersionError, match="major.minor"):
            PythonVersion.parse("3")

    def test_parse_non_numeric_raises_error(self):
        """Test that non-numeric components raise error."""
        with pytest.raises(InvalidPythonVersionError, match="integers"):
            PythonVersion.parse("3.eleven")

    def test_parse_invalid_format_raises_error(self):
        """Test that invalid format raises error."""
        with pytest.raises(InvalidPythonVersionError):
            PythonVersion.parse("invalid")


class TestPythonVersionComparison:
    """Tests for PythonVersion comparison operations."""

    def test_equal_versions(self):
        """Test equality comparison."""
        v1 = PythonVersion(3, 11)
        v2 = PythonVersion(3, 11)
        assert v1 == v2

    def test_unequal_versions(self):
        """Test inequality comparison."""
        v1 = PythonVersion(3, 11)
        v2 = PythonVersion(3, 12)
        assert v1 != v2

    def test_less_than_minor(self):
        """Test less than comparison on minor version."""
        v1 = PythonVersion(3, 10)
        v2 = PythonVersion(3, 11)
        assert v1 < v2
        assert not v2 < v1

    def test_less_than_major(self):
        """Test less than comparison on major version."""
        v1 = PythonVersion(2, 7)
        v2 = PythonVersion(3, 0)
        assert v1 < v2

    def test_sorting(self):
        """Test sorting a list of versions."""
        versions = [
            PythonVersion(3, 12),
            PythonVersion(3, 10),
            PythonVersion(3, 11),
            PythonVersion(2, 7),
        ]
        sorted_versions = sorted(versions)
        assert sorted_versions == [
            PythonVersion(2, 7),
            PythonVersion(3, 10),
            PythonVersion(3, 11),
            PythonVersion(3, 12),
        ]

    def test_hash_for_set(self):
        """Test that versions can be used in sets."""
        v1 = PythonVersion(3, 11)
        v2 = PythonVersion(3, 11)
        v3 = PythonVersion(3, 12)

        version_set = {v1, v2, v3}
        assert len(version_set) == 2


class TestValidateVersionList:
    """Tests for validate_version_list function."""

    def test_validate_valid_list(self):
        """Test validating a list of valid versions."""
        versions = validate_version_list(["3.10", "3.11", "3.12"])
        assert len(versions) == 3
        assert all(isinstance(v, PythonVersion) for v in versions)

    def test_validate_empty_list(self):
        """Test validating an empty list."""
        versions = validate_version_list([])
        assert versions == []

    def test_validate_invalid_version_raises_error(self):
        """Test that invalid version in list raises error."""
        with pytest.raises(InvalidPythonVersionError):
            validate_version_list(["3.11", "invalid", "3.12"])


class TestVersionStrings:
    """Tests for version_strings function."""

    def test_convert_to_strings(self):
        """Test converting versions to strings."""
        versions = [
            PythonVersion(3, 10),
            PythonVersion(3, 11),
            PythonVersion(3, 12),
        ]
        strings = version_strings(versions)
        assert strings == ["3.10", "3.11", "3.12"]

    def test_empty_list(self):
        """Test converting empty list."""
        assert version_strings([]) == []
