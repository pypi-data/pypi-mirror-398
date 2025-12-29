.PHONY: help install dev install-dev test lint format clean build publish

help:
	@echo "Available commands:"
	@echo "  make install       - Install package"
	@echo "  make dev           - Install package in development mode"
	@echo "  make install-dev   - Install package with dev dependencies"
	@echo "  make test          - Run tests"
	@echo "  make lint          - Run linters (ruff, mypy)"
	@echo "  make format        - Format code with ruff"
	@echo "  make clean         - Clean build artifacts"
	@echo "  make build         - Build package"
	@echo "  make publish       - Publish to PyPI"

install:
	pip install -e .

dev:
	pip install -e ".[dev]"

install-dev:
	pip install -e ".[dev]"

test:
	pytest

test-cov:
	pytest --cov=git_miner --cov-report=html

lint:
	ruff check git_miner tests
	mypy git_miner

format:
	ruff check --fix git_miner tests
	ruff format git_miner tests

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

build:
	python -m build

publish:
	python -m twine upload dist/*
