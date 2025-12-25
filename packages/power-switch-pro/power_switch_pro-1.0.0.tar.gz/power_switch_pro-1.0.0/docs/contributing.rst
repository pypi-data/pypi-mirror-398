Contributing
============

We welcome contributions to the Power Switch Pro library! This document provides guidelines for contributing.

Development Setup
-----------------

1. Fork the repository on GitHub
2. Clone your fork locally:

.. code-block:: bash

    git clone https://github.com/yourusername/power_switch_pro.git
    cd power_switch_pro

3. Install development dependencies:

.. code-block:: bash

    pip install -e ".[dev,docs]"

4. Create a branch for your changes:

.. code-block:: bash

    git checkout -b feature/my-new-feature

Code Style
----------

We use several tools to maintain code quality:

* **Black** for code formatting (line length: 88)
* **Ruff** for linting
* **mypy** for type checking

Run these before committing:

.. code-block:: bash

    make format      # Format code
    make lint        # Check style
    make type-check  # Type checking

Testing
-------

All new code should include tests. We aim for at least 80% code coverage.

Run tests:

.. code-block:: bash

    make test        # Run tests
    make test-cov    # Run tests with coverage report

Writing Tests
~~~~~~~~~~~~~

Tests should be placed in the ``tests/`` directory, mirroring the package structure:

.. code-block:: python

    # tests/test_outlets.py
    import responses
    from power_switch_pro import PowerSwitchPro

    @responses.activate
    def test_outlet_on():
        """Test turning on an outlet."""
        responses.add(
            responses.PUT,
            "http://192.168.0.100/restapi/relay/outlets/0/state/",
            json=True,
            status=200
        )
        
        switch = PowerSwitchPro("192.168.0.100", "admin", "1234")
        result = switch.outlets[0].on()
        
        assert result is True

Documentation
-------------

Documentation is built using Sphinx with the Read the Docs theme.

Build documentation locally:

.. code-block:: bash

    make docs
    # Open docs/_build/html/index.html

Use Google-style docstrings for all public APIs.

Pull Request Process
--------------------

1. Update tests for any changed functionality
2. Update documentation if needed
3. Ensure all tests pass and code is formatted
4. Update CHANGELOG.md with your changes
5. Submit a pull request with a clear description

Commit Messages
---------------

Follow conventional commit format:

.. code-block:: text

    type(scope): description

    [optional body]

    Co-Authored-By: Warp <agent@warp.dev>

Types:

* ``feat``: New feature
* ``fix``: Bug fix
* ``docs``: Documentation changes
* ``style``: Code style changes (formatting, etc.)
* ``refactor``: Code refactoring
* ``test``: Test changes
* ``chore``: Build process or auxiliary tool changes

Reporting Bugs
--------------

When reporting bugs, please include:

* Python version
* Library version
* Device firmware version
* Minimal code to reproduce the issue
* Full error traceback

Feature Requests
----------------

Feature requests are welcome! Please:

* Check if the feature already exists or is planned
* Describe the use case clearly
* Explain why it would be useful to others

Code of Conduct
---------------

* Be respectful and inclusive
* Welcome newcomers
* Focus on what is best for the community
* Show empathy towards other community members

License
-------

By contributing, you agree that your contributions will be licensed under the BSD-3-Clause License.
