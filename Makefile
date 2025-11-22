.PHONY: help install launch-jupyter check-code fix-code clean

# Python version
PYTHON := python3.11
VENV := .venv
BIN := $(VENV)/bin
POETRY := poetry

# Default target
help:
	@echo "Available targets:"
	@echo "  make install        - Create venv, install all dependencies, and create .env"
	@echo "  make laufnch-jupyter - Start Jupyter Notebook"
	@echo "  make check-code     - Check code with Ruff and mypy (no fixes, just report)"
	@echo "  make fix-code       - Run Ruff formatter/linter and mypy type checker"
	@echo "  make clean          - Remove virtual environment and cache files"

# Install everything: create venv, install dependencies, create .env
install:
	@echo "Checking Poetry installation..."
	@if ! command -v poetry > /dev/null; then \
		echo "Error: Poetry not found. Please install Poetry first:"; \
		echo "  curl -sSL https://install.python-poetry.org | python3 -"; \
		exit 1; \
	fi
	@echo "Installing dependencies with Poetry..."
	poetry install
	@if [ ! -f .env ]; then \
		echo "Creating .env file..."; \
		echo "# Environment variables" > .env; \
		echo "PYTHONPATH=." >> .env; \
		echo "JUPYTER_CONFIG_DIR=./.jupyter" >> .env; \
		echo "" >> .env; \
		echo "# Add your API keys and configuration here" >> .env; \
		echo "# EXAMPLE_API_KEY=your_key_here" >> .env; \
		echo ".env file created"; \
	fi
	@echo "Setup complete! Activate the environment with: source .venv/bin/activate"

# Launch Jupyter Notebook
launch-jupyter:
	@if [ ! -d $(VENV) ]; then \
		echo "Virtual environment not found. Run 'make install' first."; \
		exit 1; \
	fi
	@echo "Starting Jupyter Notebook..."
	$(POETRY) run jupyter notebook

# Check code with Ruff and mypy (no fixes)
check-code:
	@if [ ! -d $(VENV) ]; then \
		echo "Virtual environment not found. Run 'make install' first."; \
		exit 1; \
	fi
	@echo "Checking code formatting with Ruff..."
	$(POETRY) run ruff format --check src/
	@echo "Checking code with Ruff linter..."
	$(POETRY) run ruff check src/
	@echo "Running mypy type checker..."
	$(POETRY) run mypy src/
	@echo "Code check complete!"

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
	@echo "Running mypy type checker..."
	$(POETRY) run mypy src/
	@echo "Code fixes complete!"

# Clean up
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
