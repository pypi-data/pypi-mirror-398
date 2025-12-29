from collections.abc import AsyncIterator
from typing import Any, Protocol

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
