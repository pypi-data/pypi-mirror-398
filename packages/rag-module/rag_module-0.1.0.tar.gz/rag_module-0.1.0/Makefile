.PHONY: help install install-dev test lint format typecheck clean build publish publish-test

PYTHON := python3
PIP := $(PYTHON) -m pip

help:
	@echo "Available commands:"
	@echo "  make install       Install package"
	@echo "  make install-dev   Install package with dev dependencies"
	@echo "  make test          Run tests"
	@echo "  make lint          Run linter"
	@echo "  make format        Format code"
	@echo "  make typecheck     Run type checker"
	@echo "  make clean         Clean build artifacts"
	@echo "  make build         Build package"
	@echo "  make publish-test  Publish to TestPyPI"
	@echo "  make publish       Publish to PyPI"

install:
	$(PIP) install -e .

install-dev:
	$(PIP) install -e ".[dev]"

test:
	$(PYTHON) -m pytest tests/ -v

lint:
	$(PYTHON) -m ruff check src/ tests/

format:
	$(PYTHON) -m ruff format src/ tests/
	$(PYTHON) -m ruff check --fix src/ tests/

typecheck:
	$(PYTHON) -m mypy src/

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf src/*.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +

build: clean
	$(PYTHON) -m build

publish-test: build
	$(PYTHON) -m twine upload --repository testpypi dist/*

publish: build
	$(PYTHON) -m twine upload dist/*
