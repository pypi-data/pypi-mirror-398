# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-12-24

### Added

- **Core Features**
  - ASCII tree visualization of directory structure
  - Smart default exclusions for common development artifacts
  - Cross-platform support (Windows, macOS, Linux)

- **Output Formats**
  - Tree format (default) with colorized output
  - JSON format for machine-readable output
  - YAML format (requires PyYAML optional dependency)

- **Filtering Options**
  - Depth limiting (`-d, --depth`)
  - Custom exclusion patterns (`-e, --exclude`)
  - Include files by extension (`-I, --include-ext`)
  - Exclude files by extension (`-E, --exclude-ext`)
  - Show hidden files (`-a, --all`)
  - Show only directories (`-q, --quiet`)

- **Display Options**
  - Colorized terminal output with file type awareness
  - Statistics display (`-s, --stats`)
  - Disable colors (`--no-color`)

- **Developer Experience**
  - Installable as `structure` CLI command
  - Python API for library usage
  - Comprehensive test suite
  - CI/CD with GitHub Actions
  - Type hints throughout codebase

### Changed

- Complete rewrite from single-file script to proper Python package
- Modern packaging with `pyproject.toml` and hatchling

### Removed

- Windows-only installation method (now cross-platform via pip)

---

## [Unreleased]

### Planned

- Configuration file support (`.structurerc`)
- Git integration (show file status)
- File size display option
- Glob pattern matching for includes
