#!/usr/bin/env bash
# Run all checks: lint, format, typecheck, and tests

set -e

cd "$(dirname "$0")/.."

echo "=== Running all checks ==="
echo

echo "--- Ruff lint ---"
uv run ruff check .
echo

echo "--- Ruff format ---"
uv run ruff format --check .
echo

echo "--- Mypy typecheck ---"
uv run mypy artificer
echo

echo "--- Pytest ---"
uv run pytest
echo

echo "=== All checks passed! ==="
