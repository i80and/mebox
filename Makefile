.PHONY: check test

check:
	uv run ty check
	uv run ruff check

test:
	uv run pytest
