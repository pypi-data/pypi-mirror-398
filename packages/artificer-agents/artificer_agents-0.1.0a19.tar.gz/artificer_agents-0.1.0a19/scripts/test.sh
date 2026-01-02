#!/usr/bin/env bash
# Run pytest tests

set -e

cd "$(dirname "$0")/.."

echo "Running pytest..."
uv run pytest "$@"

echo "Tests complete!"
