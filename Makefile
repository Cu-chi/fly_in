MAIN = src/fly_in/main.py
MYPY_FLAGS = --warn-return-any --warn-unused-ignores --ignore-missing-imports \
--disallow-untyped-defs --check-untyped-defs
VENV = .venv

install:
	uv sync

run:
	uv run python $(MAIN) $(ARGS)

test:
	uv run pytest

debug:
	uv run python -m pdb $(MAIN) $(ARGS)

clean:
	@rm -rf $$(find . -type d -name "__pycache__") $$(find . -type d -name ".mypy_cache")

lint:
	uv run python -m flake8 . --extend-exclude $(VENV)
	uv run python -m mypy . $(MYPY_FLAGS)

lint-strict:
	uv run python -m flake8 . --extend-exclude $(VENV)
	uv run python -m mypy . --strict

.PHONY: install run debug clean lint lint-strict test
