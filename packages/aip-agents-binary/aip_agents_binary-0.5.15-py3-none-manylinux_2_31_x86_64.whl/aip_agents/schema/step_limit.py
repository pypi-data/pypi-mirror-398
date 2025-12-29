"""Step limit configuration and error classes for agent execution limits."""

import os
from dataclasses import dataclass, field
from enum import StrEnum


class StepLimitErrorType(StrEnum):
    """Types of step-related limit violations."""

    STEP_LIMIT_EXCEEDED = "STEP_LIMIT_EXCEEDED"
    DELEGATION_DEPTH_EXCEEDED = "DELEGATION_DEPTH_EXCEEDED"


@dataclass
class StepLimitConfig:
    """Configuration for agent step and delegation limits.

    Attributes:
        max_steps: Maximum number of execution steps allowed per invocation.
                   Includes agent node (LLM call) and every tool call (parallel batches count per call).
        max_delegation_depth: Maximum depth of delegation chain allowed.
                              Depth 0 means no delegation allowed.
    """

    max_steps: int = field(
        default_factory=lambda: int(os.getenv("STEP_LIMIT_MAX_STEPS_DEFAULT", "100")),
    )
    max_delegation_depth: int = field(
        default_factory=lambda: int(os.getenv("STEP_LIMIT_MAX_DELEGATION_DEPTH_DEFAULT", "5")),
    )

    def __post_init__(self):
        """Validate configuration values and normalize range."""
        from aip_agents.utils.logger import get_logger

        logger = get_logger(__name__)

        # Validate and clamp max_steps
        if self.max_steps < 1:
            logger.warning(f"Invalid max_steps={self.max_steps}, resetting to default (25). max_steps must be >= 1.")
            self.max_steps = 25
        elif self.max_steps > 1000:
            logger.warning(f"Invalid max_steps={self.max_steps}, capping at 1000.")
            self.max_steps = 1000

        # Validate and clamp max_delegation_depth
        if self.max_delegation_depth < 0:
            logger.warning(
                f"Invalid max_delegation_depth={self.max_delegation_depth}, resetting to default (5). "
                "max_delegation_depth must be >= 0."
            )
            self.max_delegation_depth = 5
        elif self.max_delegation_depth > 10:
            logger.warning(f"Invalid max_delegation_depth={self.max_delegation_depth}, capping at 10.")
            self.max_delegation_depth = 10


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
    delegation_chain: list[str] | None = None
    partial_result: str | None = None


class StepLimitError(Exception):
    """Base exception for step and delegation limit violations.

    Attributes:
        error_response: Structured error response with details.
    """

    def __init__(self, error_response: StepLimitErrorResponse):
        """Initialize with error response.

        Args:
            error_response: Structured error details.
        """
        self.error_response = error_response
        super().__init__(error_response.message)


class MaxStepsExceededError(StepLimitError):
    """Raised when agent exceeds configured max_steps limit."""

    pass


class MaxDelegationDepthExceededError(StepLimitError):
    """Raised when delegation would exceed max_delegation_depth limit."""

    pass
