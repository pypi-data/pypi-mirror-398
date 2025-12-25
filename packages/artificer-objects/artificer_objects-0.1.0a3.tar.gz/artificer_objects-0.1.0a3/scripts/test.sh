#!/usr/bin/env bash
# Run pytest on the codebase

set -e

cd "$(dirname "$0")/.."

echo "Running pytest..."
uv run pytest "$@"

echo "Tests complete!"
