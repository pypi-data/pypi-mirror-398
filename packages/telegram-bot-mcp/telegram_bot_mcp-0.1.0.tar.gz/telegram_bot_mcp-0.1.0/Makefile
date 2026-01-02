.PHONY: help install install-dev test typecheck lint format security check build clean

help:
	@echo "Available commands:"
	@echo "  make install      - Install package"
	@echo "  make install-dev  - Install package with dev dependencies"
	@echo "  make test         - Run tests"
	@echo "  make typecheck    - Run mypy type checking"
	@echo "  make lint         - Run ruff linter"
	@echo "  make format       - Format code with ruff"
	@echo "  make check        - Run all checks (lint + typecheck + test)"
	@echo "  make build        - Build wheel package"
	@echo "  make clean        - Remove build artifacts and cache"

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

test:
	pytest -v

typecheck:
	mypy telegram_bot

lint:
	ruff check .

format:
	ruff format .

check: lint typecheck test
	@echo "All checks passed!"

build:
	python -m build

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
