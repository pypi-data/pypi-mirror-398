# Contributing to EShopBox SDK

Thank you for your interest in contributing!

## Development Setup

1. Clone the repository
2. Install dependencies: `pip install -r requirements-dev.txt`
3. Install pre-commit hooks: `pre-commit install`
4. Run tests: `pytest`

## Pull Request Process

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write/update tests
5. Ensure all tests pass
6. Submit a pull request

## Code Style

We use:
- Black for code formatting
- isort for import sorting
- flake8 for linting
- mypy for type checking

Run `black . && isort . && flake8` before committing.
