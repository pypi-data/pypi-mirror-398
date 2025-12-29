from aip_agents.schema.hitl import ApprovalDecisionType, HitlMetadata
from dataclasses import dataclass
from enum import StrEnum

__all__ = ['ActivityContext', 'ActivityPhase']

class ActivityPhase(StrEnum):
    """Lifecycle phases for tool, delegate, and HITL events."""
    TOOL_START: str
    TOOL_END: str
    DELEGATE_START: str
    DELEGATE_END: str
    HITL_PENDING: str
    HITL_RESOLVED: str
JSONScalar = str | int | float | bool | None

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
    step_id: str | None = ...
    is_delegate: bool = ...
    hitl_metadata: HitlMetadata | None = ...
    hitl_decision: ApprovalDecisionType | None = ...
    default_heading: str | None = ...
