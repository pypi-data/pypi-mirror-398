# Contributing to pydantic-ai-todo

Thank you for your interest in contributing to pydantic-ai-todo!

## Development Setup

### Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) - Fast Python package manager

### Getting Started

```bash
# Clone the repository
git clone https://github.com/vstorm-co/pydantic-ai-todo.git
cd pydantic-ai-todo

# Install dependencies
uv sync --group dev

# Run tests
uv run pytest

# Run all checks (lint, format, typecheck)
uv run ruff check .
uv run ruff format --check .
uv run pyright
```

## Development Workflow

### Running Tests

```bash
# Run all tests with coverage
uv run coverage run -m pytest
uv run coverage report

# Run specific test
uv run pytest tests/test_toolset.py::TestCreateTodoToolset -v

# Run with debug output
uv run pytest -v -s
```

### Code Quality

We use the following tools:

- **ruff** - Linting and formatting
- **pyright** - Type checking
- **pytest** - Testing with 100% coverage requirement

```bash
# Format code
uv run ruff format .

# Fix lint issues
uv run ruff check --fix .

# Type check
uv run pyright
```

## Pull Request Guidelines

### Requirements

1. **100% test coverage** - All new code must be covered by tests
2. **Type annotations** - All functions must have type hints
3. **Passing CI** - All checks must pass (lint, typecheck, tests)

### Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Make your changes
4. Run all checks locally
5. Commit with a descriptive message
6. Push and open a Pull Request

### Commit Messages

Follow conventional commit format:

```
feat: add new storage backend
fix: handle empty todo list
docs: update README examples
test: add edge case coverage
```

## Project Structure

```
pydantic_ai_todo/
├── __init__.py     # Public API exports
├── types.py        # Todo, TodoItem models
├── storage.py      # TodoStorage, TodoStorageProtocol
└── toolset.py      # create_todo_toolset(), get_todo_system_prompt()

tests/
├── test_types.py
├── test_storage.py
└── test_toolset.py
```

## Design Principles

1. **Storage Injection** - Tools use closure pattern, not `ctx.deps`
2. **Compatibility** - `FunctionToolset[Any]` works with any pydantic-ai agent
3. **Simplicity** - Minimal API surface, easy to understand

## Questions?

Open an issue on GitHub for questions or discussions.
