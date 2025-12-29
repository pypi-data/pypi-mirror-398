"""SSE Chunk Transformer for converting A2AEvent stream to SSE-compatible output.

This module provides the SSEChunkTransformer class that transforms A2AEvent objects
into SSE-compatible chunks, enabling direct streaming without A2A server overhead.

The transformer consolidates normalization logic shared with A2AConnector and provides
both static utilities and instance methods for stream transformation.

Authors:
    AI Agent Platform Team
"""

from __future__ import annotations

__all__ = [
    "SSEChunkTransformer",
    "TaskState",
    "ChunkStatus",
    "ChunkReason",
    "ChunkFieldKeys",
]

import hashlib
import time
import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from enum import Enum, StrEnum
from typing import Any

from aip_agents.schema.a2a import A2AEvent, A2AStreamEventType
from aip_agents.utils.logger import get_logger
from aip_agents.utils.metadata_helper import (
    MetadataFieldKeys,
    MetadataTimeTracker,
    Status,
    create_metadata,
    create_status_update_metadata,
    create_tool_processing_metadata,
)
from aip_agents.utils.reference_helper import serialize_references_for_metadata

logger = get_logger(__name__)


# =============================================================================
# Type-safe constants for SSE chunk structure
# =============================================================================


class TaskState(StrEnum):
    """Task state values for SSE chunks."""

    WORKING = "working"
    COMPLETED = "completed"
    FAILED = "failed"


class ChunkStatus(StrEnum):
    """Status values for SSE chunks."""

    SUCCESS = "success"
    ERROR = "error"


class ChunkReason(StrEnum):
    """Reason codes for special chunk states."""

    EMPTY_PAYLOAD = "empty_payload"


class ChunkFieldKeys(StrEnum):
    """Field name constants for SSE chunk structure."""

    STATUS = "status"
    TASK_STATE = "task_state"
    CONTENT = "content"
    EVENT_TYPE = "event_type"
    FINAL = "final"
    METADATA = "metadata"
    TIMESTAMP = "timestamp"
    TASK_ID = "task_id"
    CONTEXT_ID = "context_id"
    ARTIFACTS = "artifacts"
    REASON = "reason"


# Event type to task state mapping
_EVENT_TYPE_TO_TASK_STATE: dict[A2AStreamEventType | str, str] = {
    A2AStreamEventType.STATUS_UPDATE: TaskState.WORKING,
    A2AStreamEventType.CONTENT_CHUNK: TaskState.WORKING,
    A2AStreamEventType.TOOL_CALL: TaskState.WORKING,
    A2AStreamEventType.TOOL_RESULT: TaskState.WORKING,
    A2AStreamEventType.FINAL_RESPONSE: TaskState.COMPLETED,
    A2AStreamEventType.ERROR: TaskState.FAILED,
    A2AStreamEventType.STEP_LIMIT_EXCEEDED: TaskState.FAILED,
    "status_update": TaskState.WORKING,
    "content_chunk": TaskState.WORKING,
    "tool_call": TaskState.WORKING,
    "tool_result": TaskState.WORKING,
    "final_response": TaskState.COMPLETED,
    "error": TaskState.FAILED,
    "step_limit_exceeded": TaskState.FAILED,
}

# Event types that indicate final events
_FINAL_EVENT_TYPES: set[A2AStreamEventType | str] = {
    A2AStreamEventType.FINAL_RESPONSE,
    A2AStreamEventType.ERROR,
    A2AStreamEventType.STEP_LIMIT_EXCEEDED,
    "final_response",
    "error",
    "step_limit_exceeded",
}


class SSEChunkTransformer:
    """Transforms A2AEvent stream to SSE-compatible output.

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
    """

    def __init__(
        self,
        task_id: str | None = None,
        context_id: str | None = None,
        pii_mapping: dict[str, str] | None = None,
    ) -> None:
        """Initialize the transformer with optional task and context IDs.

        Args:
            task_id: Optional task identifier for the stream.
            context_id: Optional context identifier for the stream.
            pii_mapping: Optional PII mapping to inject into each chunk's metadata.
        """
        self.task_id = task_id
        self.context_id = context_id
        # Accumulated pii_mapping - starts with initial value and merges event pii_mapping
        self._pii_mapping: dict[str, str] = dict(pii_mapping) if pii_mapping else {}
        self._seen_artifact_hashes: set[str] = set()
        self._collected_artifacts: list[dict[str, Any]] = []  # Track artifacts for final response
        self._time_tracker = MetadataTimeTracker()
        self._first_content_yielded: bool = False
        self._start_time: float | None = None  # Track start time for cumulative time calculation

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
        if isinstance(data, Enum):
            return data.value
        if isinstance(data, dict):
            return SSEChunkTransformer._normalize_dict(data)
        if isinstance(data, list | tuple | set):
            return [SSEChunkTransformer.normalize_metadata_enums(item) for item in data]
        return data

    @staticmethod
    def _normalize_dict(data: dict[Any, Any]) -> dict[str, Any]:
        """Normalize a dictionary by converting enum keys and values.

        Args:
            data: Dictionary to normalize.

        Returns:
            New dictionary with normalized keys and values.
        """
        normalized: dict[str, Any] = {}
        for key, value in data.items():
            normalized_key = key.value if isinstance(key, Enum) else key
            normalized_value = SSEChunkTransformer.normalize_metadata_enums(value)
            normalized[normalized_key] = normalized_value
        return normalized

    @staticmethod
    def normalize_event_type_value(event_type: Any) -> str | None:
        """Convert A2AStreamEventType enum to string.

        Args:
            event_type: Event type (enum, string, or None).

        Returns:
            String value of the event type, or None if invalid.
        """
        if event_type is None:
            return None
        if isinstance(event_type, A2AStreamEventType):
            return event_type.value
        if isinstance(event_type, str):
            return event_type
        return None

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
        hash_data = {
            "name": artifact.get("artifact_name") or artifact.get("name"),
            "content_type": artifact.get("content_type"),
            "mime_type": artifact.get("mime_type"),
        }

        # Include file_data for accurate deduplication if available
        file_data = artifact.get("file_data")
        if file_data is not None:
            hash_data["file_data"] = file_data
        else:
            # Fallback to file_uri if file_data is not available
            file_uri = artifact.get("file_uri")
            if file_uri is not None:
                hash_data["file_uri"] = file_uri

        hash_string = str(sorted(hash_data.items()))
        return hashlib.sha256(hash_string.encode()).hexdigest()

    @staticmethod
    def extract_tool_outputs(tool_calls: list[dict[str, Any]]) -> list[str]:
        """Extract human-readable output strings from tool calls.

        Args:
            tool_calls: List of tool call dictionaries.

        Returns:
            List of human-readable output strings.
        """
        outputs: list[str] = []
        for tool_call in tool_calls:
            output = tool_call.get("output")
            if isinstance(output, str):
                outputs.append(output)
            elif isinstance(output, dict):
                # Attempt to extract human-readable content field before falling back
                content = output.get("content") if isinstance(output.get("content"), str) else None
                outputs.append(content if content else str(output))
            else:
                # For other types, convert to string
                outputs.append(str(output))
        return outputs

    @staticmethod
    def format_tool_output(output: Any, tool_name: str) -> str:
        """Format a single tool output for display.

        Args:
            output: The tool output to format.
            tool_name: The name of the tool.

        Returns:
            The formatted output string.
        """
        if output is None:
            return f"Completed {tool_name}"
        if isinstance(output, str):
            return output
        elif isinstance(output, dict):
            content = output.get("content") if isinstance(output.get("content"), str) else None
            return content if content else str(output)
        else:
            return str(output)

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
        # Only apply override for tool_result events with HITL metadata
        if event_type_str != A2AStreamEventType.TOOL_RESULT.value:
            return content

        if not isinstance(metadata.get("hitl"), dict):
            return content

        tool_info = metadata.get(MetadataFieldKeys.TOOL_INFO)
        if not isinstance(tool_info, dict):
            return content

        # Handle multi-tool case
        if "tool_calls" in tool_info:
            outputs = SSEChunkTransformer.extract_tool_outputs(tool_info["tool_calls"])
            if outputs:
                return "\n".join(outputs)

        # Handle single-tool case
        elif "output" in tool_info:
            formatted_output = SSEChunkTransformer.format_tool_output(
                tool_info.get("output"), tool_info.get("name", "")
            )
            if formatted_output and not formatted_output.startswith("Completed"):
                return formatted_output

        return content

    @staticmethod
    def _create_error_chunk(message: str) -> dict[str, Any]:
        """Create a terminal error chunk matching A2AConnector._create_error_response().

        Args:
            message: Error message to include.

        Returns:
            Error chunk dict.
        """
        return {
            ChunkFieldKeys.STATUS: ChunkStatus.ERROR,
            ChunkFieldKeys.TASK_STATE: TaskState.FAILED,
            ChunkFieldKeys.CONTENT: message,
            ChunkFieldKeys.EVENT_TYPE: A2AStreamEventType.ERROR.value,
            ChunkFieldKeys.FINAL: True,
            ChunkFieldKeys.METADATA: {},
        }

    def _validate_event(self, event: dict[str, Any]) -> str | None:
        """Validate required event fields.

        Args:
            event: Event dict to validate.

        Returns:
            Error message if validation fails, None if valid.
        """
        required_fields = [
            ChunkFieldKeys.EVENT_TYPE,
            ChunkFieldKeys.CONTENT,
            ChunkFieldKeys.METADATA,
        ]
        missing = [f for f in required_fields if f not in event]
        if missing:
            return f"Malformed event: missing required field(s): {', '.join(missing)}"
        return None

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
        # Validate required fields
        validation_error = self._validate_event(event)  # type: ignore[arg-type]
        if validation_error:
            return self._create_error_chunk(validation_error)

        # Extract event properties
        raw_event_type = event.get("event_type")
        event_type_str = self._resolve_event_type(raw_event_type)
        task_state = _EVENT_TYPE_TO_TASK_STATE.get(raw_event_type, TaskState.WORKING)
        is_final = raw_event_type in _FINAL_EVENT_TYPES or event.get("is_final", False)
        status = self._determine_status(raw_event_type, event_type_str)
        content, reason = self._extract_content(event)
        timestamp = datetime.now(UTC).isoformat()

        # Build chunk
        chunk = self._build_base_chunk(status, task_state, content, event_type_str, is_final, timestamp, reason, event)

        # Apply HITL content override if applicable (must happen after metadata is built)
        metadata = chunk.get(ChunkFieldKeys.METADATA, {})
        if isinstance(metadata, dict):
            overridden_content = self.apply_hitl_content_override(
                chunk.get(ChunkFieldKeys.CONTENT), event_type_str, metadata
            )
            if overridden_content != chunk.get(ChunkFieldKeys.CONTENT):
                chunk[ChunkFieldKeys.CONTENT] = overridden_content
                # Clear empty_payload reason if content was overridden
                if chunk.get(ChunkFieldKeys.REASON) == ChunkReason.EMPTY_PAYLOAD:
                    chunk.pop(ChunkFieldKeys.REASON, None)

        # Handle artifacts
        self._process_artifacts(event, chunk, is_final)

        return chunk

    def _resolve_event_type(self, raw_event_type: Any) -> str:
        """Resolve and normalize event type to string.

        Args:
            raw_event_type: Event type value from the incoming event.

        Returns:
            Normalized string representation of the event type.
        """
        event_type_str = self.normalize_event_type_value(raw_event_type)
        if event_type_str is None:
            event_type_str = str(raw_event_type) if raw_event_type else "unknown"
            logger.warning(f"Unknown event type: {raw_event_type}, passing through as '{event_type_str}'")
        return event_type_str

    def _determine_status(self, raw_event_type: Any, event_type_str: str) -> ChunkStatus:
        """Determine chunk status based on event type.

        Args:
            raw_event_type: Raw event type value as provided in the event.
            event_type_str: Normalized event type string.

        Returns:
            ChunkStatus reflecting success or error.
        """
        is_error = (
            raw_event_type == A2AStreamEventType.ERROR
            or event_type_str == A2AStreamEventType.ERROR.value
            or raw_event_type == A2AStreamEventType.STEP_LIMIT_EXCEEDED
            or event_type_str == A2AStreamEventType.STEP_LIMIT_EXCEEDED.value
        )
        return ChunkStatus.ERROR if is_error else ChunkStatus.SUCCESS

    def _extract_content(self, event: A2AEvent) -> tuple[str | None, str | None]:
        """Extract content and reason from event.

        Args:
            event: Source A2AEvent containing content.

        Returns:
            Tuple of normalized content and optional reason when content is empty.
        """
        content: str | None = event.get("content")  # type: ignore[assignment]
        reason: str | None = None
        if content == "" or content is None:
            content = None
            reason = ChunkReason.EMPTY_PAYLOAD
        return content, reason

    def _build_base_chunk(
        self,
        status: ChunkStatus,
        task_state: str,
        content: str | None,
        event_type_str: str,
        is_final: bool,
        timestamp: str,
        reason: str | None,
        event: A2AEvent,
    ) -> dict[str, Any]:
        """Build the base chunk dictionary.

        Args:
            status: Chunk status derived from event type.
            task_state: Task state derived from event type.
            content: Text content to include in the chunk.
            event_type_str: Normalized event type string.
            is_final: Whether this is the final chunk in the stream.
            timestamp: ISO timestamp for the chunk.
            reason: Optional reason describing special states.
            event: Original event for metadata extraction.

        Returns:
            Base SSE chunk dictionary with core fields populated.
        """
        metadata = self._build_metadata(event, timestamp)
        chunk: dict[str, Any] = {
            ChunkFieldKeys.STATUS: status,
            ChunkFieldKeys.TASK_STATE: task_state,
            ChunkFieldKeys.CONTENT: content,
            ChunkFieldKeys.EVENT_TYPE: event_type_str,
            ChunkFieldKeys.FINAL: is_final,
            ChunkFieldKeys.METADATA: metadata,
            ChunkFieldKeys.TIMESTAMP: timestamp,
        }
        if reason:
            chunk[ChunkFieldKeys.REASON] = reason
        if self.task_id:
            chunk[ChunkFieldKeys.TASK_ID] = self.task_id
        if self.context_id:
            chunk[ChunkFieldKeys.CONTEXT_ID] = self.context_id
        return chunk

    def _process_artifacts(self, event: A2AEvent, chunk: dict[str, Any], is_final: bool) -> None:
        """Process and add artifacts to chunk.

        Args:
            event: Source A2AEvent possibly containing artifacts.
            chunk: Chunk being constructed.
            is_final: Whether the current event marks the end of the stream.
        """
        artifacts = event.get("artifacts")
        if artifacts:
            unique_artifacts = self._deduplicate_and_collect_artifacts(artifacts)
            if unique_artifacts:
                chunk[ChunkFieldKeys.ARTIFACTS] = unique_artifacts

        # For final response, include all collected artifacts (matching connector behavior)
        if is_final and self._collected_artifacts:
            self._merge_collected_artifacts(chunk)

    def _merge_collected_artifacts(self, chunk: dict[str, Any]) -> None:
        """Merge collected artifacts into chunk, avoiding duplicates.

        Args:
            chunk: Chunk to receive merged artifacts.
        """
        existing = chunk.get(ChunkFieldKeys.ARTIFACTS, [])
        existing_ids = {a.get("artifact_id") for a in existing}
        for artifact in self._collected_artifacts:
            if artifact.get("artifact_id") not in existing_ids:
                existing.append(artifact)
        if existing:
            chunk[ChunkFieldKeys.ARTIFACTS] = existing

    def _build_metadata(self, event: A2AEvent, timestamp: str) -> dict[str, Any]:
        """Build normalized metadata with relocated fields and enrichment.

        Enriches metadata to match A2AConnector.astream_to_agent output by adding
        kind, message, thinking_and_activity_info, and timestamp fields.

        Args:
            event: Source A2AEvent.
            timestamp: ISO timestamp to include in metadata.

        Returns:
            Normalized and enriched metadata dict matching connector output.
        """
        # Start with existing metadata, normalized, then relocate top-level fields
        existing_metadata = self._prepare_existing_metadata(event)

        # Enrich metadata based on event type
        event_type = event.get("event_type")
        content = event.get("content", "")
        is_final = event_type in _FINAL_EVENT_TYPES or event.get("is_final", False)
        metadata = self._enrich_metadata_by_event_type(event_type, content, is_final, existing_metadata)

        # Normalize and finalize
        metadata = self.normalize_metadata_enums(metadata)
        if "timestamp" not in metadata:
            metadata["timestamp"] = timestamp

        # Add cumulative time to all events (matching A2A server behavior)
        self._apply_cumulative_time(metadata)

        # Relocate thinking_and_activity_info from top-level event if not already present
        self._relocate_thinking_info(event, metadata)

        # Accumulate pii_mapping from event and inject into metadata (matching A2A executor behavior)
        self._accumulate_and_inject_pii_mapping(event, metadata)

        # Match A2AConnector output: status_update chunks should not include pii_mapping
        raw_event_type = event.get("event_type")
        if raw_event_type in (A2AStreamEventType.STATUS_UPDATE, "status_update"):
            metadata.pop(MetadataFieldKeys.PII_MAPPING, None)

        # Add event_type to metadata (matching base_executor behavior)
        event_type_value = event.get("event_type")
        if isinstance(event_type_value, A2AStreamEventType):
            metadata["event_type"] = event_type_value.value
        elif isinstance(event_type_value, str):
            metadata["event_type"] = event_type_value

        return metadata

    def _prepare_existing_metadata(self, event: A2AEvent) -> dict[str, Any]:
        """Prepare existing metadata by normalizing and relocating top-level fields.

        Args:
            event: Source A2AEvent containing metadata and relocatable fields.

        Returns:
            Normalized metadata dictionary with relocated fields.
        """
        raw_metadata = event.get("metadata", {})
        existing = self.normalize_metadata_enums(raw_metadata) if raw_metadata else {}

        # Relocate top-level fields into metadata
        # Note: Using StrEnum for TypedDict keys works at runtime since StrEnum members ARE strings
        fields_to_relocate = [
            MetadataFieldKeys.TOOL_INFO,
            MetadataFieldKeys.STEP_USAGE,
            MetadataFieldKeys.TOTAL_USAGE,
        ]
        for field in fields_to_relocate:
            if event.get(field):  # type: ignore[typeddict-item]
                existing[field] = event[field]  # type: ignore[typeddict-item]

        # Serialize references properly (matching A2AConnector behavior)
        if event.get(MetadataFieldKeys.REFERENCES):  # type: ignore[typeddict-item]
            existing[MetadataFieldKeys.REFERENCES] = serialize_references_for_metadata(
                event[MetadataFieldKeys.REFERENCES]  # type: ignore[typeddict-item]
            )
        return existing

    def _enrich_metadata_by_event_type(
        self,
        event_type: Any,
        content: Any,
        is_final: bool,
        existing_metadata: dict[str, Any],
    ) -> dict[str, Any]:
        """Enrich metadata based on event type to match connector behavior.

        Args:
            event_type: Event type value guiding metadata enrichment.
            content: Content payload associated with the event.
            is_final: Whether the event is the final message in the stream.
            existing_metadata: Metadata accumulated before enrichment.

        Returns:
            Metadata dictionary after enrichment.
        """
        content_str = content if isinstance(content, str) else ""

        if event_type in (A2AStreamEventType.TOOL_CALL, A2AStreamEventType.TOOL_RESULT, "tool_call", "tool_result"):
            return create_tool_processing_metadata(existing_metadata)
        if is_final:
            return create_metadata(
                content=content_str, is_final=True, status=Status.FINISHED, existing_metadata=existing_metadata
            )
        if event_type in (A2AStreamEventType.STATUS_UPDATE, "status_update"):
            return create_status_update_metadata(content=content_str, custom_metadata=existing_metadata)
        return create_metadata(
            content=content_str, is_final=False, status=Status.RUNNING, existing_metadata=existing_metadata
        )

    def _relocate_thinking_info(self, event: A2AEvent, metadata: dict[str, Any]) -> None:
        """Relocate thinking_and_activity_info from top-level event if not already in metadata.

        Args:
            event: Source A2AEvent potentially carrying thinking_and_activity_info.
            metadata: Metadata dict to be enriched with thinking info when absent.
        """
        key = MetadataFieldKeys.THINKING_AND_ACTIVITY_INFO
        if event.get(key) and key not in metadata:  # type: ignore[typeddict-item]
            metadata[key] = event[key]  # type: ignore[typeddict-item]

    def _apply_cumulative_time(self, metadata: dict[str, Any]) -> None:
        """Add cumulative time to metadata.

        Always applies cumulative time since first event was processed,
        matching A2A server behavior in base_executor._apply_cumulative_time().
        This ensures time is always increasing/cumulative across all events.

        Args:
            metadata: Metadata dict to update with cumulative time.
        """
        # Initialize start time on first call
        now = time.monotonic()
        if self._start_time is None:
            self._start_time = now
            elapsed = 0.0
        else:
            elapsed = max(0.0, now - self._start_time)

        # Always set cumulative time to ensure it's always increasing
        time_key = MetadataFieldKeys.TIME
        metadata[time_key] = elapsed

    def _accumulate_and_inject_pii_mapping(self, event: A2AEvent, metadata: dict[str, Any]) -> None:
        """Accumulate pii_mapping from event and inject into metadata.

        This matches A2A executor behavior (langgraph_executor.py:171) where
        current_metadata.update(chunk_metadata) accumulates pii_mapping from
        each event. The accumulated pii_mapping is then injected into each
        chunk's metadata.

        Args:
            event: Source A2AEvent potentially containing pii_mapping in metadata.
            metadata: Metadata dict to update with accumulated pii_mapping.
        """
        # Extract pii_mapping from event metadata and merge into accumulator
        event_metadata = event.get("metadata") or {}
        event_pii = event_metadata.get(MetadataFieldKeys.PII_MAPPING)
        if isinstance(event_pii, dict) and event_pii:
            self._pii_mapping.update(event_pii)

        # Match A2AConnector behavior: status_update metadata does not include pii_mapping
        raw_event_type = event.get("event_type")
        if raw_event_type in (A2AStreamEventType.STATUS_UPDATE, "status_update"):
            return

        # Inject accumulated pii_mapping into chunk metadata
        if self._pii_mapping:
            metadata[MetadataFieldKeys.PII_MAPPING] = self._pii_mapping.copy()

    def _deduplicate_and_collect_artifacts(self, artifacts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Deduplicate artifacts, normalize format, and collect them for final response.

        Args:
            artifacts: List of artifact dicts (may be in direct stream or runner format).

        Returns:
            List of unique artifacts in runner-compatible format.
        """
        unique = []
        for artifact in artifacts:
            # Normalize artifact format from direct stream to runner-expected format
            normalized = self._normalize_artifact_format(artifact)
            artifact_hash = self.create_artifact_hash(normalized)
            if artifact_hash not in self._seen_artifact_hashes:
                self._seen_artifact_hashes.add(artifact_hash)
                unique.append(normalized)
                # Collect for final response (matching connector behavior)
                self._collected_artifacts.append(normalized)
        return unique

    @staticmethod
    def _normalize_artifact_format(artifact: dict[str, Any]) -> dict[str, Any]:
        """Normalize artifact from direct stream format to ArtifactInfo-compatible format.

        Converts artifacts from ArtifactHandler format (used by arun_a2a_stream):
            {"artifact_type": "file", "data": "base64...", "name": "...", "mime_type": "..."}

        To ArtifactInfo-compatible format (matching A2AConnector output):
            {"artifact_id": "uuid", "name": "...", "content_type": "file", "mime_type": "...",
             "file_name": "...", "has_file_data": True, "has_file_uri": False,
             "file_data": "base64...", "file_uri": None, "description": "...", "parts": None}

        Args:
            artifact: Artifact dict in either format.

        Returns:
            Artifact dict in ArtifactInfo-compatible format.
        """
        normalized = artifact.copy()

        # Convert 'data' → 'file_data'
        if "data" in normalized and "file_data" not in normalized:
            normalized["file_data"] = normalized.pop("data")

        # Generate artifact_id if missing
        if not normalized.get("artifact_id"):
            normalized["artifact_id"] = str(uuid.uuid4())

        # Set file_name from name if not present
        if "name" in normalized and "file_name" not in normalized:
            normalized["file_name"] = normalized["name"]

        # Convert 'artifact_type' → 'content_type' and remove artifact_type
        if "artifact_type" in normalized:
            if "content_type" not in normalized:
                normalized["content_type"] = normalized["artifact_type"]
            del normalized["artifact_type"]

        # Remove 'artifact_name' if present (connector uses 'name' instead)
        normalized.pop("artifact_name", None)

        # Remove 'metadata' if present (not in ArtifactInfo model)
        normalized.pop("metadata", None)

        # Set has_file_data/has_file_uri flags
        if "has_file_data" not in normalized:
            normalized["has_file_data"] = bool(normalized.get("file_data"))
        if "has_file_uri" not in normalized:
            normalized["has_file_uri"] = bool(normalized.get("file_uri"))

        # Add missing fields with None defaults for ArtifactInfo compatibility
        if "file_uri" not in normalized:
            normalized["file_uri"] = None
        if "parts" not in normalized:
            normalized["parts"] = None
        if "description" not in normalized:
            normalized["description"] = None

        return normalized

    async def transform_stream(
        self,
        stream: AsyncGenerator[A2AEvent, None],
    ) -> AsyncGenerator[dict[str, Any], None]:
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
        async for event in stream:
            chunk = self.transform_event(event)

            # Update time tracker with the response
            chunk = self._time_tracker.update_response_metadata(chunk)

            yield chunk

            # Terminate stream after yielding malformed-event error chunk
            # Malformed events produce error chunks with empty metadata from _create_error_chunk
            if (
                chunk.get(ChunkFieldKeys.STATUS) == ChunkStatus.ERROR
                and chunk.get(ChunkFieldKeys.CONTENT, "").startswith("Malformed event:")
                and chunk.get(ChunkFieldKeys.METADATA) == {}
            ):
                break
