from _typeshed import Incomplete
from a2a.types import AgentCard as AgentCard
from aip_agents.utils.a2a_connector import A2AConnector as A2AConnector
from aip_agents.utils.langgraph.tool_managers.base_tool_manager import BaseLangGraphToolManager as BaseLangGraphToolManager
from aip_agents.utils.logger import get_logger as get_logger
from langchain_core.tools import BaseTool

logger: Incomplete

class A2AToolManager(BaseLangGraphToolManager):
    """Manages A2A communication tools for LangGraph agents.

    This tool manager converts A2A agent cards into LangChain tools that can
    be used in a unified ToolNode within LangGraph agents. Each A2A agent
    becomes a tool that the LLM can call for external communication.
    """
    registered_agents: list
    def __init__(self) -> None:
        """Initialize the A2A tool manager."""
    created_tools: Incomplete
    def register_resources(self, agent_cards: list[AgentCard]) -> list[BaseTool]:
        """Register A2A agents and convert them to LangChain tools.

        Args:
            agent_cards: List of AgentCard instances for external communication.

        Returns:
            List of created A2A communication tools.
        """
    def get_resource_names(self) -> list[str]:
        """Get names of all registered A2A agents.

        Returns:
            list[str]: A list of names of all registered A2A agents.
        """
