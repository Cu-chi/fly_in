MAIN = src/fly_in/main.py
MYPY_FLAGS = --warn-return-any --warn-unused-ignores --ignore-missing-imports \
--disallow-untyped-defs --check-untyped-defs
VENV = .venv

install:
	uv sync

run:
	uv run python $(MAIN)

run-bypass-limits:
	uv run python $(MAIN) --bypass-limits

test:
	uv run python -m pytest -v

debug:
	uv run python -m pdb $(MAIN)

clean:
	@rm -rf $$(find . -type d -name "__pycache__")
	@rm -rf $$(find . -type d -name ".mypy_cache")
	@rm -rf $$(find . -type d -name ".pytest_cache")
	@rm -rf $$(find . -type d -name ".ruff_cache")
	@echo temporary files and caches deleted

lint:
	uv run python -m flake8 . --extend-exclude $(VENV)
	uv run python -m mypy . $(MYPY_FLAGS)

lint-strict:
	uv run python -m flake8 . --extend-exclude $(VENV)
	uv run python -m mypy . --strict

.PHONY: install run debug clean lint lint-strict test run-bypass-limits
