# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
## [0.10.0] - 2025-12-27

### Changed
 - Renamed project to testudos

## [0.9.0] - 2025-12-27

### Added
- Strict mypy configuration with comprehensive type checking (resolves #27)
- Version bump validation script (`scripts/check_version_bump.py`)
- CI job to enforce version bump and changelog updates on PRs
- `just check-version` recipe for local validation

### Changed
- Migrated parallel execution to use only asyncio, removing ThreadPoolExecutor (resolves #19)
- `run_tests_parallel` replaced by `run_tests_parallel_async` in public API
- `runner.run()` now uses `asyncio.run()` internally for parallel execution

### Removed
- `run_tests_parallel` function (use `run_tests_parallel_async` instead)
- `concurrent.futures` dependency for parallel execution

### Fixed
- Type errors across codebase to satisfy strict mypy checks
- Added proper type annotations to nested async functions

## [0.8.0] - 2025-12-27

### Added
- GitHub Actions CI/CD workflow with lint, type-check, and test jobs
- Status check job for branch protection
- Local `justfile` for running CI commands during development

### Changed
- CI runs lint and type-check in parallel for faster feedback
- Optimized CI to reduce unnecessary workflow runs

## [0.7.0] - 2025-12-27

### Added
- Python 3.10 support - expanded compatibility from 3.11+ to 3.10+

### Changed
- Updated `requires-python` to `>=3.10`
- Added `tomli` as conditional dependency for Python < 3.11

## [0.6.0] - 2025-12-27

### Added
- Multi-package parallelism support for monorepos and workspaces
- `multi_runner` module for coordinating tests across multiple packages
- Enhanced UI for multi-package test progress display

## [0.5.0] - 2025-12-26

### Changed
- Removed `just` integration in favor of native testudos commands
- Simplified CLI interface - testudos now handles all commands directly

### Removed
- Justfile generation feature (Phase 4 functionality)
- `testudos generate` command

### Dependencies
- Bumped `typer` to >=0.21.0
- Bumped `rich` to >=14.0.0
- Bumped `httpx` to >=0.28.0
- Bumped `packaging` to >=25.0
- Bumped `pytest` to >=9.0.0
- Bumped `coverage` to >=7.13.0

## [0.4.0] - 2025-12-26

### Added
- Coverage aggregation across Python versions
- `testudos run --coverage` flag for collecting coverage data
- `testudos coverage combine` command for merging coverage from multiple versions
- `testudos coverage report` command with multiple format support (term, html, xml, json, lcov)
- `testudos coverage clean` command for removing coverage artifacts
- `--coverage-report` option for specifying report formats
- `--coverage-fail-under` option for enforcing coverage thresholds
- Coverage configuration options in `[tool.testudos]`

## [0.3.0] - 2025-12-26

### Changed
- Migrated parallel test execution from `ThreadPoolExecutor` to `asyncio`
- Improved architecture based on code review feedback
- Enhanced module separation and responsibility boundaries

### Fixed
- Various architectural improvements for better maintainability

## [0.2.0] - 2025-12-26

### Added
- Justfile generation for test commands (later removed in 0.5.0)
- Comprehensive test suite with high coverage
- Configuration validation with schema checking
- Input validation for safe command construction
- Warning system for unknown configuration keys

### Changed
- Polish and refinements across all modules
- Improved error messages and user feedback
- Enhanced documentation

## [0.1.0] - 2025-12-26

### Added
- Initial release of testudos
- Core Python version detection from `pyproject.toml` `requires-python` field
- Automatic fetching of supported Python versions from endoflife.date API
- 24-hour TTL caching for API responses with offline fallback
- Sequential test execution across Python versions
- Parallel test execution with `--parallel` / `-P` flag
- `--jobs` / `-j` option to limit parallel workers
- `--fail-fast` / `-f` flag to stop on first failure
- `--verbose` / `-v` flag for detailed output
- `--dry-run` / `-n` flag to preview commands
- `testudos run` command for executing tests
- `testudos versions` command to display compatible Python versions
- Configuration via `[tool.testudos]` in `pyproject.toml`
- Rich terminal UI with progress display
- Support for custom test commands and arguments

## [0.0.1] - 2025-12-18

### Added
- Initial project setup
- MIT License
- Architecture documentation and implementation roadmap
- Design decisions document

[0.9.0]: https://github.com/martinristovski/testudoss/compare/v0.8.0...v0.9.0
[0.8.0]: https://github.com/martinristovski/testudoss/compare/v0.7.0...v0.8.0
[0.7.0]: https://github.com/martinristovski/testudoss/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/martinristovski/testudoss/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/martinristovski/testudoss/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/martinristovski/testudoss/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/martinristovski/testudoss/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/martinristovski/testudoss/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/martinristovski/testudoss/compare/v0.0.1...v0.1.0
[0.0.1]: https://github.com/martinristovski/testudoss/releases/tag/v0.0.1
