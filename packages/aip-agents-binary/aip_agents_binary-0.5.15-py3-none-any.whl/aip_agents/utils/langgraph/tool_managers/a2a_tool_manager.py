"""A2A tool manager for LangGraph agents.

This module provides the A2AToolManager class that converts A2A agent cards
into LangChain tools for use in LangGraph agents.
"""

from a2a.types import AgentCard
from langchain_core.tools import BaseTool, tool

from aip_agents.utils.a2a_connector import A2AConnector
from aip_agents.utils.langgraph.tool_managers.base_tool_manager import BaseLangGraphToolManager
from aip_agents.utils.logger import get_logger

logger = get_logger(__name__)


class A2AToolManager(BaseLangGraphToolManager):
    """Manages A2A communication tools for LangGraph agents.

    This tool manager converts A2A agent cards into LangChain tools that can
    be used in a unified ToolNode within LangGraph agents. Each A2A agent
    becomes a tool that the LLM can call for external communication.
    """

    def __init__(self):
        """Initialize the A2A tool manager."""
        super().__init__()
        self.registered_agents: list = []

    def register_resources(self, agent_cards: list[AgentCard]) -> list[BaseTool]:
        """Register A2A agents and convert them to LangChain tools.

        Args:
            agent_cards: List of AgentCard instances for external communication.

        Returns:
            List of created A2A communication tools.
        """
        self.registered_agents = list(agent_cards)
        self.created_tools = [self._create_a2a_tool(card) for card in agent_cards]

        logger.info(f"A2AToolManager: Created {len(self.created_tools)} A2A communication tools")
        return self.created_tools

    def get_resource_names(self) -> list[str]:
        """Get names of all registered A2A agents.

        Returns:
            list[str]: A list of names of all registered A2A agents.
        """
        return [agent.name for agent in self.registered_agents]

    def _create_a2a_tool(self, agent_card) -> BaseTool:
        """Create a LangChain tool for A2A communication with a specific agent.

        Following the legacy BaseLangChainAgent.create_a2a_tool pattern.

        Args:
            agent_card: The AgentCard instance for the agent to communicate with.

        Returns:
            BaseTool: A LangChain tool for A2A communication with the agent.
        """

        @tool
        def communicate_with_agent(query: str) -> str:
            """Communicate with external agent via A2A protocol.

            Args:
                query: The message to send to the external agent.

            Returns:
                The response from the external agent.
            """
            try:
                logger.debug(f"A2AToolManager: Sending A2A message to '{agent_card.name}'")
                response = A2AConnector.send_to_agent(agent_card, query)
                logger.debug(f"A2AToolManager: Received A2A response from '{agent_card.name}'")

                # Handle response format (following legacy pattern)
                if isinstance(response, dict) and "content" in response:
                    return str(response["content"])
                else:
                    return str(response)
            except Exception as e:
                error_msg = f"A2A communication with '{agent_card.name}' failed: {e}"
                logger.error(f"A2AToolManager: {error_msg}")
                return error_msg

        # Set tool metadata for proper routing and identification
        communicate_with_agent.name = agent_card.name
        communicate_with_agent.description = (
            f"Communicate with external agent '{agent_card.name}'. "
            f"Use this when you need to: {agent_card.description or 'collaborate with this agent'}"
        )
        # Set __name__ for compatibility (following legacy pattern)
        communicate_with_agent.__name__ = agent_card.name

        return communicate_with_agent
