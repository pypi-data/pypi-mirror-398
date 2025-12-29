from _typeshed import Incomplete
from a2a.types import AgentCard
from aip_agents.agent.base_agent import BaseAgent as BaseAgent
from aip_agents.agent.google_adk_constants import DEFAULT_AUTH_URL as DEFAULT_AUTH_URL
from aip_agents.mcp.client.google_adk.client import GoogleADKMCPClient as GoogleADKMCPClient
from aip_agents.utils.a2a_connector import A2AConnector as A2AConnector
from aip_agents.utils.logger import get_logger as get_logger
from collections.abc import AsyncGenerator, AsyncIterator
from google.adk.agents import LlmAgent
from google.adk.tools.langchain_tool import LangchainTool
from langchain.tools import BaseTool as LangchainBaseTool
from pydantic import BaseModel
from typing import Any

logger: Incomplete
MODEL_TEMPERATURE: float

class A2AToolInput(BaseModel):
    """Input for the A2ATool."""
    query: str

class A2ATool(LangchainBaseTool):
    """A tool that communicates with an A2A agent."""
    name: str
    description: str
    args_schema: type[BaseModel]
    agent_card: AgentCard

def create_a2a_tool(agent_card: AgentCard) -> LangchainTool:
    """Create a LangChain tool from an A2A agent card.

    Args:
        agent_card (AgentCard): The A2A agent card to create a tool for.

    Returns:
        LangchainTool: A LangChain tool that can communicate with the A2A agent.
    """

class GoogleADKAgent(BaseAgent):
    """An agent that wraps a native Google ADK Agent with MCP support.

    This class implements the AgentInterface and uses Google's LlmAgent
    to handle the core conversation and tool execution logic via ADK's
    async-first design. It includes persistent MCP session management for
    stateful tool execution across multiple calls.

    The agent supports:
    - Native ADK tools (FunctionTool, LangchainTool)
    - MCP tools via GoogleADKMCPClient with session persistence
    - Sub-agent delegation using ADK's built-in multi-agent capabilities
    - A2A communication through tool integration
    """
    adk_native_agent: LlmAgent
    model: Incomplete
    max_iterations: Incomplete
    tools: Incomplete
    agents: Incomplete
    session_service: Incomplete
    name: Incomplete
    def __init__(self, name: str, instruction: str, model: str, tools: list[Any] | None = None, description: str | None = None, max_iterations: int = 3, agents: list['GoogleADKAgent'] | None = None, **kwargs: Any) -> None:
        '''Initializes the GoogleADKAgent with MCP support.

        Args:
            name: The name of this wrapper agent.
            instruction: The instruction for this wrapper agent.
            model: The name of the Google ADK model to use (e.g., "gemini-1.5-pro-latest").
            tools: An optional list of callable tools for the ADK agent.
            description: An optional human-readable description.
            max_iterations: Maximum number of iterations to run (default: 3).
            agents: Optional list of sub-agents that this agent can delegate to using ADK\'s
                   built-in multi-agent capabilities. These will be passed as sub_agents to the
                   underlying LlmAgent.
            **kwargs: Additional keyword arguments passed to the parent `__init__`.
        '''
    def run(self, query: str, **kwargs: Any) -> dict[str, Any]:
        '''Synchronously runs the Google ADK agent by wrapping the internal async run method.

        Args:
            query: The input query for the agent.
            **kwargs: Additional keyword arguments passed to the internal async run method.
                      Supports "session_id", "user_id", "app_name".

        Returns:
            A dictionary containing the agent\'s response.

        Raises:
            RuntimeError: If `asyncio.run()` is called from an already running event loop,
                          or for other unhandled errors during synchronous execution.
        '''
    async def arun(self, query: str, **kwargs: Any) -> dict[str, Any]:
        '''Asynchronously runs the agent with MCP tool support.

        This method ensures MCP tools are properly initialized before execution
        and provides persistent session management for stateful MCP tools.

        Args:
            query: The user\'s query to process.
            **kwargs: Additional keyword arguments. Supports "session_id", "user_id", "app_name".

        Returns:
            A dictionary containing the output, tool_calls, and session_id.
        '''
    async def cleanup(self) -> None:
        """Clean up ADK and MCP resources."""
    async def arun_stream(self, query: str, **kwargs: Any) -> AsyncIterator[str]:
        '''Runs the agent with the given query and streams the response parts.

        Args:
            query: The user\'s query to process.
            **kwargs: Additional keyword arguments. Supports "session_id", "user_id", "app_name".

        Yields:
            Text response chunks from the model. If an error occurs, the error message is yielded.
        '''
    def register_a2a_agents(self, agent_cards: list[AgentCard]) -> None:
        """Convert known A2A agents to LangChain tools.

        This method takes the agents from a2a_config.known_agents, creates A2AAgent
        instances for each one, and wraps them in LangChain tools.

        Args:
            agent_cards (list[AgentCard]): List of A2A agent cards to register as tools.

        Returns:
            None: The tools are added to the existing tools list.
        """
    async def arun_a2a_stream(self, query: str, configurable: dict[str, Any] | None = None, **kwargs: Any) -> AsyncGenerator[dict[str, Any], None]:
        '''Asynchronously streams the agent\'s response in a format compatible with A2A.

        This method formats the ADK agent\'s streaming responses into a consistent format
        that the A2A executor can understand and process.

        Args:
            query: The input query for the agent.
            configurable: Optional dictionary for configuration, may include:
                - thread_id: The A2A task ID (used as session_id).
            **kwargs: Additional keyword arguments. Supports "user_id", "app_name".

        Yields:
            Dictionary with \'status\' and \'content\' fields that describe the agent\'s response state.
        '''
