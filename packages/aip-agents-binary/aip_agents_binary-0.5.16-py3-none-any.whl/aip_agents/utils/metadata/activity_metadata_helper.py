"""Activity metadata helper utilities.

Provides helpers to build activity messages for tools and sub-agents.

Authors:
    Fachriza Adhiatma (fachriza.d.adhiatma@gdplabs.id)
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

import json
from typing import Any

from aip_agents.schema.hitl import ApprovalDecisionType
from aip_agents.utils.logger import get_logger
from aip_agents.utils.metadata.activity_narrative import (
    DELEGATE_PREFIX,
    HITL_DECISION_MESSAGES,
    HITL_PENDING_DESCRIPTION,
    HITL_PENDING_TITLE,
    ActivityNarrativeBuilder,
    _format_tool_or_subagent_name,
)
from aip_agents.utils.metadata.schemas.activity_schema import Activity

logger = get_logger(__name__)


def _create_activity_info(
    data_value: dict[str, Any] | str, top_level_id: str = "default_metadata_id"
) -> dict[str, str]:
    """Create activity info payload with a customizable ID and data_value.

    Args:
        data_value: The data content for the activity info as a dict or JSON string.
        top_level_id: The ID for the activity info. Defaults to "default_metadata_id".

    Returns a dict with top-level id and data_value as JSON string:
      {
        "data_type": "activity",
        "id": "<id>",
        "data_value": "{...}"
      }
    """
    if isinstance(data_value, dict):
        data_value_str = json.dumps(data_value)
    elif isinstance(data_value, str):
        try:
            json.loads(data_value)
            data_value_str = data_value
        except json.JSONDecodeError as e:
            raise ValueError(f"data_value string is not valid JSON: {e}") from e
    else:
        raise TypeError("data_value must be either a dict or a JSON string")
    activity = Activity(id=top_level_id, data_value=data_value_str)
    return activity.model_dump()


DEFAULT_ACTIVITY_MESSAGE = "**Performing agent tasks**\n\nProcessing the tasks."


# Message templates
TOOL_EXECUTION_RUNNING_TEMPLATE = "**Processing Agent with Tools**\n\nRunning tool {tool_name}"
TOOL_EXECUTION_COMPLETE_TEMPLATE = "**Tool Execution Complete**\n\nOutput received from {tool_name}"
SUBAGENT_DELEGATION_TEMPLATE = (
    "**Delegating to Subagent**\n\nHanding over the process to subagent {agent_name} for execution."
)
SUBAGENT_COMPLETE_TEMPLATE = "**Subagent Execution Complete**\n\nOutput received from subagent {agent_name}"
MIXED_EXECUTION_TEMPLATE = (
    "**Processing with Tools and Subagents**\n\nRunning tools: {tool_names} and delegating to subagents: {agent_names}"
)

# Exported default/terminal activity info
DEFAULT_ACTIVITY_INFO = _create_activity_info(
    {"message": DEFAULT_ACTIVITY_MESSAGE},
    "default_metadata_id",
)


def create_tool_activity_info(
    original_metadata: dict[str, Any] | None,
) -> dict[str, str]:
    """Create activity info payload with optional LLM narrative overrides.

    Args:
        original_metadata: The original metadata dictionary containing tool_info and hitl data.

    Returns:
        A dict with data_type="activity" and data_value as a JSON string.
    """
    if not original_metadata:
        logger.info("activity info requested with empty metadata; returning default payload")
        return DEFAULT_ACTIVITY_INFO

    step_id = original_metadata.get("step_id") if isinstance(original_metadata.get("step_id"), str) else None
    logger.info(
        "activity info creation started step_id=%s metadata_keys=%s",
        step_id,
        _summarize_metadata_keys(original_metadata),
    )

    builder = ActivityNarrativeBuilder()
    try:
        payload = builder.build_payload(original_metadata)
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.exception("activity narrative builder failed for step_id=%s: %s", step_id, exc)
        payload = None

    if payload:
        logger.info("activity narrative builder produced payload for step_id=%s", step_id)
        return _create_activity_info(payload)

    logger.info("activity narrative builder returned no payload; using legacy template (step_id=%s)", step_id)
    return _build_legacy_activity_info(original_metadata)


def _extract_metadata_value(metadata: dict[str, Any] | None, key: str) -> Any:
    """Retrieve a metadata value matching a key or StrEnum equivalent.

    Args:
        metadata (dict[str, Any] | None): The metadata dictionary to search in.
        key (str): The key to search for.

    Returns:
        Any: The value associated with the key, or None if not found.
    """
    if not isinstance(metadata, dict):
        return None

    if key in metadata:
        return metadata[key]

    for meta_key, value in metadata.items():
        if getattr(meta_key, "value", None) == key:
            return value
    return None


def _summarize_metadata_keys(metadata: dict[str, Any]) -> str:
    """Return a deterministic summary of metadata keys for logging.

    Args:
        metadata: Metadata dictionary emitted by the runner.

    Returns:
        str: Comma-separated list of sorted keys or a fallback token.
    """
    if not isinstance(metadata, dict):
        return "<invalid>"
    try:
        return ",".join(sorted(str(key) for key in metadata.keys()))
    except Exception:  # pragma: no cover - best-effort logging
        return "<unavailable>"


def _get_hitl_decision(metadata: dict[str, Any] | None) -> ApprovalDecisionType | None:
    """Extract the HITL decision from metadata if available.

    Args:
        metadata (dict[str, Any] | None): The metadata dictionary containing the decision.

    Returns:
        ApprovalDecisionType | None: The HITL decision if found, or None if not available.
    """
    if not isinstance(metadata, dict):
        return None

    decision = metadata.get("decision")
    if isinstance(decision, ApprovalDecisionType):
        return decision
    if isinstance(decision, str):
        try:
            return ApprovalDecisionType(decision.lower())
        except ValueError:
            return None
    return None


def _generate_hitl_pending_message(request_id: str | None = None) -> dict[str, str]:
    """Generate activity info for pending HITL approvals.

    Args:
        request_id (str | None, optional): The request ID for the HITL approval. Defaults to None.

    Returns:
        dict[str, str]: The activity info dictionary for the pending HITL approval.
    """
    message = f"{HITL_PENDING_TITLE}\n\n{HITL_PENDING_DESCRIPTION}"
    top_level_id = request_id if isinstance(request_id, str) and request_id else "default_metadata_id"
    return _create_activity_info({"message": message}, top_level_id)


def _append_hitl_decision_message(
    activity_info: dict[str, str],
    decision: ApprovalDecisionType,
    *,
    request_id: str | None = None,
) -> dict[str, str]:
    """Append HITL decision context to an existing activity info payload.

    This function takes an existing activity info dictionary and appends
    human-in-the-loop (HITL) decision information to it. The decision
    information includes a title and description based on the approval
    decision type.

    Args:
        activity_info: The existing activity info dictionary containing
            data_type, id, and data_value fields.
        decision: The HITL approval decision type (approved, rejected,
            skipped, or timeout_skip).
        request_id: Optional request ID to use as the activity ID.
            If provided and non-empty, replaces the existing ID.

    Returns:
        A new activity info dictionary with the HITL decision message
        appended to the existing message. If the decision type is not
        recognized or the input data is malformed, returns the original
        activity_info unchanged.

    """
    decision_entry = HITL_DECISION_MESSAGES.get(decision)
    if not decision_entry:
        return activity_info

    title, description = decision_entry
    try:
        payload = json.loads(activity_info["data_value"])
        base_message = payload.get("message", "")
    except (KeyError, json.JSONDecodeError):
        return activity_info

    combined_message = f"{title}\n\n{description}".strip()
    if base_message:
        combined_message = f"{combined_message}\n\n{base_message}"
    updated_payload = dict(payload)
    updated_payload["message"] = combined_message

    updated_activity = dict(activity_info)
    updated_activity["data_value"] = json.dumps(updated_payload)
    if isinstance(request_id, str) and request_id:
        updated_activity["id"] = request_id

    return updated_activity


def _extract_tool_names(tool_info: dict[str, Any] | None) -> list[str]:
    """Extract tool names from tool_info structure.

    Args:
        tool_info: A dict that may contain name or tool_calls, or None/invalid type.

    Returns:
        A list of tool names.
    """
    tool_names: list[str] = []

    if not isinstance(tool_info, dict):
        return tool_names

    if "name" in tool_info:
        tool_names = [tool_info["name"]]
    elif "tool_calls" in tool_info and isinstance(tool_info["tool_calls"], list):
        tool_names = [call["name"] for call in tool_info["tool_calls"] if isinstance(call, dict) and "name" in call]

    return tool_names


def _generate_tool_message(tool_names: list[str], has_output: bool) -> dict[str, str]:
    """Generate activity info for regular tools.

    Args:
        tool_names: A list of tool names.
        has_output: Whether the tool has output.

    Returns:
        A dict with data_type="activity" and data_value as a JSON string
        including a randomized UUID and the generated message.
    """
    formatted_tools = [_format_tool_or_subagent_name(tool) for tool in tool_names]
    tool_name = formatted_tools[0] if len(formatted_tools) == 1 else ", ".join(formatted_tools)

    if has_output:
        message = TOOL_EXECUTION_COMPLETE_TEMPLATE.format(tool_name=tool_name)
    else:
        message = TOOL_EXECUTION_RUNNING_TEMPLATE.format(tool_name=tool_name)

    return _create_activity_info({"message": message})


def _generate_subagent_message(subagent_names: list[str], has_output: bool) -> dict[str, str]:
    """Generate activity info for sub-agents.

    Args:
        subagent_names: A list of sub-agent names.
        has_output: Whether the sub-agent has output.

    Returns:
        A dict with data_type="activity" and data_value as a JSON string
        including a randomized UUID and the generated message.
    """
    formatted_agents = [_format_tool_or_subagent_name(agent, remove_delegate_prefix=True) for agent in subagent_names]
    agent_name = formatted_agents[0] if len(formatted_agents) == 1 else ", ".join(formatted_agents)

    if has_output:
        message = SUBAGENT_COMPLETE_TEMPLATE.format(agent_name=agent_name)
    else:
        message = SUBAGENT_DELEGATION_TEMPLATE.format(agent_name=agent_name)

    return _create_activity_info({"message": message})


def _generate_mixed_message(tool_names: list[str], subagent_names: list[str]) -> dict[str, str]:
    """Generate activity info for mixed tools and sub-agents execution.

    Args:
        tool_names: A list of tool names.
        subagent_names: A list of sub-agent names.

    Returns:
        A dict with data_type="activity" and data_value as a JSON string
        including a randomized UUID and the generated message.
    """
    formatted_tools = [_format_tool_or_subagent_name(tool) for tool in tool_names]
    formatted_agents = [_format_tool_or_subagent_name(agent, remove_delegate_prefix=True) for agent in subagent_names]

    tool_names_str = ", ".join(formatted_tools)
    agent_names_str = ", ".join(formatted_agents)

    message = MIXED_EXECUTION_TEMPLATE.format(tool_names=tool_names_str, agent_names=agent_names_str)
    return _create_activity_info({"message": message})


def _extract_hitl_request_id(hitl_metadata: dict[str, Any] | None) -> str | None:
    """Extract HITL request ID from metadata.

    Args:
        hitl_metadata: HITL metadata dictionary.

    Returns:
        Request ID string if found, None otherwise.
    """
    if not isinstance(hitl_metadata, dict):
        return None
    request_id = hitl_metadata.get("request_id")
    return request_id if isinstance(request_id, str) and request_id else None


def _build_tool_message_result(tool_names: list[str], has_output: bool) -> dict[str, str]:
    """Build activity message result based on tool types.

    Args:
        tool_names: List of tool names.
        has_output: Whether tool has output.

    Returns:
        Activity info dictionary.
    """
    subagent_tools = [name for name in tool_names if name.startswith(DELEGATE_PREFIX)]
    regular_tools = [name for name in tool_names if not name.startswith(DELEGATE_PREFIX)]

    # Mixed case: both tools and subagents (only when being called, not when output received)
    if subagent_tools and regular_tools and not has_output:
        return _generate_mixed_message(regular_tools, subagent_tools)

    # Pure tool case (including when mixed case has output)
    base_result = _generate_tool_message(tool_names, has_output)

    # Pure subagent case
    if subagent_tools and not regular_tools:
        base_result = _generate_subagent_message(subagent_tools, has_output)

    return base_result


def _build_legacy_activity_info(original_metadata: dict[str, Any] | None) -> dict[str, str]:
    """Create activity info based on tool information using legacy templates.

    Args:
        original_metadata: The original metadata dictionary containing tool_info and hitl data.

    Returns:
        A dict with data_type="activity" and data_value as a JSON string.
    """
    if not original_metadata:
        return DEFAULT_ACTIVITY_INFO

    tool_info = _extract_metadata_value(original_metadata, "tool_info")
    if not isinstance(tool_info, dict):
        tool_info = {}

    hitl_metadata = _extract_metadata_value(original_metadata, "hitl")
    hitl_decision = _get_hitl_decision(hitl_metadata)
    hitl_request_id = _extract_hitl_request_id(hitl_metadata)

    if hitl_decision == ApprovalDecisionType.PENDING:
        return _generate_hitl_pending_message(hitl_request_id)

    tool_names = _extract_tool_names(tool_info)
    if not tool_names:
        base_result = DEFAULT_ACTIVITY_INFO
    else:
        has_output = "output" in tool_info
        base_result = _build_tool_message_result(tool_names, has_output)

    if hitl_decision in HITL_DECISION_MESSAGES and hitl_decision is not None:
        return _append_hitl_decision_message(base_result, hitl_decision, request_id=hitl_request_id)

    return base_result
