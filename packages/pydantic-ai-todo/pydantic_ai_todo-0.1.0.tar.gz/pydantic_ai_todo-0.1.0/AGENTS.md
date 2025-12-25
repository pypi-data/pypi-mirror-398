# AGENTS.md

Instructions for AI coding assistants working on this repository.

## Project Overview

**pydantic-ai-todo** is a standalone todo/task planning toolset for [pydantic-ai](https://ai.pydantic.dev/) agents. It provides `read_todos` and `write_todos` tools that work with any pydantic-ai agent without requiring specific dependencies.

## Quick Reference

| Task | Command |
|------|---------|
| Install | `uv sync --group dev` |
| Test | `uv run pytest` |
| Test + Coverage | `uv run coverage run -m pytest && uv run coverage report` |
| Lint | `uv run ruff check .` |
| Format | `uv run ruff format .` |
| Typecheck | `uv run pyright` |
| Build | `uv run python -m build` |

## Architecture

```
pydantic_ai_todo/
├── types.py      # Todo, TodoItem - Pydantic models
├── storage.py    # TodoStorage, TodoStorageProtocol - state management
├── toolset.py    # create_todo_toolset() - main factory
└── __init__.py   # public API
```

### Key Design: Storage Injection

Tools capture storage via closure, NOT through `ctx.deps`:

```python
def create_todo_toolset(storage=None):
    _storage = storage or TodoStorage()

    @toolset.tool
    async def read_todos() -> str:  # No ctx parameter!
        return format(_storage.todos)
```

This pattern ensures compatibility with ANY pydantic-ai agent deps type.

## Code Standards

- **Coverage**: 100% required - check with `uv run coverage report`
- **Types**: Pyright strict mode - all functions need type annotations
- **Style**: ruff handles formatting and linting

## Testing

Tests are in `tests/` directory. Use pytest-asyncio for async tests:

```python
async def test_write_todos():
    storage = TodoStorage()
    toolset = create_todo_toolset(storage=storage)
    # Test using toolset.tools dict
```

## When Modifying

1. Run tests after changes: `uv run pytest`
2. Check coverage stays at 100%
3. Run `uv run pyright` for type errors
4. Format with `uv run ruff format .`
