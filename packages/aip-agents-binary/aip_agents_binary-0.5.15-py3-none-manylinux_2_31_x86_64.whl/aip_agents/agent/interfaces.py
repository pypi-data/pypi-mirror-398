"""Common agent-facing protocols used by A2A executors.

These runtime-checkable protocols let executors validate agent instances
without importing the concrete implementation classes, which avoids
introducing circular import chains at runtime.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class LangGraphAgentProtocol(Protocol):
    """Minimal interface required by LangGraphA2AExecutor."""

    name: str

    async def arun_a2a_stream(self, query: str, **kwargs: Any) -> AsyncIterator[dict[str, Any]]:
        """Stream A2A-compatible chunks for the given query.

        Args:
            query (str): The query to execute and stream.
            **kwargs (Any): Additional keyword arguments for execution.

        Yields:
            dict[str, Any]: A2A-compatible streaming chunks.
        """


@runtime_checkable
class LangflowAgentProtocol(Protocol):
    """Minimal interface required by LangflowA2AExecutor."""

    name: str

    async def arun_a2a_stream(self, query: str, **kwargs: Any) -> AsyncIterator[dict[str, Any]]:
        """Stream A2A-compatible chunks for the given query.

        Args:
            query (str): The query to execute and stream.
            **kwargs (Any): Additional keyword arguments for execution.

        Yields:
            dict[str, Any]: A2A-compatible streaming chunks.
        """


@runtime_checkable
class GoogleADKAgentProtocol(Protocol):
    """Minimal interface required by GoogleADKExecutor."""

    name: str

    async def arun_a2a_stream(self, query: str, **kwargs: Any) -> AsyncIterator[dict[str, Any]]:
        """Stream A2A-compatible chunks for the given query.

        Args:
            query (str): The query to execute and stream.
            **kwargs (Any): Additional keyword arguments for execution.

        Yields:
            dict[str, Any]: A2A-compatible streaming chunks.
        """
