from enum import Enum
from typing import Any
from typing_extensions import TypedDict

__all__ = ['A2AStreamEventType', 'A2AEvent', 'ToolCallInfo', 'ToolResultInfo']

class A2AStreamEventType(Enum):
    """Semantic event types for A2A agent-executor communication."""
    STATUS_UPDATE: str
    CONTENT_CHUNK: str
    FINAL_RESPONSE: str
    TOOL_CALL: str
    TOOL_RESULT: str
    ERROR: str
    STEP_LIMIT_EXCEEDED: str

class A2AEvent(TypedDict):
    """Structured event data used by the A2A connector."""
    event_type: A2AStreamEventType
    content: str
    metadata: dict[str, Any]
    tool_info: dict[str, Any] | None
    is_final: bool
    artifacts: list[dict[str, Any]] | None
    references: list[Any] | None
    step_usage: dict[str, Any] | None
    total_usage: dict[str, Any] | None
    thinking_and_activity_info: dict[str, Any] | None

class ToolCallInfo(TypedDict):
    """Structured information for tool invocation events."""
    tool_calls: list[dict[str, Any]]
    status: str

class ToolResultInfo(TypedDict):
    """Structured information for tool completion events."""
    name: str
    args: dict[str, Any]
    output: str
    execution_time: float | None
