"""Reference helper utilities for handling and validating reference data.

Authors:
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

from typing import Any

from gllm_core.schema import Chunk
from langgraph.types import Command

from aip_agents.utils.logger import get_logger
from aip_agents.utils.metadata_helper import MetadataFieldKeys

logger = get_logger(__name__)


# Tool attribute constants for reference extraction
SAVE_OUTPUT_HISTORY_ATTR = "save_output_history"
FORMAT_AGENT_REFERENCE = "_format_agent_reference"


def extract_references_from_tool(tool: Any, tool_output: Any) -> list[Chunk]:
    """Extract reference data from tools that support it.

    Extraction priority:
    1. Direct tool references via _format_agent_reference (preferred)
    2. Command.update references (fallback for delegation tools)

    Args:
        tool: The tool instance to extract references from
        tool_output: The output from the tool execution
    Returns:
        List of deduplicated Chunk objects containing reference data

    Note:
        - Never raises exceptions; logs warnings for issues
        - Direct tool references take precedence over Command references
    """
    if getattr(tool, SAVE_OUTPUT_HISTORY_ATTR, False):
        logger.debug(
            "Ignoring save_output_history for %s during reference extraction.",
            tool.__class__.__name__,
        )

    # Prefer direct tool references
    direct_references = _extract_direct_tool_references(tool, tool_output)
    if direct_references:
        return validate_references(direct_references)

    if isinstance(tool_output, Command):
        command_references = extract_references_from_command_update(tool_output)
        if command_references:
            return validate_references(command_references)

    return []


def _extract_direct_tool_references(tool: Any, tool_output: Any) -> list[Any]:
    """Extract references directly from tool hooks when available.

    Args:
        tool: The tool instance to extract references from
        tool_output: The output from the tool execution

    Returns:
        List of reference data (not yet validated/deduplicated)
    """
    if not hasattr(tool, FORMAT_AGENT_REFERENCE):
        return []

    try:
        reference_data = tool._format_agent_reference(tool_output)
    except (AttributeError, ValueError, TypeError) as e:
        logger.warning(f"Failed to extract references from {tool.__class__.__name__}: {e}")
        return []
    except Exception as e:
        logger.error(
            f"Unexpected error extracting references from {tool.__class__.__name__}: {e}",
            exc_info=True,
        )
        return []

    return _normalize_reference_data(reference_data, tool)


def _normalize_reference_data(reference_data: Any, tool: Any | None = None) -> list[Any]:
    """Normalize reference payloads into a list for downstream processing.

    Args:
        reference_data: Arbitrary payload returned by a tool or command.
        tool: Optional tool instance used for contextual logging when payload type is invalid.

    Returns:
        A list of reference objects ready for validation. Returns an empty list when
        the payload is ``None`` or cannot be interpreted as a reference collection.

    Notes:
        - Accepts `Chunk` instances and wraps them in a list.
        - Pass-through for list inputs to preserve existing semantics.
        - Emits a warning when encountering unsupported payload types, including
          the originating tool class when available.
    """
    if reference_data is None:
        return []
    if isinstance(reference_data, Chunk):
        return [reference_data]
    if isinstance(reference_data, list):
        return reference_data

    if tool is not None:
        logger.warning(
            "Invalid reference data format from %s: %s",
            tool.__class__.__name__,
            reference_data,
        )
    else:
        logger.warning("Invalid reference data format: %s", reference_data)

    return []


def extract_references_from_command_update(command: Command) -> list[Any]:
    """Extract references from a Command object's update dictionary.

    Args:
        command: A Command object potentially containing references in its update dict.

    Returns:
        List of reference data (not yet validated/deduplicated)

    Note:
        - Never raises exceptions; logs warnings for malformed data
        - Skips non-Chunk items with warning log
    """
    update = getattr(command, "update", None)
    if not isinstance(update, dict):
        return []

    raw_refs = update.get(MetadataFieldKeys.REFERENCES)
    if not isinstance(raw_refs, list):
        return []

    valid_refs = []
    for ref in raw_refs:
        if isinstance(ref, Chunk):
            valid_refs.append(ref)
        else:
            logger.warning(
                "Ignoring non-Chunk reference payload from delegation command: %s (type: %s)",
                ref,
                type(ref).__name__,
            )

    return valid_refs


def validate_references(references: list[Any]) -> list[Chunk]:
    """Validate and deduplicate reference data.

    Args:
        references: List of reference data (expected to be Chunk objects).

    Returns:
        List of validated, deduplicated Chunk objects by content.
    """
    if not references:
        return []

    validated = []
    seen_content = set()

    for ref in references:
        # Skip non-Chunk objects
        if not isinstance(ref, Chunk):
            logger.debug(f"Skipping non-Chunk reference: {type(ref)}")
            continue

        # Skip invalid content/metadata
        if not isinstance(ref.content, str | bytes) or not isinstance(ref.metadata, dict):
            logger.debug(f"Skipping reference with invalid content/metadata: {type(ref.content)}, {type(ref.metadata)}")
            continue

        # Deduplicate by content
        if ref.content not in seen_content:
            seen_content.add(ref.content)
            validated.append(ref)

    return validated


def serialize_references_for_metadata(references: list[Any]) -> list[dict[str, Any]]:
    """Serialize references for inclusion in A2A metadata.

    Args:
        references: List of reference objects (typically Chunk objects).

    Returns:
        List of serialized reference dictionaries.
    """
    serialized_refs = []
    for ref in references:
        if hasattr(ref, "model_dump"):
            # For Pydantic models like Chunk
            serialized_refs.append(ref.model_dump(mode="python"))
        elif isinstance(ref, dict):
            # Plain dicts pass through unchanged
            serialized_refs.append(ref)
        elif hasattr(ref, "__dict__"):
            # For regular objects with attributes
            serialized_refs.append(ref.__dict__)
        else:
            # Fallback for other types
            serialized_refs.append(str(ref))
    return serialized_refs


def add_references_chunks(left: list[Chunk], right: list[Chunk]) -> list[Chunk]:
    """Reducer function to accumulate reference data from multiple tool calls.

    This is a LangGraph reducer function that should be forgiving and handle
    edge cases gracefully. Non-Chunk items are filtered out.

    Args:
        left: Existing list of reference chunks (or None/non-list)
        right: New list of reference chunks to add (or None/non-list)

    Returns:
        Combined list of valid Chunk objects
    """
    # Handle None/non-list cases by converting to empty lists
    left_list = left if isinstance(left, list) else []
    right_list = right if isinstance(right, list) else []

    # Filter to only include valid Chunk objects
    valid_left = [item for item in left_list if isinstance(item, Chunk)]
    valid_right = [item for item in right_list if isinstance(item, Chunk)]

    # Handle empty cases efficiently
    if not valid_left:
        return valid_right
    if not valid_right:
        return valid_left

    return valid_left + valid_right


def extract_references_from_agent_response(result: Any) -> list[dict[str, Any]] | None:
    """Extract references from agent response for delegation tools.

    Args:
        result: The result returned by the delegated agent.

    Returns:
        List of reference chunks if found, None otherwise.
    """
    if not isinstance(result, dict):
        return None

    full_state = result.get("full_final_state", {})
    if not isinstance(full_state, dict):
        return None

    references = full_state.get("references")
    if not isinstance(references, list) or not references:
        return None

    try:
        validated_refs = validate_references(references)
        return validated_refs if validated_refs else None
    except Exception as e:
        logger.warning(f"ExtractRefFromAgentResponse: Error validating references: {e}")
        return None
