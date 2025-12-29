# Python Package Publishing Guide

This guide provides a definitive, step-by-step checklist for preparing, building, and publishing a Python package to PyPI. It follows modern best practices, using `pyproject.toml` for configuration and the `build` and `twine` tools for distribution.

## Phase 1: Pre-Release Preparation

Before you package your code, ensure it's in a stable and well-documented state.

1.  **Finalize Code**: Merge all features and bug fixes for the release into your main development branch (e.g., `develop` or `main`).
2.  **Run Tests**: Ensure the entire test suite passes and that code coverage is at an acceptable level.
    ```bash
    # Example using uv
    uv run pytest
    ```
3.  **Update CHANGELOG**: Add a new entry in `CHANGELOG.md` for the upcoming version. Document all new features, bug fixes, and breaking changes.
4.  **Versioning with git tags (`setuptools_scm`)**: This project uses [`setuptools_scm`](https://github.com/pypa/setuptools_scm) to derive the version from git tags, so you do **not** edit a `version` field in `pyproject.toml` manually. Decide the next version number (for example `0.2.0`) and create a matching git tag later in Phase 6.

    ```toml
    # In pyproject.toml (this project)
    [project]
    name = "zoho-creator-sdk"
    dynamic = ["version"]
    ```

## Phase 2: Package Configuration (`pyproject.toml`)

Your `pyproject.toml` file is the single source of truth for your package's configuration. Below is a complete, well-commented example using `setuptools`.

```toml
# pyproject.toml (simplified excerpt for this project)

[build-system]
requires = ["setuptools>=45", "wheel", "setuptools_scm[toml]>=6.2"]
build-backend = "setuptools.build_meta"

[project]
# --- Core Metadata ---
name = "zoho-creator-sdk"
dynamic = ["version"]
authors = [
  { name = "Carlos Paiva", email = "2202731+carlospaiva@users.noreply.github.com" },
]
description = "A modern Python SDK for the Zoho Creator API"

# --- Long Description (from README) ---
readme = "README.md"
requires-python = ">=3.8.1"

# --- License ---
license = { file = "LICENSE" }

# --- Classifiers (for PyPI filtering) ---
# Full list: https://pypi.org/classifiers/
classifiers = [
    "Programming Language :: Python :: 3",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "Topic :: Software Development :: Libraries :: Python Modules",
]

# --- Dependencies ---
dependencies = [
    "dotenv>=0.9.9",
    "httpx>=0.23.0,<1.0.0",
    "pydantic>=2.0.0,<3.0.0",
    "pydantic[email]>=2.0.0,<3.0.0",
    "python-dateutil>=2.8.0,<3.0.0",
]

# --- Project URLs (for PyPI sidebar) ---
[project.urls]
"Homepage" = "https://github.com/carlospaiva/zoho-creator-sdk"
"Bug Tracker" = "https://github.com/carlospaiva/zoho-creator-sdk/issues"
"Repository" = "https://github.com/carlospaiva/zoho-creator-sdk.git"

# --- Optional Dependencies (e.g., for 'dev' or 'test' extras) ---
[project.optional-dependencies]
dev = [
    "pytest",
    "pytest-cov",
    "black",
    "isort",
    "mypy",
    "flake8",
    "pylint",
    "build",
    "twine",
]
```

## Phase 3: Building the Distribution

This step generates the distributable files that will be uploaded to PyPI.

1.  **Run the build command**:
    ```bash
    make build
    # or, equivalently:
    uv run python -m build
    ```
    This command creates a `dist/` directory containing two files:
    - `my-awesome-package-0.2.0.tar.gz`: A source distribution (sdist).
    - `my_awesome_package-0.2.0-py3-none-any.whl`: A built distribution (wheel). The wheel is a pre-built package that is faster for end-users to install.

## Phase 4: Testing on TestPyPI

Before publishing to the official PyPI, always upload to TestPyPI to ensure everything works as expected.

1.  **Create a TestPyPI Account**: If you don't have one, register at [test.pypi.org/account/register/](https://test.pypi.org/account/register/).
2.  **Create an API Token**: Go to your account settings on TestPyPI and create a new API token. Copy it immediately, as it will not be shown again.
3.  **Upload to TestPyPI**: Use `twine` to upload your distribution files.

    ```bash
    # Install twine if you haven't already
    uv pip install --system twine

    # Upload to TestPyPI
    uv run python -m twine upload --repository testpypi dist/*
    ```

    When prompted, enter `__token__` as the username and your API token (including the `pypi-` prefix) as the password.

4.  **Verify the Installation**: Create a new virtual environment and try installing your package from TestPyPI.
    ```bash
    uv venv test_env
    source test_env/bin/activate
    uv pip install --index-url https://test.pypi.org/simple/ my-awesome-package
    # Test the package
    python -c "import my_awesome_package; print(my_awesome_package.__version__)"
    ```

## Phase 5: Publishing to PyPI

Once you've confirmed the package works correctly on TestPyPI, you can publish it to the official Python Package Index (PyPI).

1.  **Create a PyPI Account**: If you don't have one, register at [pypi.org/account/register/](https://pypi.org/account/register/).
2.  **Create an API Token**: Just like with TestPyPI, create an API token in your PyPI account settings.
3.  **Upload to PyPI**: Use the final `twine` command, run with `uv`, to publish.
    ```bash
    # This is the final step!
    uv run python -m twine upload dist/*
    ```
    Again, use `__token__` as the username and your PyPI API token as the password.

Congratulations! Your package is now live on PyPI.

## Phase 6: Post-Release Actions

Good repository hygiene makes it easier to track releases and manage future development.

1.  **Create a Git Tag**: Tag the release commit with the version number.
    ```bash
    git tag -a v0.2.0 -m "Release version 0.2.0"
    ```
2.  **Push the Tag**: Push the new tag to your remote repository.
    ```bash
    git push origin v0.2.0
    ```
3.  **Create a Release on GitHub**: Go to your repository's "Releases" page and draft a new release. Select the tag you just pushed, and copy your `CHANGELOG.md` notes into the description.
