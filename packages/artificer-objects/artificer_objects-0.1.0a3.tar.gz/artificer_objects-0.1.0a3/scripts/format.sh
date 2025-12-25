#!/usr/bin/env bash
# Run ruff formatter on the codebase

set -e

cd "$(dirname "$0")/.."

echo "Running ruff format..."
uv run ruff format .

echo "Format complete!"
