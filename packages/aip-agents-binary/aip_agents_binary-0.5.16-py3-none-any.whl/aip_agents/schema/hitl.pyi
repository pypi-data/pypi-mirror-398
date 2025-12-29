from _typeshed import Incomplete
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from pydantic import BaseModel
from typing import Any

__all__ = ['ApprovalDecisionType', 'ApprovalRequest', 'ApprovalDecision', 'ApprovalLogEntry', 'HitlMetadata']

class ApprovalDecisionType(StrEnum):
    """Enumeration of possible approval decision types."""
    APPROVED: str
    REJECTED: str
    SKIPPED: str
    TIMEOUT_SKIP: str
    PENDING: str

@dataclass
class ApprovalRequest:
    """Represents an in-flight prompt shown to the operator."""
    request_id: str
    tool_name: str
    arguments_preview: str
    context: dict[str, str] | None = ...
    created_at: datetime | None = ...
    timeout_at: datetime | None = ...
    def __post_init__(self) -> None:
        """Initialize timestamps if not provided."""
    @classmethod
    def create(cls, tool_name: str, arguments_preview: str, context: dict[str, str] | None = None) -> ApprovalRequest:
        """Create a new approval request with generated request_id.

        Args:
            tool_name (str): The name of the tool requiring approval.
            arguments_preview (str): A preview of the arguments for display.
            context (dict[str, str] | None, optional): Additional context information.

        Returns:
            ApprovalRequest: A new approval request instance.
        """

@dataclass
class ApprovalDecision:
    """Captures the operator outcome."""
    request_id: str
    decision: ApprovalDecisionType
    operator_input: str
    decided_at: datetime | None = ...
    latency_ms: int | None = ...
    def __post_init__(self) -> None:
        """Initialize timestamp if not provided."""

@dataclass
class ApprovalLogEntry:
    """Structured log entry for HITL decisions."""
    request_id: str
    tool_name: str
    decision: str
    event: str = ...
    agent_id: str | None = ...
    thread_id: str | None = ...
    additional_context: dict[str, Any] | None = ...
    timestamp: datetime | None = ...
    def __post_init__(self) -> None:
        """Initialize timestamp if not provided."""

class HitlMetadata(BaseModel):
    """Structured metadata payload included in agent streaming events."""
    required: bool
    decision: ApprovalDecisionType
    request_id: str
    timeout_seconds: int | None
    timeout_at: datetime | None
    model_config: Incomplete
    def as_payload(self) -> dict[str, Any]:
        """Return a JSON-ready metadata payload."""
    @classmethod
    def from_decision(cls, decision: ApprovalDecision, *, required: bool = True, timeout_seconds: int | None = None, timeout_at: datetime | None = None) -> HitlMetadata:
        """Build metadata from an ``ApprovalDecision``.

        Args:
            decision (ApprovalDecision): The approval decision to build metadata from.
            required (bool, optional): Whether approval is required. Defaults to True.
            timeout_seconds (int | None, optional): Timeout in seconds for the decision.
            timeout_at (datetime | None, optional): Specific timeout datetime.

        Returns:
            HitlMetadata: The constructed metadata instance.
        """
