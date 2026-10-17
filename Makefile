.PHONY: help install install-dev install-web test lint format clean build upload upload-test check

help:
	@echo "Available commands:"
	@echo "  install        Install package"
	@echo "  install-dev    Install package with dev dependencies"
	@echo "  install-web    Install package with web (FastAPI + ReactPy) extras"
	@echo "  test           Run tests with coverage"
	@echo "  lint           Run pylint and ruff"
	@echo "  format         Format code with ruff"
	@echo "  check          Lint + test"
	@echo "  clean          Clean build artifacts"
	@echo "  build          Build sdist and wheel"
	@echo "  upload         Upload to PyPI"
	@echo "  upload-test    Upload to TestPyPI"
	@echo "  serve          Run the UI against the example skill"

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

install-web:
	pip install -e ".[web]"

test:
	pytest

lint:
	pylint src/skillgraph
	ruff check src/skillgraph tests

format:
	ruff check --fix src/skillgraph tests
	ruff format src/skillgraph tests

check: lint test

serve:
	skillgraph up examples/demo.skill

clean:
	rm -rf build/ dist/ *.egg-info src/*.egg-info .pytest_cache .coverage htmlcov .ruff_cache

build: clean
	python -m build

upload: build
	python -m twine upload dist/*

upload-test: build
	python -m twine upload --repository testpypi dist/*
