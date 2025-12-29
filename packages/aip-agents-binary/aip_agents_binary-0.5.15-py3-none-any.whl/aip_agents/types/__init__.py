"""Type definitions for aip_agents package.

This module exports type definitions used throughout the aip_agents package
for better type safety and code clarity.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel

from aip_agents.schema.a2a import (
    A2AEvent,
    A2AStreamEventType,
    ToolCallInfo,
    ToolResultInfo,
)


class ChatMessage(BaseModel):
    """Represents a single message in a chat conversation."""

    role: str
    content: str


@runtime_checkable
class AgentProtocol(Protocol):
    """Defines the expected interface for an agent."""

    id: str
    name: str
    description: str

    def run(self, query: str, **kwargs: Any) -> dict[str, Any]:
        """Synchronous execution method.

        Args:
            query (str): The query to execute.
            **kwargs (Any): Additional keyword arguments.

        Returns:
            dict[str, Any]: The execution result.
        """
        ...

    async def arun(self, query: str, **kwargs: Any) -> dict[str, Any]:
        """Asynchronous execution method.

        Args:
            query (str): The query to execute.
            **kwargs (Any): Additional keyword arguments.

        Returns:
            dict[str, Any]: The execution result.
        """
        ...


__all__ = [
    "A2AEvent",
    "A2AStreamEventType",
    "ToolCallInfo",
    "ToolResultInfo",
    "AgentProtocol",
    "ChatMessage",
]
