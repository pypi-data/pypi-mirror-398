# Default recipe
default:
    @just --list

# Setup virtual envionment
dev-setup:
    uv venv
    uv sync

# Build the project using maturin
build:
    uv run maturin develop

# Run linting with ruff and ty
lint:
    uv run ruff check .
    uv run ty check

# Run tests using pytest
test:
    uv run pytest tests/ -vvv

# Run all checks (lint + test)
check: lint test
