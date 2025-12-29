"""Context objects describing activity-builder inputs.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from aip_agents.schema.hitl import ApprovalDecisionType, HitlMetadata


class ActivityPhase(StrEnum):
    """Lifecycle phases for tool, delegate, and HITL events."""

    TOOL_START = "tool_start"
    TOOL_END = "tool_end"
    DELEGATE_START = "delegate_start"
    DELEGATE_END = "delegate_end"
    HITL_PENDING = "hitl_pending"
    HITL_RESOLVED = "hitl_resolved"


JSONScalar = str | int | float | bool | None
JSONValue = JSONScalar | dict[str, "JSONValue"] | list["JSONValue"]


@dataclass
class ActivityContext:
    """Structured representation of an activity event."""

    phase: ActivityPhase
    agent_name: str | None
    subject_name: str | None
    sanitized_args: dict[str, JSONValue] | None
    sanitized_output: JSONValue | None
    arguments_excerpt: str | None
    output_excerpt: str | None
    error_excerpt: str | None
    step_id: str | None = None
    is_delegate: bool = False
    hitl_metadata: HitlMetadata | None = None
    hitl_decision: ApprovalDecisionType | None = None
    default_heading: str | None = None


__all__ = ["ActivityContext", "ActivityPhase"]
