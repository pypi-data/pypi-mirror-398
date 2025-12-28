.PHONY: help install check test lint type-check build clean

# Display help information by default
help:
	@echo "Available commands:"
	@echo "  make install    - Install development dependencies"
	@echo "  make check      - Run all checks (lint + type-check + test)"
	@echo "  make lint       - Run ruff for code checking and formatting"
	@echo "  make type-check - Run mypy for type checking"
	@echo "  make test       - Run pytest with coverage report"
	@echo "  make build      - Build package (wheel & sdist)"
	@echo "  make clean      - Clean build artifacts and cache"

# Install dependencies
install:
	pip install --upgrade pip
	pip install -e ".[dev]"

# Code style check and auto-formatting
lint:
	ruff check src/ --fix
	ruff format src/

# Type checking
type-check:
	mypy src

# Run tests
test:
	pytest --cov=gns3_copilot --cov-report=term-missing || true

# Run all key checks at once (must run before commit)
check: lint type-check tests

# Build and test package
build:
	rm -rf dist/
	python -m build
	twine check dist/*

# Clean up junk files
clean:
	rm -rf build/ dist/ *.egg-info .mypy_cache .pytest_cache .coverage htmlcov
	find . -type d -name "__pycache__" -exec rm -rf {} +
