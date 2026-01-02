"""Python version resolution for testudos.

This module handles:
1. Fetching currently supported Python versions from endoflife.date API
2. Parsing requires-python from pyproject.toml
3. Computing the intersection to determine which versions to test
"""

import json
import os
import sys
import time

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib  # type: ignore[import-not-found]
import warnings
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import httpx
from packaging.specifiers import SpecifierSet

from testudos.python_version import InvalidPythonVersionError, PythonVersion

# API endpoint for Python version data
ENDOFLIFE_API = "https://endoflife.date/api/python.json"

# Fallback versions (updated with each release)
FALLBACK_VERSIONS = ["3.11", "3.12", "3.13", "3.14"]


@dataclass
class CacheConfig:
    """Configuration for version cache.

    This allows customizing cache location and TTL, making testing easier
    and supporting different environments.
    """

    cache_dir: Path
    cache_file: Path
    ttl: timedelta

    @classmethod
    def default(cls) -> "CacheConfig":
        """Create default cache configuration.

        Uses XDG_CACHE_HOME if available, otherwise ~/.cache.
        """
        base_dir = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
        cache_dir = base_dir / "testudos"
        return cls(
            cache_dir=cache_dir,
            cache_file=cache_dir / "endoflife.json",
            ttl=timedelta(hours=24),
        )


# Global default cache configuration
_cache_config = CacheConfig.default()


def get_cache_config() -> CacheConfig:
    """Get the current cache configuration."""
    return _cache_config


def set_cache_config(config: CacheConfig) -> None:
    """Set the cache configuration.

    This is primarily useful for testing.

    Args:
        config: New cache configuration to use
    """
    global _cache_config
    _cache_config = config


@contextmanager
def cache_config_context(config: CacheConfig) -> Generator[CacheConfig, None, None]:
    """Context manager for temporarily setting cache configuration.

    This ensures the original configuration is restored after the context exits,
    making it safe to use in tests without manual cleanup.

    Args:
        config: Cache configuration to use within the context

    Yields:
        The cache configuration being used

    Example:
        with cache_config_context(temp_config):
            versions = get_supported_python_versions()
    """
    old_config = get_cache_config()
    set_cache_config(config)
    try:
        yield config
    finally:
        set_cache_config(old_config)


# Retry configuration for API calls
MAX_RETRIES = 3
INITIAL_BACKOFF = 1.0  # seconds
MAX_BACKOFF = 10.0  # seconds
BACKOFF_MULTIPLIER = 2.0


class VersionResolutionError(Exception):
    """Raised when version resolution fails."""

    pass


def _ensure_cache_dir() -> None:
    """Ensure the cache directory exists."""
    _cache_config.cache_dir.mkdir(parents=True, exist_ok=True)


def _load_cache() -> dict[str, Any] | None:
    """Load cached version data if it exists and hasn't expired."""
    if not _cache_config.cache_file.exists():
        return None

    try:
        with open(_cache_config.cache_file) as f:
            data = json.load(f)

        # Check if cache has expired
        cached_time = datetime.fromisoformat(data["timestamp"])
        if datetime.now() - cached_time > _cache_config.ttl:
            return None

        return dict(data)
    except (KeyError, ValueError, json.JSONDecodeError):
        return None


def _save_cache(versions: list[str]) -> None:
    """Save version data to cache."""
    _ensure_cache_dir()

    data = {"timestamp": datetime.now().isoformat(), "versions": versions}

    with open(_cache_config.cache_file, "w") as f:
        json.dump(data, f)


def _fetch_from_api_once() -> list[str]:
    """Fetch currently supported Python versions from endoflife.date API (single attempt).

    Returns:
        List of Python version strings (e.g., ["3.11", "3.12", "3.13"])

    Raises:
        httpx.HTTPError: If the API request fails
    """
    response = httpx.get(ENDOFLIFE_API, timeout=10.0)
    response.raise_for_status()
    data = response.json()

    supported = []
    for release in data:
        # Include versions that are not EOL (either in bugfix or security support)
        # eol can be a date string or boolean False
        eol = release.get("eol")

        if eol is False:
            # Not EOL yet
            supported.append(release["cycle"])
        elif isinstance(eol, str):
            # Check if EOL date is in the future
            try:
                eol_date = datetime.fromisoformat(eol)
                if eol_date > datetime.now():
                    supported.append(release["cycle"])
            except ValueError:
                # If we can't parse the date, skip this version
                continue

    # Sort versions by semantic version
    return sorted(supported, key=lambda v: tuple(map(int, v.split("."))))


def _fetch_from_api() -> list[str]:
    """Fetch currently supported Python versions with retry and exponential backoff.

    Retries up to MAX_RETRIES times with exponential backoff between attempts.

    Returns:
        List of Python version strings (e.g., ["3.11", "3.12", "3.13"])

    Raises:
        httpx.HTTPError: If all retry attempts fail
    """
    last_exception: Exception | None = None
    backoff = INITIAL_BACKOFF

    for attempt in range(MAX_RETRIES):
        try:
            return _fetch_from_api_once()
        except (httpx.HTTPError, httpx.TimeoutException, httpx.ConnectError) as e:
            last_exception = e
            if attempt < MAX_RETRIES - 1:
                # Wait before retrying with exponential backoff
                time.sleep(backoff)
                backoff = min(backoff * BACKOFF_MULTIPLIER, MAX_BACKOFF)

    # All retries exhausted, raise the last exception
    raise last_exception  # type: ignore[misc]


def get_supported_python_versions(use_cache: bool = True) -> list[str]:
    """Get currently supported Python versions.

    This function tries to fetch versions from the endoflife.date API.
    If that fails, it falls back to cached data or bundled fallback versions.

    Args:
        use_cache: Whether to use cached data (default: True)

    Returns:
        List of Python version strings (e.g., ["3.11", "3.12", "3.13"])
    """
    # Try cache first if enabled
    if use_cache:
        cached = _load_cache()
        if cached:
            return list(cached["versions"])

    # Try to fetch from API
    try:
        versions = _fetch_from_api()
        _save_cache(versions)
        return versions
    except (httpx.HTTPError, httpx.TimeoutException, KeyError, Exception):
        # If API fails, try cache (even if expired)
        if use_cache:
            cached = _load_cache()
            if cached:
                warnings.warn(
                    "Could not reach endoflife.date API, using cached version data",
                    UserWarning,
                    stacklevel=2,
                )
                return list(cached["versions"])

        # Fall back to bundled versions
        warnings.warn(
            "Could not reach endoflife.date API, using bundled fallback versions",
            UserWarning,
            stacklevel=2,
        )
        return FALLBACK_VERSIONS


def parse_requires_python(pyproject_path: Path | str) -> SpecifierSet:
    """Parse requires-python from pyproject.toml.

    Args:
        pyproject_path: Path to pyproject.toml file

    Returns:
        SpecifierSet representing the Python version requirement

    Raises:
        VersionResolutionError: If pyproject.toml is missing or requires-python is not specified
    """
    pyproject_path = Path(pyproject_path)

    if not pyproject_path.exists():
        raise VersionResolutionError(f"pyproject.toml not found at {pyproject_path}")

    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)

    requires_python = data.get("project", {}).get("requires-python")

    if not requires_python:
        raise VersionResolutionError(
            "requires-python not specified in pyproject.toml. Please add it to [project] section."
        )

    return SpecifierSet(requires_python)


def resolve_test_versions(
    pyproject_path: Path | str = "pyproject.toml",
    explicit_versions: list[str] | None = None,
) -> list[str]:
    """Determine which Python versions to test against.

    This computes the intersection of:
    1. Currently supported Python versions (from endoflife.date)
    2. Package-compatible versions (from requires-python in pyproject.toml)

    Args:
        pyproject_path: Path to pyproject.toml file (default: "pyproject.toml")
        explicit_versions: If provided, use these versions instead of auto-detection

    Returns:
        List of Python version strings to test (e.g., ["3.11", "3.12", "3.13"])

    Raises:
        VersionResolutionError: If version resolution fails or explicit versions are invalid
    """
    # If explicit versions provided, validate and use those
    if explicit_versions:
        try:
            validated = [PythonVersion.parse(v) for v in explicit_versions]
            return [str(v) for v in sorted(validated)]
        except InvalidPythonVersionError as e:
            raise VersionResolutionError(f"Invalid Python version: {e}") from e

    # Get supported versions
    supported = get_supported_python_versions()

    # Parse requires-python specifier
    specifier = parse_requires_python(pyproject_path)

    # Filter supported versions by requires-python compatibility
    # We need to convert version strings like "3.11" to "3.11.0" for specifier matching
    compatible = []
    for version in supported:
        # Try matching with .0 appended (e.g., "3.11.0")
        version_with_patch = f"{version}.0"
        if version_with_patch in specifier:
            compatible.append(version)

    if not compatible:
        raise VersionResolutionError(
            f"No Python versions found that are both supported and compatible with "
            f"requires-python = '{specifier}'. "
            f"Supported versions: {', '.join(supported)}"
        )

    return compatible
