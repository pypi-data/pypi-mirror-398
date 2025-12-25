.PHONY: help install test build upload

VENV := .venv

# Default target
help:
	@echo "Korea Investment Stock - Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  install    Install package in editable mode"
	@echo "  test       Run all tests"
	@echo "  build      Build distribution packages"
	@echo "  upload     Upload package to PyPI"

# Install package in editable mode
install:
	@test -d $(VENV) || python3 -m venv $(VENV)
	@source $(VENV)/bin/activate && pip install -e .

# Run all tests
test:
	@test -d $(VENV) || python3 -m venv $(VENV)
	@source $(VENV)/bin/activate && pytest

# Build distribution packages
build:
	@test -d $(VENV) || python3 -m venv $(VENV)
	@rm -rf build/ dist/ *.egg-info
	@source $(VENV)/bin/activate && python -m build

# Upload to PyPI
upload:
	@test -d $(VENV) || python3 -m venv $(VENV)
	@source $(VENV)/bin/activate && python -m twine upload dist/*
