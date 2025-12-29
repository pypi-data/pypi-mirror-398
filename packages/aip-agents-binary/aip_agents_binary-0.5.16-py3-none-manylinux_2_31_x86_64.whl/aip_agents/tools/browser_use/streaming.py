"""Helpers for assembling streaming responses emitted by the browser-use tool.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable, Mapping
from textwrap import shorten
from typing import Any, Literal

from browser_use import Agent
from browser_use.agent.views import ActionResult, AgentBrain
from gllm_inference.schema import Message, MessageRole

from aip_agents.tools.browser_use.types import StreamingResponse, ToolCallInfo
from aip_agents.types import A2AStreamEventType
from aip_agents.utils.formatter_llm_client import (
    FormatterInvocationError,
    FormatterInvokerUnavailableError,
    get_formatter_llm_client,
)
from aip_agents.utils.logger import get_logger
from aip_agents.utils.metadata.activity_metadata_helper import _create_activity_info
from aip_agents.utils.metadata.schemas.thinking_schema import ThinkingDataType
from aip_agents.utils.metadata.thinking_metadata_helper import _create_thinking_info
from aip_agents.utils.metadata_helper import Kind, MetadataFieldKeys, Status

TASK_COMPLETED_MESSAGE = "Task completed"
PROCESSING_MESSAGE = "Working on your request..."
PRIMARY_TOOL_NAME = "browser_use_tool"

THINKING_SUMMARY_SYSTEM_PROMPT = (
    "You summarize the latest progress made by an automation agent. Provide Markdown with a bold, concise headline "
    "describing the key outcome, followed by one to three bullet points that highlight notable actions or findings. "
    "Stay factual, avoid internal identifiers, and keep the explanation user-friendly."
)

logger = get_logger(__name__)
_formatter_llm_client = get_formatter_llm_client()


def _normalize_segment(value: str) -> str:
    """Collapse whitespace and strip the provided segment.

    Args:
        value: The text segment to normalize.

    Returns:
        The normalized text segment.
    """
    return re.sub(r"\s+", " ", value or "").strip()


def _first_sentence(value: str) -> str:
    """Return the first sentence-like segment from the provided text.

    Args:
        value: The text to extract the first sentence from.

    Returns:
        The first sentence from the text, or empty string if no text provided.
    """
    if not value:
        return ""
    sentence, *_ = re.split(r"(?<=[.!?])\s+", value, maxsplit=1)
    return sentence.strip()


def _format_completion_content(tool_names: list[str]) -> str:
    """Mirror agent completion content formatting for consistency with A2A events.

    Args:
        tool_names: Ordered collection of tool names involved in the step.

    Returns:
        A descriptive completion string (e.g., ``"Completed tools: browser_use_tool"``).
    """
    unique_tool_names = list(dict.fromkeys(tool_names))
    has_delegation_tools = any(name.startswith("delegate_to") for name in unique_tool_names)
    content_prefix = "Completed sub-agents:" if has_delegation_tools else "Completed tools:"
    return f"{content_prefix} {', '.join(unique_tool_names)}"


def _format_tool_display_name(tool_name: str) -> str:
    """Convert a snake_case tool identifier into a human-friendly display name.

    Args:
        tool_name: Raw tool identifier, typically snake_case.

    Returns:
        A human-friendly display name with capitalized words.
    """
    parts = tool_name.replace("_", " ").split()
    return " ".join(part.capitalize() if not part.isupper() else part for part in parts)


def _build_completion_activity_message(tool_info: dict[str, Any], final_output: str) -> str:
    """Create a succinct completion headline for activity metadata.

    Args:
        tool_info: Dictionary containing tool metadata information.
        final_output: The final output text returned by the tool.

    Returns:
        Formatted completion headline string.
    """
    display_name = _format_tool_display_name(_resolve_tool_name(tool_info))
    headline = _summarize_final_headline(final_output) or f"{display_name} task completed."
    detail = _summarize_final_detail(final_output, display_name)
    return f"**{headline}**\n\n{detail}"


def _summarize_final_headline(final_output: str) -> str:
    """Return a concise headline extracted from the final output string.

    Args:
        final_output: The final output text returned by the tool.

    Returns:
        A concise headline string, or empty string if no output provided.
    """
    if not final_output:
        return ""

    for raw_line in final_output.splitlines():
        line = _normalize_segment(raw_line)
        if not line:
            continue
        candidate = _first_sentence(line) or line
        if "|" in candidate:
            candidate = candidate.split("|", 1)[0].strip()
        candidate = candidate.rstrip(":")
        if candidate:
            return candidate
    return ""


def _summarize_final_detail(final_output: str, display_name: str) -> str:
    """Return a short detail sentence summarizing completion.

    Args:
        final_output: The final output text returned by the tool.
        display_name: Human-friendly display name of the tool.

    Returns:
        A short detail sentence summarizing completion.
    """
    if not final_output:
        return f"Finished via {display_name}; no additional summary provided."

    lines = [line.strip() for line in final_output.splitlines() if line.strip()]
    if len(lines) > 1:
        second_line = _normalize_segment(lines[1])
        if second_line and not second_line.startswith("|"):
            return second_line
    return f"Finished via {display_name}; see the shared output for details."


def _resolve_tool_name(tool_info: dict[str, Any]) -> str:
    """Return the most specific tool name present in ``tool_info``.

    Args:
        tool_info: Metadata dictionary emitted by browser-use steps.

    Returns:
        str: Tool name suitable for display, defaulting to ``PRIMARY_TOOL_NAME``.
    """
    if not isinstance(tool_info, dict):
        return PRIMARY_TOOL_NAME

    name = tool_info.get("name")
    if _is_valid_tool_name(name):
        return name  # type: ignore[return-value]

    tool_calls = tool_info.get("tool_calls")
    if not isinstance(tool_calls, list):
        return PRIMARY_TOOL_NAME

    for entry in tool_calls:
        candidate = entry.get("name") if isinstance(entry, dict) else None
        if _is_valid_tool_name(candidate):
            return candidate  # type: ignore[return-value]

    return PRIMARY_TOOL_NAME


def _is_valid_tool_name(name: Any) -> bool:
    """Return True when the provided name is a non-empty string.

    Args:
        name: Candidate tool name.

    Returns:
        bool: True when ``name`` is a non-empty string.
    """
    return isinstance(name, str) and bool(name.strip())


def create_step_response(
    agent: Agent,
    tool_calls: list[ToolCallInfo],
    is_done: bool,
    content: str,
    thinking_message: str | None,
) -> StreamingResponse:
    """Compose the per-step payload emitted during browser-use streaming.

    Args:
        agent: Browser-use agent producing the step output.
        tool_calls: Tool call descriptors extracted from the step.
        is_done: Flag indicating whether this is the final step in the run.
        content: High-level status text describing the step progress.
        thinking_message: Optional preformatted thinking summary to attach.

    Returns:
        StreamingResponse: Serialized payload for the current streaming step.
    """
    tool_calls_dict = [{"name": tc.name, "args": tc.args, "output": tc.output} for tc in tool_calls]

    if is_done:
        final_tool = _get_done_tool_for_final_response(agent, tool_calls_dict)
        final_output = final_tool.get("output") or TASK_COMPLETED_MESSAGE
        tool_info = {
            "name": PRIMARY_TOOL_NAME,
            "args": final_tool.get("args", {}),
            "output": final_output,
            "execution_time": final_tool.get("execution_time"),
            "tool_calls": tool_calls_dict,
        }
        completion_message = _build_completion_activity_message(tool_info, final_output)
        logger.info(
            "Browser-use completion message generated: headline=%r detail=%r",
            completion_message.split("\n\n", 1)[0].strip("*"),
            completion_message.split("\n\n", 1)[1] if "\n\n" in completion_message else "",
        )
        activity_info = _create_activity_info({"message": completion_message})
        logger.debug("Browser-use completion activity info payload: %s", activity_info)
        metadata = {
            MetadataFieldKeys.KIND: Kind.FINAL_THINKING_STEP,
            MetadataFieldKeys.STATUS: Status.FINISHED,
            MetadataFieldKeys.TOOL_INFO: tool_info,
        }
        return StreamingResponse(
            event_type=A2AStreamEventType.STATUS_UPDATE,
            content=final_output,
            thinking_and_activity_info=activity_info,
            is_final=False,
            tool_info=tool_info,
            metadata=metadata,
        )

    tool_info = {"tool_calls": tool_calls_dict, "status": "running"}
    thinking_text = thinking_message or _build_fallback_thinking_message(content, tool_calls_dict)
    thinking_info = _create_thinking_info(thinking_text)
    metadata = {
        MetadataFieldKeys.KIND: Kind.AGENT_THINKING_STEP,
        MetadataFieldKeys.STATUS: Status.RUNNING,
        MetadataFieldKeys.TOOL_INFO: tool_info,
    }

    return StreamingResponse(
        event_type=A2AStreamEventType.STATUS_UPDATE,
        content=content,
        thinking_and_activity_info=thinking_info,
        is_final=False,
        tool_info=tool_info,
        metadata=metadata,
    )


async def generate_thinking_message(
    content: str,
    tool_calls: list[dict[str, Any]],
    *,
    is_final: bool,
) -> str | None:
    """Generate a user-facing thinking summary using the formatter LLM when available.

    Args:
        content: High-level status text describing the step progress.
        tool_calls: Serialized tool call dictionaries with outputs.
        is_final: Whether the task has completed.

    Returns:
        Markdown-formatted summary string, or ``None`` when not applicable.
    """
    if is_final:
        return None

    summary = await _summarize_with_llm(content, tool_calls)
    if summary:
        return summary

    return _build_fallback_thinking_message(content, tool_calls)


def _build_fallback_thinking_message(content: str, tool_calls: list[dict[str, Any]]) -> str:
    """Fallback deterministic summary when the formatter LLM is unavailable.

    Args:
        content: High-level status text describing the step progress.
        tool_calls: Serialized tool call dictionaries with outputs.

    Returns:
        Markdown summary string built from deterministic heuristics.
    """
    headline = _normalize_segment(_first_sentence(content)) or "Working on your request"
    details = "\n".join(_summarize_tool_details(tool_calls))
    return f"**{headline}**\n\n{details}"


def _tool_display_and_output(
    call: dict[str, Any],
    *,
    width: int,
    fallback: str,
) -> tuple[str, str] | None:
    """Extract a display name and truncated output snippet for a tool call.

    Args:
        call: Serialized tool call dictionary.
        width: Character width for truncating the output snippet.
        fallback: Placeholder text when the call lacks textual output.

    Returns:
        tuple[str, str] | None: (display name, snippet) pair when parsable, otherwise None.
    """
    if not isinstance(call, dict):
        return None

    name = _format_tool_display_name(str(call.get("name", PRIMARY_TOOL_NAME)))
    output = call.get("output")
    if isinstance(output, str) and output.strip():
        snippet = shorten(_normalize_segment(output), width=width, placeholder="…")
    else:
        snippet = fallback
    return name, snippet


def _summarize_tool_details(tool_calls: list[dict[str, Any]]) -> list[str]:
    """Return bullet-friendly summaries for each tool call.

    Args:
        tool_calls: Serialized tool call dictionaries with outputs.

    Returns:
        list[str]: Markdown bullet strings describing tool outputs.
    """
    detail_lines: list[str] = []
    for call in tool_calls:
        result = _tool_display_and_output(call, width=240, fallback="running")
        if not result:
            continue
        name, snippet = result
        detail_lines.append(f"- {name}: {snippet}")
    if not detail_lines:
        detail_lines.append("- Awaiting tool output")
    return detail_lines


async def _summarize_with_llm(content: str, tool_calls: list[dict[str, Any]]) -> str | None:
    """Attempt to summarize progress with the formatter LLM.

    Args:
        content: High-level status text describing the step progress.
        tool_calls: Serialized tool call dictionaries with outputs.

    Returns:
        Markdown-formatted summary string, or ``None`` when LLM is unavailable or fails.
    """
    messages = _build_thinking_messages(content, tool_calls)
    try:
        response = await _formatter_llm_client.invoke(messages=messages)
    except FormatterInvokerUnavailableError:
        logger.warning("Unable to initialize thinking summary LLM; DEFAULT_MODEL_FORMATTER is unset")
        return None
    except FormatterInvocationError as exc:  # noqa: BLE001
        logger.warning("Thinking summary LLM invocation failed: %s", exc)
        return None

    response_text = _coerce_response_text(response)
    return response_text or None


def _build_thinking_messages(content: str, tool_calls: list[dict[str, Any]]) -> list[Message]:
    """Compose the message list sent to the formatter LLM.

    Args:
        content: High-level status text describing the step progress.
        tool_calls: Serialized tool call dictionaries with outputs.

    Returns:
        list[Message]: LangChain message objects forming the prompt.
    """
    formatted_tools = _format_tool_context(tool_calls)
    user_sections = [
        f"Current status: {content}",
        "Latest tool outputs:",
        formatted_tools or "- No tool output available yet.",
        (
            "Produce Markdown with a bold first sentence capturing the key progress so far, "
            "followed by one to three bullet points highlighting notable actions or findings."
        ),
    ]
    user_prompt = "\n\n".join(user_sections)
    return [
        Message(role=MessageRole.SYSTEM, contents=[THINKING_SUMMARY_SYSTEM_PROMPT]),
        Message(role=MessageRole.USER, contents=[user_prompt]),
    ]


def _format_tool_context(tool_calls: list[dict[str, Any]]) -> str:
    """Format tool calls as enumerated Markdown lines for the LLM prompt.

    Args:
        tool_calls: Serialized tool call dictionaries with outputs.

    Returns:
        str: Human-readable summary of recent tool activity.
    """
    lines: list[str] = []
    for idx, call in enumerate(tool_calls, start=1):
        result = _tool_display_and_output(call, width=300, fallback="(no output)")
        if not result:
            continue
        name, snippet = result
        lines.append(f"{idx}. {name}: {snippet}")
    return "\n".join(lines)


def _coerce_response_text(response: Any) -> str:
    """Normalize formatter responses into a plain string.

    Args:
        response: Formatter output which may be a string, mapping, or object.

    Returns:
        str: Stripped textual representation.
    """
    if isinstance(response, str):
        return response.strip()
    if isinstance(response, Mapping):
        for key in ("content", "text", "message"):
            value = response.get(key)
            if isinstance(value, str):
                return value.strip()
        return ""
    content_value = getattr(response, "content", None)
    if isinstance(content_value, str):
        return content_value.strip()
    if response is None:
        return ""
    return str(response).strip()


def create_error_response(error_message: str, recording_url: str = "") -> dict:
    """Create a standardized error response.

    Args:
        error_message: The error message to include.
        recording_url: The recording URL if available.

    Returns:
        dict: Standardized error response.
    """
    activity_info = _create_activity_info({"message": f"**Error**\n\n{error_message}"})
    metadata: dict[str, Any] = {}
    if recording_url:
        metadata["recording_url"] = recording_url

    response = StreamingResponse(
        event_type=A2AStreamEventType.TOOL_RESULT,
        content=f"Error: {error_message}",
        thinking_and_activity_info=activity_info,
        is_final=True,
        tool_info={"tool_calls": []},
        metadata=metadata,
    )

    return response.to_dict()


def _compose_thinking_message(agent: Agent, summary: str | None = None) -> str:
    """Compose a combined memory/thinking message from agent state.

    Args:
        agent: Browser-use agent instance containing state information.
        summary: Optional high-level summary to headline the thinking message.

    Returns:
        Formatted Markdown message combining thinking and memory state.
    """
    thinking_text, memory_text = _extract_state_texts(agent)
    summary_headline = _summarize_headline(summary)
    headline = _build_thinking_headline(summary_headline, thinking_text, memory_text)
    if not headline:
        return "**Working on your request…**"

    message = f"**{headline}**"
    remainder = _compose_remainder_block(summary_headline, thinking_text, memory_text)
    if remainder:
        message += f"\n\n{remainder}"
    return message


def _extract_state_texts(agent: Agent) -> tuple[str, str]:
    """Return normalized thinking and memory text from the agent state.

    Args:
        agent: Browser-use agent instance containing state information.

    Returns:
        Tuple of (thinking_text, memory_text) both normalized strings.
    """
    thinking_text = ""
    memory_text = ""

    if agent.state.last_model_output and agent.state.last_model_output.current_state:
        current_state: AgentBrain = agent.state.last_model_output.current_state
        memory_text = _normalize_segment(current_state.memory)
        thinking_text = _normalize_segment(current_state.thinking)

    return thinking_text, memory_text


def _summarize_headline(summary: str | None) -> str:
    """Return a single-sentence headline from the summary output.

    Args:
        summary: Raw Markdown output summary.

    Returns:
        str: Headline text truncated for display.
    """
    if not summary:
        return ""
    return shorten(_normalize_segment(_first_sentence(summary)), width=200, placeholder="…")


def _build_thinking_headline(
    summary_headline: str,
    thinking_text: str,
    memory_text: str,
) -> str:
    """Build a fallback headline from thinking/memory when summary is absent.

    Args:
        summary_headline: Headline derived from the final summary.
        thinking_text: Normalized thinking text emitted by the agent.
        memory_text: Normalized scratchpad/memory text emitted by the agent.

    Returns:
        str: Headline string for the thinking panel.
    """
    focus_source = thinking_text or memory_text
    headline_source = _normalize_segment(_first_sentence(focus_source)) if focus_source else ""

    return summary_headline or (shorten(headline_source, width=200, placeholder="…") if headline_source else "")


def _compose_remainder_block(summary_headline: str, thinking_text: str, memory_text: str) -> str:
    """Compose the supporting paragraph following the headline.

    Args:
        summary_headline: Headline text already chosen.
        thinking_text: Normalized thinking text.
        memory_text: Normalized memory text.

    Returns:
        str: Supporting text block or empty string.
    """
    remainder_text = _compute_remainder_text(thinking_text, memory_text)
    if not remainder_text:
        return ""

    shortened_remainder = shorten(remainder_text, width=240, placeholder="…")
    if summary_headline:
        duplicate = (
            summary_headline.lower() in shortened_remainder.lower()
            or shortened_remainder.lower() in summary_headline.lower()
        )
        if duplicate:
            return ""
    return shortened_remainder


def _compute_remainder_text(thinking_text: str, memory_text: str) -> str:
    """Derive remainder text after the headline sentence.

    Args:
        thinking_text: Normalized thinking text.
        memory_text: Normalized memory text.

    Returns:
        str: Multi-sentence remainder text for display.
    """
    focus_source = thinking_text or memory_text
    if not focus_source:
        return ""

    focus_sentence_raw = _first_sentence(focus_source)
    remainder_text = focus_source[len(focus_sentence_raw) :].strip()
    if not remainder_text and memory_text and memory_text != focus_source:
        remainder_text = memory_text
    return _normalize_segment(remainder_text)


def generate_step_content(tool_calls: list[ToolCallInfo], is_done: bool) -> str:
    """Return user-friendly status text derived from tool call outputs.

    Args:
        tool_calls: Tool call descriptors extracted from the step.
        is_done: Flag indicating whether this is the final step in the run.

    Returns:
        User-friendly status text string.
    """
    if not tool_calls:
        return TASK_COMPLETED_MESSAGE if is_done else PROCESSING_MESSAGE

    if is_done:
        return TASK_COMPLETED_MESSAGE

    return _get_progress_message_from_tool_calls(tool_calls)


def _get_final_output_from_tool_calls(tool_calls: list[ToolCallInfo]) -> str:
    """Extract final output from tool calls when task is done.

    Args:
        tool_calls: List of tool calls to extract output from.

    Returns:
        str: Final output string.
    """
    for tool_call in reversed(tool_calls):
        if tool_call.name == "done" and tool_call.output:
            return tool_call.output

    for tool_call in reversed(tool_calls):
        if tool_call.output:
            return tool_call.output

    return TASK_COMPLETED_MESSAGE


def _get_progress_message_from_tool_calls(tool_calls: list[ToolCallInfo]) -> str:
    """Generate progress message from tool calls.

    Args:
        tool_calls: List of tool calls to generate progress message from.

    Returns:
        str: Progress message string.
    """
    tool_names = [tc.name for tc in tool_calls if tc.name]
    if tool_names:
        return f"Completed {', '.join(tool_names)}"
    return PROCESSING_MESSAGE


def _get_done_tool_for_final_response(agent: Agent, tool_calls_dict: list[dict]) -> dict[str, Any]:
    """Find or create the 'done' tool for final response.

    Args:
        agent: The browser-use agent.
        tool_calls_dict: List of tool call dictionaries.

    Returns:
        dict[str, Any]: The 'done' tool dictionary for final response.
    """
    for tool_call in tool_calls_dict:
        if tool_call.get("name") == "done":
            return tool_call

    final_response = _extract_final_response(agent.state.last_result)
    extracted_content = ""

    if final_response and final_response.get("extracted_content"):
        extracted_content = final_response["extracted_content"]
    elif tool_calls_dict:
        extracted_content = tool_calls_dict[-1]["output"]

    return {"name": "done", "args": {}, "output": extracted_content or TASK_COMPLETED_MESSAGE}


def _extract_final_response(last_result: Iterable[ActionResult] | None) -> dict[str, Any] | None:
    """Extract final response data from ActionResult when is_done=True.

    Args:
        last_result: Iterable of ActionResult objects from the agent's last operation.

    Returns:
        Dictionary containing serialized final response data, or ``None`` if no result found.
    """
    results = list(last_result or [])
    done_result = _first_matching_result(results, lambda item: getattr(item, "is_done", False))
    if done_result:
        return _serialize_action_result(done_result, bool(done_result.success))

    extracted_result = _first_matching_result(reversed(results), lambda item: getattr(item, "extracted_content", ""))
    if extracted_result:
        return _serialize_action_result(extracted_result, True)
    return None


def _first_matching_result(iterable: Iterable[Any], predicate: Callable[[Any], bool]) -> Any | None:
    """Return the first item in ``iterable`` that satisfies ``predicate``.

    Args:
        iterable: Sequence or generator of results.
        predicate: Callable returning True for the desired item.

    Returns:
        Any | None: Matching item or None when not found.
    """
    for item in iterable:
        if predicate(item):
            return item
    return None


def _serialize_action_result(result: ActionResult, success: bool) -> dict[str, Any]:
    """Normalize an ``ActionResult`` to a dict for streaming responses.

    Args:
        result: ActionResult emitted by browser-use.
        success: Whether the action is considered successful.

    Returns:
        dict[str, Any]: Structured payload capturing success/error information.
    """
    return {
        "success": success,
        "extracted_content": getattr(result, "extracted_content", "") or "",
        "error": getattr(result, "error", None),
    }


def yield_iframe_activity(url: str, content: str) -> dict:
    """Create and return an iframe activity streaming response.

    Args:
        url: The URL to display in the iframe.
        content: The content message for the response.

    Returns:
        dict: Streaming response dictionary.
    """
    activity_info = _create_activity_info({"type": "iframe", "message": url})
    return StreamingResponse(
        event_type=A2AStreamEventType.STATUS_UPDATE,
        content=content,
        thinking_and_activity_info=activity_info,
        is_final=False,
        metadata={MetadataFieldKeys.KIND: Kind.AGENT_THINKING_STEP},
    ).to_dict()


def yield_status_message(content: str) -> dict:
    """Create a status update event notifying clients about recovery attempts.

    Args:
        content: The status message content to include in the event.

    Returns:
        dict: Streaming response dictionary for the status update event.
    """
    thinking_info = _create_thinking_info(content)
    return StreamingResponse(
        event_type=A2AStreamEventType.STATUS_UPDATE,
        content=content,
        thinking_and_activity_info=thinking_info,
        is_final=False,
        metadata={MetadataFieldKeys.KIND: Kind.AGENT_THINKING_STEP, MetadataFieldKeys.STATUS: Status.RUNNING},
    ).to_dict()


def yield_thinking_marker(marker_type: Literal["start", "end"]) -> dict:
    """Create and return a thinking marker streaming response.

    Args:
        marker_type: Either 'start' or 'end' to indicate thinking phase.

    Returns:
        dict: Streaming response dictionary.
    """
    data_type = ThinkingDataType.THINKING_START if marker_type == "start" else ThinkingDataType.THINKING_END
    content = f"Thinking {marker_type}"
    thinking_info = _create_thinking_info(message="", data_type=data_type.value)
    return StreamingResponse(
        event_type=A2AStreamEventType.STATUS_UPDATE,
        content=content,
        thinking_and_activity_info=thinking_info,
        is_final=False,
        metadata={MetadataFieldKeys.KIND: Kind.AGENT_THINKING_STEP},
    ).to_dict()


__all__ = [
    "PROCESSING_MESSAGE",
    "TASK_COMPLETED_MESSAGE",
    "create_error_response",
    "create_step_response",
    "generate_step_content",
    "generate_thinking_message",
    "yield_iframe_activity",
    "yield_status_message",
    "yield_thinking_marker",
]
