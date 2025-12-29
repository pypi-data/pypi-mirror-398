"""PII mapping helper functions for LangGraph agent state management.

This module provides reducer functions and extraction utilities for managing
PII mappings across tool execution and multi-agent delegation scenarios.

Authors:
    Fachriza Adhiatma (fachriza.d.adhiatma@gdplabs.id)
"""

from typing import Any

from aip_agents.utils.logger import LoggerManager

logger = LoggerManager().get_logger(__name__)


def normalize_enable_pii(enable_pii: Any) -> bool | None:
    """Normalize enable_pii value from agent configuration.

    Args:
        enable_pii: Raw enable_pii value from agent configuration.

    Returns:
        The normalized enable_pii flag when explicitly set (True/False), otherwise None.
    """
    if enable_pii is None:
        return None

    if isinstance(enable_pii, bool):
        return enable_pii

    logger.warning("Ignoring invalid enable_pii value from agent config: %s", enable_pii)
    return None


def _get_pii_mapping_from_metadata(metadata: dict[str, Any] | None) -> dict[str, str] | None:
    """Extract the pii_mapping dictionary from metadata structures.

    Args:
        metadata: Metadata payload that may contain a pii_mapping key directly or nested
            inside another metadata dictionary.

    Returns:
        A dict containing tag-to-value mappings when found, otherwise None.
    """
    if not isinstance(metadata, dict):
        return None

    metadata_dict = metadata
    if "pii_mapping" not in metadata_dict and isinstance(metadata.get("metadata"), dict):
        metadata_dict = metadata["metadata"]

    pii_mapping = metadata_dict.get("pii_mapping")
    if isinstance(pii_mapping, dict) and pii_mapping:
        return pii_mapping  # type: ignore[return-value]
    return None


def _replace_content_segments(content: str, replacements: list[tuple[str, str]]) -> str:
    """Apply sequential placeholder replacements on a response string.

    Args:
        content: Original response content containing placeholders.
        replacements: List of (placeholder, actual_value) tuples to apply in order.

    Returns:
        The content string with all replacements applied.
    """
    if not replacements:
        return content

    result = content
    for placeholder, actual in replacements:
        result = result.replace(placeholder, actual)
    return result


def add_pii_mappings(
    left: dict[str, str] | None,
    right: dict[str, str] | None,
) -> dict[str, str]:
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
    # Handle None/non-dict inputs
    left_dict = left if isinstance(left, dict) else {}
    right_dict = right if isinstance(right, dict) else {}

    # Merge: right takes precedence
    merged = {**left_dict, **right_dict}

    return merged if merged else {}


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
    # Validate result is a dict
    if not isinstance(result, dict):
        return None

    # Extract full_final_state
    full_final_state = result.get("full_final_state")
    if not isinstance(full_final_state, dict):
        return None

    # Extract pii_mapping
    pii_mapping = full_final_state.get("pii_mapping")
    if not isinstance(pii_mapping, dict) or not pii_mapping:
        return None

    logger.info(f"Extracted PII mapping with {len(pii_mapping)} entries from agent response")
    return pii_mapping  # type: ignore


def deanonymize_final_response_content(
    content: str,
    is_final_response: bool,
    metadata: dict[str, Any] | None,
) -> str:
    """Deanonymize final response content using PII mapping from metadata.

    Args:
        content: Final response content that may contain PII tags.
        is_final_response: Flag indicating whether this message is a final response.
        metadata: Optional metadata dict (or event payload containing ``metadata``) with
            ``pii_mapping`` tag-to-value mapping.

    Returns:
        Content string with PII tags replaced by real values when applicable.
    """
    if not is_final_response:
        return content

    pii_mapping = _get_pii_mapping_from_metadata(metadata)
    if not pii_mapping:
        return content

    replacements = [
        (tag, value) for tag, value in pii_mapping.items() if isinstance(tag, str) and isinstance(value, str) and tag
    ]

    return _replace_content_segments(content, replacements)


def anonymize_final_response_content(content: str, metadata: dict[str, Any] | None) -> str:
    """Anonymize final response content using PII mapping from metadata.

    Args:
        content: Final response content that may contain real PII values.
        metadata: Metadata dict (or event payload containing ``metadata``) with
            ``pii_mapping`` tag-to-value mapping.

    Returns:
        Content string with real PII values replaced by their PII tags when mapping is present.
    """
    if not isinstance(content, str) or not content:
        return content

    pii_mapping = _get_pii_mapping_from_metadata(metadata)
    if not pii_mapping:
        return content

    replacements = [
        (tag, value) for tag, value in pii_mapping.items() if isinstance(tag, str) and isinstance(value, str) and value
    ]
    if not replacements:
        return content

    # Replace longer values first to avoid partial replacements (e.g., "John" before "John Smith").
    replacements.sort(key=lambda item: len(item[1]), reverse=True)
    normalized_pairs = [(value, tag) for tag, value in replacements]

    return _replace_content_segments(content, normalized_pairs)
