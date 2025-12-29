"""Shared data structures for the browser-use tool.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


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
    tool_info: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format for yielding."""
        return {
            "event_type": self.event_type,
            "content": self.content,
            "thinking_and_activity_info": self.thinking_and_activity_info,
            "tool_info": self.tool_info,
            "is_final": self.is_final,
            "metadata": self.metadata,
        }


@dataclass
class StreamingState:
    """State management for streaming operations."""

    debug_url: str
    recording_url: str
    step_count: int = 0
    is_complete: bool = False
    session_id: str | None = None
    terminal_error: str | None = None
    recording_started: bool = False


@dataclass
class RetryDecision:
    """Encapsulate retry metadata when Steel sessions need to be restarted."""

    retries_remaining: int
    attempted_retries: int
    message: str
    delay: float


__all__ = [
    "BrowserUseFatalError",
    "RetryDecision",
    "StreamingResponse",
    "StreamingState",
    "ToolCallInfo",
]
