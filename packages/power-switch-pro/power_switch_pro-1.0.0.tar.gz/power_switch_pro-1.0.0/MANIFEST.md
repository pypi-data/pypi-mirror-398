# Power Switch Pro Library - Project Manifest

## Project Overview

A professional-grade Python library for controlling Digital Loggers Power Switch Pro devices via their REST API.

**Author**: Bryan Kemp (bryan@kempville.com)  
**License**: BSD-3-Clause  
**API Version**: 20221009T204818Z (October 9, 2022)

## Project Structure

```
power_switch_pro/
├── LICENSE                      # BSD-3-Clause license
├── README.md                    # Main project README
├── CHANGELOG.md                 # Version history
├── WARP.md                      # Warp AI development rules
├── MANIFEST.md                  # This file
├── setup.py                     # setuptools configuration
├── pyproject.toml               # Modern Python packaging config
├── Makefile                     # Development commands
├── .gitignore                   # Git ignore rules
├── .readthedocs.yaml            # ReadTheDocs configuration
├──  .github/
│   └── workflows/
│       ├── ci.yml               # CI/CD pipeline
│       └── publish.yml          # PyPI publishing
├── power_switch_pro/            # Main package
│   ├── __init__.py              # Package initialization
│   ├── client.py                # Main PowerSwitchPro client
│   ├── exceptions.py            # Custom exceptions
│   ├── outlets.py               # Outlet management
│   ├── auth.py                  # User authentication
│   ├── config.py                # Device configuration
│   ├── meters.py                # Power monitoring
│   ├── autoping.py              # AutoPing management
│   └── script.py                # Script execution
├── tests/                       # Test suite
│   ├── __init__.py
│   ├── conftest.py              # Pytest fixtures
│   ├── test_client.py           # Client tests
│   ├── test_outlets.py          # Outlet tests
│   └── (additional test files)
├── docs/                        # Sphinx documentation
│   ├── conf.py                  # Sphinx configuration
│   ├── Makefile                 # Doc build commands
│   ├── index.rst                # Main documentation page
│   ├── installation.rst         # Installation guide
│   ├── device.rst               # Device information
│   ├── quickstart.rst           # Quick start guide
│   ├── api.rst                  # API reference
│   ├── examples.rst             # Code examples
│   └── contributing.rst         # Contribution guidelines
└── api/
    └── restapi.pdf              # DLI API documentation
```

## Features Implemented

### Core Functionality
- [x] HTTP Digest authentication
- [x] HTTPS support with SSL verification
- [x] CSRF protection for state-modifying requests
- [x] Comprehensive error handling
- [x] Session-based HTTP communication
- [x] Matrix URI support for bulk operations

### API Managers
- [x] **OutletManager**: Control individual and multiple outlets
- [x] **AuthManager**: User management and authentication
- [x] **ConfigManager**: Device configuration
- [x] **MeterManager**: Power monitoring (voltage, current, power, energy)
- [x] **AutoPingManager**: AutoPing configuration
- [x] **ScriptManager**: Script execution

### Python Features
- [x] Type hints throughout
- [x] Property-based access (e.g., `outlet.state`, `outlet.name`)
- [x] Array indexing (e.g., `switch.outlets[0]`)
- [x] Google-style docstrings
- [x] Python 3.7+ compatibility

## Development Tools

### Code Quality
- **Black**: Code formatting (line-length: 88)
- **Ruff**: Fast Python linter
- **mypy**: Static type checking
- **pytest**: Testing framework
- **responses**: HTTP request mocking

### CI/CD
- **GitHub Actions**: Automated testing and linting
- **Multiple OS**: Ubuntu, macOS, Windows
- **Multiple Python**: 3.7, 3.8, 3.9, 3.10, 3.11, 3.12
- **Coverage**: Codecov integration

### Documentation
- **Sphinx**: Documentation generator
- **ReadTheDocs**: Hosted documentation
- **sphinx-rtd-theme**: Read the Docs theme
- **sphinx-autodoc-typehints**: Type hint support

## Quick Commands

```bash
# Development setup
make install-dev

# Testing
make test           # Run tests
make test-cov       # Run with coverage

# Code quality
make format         # Format code
make lint           # Check style
make type-check     # Type checking

# Documentation
make docs           # Build docs

# Build and publish
make build          # Build distribution
make publish        # Publish to PyPI
```

## Testing Strategy

### Test Coverage Goals
- Minimum 80% code coverage
- All public APIs tested
- Error handling tested
- Edge cases covered

### Test Organization
- Mirror package structure in `tests/`
- Use pytest fixtures for common setup
- Mock HTTP requests with responses library
- Test both success and failure paths

## Documentation Structure

### User Documentation
1. **Installation**: Setup instructions
2. **Device Info**: Hardware and firmware details (API version noted)
3. **Quick Start**: Getting started guide
4. **API Reference**: Complete API documentation
5. **Examples**: Practical code examples
6. **Contributing**: Development guidelines

### Key Documentation Features
- Firmware version prominently displayed (20221009T204818Z)
- Device specifications and models
- Security best practices
- Troubleshooting guide
- Code examples for common use cases

## Release Process

1. Update version in `pyproject.toml` and `setup.py`
2. Update `CHANGELOG.md` with changes
3. Run full test suite: `make test-cov`
4. Check code quality: `make lint && make type-check`
5. Build documentation: `make docs`
6. Build package: `make build`
7. Create GitHub release (triggers automatic PyPI publish)
8. Tag release with version number

## Supported Devices

- DLI Web Power Switch Pro (LPC)
- Pro Switch
- Ethernet Power Controller III and later
- Firmware 1.7.0+ (REST API support)

## Dependencies

### Runtime
- `requests>=2.25.0`: HTTP client library

### Development
- `pytest>=7.0.0`: Testing framework
- `pytest-cov>=3.0.0`: Coverage plugin
- `pytest-mock>=3.10.0`: Mocking support
- `responses>=0.22.0`: HTTP mocking
- `black>=22.0.0`: Code formatter
- `ruff>=0.0.200`: Linter
- `mypy>=0.990`: Type checker
- `types-requests>=2.28.0`: Type stubs

### Documentation
- `sphinx>=5.0.0`: Documentation generator
- `sphinx-rtd-theme>=1.0.0`: Theme
- `sphinx-autodoc-typehints>=1.19.0`: Type hint support

## Future Enhancements

Potential areas for future development:
- Network configuration management
- Firmware update automation
- Event streaming/webhooks
- CLI tool for command-line usage
- Async/await support for concurrent operations
- Additional power monitoring features
- Enhanced logging and debugging

## Contributing

See `CONTRIBUTING.md` and `WARP.md` for detailed contribution guidelines.

## Links

- **GitHub**: https://github.com/bryankemp/power_switch_pro
- **PyPI**: https://pypi.org/project/power_switch_pro/
- **Documentation**: https://power-switch-pro.readthedocs.io
- **Issues**: https://github.com/bryankemp/power_switch_pro/issues
- **Digital Loggers**: https://www.digital-loggers.com/

## License

BSD 3-Clause License - See LICENSE file for details.
