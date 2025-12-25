#!/usr/bin/env sh
# Local CI script for tc-pytools
# This script runs all checks that would be run in CI

set -e

echo "================================"
echo "TC PyTools Local CI"
echo "================================"
echo

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print step
print_step() {
    printf "%b\n" "${BLUE}==>${NC} $1"
}

# Function to print success
print_success() {
    printf "%b\n" "${GREEN}✓${NC} $1"
}

# Function to print error
print_error() {
    printf "%b\n" "${RED}✗${NC} $1"
}

# Track if any step fails
FAILED=0

# Step 1: Check if uv is installed
print_step "Checking uv installation..."
if ! command -v uv >/dev/null 2>&1; then
    print_error "uv is not installed. Please install it first."
    exit 1
fi
print_success "uv is installed"
echo

# Step 2: Sync dependencies
print_step "Syncing dependencies with uv..."
if uv sync; then
    print_success "Dependencies synced"
else
    print_error "Failed to sync dependencies"
    FAILED=1
fi
echo

# Step 3: Run code formatters check
print_step "Checking code formatting with ruff..."
if uv run ruff format --check .; then
    print_success "Code formatting is correct"
else
    print_error "Code formatting issues found. Run 'uv run ruff format .' to fix"
    FAILED=1
fi
echo

# Step 4: Run linter
print_step "Running linter (ruff)..."
if uv run ruff check .; then
    print_success "No linting issues found"
else
    print_error "Linting issues found. Run 'uv run ruff check --fix .' to fix"
    FAILED=1
fi
echo

# Step 5: Run type checker
print_step "Running type checker (mypy)..."
if uv run mypy genome liftover --ignore-missing-imports; then
    print_success "Type checking passed"
else
    print_error "Type checking failed"
    FAILED=1
fi
echo

# Step 6: Run tests
print_step "Running tests with pytest..."
if uv run pytest -v; then
    print_success "All tests passed"
else
    print_error "Tests failed"
    FAILED=1
fi
echo

# Step 7: Run tests with coverage
print_step "Running tests with coverage..."
if uv run pytest --cov=genome --cov=liftover --cov=vcf --cov-report=term-missing --cov-report=html; then
    print_success "Coverage report generated"
    echo "    HTML report: htmlcov/index.html"
else
    print_error "Coverage test failed"
    FAILED=1
fi
echo

# Final result
echo "================================"
if [ $FAILED -eq 0 ]; then
    print_success "All checks passed!"
    echo "================================"
    exit 0
else
    print_error "Some checks failed!"
    echo "================================"
    exit 1
fi
