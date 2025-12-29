from aip_agents.schema.a2a import A2AEvent as A2AEvent, A2AStreamEventType as A2AStreamEventType, ToolCallInfo as ToolCallInfo, ToolResultInfo as ToolResultInfo
from pydantic import BaseModel
from typing import Any, Protocol

__all__ = ['A2AEvent', 'A2AStreamEventType', 'ToolCallInfo', 'ToolResultInfo', 'AgentProtocol', 'ChatMessage']

class ChatMessage(BaseModel):
    """Represents a single message in a chat conversation."""
    role: str
    content: str

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
    async def arun(self, query: str, **kwargs: Any) -> dict[str, Any]:
        """Asynchronous execution method.

        Args:
            query (str): The query to execute.
            **kwargs (Any): Additional keyword arguments.

        Returns:
            dict[str, Any]: The execution result.
        """
