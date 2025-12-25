# Contributing

Thank you for your interest in contributing to langchain-maritaca!

## Environment Setup

### 1. Clone the repository

```bash
git clone https://github.com/anderson-ufrj/langchain-maritaca.git
cd langchain-maritaca
```

### 2. Install development dependencies

```bash
pip install -e ".[dev]"
```

Or with uv:

```bash
uv pip install -e ".[dev]"
```

### 3. Set up pre-commit

```bash
pre-commit install
```

## Running Tests

### Unit Tests

```bash
pytest tests/unit_tests/ -v
```

### Integration Tests

Requires `MARITACA_API_KEY`:

```bash
export MARITACA_API_KEY="your-key"
pytest tests/integration_tests/ -v
```

### All Tests

```bash
pytest
```

### With Coverage

```bash
pytest --cov=langchain_maritaca --cov-report=html
```

## Linting and Formatting

### Check

```bash
ruff check langchain_maritaca tests
ruff format --check langchain_maritaca tests
```

### Fix

```bash
ruff check --fix langchain_maritaca tests
ruff format langchain_maritaca tests
```

### Type Checking

```bash
mypy langchain_maritaca
```

## Project Structure

```
langchain-maritaca/
├── langchain_maritaca/
│   ├── __init__.py         # Public exports
│   ├── chat_models.py      # Main implementation
│   └── version.py          # Package version
├── tests/
│   ├── unit_tests/         # Tests without real API
│   └── integration_tests/  # Tests with real API
├── docs/                   # MkDocs documentation
├── pyproject.toml          # Project configuration
└── README.md
```

## Contribution Flow

### 1. Create an issue

Before starting, create an issue describing the proposed change.

### 2. Fork and branch

```bash
git checkout -b feature/my-feature
```

### 3. Make your changes

- Follow existing code style
- Add tests for new functionality
- Update documentation if needed

### 4. Test

```bash
pytest
ruff check .
mypy langchain_maritaca
```

### 5. Commit

Follow the [Conventional Commits](https://www.conventionalcommits.org/) pattern:

```bash
git commit -m "feat: add support for X"
git commit -m "fix: fix bug in Y"
git commit -m "docs: update documentation for Z"
```

### 6. Pull Request

Open a PR with a clear description of the changes.

## Code Standards

### Docstrings

Use Google style:

```python
def function(param1: str, param2: int) -> bool:
    """Brief description.

    More detailed description if needed.

    Args:
        param1: Description of param1.
        param2: Description of param2.

    Returns:
        Description of return value.

    Raises:
        ValueError: When error occurs.
    """
```

### Type Hints

Always use type hints:

```python
def process(text: str, limit: int | None = None) -> list[str]:
    ...
```

### Imports

Organize imports with isort (via ruff):

```python
# stdlib
import os
from typing import Any

# third-party
import httpx
from langchain_core.messages import AIMessage

# local
from langchain_maritaca.version import __version__
```

## Reporting Bugs

Include in the issue:

1. Python version
2. langchain-maritaca version
3. Code to reproduce
4. Complete error message
5. Expected vs actual behavior

## Suggesting Features

Describe in the issue:

1. Problem it solves
2. Proposed solution
3. Alternatives considered
4. Usage examples

## Code of Conduct

- Be respectful
- Accept constructive feedback
- Focus on what's best for the community

## License

By contributing, you agree that your contributions will be licensed under the same MIT license as the project.
