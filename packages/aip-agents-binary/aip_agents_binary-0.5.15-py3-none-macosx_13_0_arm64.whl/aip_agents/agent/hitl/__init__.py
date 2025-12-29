"""Human-in-the-Loop (HITL) approval system for LangGraph tools.

This package provides components for intercepting tool calls and requiring
human approval before execution. It includes configuration, models, approval
management, and prompt handlers for deferred approval flows.

Author:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from aip_agents.agent.hitl.config import ToolApprovalConfig
from aip_agents.agent.hitl.manager import ApprovalManager
from aip_agents.agent.hitl.prompt import BasePromptHandler, DeferredPromptHandler
from aip_agents.schema.hitl import ApprovalDecision, ApprovalLogEntry, ApprovalRequest

__all__ = [
    "ToolApprovalConfig",
    "ApprovalManager",
    "ApprovalDecision",
    "ApprovalLogEntry",
    "ApprovalRequest",
    "BasePromptHandler",
    "DeferredPromptHandler",
]
