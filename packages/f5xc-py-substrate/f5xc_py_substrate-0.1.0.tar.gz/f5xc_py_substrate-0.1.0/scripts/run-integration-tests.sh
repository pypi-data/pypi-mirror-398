#!/bin/bash
#
# Run integration tests against a real F5 XC tenant.
#
# This script:
# 1. Loads credentials from .env file or environment variables
# 2. Runs pytest with JSON output and code coverage
# 3. Generates Markdown coverage report from JSON results
# 4. Prints summary
#
# Usage:
#   ./scripts/run-integration-tests.sh
#
# Prerequisites:
#   - F5XC_TENANT_URL and F5XC_API_TOKEN must be set (env vars or .env file)
#   - Python virtual environment should be activated
#

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================"
echo "F5 XC SDK Integration Tests"
echo "========================================"
echo ""

# Load .env if present
if [ -f "$PROJECT_ROOT/.env" ]; then
    echo -e "${GREEN}Loading credentials from .env${NC}"
    set -a
    source "$PROJECT_ROOT/.env"
    set +a
fi

# Check required vars
if [ -z "$F5XC_TENANT_URL" ] || [ -z "$F5XC_API_TOKEN" ]; then
    echo -e "${RED}Error: F5XC_TENANT_URL and F5XC_API_TOKEN must be set${NC}"
    echo ""
    echo "Set environment variables or create .env file (see .env.example)"
    exit 1
fi

# Mask token in output
MASKED_TOKEN="${F5XC_API_TOKEN:0:8}..."
echo "Running integration tests against: $F5XC_TENANT_URL"
echo "Using token: $MASKED_TOKEN"
echo ""

# Ensure output directory exists
mkdir -p "$PROJECT_ROOT/docs/test-results"

# Change to project root
cd "$PROJECT_ROOT"

# Activate virtual environment if not already active
if [ -z "$VIRTUAL_ENV" ]; then
    if [ -f ".venv/bin/activate" ]; then
        echo "Activating virtual environment..."
        source .venv/bin/activate
    else
        echo -e "${YELLOW}Warning: No virtual environment found${NC}"
    fi
fi

# Run pytest with JSON output
echo ""
echo "Running tests..."
echo "----------------------------------------"

# Run pytest, capture exit code but don't fail immediately
set +e
python -m pytest tests/integration/ \
    -v \
    --tb=short \
    --json-report \
    --json-report-file=docs/test-results/pytest-report.json \
    --cov=f5xc_py_substrate \
    --cov-report=json:docs/test-results/code-coverage.json \
    --cov-report=term-missing \
    -s

PYTEST_EXIT_CODE=$?
set -e

echo ""
echo "----------------------------------------"

# Generate Markdown report from JSON
if [ -f "$PROJECT_ROOT/docs/test-results/pytest-report.json" ]; then
    echo "Generating coverage report..."
    python "$PROJECT_ROOT/scripts/generate_coverage_report.py"
fi

echo ""
echo "========================================"
echo "Reports written to:"
echo "  docs/test-results/pytest-report.json"
echo "  docs/test-results/code-coverage.json"
echo "  docs/test-results/coverage.json"
echo "  docs/test-results/coverage.md"
echo "========================================"

# Exit with pytest's exit code
exit $PYTEST_EXIT_CODE
