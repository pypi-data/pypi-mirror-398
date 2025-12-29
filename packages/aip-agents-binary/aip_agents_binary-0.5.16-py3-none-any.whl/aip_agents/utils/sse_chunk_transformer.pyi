from _typeshed import Incomplete
from aip_agents.schema.a2a import A2AEvent
from collections.abc import AsyncGenerator
from enum import StrEnum
from typing import Any

__all__ = ['SSEChunkTransformer', 'TaskState', 'ChunkStatus', 'ChunkReason', 'ChunkFieldKeys']

class TaskState(StrEnum):
    """Task state values for SSE chunks."""
    WORKING: str
    COMPLETED: str
    FAILED: str

class ChunkStatus(StrEnum):
    """Status values for SSE chunks."""
    SUCCESS: str
    ERROR: str

class ChunkReason(StrEnum):
    """Reason codes for special chunk states."""
    EMPTY_PAYLOAD: str

class ChunkFieldKeys(StrEnum):
    """Field name constants for SSE chunk structure."""
    STATUS: str
    TASK_STATE: str
    CONTENT: str
    EVENT_TYPE: str
    FINAL: str
    METADATA: str
    TIMESTAMP: str
    TASK_ID: str
    CONTEXT_ID: str
    ARTIFACTS: str
    REASON: str

class SSEChunkTransformer:
    '''Transforms A2AEvent stream to SSE-compatible output.

    This class converts events from arun_a2a_stream into the normalized dict format
    matching A2AConnector.astream_to_agent output.

    Lifecycle:
        Single-stream instance. Must NOT be reused across concurrent streams.
        Each arun_sse_stream call creates a fresh instance.

    Attributes:
        task_id: Optional task identifier for the stream.
        context_id: Optional context identifier for the stream.

    Example:
        >>> transformer = SSEChunkTransformer(task_id="task-123")
        >>> async for chunk in transformer.transform_stream(agent.arun_a2a_stream("query")):
        ...     print(chunk)
    '''
    task_id: Incomplete
    context_id: Incomplete
    def __init__(self, task_id: str | None = None, context_id: str | None = None, pii_mapping: dict[str, str] | None = None) -> None:
        """Initialize the transformer with optional task and context IDs.

        Args:
            task_id: Optional task identifier for the stream.
            context_id: Optional context identifier for the stream.
            pii_mapping: Optional PII mapping to inject into each chunk's metadata.
        """
    @staticmethod
    def normalize_metadata_enums(data: Any) -> Any:
        """Recursively convert enum keys/values to their string values.

        This is a pure normalization utility that converts any enum instances
        (MetadataFieldKeys, Kind, Status, etc.) to their .value strings.

        Args:
            data: Dict, list, or value that may contain enum keys/values.

        Returns:
            Normalized data with all enums converted to their .value strings.
        """
    @staticmethod
    def normalize_event_type_value(event_type: Any) -> str | None:
        """Convert A2AStreamEventType enum to string.

        Args:
            event_type: Event type (enum, string, or None).

        Returns:
            String value of the event type, or None if invalid.
        """
    @staticmethod
    def create_artifact_hash(artifact: dict[str, Any]) -> str:
        """Create a stable hash for artifact deduplication.

        Uses name, content_type, mime_type, and file_data for hashing,
        excluding artifact_id which may be randomly generated.

        Args:
            artifact: Artifact dict with name, content_type, mime_type, and optionally file_data.

        Returns:
            SHA256 hexdigest hash string for deduplication.
        """
    @staticmethod
    def extract_tool_outputs(tool_calls: list[dict[str, Any]]) -> list[str]:
        """Extract human-readable output strings from tool calls.

        Args:
            tool_calls: List of tool call dictionaries.

        Returns:
            List of human-readable output strings.
        """
    @staticmethod
    def format_tool_output(output: Any, tool_name: str) -> str:
        """Format a single tool output for display.

        Args:
            output: The tool output to format.
            tool_name: The name of the tool.

        Returns:
            The formatted output string.
        """
    @staticmethod
    def apply_hitl_content_override(content: str | None, event_type_str: str, metadata: dict[str, Any]) -> str | None:
        """Apply HITL content override when HITL is active and tool results are available.

        This method overrides the content with human-readable tool output when HITL
        is active, matching A2AConnector behavior.

        Args:
            content: The original content/status message.
            event_type_str: The type of event being processed (normalized string).
            metadata: The metadata dictionary containing tool_info and hitl flag.

        Returns:
            The original content or human-readable tool output if HITL is active.
        """
    def transform_event(self, event: A2AEvent) -> dict[str, Any]:
        """Transform a single A2AEvent to SSE chunk format.

        Converts the A2AEvent structure to the normalized SSE chunk format,
        relocating fields like tool_info and thinking_and_activity_info into
        metadata, and normalizing enum values to strings.

        Args:
            event: Single A2AEvent dict from arun_a2a_stream.

        Returns:
            SSEChunk dict with normalized structure.
        """
    async def transform_stream(self, stream: AsyncGenerator[A2AEvent, None]) -> AsyncGenerator[dict[str, Any], None]:
        """Transform A2AEvent stream to SSE-compatible chunks.

        Wraps the input stream and transforms each event, handling artifact
        deduplication and time tracking across the stream.

        Args:
            stream: Async generator yielding A2AEvent dicts.

        Yields:
            SSEChunk dicts with normalized structure.

        Raises:
            Exceptions from underlying stream propagate to caller.
        """
