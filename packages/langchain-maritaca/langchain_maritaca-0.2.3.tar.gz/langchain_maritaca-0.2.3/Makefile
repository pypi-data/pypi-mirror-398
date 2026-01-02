.PHONY: all format lint test tests integration_tests help install dev clean build publish

# Default target
all: help

# Variables
PYTHON_FILES = langchain_maritaca tests
TEST_FILE ?= tests/

# Installation
install:
	pip install -e .

dev:
	pip install -e ".[dev]"

# Testing
test tests:
	pytest tests/unit_tests/ -v

integration_test integration_tests:
	pytest tests/integration_tests/ -v

test_all:
	pytest $(TEST_FILE) -v

test_cov:
	pytest --cov=langchain_maritaca --cov-report=html --cov-report=term-missing

# Linting and formatting
lint:
	ruff check $(PYTHON_FILES)
	ruff format $(PYTHON_FILES) --check
	mypy langchain_maritaca

format:
	ruff format $(PYTHON_FILES)
	ruff check --fix $(PYTHON_FILES)

# Type checking
typecheck:
	mypy langchain_maritaca

# Build and publish
clean:
	rm -rf dist/ build/ *.egg-info .pytest_cache .mypy_cache .ruff_cache htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

build: clean
	python -m build

publish: build
	python -m twine upload dist/*

publish_test: build
	python -m twine upload --repository testpypi dist/*

# Help
help:
	@echo 'langchain-maritaca Development Commands'
	@echo '========================================'
	@echo ''
	@echo 'Installation:'
	@echo '  install              - Install package'
	@echo '  dev                  - Install with dev dependencies'
	@echo ''
	@echo 'Testing:'
	@echo '  test                 - Run unit tests'
	@echo '  integration_tests    - Run integration tests'
	@echo '  test_all             - Run all tests'
	@echo '  test_cov             - Run tests with coverage'
	@echo ''
	@echo 'Code Quality:'
	@echo '  lint                 - Run linters'
	@echo '  format               - Format code'
	@echo '  typecheck            - Run type checking'
	@echo ''
	@echo 'Build & Publish:'
	@echo '  clean                - Remove build artifacts'
	@echo '  build                - Build package'
	@echo '  publish              - Publish to PyPI'
	@echo '  publish_test         - Publish to TestPyPI'
