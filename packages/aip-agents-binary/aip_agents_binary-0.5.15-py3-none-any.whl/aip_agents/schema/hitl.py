"""Schema definitions for Human-in-the-Loop approval workflows."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "ApprovalDecisionType",
    "ApprovalRequest",
    "ApprovalDecision",
    "ApprovalLogEntry",
    "HitlMetadata",
]


class ApprovalDecisionType(StrEnum):
    """Enumeration of possible approval decision types."""

    APPROVED = "approved"
    REJECTED = "rejected"
    SKIPPED = "skipped"
    TIMEOUT_SKIP = "timeout_skip"
    PENDING = "pending"


@dataclass
class ApprovalRequest:
    """Represents an in-flight prompt shown to the operator."""

    request_id: str
    tool_name: str
    arguments_preview: str
    context: dict[str, str] | None = None
    created_at: datetime | None = None
    timeout_at: datetime | None = None

    def __post_init__(self) -> None:
        """Initialize timestamps if not provided."""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.timeout_at is None and self.created_at is not None:
            # Timeout is set externally when configuration is available
            pass

    @classmethod
    def create(
        cls,
        tool_name: str,
        arguments_preview: str,
        context: dict[str, str] | None = None,
    ) -> "ApprovalRequest":
        """Create a new approval request with generated request_id.

        Args:
            tool_name (str): The name of the tool requiring approval.
            arguments_preview (str): A preview of the arguments for display.
            context (dict[str, str] | None, optional): Additional context information.

        Returns:
            ApprovalRequest: A new approval request instance.
        """
        return cls(
            request_id=str(uuid4()),
            tool_name=tool_name,
            arguments_preview=arguments_preview,
            context=context,
        )


@dataclass
class ApprovalDecision:
    """Captures the operator outcome."""

    request_id: str
    decision: ApprovalDecisionType
    operator_input: str
    decided_at: datetime | None = None
    latency_ms: int | None = None

    def __post_init__(self) -> None:
        """Initialize timestamp if not provided."""
        if self.decided_at is None:
            self.decided_at = datetime.now()


@dataclass
class ApprovalLogEntry:
    """Structured log entry for HITL decisions."""

    request_id: str
    tool_name: str
    decision: str
    event: str = "hitl_decision"
    agent_id: str | None = None
    thread_id: str | None = None
    additional_context: dict[str, Any] | None = None
    timestamp: datetime | None = None

    def __post_init__(self) -> None:
        """Initialize timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.now()


class HitlMetadata(BaseModel):
    """Structured metadata payload included in agent streaming events."""

    required: bool = Field(default=True)
    decision: ApprovalDecisionType
    request_id: str
    timeout_seconds: int | None = Field(default=None, ge=0)
    timeout_at: datetime | None = None

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    def as_payload(self) -> dict[str, Any]:
        """Return a JSON-ready metadata payload."""
        payload = self.model_dump(mode="json", exclude_none=True)

        # Pydantic emits UTC datetimes as Zulu strings when dumping to JSON.
        # Preserve the canonical ``+00:00`` suffix expected by downstream tests.
        if "timeout_at" in payload and isinstance(self.timeout_at, datetime):
            payload["timeout_at"] = self.timeout_at.isoformat()

        return payload

    @classmethod
    def from_decision(
        cls,
        decision: ApprovalDecision,
        *,
        required: bool = True,
        timeout_seconds: int | None = None,
        timeout_at: datetime | None = None,
    ) -> "HitlMetadata":
        """Build metadata from an ``ApprovalDecision``.

        Args:
            decision (ApprovalDecision): The approval decision to build metadata from.
            required (bool, optional): Whether approval is required. Defaults to True.
            timeout_seconds (int | None, optional): Timeout in seconds for the decision.
            timeout_at (datetime | None, optional): Specific timeout datetime.

        Returns:
            HitlMetadata: The constructed metadata instance.
        """
        return cls(
            required=required,
            decision=decision.decision,
            request_id=decision.request_id,
            timeout_seconds=timeout_seconds,
            timeout_at=timeout_at,
        )
