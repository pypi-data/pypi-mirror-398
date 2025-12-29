from _typeshed import Incomplete
from aip_agents.agent.base_agent import BaseAgent as BaseAgent
from aip_agents.schema.step_limit import MaxDelegationDepthExceededError as MaxDelegationDepthExceededError
from aip_agents.types import A2AEvent as A2AEvent, A2AStreamEventType as A2AStreamEventType
from aip_agents.utils.artifact_helpers import extract_artifacts_from_agent_response as extract_artifacts_from_agent_response
from aip_agents.utils.langgraph.tool_managers.base_tool_manager import BaseLangGraphToolManager as BaseLangGraphToolManager
from aip_agents.utils.logger import get_logger as get_logger
from aip_agents.utils.metadata_helper import MetadataFieldKeys as MetadataFieldKeys, get_next_step_number as get_next_step_number
from aip_agents.utils.pii.pii_helper import anonymize_final_response_content as anonymize_final_response_content, extract_pii_mapping_from_agent_response as extract_pii_mapping_from_agent_response
from aip_agents.utils.reference_helper import extract_references_from_agent_response as extract_references_from_agent_response
from aip_agents.utils.step_limit_manager import StepLimitManager as StepLimitManager
from aip_agents.utils.token_usage_helper import STEP_USAGE_KEY as STEP_USAGE_KEY, TOTAL_USAGE_KEY as TOTAL_USAGE_KEY, USAGE_METADATA_KEY as USAGE_METADATA_KEY, extract_token_usage_from_agent_response as extract_token_usage_from_agent_response
from langchain_core.tools import BaseTool

logger: Incomplete
OUTPUT_KEY: str
RESULT_KEY: str
ARTIFACTS_KEY: str
METADATA_KEY: str
METADATA_INTERNAL_PREFIXES: Incomplete
METADATA_INTERNAL_KEYS: Incomplete
AGENT_RUN_A2A_STREAMING_METHOD: str

class DelegationToolManager(BaseLangGraphToolManager):
    """Manages internal agent delegation tools for LangGraph agents.

    This tool manager converts internal agent instances into LangChain tools
    that can be used for task delegation within a unified ToolNode. Each
    delegated agent becomes a tool that the coordinator can call.

    Simplified version following legacy BaseLangChainAgent patterns.
    """
    registered_agents: list[BaseAgent]
    parent_agent: Incomplete
    def __init__(self, parent_agent: BaseAgent | None = None) -> None:
        """Initialize the delegation tool manager.

        Args:
            parent_agent: The parent agent that creates delegation tools, used for parent step lookup.
        """
    created_tools: Incomplete
    def register_resources(self, agents: list[BaseAgent]) -> list[BaseTool]:
        """Register internal agents for delegation and convert them to tools.

        Args:
            agents: List of BaseAgent instances for internal task delegation.

        Returns:
            List of created delegation tools.
        """
    def get_resource_names(self) -> list[str]:
        """Get names of all registered delegation agents.

        Returns:
            list[str]: A list of names of all registered delegation agents.
        """
