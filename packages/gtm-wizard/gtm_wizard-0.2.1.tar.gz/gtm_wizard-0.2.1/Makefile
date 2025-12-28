.PHONY: install dev lint format type-check test clean build publish all sync lock inspect serve

# UV-based commands (recommended)
sync:
	uv sync --all-extras

lock:
	uv lock

lint:
	uv run ruff check src tests

format:
	uv run ruff format src tests
	uv run ruff check --fix src tests

type-check:
	uv run mypy src

test:
	uv run pytest

test-cov:
	uv run pytest --cov --cov-report=html

# Development tools
inspect:
	npx @modelcontextprotocol/inspector uv run python -m gtm_wizard.server

serve:
	uv run python -m gtm_wizard.server

# Legacy pip commands (for compatibility)
install:
	pip install -e .

dev:
	pip install -e ".[dev]"

# Build and publish
clean:
	rm -rf build dist *.egg-info .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage .venv

build: clean
	uv run python -m build

publish: build
	uv run twine upload dist/*

all: format lint type-check test
