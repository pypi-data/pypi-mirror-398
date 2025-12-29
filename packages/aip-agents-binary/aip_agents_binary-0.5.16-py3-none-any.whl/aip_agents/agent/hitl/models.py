"""Backward-compatible exports for HITL approval schema.

Prefer importing from ``aip_agents.schema.hitl`` in new code.
"""

from aip_agents.schema.hitl import (
    ApprovalDecision,
    ApprovalDecisionType,
    ApprovalLogEntry,
    ApprovalRequest,
)

__all__ = [
    "ApprovalDecisionType",
    "ApprovalRequest",
    "ApprovalDecision",
    "ApprovalLogEntry",
]
