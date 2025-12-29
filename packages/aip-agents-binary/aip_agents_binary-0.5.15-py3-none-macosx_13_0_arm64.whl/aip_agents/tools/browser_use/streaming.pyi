from aip_agents.tools.browser_use.types import StreamingResponse, ToolCallInfo
from browser_use import Agent
from typing import Any, Literal

__all__ = ['PROCESSING_MESSAGE', 'TASK_COMPLETED_MESSAGE', 'create_error_response', 'create_step_response', 'generate_step_content', 'generate_thinking_message', 'yield_iframe_activity', 'yield_status_message', 'yield_thinking_marker']

TASK_COMPLETED_MESSAGE: str
PROCESSING_MESSAGE: str

def create_step_response(agent: Agent, tool_calls: list[ToolCallInfo], is_done: bool, content: str, thinking_message: str | None) -> StreamingResponse:
    """Compose the per-step payload emitted during browser-use streaming.

    Args:
        agent: Browser-use agent producing the step output.
        tool_calls: Tool call descriptors extracted from the step.
        is_done: Flag indicating whether this is the final step in the run.
        content: High-level status text describing the step progress.
        thinking_message: Optional preformatted thinking summary to attach.

    Returns:
        StreamingResponse: Serialized payload for the current streaming step.
    """
async def generate_thinking_message(content: str, tool_calls: list[dict[str, Any]], *, is_final: bool) -> str | None:
    """Generate a user-facing thinking summary using the formatter LLM when available.

    Args:
        content: High-level status text describing the step progress.
        tool_calls: Serialized tool call dictionaries with outputs.
        is_final: Whether the task has completed.

    Returns:
        Markdown-formatted summary string, or ``None`` when not applicable.
    """
def create_error_response(error_message: str, recording_url: str = '') -> dict:
    """Create a standardized error response.

    Args:
        error_message: The error message to include.
        recording_url: The recording URL if available.

    Returns:
        dict: Standardized error response.
    """
def generate_step_content(tool_calls: list[ToolCallInfo], is_done: bool) -> str:
    """Return user-friendly status text derived from tool call outputs.

    Args:
        tool_calls: Tool call descriptors extracted from the step.
        is_done: Flag indicating whether this is the final step in the run.

    Returns:
        User-friendly status text string.
    """
def yield_iframe_activity(url: str, content: str) -> dict:
    """Create and return an iframe activity streaming response.

    Args:
        url: The URL to display in the iframe.
        content: The content message for the response.

    Returns:
        dict: Streaming response dictionary.
    """
def yield_status_message(content: str) -> dict:
    """Create a status update event notifying clients about recovery attempts.

    Args:
        content: The status message content to include in the event.

    Returns:
        dict: Streaming response dictionary for the status update event.
    """
def yield_thinking_marker(marker_type: Literal['start', 'end']) -> dict:
    """Create and return a thinking marker streaming response.

    Args:
        marker_type: Either 'start' or 'end' to indicate thinking phase.

    Returns:
        dict: Streaming response dictionary.
    """
