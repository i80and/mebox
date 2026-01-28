.PHONY: check test

check:
	uv run mypy .
	uv run ruff check

test:
	uv run pytest
