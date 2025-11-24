.PHONY: help install setup launch-jupyter run-adk-web check-code fix-code type-check clean init-db clean-db

# Python version
PYTHON := python3.11
VENV := .venv
BIN := $(VENV)/bin
POETRY := poetry
AGENTS_DIR := src/agents
DB_PATH := data/data_engineer.db


# Default target
help:
	@echo "Available targets:"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make install        - Install all dependencies with Poetry"
	@echo "  make setup          - Complete setup (install + create .env)"
	@echo "  make init-db        - Initialize/reinitialize database with sample data"
	@echo ""
	@echo "Running the Agent:"
	@echo "  make run-adk-web    - Launch ADK Web UI (http://127.0.0.1:8000)"
	@echo "  make run-adk-api    - Launch ADK API Server (http://127.0.0.1:8000)"
	@echo "  make test-agent     - Test agent with InMemoryRunner (no server needed)"
	@echo ""
	@echo "Agent2Agent (A2A) Workflow:"
	@echo "  make start-data-source  - Start Data Source Agent A2A Server (port 8001)"
	@echo "  make run-ingestion      - Run Ingestion Agent (interactive mode)"
	@echo ""
	@echo "Development Tools:"
	@echo "  make launch-jupyter - Start Jupyter Notebook"
	@echo "  make check-code     - Check code with Ruff (no fixes)"
	@echo "  make fix-code       - Run Ruff formatter/linter to fix code"
	@echo "  make type-check     - Run mypy type checker"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean          - Remove virtual environment and cache files"
	@echo "  make clean-db       - Remove database files"

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
	@echo "  2. Run 'make run-adk-web' to start the agent"
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

# Launch ADK Web interface
run-adk-web:
	@if [ ! -d $(VENV) ]; then \
		echo "Virtual environment not found. Run 'make install' first."; \
		exit 1; \
	fi
	@echo "Starting ADK Web UI..."
	@echo "🚀 Data Engineer Agent will be available at: http://127.0.0.1:8000"
	@echo "Press Ctrl+C to stop the server"
	@echo ""
	$(POETRY) run adk web $(AGENTS_DIR) --port 8000

# Launch ADK API Server
run-adk-api:
	@if [ ! -d $(VENV) ]; then \
		echo "Virtual environment not found. Run 'make install' first."; \
		exit 1; \
	fi
	@echo "Starting ADK API Server..."
	@echo "🚀 API Server will be available at: http://127.0.0.1:8000"
	@echo "📡 API Docs available at: http://127.0.0.1:8000/docs"
	@echo "Press Ctrl+C to stop the server"
	@echo ""
	$(POETRY) run adk api_server $(AGENTS_DIR) --port 8000

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

# Test agent with InMemoryRunner
test-agent:
	@if [ ! -d $(VENV) ]; then \
		echo "Virtual environment not found. Run 'make install' first."; \
		exit 1; \
	fi
	@echo "Testing agent with InMemoryRunner..."
	@echo ""
	$(POETRY) run python test_agent_runner.py

# Start Data Source Agent A2A Server
start-data-source:
	@if [ ! -d $(VENV) ]; then \
		echo "Virtual environment not found. Run 'make install' first."; \
		exit 1; \
	fi
	@echo "Starting Data Source Agent A2A Server..."
	$(POETRY) run python -m src.agents.data_source_agent.server

# Run Ingestion Agent (interactive mode)
run-ingestion:
	@if [ ! -d $(VENV) ]; then \
		echo "Virtual environment not found. Run 'make install' first."; \
		exit 1; \
	fi
	@echo "Running Ingestion Agent (interactive mode)..."
	@echo "Make sure Data Source Agent is running on port 8001!"
	@echo ""
	$(POETRY) run adk web src/agents/ingestion_agent --port 8002

# Initialize database with sample data
init-db:
	@if [ ! -d $(VENV) ]; then \
		echo "Virtual environment not found. Run 'make install' first."; \
		exit 1; \
	fi
	@echo "Initializing database..."
	$(POETRY) run python -m src.database.init_db
	@echo ""
	@echo "Database initialized successfully!"

# Remove database files
clean-db:
	@echo "Removing database files..."
	@if [ -f $(DB_PATH) ]; then \
		rm -f $(DB_PATH); \
		echo "  ✓ Removed $(DB_PATH)"; \
	else \
		echo "  - No database file found at $(DB_PATH)"; \
	fi
	@if [ -d data/ ]; then \
		rmdir --ignore-fail-on-non-empty data/ 2>/dev/null || true; \
	fi
	@echo "Database cleanup complete"

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