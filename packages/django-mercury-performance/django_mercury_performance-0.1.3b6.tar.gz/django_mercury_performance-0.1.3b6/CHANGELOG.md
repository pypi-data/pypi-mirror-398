# Changelog

All notable changes to Django Mercury will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Django 6.0 Support** - Full compatibility with Django 6.0
  - Updated version constraint to `Django>=3.2,<7.0`
  - Added Django 6.0 classifier
  - All 73 tests pass with Django 6.0
  - No code changes required - uses only stable Django APIs

## [0.1.1] - 2025-12-10

### Added
- **NO_COLOR Environment Variable Support** - Disable ANSI colors for CI/CD logs
  - Respects standard `NO_COLOR` environment variable (https://no-color.org/)
  - Also supports `MERCURY_NO_COLOR` for Mercury-specific control
  - Proper truthy value checking (`1`, `true`, `yes`, `on`)
  - Setting to `0` will NOT disable colors

- **End-of-Run Summary Report** - Automatic performance summary after test completion
  - Shows total tests monitored with pass/fail percentages
  - Lists top 5 slowest tests with timing and query counts
  - Aggregates common issues (N+1 patterns, threshold violations)
  - Displays average and median metrics
  - Auto-prints on program exit via `atexit` handler
  - Disable with `MERCURY_NO_SUMMARY=1`
  - Self-documenting with disable instruction in output

- **Django Management Command** - Smart test discovery with AST parsing
  - `python manage.py mercury_test` - Run only tests using `monitor()`
  - AST-based detection finds `from django_mercury import monitor` imports
  - AST-based detection finds `with monitor()` context manager usage
  - Skips irrelevant tests (no manual test labels needed)
  - Automatic summary at end of run
  - Optional usage: Add `django_mercury` to `INSTALLED_APPS` to enable
  - Minimal usage: Just use `monitor()` context manager without INSTALLED_APPS
  - Options: `--keepdb`, `--no-discover`, `--verbosity` (0-3)
  - Filters by app or test file: `mercury_test myapp.tests.test_api`

- **HTML Report Export** - Professional dark mode performance dashboards
  - `python manage.py mercury_test --html` - Generate standalone HTML report
  - Auto-generates filename: `mercury_report_YYYYMMDD_HHMMSS.html`
  - Or specify custom filename: `--html my_report.html`
  - **Professional Dark Mode Design** - GitHub-inspired color palette
    - Dark background (#0d1117) with card layouts (#161b22)
    - No emojis, no gradients - clean and professional
    - Responsive design for desktop and mobile
  - **Interactive Sortable Tables** - Click column headers to sort
    - Sort by test name, response time, query count, or status
    - Automatic type detection (string, number, date)
    - Instant client-side sorting with vanilla JavaScript
  - **Performance Visualizations** with Chart.js
    - Response time bar chart showing test performance
    - Query distribution pie chart
    - Dark theme integration
  - **Comprehensive Dashboard**
    - Test statistics: total, pass/fail %, averages
    - Slowest tests (top 10) with timing and query counts
    - N+1 patterns aggregated across all tests
    - All test results in sortable table format
  - **Modular JavaScript Architecture** (.mjs ES modules)
    - `main.mjs` - Entry point and initialization
    - `common.mjs` - Utility functions (formatting, parsing)
    - `tables.mjs` - Sortable table logic
    - `charts.mjs` - Chart.js integration with dark theme
  - **Data Injection** - `window.MERCURY_DATA` JSON for JavaScript access
  - **XSS Protection** - All user content properly HTML-escaped
  - Fully standalone - inline CSS, Chart.js via CDN
  - Individual test export: `result.to_html('report.html')`
  - Perfect for sharing with team/stakeholders, attaching to PRs, archiving
  - CI/CD friendly - generates even when tests fail

- **Comprehensive Test Suite for HTML Export** - 27 tests ensuring quality
  - Generates actual HTML files for visual inspection
  - Tests validate dark mode design (no emojis, no gradients, correct colors)
  - Verifies sortable table markup and JavaScript integration
  - Checks Chart.js canvas elements and data injection
  - HTML escaping tests prevent XSS vulnerabilities
  - All generated HTML files gitignored (won't clutter repo)
  - Test fixtures with sample data factories
  - BeautifulSoup HTML parsing for structural validation
  - Serve locally: `cd tests/output && python -m http.server 8000`
  - Documentation: `tests/README.md` with usage instructions

### Changed
- **Export Module Restructured** - Modular architecture for maintainability
  - Moved from single `export.py` (1074 lines) to `export/` package
  - `export/single.py` - Individual test HTML export with dark mode
  - `export/summary.py` - Multi-test summary with tables and charts
  - `export/utils.py` - Shared utilities (HTML escaping)
  - `export/__init__.py` - Clean public API
  - Easier to maintain, test, and extend

- **ANSI Colors** - Replaced emojis with professional ANSI color codes
  - Bold cyan headers
  - Green/red for pass/fail metrics
  - Yellow for warnings
  - Red for failures
  - Dim gray for metadata
  - ASCII bullets (``, ``, `"`) instead of emoji

### Fixed
- Environment variable handling now uses proper truthy value parsing
  - `VAR=0` no longer incorrectly disables features
  - Only `1`, `true`, `yes`, `on` are treated as truthy

## [0.1.0] - 2025-12-10

### Breaking Changes
- **Complete Architecture Redesign** - Rebuilt from scratch following SOLID principles
  - Deleted 6,700 lines of legacy code
  - New codebase: ~600 lines of clean, maintainable code
  - No backward compatibility with pre-0.1.0 versions

### Added
- **Simple Context Manager API** - `monitor()` for zero-config performance testing
  - Automatic response time tracking (perf_counter precision)
  - Automatic query count monitoring via Django's CaptureQueriesContext
  - Automatic N+1 query detection with SQL normalization
  - Configurable thresholds (inline, file-level, Django settings, defaults)

- **N+1 Query Detection** - Intelligent SQL pattern matching
  - Normalizes string literals, numbers, UUIDs, IN clauses, booleans
  - Groups identical query patterns
  - Shows sample queries for debugging
  - 3 severity levels: Failure (100%), Warning (80%), Notice (50%)

- **4-Layer Configuration Hierarchy**
  1. Inline overrides: `monitor(response_time_ms=100)`
  2. File-level: `MERCURY_PERFORMANCE_THRESHOLDS` in test module
  3. Django settings: `settings.MERCURY_PERFORMANCE_THRESHOLDS`
  4. Sensible defaults: 200ms response, 20 queries, 10 N+1 threshold

- **Automatic Test Context Capture**
  - Stack inspection to find test method name
  - Clickable file:line locations in reports
  - Works with any test runner (unittest, pytest, Django test)

- **Professional Terminal Output**
  - ANSI color-coded reports
  - Clear pass/fail indicators
  - Detailed failure messages with context
  - `.explain()` method for manual inspection

### Design Philosophy
- **Simple is better than Complex** - Zero config to start, customize when needed
- **80-20 Human-in-the-Loop** - 80% automation, 20% human control
- **SOLID Principles** - Clean architecture, easy to extend
- **Pure Functions** - Testable, no side effects
- **Type Hints** - Full type annotations throughout

### Technical Details
- **Core Modules**:
  - `monitor.py` (400 lines) - Main context manager and reporting
  - `n_plus_one.py` (96 lines) - SQL normalization and pattern detection
  - `config.py` (78 lines) - Threshold resolution with stack search
  - `summary.py` (140 lines) - Global result tracking and summary

- **Test Coverage**: 46 unit tests covering all core functionality
- **Zero Dependencies**: Only requires Django
- **Python 3.10+**: Modern Python features
- **Django 3.2-5.1**: Wide Django version support