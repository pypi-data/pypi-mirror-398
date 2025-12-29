"""Activity narrative builder utilities for tool and delegate messaging.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from typing import Any

from gllm_inference.schema import Message

from aip_agents.schema.hitl import ApprovalDecisionType, HitlMetadata
from aip_agents.utils.formatter_llm_client import (
    FormatterInvocationError,
    FormatterInvokerUnavailableError,
    get_formatter_llm_client,
)
from aip_agents.utils.logger import get_logger
from aip_agents.utils.metadata.activity_narrative.constants import (
    DELEGATE_PREFIX,
    HITL_DECISION_MESSAGES,
    HITL_PENDING_DESCRIPTION,
    HITL_PENDING_TITLE,
    OUTPUT_EXCERPT_MAX_CHARS,
    SYSTEM_PROMPT,
)
from aip_agents.utils.metadata.activity_narrative.context import ActivityContext, ActivityPhase
from aip_agents.utils.metadata.activity_narrative.formatters import (
    ArgsFormatter,
    OutputFormatter,
    SensitiveInfoFilter,
)
from aip_agents.utils.metadata.activity_narrative.utils import _format_tool_or_subagent_name

logger = get_logger(__name__)
_formatter_llm_client = get_formatter_llm_client()


class ActivityNarrativeBuilder:
    """Generate structured activity payloads via formatter LLM.

    High-level flow:
    1. Gather raw metadata about a tool/delegate event and normalize it into an ``ActivityContext``.
    2. Sanitize arguments and outputs so no sensitive values reach downstream renderers or the formatter model.
    3. Prompt the shared formatter with phase-specific instructions (e.g., describe intent on start, summarize results on end).
    4. If the formatter responds with usable heading/body text, surface it; otherwise fall back to deterministic templates
       built from the sanitized context.

    This approach keeps SSE activity cards readable when the formatter is healthy while still providing sensible copy when
    the formatter is unavailable or returns low-quality text.
    """

    _PHASE_PROMPTS: dict[ActivityPhase, dict[str, str]] = {
        ActivityPhase.TOOL_START: {
            "heading": (
                "Return heading_text describing the tool action such as 'Executing Time Tool' or "
                "'Searching for flight status'. Keep it short, friendly, and avoid colon-separated detail."
            ),
            "body": (
                "Summarize what the tool is about to do using the arguments. "
                "The first sentence must start with 'Trying to'. Use at most two sentences."
            ),
        },
        ActivityPhase.TOOL_END: {
            "heading": (
                "Return heading_text in the form '<subject> completed'. Do not add colons or extra punctuation."
            ),
            "body": (
                "Summarize the observed outcome using the outputs or errors. "
                "Only mention errors when one is provided; never state that no errors occurred. "
                "The first sentence must start with 'Reporting'. Keep it concise."
            ),
        },
        ActivityPhase.DELEGATE_START: {
            "heading": (
                "Return heading_text describing the delegated agent, e.g., 'Delegating to Research Agent'. "
                "Keep it friendly and avoid punctuation beyond spaces."
            ),
            "body": (
                "Explain the work being handed off using the arguments or task description. "
                "Start the first sentence with 'Investigating' or 'Researching' and describe the sub-agent's goal."
            ),
        },
        ActivityPhase.DELEGATE_END: {
            "heading": (
                "Return heading_text describing that the delegate finished, such as 'Compiling results from Research Agent'."
            ),
            "body": (
                "Summarize the delegate's outcome using the outputs. "
                "Only mention errors when one is provided; never state that no errors occurred. "
                "The first sentence should start with 'Reporting' or 'Returning'."
            ),
        },
    }

    def __init__(self) -> None:
        """Initialize the activity narrative builder."""
        self._filter = SensitiveInfoFilter()
        self._args_formatter = ArgsFormatter()
        self._output_formatter = OutputFormatter()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def build_payload(self, metadata: dict[str, Any] | None) -> dict[str, Any] | None:
        """Build enriched payload for the provided metadata.

        Args:
            metadata: The metadata dictionary containing tool_info, hitl, and other context.

        Returns:
            Dictionary payload with a rendered message, or None when not available.
        """
        if not isinstance(metadata, dict):
            logger.info("activity narrative skipping non-dict metadata (type=%s)", type(metadata))
            return None

        step_id = metadata.get("step_id") if isinstance(metadata.get("step_id"), str) else None

        context = self._build_context(metadata)
        if context is None:
            logger.info("activity narrative context unavailable; falling back to templates (step_id=%s)", step_id)
            return None

        if context.phase in {ActivityPhase.HITL_PENDING, ActivityPhase.HITL_RESOLVED}:
            message = self._build_hitl_message(context)
            logger.info(
                "activity narrative generated HITL message step_id=%s phase=%s subject=%s",
                context.step_id,
                context.phase.value,
                context.subject_name,
            )
            return {"message": message}

        heading_text, body_text = self._generate_llm_texts(context)
        message = self._assemble_message(context, heading_text, body_text)
        logger.info(
            "activity narrative message ready step_id=%s phase=%s chars=%s",
            context.step_id,
            context.phase.value,
            len(message),
        )
        return {"message": message}

    # ------------------------------------------------------------------
    # Context extraction
    # ------------------------------------------------------------------
    def _build_context(self, metadata: dict[str, Any]) -> ActivityContext | None:
        """Build ActivityContext from metadata dictionary.

        Args:
            metadata: Metadata dictionary containing tool_info, hitl, and other context.

        Returns:
            ActivityContext instance with extracted and formatted information, or None if invalid.
        """
        tool_info = self._ensure_dict(self._extract_value(metadata, "tool_info"))
        hitl_payload = self._extract_value(metadata, "hitl")
        hitl_metadata = self._parse_hitl_metadata(hitl_payload)
        hitl_decision = self._to_decision(hitl_metadata)

        phase = self._resolve_phase(tool_info, hitl_decision)
        args = self._extract_args(tool_info)
        output = self._extract_output(tool_info)
        sanitizer = self._extract_activity_sanitizer(tool_info)
        sanitized_args, sanitized_output = self._filter.sanitize(args, output, sanitizer)
        sanitized_args = self._ensure_dict(sanitized_args)

        arguments_excerpt = self._args_formatter.format(sanitized_args)
        output_excerpt = self._output_formatter.format(sanitized_output)
        error_excerpt = self._extract_error_excerpt(tool_info, metadata)
        is_delegate = self._is_delegate_tool(tool_info)
        subject_name = self._resolve_subject_name(tool_info, is_delegate)
        agent_name = self._extract_agent_name(metadata)
        step_id_value = self._extract_value(metadata, "step_id")
        step_id = step_id_value if isinstance(step_id_value, str) and step_id_value.strip() else None
        default_heading = self._default_heading(phase, subject_name, is_delegate)

        context = ActivityContext(
            phase=phase,
            agent_name=agent_name,
            step_id=step_id,
            subject_name=subject_name,
            sanitized_args=sanitized_args,
            sanitized_output=sanitized_output,
            arguments_excerpt=arguments_excerpt,
            output_excerpt=output_excerpt,
            error_excerpt=error_excerpt,
            is_delegate=is_delegate,
            hitl_metadata=hitl_metadata,
            hitl_decision=hitl_decision,
            default_heading=default_heading,
        )
        return context

    def _extract_value(self, metadata: dict[str, Any], key: str) -> Any:
        """Extract value from metadata by key name or enum value.

        Args:
            metadata: Metadata dictionary.
            key: Key name or enum value to look up.

        Returns:
            Extracted value, or None if not found.
        """
        if key in metadata:
            return metadata[key]
        for meta_key, value in metadata.items():
            if getattr(meta_key, "value", None) == key:
                return value
        return None

    def _ensure_dict(self, value: Any) -> dict[str, Any] | None:
        """Ensure value is a dictionary.

        Args:
            value: Value to check.

        Returns:
            Value if it's a dict, None otherwise.
        """
        return value if isinstance(value, dict) else None

    def _resolve_phase(
        self, tool_info: dict[str, Any] | None, hitl_decision: ApprovalDecisionType | None
    ) -> ActivityPhase:
        """Determine activity phase from tool info and HITL decision.

        Args:
            tool_info: Tool information dictionary.
            hitl_decision: HITL approval decision type.

        Returns:
            ActivityPhase enum value indicating the current phase.
        """
        if hitl_decision == ApprovalDecisionType.PENDING:
            return ActivityPhase.HITL_PENDING
        if hitl_decision and hitl_decision != ApprovalDecisionType.PENDING:
            return ActivityPhase.HITL_RESOLVED

        has_output = isinstance(tool_info, dict) and "output" in tool_info
        is_delegate = self._is_delegate_tool(tool_info)
        if is_delegate:
            return ActivityPhase.DELEGATE_END if has_output else ActivityPhase.DELEGATE_START
        return ActivityPhase.TOOL_END if has_output else ActivityPhase.TOOL_START

    def _is_delegate_tool(self, tool_info: dict[str, Any] | None) -> bool:
        """Check if tool is a delegation tool.

        Args:
            tool_info: Tool information dictionary.

        Returns:
            True if tool is a delegation tool, False otherwise.
        """
        if not isinstance(tool_info, dict):
            return False
        tool_instance = tool_info.get("tool_instance")
        metadata = getattr(tool_instance, "metadata", None)
        if isinstance(metadata, dict) and metadata.get("is_delegation_tool"):
            return True
        names = self._collect_tool_names(tool_info)
        return any(isinstance(name, str) and name.startswith(DELEGATE_PREFIX) for name in names)

    def _extract_args(self, tool_info: dict[str, Any] | None) -> dict[str, Any] | None:
        """Extract tool arguments from tool info.

        Args:
            tool_info: Tool information dictionary.

        Returns:
            Arguments dictionary, or None if not found.
        """
        if not isinstance(tool_info, dict):
            return None
        if isinstance(tool_info.get("args"), dict):
            return tool_info["args"]
        calls = tool_info.get("tool_calls")
        if isinstance(calls, list):
            for call in calls:
                if isinstance(call, dict) and isinstance(call.get("args"), dict):
                    return call["args"]
        return None

    def _extract_output(self, tool_info: dict[str, Any] | None) -> Any:
        """Extract tool output from tool info.

        Args:
            tool_info: Tool information dictionary.

        Returns:
            Tool output value, or None if not found.
        """
        if not isinstance(tool_info, dict):
            return None
        return tool_info.get("output")

    def _extract_activity_sanitizer(
        self, tool_info: dict[str, Any] | None
    ) -> Callable[[dict[str, Any] | None, Any | None], dict[str, Any]] | None:
        """Extract activity sanitizer function from tool instance.

        Args:
            tool_info: Tool information dictionary.

        Returns:
            Sanitizer callable if found, None otherwise.
        """
        if not isinstance(tool_info, dict):
            return None
        tool_instance = tool_info.get("tool_instance")
        sanitizer = getattr(tool_instance, "activity_sanitizer", None)
        return sanitizer if callable(sanitizer) else None

    def _extract_agent_name(self, metadata: dict[str, Any]) -> str | None:
        """Extract and prettify agent name from metadata.

        Args:
            metadata: Metadata dictionary.

        Returns:
            Prettified agent name, or None if not found.
        """
        candidate: str | None = None
        for key in ("agent_display_name", "agent_label", "agent_name", "agent_id", "memory_user_id"):
            value = self._extract_value(metadata, key)
            if isinstance(value, str) and value.strip():
                candidate = value.strip()
                if key in ("agent_display_name", "agent_label"):
                    break
        if not candidate:
            return None
        return _format_tool_or_subagent_name(candidate)

    def _extract_error_excerpt(self, tool_info: dict[str, Any] | None, metadata: dict[str, Any]) -> str | None:
        """Extract error message excerpt from tool info or metadata.

        Args:
            tool_info: Tool information dictionary.
            metadata: Metadata dictionary.

        Returns:
            Error message string, or None if no error found.
        """
        error_payload = None
        if isinstance(tool_info, dict):
            error_payload = tool_info.get("error")
        if not error_payload:
            error_payload = self._extract_value(metadata, "error")
        if isinstance(error_payload, dict):
            message = error_payload.get("message") or error_payload.get("detail")
            if isinstance(message, str) and message.strip():
                return message.strip()
            try:
                return json.dumps(error_payload, ensure_ascii=False)
            except Exception:
                return str(error_payload)
        if isinstance(error_payload, str) and error_payload.strip():
            return error_payload.strip()
        return None

    def _resolve_subject_name(self, tool_info: dict[str, Any] | None, is_delegate: bool) -> str | None:
        """Resolve subject name (tool or agent) from tool info.

        Args:
            tool_info: Tool information dictionary.
            is_delegate: Whether this is a delegation tool.

        Returns:
            Formatted subject name, or None if not found.
        """
        if not isinstance(tool_info, dict):
            return None
        tool_instance = tool_info.get("tool_instance")
        metadata = getattr(tool_instance, "metadata", None)
        if isinstance(metadata, dict):
            delegated = metadata.get("delegated_agent_name")
            if isinstance(delegated, str) and delegated.strip():
                return delegated
        names = self._collect_tool_names(tool_info)
        if not names:
            return None
        formatted = (
            [_format_tool_or_subagent_name(name, remove_delegate_prefix=True) for name in names]
            if is_delegate
            else [_format_tool_or_subagent_name(name) for name in names]
        )
        if len(formatted) == 1:
            return formatted[0]
        return ", ".join(formatted)

    def _collect_tool_names(self, tool_info: dict[str, Any]) -> list[str]:
        """Collect tool names from tool info.

        Args:
            tool_info: Tool information dictionary.

        Returns:
            List of tool names found.
        """
        names: list[str] = []
        if "name" in tool_info and isinstance(tool_info["name"], str):
            names.append(tool_info["name"])
        calls = tool_info.get("tool_calls")
        if isinstance(calls, list):
            for call in calls:
                if isinstance(call, dict) and isinstance(call.get("name"), str):
                    names.append(call["name"])
        return names

    def _default_heading(self, phase: ActivityPhase, subject_name: str | None, is_delegate: bool) -> str:
        """Return a deterministic heading used when the LLM omits one.

        Args:
            phase: Current activity phase indicating start/end/delegate state.
            subject_name: Friendly tool or delegate name, when available.
            is_delegate: Whether the subject represents a delegated agent.

        Returns:
            Heading string normalized for markdown display.
        """
        subject = subject_name or ("delegated task" if is_delegate else "agent task")
        subject = subject.strip().rstrip(".")
        templates: dict[ActivityPhase, str] = {
            ActivityPhase.TOOL_START: "Executing {subject}",
            ActivityPhase.TOOL_END: "{subject} completed",
            ActivityPhase.DELEGATE_START: "Delegating to {subject}",
            ActivityPhase.DELEGATE_END: "Compiling results from {subject}",
        }
        template = templates.get(phase)
        if template:
            heading = template.format(subject=subject)
        elif subject_name:
            heading = subject_name.strip()
        else:
            heading = "Delegated task" if is_delegate else "Agent update"
        heading = re.sub(r"\s+", " ", heading).strip()
        return heading.rstrip(":.")

    def _parse_hitl_metadata(self, payload: Any) -> HitlMetadata | None:
        """Parse HITL metadata from payload.

        Args:
            payload: HITL metadata payload (dict, HitlMetadata, or other).

        Returns:
            HitlMetadata instance if valid, None otherwise.
        """
        if isinstance(payload, HitlMetadata):
            return payload
        if isinstance(payload, dict):
            try:
                return HitlMetadata.model_validate(payload)  # type: ignore[attr-defined]
            except Exception:
                try:
                    return HitlMetadata(**payload)
                except Exception:
                    return None
        return None

    def _to_decision(self, metadata: HitlMetadata | None) -> ApprovalDecisionType | None:
        """Convert HITL metadata decision to ApprovalDecisionType.

        Args:
            metadata: HITL metadata instance.

        Returns:
            ApprovalDecisionType enum value, or None if invalid.
        """
        if metadata and metadata.decision:
            try:
                return ApprovalDecisionType(metadata.decision)
            except Exception:
                return None
        return None

    def _build_context_summary(self, context: ActivityContext) -> str | None:
        """Build summary from context excerpts or sanitized data.

        Args:
            context: Activity context.

        Returns:
            Summary string, or None if no data available.
        """
        if context.arguments_excerpt:
            return context.arguments_excerpt
        if context.output_excerpt:
            return context.output_excerpt
        if context.sanitized_args:
            return self._truncate_json(context.sanitized_args)
        if context.sanitized_output:
            return self._truncate_json(context.sanitized_output)
        return None

    def _truncate_json(self, value: Any, limit: int = OUTPUT_EXCERPT_MAX_CHARS) -> str | None:
        """Truncate JSON-serialized value to limit with ellipsis.

        Args:
            value: Value to serialize and truncate.
            limit: Maximum length (default 400).

        Returns:
            Truncated JSON string, or None if empty.
        """
        try:
            serialized = json.dumps(value, ensure_ascii=False)
        except Exception:
            serialized = str(value)
        serialized = serialized.strip()
        if not serialized:
            return None
        if len(serialized) <= limit:
            return serialized
        return serialized[: limit - 1].rstrip() + "…"

    def _build_hitl_message(self, context: ActivityContext) -> str:
        """Build HITL message based on phase and decision.

        Args:
            context: Activity context with HITL information.

        Returns:
            Formatted HITL message string.
        """
        if context.phase == ActivityPhase.HITL_PENDING:
            detail = HITL_PENDING_DESCRIPTION
            summary = context.subject_name or self._build_context_summary(context)
            if summary:
                detail = f"{detail} Request: {summary}."
            return f"{HITL_PENDING_TITLE}\n\n{detail}"

        title, desc = HITL_DECISION_MESSAGES.get(
            context.hitl_decision or ApprovalDecisionType.SKIPPED,
            HITL_DECISION_MESSAGES[ApprovalDecisionType.SKIPPED],
        )
        message = f"{title}\n\n{desc}"
        extra = self._build_context_summary(context)
        if extra:
            message = f"{message}\n\nContext: {extra}"
        return message

    def _invoke_formatter(self, context: ActivityContext) -> Any | None:
        """Invoke the formatter LLM and return the raw response.

        Args:
            context: Prepared activity context containing prompt payload inputs.

        Returns:
            Formatter client response object or None when the invoker is unavailable.
        """
        prompt_payload = self._build_prompt_payload(context)
        user_prompt = self._build_user_prompt(prompt_payload)
        messages = [
            Message.system(SYSTEM_PROMPT),
            Message.user(user_prompt),
        ]
        try:
            raw_response = _formatter_llm_client.invoke_blocking(messages=messages)
            return raw_response
        except FormatterInvokerUnavailableError:
            logger.warning(
                "activity narrative formatter unavailable; skipping narrative (step_id=%s phase=%s subject=%s)",
                context.step_id,
                context.phase.value,
                context.subject_name,
            )
            return None
        except FormatterInvocationError as exc:  # pragma: no cover - defensive
            logger.warning(
                "activity narrative LLM invocation failed step_id=%s phase=%s: %s",
                context.step_id,
                context.phase.value,
                exc,
            )
            return None

    def _generate_llm_texts(self, context: ActivityContext) -> tuple[str | None, str]:
        """Return heading/body text strings produced by the formatter model.

        Args:
            context: Fully constructed activity context for the event.

        Returns:
            A tuple of (heading_text, body_text) where heading_text may be None when
            the formatter is unavailable and body_text always contains a fallback.
        """
        fallback_body = self._build_context_summary(context) or "No additional detail provided."
        raw_response = self._invoke_formatter(context)
        if raw_response is None:
            logger.info("activity narrative LLM unavailable step_id=%s; using fallback", context.step_id)
            return None, fallback_body

        response_text = self._extract_response_text(raw_response)
        logger.debug(
            "activity narrative LLM raw response step_id=%s preview=%s",
            context.step_id,
            response_text[:160] + ("…" if len(response_text) > 160 else ""),
        )
        heading_text, body_text = self._extract_payload_texts(response_text, context)

        if not body_text:
            body_text = self._clean_llm_body(response_text)
        if not body_text:
            body_text = fallback_body
        return heading_text, body_text

    def _extract_payload_texts(self, response_text: str, context: ActivityContext) -> tuple[str | None, str | None]:
        """Extract heading/body strings from an embedded JSON block.

        Args:
            response_text: Raw formatter response serialized as text.
            context: Activity context used for logging.

        Returns:
            Tuple of sanitized heading and body text strings, or (None, None) when parsing fails.
        """
        payload = self._parse_embedded_json(response_text)
        if not isinstance(payload, dict):
            return None, None
        heading_text = self._sanitize_heading_text(payload.get("heading_text"))
        body_candidate = payload.get("body_text")
        body_text = self._clean_llm_body(body_candidate) if body_candidate is not None else None
        heading_present = bool(heading_text)
        body_present = bool(body_text)
        logger.debug(
            "activity narrative parsed JSON step_id=%s heading_present=%s body_present=%s",
            context.step_id,
            heading_present,
            body_present,
        )
        return heading_text, body_text

    def _parse_embedded_json(self, response_text: str) -> dict[str, Any] | None:
        """Return a dict parsed from the first {...} block in the response text.

        Args:
            response_text: Formatter output that may contain an embedded JSON payload.

        Returns:
            Parsed dictionary if JSON is found and valid, otherwise None.
        """
        start = response_text.find("{")
        end = response_text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        candidate = response_text[start : end + 1]
        try:
            parsed_payload = json.loads(candidate)
        except Exception:
            return None
        return parsed_payload if isinstance(parsed_payload, dict) else None

    def _build_prompt_payload(self, context: ActivityContext) -> dict[str, Any]:
        """Build prompt payload for LLM invocation.

        Args:
            context: Activity context.

        Returns:
            Prompt payload dictionary.
        """
        payload = {
            "phase": context.phase.value,
            "agent": context.agent_name,
            "subject": context.subject_name,
            "arguments": context.sanitized_args,
            "output": context.sanitized_output,
            "arguments_excerpt": context.arguments_excerpt,
            "output_excerpt": context.output_excerpt,
            "error": context.error_excerpt,
            "is_delegate": context.is_delegate,
        }
        if context.hitl_metadata:
            payload["hitl"] = context.hitl_metadata.model_dump(mode="json", exclude_none=True)
        instructions = self._phase_prompt(context.phase)
        return {
            "context": payload,
            "heading_instruction": instructions["heading"],
            "body_instruction": instructions["body"],
        }

    def _phase_prompt(self, phase: ActivityPhase) -> dict[str, str]:
        """Return heading/body instructions for the given phase.

        Args:
            phase: Activity phase to build prompt instructions for.

        Returns:
            Dictionary with "heading" and "body" instruction strings.
        """
        return self._PHASE_PROMPTS.get(
            phase,
            {
                "heading": "Return heading_text describing this update in five words or fewer.",
                "body": "Return body_text summarizing the activity in one or two sentences.",
            },
        )

    def _build_user_prompt(self, payload: dict[str, Any]) -> str:
        """Compose the user-facing prompt string for the formatter model.

        Args:
            payload: Prompt payload containing context plus heading/body instructions.

        Returns:
            Fully formatted string that will be sent as the user message.
        """
        heading_instruction = payload.get("heading_instruction") or "Provide heading_text describing this update."
        body_instruction = payload.get("body_instruction") or "Provide sentence_text summarizing this update."
        context_payload = payload.get("context") or {}
        arguments_excerpt = context_payload.get("arguments_excerpt") or "Not provided."
        output_excerpt = context_payload.get("output_excerpt") or "Not provided."
        context_json = json.dumps(context_payload, ensure_ascii=False)
        return (
            "Return valid JSON with keys 'heading_text' and 'body_text'. "
            "Do not include any other keys.\n"
            f"Heading instruction: {heading_instruction}\n"
            f"Body instruction: {body_instruction}\n"
            "Constraints: start each text with a verb phrase, avoid 'I' or 'We'.\n"
            f"Arguments excerpt: {arguments_excerpt}\n"
            f"Output excerpt: {output_excerpt}\n"
            f"Context JSON: {context_json}"
        )

    def _clean_llm_body(self, response: Any) -> str | None:
        """Normalize the LLM response (or snippet) into a plain body string.

        Args:
            response: Formatter response object, dictionary, or string snippet.

        Returns:
            Cleaned body text or None when the response lacks usable content.
        """
        text = self._extract_response_text(response)
        if not text:
            return None
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        body_lines: list[str] = []
        for line in lines:
            if line.startswith("#"):
                continue
            if line.startswith("**") and line.endswith("**"):
                continue
            body_lines.append(line)
        body = "\n".join(body_lines).strip()
        return body or None

    def _sanitize_heading_text(self, heading: Any | None) -> str | None:
        """Normalize heading text extracted from the formatter JSON payload.

        Args:
            heading: Raw heading value returned by the formatter.

        Returns:
            Sanitized heading string or None when the value is unusable.
        """
        if not isinstance(heading, str):
            return None
        text = heading.replace("\n", " ").strip()
        text = re.sub(r"\s+", " ", text)
        return text.rstrip(" .:;-")

    def _extract_response_text(self, response: Any) -> str:
        """Extract a usable text payload from various LLM client response shapes.

        Args:
            response: Formatter response object/dict/string produced by the client.

        Returns:
            Stripped string representation suitable for downstream parsing.
        """
        if hasattr(response, "output_text"):
            text = getattr(response, "output_text")
        elif isinstance(response, dict) and isinstance(response.get("output_text"), str):
            text = response["output_text"]
        else:
            text = response if isinstance(response, str) else str(response or "")
        return text.strip()

    def _assemble_message(
        self,
        context: ActivityContext,
        heading_text: str | None = None,
        body_text: str | None = None,
    ) -> str:
        """Combine heading/body strings with deterministic fallbacks.

        Args:
            context: Activity context associated with the event.
            heading_text: Optional heading supplied by the formatter.
            body_text: Optional body text supplied by the formatter.

        Returns:
            Markdown-formatted message ready for dashboards.
        """
        heading = (
            heading_text
            or context.default_heading
            or self._default_heading(context.phase, context.subject_name, context.is_delegate)
        )
        if heading:
            heading = heading.strip()
        else:
            heading = "Delegated task"
            if not context.is_delegate:
                heading = "Agent update"
        heading = re.sub(r"\s+", " ", heading).rstrip(".")

        body = body_text.strip() if body_text else (self._build_context_summary(context) or "")
        if not body:
            body = "No additional detail provided."
        return f"**{heading}**\n\n{body}"
