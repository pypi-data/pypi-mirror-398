"""Testudos - A testing harness for Python packages.

Testudos simplifies running your Python package's test suite across
multiple Python versions using uv's isolated environments.
"""

from testudos.config import ConfigValidationError, TestudosConfig, validate_config
from testudos.coverage import (
    CoverageError,
    CoverageNotAvailableError,
    CoverageResult,
    CoverageSummary,
    check_coverage_available,
    clean_coverage_data,
    generate_coverage_report,
    get_combined_coverage_path,
    get_coverage_data_path,
    list_coverage_data_files,
    run_coverage_combine,
)
from testudos.executor import (
    CommandValidationError,
    ExecutorError,
    TestResult,
    TestStatus,
    check_uv_available,
    run_single_test,
    run_tests_parallel_async,
    run_tests_sequential,
    validate_test_args,
    validate_test_command,
    validate_version,
)
from testudos.python_version import (
    InvalidPythonVersionError,
    PythonVersion,
)
from testudos.runner import (
    RunOptions,
    RunPlan,
    TestRunner,
)
from testudos.versions import (
    CacheConfig,
    VersionResolutionError,
    cache_config_context,
    get_cache_config,
    get_supported_python_versions,
    parse_requires_python,
    resolve_test_versions,
    set_cache_config,
)

__all__ = [
    # Config
    "ConfigValidationError",
    "TestudosConfig",
    "validate_config",
    # Coverage
    "CoverageError",
    "CoverageNotAvailableError",
    "CoverageResult",
    "CoverageSummary",
    "check_coverage_available",
    "clean_coverage_data",
    "generate_coverage_report",
    "get_combined_coverage_path",
    "get_coverage_data_path",
    "list_coverage_data_files",
    "run_coverage_combine",
    # Executor
    "CommandValidationError",
    "ExecutorError",
    "TestResult",
    "TestStatus",
    "check_uv_available",
    "run_single_test",
    "run_tests_parallel_async",
    "run_tests_sequential",
    "validate_test_args",
    "validate_test_command",
    "validate_version",
    # Python Version
    "InvalidPythonVersionError",
    "PythonVersion",
    # Runner
    "RunOptions",
    "RunPlan",
    "TestRunner",
    # Versions
    "CacheConfig",
    "VersionResolutionError",
    "cache_config_context",
    "get_cache_config",
    "get_supported_python_versions",
    "parse_requires_python",
    "resolve_test_versions",
    "set_cache_config",
]
