.PHONY: help install install-dev test test-cov lint format type-check docs clean build publish

help:
	@echo "Available commands:"
	@echo "  install      Install package"
	@echo "  install-dev  Install package with dev dependencies"
	@echo "  test         Run tests"
	@echo "  test-cov     Run tests with coverage"
	@echo "  lint         Run ruff linter"
	@echo "  format       Format code with black and ruff"
	@echo "  type-check   Run mypy type checker"
	@echo "  docs         Build documentation"
	@echo "  clean        Clean build artifacts"
	@echo "  build        Build distribution packages"
	@echo "  publish      Publish to PyPI (requires credentials)"

install:
	pip install -e .

install-dev:
	pip install -e ".[dev,docs]"

test:
	pytest

test-cov:
	pytest --cov=power_switch_pro --cov-report=html --cov-report=term-missing

lint:
	ruff check power_switch_pro tests
	black --check power_switch_pro tests

format:
	black power_switch_pro tests
	ruff check --fix power_switch_pro tests

type-check:
	mypy power_switch_pro

docs:
	cd docs && make html

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete

build: clean
	python -m build

publish: build
	python -m twine upload dist/*
