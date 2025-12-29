.PHONY: test test-coverage docs docs-build docs-gen

# --------------------------------
# Environment Variables
# --------------------------------

PYTHON_VERSION ?= 3.12
VENV_DIR ?= .venv

# --------------------------------
# Development Environment Commands
# --------------------------------

# Create virtual environment with uv using Python 3.12
uv-venv:
	uv venv $(VENV_DIR) --python $(PYTHON_VERSION)
	@echo "Virtual environment created at $(VENV_DIR) with Python $(PYTHON_VERSION)"
	@echo "Run 'source $(VENV_DIR)/bin/activate' to activate"

# Install dependencies with uv
uv-install:
	uv sync --all-extras

# Create venv and install dependencies
uv-setup: uv-venv uv-install
	@echo "Development environment setup complete"

# Remove virtual environment
uv-clean-venv:
	rm -rf $(VENV_DIR)
	@echo "Virtual environment removed"

# --------------------------------
# Testing Commands
# --------------------------------

# Run all tests
test:
	uv run python -m pytest tests/ -v

# Run tests with coverage report
test-coverage:
	uv run python -m pytest tests/ --cov=synapse_sdk --cov-report=term-missing --cov-report=html --cov-report=xml

# --------------------------------
# Documentation Commands
# --------------------------------

# Start docs dev server
docs:
	cd docs && npm start -- --port 3500

# Build docs
docs-build:
	cd docs && npm run build

# Generate API docs from Python docstrings
docs-gen:
	uv run pydoc-markdown
