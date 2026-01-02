"""File storage and sandbox backends for AI agents.

pydantic-ai-backend provides a unified interface for file storage and
command execution across different backends (in-memory, filesystem, Docker).

Basic usage:
    ```python
    from pydantic_ai_backends import StateBackend, FilesystemBackend

    # In-memory storage (for testing)
    backend = StateBackend()
    backend.write("/app.py", "print('hello')")
    content = backend.read("/app.py")

    # Real filesystem
    backend = FilesystemBackend("/workspace")
    ```

Docker sandbox (requires optional dependencies):
    ```python
    from pydantic_ai_backends import DockerSandbox, RuntimeConfig

    # pip install pydantic-ai-backend[docker]
    sandbox = DockerSandbox(image="python:3.12-slim")
    result = sandbox.execute("python -c 'print(1+1)'")
    print(result.output)  # "2"
    ```
"""

from __future__ import annotations

from typing import TYPE_CHECKING

# Core exports - always available
from pydantic_ai_backends.composite import CompositeBackend
from pydantic_ai_backends.filesystem import FilesystemBackend
from pydantic_ai_backends.protocol import BackendProtocol, SandboxProtocol
from pydantic_ai_backends.state import StateBackend
from pydantic_ai_backends.types import (
    EditResult,
    ExecuteResponse,
    FileData,
    FileInfo,
    GrepMatch,
    RuntimeConfig,
    WriteResult,
)

if TYPE_CHECKING:
    from pydantic_ai_backends.runtimes import BUILTIN_RUNTIMES, get_runtime
    from pydantic_ai_backends.sandbox import BaseSandbox, DockerSandbox, LocalSandbox
    from pydantic_ai_backends.session import SessionManager

# Lazy loading for optional Docker dependencies
_LAZY_IMPORTS = {
    "DockerSandbox": "pydantic_ai_backends.sandbox",
    "BaseSandbox": "pydantic_ai_backends.sandbox",
    "LocalSandbox": "pydantic_ai_backends.sandbox",
    "SessionManager": "pydantic_ai_backends.session",
    "BUILTIN_RUNTIMES": "pydantic_ai_backends.runtimes",
    "get_runtime": "pydantic_ai_backends.runtimes",
}


def __getattr__(name: str) -> object:
    """Lazy loading for optional dependencies."""
    if name in _LAZY_IMPORTS:
        import importlib

        module = importlib.import_module(_LAZY_IMPORTS[name])
        return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    # Protocols
    "BackendProtocol",
    "SandboxProtocol",
    # Types
    "FileData",
    "FileInfo",
    "WriteResult",
    "EditResult",
    "ExecuteResponse",
    "GrepMatch",
    "RuntimeConfig",
    # Backends
    "StateBackend",
    "FilesystemBackend",
    "CompositeBackend",
    # Sandbox (optional - requires docker extra)
    "BaseSandbox",
    "DockerSandbox",
    "LocalSandbox",
    "SessionManager",
    # Runtimes
    "BUILTIN_RUNTIMES",
    "get_runtime",
]

__version__ = "0.0.1"
