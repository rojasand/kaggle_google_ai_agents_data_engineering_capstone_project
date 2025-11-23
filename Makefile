.PHONY: help install setup launch-jupyter check-code fix-code type-check clean

# Python version
PYTHON := python3.11
VENV := .venv
BIN := $(VENV)/bin
POETRY := poetry

# Default target
help:
	@echo "Available targets:"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make install        - Install all dependencies with Poetry"
	@echo "  make setup          - Complete setup (install + create .env)"
	@echo ""
	@echo "Development Tools:"
	@echo "  make launch-jupyter - Start Jupyter Notebook"
	@echo "  make check-code     - Check code with Ruff (no fixes)"
	@echo "  make fix-code       - Run Ruff formatter/linter to fix code"
	@echo "  make type-check     - Run mypy type checker"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean          - Remove virtual environment and cache files"
	@echo ""
	@echo "Agent Usage:"
	@echo "  To run the Data Engineer Agent:"
	@echo "  1. cd agents"
	@echo "  2. poetry run adk web --port 8000"
	@echo "  3. Open http://127.0.0.1:8000 in browser"

# Install dependencies only
install:
	@echo "Checking Poetry installation..."
	@if ! command -v poetry > /dev/null; then \
		echo "Error: Poetry not found. Please install Poetry first:"; \
		echo "  curl -sSL https://install.python-poetry.org | python3 -"; \
		exit 1; \
	fi
	@echo "Installing dependencies with Poetry..."
	$(POETRY) install
	@echo "Dependencies installed!"

# Complete setup: install + create .env
setup: install
	@if [ ! -f .env ]; then \
		echo "Creating .env file from .env.example..."; \
		cp .env.example .env; \
		echo ".env file created. Please edit it to add your GOOGLE_API_KEY"; \
	else \
		echo ".env file already exists"; \
	fi
	@echo ""
	@echo "=========================================="
	@echo "Setup complete!"
	@echo "=========================================="
	@echo "Next steps:"
	@echo "  1. Edit .env and add your GOOGLE_API_KEY"
	@echo "  2. cd agents && poetry run adk web --port 8000"
	@echo "  3. Open http://127.0.0.1:8000 in your browser"
	@echo "=========================================="

# Launch Jupyter Notebook
launch-jupyter:
	@if [ ! -d $(VENV) ]; then \
		echo "Virtual environment not found. Run 'make install' first."; \
		exit 1; \
	fi
	@echo "Starting Jupyter Notebook..."
	$(POETRY) run jupyter notebook

# Check code with Ruff (no fixes)
check-code:
	@if [ ! -d $(VENV) ]; then \
		echo "Virtual environment not found. Run 'make install' first."; \
		exit 1; \
	fi
	@echo "Checking code formatting with Ruff..."
	$(POETRY) run ruff format --check src/
	@echo "Checking code with Ruff linter..."
	$(POETRY) run ruff check src/
	@echo "Code check complete!"

# Type checking with mypy (optional, may have false positives)
type-check:
	@if [ ! -d $(VENV) ]; then \
		echo "Virtual environment not found. Run 'make install' first."; \
		exit 1; \
	fi
	@echo "Running mypy type checker..."
	$(POETRY) run mypy src/ || true
	@echo "Type check complete!"

# Fix code with Ruff and check types with mypy
fix-code:
	@if [ ! -d $(VENV) ]; then \
		echo "Virtual environment not found. Run 'make install' first."; \
		exit 1; \
	fi
	@echo "Running Ruff formatter..."
	$(POETRY) run ruff format src/
	@echo "Running Ruff linter..."
	$(POETRY) run ruff check src/ --fix
	@echo "Code fixes complete!"

# Clean up virtual environment and cache files
clean:
	@echo "Cleaning up..."
	rm -rf $(VENV)
	rm -rf build dist *.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ipynb_checkpoints" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "Cleanup complete"