# Multi-Package Parallelism Design

This document describes the design for extending testudos to support testing multiple packages in parallel.

## Goals

1. **Preserve existing behavior**: Single-package testing must work exactly as before
2. **Add horizontal parallelism**: Test multiple packages concurrently
3. **Output isolation**: Each package's output must remain separate and clean
4. **Flexible control**: Independent control over package-level and version-level parallelism

## Architecture Overview

### Parallelism Model: Hierarchical

The design uses a **hierarchical parallelism model**:

```
                    MultiPackageRunner
                           │
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
      TestRunner      TestRunner      TestRunner
       (pkg1)          (pkg2)          (pkg3)
           │               │               │
       ┌───┼───┐       ┌───┼───┐       ┌───┼───┐
       ▼   ▼   ▼       ▼   ▼   ▼       ▼   ▼   ▼
     3.11 3.12 3.13  3.11 3.12 3.13  3.11 3.12 3.13
```

- Packages run in parallel (controlled by `--package-jobs`)
- Within each package, versions run in parallel (controlled by `--jobs`)
- Each package is an independent unit with its own `TestRunner`

### Key Design Decisions

1. **Composition over modification**: `MultiPackageRunner` composes multiple `TestRunner` instances
2. **Separate display modes**: `MultiPackageProgressDisplay` is separate from `ParallelProgressDisplay`
3. **Automatic routing**: CLI detects single vs multi-package and routes accordingly
4. **Callback key extension**: Multi-package callbacks include `(package_name, version)` tuple

## New Components

### 1. `workspace.py` - Package Discovery and Data Structures

```python
@dataclass
class PackageSpec:
    """Specification for a single package."""
    path: Path           # Absolute path to package directory
    name: str            # Display name (from pyproject.toml or directory)

@dataclass
class PackageResult:
    """Results for a single package across all versions."""
    package: PackageSpec
    results: dict[str, TestResult]  # version -> result

@dataclass
class WorkspaceResult:
    """Aggregated results for all packages."""
    package_results: dict[str, PackageResult]  # package_name -> results

@dataclass
class WorkspaceConfig:
    """Configuration for multi-package testing."""
    packages: list[PackageSpec]
    parallel_packages: bool = True
    max_package_workers: int | None = None
```

### 2. `multi_runner.py` - Multi-Package Orchestration

```python
class MultiPackageRunner:
    """Orchestrates test execution across multiple packages."""

    async def run_all_async(
        self,
        options: RunOptions,
        on_package_status_change: Callable[
            [str, str, TestStatus, TestResult | None], None
        ] | None = None,
    ) -> WorkspaceResult:
        """Run tests for all packages."""
```

Key features:
- Uses asyncio semaphore to limit concurrent packages
- Each package gets its own `TestRunner` instance
- Status callbacks include package name prefix

### 3. `MultiPackageProgressDisplay` in `ui.py`

Two display modes:
- **Collapsed** (default): One row per package with aggregate status
- **Expanded**: Package sections with version rows

```
┌─────────────────────────────────────────────────────────┐
│                Multi-Package Test Progress              │
├─────────────────┬────────────────┬──────────────────────┤
│ Package         │ Progress       │ Status               │
├─────────────────┼────────────────┼──────────────────────┤
│ mylib-core      │ 3/3 versions   │ ✓ All 3 passed       │
│ mylib-utils     │ 2/3 versions   │ ⠋ Running (1)...     │
│ mylib-cli       │ 0/3 versions   │ ○ Pending            │
└─────────────────┴────────────────┴──────────────────────┘
```

### 4. CLI Extensions in `cli.py`

New options:
- `--package PATH` / `-k PATH`: Additional package to test (repeatable)
- `--discover` / `-d`: Auto-discover packages under path (finds all dirs with pyproject.toml)
- `--parallel-packages / --no-parallel-packages`: Control package parallelism
- `--package-jobs N` / `-J N`: Max concurrent packages

## Data Flow

### Single Package (Unchanged)

```
CLI → TestRunner → executor.run_tests_parallel_async()
                         ↓
              ParallelProgressDisplay
```

### Multiple Packages (New)

```
CLI → MultiPackageRunner
              ↓
    ┌─────────┼─────────┐
    ↓         ↓         ↓
TestRunner TestRunner TestRunner
    ↓         ↓         ↓
    └─────────┼─────────┘
              ↓
   MultiPackageProgressDisplay
```

## CLI Usage Examples

```bash
# Single package (existing behavior, unchanged)
testudos run
testudos run ./my-package --parallel

# Multiple packages
testudos run --package ./pkg1 --package ./pkg2
testudos run ./pkg1 ./pkg2 ./pkg3

# Control parallelism
testudos run ./pkg1 ./pkg2 --parallel-packages --package-jobs 2
testudos run ./pkg1 ./pkg2 --parallel-packages --parallel --jobs 4

# Sequential packages, parallel versions within
testudos run ./pkg1 ./pkg2 --no-parallel-packages --parallel
```

## Parallelism Control Matrix

| Flag | Scope | Effect |
|------|-------|--------|
| `--parallel` (`-P`) | Versions | Python versions run in parallel within each package |
| `--jobs N` (`-j`) | Versions | Max concurrent version tests per package |
| `--parallel-packages` | Packages | Packages run in parallel (default when >1) |
| `--package-jobs N` (`-J`) | Packages | Max concurrent packages |

## Output Isolation

1. **During execution**: Only show progress table (no stdout from tests)
2. **After completion**:
   - Show summary table for all packages
   - With `--verbose`: Show failed outputs sequentially, one package at a time

Each package's test output is captured and stored separately in `PackageResult`.

## Coverage Handling

Coverage remains per-package:
- Each package has its own `.testudos/coverage/` directory
- Coverage combine/report operates per-package
- Future: Optional cross-package coverage aggregation

## File Changes Summary

| File | Change Type | Description |
|------|-------------|-------------|
| `src/testudos/workspace.py` | New | Package discovery and data structures |
| `src/testudos/multi_runner.py` | New | Multi-package orchestration |
| `src/testudos/ui.py` | Modified | Add `MultiPackageProgressDisplay` |
| `src/testudos/cli.py` | Modified | Add multi-package CLI options and routing |

## Implementation Order

1. Create `workspace.py` with data structures
2. Create `multi_runner.py` with `MultiPackageRunner`
3. Add `MultiPackageProgressDisplay` to `ui.py`
4. Update `cli.py` with new options and routing
5. Add tests for new functionality
