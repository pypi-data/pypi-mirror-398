# Python executable detection
PYTHON := $(shell command -v python3 2> /dev/null || command -v python 2> /dev/null)

.PHONY: help install install-dev test lint format type-check clean release-patch release-minor release-major version

help:
	@echo "Available commands:"
	@echo "  make install       - Install package"
	@echo "  make install-dev   - Install package with dev dependencies"
	@echo "  make test          - Run tests"
	@echo "  make lint          - Run linter"
	@echo "  make format        - Format code with black"
	@echo "  make type-check    - Run type checker"
	@echo "  make clean         - Clean build artifacts"
	@echo "  make version       - Show current version"
	@echo "  make release-patch - Release new patch version (0.0.x)"
	@echo "  make release-minor - Release new minor version (0.x.0)"
	@echo "  make release-major - Release new major version (x.0.0)"

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

test:
	pytest tests/ -v --cov=src/py_mcp_installer --cov-report=term-missing

lint:
	ruff check src/ tests/

format:
	black src/ tests/
	ruff check --fix src/ tests/

type-check:
	mypy src/

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +

release-patch:  ## Release new patch version (0.0.x)
	@./scripts/release.sh patch

release-minor:  ## Release new minor version (0.x.0)
	@./scripts/release.sh minor

release-major:  ## Release new major version (x.0.0)
	@./scripts/release.sh major

version:  ## Show current version
	@$(PYTHON) scripts/manage_version.py
