#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "packaging>=24.0",
#     "tomli>=2.0.0; python_version < '3.11'",
# ]
# ///
"""Check that version and changelog have been updated before merging to main.

This script verifies:
1. The version in pyproject.toml has been bumped compared to main
2. CHANGELOG.md has been modified compared to main
3. The new version is documented in CHANGELOG.md

Usage:
    uv run scripts/check_version_bump.py
"""

from __future__ import annotations

import re
import subprocess
import sys

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore[import-not-found,no-redef]

from packaging.version import Version


def get_current_version() -> str:
    """Get version from current pyproject.toml."""
    with open("pyproject.toml", "rb") as f:
        data = tomllib.load(f)
    return data["project"]["version"]


def get_main_version() -> str | None:
    """Get version from main branch's pyproject.toml."""
    try:
        result = subprocess.run(
            ["git", "show", "origin/main:pyproject.toml"],
            capture_output=True,
            text=True,
            check=True,
        )
        data = tomllib.loads(result.stdout)
        return data["project"]["version"]
    except subprocess.CalledProcessError:
        # Main branch might not exist yet (first PR)
        return None


def check_changelog_has_version(version: str) -> bool:
    """Check if version is documented in CHANGELOG.md."""
    try:
        with open("CHANGELOG.md") as f:
            content = f.read()
        # Look for version header like "## [0.8.0]" or "## [0.8.0] - 2025-12-27"
        pattern = rf"## \[{re.escape(version)}\]"
        return bool(re.search(pattern, content))
    except FileNotFoundError:
        return False


def check_changelog_modified() -> bool:
    """Check if CHANGELOG.md has been modified compared to main."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "origin/main...HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        changed_files = result.stdout.strip().split("\n")
        return "CHANGELOG.md" in changed_files
    except subprocess.CalledProcessError:
        # If we can't compare, check if file exists at all on main
        result = subprocess.run(
            ["git", "show", "origin/main:CHANGELOG.md"],
            capture_output=True,
            text=True,
        )
        # If CHANGELOG.md doesn't exist on main, any local version is "new"
        return result.returncode != 0


def check_pyproject_modified() -> bool:
    """Check if pyproject.toml has been modified compared to main."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "origin/main...HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        changed_files = result.stdout.strip().split("\n")
        return "pyproject.toml" in changed_files
    except subprocess.CalledProcessError:
        return False


def main() -> int:
    current_version = get_current_version()
    main_version = get_main_version()

    print(f"Current branch version: {current_version}")
    print(f"Main branch version:    {main_version or '(not found)'}")

    errors: list[str] = []

    # If main doesn't exist yet, just check changelog exists with version
    if main_version is None:
        print("Main branch not found - skipping comparison checks")
        if not check_changelog_has_version(current_version):
            print(f"\n❌ Version {current_version} not found in CHANGELOG.md")
            return 1
        print(f"\n✓ Version {current_version} is documented in CHANGELOG.md")
        return 0

    # Check pyproject.toml is modified
    if not check_pyproject_modified():
        errors.append("pyproject.toml has not been modified")

    # Check CHANGELOG.md is modified
    if not check_changelog_modified():
        errors.append("CHANGELOG.md has not been modified")

    # Compare versions
    current = Version(current_version)
    main = Version(main_version)

    if current <= main:
        errors.append(
            f"Version not bumped: {main_version} → {current_version}\n"
            f"   Please update the version in pyproject.toml"
        )

    # Check changelog has the new version entry
    if not check_changelog_has_version(current_version):
        errors.append(
            f"Version {current_version} not found in CHANGELOG.md\n"
            f"   Please add a changelog entry for this version"
        )

    # Report results
    if errors:
        print("\n❌ Version check failed:\n")
        for error in errors:
            print(f"   • {error}")
        return 1

    print(f"\n✓ Version bumped: {main_version} → {current_version}")
    print(f"✓ pyproject.toml has been modified")
    print(f"✓ CHANGELOG.md has been modified")
    print(f"✓ Version {current_version} is documented in CHANGELOG.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
