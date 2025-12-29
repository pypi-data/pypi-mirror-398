# Contributing to the Zoho Creator SDK

First off, thank you for considering contributing to the Zoho Creator SDK! Your help is greatly appreciated.

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## How Can I Contribute?

### Reporting Bugs

- **Ensure the bug was not already reported** by searching on GitHub under [Issues](https://github.com/carlospaiva/zoho-creator-sdk/issues).
- If you're unable to find an open issue addressing the problem, [open a new one](https://github.com/carlospaiva/zoho-creator-sdk/issues/new). Be sure to include a **title and clear description**, as much relevant information as possible, and a **code sample** or an **executable test case** demonstrating the expected behavior that is not occurring.

### Suggesting Enhancements

- Open a new issue to discuss your enhancement.
- Clearly describe the proposed enhancement and its use case.

### Pull Requests

1.  Fork the repo and create your branch from `main`.
2.  If you've added code that should be tested, add tests.
3.  Ensure the test suite passes (`uv run pytest`).
4.  Make sure your code lints (`uv run black .`, `uv run isort .`, `uv run flake8 .`).
5.  Issue that pull request!

## Styleguides

### Git Commit Messages

- Use the present tense ("Add feature" not "Added feature").
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...").
- Limit the first line to 72 characters or less.
- Reference issues and pull requests liberally after the first line.

### Python Styleguide

- All Python code must be formatted with `black` and `isort`.
- Follow PEP 8 conventions.
- All new code should be fully type-hinted.

Thank you for your contribution!
