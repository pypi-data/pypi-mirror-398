.PHONY: help test test-verbose lint format install clean dev

help:
	@echo "FreeRouter Development Commands"
	@echo ""
	@echo "Testing:"
	@echo "  make test          - Run tests with coverage"
	@echo "  make test-verbose  - Run tests with detailed timing"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint          - Run linters (ruff, mypy)"
	@echo "  make format        - Format code with ruff"
	@echo ""
	@echo "Installation:"
	@echo "  make install       - Install in development mode"
	@echo "  make dev           - Install with dev dependencies"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean         - Clean temporary files"

test:
	@echo "Running tests with coverage..."
	uv run pytest --cov=freerouter --cov-report=term-missing -v

test-verbose:
	@echo "Running tests with detailed timing..."
	uv run pytest --cov=freerouter --cov-report=term-missing --durations=0 -v

lint:
	@echo "Running linters..."
	@echo "Checking code style with ruff..."
	-uv run ruff check freerouter/ tests/
	@echo "Checking types with mypy..."
	-uv run mypy freerouter/ || true

format:
	@echo "Formatting code with ruff..."
	uv run ruff format freerouter/ tests/

install:
	@echo "Installing in development mode..."
	uv pip install -e .

dev:
	@echo "Installing with dev dependencies..."
	uv pip install -e ".[dev]"

clean:
	@echo "Cleaning temporary files..."
	rm -rf build/ dist/ *.egg-info .pytest_cache .coverage htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "✓ Cleaned"
