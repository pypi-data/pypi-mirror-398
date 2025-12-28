.PHONY: install dev test lint format check run clean build publish

install:
	uv sync

dev:
	uv sync --all-groups
	uv run pre-commit install

test:
	uv run pytest -v

lint:
	uv run ruff check src tests
	uv run ruff format --check src tests

format:
	uv run ruff format src tests
	uv run ruff check --fix src tests

check: lint test

run:
	uv run mcpserver

clean:
	rm -rf build/ dist/ *.egg-info/ .pytest_cache/ .ruff_cache/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

build: clean
	uv build

publish: build
	uv publish --username __token__
