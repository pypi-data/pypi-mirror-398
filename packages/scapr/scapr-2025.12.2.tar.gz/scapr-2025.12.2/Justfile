@default:
  @just --list

# Run test, lint, check, flit build
@build: test lint check
  uv run flit build

# Check formatting with ruff
@check:
  uv run ruff format --check

# Run test, lint, check
@checks: test lint check

# Clean up dist folder
@clean:
  -rm dist/*

# Apply ruff formatting
@format:
  uv run ruff format

# Chcek linting with ruff
@lint:
  uv run ruff check

# Run pytest
@test:
  uv run pytest

# Build and publish using flit
@publish: build
  uv run flit publish
