#!/usr/bin/env bash
# Run all checks: lint, format, and typecheck

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
uv run mypy
echo

echo "=== All checks passed! ==="
