"""Tests for multi-package UI components."""

import re
from io import StringIO
from pathlib import Path

import pytest
from rich.console import Console

from testudos.executor import TestResult, TestStatus
from testudos.ui import MultiPackageProgressDisplay, display_multi_package_results
from testudos.workspace import PackageResult, PackageSpec, WorkspaceResult


def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from text."""
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", text)


@pytest.fixture
def sample_packages(tmp_path: Path) -> list[PackageSpec]:
    """Create sample PackageSpec objects."""
    return [
        PackageSpec(path=tmp_path / "pkg1", name="pkg1"),
        PackageSpec(path=tmp_path / "pkg2", name="pkg2"),
        PackageSpec(path=tmp_path / "pkg3", name="pkg3"),
    ]


class TestMultiPackageProgressDisplay:
    """Tests for MultiPackageProgressDisplay class."""

    def test_init(self, sample_packages: list[PackageSpec]) -> None:
        """Test initialization."""
        display = MultiPackageProgressDisplay(sample_packages)
        assert display.packages == sample_packages
        assert display.show_versions is False
        assert len(display.statuses) == 3

    def test_init_with_show_versions(self, sample_packages: list[PackageSpec]) -> None:
        """Test initialization with show_versions=True."""
        display = MultiPackageProgressDisplay(sample_packages, show_versions=True)
        assert display.show_versions is True

    def test_register_versions(self, sample_packages: list[PackageSpec]) -> None:
        """Test registering versions for a package."""
        display = MultiPackageProgressDisplay(sample_packages)
        display.register_versions("pkg1", ["3.11", "3.12", "3.13"])

        assert len(display.statuses["pkg1"]) == 3
        assert all(s == TestStatus.PENDING for s in display.statuses["pkg1"].values())

    def test_update(self, sample_packages: list[PackageSpec]) -> None:
        """Test updating status for a package/version."""
        display = MultiPackageProgressDisplay(sample_packages)
        display.register_versions("pkg1", ["3.11"])

        # Update to running
        display.update("pkg1", "3.11", TestStatus.RUNNING, None)
        assert display.statuses["pkg1"]["3.11"] == TestStatus.RUNNING

        # Update to passed
        result = TestResult(version="3.11", success=True, return_code=0, duration=1.5)
        display.update("pkg1", "3.11", TestStatus.PASSED, result)
        assert display.statuses["pkg1"]["3.11"] == TestStatus.PASSED
        assert display.results["pkg1"]["3.11"] == result

    def test_update_creates_package_if_missing(self, sample_packages: list[PackageSpec]) -> None:
        """Test that update creates package entry if missing."""
        display = MultiPackageProgressDisplay(sample_packages)

        # Update for a package that wasn't registered
        display.update("new-pkg", "3.11", TestStatus.RUNNING, None)
        assert "new-pkg" in display.statuses
        assert display.statuses["new-pkg"]["3.11"] == TestStatus.RUNNING

    def test_render_collapsed(self, sample_packages: list[PackageSpec]) -> None:
        """Test rendering collapsed view."""
        display = MultiPackageProgressDisplay(sample_packages, show_versions=False)
        display.register_versions("pkg1", ["3.11", "3.12"])
        display.register_versions("pkg2", ["3.11", "3.12"])

        # Set some statuses
        display.update(
            "pkg1",
            "3.11",
            TestStatus.PASSED,
            TestResult(version="3.11", success=True, return_code=0),
        )
        display.update(
            "pkg1",
            "3.12",
            TestStatus.PASSED,
            TestResult(version="3.12", success=True, return_code=0),
        )
        display.update("pkg2", "3.11", TestStatus.RUNNING, None)

        table = display.render()
        assert table.title == "Multi-Package Test Progress"
        assert len(table.columns) == 3

    def test_render_expanded(self, sample_packages: list[PackageSpec]) -> None:
        """Test rendering expanded view."""
        display = MultiPackageProgressDisplay(sample_packages, show_versions=True)
        display.register_versions("pkg1", ["3.11", "3.12"])
        display.register_versions("pkg2", ["3.11"])

        table = display.render()
        assert table.title == "Multi-Package Test Progress"
        assert len(table.columns) == 3  # Package, Version, Status

    def test_render_all_pending(self, sample_packages: list[PackageSpec]) -> None:
        """Test rendering when all packages are pending."""
        display = MultiPackageProgressDisplay(sample_packages[:1])
        display.register_versions("pkg1", ["3.11", "3.12"])

        table = display.render()
        # Should show "Pending" status
        console = Console(file=StringIO(), force_terminal=True)
        console.print(table)
        output = console.file.getvalue()
        assert "Pending" in output

    def test_render_with_failures(self, sample_packages: list[PackageSpec]) -> None:
        """Test rendering shows failure count."""
        display = MultiPackageProgressDisplay(sample_packages[:1])
        display.register_versions("pkg1", ["3.11", "3.12"])

        display.update(
            "pkg1",
            "3.11",
            TestStatus.FAILED,
            TestResult(version="3.11", success=False, return_code=1),
        )
        display.update(
            "pkg1",
            "3.12",
            TestStatus.PASSED,
            TestResult(version="3.12", success=True, return_code=0),
        )

        table = display.render()
        console = Console(file=StringIO(), force_terminal=True)
        console.print(table)
        output = console.file.getvalue()
        assert "1 failed" in output

    def test_render_running_shows_count(self, sample_packages: list[PackageSpec]) -> None:
        """Test rendering shows running count."""
        display = MultiPackageProgressDisplay(sample_packages[:1])
        display.register_versions("pkg1", ["3.11", "3.12", "3.13"])

        display.update("pkg1", "3.11", TestStatus.RUNNING, None)
        display.update("pkg1", "3.12", TestStatus.RUNNING, None)

        table = display.render()
        console = Console(file=StringIO(), force_terminal=True)
        console.print(table)
        output = console.file.getvalue()
        assert "Running (2)" in output

    def test_thread_safety(self, sample_packages: list[PackageSpec]) -> None:
        """Test that updates and renders are thread-safe."""
        import threading

        display = MultiPackageProgressDisplay(sample_packages)
        display.register_versions("pkg1", ["3.11", "3.12", "3.13"])

        errors: list[Exception] = []

        def update_loop():
            try:
                for i in range(100):
                    display.update("pkg1", "3.11", TestStatus.RUNNING, None)
                    display.update(
                        "pkg1",
                        "3.11",
                        TestStatus.PASSED,
                        TestResult(version="3.11", success=True, return_code=0),
                    )
            except Exception as e:
                errors.append(e)

        def render_loop():
            try:
                for i in range(100):
                    display.render()
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=update_loop),
            threading.Thread(target=render_loop),
            threading.Thread(target=update_loop),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0


class TestDisplayMultiPackageResults:
    """Tests for display_multi_package_results function."""

    def test_display_all_passed(self, tmp_path: Path) -> None:
        """Test displaying results when all pass."""
        pkg1 = PackageSpec(path=tmp_path / "pkg1", name="pkg1")
        pkg2 = PackageSpec(path=tmp_path / "pkg2", name="pkg2")

        result = WorkspaceResult(
            package_results={
                "pkg1": PackageResult(
                    package=pkg1,
                    results={
                        "3.11": TestResult(
                            version="3.11", success=True, return_code=0, duration=1.0
                        ),
                        "3.12": TestResult(
                            version="3.12", success=True, return_code=0, duration=1.5
                        ),
                    },
                ),
                "pkg2": PackageResult(
                    package=pkg2,
                    results={
                        "3.11": TestResult(
                            version="3.11", success=True, return_code=0, duration=2.0
                        ),
                    },
                ),
            }
        )

        # Capture output by replacing the console
        output_file = StringIO()
        test_console = Console(file=output_file, force_terminal=True)

        import testudos.ui

        original_console = testudos.ui.console
        testudos.ui.console = test_console
        try:
            display_multi_package_results(result)
        finally:
            testudos.ui.console = original_console

        output = strip_ansi(output_file.getvalue())
        assert "pkg1" in output
        assert "pkg2" in output
        assert "PASSED" in output
        assert "2/2 packages passed" in output

    def test_display_with_failures(self, tmp_path: Path) -> None:
        """Test displaying results with failures."""
        pkg1 = PackageSpec(path=tmp_path / "pkg1", name="pkg1")
        pkg2 = PackageSpec(path=tmp_path / "pkg2", name="pkg2")

        result = WorkspaceResult(
            package_results={
                "pkg1": PackageResult(
                    package=pkg1,
                    results={
                        "3.11": TestResult(version="3.11", success=True, return_code=0),
                    },
                ),
                "pkg2": PackageResult(
                    package=pkg2,
                    results={
                        "3.11": TestResult(version="3.11", success=False, return_code=1),
                    },
                ),
            }
        )

        output_file = StringIO()
        test_console = Console(file=output_file, force_terminal=True)

        import testudos.ui

        original_console = testudos.ui.console
        testudos.ui.console = test_console
        try:
            display_multi_package_results(result)
        finally:
            testudos.ui.console = original_console

        output = strip_ansi(output_file.getvalue())
        assert "FAILED" in output
        assert "1/2 packages passed" in output
