from _typeshed import Incomplete
from aip_agents.schema.hitl import ApprovalDecisionType as ApprovalDecisionType
from aip_agents.utils.logger import get_logger as get_logger
from aip_agents.utils.metadata.activity_narrative import ActivityNarrativeBuilder as ActivityNarrativeBuilder, DELEGATE_PREFIX as DELEGATE_PREFIX, HITL_DECISION_MESSAGES as HITL_DECISION_MESSAGES, HITL_PENDING_DESCRIPTION as HITL_PENDING_DESCRIPTION, HITL_PENDING_TITLE as HITL_PENDING_TITLE
from aip_agents.utils.metadata.schemas.activity_schema import Activity as Activity
from typing import Any

logger: Incomplete
DEFAULT_ACTIVITY_MESSAGE: str
TOOL_EXECUTION_RUNNING_TEMPLATE: str
TOOL_EXECUTION_COMPLETE_TEMPLATE: str
SUBAGENT_DELEGATION_TEMPLATE: str
SUBAGENT_COMPLETE_TEMPLATE: str
MIXED_EXECUTION_TEMPLATE: str
DEFAULT_ACTIVITY_INFO: Incomplete

def create_tool_activity_info(original_metadata: dict[str, Any] | None) -> dict[str, str]:
    '''Create activity info payload with optional LLM narrative overrides.

    Args:
        original_metadata: The original metadata dictionary containing tool_info and hitl data.

    Returns:
        A dict with data_type="activity" and data_value as a JSON string.
    '''
