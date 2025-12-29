# Task Completion Checklist

When completing a task, ensure the following:

## Code Quality
1. **Lint**: `uv run ruff check .` - fix any issues
2. **Format**: `uv run ruff format .` - ensure consistent formatting
3. **Tests**: `make test` or `uv run pytest` - all tests should pass

## Documentation
- **README.md**: Update when adding new features or making breaking changes
- **REFACTORING.md**: Track migration progress (if exists)
- Document migration paths for breaking changes

## Git
- Commit with clear, descriptive messages
- Reference issues if applicable

## Before Submitting
- [ ] Code follows style conventions (single quotes, 120 line length, modern type hints)
- [ ] No linting errors (`ruff check`)
- [ ] Code is formatted (`ruff format`)
- [ ] Tests pass (`make test`)
- [ ] Documentation updated if needed
- [ ] No debug code or print statements left behind
