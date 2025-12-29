from _typeshed import Incomplete
from aip_agents.agent.hitl.config import ToolApprovalConfig as ToolApprovalConfig
from aip_agents.agent.hitl.manager import ApprovalManager as ApprovalManager
from aip_agents.schema.hitl import ApprovalDecision as ApprovalDecision, ApprovalDecisionType as ApprovalDecisionType, ApprovalRequest as ApprovalRequest, HitlMetadata as HitlMetadata
from aip_agents.schema.langgraph import ToolCallResult as ToolCallResult
from aip_agents.tools.tool_config_injector import TOOL_CONFIGS_KEY as TOOL_CONFIGS_KEY
from aip_agents.utils.datetime import ensure_utc_datetime as ensure_utc_datetime
from aip_agents.utils.logger import get_logger as get_logger
from collections.abc import Callable
from typing import Any

logger: Incomplete
MAX_CONTEXT_MESSAGE_LENGTH: int

class LangGraphHitLMixin:
    """Provide Human-in-the-Loop helpers for LangGraph agents."""
    tool_configs: dict[str, Any] | None
    name: str
    @property
    def hitl_manager(self) -> ApprovalManager | None:
        """Return the active ``ApprovalManager``, creating one if needed."""
    @hitl_manager.setter
    def hitl_manager(self, manager: ApprovalManager | None) -> None:
        """Set the HITL approval manager instance.

        Args:
            manager: ApprovalManager instance or None.
        """
    def ensure_hitl_manager(self) -> ApprovalManager | None:
        """Ensure an ``ApprovalManager`` exists when HITL configs are present."""
    def use_hitl_manager(self, manager: ApprovalManager) -> None:
        """Replace the current ``ApprovalManager`` with the supplied instance.

        Args:
            manager: The ApprovalManager instance to use for HITL approvals.
        """
    def register_hitl_notifier(self, notifier: Callable[[ApprovalRequest], None]) -> None:
        """Register a notifier callback to receive HITL approval requests.

        Args:
            notifier: Callback function that will be called with approval requests.
        """
