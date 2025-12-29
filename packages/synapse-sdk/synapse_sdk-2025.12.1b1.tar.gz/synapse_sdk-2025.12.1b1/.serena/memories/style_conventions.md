# Code Style and Conventions

## Python Version & Imports
- Python 3.12+ required
- Always use `from __future__ import annotations` at top of files
- Modern type hints: `dict[str, Any]` not `Dict`, `X | None` not `Optional[X]`
- Use `list[str]` not `List[str]`, `tuple[int, ...]` not `Tuple[int, ...]`

## Formatting (Ruff)
- Line length: 120 characters
- Quote style: Single quotes (`'string'`)
- Import sorting: isort-compatible, first-party = `synapse_sdk`

## Naming Conventions
- Classes: PascalCase (`BaseAction`, `RuntimeContext`)
- Functions/methods: snake_case (`get_plugin_actions`, `set_progress`)
- Constants: UPPER_SNAKE_CASE
- Private: prefix with underscore (`_internal_method`)

## Type Hints
- All public functions should have type hints
- Use Pydantic v2 for validation models
- Use `TypeVar` and generics for action parameter types

## Docstrings
- Google style docstrings (configured in ruff)
- Required for public APIs

## Error Handling
- Use custom exception hierarchy from `synapse_sdk/exceptions.py`
- Plugin errors from `synapse_sdk/plugins/errors.py`

## Design Patterns
- Protocol-based interfaces (duck typing) over ABC inheritance
- Dependency injection via RuntimeContext
- Plugin discovery pattern (config.yaml or module introspection)
