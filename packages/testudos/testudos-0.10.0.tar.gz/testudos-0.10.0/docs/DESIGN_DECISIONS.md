# Testudos Design Decisions

This document captures the key design decisions made before implementation.

## Decision Summary

| # | Decision | Choice |
|---|----------|--------|
| 1 | API Caching Strategy | File-based cache with TTL |
| 2 | Offline Mode / Fallback | Cache + hardcoded fallback list |
| 3 | Pre-release Python Versions | Exclude by default, `--include-prerelease` flag |
| 4 | Python Version Requirement | Require Python 3.11+ |
| 5 | Custom Test Runners | Configurable via `test-command` |
| 6 | Error Handling | Fail-fast, require `requires-python` |
| 7 | Parallel Output Handling | Rich live display |
| 8 | Pre/Post Hooks | Not in v1 |
| 9 | CI Integration | Future enhancement |

---

## Detailed Decisions

### 1. API Caching Strategy

**Decision:** File-based cache with TTL

**Implementation:**
- Cache location: `~/.cache/testudos/endoflife.json`
- Default TTL: 24 hours
- Cache includes timestamp for TTL validation
- Respect `XDG_CACHE_HOME` if set

```python
CACHE_DIR = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "testudos"
CACHE_FILE = CACHE_DIR / "endoflife.json"
CACHE_TTL = timedelta(hours=24)
```

---

### 2. Offline Mode / Fallback Behavior

**Decision:** Try cache first, then fall back to bundled list

**Fallback order:**
1. Try to fetch from endoflife.date API
2. If network fails, use cached response (if not expired)
3. If cache expired or missing, use bundled fallback list
4. Warn user when using fallback data

**Implementation:**
- Bundle a `FALLBACK_VERSIONS` list in `versions.py`
- Update this list with each testudos release
- Log a warning when fallback is used

```python
FALLBACK_VERSIONS = ["3.11", "3.12", "3.13"]  # Updated with releases

def get_supported_python_versions() -> list[str]:
    try:
        return fetch_from_api()
    except NetworkError:
        cached = load_from_cache()
        if cached and not cached.expired:
            warn("Using cached version data (network unavailable)")
            return cached.versions
        warn("Using bundled fallback versions (network unavailable)")
        return FALLBACK_VERSIONS
```

---

### 3. Pre-release Python Version Handling

**Decision:** Exclude pre-release versions by default

**Implementation:**
- Filter out versions where `eol` date is in the future AND no stable release exists
- Add `--include-prerelease` / `-r` CLI flag to include them
- Add `include-prerelease = true` config option in `[tool.testudos]`

**Rationale:** Pre-release Python versions (e.g., 3.14 alpha) may cause test failures that aren't actionable for most users.

---

### 4. Python Version Requirement

**Decision:** Require Python 3.11+

**Implementation:**
```toml
[project]
requires-python = ">=3.11"
```

**Rationale:**
- `tomllib` is in stdlib from 3.11+
- Simplifies dependencies (no `tomli` fallback needed)
- Python 3.10 reaches end of security support in October 2026
- Modern Python features available (better typing, etc.)

---

### 5. Custom Test Runner Support

**Decision:** Configurable via `test-command` setting

**Implementation:**
- Already designed in `[tool.testudos]` config
- No validation of test command (user's responsibility)
- Support arbitrary commands, not just pytest

```toml
[tool.testudos]
test-command = "python -m unittest discover"
test-args = ["-v"]
```

---

### 6. Error Handling Strategy

**Decision:** Fail-fast, require `requires-python`

| Scenario | Behavior |
|----------|----------|
| Missing `pyproject.toml` | Error: "No pyproject.toml found at {path}" |
| Missing `requires-python` | Error: "requires-python not specified in pyproject.toml" |
| Python version unavailable | Error: "Python {version} not available. Install with: uv python install {version}" |
| Test failure on one version | **Stop immediately**, report failure |
| `uv` not installed | Error: "uv not found. Install from https://docs.astral.sh/uv/" |

**Rationale:**
- Fail-fast prevents wasting time on subsequent versions when one fails
- Requiring `requires-python` ensures intentional version specification
- Clear error messages help users fix issues quickly

**Note:** Consider adding `--continue-on-failure` flag in future if users request it.

---

### 7. Parallel Execution Output Handling

**Decision:** Rich live display

**Implementation:**
- Use `rich.live.Live` with a dynamically updating table
- Show real-time progress for each Python version
- Display spinner while tests are running
- Update to checkmark/cross when complete

```
┌─────────────────────────────────────┐
│ Python Version │ Status            │
├─────────────────────────────────────┤
│ 3.11           │ ✓ Passed (2.3s)   │
│ 3.12           │ ⠋ Running...      │
│ 3.13           │ ⠋ Running...      │
│ 3.14           │ ○ Pending         │
└─────────────────────────────────────┘
```

**Rationale:** Provides best user experience with real-time feedback while maintaining clean output.

---

### 8. Pre/Post Hooks

**Decision:** Not in v1

**Rationale:**
- Keep initial implementation simple
- Users can wrap testudos in their own scripts if needed
- Reconsider for v2 based on user feedback

---

### 9. CI Integration

**Decision:** Future enhancement

**Rationale:**
- Focus on core functionality first
- GitHub Actions generation can be added later

**Future consideration:**
```bash
testudos ci --github-actions  # Generate .github/workflows/test.yml
```

---

## Updated Dependencies

Based on these decisions:

```toml
[project]
name = "testudos"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "typer>=0.9.0",
    "rich>=13.0.0",
    "httpx>=0.25.0",
    "packaging>=23.0",
]
```

Note: `tomllib` is stdlib in Python 3.11+, no external dependency needed.

---

## Updated File Structure

```
testudos/
├── pyproject.toml
├── README.md
├── src/
│   └── testudos/
│       ├── __init__.py
│       ├── cli.py
│       ├── config.py
│       ├── versions.py
│       ├── executor.py
│       ├── runner.py
│       ├── coverage.py
│       └── ui.py
├── tests/
│   └── ...
└── docs/
    ├── ARCHITECTURE.md
    ├── DESIGN_DECISIONS.md
    └── IMPLEMENTATION_ROADMAP.md
```
