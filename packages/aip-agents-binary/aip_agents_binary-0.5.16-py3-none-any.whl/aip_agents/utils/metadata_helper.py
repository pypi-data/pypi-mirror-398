"""Helper functions for creating and handling metadata for A2A communication.

Authors:
    Fachriza Adhiatma (fachriza.d.adhiatma@gdplabs.id)
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from contextvars import ContextVar
from enum import StrEnum
from typing import Any

from aip_agents.utils.logger import get_logger
from aip_agents.utils.metadata import (
    create_tool_activity_info,
)
from aip_agents.utils.token_usage_helper import (
    STEP_USAGE_KEY,
    TOTAL_USAGE_KEY,
)

logger = get_logger(__name__)

_STEP_COUNTER_STATE_CVAR: ContextVar[dict[str, int] | None] = ContextVar("gllm_step_counter_state", default=None)


def _ensure_step_counter_state() -> dict[str, int]:
    """Get or initialize step counter state for the current async context.

    Returns:
        dict[str, int]: Dictionary containing 'count' and 'depth' keys for step tracking.
    """
    state = _STEP_COUNTER_STATE_CVAR.get()
    if state is None:
        state = {"count": 0, "depth": 0}
        _STEP_COUNTER_STATE_CVAR.set(state)
    return state


def start_step_counter_scope(start: int = 1) -> None:
    """Begin a step counter scope, resetting only when entering the outermost scope.

    Args:
        start: Starting step number for the counter. Defaults to 1.
    """
    state = _ensure_step_counter_state()
    if state["depth"] == 0:
        state["count"] = start - 1
    state["depth"] += 1


def end_step_counter_scope() -> None:
    """Exit a step counter scope, maintaining parent scope counters.

    Decrements the depth counter while preserving the step count for parent scopes.
    """
    state = _ensure_step_counter_state()
    if state["depth"] > 0:
        state["depth"] -= 1


def get_next_step_number() -> int:
    """Return the next step number within the active scope.

    Returns:
        int: The next sequential step number in the current scope.
    """
    state = _ensure_step_counter_state()
    state["count"] += 1
    return state["count"]


class DefaultStepMessages(StrEnum):
    """Constants for default step indicator messages."""

    EN = "Performing agent tasks"
    ID = "Melakukan tugas agen"


class Kind(StrEnum):
    """Constants for metadata kind values."""

    AGENT_STEP = "agent_step"
    AGENT_THINKING_STEP = "agent_thinking_step"
    FINAL_RESPONSE = "final_response"
    FINAL_THINKING_STEP = "final_agent_thinking_step"
    AGENT_DEFAULT = "agent_default"
    TOKEN = "token"


class Status(StrEnum):
    """Constants for metadata status values."""

    RUNNING = "running"
    FINISHED = "finished"
    STOPPED = "stopped"


class MetadataFieldKeys(StrEnum):
    """Enumeration of standard metadata field keys used in A2A events."""

    KIND = "kind"
    STATUS = "status"
    TIME = "time"
    MESSAGE = "message"
    TOOL_INFO = "tool_info"
    REFERENCES = "references"
    THINKING_AND_ACTIVITY_INFO = "thinking_and_activity_info"
    HITL = "hitl"
    STEP_USAGE = STEP_USAGE_KEY
    TOTAL_USAGE = TOTAL_USAGE_KEY
    TOKEN_STREAMING = "token_streaming"
    PII_MAPPING = "pii_mapping"


class MetadataTimeTracker:
    """Tracks cumulative execution time across agent steps for final response metadata.

    This class provides a clean way to accumulate execution times from individual
    agent steps and apply the total time to final response metadata.

    Attributes:
        FLOAT_EPSILON: Epsilon value for floating point comparisons to avoid precision issues.
    """

    # Epsilon value for floating point comparisons to avoid precision issues
    FLOAT_EPSILON = 1e-10

    def __init__(self):
        """Initialize the time tracker with zero accumulated time."""
        self._total_agent_step_time = 0.0
        self._last_seen_time: float = 0.0

    def _track_response_time(self, metadata: dict[str, Any]) -> None:
        """Track and update time from response metadata.

        Args:
            metadata: Response metadata dictionary containing time information.
        """
        try:
            t = metadata.get(MetadataFieldKeys.TIME) if isinstance(metadata, dict) else None
            # Accept both enum key and string key variants
            if t is None and isinstance(metadata, dict):
                t = metadata.get(MetadataFieldKeys.TIME)
            if isinstance(t, int | float) and t > 0:
                self._last_seen_time = float(t)
        except Exception:
            pass

    def _set_final_response_time(self, metadata: dict[str, Any]) -> None:
        """Set time for final responses if missing or zero.

        Args:
            metadata: Response metadata dictionary to update with time information.
        """
        current_time = metadata.get(MetadataFieldKeys.TIME, 0.0) if isinstance(metadata, dict) else 0.0
        if not isinstance(current_time, int | float) or abs(current_time) < self.FLOAT_EPSILON:
            # Prefer last seen non-zero time from stream; otherwise fall back to accumulated agent step time
            metadata[MetadataFieldKeys.TIME] = (
                self._last_seen_time if self._last_seen_time > 0 else self._get_total_time()
            )

    def _accumulate_agent_step_time(self, metadata: dict[str, Any]) -> None:
        """Accumulate execution time from agent step metadata only.

        Args:
            metadata: Metadata dictionary from an agent step response containing time information.
        """
        try:
            kind = metadata.get(MetadataFieldKeys.KIND)
            status = metadata.get(MetadataFieldKeys.STATUS)
            # Only accumulate time for agent steps, not final responses
            if kind == Kind.AGENT_STEP and status == Status.FINISHED:
                self._total_agent_step_time += float(metadata.get(MetadataFieldKeys.TIME, 0.0))
        except Exception:
            pass

    def _get_total_time(self) -> float:
        """Get the current total accumulated time.

        Returns:
            float: The total accumulated execution time in seconds.
        """
        return self._total_agent_step_time

    def update_response_metadata(self, response: dict[str, Any]) -> dict[str, Any]:
        """Update response metadata with accumulated time tracking.

        Args:
            response: Response dictionary containing metadata to update.

        Returns:
            dict[str, Any]: Response with updated metadata for final responses. If any error occurs,
                returns the original response unchanged.
        """
        try:
            if self._should_skip_metadata_update(response):
                return response

            metadata = response["metadata"]

            # Track time from response metadata
            self._track_response_time(metadata)

            # Maintain legacy accumulation for agent steps
            self._accumulate_agent_step_time(metadata)

            # Set time for final responses if needed
            if self._is_final_response(response, metadata):
                self._set_final_response_time(metadata)

            return response
        except Exception as e:
            logger.warning(f"Failed to update response metadata with time tracking: {e}")
            return response

    def _should_skip_metadata_update(self, response: dict[str, Any]) -> bool:
        """Check if metadata update should be skipped.

        Args:
            response: Response dictionary to check.

        Returns:
            bool: True if update should be skipped, False otherwise.
        """
        return response is None or "metadata" not in response

    def _is_final_response(self, response: dict[str, Any], metadata: dict[str, Any]) -> bool:
        """Check if this is a final response that needs time setting.

        Args:
            response: Response dictionary to check.
            metadata: Response metadata dictionary to check.

        Returns:
            bool: True if this is a final response requiring time update.
        """
        return response.get("final", False) and metadata.get(MetadataFieldKeys.KIND) == Kind.FINAL_RESPONSE


def _create_message_metadata(
    en_content: str = DefaultStepMessages.EN.value, id_content: str = DefaultStepMessages.ID.value
) -> dict[str, str]:
    """Create a message metadata dictionary with English and Indonesian content.

    Args:
        en_content: English content. Defaults to DefaultStepMessages.EN.value.
        id_content: Indonesian content. Defaults to DefaultStepMessages.ID.value.

    Returns:
        dict[str, str]: Dictionary with language codes as keys and translated content as values.
    """
    return {"en": en_content, "id": id_content}


def create_metadata(
    content: str = "",
    status: Status = Status.RUNNING,
    is_final: bool = False,
    existing_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create metadata for A2A responses with content-based message.

    Args:
        content: The content to create metadata for.
        status: The status of the content.
        is_final: Whether the content is final.
        existing_metadata: Optional existing metadata to merge with. Existing metadata
            takes precedence over generated metadata for conflicting keys.

    Returns:
        dict[str, Any]: The metadata for the content, merged with existing metadata if provided.
    """
    if is_final:
        detected_kind = Kind.FINAL_RESPONSE
        message_content = _create_message_metadata(
            en_content=DefaultStepMessages.EN.value, id_content=DefaultStepMessages.ID.value
        )
        final_status = Status.FINISHED if status == Status.RUNNING else status
        base_metadata = {
            MetadataFieldKeys.KIND: detected_kind,
            MetadataFieldKeys.MESSAGE: message_content,
            MetadataFieldKeys.STATUS: final_status,
        }
    else:
        detected_kind = Kind.AGENT_DEFAULT
        final_status = status
        base_metadata = {
            MetadataFieldKeys.KIND: detected_kind,
            MetadataFieldKeys.STATUS: final_status,
        }

    # Merge with existing metadata if provided
    if existing_metadata and isinstance(existing_metadata, dict):
        if is_final:
            return {**existing_metadata, **base_metadata}
        return {**base_metadata, **existing_metadata}

    return base_metadata


def create_tool_processing_metadata(original_metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    """Create metadata for tool processing events (tool_call and tool_result).

    Args:
        original_metadata: Optional original metadata to merge with.

    Returns:
        dict[str, Any]: Metadata dictionary with agent_thinking_step kind and no message/time/status.
    """
    metadata = {
        MetadataFieldKeys.KIND: Kind.AGENT_THINKING_STEP,
    }

    if original_metadata:
        original = original_metadata.copy()
        original.update(metadata)
        metadata = original

    if MetadataFieldKeys.THINKING_AND_ACTIVITY_INFO not in metadata:
        thinking_and_activity_info = create_tool_activity_info(original_metadata)
        metadata[MetadataFieldKeys.THINKING_AND_ACTIVITY_INFO] = thinking_and_activity_info

    return metadata


def create_status_update_metadata(content: str, custom_metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    """Create metadata for status update events with content-based rules.

    Args:
        content: The content of the status update.
        custom_metadata: Optional custom metadata to merge with.

    Returns:
        dict[str, Any]: Metadata dictionary following the specific rules for different content types.
    """
    if content == DefaultStepMessages.EN.value:
        metadata = {
            MetadataFieldKeys.KIND: Kind.AGENT_STEP,
            MetadataFieldKeys.MESSAGE: _create_message_metadata(content, DefaultStepMessages.ID.value),
            MetadataFieldKeys.STATUS: Status.RUNNING,
            MetadataFieldKeys.TIME: 0.0,
        }
        # Merge any custom metadata (e.g., step_id, agent_name) for initial status too
        if custom_metadata and isinstance(custom_metadata, dict):
            metadata = {**metadata, **custom_metadata}
    else:
        metadata = create_metadata(
            content=content,
            is_final=False,
            status=Status.RUNNING,
            existing_metadata=custom_metadata,
        )

    if custom_metadata and content not in [DefaultStepMessages.EN.value]:
        metadata = {**metadata, **custom_metadata}

    return metadata
