# Changelog

All notable changes to agentic-dev-boilerplate will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.2] - 2025-12-27

### Fixed
- Corrected Jinja2 template rendering issues causing YAML syntax errors in generated workflows
- Fixed test mocking issues for proper CI/CD validation
- Improved error handling in temporary file management
- Resolved directory pruning logic in TmpManager

### Changed
- Updated GitHub Actions to latest versions (checkout@v6, setup-python@v6, etc.)
- Enhanced test coverage and reliability

## [1.1.1] - 2025-12-27

### Added
- Comprehensive test suite with `test-package.sh` script
- Docker container for isolated testing and validation
- UV lock file for reproducible dependency management

### Changed
- Pinned all dependencies to specific versions for reproducibility
- Updated to use UV for all Python package management
- Improved package structure with templates included in wheel
- Enhanced CI/CD with comprehensive testing

### Fixed
- Template path resolution for packaged installation
- Package build configuration to include all necessary files

### Security
- N/A

### Added
- Initial project setup with agentic development boilerplate
- Automated PR creation, validation, and enrichment
- Task tracking and status management
- Commit signing enforcement
- CI/CD automation with phased testing

### Changed
- N/A

### Deprecated
- N/A

### Removed
- N/A

### Fixed
- N/A

### Security
- N/A
