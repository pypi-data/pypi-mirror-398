from aip_agents.agent.hitl.manager import ApprovalManager as ApprovalManager
from aip_agents.agent.hitl.prompt.base import BasePromptHandler as BasePromptHandler
from aip_agents.schema.hitl import ApprovalDecision as ApprovalDecision, ApprovalDecisionType as ApprovalDecisionType, ApprovalRequest as ApprovalRequest
from collections.abc import Callable

class DeferredPromptHandler(BasePromptHandler):
    """Prompt handler that defers tool execution until an external decision is received."""
    def __init__(self, notify: Callable[[ApprovalRequest], None] | None = None) -> None:
        """Initialize the deferred prompt handler.

        Args:
            notify: Optional callback function to notify when an approval request is made.
        """
    def attach_manager(self, manager: ApprovalManager) -> None:
        """Attach the ApprovalManager orchestrating approvals.

        Args:
            manager: The ApprovalManager instance to attach for handling approval decisions.
        """
    async def prompt_for_decision(self, request: ApprovalRequest, timeout_seconds: int, context_keys: list[str] | None = None) -> ApprovalDecision:
        """Register a waiter and return a pending decision sentinel.

        Args:
            request: The approval request containing the tool call details and context.
            timeout_seconds: Number of seconds to wait for approval before timing out.
            context_keys: Optional list of context keys to include in the approval request.

        Returns:
            ApprovalDecision with PENDING status and registered waiter for external resolution.
        """
