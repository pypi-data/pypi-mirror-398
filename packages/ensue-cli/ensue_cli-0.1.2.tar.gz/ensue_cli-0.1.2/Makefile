.PHONY: format lint check test test-cov install clean build publish

# Formatting
format:
	ruff format .

# Linting
lint:
	ruff check --fix .

# Check without modifying (for CI)
check:
	ruff format --check .
	ruff check .

# Run tests
test:
	pytest -v

# Run tests with coverage
test-cov:
	pytest --cov=ensue_cli --cov-report=term-missing --cov-fail-under=100

# Install in development mode
install:
	pip install -e ".[dev]"

# Clean build artifacts
clean:
	rm -rf dist/ build/ *.egg-info src/*.egg-info .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

# Build package
build: clean
	python -m build

# Publish to PyPI
publish: build
	twine upload dist/*
