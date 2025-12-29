from _typeshed import Incomplete
from aip_agents.utils.logger import get_logger as get_logger
from aip_agents.utils.metadata import create_tool_activity_info as create_tool_activity_info
from aip_agents.utils.token_usage_helper import STEP_USAGE_KEY as STEP_USAGE_KEY, TOTAL_USAGE_KEY as TOTAL_USAGE_KEY
from enum import StrEnum
from typing import Any

logger: Incomplete

def start_step_counter_scope(start: int = 1) -> None:
    """Begin a step counter scope, resetting only when entering the outermost scope.

    Args:
        start: Starting step number for the counter. Defaults to 1.
    """
def end_step_counter_scope() -> None:
    """Exit a step counter scope, maintaining parent scope counters.

    Decrements the depth counter while preserving the step count for parent scopes.
    """
def get_next_step_number() -> int:
    """Return the next step number within the active scope.

    Returns:
        int: The next sequential step number in the current scope.
    """

class DefaultStepMessages(StrEnum):
    """Constants for default step indicator messages."""
    EN: str
    ID: str

class Kind(StrEnum):
    """Constants for metadata kind values."""
    AGENT_STEP: str
    AGENT_THINKING_STEP: str
    FINAL_RESPONSE: str
    FINAL_THINKING_STEP: str
    AGENT_DEFAULT: str
    TOKEN: str

class Status(StrEnum):
    """Constants for metadata status values."""
    RUNNING: str
    FINISHED: str
    STOPPED: str

class MetadataFieldKeys(StrEnum):
    """Enumeration of standard metadata field keys used in A2A events."""
    KIND: str
    STATUS: str
    TIME: str
    MESSAGE: str
    TOOL_INFO: str
    REFERENCES: str
    THINKING_AND_ACTIVITY_INFO: str
    HITL: str
    STEP_USAGE = STEP_USAGE_KEY
    TOTAL_USAGE = TOTAL_USAGE_KEY
    TOKEN_STREAMING: str
    PII_MAPPING: str

class MetadataTimeTracker:
    """Tracks cumulative execution time across agent steps for final response metadata.

    This class provides a clean way to accumulate execution times from individual
    agent steps and apply the total time to final response metadata.

    Attributes:
        FLOAT_EPSILON: Epsilon value for floating point comparisons to avoid precision issues.
    """
    FLOAT_EPSILON: float
    def __init__(self) -> None:
        """Initialize the time tracker with zero accumulated time."""
    def update_response_metadata(self, response: dict[str, Any]) -> dict[str, Any]:
        """Update response metadata with accumulated time tracking.

        Args:
            response: Response dictionary containing metadata to update.

        Returns:
            dict[str, Any]: Response with updated metadata for final responses. If any error occurs,
                returns the original response unchanged.
        """

def create_metadata(content: str = '', status: Status = ..., is_final: bool = False, existing_metadata: dict[str, Any] | None = None) -> dict[str, Any]:
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
def create_tool_processing_metadata(original_metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    """Create metadata for tool processing events (tool_call and tool_result).

    Args:
        original_metadata: Optional original metadata to merge with.

    Returns:
        dict[str, Any]: Metadata dictionary with agent_thinking_step kind and no message/time/status.
    """
def create_status_update_metadata(content: str, custom_metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    """Create metadata for status update events with content-based rules.

    Args:
        content: The content of the status update.
        custom_metadata: Optional custom metadata to merge with.

    Returns:
        dict[str, Any]: Metadata dictionary following the specific rules for different content types.
    """
