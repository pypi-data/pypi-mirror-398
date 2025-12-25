.PHONY: help install test lint format type-check ci clean

help:  ## Show this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## Install dependencies with uv
	uv sync

test:  ## Run tests
	uv run pytest -v

test-cov:  ## Run tests with coverage
	uv run pytest --cov=genome --cov=liftover --cov-report=term-missing --cov-report=html

lint:  ## Run linter
	uv run ruff check .

lint-fix:  ## Run linter and fix issues
	uv run ruff check --fix .

format:  ## Format code
	uv run ruff format .

format-check:  ## Check code formatting
	uv run ruff format --check .

type-check:  ## Run type checker
	uv run mypy genome liftover --ignore-missing-imports

ci:  ## Run local CI checks
	./ci.sh

pre-commit-install:  ## Install pre-commit hooks
	uv run pre-commit install

pre-commit-run:  ## Run pre-commit on all files
	uv run pre-commit run --all-files

clean:  ## Clean build artifacts and cache
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build:  ## Build package
	uv build

publish-test:  ## Publish to Test PyPI
	@echo "Publishing to Test PyPI..."
	uv publish --publish-url https://test.pypi.org/legacy/

publish:  ## Publish to PyPI
	@echo "Publishing to PyPI..."
	@echo "WARNING: This will publish to the official PyPI!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		uv publish; \
	else \
		echo "Cancelled."; \
	fi

publish-check:  ## Check package before publishing
	@echo "Checking package..."
	uv pip install --quiet twine 2>/dev/null || true
	uv run twine check dist/*

version:  ## Show current version
	@echo "Current version:"
	@grep '^version = ' pyproject.toml
	@grep '^__version__ = ' genome/__init__.py || echo "genome/__init__.py: version not found"
	@grep '^__version__ = ' liftover/__init__.py || echo "liftover/__init__.py: version not found"

release:  ## Full release process (build + check + publish to Test PyPI)
	@echo "Starting release process..."
	make clean
	make build
	make publish-check
	make publish-test
	@echo "Released to Test PyPI. Test it with:"
	@echo "  pip install --index-url https://test.pypi.org/simple/ tc-pytools"

run:  ## Run the main script (example usage)
	@echo "Usage: uv run rename-ngdc-genome-id -f <fasta> -o <output> [-g <gff> -og <output_gff>]"
