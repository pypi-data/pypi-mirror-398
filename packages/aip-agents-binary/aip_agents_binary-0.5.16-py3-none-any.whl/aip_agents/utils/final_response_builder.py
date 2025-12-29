"""Utilities for assembling final response events with consistent structure.

This module wraps the lower-level ``_build_final_response_event`` helper and
provides a single entry point for producing final response payloads that may
include accumulated artifacts, custom metadata overrides, and additional
top-level fields.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from aip_agents.utils.metadata_helper import Kind, MetadataFieldKeys, Status

_FINAL_METADATA_RESERVED_KEYS = {
    MetadataFieldKeys.KIND.value,
    MetadataFieldKeys.STATUS.value,
    "timestamp",
}


@dataclass(slots=True)
class FinalResponseMetadataOptions:
    """Container for optional metadata fields on final response events."""

    step_id: str | None = None
    previous_step_ids: list[str] | None = None
    tool_info: dict[str, Any] | None = None
    thinking_and_activity_info: dict[str, Any] | None = None
    completion_reason: str | None = None
    timeout_seconds: float | None = None
    message: dict[str, Any] | None = None
    partial_result: str | None = None
    metadata_extra: dict[str, Any] | None = None


def _metadata_overrides_from_options(options: FinalResponseMetadataOptions) -> dict[str, Any]:
    """Build a dictionary of metadata overrides from the provided options.

    Args:
        options: The metadata options to extract overrides from.
    """
    potential_overrides = {
        "step_id": options.step_id,
        "previous_step_ids": options.previous_step_ids,
        MetadataFieldKeys.TOOL_INFO: options.tool_info,
        MetadataFieldKeys.THINKING_AND_ACTIVITY_INFO: options.thinking_and_activity_info,
        "completion_reason": options.completion_reason,
        "timeout_seconds": options.timeout_seconds,
        MetadataFieldKeys.MESSAGE: options.message,
        "partial_result": options.partial_result,
    }
    return {key: value for key, value in potential_overrides.items() if value is not None}


def _normalized_metadata_extras(metadata_extra: dict[str, Any] | None) -> dict[str, Any]:
    """Return metadata extras filtered for reserved keys and normalized to strings.

    Args:
        metadata_extra: Additional metadata to normalize, or None.
    """
    if not metadata_extra:
        return {}
    normalized: dict[str, Any] = {}
    for key, value in metadata_extra.items():
        normalized_key = str(key)
        if normalized_key in _FINAL_METADATA_RESERVED_KEYS:
            continue
        normalized[normalized_key] = value
    return normalized


def _update_optional_top_level_fields(
    event: dict[str, Any],
    status: str,
    task_state: str,
    artifacts: list[dict[str, Any]] | None,
) -> None:
    """Apply optional top-level fields when they are provided.

    Args:
        event: The event dictionary to update.
        status: The status value to set.
        task_state: The task state value to set.
        artifacts: List of artifacts to include, or None.
    """
    for key, value in (("status", status), ("task_state", task_state)):
        if value:
            event[key] = value
    if artifacts:
        event["artifacts"] = artifacts


def _ensure_timestamp_alignment(
    event: dict[str, Any],
    metadata: dict[str, Any],
    timestamp: datetime | None,
) -> None:
    """Keep event-level and metadata timestamps synchronized.

    Args:
        event: The event dictionary containing timestamp information.
        metadata: The metadata dictionary to update.
        timestamp: The timestamp to align, or None.
    """
    event_timestamp = event.get("timestamp")
    if event_timestamp is not None:
        metadata["timestamp"] = event_timestamp
        return

    metadata_timestamp = metadata.get("timestamp")
    if metadata_timestamp is not None:
        event["timestamp"] = metadata_timestamp
        return

    resolved_timestamp = (timestamp or datetime.now(UTC)).isoformat()
    metadata["timestamp"] = resolved_timestamp
    event["timestamp"] = resolved_timestamp


def _build_final_response_event(
    *,
    content: str,
    metadata_options: FinalResponseMetadataOptions | None = None,
    event_extra: dict[str, Any] | None = None,
    timestamp: datetime | None = None,
) -> dict[str, Any]:
    """Build a standardized final_response event payload.

    Args:
        content: The human-readable message to include in the event.
        metadata_options: Optional container for per-event metadata overrides such as
            identifiers, tool info, localized messages, and completion details.
        event_extra: Additional top-level event fields to merge (e.g., task_id).
        timestamp: Explicit timestamp for the event; defaults to current UTC time.

    Returns:
        dict[str, Any]: Final response payload ready for SSE serialization.
    """
    timestamp_value = (timestamp or datetime.now(UTC)).isoformat()
    metadata: dict[str, Any] = {
        MetadataFieldKeys.KIND: Kind.FINAL_RESPONSE,
        MetadataFieldKeys.STATUS: Status.FINISHED,
        MetadataFieldKeys.TIME: 0.0,
        "timestamp": timestamp_value,
    }

    if metadata_options is not None:
        metadata.update(_metadata_overrides_from_options(metadata_options))
        metadata.update(_normalized_metadata_extras(metadata_options.metadata_extra))

    event: dict[str, Any] = {
        "status": "success",
        "task_state": "completed",
        "content": content,
        "event_type": "final_response",
        "final": True,
        "metadata": metadata,
    }

    if event_extra:
        event.update(event_extra)

    return event


def assemble_final_response(
    *,
    content: str,
    artifacts: list[dict[str, Any]] | None = None,
    metadata_options: FinalResponseMetadataOptions | None = None,
    status: str = "success",
    task_state: str = "completed",
    extra_fields: dict[str, Any] | None = None,
    timestamp: datetime | None = None,
) -> dict[str, Any]:
    """Create a final response event with optional artifacts and overrides.

    Args:
        content: Human readable message for the final response.
        artifacts: Optional list of artifact dictionaries to attach.
        metadata_options: Metadata overrides passed through to the underlying builder.
        status: Top-level status string; defaults to ``"success"``.
        task_state: State string describing the task; defaults to ``"completed"``.
        extra_fields: Additional top-level fields to merge onto the event.
        timestamp: Explicit timestamp for the event. Defaults to ``datetime.now(UTC)``.

    Returns:
        dict[str, Any]: Final response event payload ready for downstream streaming.
    """
    event = _build_final_response_event(
        content=content,
        metadata_options=metadata_options,
        event_extra=extra_fields,
        timestamp=timestamp,
    )

    _update_optional_top_level_fields(event, status, task_state, artifacts)

    metadata = event.setdefault("metadata", {})
    _ensure_timestamp_alignment(event, metadata, timestamp)

    return event


__all__ = ["FinalResponseMetadataOptions", "assemble_final_response"]
