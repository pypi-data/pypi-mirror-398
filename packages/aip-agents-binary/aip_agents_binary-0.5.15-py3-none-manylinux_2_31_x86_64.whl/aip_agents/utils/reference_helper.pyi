from _typeshed import Incomplete
from aip_agents.utils.logger import get_logger as get_logger
from aip_agents.utils.metadata_helper import MetadataFieldKeys as MetadataFieldKeys
from gllm_core.schema import Chunk
from langgraph.types import Command
from typing import Any

logger: Incomplete
SAVE_OUTPUT_HISTORY_ATTR: str
FORMAT_AGENT_REFERENCE: str

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
def validate_references(references: list[Any]) -> list[Chunk]:
    """Validate and deduplicate reference data.

    Args:
        references: List of reference data (expected to be Chunk objects).

    Returns:
        List of validated, deduplicated Chunk objects by content.
    """
def serialize_references_for_metadata(references: list[Any]) -> list[dict[str, Any]]:
    """Serialize references for inclusion in A2A metadata.

    Args:
        references: List of reference objects (typically Chunk objects).

    Returns:
        List of serialized reference dictionaries.
    """
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
def extract_references_from_agent_response(result: Any) -> list[dict[str, Any]] | None:
    """Extract references from agent response for delegation tools.

    Args:
        result: The result returned by the delegated agent.

    Returns:
        List of reference chunks if found, None otherwise.
    """
