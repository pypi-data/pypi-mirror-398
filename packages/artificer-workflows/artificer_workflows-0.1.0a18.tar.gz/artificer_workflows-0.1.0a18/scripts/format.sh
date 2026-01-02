#!/usr/bin/env bash
# Run ruff formatter on the codebase

set -e

cd "$(dirname "$0")/.."

echo "Running ruff format check..."
uv run ruff format --check .

echo "Format check complete!"
