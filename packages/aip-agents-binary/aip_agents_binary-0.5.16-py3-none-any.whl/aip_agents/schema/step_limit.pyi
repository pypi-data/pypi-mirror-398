from _typeshed import Incomplete
from dataclasses import dataclass, field
from enum import StrEnum

class StepLimitErrorType(StrEnum):
    """Types of step-related limit violations."""
    STEP_LIMIT_EXCEEDED: str
    DELEGATION_DEPTH_EXCEEDED: str

@dataclass
class StepLimitConfig:
    """Configuration for agent step and delegation limits.

    Attributes:
        max_steps: Maximum number of execution steps allowed per invocation.
                   Includes agent node (LLM call) and every tool call (parallel batches count per call).
        max_delegation_depth: Maximum depth of delegation chain allowed.
                              Depth 0 means no delegation allowed.
    """
    max_steps: int = field(default_factory=Incomplete)
    max_delegation_depth: int = field(default_factory=Incomplete)
    def __post_init__(self) -> None:
        """Validate configuration values and normalize range."""

@dataclass
class StepLimitErrorResponse:
    """Structured error response for step limit violations.

    Attributes:
        error_type: The type of limit that was exceeded.
        agent_name: Name of the agent that hit the limit.
        current_value: Current step count or delegation depth.
        configured_limit: The configured limit that was exceeded.
        message: Human-readable error message.
        delegation_chain: Full chain for delegation errors.
        partial_result: Any output generated before hitting the limit.
    """
    error_type: StepLimitErrorType
    agent_name: str
    current_value: int
    configured_limit: int
    message: str
    delegation_chain: list[str] | None = ...
    partial_result: str | None = ...

class StepLimitError(Exception):
    """Base exception for step and delegation limit violations.

    Attributes:
        error_response: Structured error response with details.
    """
    error_response: Incomplete
    def __init__(self, error_response: StepLimitErrorResponse) -> None:
        """Initialize with error response.

        Args:
            error_response: Structured error details.
        """

class MaxStepsExceededError(StepLimitError):
    """Raised when agent exceeds configured max_steps limit."""
class MaxDelegationDepthExceededError(StepLimitError):
    """Raised when delegation would exceed max_delegation_depth limit."""
