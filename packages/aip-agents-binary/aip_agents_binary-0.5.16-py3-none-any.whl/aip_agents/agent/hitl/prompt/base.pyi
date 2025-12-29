from abc import ABC, abstractmethod
from aip_agents.agent.hitl.manager import ApprovalManager as ApprovalManager
from aip_agents.schema.hitl import ApprovalDecision as ApprovalDecision, ApprovalRequest as ApprovalRequest

class BasePromptHandler(ABC):
    """Abstract base class for prompt handlers used in HITL flows."""
    def attach_manager(self, manager: ApprovalManager) -> None:
        """Optionally attach the ``ApprovalManager`` coordinating approvals.

        Args:
            manager (ApprovalManager): The approval manager instance to attach.
        """
    @abstractmethod
    async def prompt_for_decision(self, request: ApprovalRequest, timeout_seconds: int, context_keys: list[str] | None = None) -> ApprovalDecision:
        """Collect and return a decision for the given approval request.

        Args:
            request (ApprovalRequest): The approval request to prompt for.
            timeout_seconds (int): Maximum time to wait for a decision in seconds.
            context_keys (list[str] | None, optional): Optional keys for additional context. Defaults to None.

        Returns:
            ApprovalDecision: The decision made for the approval request.
        """
