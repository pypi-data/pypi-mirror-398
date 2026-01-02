# Contributing to pydantic-ai-backend

Thank you for your interest in contributing to pydantic-ai-backend!

## Development Setup

### Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) - Fast Python package manager
- Docker (optional, for running sandbox tests)

### Getting Started

```bash
# Clone the repository
git clone https://github.com/vstorm-co/pydantic-ai-backend.git
cd pydantic-ai-backend

# Install dependencies
uv sync --all-extras --group dev

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
uv run pytest tests/test_backends.py::TestStateBackend -v

# Run with debug output
uv run pytest -v -s
```

### Code Quality

We use the following tools:

- **ruff** - Linting and formatting
- **pyright** - Type checking
- **mypy** - Additional type checking
- **pytest** - Testing with 100% coverage requirement

```bash
# Format code
uv run ruff format .

# Fix lint issues
uv run ruff check --fix .

# Type check
uv run pyright
uv run mypy src/pydantic_ai_backends
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
fix: handle empty file content
docs: update README examples
test: add edge case coverage
```

## Project Structure

```
src/pydantic_ai_backends/
├── __init__.py       # Public API exports with lazy loading
├── types.py          # FileData, FileInfo, WriteResult, EditResult, etc.
├── protocol.py       # BackendProtocol, SandboxProtocol
├── state.py          # StateBackend (in-memory)
├── filesystem.py     # FilesystemBackend (real filesystem)
├── composite.py      # CompositeBackend (routing)
├── sandbox.py        # BaseSandbox, DockerSandbox, LocalSandbox
├── session.py        # SessionManager
└── runtimes.py       # RuntimeConfig, BUILTIN_RUNTIMES

tests/
├── test_backends.py
├── test_backends_extended.py
├── test_runtimes.py
├── test_session.py
└── test_lazy_loading.py
```

## Design Principles

1. **Protocol-based** - All backends implement `BackendProtocol`
2. **Lazy Loading** - Optional dependencies (docker, pypdf, chardet) loaded on-demand
3. **Composable** - Backends can be combined with `CompositeBackend`
4. **Type Safe** - Full type annotations, strict mode compatible

## Questions?

Open an issue on GitHub for questions or discussions.
