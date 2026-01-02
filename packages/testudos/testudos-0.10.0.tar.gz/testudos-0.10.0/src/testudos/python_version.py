"""Python version type for testudos.

This module provides a validated PythonVersion type that ensures
version strings are properly formatted.
"""

from dataclasses import dataclass
from functools import total_ordering


class InvalidPythonVersionError(ValueError):
    """Raised when a Python version string is invalid."""

    pass


@total_ordering
@dataclass(frozen=True)
class PythonVersion:
    """A validated Python version with major and minor components.

    This class ensures Python version strings are properly formatted
    and provides comparison operations for sorting.

    Examples:
        >>> PythonVersion.parse("3.11")
        PythonVersion(major=3, minor=11)
        >>> str(PythonVersion(3, 12))
        '3.12'
    """

    major: int
    minor: int

    def __post_init__(self) -> None:
        """Validate version components."""
        if self.major < 0:
            raise InvalidPythonVersionError(f"Major version must be non-negative, got {self.major}")
        if self.minor < 0:
            raise InvalidPythonVersionError(f"Minor version must be non-negative, got {self.minor}")

    @classmethod
    def parse(cls, version_str: str) -> "PythonVersion":
        """Parse a version string into a PythonVersion.

        Args:
            version_str: A version string like "3.11" or "3.12"

        Returns:
            A PythonVersion instance

        Raises:
            InvalidPythonVersionError: If the version string is invalid
        """
        version_str = version_str.strip()

        if not version_str:
            raise InvalidPythonVersionError("Version string cannot be empty")

        parts = version_str.split(".")

        if len(parts) < 2:
            raise InvalidPythonVersionError(
                f"Version must have major.minor format, got '{version_str}'"
            )

        # Only use major.minor, ignore patch if present
        try:
            major = int(parts[0])
            minor = int(parts[1])
        except ValueError as e:
            raise InvalidPythonVersionError(
                f"Version components must be integers, got '{version_str}'"
            ) from e

        return cls(major=major, minor=minor)

    def __str__(self) -> str:
        """Return the version as a string."""
        return f"{self.major}.{self.minor}"

    def __lt__(self, other: object) -> bool:
        """Compare versions for sorting."""
        if not isinstance(other, PythonVersion):
            return NotImplemented
        return (self.major, self.minor) < (other.major, other.minor)

    def __eq__(self, other: object) -> bool:
        """Check version equality."""
        if not isinstance(other, PythonVersion):
            return NotImplemented
        return self.major == other.major and self.minor == other.minor

    def __hash__(self) -> int:
        """Hash the version for use in sets/dicts."""
        return hash((self.major, self.minor))

    def with_patch(self, patch: int = 0) -> str:
        """Return version string with patch component.

        Args:
            patch: Patch version number (default: 0)

        Returns:
            Version string like "3.11.0"
        """
        return f"{self.major}.{self.minor}.{patch}"


def validate_version_list(versions: list[str]) -> list[PythonVersion]:
    """Validate a list of version strings.

    Args:
        versions: List of version strings to validate

    Returns:
        List of validated PythonVersion objects

    Raises:
        InvalidPythonVersionError: If any version string is invalid
    """
    return [PythonVersion.parse(v) for v in versions]


def version_strings(versions: list[PythonVersion]) -> list[str]:
    """Convert a list of PythonVersion objects to strings.

    Args:
        versions: List of PythonVersion objects

    Returns:
        List of version strings
    """
    return [str(v) for v in versions]
