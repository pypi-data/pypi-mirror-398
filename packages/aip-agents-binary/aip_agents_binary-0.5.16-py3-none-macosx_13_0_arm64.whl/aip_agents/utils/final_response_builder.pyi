from dataclasses import dataclass
from datetime import datetime
from typing import Any

__all__ = ['FinalResponseMetadataOptions', 'assemble_final_response']

@dataclass(slots=True)
class FinalResponseMetadataOptions:
    """Container for optional metadata fields on final response events."""
    step_id: str | None = ...
    previous_step_ids: list[str] | None = ...
    tool_info: dict[str, Any] | None = ...
    thinking_and_activity_info: dict[str, Any] | None = ...
    completion_reason: str | None = ...
    timeout_seconds: float | None = ...
    message: dict[str, Any] | None = ...
    partial_result: str | None = ...
    metadata_extra: dict[str, Any] | None = ...

def assemble_final_response(*, content: str, artifacts: list[dict[str, Any]] | None = None, metadata_options: FinalResponseMetadataOptions | None = None, status: str = 'success', task_state: str = 'completed', extra_fields: dict[str, Any] | None = None, timestamp: datetime | None = None) -> dict[str, Any]:
    '''Create a final response event with optional artifacts and overrides.

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
    '''
