# Zoho Creator SDK - Makefile Usage Guide

This document explains how to use the Makefile for common development tasks in the Zoho Creator SDK project.

## Prerequisites

Before using the Makefile, ensure you have:

- Python 3.8.1+ (matches the `requires-python` setting in `pyproject.toml`)
- `uv` package manager installed (`pip install uv` or follow installation instructions at https://github.com/astral-sh/uv)

## Available Targets

### Installation

- `make install` - Install the package in development mode using uv
- `make install-dev` - Install development dependencies using uv
- `make install-test` - Install test dependencies only using uv

### Testing

- `make test` - Run all tests
- `make test-unit` - Run unit tests only
- `make test-integration` - Run integration tests only
- `make test-e2e` - Run end-to-end tests only
- `make test-quick` - Run quick tests (skip slow tests)

### Coverage

- `make test-coverage` - Run tests with coverage report (requires 95%+ coverage)
- `make test-coverage-html` - Run tests with HTML coverage report
- `make test-coverage-xml` - Run tests with XML coverage report
- `make verify-coverage` - Verify 95%+ test coverage
- `make html-coverage` - Generate HTML coverage report

### Code Quality

- `make format` - Format code with black and isort using uv
- `make lint` - Run all linters using uv and scripts (includes proper mypy configuration)
- `make lint-check` - Check code formatting and linting without making changes
- `make check` - Run all code quality checks (format, lint, test)

### Development Workflows

- `make dev` - Run development workflow (format, lint, test)
- `make pre-commit` - Run pre-commit checks (format, lint-check, test-quick)

### Continuous Integration

- `make ci` - Run continuous integration checks (sync dev deps, lint, test with coverage, verify coverage)

### Building and Publishing

- `make build` - Build distribution packages
- `make publish-test` - Publish to TestPyPI (includes build step)
- `make publish` - Publish to PyPI

### Documentation

- `make docs` - Generate documentation (placeholder)
- `make docs-serve` - Serve documentation locally (placeholder)

### Cleanup

- `make clean` - Clean build artifacts and cache files
- `make clean-test` - Clean test artifacts only

### Help

- `make help` - Display available targets with descriptions

## Common Workflows

### Setting up a new development environment

```bash
make install-dev
```

### Before committing code

```bash
make pre-commit
```

### Running the full test suite with coverage

```bash
make test-coverage
```

### Running all quality checks (formatting, linting, testing)

```bash
make check
```

### For CI/CD pipeline

```bash
make ci
```

## Notes

- All commands use `uv` as the package manager as specified in the project documentation
- The lint target uses the project's custom linting script which includes proper mypy configuration with MYPYPATH
- Coverage requirements are enforced at 95%+ across all targets that include coverage
- The Makefile is designed to work consistently with the project's development practices as documented in AGENTS.md
