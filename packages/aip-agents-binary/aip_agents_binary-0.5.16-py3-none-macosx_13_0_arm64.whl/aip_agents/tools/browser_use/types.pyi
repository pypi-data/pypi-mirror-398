from dataclasses import dataclass
from typing import Any

__all__ = ['BrowserUseFatalError', 'RetryDecision', 'StreamingResponse', 'StreamingState', 'ToolCallInfo']

class BrowserUseFatalError(RuntimeError):
    """Raised when the Browser Use session must terminate immediately."""

@dataclass
class ToolCallInfo:
    """Structured information for a single tool call."""
    name: str
    args: dict[str, Any]
    output: str

@dataclass
class StreamingResponse:
    """Standardized streaming response structure."""
    event_type: str
    content: str
    thinking_and_activity_info: dict
    is_final: bool
    tool_info: dict[str, Any] | None = ...
    metadata: dict[str, Any] | None = ...
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format for yielding."""

@dataclass
class StreamingState:
    """State management for streaming operations."""
    debug_url: str
    recording_url: str
    step_count: int = ...
    is_complete: bool = ...
    session_id: str | None = ...
    terminal_error: str | None = ...
    recording_started: bool = ...

@dataclass
class RetryDecision:
    """Encapsulate retry metadata when Steel sessions need to be restarted."""
    retries_remaining: int
    attempted_retries: int
    message: str
    delay: float
