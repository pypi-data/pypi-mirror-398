"""This module provides utility functions for handling token usage in LangGraph agents.

Authors:
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

from typing import Any

from langchain_core.messages.ai import AIMessage, UsageMetadata
from langchain_core.messages.tool import ToolMessage
from langgraph.types import Command

# Constants for token usage field names
USAGE_METADATA_KEY = "usage_metadata"
TOTAL_USAGE_KEY = "total_usage"
STEP_USAGE_KEY = "step_usage"


def add_usage_metadata(
    cur_accumulated_token_usage: UsageMetadata | None, new_token_usage: UsageMetadata | None
) -> UsageMetadata | None:
    """Reducer function to accumulate UsageMetadata across agent runs.

    Args:
        cur_accumulated_token_usage: The current accumulated token usage metadata.
        new_token_usage: New token usage metadata to add.

    Returns:
        Accumulated usage metadata or None if both inputs are None.
    """
    # Fast path for common cases
    if cur_accumulated_token_usage is None:
        return new_token_usage
    if new_token_usage is None:
        return cur_accumulated_token_usage

    # Pre-allocate result dictionary with known size
    keys = {"input_tokens", "output_tokens", "total_tokens"}
    result = {key: cur_accumulated_token_usage.get(key, 0) + new_token_usage.get(key, 0) for key in keys}

    # Only process details if they exist
    detail_keys = {"input_token_details", "output_token_details"}
    for key in detail_keys:
        if cur_accumulated_token_usage.get(key) or new_token_usage.get(key):
            result[key] = _merge_token_details(cur_accumulated_token_usage.get(key, {}), new_token_usage.get(key, {}))

    return result


def _merge_token_details(current: dict[str, int], new: dict[str, int]) -> dict[str, int]:
    """Merge token details from two dictionaries.

    Args:
        current: Current token details.
        new: New token details to add.

    Returns:
        Merged token details.
    """
    # Use dict comprehension for better performance
    all_keys = current.keys() | new.keys()
    return {key: current.get(key, 0) + new.get(key, 0) for key in all_keys}


def extract_and_update_token_usage_from_ai_message(ai_message: AIMessage) -> dict[str, Any]:
    """Extract token usage from AI message and prepare state update.

    Args:
        ai_message: The AI message containing usage metadata.

    Returns:
        Dictionary with accumulated_usage_metadata update if usage metadata is available.
    """
    state_updates = {}

    if hasattr(ai_message, USAGE_METADATA_KEY) and ai_message.usage_metadata:
        state_updates[TOTAL_USAGE_KEY] = ai_message.usage_metadata

    return state_updates


def extract_token_usage_from_tool_output(tool_output: Any) -> UsageMetadata | None:
    """Extract token usage from various tool output formats.

    Supports multiple tool output formats:
    1. Dictionary with 'usage_metadata' field
    2. Command with 'usage_metadata' attribute
    3. Any object with 'usage_metadata' attribute

    Args:
        tool_output: The output from a tool execution.

    Returns:
        UsageMetadata if found, None otherwise.
    """
    # Handle dictionary format: {"result": "...", "usage_metadata": {...}}
    if isinstance(tool_output, dict) and USAGE_METADATA_KEY in tool_output:
        return tool_output[USAGE_METADATA_KEY]

    # Handle Command format with usage_metadata in update field
    if isinstance(tool_output, Command):
        return extract_token_usage_from_command(tool_output)

    # Handle any object with usage_metadata attribute
    if hasattr(tool_output, USAGE_METADATA_KEY):
        return getattr(tool_output, USAGE_METADATA_KEY)

    return None


def extract_token_usage_from_command(command: Command) -> UsageMetadata | None:
    """Extract token usage from Command object.

    Args:
        command: The Command object to extract token usage from.

    Returns:
        UsageMetadata if found, None otherwise.
    """
    update_dict = getattr(command, "update", {}) or {}
    if USAGE_METADATA_KEY in update_dict:
        return update_dict[USAGE_METADATA_KEY]

    # if not try to get from messages in update, and accumulate token usage
    messages: list[ToolMessage] = update_dict.get("messages", [])
    if not messages:
        return None

    accumulated_token_usage = None
    for message in messages:
        if USAGE_METADATA_KEY in message.response_metadata:
            accumulated_token_usage = add_usage_metadata(
                accumulated_token_usage, message.response_metadata[USAGE_METADATA_KEY]
            )
    return accumulated_token_usage


def extract_token_usage_from_agent_response(agent_response: dict[str, Any]) -> UsageMetadata | None:
    """Extract accumulated token usage from agent response.

    Args:
        agent_response: The agent response to extract token usage from.

    Returns:
        UsageMetadata if found, None otherwise.
    """
    if not isinstance(agent_response, dict):
        return None

    full_state = agent_response.get("full_final_state", {})
    if not isinstance(full_state, dict):
        return None

    if TOTAL_USAGE_KEY in full_state:
        return full_state[TOTAL_USAGE_KEY]
    return None
