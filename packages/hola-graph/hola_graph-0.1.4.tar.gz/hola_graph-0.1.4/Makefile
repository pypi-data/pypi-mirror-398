.PHONY: build rebuild test clean swig-python lint format help typecheck check dist

build:
	@uv sync --reinstall-package hola-graph

rebuild: clean build

dist:
	@rm -rf dist/*
	@uv build

test:
	@uv run pytest

lint:
	@uv run ruff check --fix .

format:
	@uv run ruff format .

typecheck:
	@uv run mypy src/

check: lint format typecheck test

swig-python:
	@if [ ! -d "build/adaptagrams" ]; then bash scripts/setup.sh; fi
	@cd build/adaptagrams && make python

clean:
	@rm -rf .pytest_cache
	@rm -rf __pycache__ tests/__pycache__ src/__pycache__ src/hola-graph/__pycache__
	@rm -rf build thirdparty .venv dist
	@rm -rf src/*.so src/*.egg-info src/hola-graph/*.so

help:
	@echo "hola-graph build targets:"
	@echo "  build       Build and install via uv (default)"
	@echo "  rebuild     Clean and rebuild"
	@echo "  dist        Build wheel and sdist to dist/"
	@echo "  test        Run pytest"
	@echo "  lint        Run ruff linter"
	@echo "  format      Format code with ruff"
	@echo "  typecheck   Run mypy type checks"
	@echo "  check       Run lint, format, typecheck, and test"
	@echo "  swig-python Build SWIG wrapper (if available)"
	@echo "  clean       Remove build artifacts"
