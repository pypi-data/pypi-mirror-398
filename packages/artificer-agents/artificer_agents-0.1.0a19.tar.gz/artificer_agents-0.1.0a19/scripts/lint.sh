#!/usr/bin/env bash
# Run ruff linter on the codebase

set -e

cd "$(dirname "$0")/.."

echo "Running ruff check..."
uv run ruff check .

echo "Lint check complete!"
