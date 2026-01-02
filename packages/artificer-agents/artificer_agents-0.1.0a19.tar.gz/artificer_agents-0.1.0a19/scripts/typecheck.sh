#!/usr/bin/env bash
# Run mypy type checker on the codebase

set -e

cd "$(dirname "$0")/.."

echo "Running mypy type check..."
uv run mypy artificer

echo "Type check complete!"
