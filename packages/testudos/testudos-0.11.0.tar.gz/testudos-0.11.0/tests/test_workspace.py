"""Tests for workspace module."""

from pathlib import Path

import pytest

from testudos.executor import TestResult
from testudos.workspace import (
    PackageResult,
    PackageSpec,
    WorkspaceConfig,
    WorkspaceResult,
)


class TestPackageSpec:
    """Tests for PackageSpec dataclass."""

    def test_init_with_name(self, tmp_path: Path) -> None:
        """Test initialization with explicit name."""
        pkg = PackageSpec(path=tmp_path, name="my-package")
        assert pkg.path == tmp_path
        assert pkg.name == "my-package"
        assert pkg.display_name == "my-package"

    def test_init_derives_name_from_path(self, tmp_path: Path) -> None:
        """Test that name is derived from path if not provided."""
        pkg = PackageSpec(path=tmp_path)
        assert pkg.name == tmp_path.name

    def test_init_derives_name_from_pyproject(self, tmp_path: Path) -> None:
        """Test that name is derived from pyproject.toml if available."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[project]
name = "cool-project"
version = "1.0.0"
""")
        pkg = PackageSpec(path=tmp_path)
        assert pkg.name == "cool-project"

    def test_init_derives_name_from_poetry_pyproject(self, tmp_path: Path) -> None:
        """Test that name is derived from Poetry pyproject.toml."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[tool.poetry]
name = "poetry-project"
version = "1.0.0"
""")
        pkg = PackageSpec(path=tmp_path)
        assert pkg.name == "poetry-project"

    def test_path_is_resolved(self, tmp_path: Path) -> None:
        """Test that path is resolved to absolute."""
        relative = Path(".")
        pkg = PackageSpec(path=relative)
        assert pkg.path.is_absolute()

    def test_pyproject_path(self, tmp_path: Path) -> None:
        """Test pyproject_path property."""
        pkg = PackageSpec(path=tmp_path)
        assert pkg.pyproject_path == tmp_path / "pyproject.toml"

    def test_has_pyproject_true(self, tmp_path: Path) -> None:
        """Test has_pyproject returns True when file exists."""
        (tmp_path / "pyproject.toml").touch()
        pkg = PackageSpec(path=tmp_path)
        assert pkg.has_pyproject() is True

    def test_has_pyproject_false(self, tmp_path: Path) -> None:
        """Test has_pyproject returns False when file doesn't exist."""
        pkg = PackageSpec(path=tmp_path)
        assert pkg.has_pyproject() is False


class TestPackageResult:
    """Tests for PackageResult dataclass."""

    def test_success_all_passed(self, tmp_path: Path) -> None:
        """Test success property when all tests pass."""
        pkg = PackageSpec(path=tmp_path, name="pkg")
        result = PackageResult(
            package=pkg,
            results={
                "3.11": TestResult(version="3.11", success=True, return_code=0),
                "3.12": TestResult(version="3.12", success=True, return_code=0),
            },
        )
        assert result.success is True

    def test_success_some_failed(self, tmp_path: Path) -> None:
        """Test success property when some tests fail."""
        pkg = PackageSpec(path=tmp_path, name="pkg")
        result = PackageResult(
            package=pkg,
            results={
                "3.11": TestResult(version="3.11", success=True, return_code=0),
                "3.12": TestResult(version="3.12", success=False, return_code=1),
            },
        )
        assert result.success is False

    def test_success_empty_results(self, tmp_path: Path) -> None:
        """Test success property with no results."""
        pkg = PackageSpec(path=tmp_path, name="pkg")
        result = PackageResult(package=pkg, results={})
        assert result.success is False

    def test_total_duration(self, tmp_path: Path) -> None:
        """Test total_duration property."""
        pkg = PackageSpec(path=tmp_path, name="pkg")
        result = PackageResult(
            package=pkg,
            results={
                "3.11": TestResult(version="3.11", success=True, return_code=0, duration=1.5),
                "3.12": TestResult(version="3.12", success=True, return_code=0, duration=2.5),
            },
        )
        assert result.total_duration == 4.0

    def test_passed_count(self, tmp_path: Path) -> None:
        """Test passed_count property."""
        pkg = PackageSpec(path=tmp_path, name="pkg")
        result = PackageResult(
            package=pkg,
            results={
                "3.11": TestResult(version="3.11", success=True, return_code=0),
                "3.12": TestResult(version="3.12", success=False, return_code=1),
                "3.13": TestResult(version="3.13", success=True, return_code=0),
            },
        )
        assert result.passed_count == 2

    def test_failed_count(self, tmp_path: Path) -> None:
        """Test failed_count property."""
        pkg = PackageSpec(path=tmp_path, name="pkg")
        result = PackageResult(
            package=pkg,
            results={
                "3.11": TestResult(version="3.11", success=True, return_code=0),
                "3.12": TestResult(version="3.12", success=False, return_code=1),
                "3.13": TestResult(version="3.13", success=False, return_code=1),
            },
        )
        assert result.failed_count == 2

    def test_get_failed_output(self, tmp_path: Path) -> None:
        """Test get_failed_output method."""
        pkg = PackageSpec(path=tmp_path, name="pkg")
        result = PackageResult(
            package=pkg,
            results={
                "3.11": TestResult(
                    version="3.11",
                    success=False,
                    return_code=1,
                    output="Test failed!",
                ),
            },
        )
        output = result.get_failed_output()
        assert "pkg" in output
        assert "3.11" in output
        assert "Test failed!" in output


class TestWorkspaceResult:
    """Tests for WorkspaceResult dataclass."""

    def test_all_passed_true(self, tmp_path: Path) -> None:
        """Test all_passed when all packages pass."""
        pkg1 = PackageSpec(path=tmp_path / "pkg1", name="pkg1")
        pkg2 = PackageSpec(path=tmp_path / "pkg2", name="pkg2")

        result = WorkspaceResult(
            package_results={
                "pkg1": PackageResult(
                    package=pkg1,
                    results={"3.11": TestResult(version="3.11", success=True, return_code=0)},
                ),
                "pkg2": PackageResult(
                    package=pkg2,
                    results={"3.11": TestResult(version="3.11", success=True, return_code=0)},
                ),
            }
        )
        assert result.all_passed is True

    def test_all_passed_false(self, tmp_path: Path) -> None:
        """Test all_passed when some packages fail."""
        pkg1 = PackageSpec(path=tmp_path / "pkg1", name="pkg1")
        pkg2 = PackageSpec(path=tmp_path / "pkg2", name="pkg2")

        result = WorkspaceResult(
            package_results={
                "pkg1": PackageResult(
                    package=pkg1,
                    results={"3.11": TestResult(version="3.11", success=True, return_code=0)},
                ),
                "pkg2": PackageResult(
                    package=pkg2,
                    results={"3.11": TestResult(version="3.11", success=False, return_code=1)},
                ),
            }
        )
        assert result.all_passed is False

    def test_package_counts(self, tmp_path: Path) -> None:
        """Test package count properties."""
        pkg1 = PackageSpec(path=tmp_path / "pkg1", name="pkg1")
        pkg2 = PackageSpec(path=tmp_path / "pkg2", name="pkg2")
        pkg3 = PackageSpec(path=tmp_path / "pkg3", name="pkg3")

        result = WorkspaceResult(
            package_results={
                "pkg1": PackageResult(
                    package=pkg1,
                    results={"3.11": TestResult(version="3.11", success=True, return_code=0)},
                ),
                "pkg2": PackageResult(
                    package=pkg2,
                    results={"3.11": TestResult(version="3.11", success=False, return_code=1)},
                ),
                "pkg3": PackageResult(
                    package=pkg3,
                    results={"3.11": TestResult(version="3.11", success=True, return_code=0)},
                ),
            }
        )
        assert result.total_packages == 3
        assert result.passed_packages == 2
        assert result.failed_packages == 1

    def test_get_summary(self, tmp_path: Path) -> None:
        """Test get_summary method."""
        pkg1 = PackageSpec(path=tmp_path / "pkg1", name="pkg1")
        pkg2 = PackageSpec(path=tmp_path / "pkg2", name="pkg2")

        result = WorkspaceResult(
            package_results={
                "pkg1": PackageResult(
                    package=pkg1,
                    results={
                        "3.11": TestResult(version="3.11", success=True, return_code=0),
                        "3.12": TestResult(version="3.12", success=True, return_code=0),
                    },
                ),
                "pkg2": PackageResult(
                    package=pkg2,
                    results={
                        "3.11": TestResult(version="3.11", success=False, return_code=1),
                        "3.12": TestResult(version="3.12", success=True, return_code=0),
                    },
                ),
            }
        )
        summary = result.get_summary()
        assert summary["total_packages"] == 2
        assert summary["passed_packages"] == 1
        assert summary["failed_packages"] == 1
        assert summary["total_versions"] == 4
        assert summary["passed_versions"] == 3
        assert summary["failed_versions"] == 1


class TestWorkspaceConfig:
    """Tests for WorkspaceConfig dataclass."""

    def test_from_paths(self, tmp_path: Path) -> None:
        """Test from_paths class method."""
        pkg1 = tmp_path / "pkg1"
        pkg2 = tmp_path / "pkg2"
        pkg1.mkdir()
        pkg2.mkdir()

        config = WorkspaceConfig.from_paths([pkg1, pkg2])
        assert len(config.packages) == 2
        assert config.parallel_packages is True
        assert config.max_package_workers is None

    def test_from_paths_with_options(self, tmp_path: Path) -> None:
        """Test from_paths with parallelism options."""
        pkg1 = tmp_path / "pkg1"
        pkg1.mkdir()

        config = WorkspaceConfig.from_paths([pkg1], parallel=False, max_workers=2)
        assert config.parallel_packages is False
        assert config.max_package_workers == 2

    def test_from_paths_nonexistent(self, tmp_path: Path) -> None:
        """Test from_paths with nonexistent path raises error."""
        with pytest.raises(ValueError, match="does not exist"):
            WorkspaceConfig.from_paths([tmp_path / "nonexistent"])

    def test_from_paths_not_directory(self, tmp_path: Path) -> None:
        """Test from_paths with file raises error."""
        file_path = tmp_path / "file.txt"
        file_path.touch()

        with pytest.raises(ValueError, match="not a directory"):
            WorkspaceConfig.from_paths([file_path])

    def test_auto_discover(self, tmp_path: Path) -> None:
        """Test auto_discover finds packages with pyproject.toml."""
        # Create packages
        pkg1 = tmp_path / "pkg1"
        pkg2 = tmp_path / "pkg2"
        pkg1.mkdir()
        pkg2.mkdir()
        (pkg1 / "pyproject.toml").touch()
        (pkg2 / "pyproject.toml").touch()

        config = WorkspaceConfig.auto_discover(tmp_path)
        assert len(config.packages) == 2

    def test_auto_discover_excludes_hidden(self, tmp_path: Path) -> None:
        """Test auto_discover excludes hidden directories."""
        hidden = tmp_path / ".hidden"
        hidden.mkdir()
        (hidden / "pyproject.toml").touch()

        config = WorkspaceConfig.auto_discover(tmp_path)
        assert len(config.packages) == 0

    def test_auto_discover_excludes_venv(self, tmp_path: Path) -> None:
        """Test auto_discover excludes venv directories."""
        venv = tmp_path / "venv"
        venv.mkdir()
        (venv / "pyproject.toml").touch()

        config = WorkspaceConfig.auto_discover(tmp_path)
        assert len(config.packages) == 0

    def test_validate_empty_packages(self) -> None:
        """Test validate catches empty packages."""
        config = WorkspaceConfig(packages=[])
        errors = config.validate()
        assert any("No packages specified" in e for e in errors)

    def test_validate_missing_path(self, tmp_path: Path) -> None:
        """Test validate catches missing paths."""
        pkg = PackageSpec(path=tmp_path / "nonexistent", name="pkg")
        config = WorkspaceConfig(packages=[pkg])
        errors = config.validate()
        assert any("does not exist" in e for e in errors)

    def test_validate_missing_pyproject(self, tmp_path: Path) -> None:
        """Test validate catches missing pyproject.toml."""
        pkg_dir = tmp_path / "pkg"
        pkg_dir.mkdir()
        pkg = PackageSpec(path=pkg_dir, name="pkg")
        config = WorkspaceConfig(packages=[pkg])
        errors = config.validate()
        assert any("no pyproject.toml" in e for e in errors)

    def test_validate_duplicate_names(self, tmp_path: Path) -> None:
        """Test validate catches duplicate package names."""
        pkg1 = tmp_path / "pkg1"
        pkg2 = tmp_path / "pkg2"
        pkg1.mkdir()
        pkg2.mkdir()
        (pkg1 / "pyproject.toml").touch()
        (pkg2 / "pyproject.toml").touch()

        config = WorkspaceConfig(
            packages=[
                PackageSpec(path=pkg1, name="same-name"),
                PackageSpec(path=pkg2, name="same-name"),
            ]
        )
        errors = config.validate()
        assert any("Duplicate package name" in e for e in errors)

    def test_validate_invalid_max_workers(self, tmp_path: Path) -> None:
        """Test validate catches invalid max_package_workers."""
        pkg = tmp_path / "pkg"
        pkg.mkdir()
        (pkg / "pyproject.toml").touch()

        config = WorkspaceConfig(
            packages=[PackageSpec(path=pkg, name="pkg")],
            max_package_workers=0,
        )
        errors = config.validate()
        assert any("at least 1" in e for e in errors)
