from _typeshed import Incomplete
from aip_agents.schema.hitl import ApprovalDecisionType as ApprovalDecisionType, HitlMetadata as HitlMetadata
from aip_agents.utils.formatter_llm_client import FormatterInvocationError as FormatterInvocationError, FormatterInvokerUnavailableError as FormatterInvokerUnavailableError, get_formatter_llm_client as get_formatter_llm_client
from aip_agents.utils.logger import get_logger as get_logger
from aip_agents.utils.metadata.activity_narrative.constants import DELEGATE_PREFIX as DELEGATE_PREFIX, HITL_DECISION_MESSAGES as HITL_DECISION_MESSAGES, HITL_PENDING_DESCRIPTION as HITL_PENDING_DESCRIPTION, HITL_PENDING_TITLE as HITL_PENDING_TITLE, OUTPUT_EXCERPT_MAX_CHARS as OUTPUT_EXCERPT_MAX_CHARS, SYSTEM_PROMPT as SYSTEM_PROMPT
from aip_agents.utils.metadata.activity_narrative.context import ActivityContext as ActivityContext, ActivityPhase as ActivityPhase
from aip_agents.utils.metadata.activity_narrative.formatters import ArgsFormatter as ArgsFormatter, OutputFormatter as OutputFormatter, SensitiveInfoFilter as SensitiveInfoFilter
from typing import Any

logger: Incomplete

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
    def __init__(self) -> None:
        """Initialize the activity narrative builder."""
    def build_payload(self, metadata: dict[str, Any] | None) -> dict[str, Any] | None:
        """Build enriched payload for the provided metadata.

        Args:
            metadata: The metadata dictionary containing tool_info, hitl, and other context.

        Returns:
            Dictionary payload with a rendered message, or None when not available.
        """
