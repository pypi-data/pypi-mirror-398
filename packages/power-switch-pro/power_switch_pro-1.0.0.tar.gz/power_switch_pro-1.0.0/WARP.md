# Power Switch Pro - Warp AI Development Rules

This file contains project-specific rules and guidelines for AI-assisted development with Warp.

## Project Overview

Power Switch Pro is a Python library for controlling Digital Loggers Power Switch Pro devices via their REST API. The library provides a clean, Pythonic interface to all device features including outlet control, power monitoring, user management, and AutoPing functionality.

## Code Style and Standards

### Python Style
- Use Black for code formatting (line length: 88)
- Follow PEP 8 guidelines
- Use Ruff for linting with the configuration in pyproject.toml
- Run type checking with mypy
- Maintain Python 3.7+ compatibility

### Formatting Commands
```bash
make format     # Format code with Black and Ruff
make lint       # Check code style
make type-check # Run mypy type checker
```

## Testing Requirements

### Test Coverage
- All new code must have accompanying tests
- Maintain minimum 80% code coverage
- Use pytest for all tests
- Use responses library for mocking HTTP requests
- Place tests in `tests/` directory mirroring the package structure

### Running Tests
```bash
make test       # Run tests
make test-cov   # Run tests with coverage report
```

### Test Naming Convention
- Test files: `test_*.py`
- Test classes: `Test*`
- Test functions: `test_*`

## Code Organization

### Module Structure
```
power_switch_pro/
├── __init__.py          # Package initialization and exports
├── client.py            # Main PowerSwitchPro client
├── exceptions.py        # Custom exceptions
├── outlets.py           # Outlet management
├── auth.py              # User authentication management
├── config.py            # Device configuration
├── meters.py            # Power meter management
├── autoping.py          # AutoPing functionality
└── script.py            # Script execution
```

### API Design Principles
1. **Pythonic Interface**: Use properties, context managers, and familiar Python idioms
2. **Manager Pattern**: Each feature area has its own manager class (OutletManager, AuthManager, etc.)
3. **Array Indexing**: Support `switch.outlets[0]` for intuitive outlet access
4. **Consistent Returns**: Boolean for success/failure, objects for data retrieval
5. **Error Handling**: Raise specific exceptions from `exceptions.py`

## Documentation

### Docstring Style
Use Google-style docstrings for all public APIs:

```python
def function_name(param1: str, param2: int) -> bool:
    """
    Brief description.

    Longer description if needed.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ExceptionType: When this exception is raised

    Examples:
        >>> function_name("test", 42)
        True
    """
```

### Documentation Build
```bash
make docs  # Build Sphinx documentation
```

## API Guidelines

### HTTP Communication
- All HTTP requests go through the `PowerSwitchPro` client methods
- Use HTTP Digest Authentication (configured in client)
- Always include X-CSRF header for state-modifying operations (POST, PUT, PATCH, DELETE)
- Handle standard HTTP status codes appropriately:
  - 200/204: Success
  - 201: Resource created
  - 207: Multiple responses (bulk operations)
  - 401: Authentication error
  - 404: Resource not found
  - 409: Conflict

### REST API Paths
- All paths must end with `/`
- Use matrix URIs for filtering: `outlets/all;locked=true/`
- Use `=` selector for specific items: `outlets/=0,1,4/`

### Data Formats
- Accept and return JSON by default
- Use `application/x-www-form-urlencoded` for simple form data
- Boolean values in requests should be lowercase strings: "true" / "false"

## Error Handling

### Exception Hierarchy
```
PowerSwitchError (base)
├── AuthenticationError
├── ConnectionError
├── APIError
│   ├── ResourceNotFoundError
│   └── ConflictError
└── ValidationError
```

### Error Handling Pattern
```python
try:
    result = switch.outlets[0].on()
except AuthenticationError:
    # Handle auth failure
    pass
except ConnectionError:
    # Handle connection issues
    pass
except APIError as e:
    # Handle API errors with e.status_code and e.response
    pass
```

## Git Workflow

### Branch Strategy
- `main`: Stable releases only
- `develop`: Active development
- Feature branches: `feature/description`
- Bug fixes: `fix/description`

### Commit Messages
Follow conventional commits:
```
type(scope): description

[optional body]

Co-Authored-By: Warp <agent@warp.dev>
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

### Pre-commit Checklist
1. Run `make format` to format code
2. Run `make lint` to check style
3. Run `make test-cov` to verify tests pass
4. Run `make type-check` for type safety
5. Update documentation if needed

## Release Process

### Version Numbering
Follow Semantic Versioning (SemVer): MAJOR.MINOR.PATCH

### Release Steps
1. Update version in `pyproject.toml` and `setup.py`
2. Update CHANGELOG.md
3. Run full test suite: `make test-cov`
4. Build package: `make build`
5. Create GitHub release (triggers automatic PyPI publish)

## Dependencies

### Adding Dependencies
- Add to `dependencies` in `pyproject.toml`
- Keep dependencies minimal
- Pin major versions only: `requests>=2.25.0`

### Dev Dependencies
Development dependencies go in `[project.optional-dependencies]` under `dev` or `docs`.

## DLI REST API Specifics

### Important API Characteristics
- Digest authentication required (no basic auth by default)
- CSRF protection via X-CSRF or X-Requested-With headers
- Matrix URI support for bulk operations
- Response depth limiting with Range: dli-depth=N header
- 207 Multi-Status responses for bulk operations

### Common API Patterns
```python
# Single outlet control
PUT /restapi/relay/outlets/0/state/ with value=true

# Bulk operations (matrix URI)
PUT /restapi/relay/outlets/all;locked=false/state/ with value=false

# Multiple specific outlets
GET /restapi/relay/outlets/=0,1,4/state/

# Filtering
GET /restapi/relay/outlets/all;name=server/state/
```

## Author Information

- **Name**: Bryan Kemp
- **Email**: bryan@kempville.com
- **License**: BSD-3-Clause

Always include proper attribution in git commits and documentation.

## Additional Resources

- [DLI REST API Documentation](api/restapi.pdf)
- [Project GitHub](https://github.com/bryankemp/power_switch_pro)
- [ReadTheDocs](https://power-switch-pro.readthedocs.io)
- [PyPI Package](https://pypi.org/project/power-switch-pro/)
