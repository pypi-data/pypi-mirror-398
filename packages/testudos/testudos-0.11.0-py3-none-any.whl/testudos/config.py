"""Configuration loading for testudos.

This module handles loading and validating configuration from pyproject.toml.
Configuration can be specified in [tool.testudos] section.
"""

import sys

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib  # type: ignore[import-not-found]
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class ConfigValidationError(ValueError):
    """Raised when configuration validation fails."""

    pass


# Schema definition for [tool.testudos] section
# Each key maps to (expected_type, is_required, description)
CONFIG_SCHEMA: dict[str, tuple[type | tuple[type, ...], bool, str]] = {
    "python-versions": ((list, type(None)), False, "list of version strings like ['3.11', '3.12']"),
    "test-command": (str, False, "test command to run (e.g., 'pytest')"),
    "test-args": (list, False, "list of test arguments"),
    "parallel": (bool, False, "whether to run tests in parallel"),
    "max-jobs": ((int, type(None)), False, "maximum number of parallel jobs"),
    # Coverage options
    "coverage": (bool, False, "whether to collect coverage data"),
    "coverage-combine": (bool, False, "whether to combine coverage from all versions"),
    "coverage-report": (list, False, "list of report formats to generate (e.g., ['html', 'xml'])"),
    "coverage-fail-under": (
        (int, float, type(None)),
        False,
        "minimum coverage percentage required",
    ),
    "timeout": (
        (int, float, type(None)),
        False,
        "timeout in seconds per Python version test run",
    ),
}

# Known valid keys
VALID_KEYS = set(CONFIG_SCHEMA.keys())


def validate_config(config: dict[str, Any]) -> list[str]:
    """Validate a testudos configuration dictionary.

    Args:
        config: The [tool.testudos] section from pyproject.toml

    Returns:
        List of warning messages for unknown keys (validation still passes)

    Raises:
        ConfigValidationError: If a configuration value has the wrong type
    """
    warnings: list[str] = []

    # Check for unknown keys
    for key in config:
        if key not in VALID_KEYS:
            warnings.append(f"Unknown configuration key: '{key}'")

    # Validate known keys
    for key, (expected_type, is_required, description) in CONFIG_SCHEMA.items():
        if key not in config:
            if is_required:
                raise ConfigValidationError(f"Missing required configuration: '{key}'")
            continue

        value = config[key]

        # Handle None values
        if value is None:
            if isinstance(expected_type, tuple) and type(None) in expected_type:
                continue
            raise ConfigValidationError(
                f"Configuration '{key}' cannot be null. Expected {description}"
            )

        # Type check
        if not isinstance(value, expected_type):
            type_name = (
                expected_type.__name__ if isinstance(expected_type, type) else str(expected_type)
            )
            raise ConfigValidationError(
                f"Configuration '{key}' has wrong type: expected {type_name}, "
                f"got {type(value).__name__}. Expected {description}"
            )

        # Additional validation for specific fields
        if key == "python-versions" and value is not None:
            if not all(isinstance(v, str) for v in value):
                raise ConfigValidationError(
                    f"Configuration 'python-versions' must be a list of strings, got {value}"
                )
            # Validate version format
            for v in value:
                if not _is_valid_version_string(v):
                    raise ConfigValidationError(
                        f"Invalid Python version in 'python-versions': '{v}'. "
                        f"Expected format like '3.11' or '3.12'"
                    )

        if key == "test-args" and value is not None:
            if not all(isinstance(v, str) for v in value):
                raise ConfigValidationError(
                    f"Configuration 'test-args' must be a list of strings, got {value}"
                )

        if key == "max-jobs" and value is not None:
            if value < 1:
                raise ConfigValidationError(
                    f"Configuration 'max-jobs' must be at least 1, got {value}"
                )

        if key == "coverage-report" and value is not None:
            if not all(isinstance(v, str) for v in value):
                raise ConfigValidationError(
                    f"Configuration 'coverage-report' must be a list of strings, got {value}"
                )
            valid_formats = {"term", "term-missing", "html", "xml", "json", "lcov"}
            for fmt in value:
                if fmt not in valid_formats:
                    raise ConfigValidationError(
                        f"Invalid coverage report format: '{fmt}'. "
                        f"Valid formats are: {', '.join(sorted(valid_formats))}"
                    )

        if key == "coverage-fail-under" and value is not None:
            if value < 0 or value > 100:
                raise ConfigValidationError(
                    f"Configuration 'coverage-fail-under' must be between 0 and 100, got {value}"
                )

        if key == "timeout" and value is not None:
            if value <= 0:
                raise ConfigValidationError(
                    f"Configuration 'timeout' must be a positive number, got {value}"
                )

    return warnings


def _is_valid_version_string(version: str) -> bool:
    """Check if a version string is valid.

    Args:
        version: Version string like "3.11" or "3.12"

    Returns:
        True if valid, False otherwise
    """
    parts = version.split(".")
    if len(parts) < 2:
        return False
    try:
        major = int(parts[0])
        minor = int(parts[1])
        return major >= 0 and minor >= 0
    except ValueError:
        return False


@dataclass
class TestudosConfig:
    """Configuration for testudos test execution.

    This configuration can be specified in pyproject.toml under [tool.testudos]:

    [tool.testudos]
    python-versions = ["3.11", "3.12", "3.13"]  # Optional: override auto-detection
    test-command = "pytest"                      # Test command to run (default: pytest)
    test-args = ["-v", "--tb=short"]            # Additional arguments for test command
    parallel = false                             # Run tests in parallel (default: false)
    max-jobs = 4                                 # Max parallel jobs (default: number of versions)
    timeout = 300                                # Timeout per version in seconds (default: none)
    coverage = false                             # Enable coverage collection (default: false)
    coverage-combine = true                      # Combine coverage from all versions
    coverage-report = ["term"]                   # Report formats to generate
    coverage-fail-under = 0                      # Minimum coverage percentage (0 = disabled)
    """

    python_versions: list[str] | None = None
    test_command: str = "pytest"
    test_args: list[str] = field(default_factory=list)
    parallel: bool = False
    max_jobs: int | None = None
    timeout: float | None = None
    # Coverage options
    coverage: bool = False
    coverage_combine: bool = True
    coverage_report: list[str] = field(default_factory=lambda: ["term"])
    coverage_fail_under: float | None = None

    @classmethod
    def from_pyproject(
        cls,
        path: Path | str = "pyproject.toml",
        validate: bool = True,
    ) -> "TestudosConfig":
        """Load configuration from pyproject.toml.

        Args:
            path: Path to pyproject.toml file (default: "pyproject.toml")
            validate: Whether to validate the configuration (default: True)

        Returns:
            TestudosConfig instance with loaded configuration

        Raises:
            ConfigValidationError: If validation is enabled and config is invalid

        Note:
            If pyproject.toml doesn't exist or doesn't have [tool.testudos],
            returns a config with default values.
        """
        import warnings as warn_module

        path = Path(path)

        # If file doesn't exist, return defaults
        if not path.exists():
            return cls()

        with open(path, "rb") as f:
            data = tomllib.load(f)

        # Get [tool.testudos] section, or empty dict if not present
        tool_config = data.get("tool", {}).get("testudos", {})

        # Validate configuration if enabled
        if validate and tool_config:
            config_warnings = validate_config(tool_config)
            for warning in config_warnings:
                warn_module.warn(warning, UserWarning, stacklevel=2)

        # Convert kebab-case keys to snake_case for Python
        return cls(
            python_versions=tool_config.get("python-versions"),
            test_command=tool_config.get("test-command", "pytest"),
            test_args=tool_config.get("test-args", []),
            parallel=tool_config.get("parallel", False),
            max_jobs=tool_config.get("max-jobs"),
            timeout=tool_config.get("timeout"),
            # Coverage options
            coverage=tool_config.get("coverage", False),
            coverage_combine=tool_config.get("coverage-combine", True),
            coverage_report=tool_config.get("coverage-report", ["term"]),
            coverage_fail_under=tool_config.get("coverage-fail-under"),
        )

    def get_effective_max_jobs(self, num_versions: int) -> int:
        """Get the effective maximum number of parallel jobs.

        Args:
            num_versions: Number of Python versions to test

        Returns:
            Maximum number of parallel jobs (defaults to num_versions if not specified)
        """
        return self.max_jobs if self.max_jobs is not None else num_versions
