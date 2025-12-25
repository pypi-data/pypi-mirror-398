# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.0] - 2025-12-22

### Changed
- Automatic resolution of $ref references in device.info property
- Returns actual device values (serial, version, hostname, hardware_id) instead of API references

## [1.0.0] - 2025-12-22

### Fixed
- Increased HTTP header limit from 100 to 200 to handle Power Switch Pro devices that return excessive headers in config endpoint responses
- Resolves "got more than 100 headers" error when accessing device.info property
- Added graceful error handling for devices without power metering hardware

### Changed
- Project status upgraded to Production/Stable
- Library is now considered production-ready
- Added disclaimer that this is an unofficial library
- Added documentation note that power metering APIs are untested (no hardware available)

## [0.1.0] - 2025-12-22

### Added
- Initial release of Power Switch Pro Python library
- Full support for DLI REST-style API (version 20221009T204818Z)
- PowerSwitchPro main client class with HTTP Digest authentication
- Outlet management with OutletManager and Outlet classes
- Support for individual and bulk outlet operations
- Matrix URI support for filtering and bulk operations
- User authentication and management via AuthManager
- Device configuration management via ConfigManager
- Power monitoring with MeterManager (voltage, current, power, energy)
- AutoPing configuration via AutoPingManager
- Script execution support via ScriptManager
- Comprehensive exception hierarchy
- CSRF protection for state-modifying operations
- HTTPS support with optional SSL verification
- Complete API documentation with Sphinx
- Extensive test suite with pytest
- Code quality tools: Black, Ruff, mypy
- GitHub Actions CI/CD workflows
- ReadTheDocs integration
- BSD-3-Clause license

### Features
- Pythonic API with property access and array indexing
- Support for Python 3.7+
- Type hints throughout the codebase
- Detailed docstrings in Google style
- Example scripts and use cases
- Comprehensive error handling
- Automatic request retry on connection errors
- Session-based HTTP communication for efficiency

### Documentation
- Quick start guide
- Complete API reference
- Device information and specifications
- Practical examples for common use cases
- Contributing guidelines
- Troubleshooting guide

[Unreleased]: https://github.com/bryankemp/power_switch_pro/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/bryankemp/power_switch_pro/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/bryankemp/power_switch_pro/compare/v0.1.0...v1.0.0
[0.1.0]: https://github.com/bryankemp/power_switch_pro/releases/tag/v0.1.0
