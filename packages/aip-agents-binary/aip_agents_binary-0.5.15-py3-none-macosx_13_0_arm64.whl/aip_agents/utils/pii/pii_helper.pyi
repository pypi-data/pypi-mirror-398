from _typeshed import Incomplete
from aip_agents.utils.logger import LoggerManager as LoggerManager
from typing import Any

logger: Incomplete

def normalize_enable_pii(enable_pii: Any) -> bool | None:
    """Normalize enable_pii value from agent configuration.

    Args:
        enable_pii: Raw enable_pii value from agent configuration.

    Returns:
        The normalized enable_pii flag when explicitly set (True/False), otherwise None.
    """
def add_pii_mappings(left: dict[str, str] | None, right: dict[str, str] | None) -> dict[str, str]:
    """Reducer function to merge PII mappings from multiple sources.

    This is a LangGraph reducer function that merges PII mappings from:
    - Parent agent's initial mapping
    - Tool outputs with newly discovered PII
    - Subagent responses with their discovered PII

    Args:
        left: Existing PII mapping (or None)
        right: New PII mapping to merge (or None)

    Returns:
        Merged PII mapping dictionary

    Note:
        - Right (new) mappings take precedence over left (existing)
        - Handles None/non-dict cases gracefully
        - Preserves all unique PII tags
        - Returns empty dict if both inputs are None/empty
    """
def extract_pii_mapping_from_agent_response(result: Any) -> dict[str, str] | None:
    """Extract PII mapping from subagent response.

    Used by DelegationToolManager to propagate PII mappings from subagents
    back to parent agents.

    Args:
        result: The result returned by the delegated agent

    Returns:
        PII mapping dictionary if found, None otherwise

    Note:
        - Checks if result is a dict
        - Extracts 'full_final_state' from result
        - Extracts 'pii_mapping' from full_final_state
        - Validates mapping is a non-empty dict
        - Returns None if any step fails
    """
def deanonymize_final_response_content(content: str, is_final_response: bool, metadata: dict[str, Any] | None) -> str:
    """Deanonymize final response content using PII mapping from metadata.

    Args:
        content: Final response content that may contain PII tags.
        is_final_response: Flag indicating whether this message is a final response.
        metadata: Optional metadata dict (or event payload containing ``metadata``) with
            ``pii_mapping`` tag-to-value mapping.

    Returns:
        Content string with PII tags replaced by real values when applicable.
    """
def anonymize_final_response_content(content: str, metadata: dict[str, Any] | None) -> str:
    """Anonymize final response content using PII mapping from metadata.

    Args:
        content: Final response content that may contain real PII values.
        metadata: Metadata dict (or event payload containing ``metadata``) with
            ``pii_mapping`` tag-to-value mapping.

    Returns:
        Content string with real PII values replaced by their PII tags when mapping is present.
    """
