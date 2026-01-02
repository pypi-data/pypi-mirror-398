# pydantic-ai-backend

[![PyPI version](https://img.shields.io/pypi/v/pydantic-ai-backend.svg)](https://pypi.org/project/pydantic-ai-backend/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

File storage and sandbox backends for AI agents. Works with [pydantic-ai](https://github.com/pydantic/pydantic-ai) and [pydantic-deep](https://github.com/vstorm-co/pydantic-deepagents).

## Features

- **BackendProtocol** - Unified interface for file operations
- **StateBackend** - In-memory storage (perfect for testing)
- **FilesystemBackend** - Real filesystem with path sandboxing
- **CompositeBackend** - Route operations to different backends by path
- **DockerSandbox** - Isolated Docker containers with command execution
- **SessionManager** - Multi-user session management for Docker sandboxes
- **RuntimeConfig** - Pre-configured Docker environments

## Installation

```bash
pip install pydantic-ai-backend
```

With Docker sandbox support:

```bash
pip install pydantic-ai-backend[docker]
```

## Quick Start

### In-Memory Backend (Testing)

```python
from pydantic_ai_backends import StateBackend

backend = StateBackend()

# Write a file
backend.write("/src/app.py", "print('hello')")

# Read it back (with line numbers)
content = backend.read("/src/app.py")
print(content)  # "     1\tprint('hello')"

# Search files
matches = backend.grep_raw("print")
```

### Filesystem Backend

```python
from pydantic_ai_backends import FilesystemBackend

backend = FilesystemBackend("/path/to/workspace")

# All operations are sandboxed to the root directory
backend.write("/data/file.txt", "content")
files = backend.glob_info("**/*.py")
```

### Composite Backend

```python
from pydantic_ai_backends import CompositeBackend, StateBackend, FilesystemBackend

backend = CompositeBackend(
    default=StateBackend(),  # For unmatched paths
    routes={
        "/project/": FilesystemBackend("/my/project"),
        "/workspace/": FilesystemBackend("/tmp/workspace"),
    },
)

# Routes to FilesystemBackend
backend.write("/project/app.py", "...")

# Routes to StateBackend (default)
backend.write("/temp/scratch.txt", "...")
```

### Docker Sandbox

```python
from pydantic_ai_backends import DockerSandbox

sandbox = DockerSandbox(image="python:3.12-slim")

try:
    # Write and execute
    sandbox.write("/workspace/script.py", "print(1 + 1)")
    result = sandbox.execute("python /workspace/script.py")
    print(result.output)  # "2"
finally:
    sandbox.stop()
```

### Docker Sandbox with Runtime Config

```python
from pydantic_ai_backends import DockerSandbox, RuntimeConfig

# Custom runtime with packages pre-installed
runtime = RuntimeConfig(
    name="ml-env",
    base_image="python:3.12-slim",
    packages=["pandas", "numpy", "scikit-learn"],
)

sandbox = DockerSandbox(runtime=runtime)
result = sandbox.execute("python -c 'import pandas; print(pandas.__version__)'")
```

### Built-in Runtimes

```python
from pydantic_ai_backends import DockerSandbox

# Use a built-in runtime by name
sandbox = DockerSandbox(runtime="python-datascience")

# Available runtimes:
# - python-minimal: Clean Python 3.12
# - python-datascience: pandas, numpy, matplotlib, scikit-learn, seaborn
# - python-web: FastAPI, SQLAlchemy, httpx
# - node-minimal: Clean Node.js 20
# - node-react: TypeScript, Vite, React
```

### Session Manager (Multi-User)

```python
from pydantic_ai_backends import SessionManager

manager = SessionManager(default_runtime="python-datascience")

# Get or create sandbox for user
sandbox = await manager.get_or_create("user-123")

# Use the sandbox...
result = sandbox.execute("python script.py")

# Cleanup idle sessions
cleaned = await manager.cleanup_idle(max_idle=1800)

# Shutdown all sessions
await manager.shutdown()
```

## Backend Protocol

All backends implement `BackendProtocol`:

```python
class BackendProtocol(Protocol):
    def ls_info(self, path: str) -> list[FileInfo]: ...
    def read(self, path: str, offset: int = 0, limit: int = 2000) -> str: ...
    def write(self, path: str, content: str | bytes) -> WriteResult: ...
    def edit(self, path: str, old: str, new: str, replace_all: bool = False) -> EditResult: ...
    def glob_info(self, pattern: str, path: str = "/") -> list[FileInfo]: ...
    def grep_raw(self, pattern: str, path: str | None = None, glob: str | None = None) -> list[GrepMatch] | str: ...
```

`SandboxProtocol` extends this with command execution:

```python
class SandboxProtocol(BackendProtocol, Protocol):
    def execute(self, command: str, timeout: int | None = None) -> ExecuteResponse: ...
    @property
    def id(self) -> str: ...
```

## Integration with pydantic-ai

```python
from pydantic_ai import Agent
from pydantic_ai_backends import StateBackend

# Use backends with any pydantic-ai agent
backend = StateBackend()

# Your agent can use backend for file operations
# See pydantic-deep for full integration
```

## Development

```bash
# Clone and install
git clone https://github.com/vstorm-co/pydantic-ai-backend.git
cd pydantic-ai-backend
make install

# Run tests
make test

# Run all checks
make all
```

## License

MIT License - see [LICENSE](LICENSE) for details.
