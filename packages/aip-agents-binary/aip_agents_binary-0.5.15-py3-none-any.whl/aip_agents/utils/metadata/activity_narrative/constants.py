"""Shared constants for activity narrative generation.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

from aip_agents.schema.hitl import ApprovalDecisionType

SYSTEM_PROMPT = """You summarize agent activity for operator dashboards.
- Describe what happened in short, factual sentences that highlight the most relevant arguments or outputs.
- Do not mention execution time, latency, token counts, or other operational metrics.
- Never mention internal IDs, UUIDs, or opaque agent identifiers. Prefer tool/delegate display names.
- Mention errors only when an actual error is present; never say that no errors occurred.
- Summaries should avoid quoting raw JSON unless necessary."""

DELEGATE_PREFIX = "delegate_to_"
OUTPUT_EXCERPT_MAX_CHARS = 512  # no specific reason, just a guess

HITL_PENDING_TITLE = "**Awaiting Review**"
HITL_PENDING_DESCRIPTION = (
    "This action requires human verification. The agent is paused until a reviewer approves or rejects the request."
)
HITL_DECISION_MESSAGES: dict[ApprovalDecisionType, tuple[str, str]] = {
    ApprovalDecisionType.APPROVED: (
        "**Request Approved**",
        "The reviewer approved this action. Execution will continue as planned.",
    ),
    ApprovalDecisionType.REJECTED: (
        "**Request Rejected**",
        "The reviewer rejected this action. The workflow moves to the next applicable step.",
    ),
    ApprovalDecisionType.SKIPPED: (
        "**Request Skipped**",
        "The reviewer skipped this action. Execution proceeds without performing it.",
    ),
    ApprovalDecisionType.TIMEOUT_SKIP: (
        "**Request Timed Out**",
        "No decision arrived before the timeout so the request was skipped automatically.",
    ),
}

__all__ = [
    "SYSTEM_PROMPT",
    "DELEGATE_PREFIX",
    "OUTPUT_EXCERPT_MAX_CHARS",
    "HITL_PENDING_TITLE",
    "HITL_PENDING_DESCRIPTION",
    "HITL_DECISION_MESSAGES",
]
