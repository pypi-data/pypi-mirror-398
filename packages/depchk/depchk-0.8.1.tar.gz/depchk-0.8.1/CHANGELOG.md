# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.8.1] - 2025-12-21

### Fixed

- **Poetry Group Syntax for Dev Dependencies**

  - Fixed bug where dev dependencies using the new Poetry group syntax were not analyzed
  - Now supports both `[tool.poetry.dev-dependencies]` (legacy) and `[tool.poetry.group.dev.dependencies]` (Poetry 1.2+)
  - Affected files: `compatibility.py`, `constraints.py`

## [0.8.0] - 2025-12-21

### Added

- **Standardized JSON Response Envelope**

  - All `--json` output now uses a consistent envelope structure
  - Success responses: `{"status": "success", "data": {...}}`
  - Error responses: `{"status": "error", "error": {"code": "...", "message": "..."}}`
  - This allows for programmatic parsing and error handling
  - Existing data fields moved under `data` key (e.g., `jq '.data.updates'` instead of `jq '.updates'`)

- **Flag Validation for `--json` and `--verbose`**

  - Added safeguard preventing simultaneous use of `--json` and `--verbose`
  - These flags are mutually exclusive (verbose logging is suppressed in JSON mode)
  - Exits immediately with structured JSON error when both flags are used
  - Prevents unnecessary processing time with no benefit

### Removed

- **`--max-packages` CLI Option**

  - Removed package limit feature; all dependencies are now analyzed by default
  - Simplifies CLI and removes arbitrary limitations

- **`cli.show_path` Configuration Option**

  - Removed unused configuration option that had no effect after changing the logging in previous release 
  - The option only affected log message formatting
  - Main output uses Rich console, not logging, so this setting was never useful
  - Also removed `DEPCHK_SHOW_PATH` environment variable

## [0.7.0] - 2025-11-11

### Added

- **Automatic Python Constraint Application**
  - Automatically applies explicit Python version constraints to dependencies where needed
  - Prevents Poetry lock failures due to Python version incompatibilities
  - Detects when recommended package versions require narrower Python ranges than project specifies
  - Converts simple format (selectolax = "^0.4.2") to table format with constraint:
    ```toml
    [tool.poetry.dependencies.selectolax]
    version = "^0.4.2"
    python = ">=3.12.0,<3.14"
    ```
  - **Fallback to Python Classifiers**: When PyPI API returns incomplete requires_python metadata
    (e.g., `>=3.9` missing upper bound `\<3.15`), constructs complete constraint from package classifiers
  - **Smart Constraint Calculation**: Only adds constraints when necessary (avoids redundant constraints)
  - **Enhanced Reporter Output**:
    - New "Constraint" column in update table with checkmark indicator
    - Summary section listing all automatically applied constraints
    - Clear explanation of why constraints were added
  - **JSON Output Support**: Includes python_constraint field in report and python_constraints dict
  - **Unit Tests**: For covering constraint detection, calculation, and edge cases
  - Example: `selectolax ^0.4.2` (supports `Python 3.9-3.13`) automatically gets `python = ">=3.12.0,\<3.14"`
    constraint for projects requiring `^3.12`, preventing lock failures when Poetry tries to select `3.14+`

### Fixed

- **False Positive Updates**

  - Fixed bug where packages already at the latest version were incorrectly reported as having "updates available"
  - Now compares current and recommended versions before adding to updates list
  - Example: PyYAML ^6.0.3 -> ^6.0.3 no longer counted as an update
  - Significantly reduces false positive update counts (e.g., from 16 to 4 actual updates)

- **Python Version Range Compatibility**

  - Fixed critical bug where packages with incompatible Python upper bounds were incorrectly recommended
  - Now validates that packages support the ENTIRE project Python version range, not just partial overlap
  - Example: Package requiring >=3.9,\<3.15 is correctly excluded for project with >=3.12,\<4.0 (incompatible at 3.15+)
  - Prevents Poetry lock failures due to Python version incompatibilities
  - Extended sampling range to Python 3.6-3.20 with more granular patch versions (0, 5, 10, 15, 20) for better coverage

- **Redundant Python Compatibility Check**

  - Removed redundant Python compatibility checking from resolver
  - PyPI client now handles full Python range validation (including upper bounds)
  - Simplifies code and eliminates duplication

### Changed

- Updated existing tests to reflect correct Python version range validation behavior

### Added

- **New Test Coverage for Bug Fixes**
  - Added comprehensive test cases for false positive update detection
  - Added comprehensive test cases for Python version range compatibility

## [0.6.0b0] - 2025-10-19

### Changed

- **Project Rename**: Renamed from `py-dependency-checker` to `depchk`
  - Updated PyPI package name for consistency with command name
  - Shortened name for better CLI
  - Updated all documentation and repository references
- **Python Support**: Confirmed Python 3.12-3.13 support (limited by ChalkBox dependency)
- **CI/CD**: Complete GitHub Actions workflow with linting, formatting, type checking, and testing
  - Tests run on both Python 3.12 and 3.13 in parallel
  - Automated quality checks (ruff, mypy, bandit)

### Fixed

- **Type Annotations**: Fixed mypy type errors for strict type checking
  - Added return type annotations to all methods
  - Improved types for union types
  - Fixed variable shadowing issues

## [0.5.0] - 2025-09-10

### Added

- **Local Path Dependency Support (Monorepo)**
  - Detects local path dependencies in `pyproject.toml`
  - Enforces version constraints from local dependencies
  - Prevents incompatible upgrades in monorepo setups
  - Can be disabled with `--ignore-local-deps` flag
- **Non-Existent Version Validation**
  - Warns users about package versions that don't exist on PyPI
  - Validates both current and recommended versions against PyPI
  - Helpful for catching typos in version specifications
- **CLI Enhancement**: Added `--ignore-local-deps` flag for independent analysis

### Fixed

- **Cache Validation**: Fixed bug where cache fallback recommended incompatible versions
  - Cache now respects Python version constraints when building
  - Improved cache invalidation logic
- **PyPI Client**: Enhanced error handling for network failures and timeouts

### Changed

- **Rich Console Output**: Improved formatting and color-coded risk indicators
- **Progress Spinners**: Added step information to spinner messages

## [0.4.0] - 2025-07-28

### Added

- **Python Version Constraint Enforcement**
  - Respects both lower AND upper bounds in Python version constraints
  - Correctly filters package versions based on project's Python range
  - Supports operators: `^` (caret), `~` (tilde), `>=`, `<`, `==`
  - Handles complex constraints like `>=3.9,<3.13,!=3.11`
  - Converts Poetry constraints to PEP 440 format for PyPI compatibility

### Fixed

- **Poetry to PEP 440 Conversion**
  - Fixed `Invalid specifier: '^3.9.0'` error
  - Poetry caret/tilde operators now properly converted to PEP 440
- **Python Range Constraint Filtering**
  - Correctly handles narrow ranges like `>=3.8.1,<3.9`
  - Prevents recommending packages requiring Python 3.10+ for Python 3.8 projects
  - Tests for overlap between project's Python range and package requirements

### Removed

- **Legacy Cache Format**: Removed support for old `.depchk-cache.json` format
  - Now uses Python-version-specific cache files
  - Automatic migration to new format§Z

### Security

- **Dependency Updates**: Updated aiohttp to 3.10.0 to address CVE-2024-23334
- **Input Validation**: Added sanitization for file paths

## [0.3.0] - 2025-06-20

### Added

- **Configuration System**
  - User config file support: `~/.depchk/config.toml`
  - Environment variable support for all settings
  - Priority: CLI flags > Environment variables > Config file > Defaults
- **CLI Features**
  - `--target-python` flag to override project's Python version
  - `--update-source-file` flag to apply updates directly to the `pyproject.toml`
  - `--json` flag for JSON output
  - `--verbose` flag for detailed logging
  - `--max-packages` to limit analysis scope (default: 40)
  - `--allow-prerelease` to include pre-release versions
- **ChalkBox Console Output**
  - Formatted tables for dependency updates
  - Warning alerts for non-existent versions
  - Summary statistics

### Changed

- **PyPI Client**: Improved concurrent request handling with rate limiting
- **Version Cache**: Increased default TTL from 12 hours to 24 hours
- **Documentation**: Added examples for all CLI flags

### Deprecated

- **Plain Text Output**: Simple text output format deprecated in favor of ChalkBox's console output
  - Will be removed in 1.0.0
  - Use `--json` for machine-readable output

### Fixed

- **Error Messages**: Improved error messages for missing `pyproject.toml` files
- **Cache Cleanup**: Fixed cache files not being properly cleaned up on errors

## [0.2.0] - 2025-05-15

### Added

- **Risk Assessment System**
  - Multi-factor risk scoring (LOW/MEDIUM/HIGH confidence)
  - Python version compatibility analysis
  - Semantic version jump detection (major/minor/patch)
  - Python classifier extraction from PyPI metadata
- **Version Cache System**
  - 24-hour TTL cache for PyPI version lookups
  - Python-version-specific caching (separate caches for different Python versions)
  - Reduces PyPI API calls for faster analysis
  - Cache files: `.depchk-cache.json`, `.depchk-cache-py{version}.json`
- **PyPI Client Enhancements**
  - Metadata extraction from wheel/sdist files
  - Python compatibility filtering
  - Version candidate scoring (prefers wheels with metadata)

### Changed

- **CLI Output**: Improved table formatting with proper alignment
- **Performance**: Reduced PyPI API calls by 60% through caching

### Fixed

- **Version Parsing**: Fixed edge cases in version extraction from filenames
  - Handle versions like "2004d" correctly
  - Support for version formats with + (plus) symbols
- **Async Operations**: Fixed race condition in concurrent PyPI requests

### Security

- **Input Sanitization**: Added validation for package names
- **HTTPS Enforcement**: All PyPI requests now enforce HTTPS with no HTTP fallback

## [0.1.0] - 2025-04-01 (Alpha Release - py-dependency-checker)

### Added

- **Core Features**:
  - Basic dependency analysis for Poetry projects
  - PyPI API client with PEP 691 support (JSON)
  - Async HTTP client for concurrent requests
  - Version extraction from wheels and sdist filenames
  - Package name normalization (PEP 503)
- **Command Line Interface**:
  - Basic CLI with argument parsing
  - Support for analyzing local `pyproject.toml` files
  - Basic console output with dependency update recommendations
- **PyPI API Client**:
  - Fetch package metadata from PyPI Simple API
  - Support for both JSON and HTML responses
  - Basic caching with one hour TTL
  - Concurrent request handling
- **Dependencies**:
  - Built on Rich for terminal output
  - ChalkBox for UI components
  - TOML parser for pyproject.toml parsing
  - httpx and aiohttp for HTTP requests
  - packaging library for version specifier parsing
