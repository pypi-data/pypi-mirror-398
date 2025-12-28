.PHONY: help install install-dev clean lint format type-check pre-commit setup

help:
	@echo "Available targets:"
	@echo "  install        - Install production dependencies using uv"
	@echo "  install-dev    - Install development dependencies using uv"
	@echo "  clean          - Remove build artifacts and cache files"
	@echo "  lint           - Run ruff linter"
	@echo "  format         - Format code with ruff"
	@echo "  type-check     - Run mypy type checker"
	@echo "  test           - Run pytest"
	@echo "  pre-commit     - Run all pre-commit checks"
	@echo "  setup          - Initial project setup"

init:
	uv sync --all-extras
	pre-commit install -f -t pre-push -t pre-commit

install:
	uv pip install -e .

install-dev:
	uv pip install -e ".[dev]"

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

lint:
	uv run ruff check src/ tests/

lint-fix:
	uv run ruff check --fix src/ tests/

format:
	uv run ruff format --diff src/ tests/

format-fix:
	uv run ruff format src/ tests/

type-check:
	uv run mypy src/

test:
	uv run pytest tests/ -v

pre-commit: format-fix lint-fix type-check
	@echo "✓ All pre-commit checks passed"

setup: init install-dev pre-commit
	@echo "✓ Project setup complete"
