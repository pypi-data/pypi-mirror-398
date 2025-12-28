"""
Minimal stub for sandbox interface.

This provides the SandboxInterface and ExecResult types without requiring
the full sandbox package. Used when sandbox functionality is not needed
(e.g., for GriffinBot which runs locally).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Self


@dataclass
class ExecResult:
    """
    Result from a completed sandbox exec operation.
    """

    stdout: bytes
    """Complete stdout output from the command."""

    stderr: bytes
    """Complete stderr output from the command."""

    returncode: int
    """Exit code of the process."""


class SandboxInterface(ABC):
    """
    Abstract interface for sandbox operations.

    This is a minimal stub that defines the interface without implementation.
    For actual sandbox functionality, install the full sandbox package.
    """

    @abstractmethod
    async def __aenter__(self) -> Self:
        """Enter the async context manager, starting the sandbox."""
        ...

    @abstractmethod
    async def __aexit__(self, *args: Any) -> None:
        """Exit the async context manager, stopping the sandbox."""
        ...

    @abstractmethod
    async def start(
        self,
        *,
        command: str,
        args: list[str] | None = None,
        container_image: str,
        tags: list[str] | None = None,
        timeout_seconds: int | None = None,
        **kwargs: Any,
    ) -> str:
        """Start the sandbox and wait for it to be ready."""
        ...

    @abstractmethod
    async def stop(
        self,
        *,
        snapshot_on_stop: bool = False,
        timeout_seconds: int | None = None,
    ) -> bool:
        """Stop the sandbox."""
        ...

    @abstractmethod
    async def exec(
        self,
        command: list[str],
        *,
        timeout_seconds: int | None = None,
    ) -> ExecResult:
        """Execute a command in the running sandbox."""
        ...

    @abstractmethod
    async def read_file(
        self,
        filepath: str,
        *,
        timeout_seconds: int | None = None,
    ) -> bytes:
        """Read a file from the sandbox filesystem."""
        ...

    @abstractmethod
    async def write_file(
        self,
        filepath: str,
        contents: bytes,
        *,
        timeout_seconds: int | None = None,
    ) -> bool:
        """Write a file to the sandbox filesystem."""
        ...
