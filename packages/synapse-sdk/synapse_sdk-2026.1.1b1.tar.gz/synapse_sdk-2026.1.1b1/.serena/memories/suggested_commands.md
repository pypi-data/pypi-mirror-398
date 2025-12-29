# Development Commands

## Package Management (uv)
```bash
uv sync                    # Install dependencies
uv sync --all-extras       # Install all optional dependencies
uv add <package>           # Add a dependency
uv run <command>           # Run command in virtual environment
```

## Testing
```bash
make test                  # Run all tests
make test-coverage         # Run tests with coverage report
uv run pytest tests/ -v    # Run tests directly
uv run pytest tests/path/to/test.py -k "test_name"  # Run specific test
```

## Linting & Formatting
```bash
uv run ruff check .        # Lint code
uv run ruff check . --fix  # Lint and auto-fix
uv run ruff format .       # Format code
```

## Documentation
```bash
make docs                  # Start docs dev server (port 3500)
make docs-build            # Build docs
make docs-gen              # Generate API docs from docstrings
```

## CLI Entry Point
```bash
synapse                    # Main CLI (defined in pyproject.toml)
uv run synapse             # Run CLI via uv
```

## System Commands (Darwin/macOS)
```bash
git status/log/diff/etc    # Git operations
ls -la                     # List files
find . -name "*.py"        # Find files
grep -r "pattern" .        # Search in files
```
