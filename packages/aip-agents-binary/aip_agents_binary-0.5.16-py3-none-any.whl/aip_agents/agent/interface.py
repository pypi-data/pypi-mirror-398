"""Defines the abstract base class AgentInterface for all agent implementations, now with MCP and A2A support.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import Any

from a2a.types import AgentCard
from gllm_inference.lm_invoker.lm_invoker import BaseLMInvoker

from aip_agents.schema.agent import BaseAgentConfig


class AgentInterface(ABC):
    """A general and minimal interface for agent implementations.

    Defines core execution methods (`__init__`, `run`, `arun`, `arun_stream`).
    Concrete subclasses must implement all abstract methods.
    """

    name: str
    instruction: str
    description: str | None
    mcp_config: dict[str, Any] = {}
    lm_invoker: BaseLMInvoker | None = None
    config: BaseAgentConfig | None = None

    def __init__(
        self,
        name: str,
        instruction: str,
        description: str | None = None,
        lm_invoker: BaseLMInvoker | None = None,
        config: BaseAgentConfig | None = None,
        **kwargs: Any,
    ):
        """Initializes the agent.

        Args:
            name: The name of the agent.
            instruction: The core directive or system prompt for the agent.
            description: Human-readable description. Defaults to instruction if not provided.
            lm_invoker: The language model invoker to use for LLM interactions. Defaults to None.
            config: Additional configuration for the agent.
            **kwargs: Additional keyword arguments for concrete implementations.
        """
        self.name = name
        self.instruction = instruction
        self.description = description or self.instruction
        self.lm_invoker = lm_invoker
        self.config = config

    @abstractmethod
    def run(
        self,
        query: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Synchronously runs the agent.

        Args:
            query: The input query for the agent.
            **kwargs: Additional keyword arguments for execution.

        Returns:
            Dict containing at least {'output': ...}.
        """
        raise NotImplementedError(
            f"'{self.__class__.__name__}' has not implemented the 'run' method."
        )  # pragma: no cover

    @abstractmethod
    async def arun(
        self,
        query: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Asynchronously runs the agent.

        Args:
            query: The input query for the agent.
            **kwargs: Additional keyword arguments for execution.

        Returns:
            Dict containing at least {'output': ...}.
        """
        raise NotImplementedError(
            f"'{self.__class__.__name__}' has not implemented the 'arun' method."
        )  # pragma: no cover

    @abstractmethod
    async def arun_stream(
        self,
        query: str,
        **kwargs: Any,
    ) -> AsyncGenerator[str | dict[str, Any], None]:
        """Asynchronously streams the agent's response.

        Args:
            query: The input query.
            **kwargs: Extra parameters for execution.

        Yields:
            Chunks of output (strings or dicts).
        """
        raise NotImplementedError(
            f"'{self.__class__.__name__}' has not implemented the 'arun_stream' method."
        )  # pragma: no cover

    @abstractmethod
    def add_mcp_server(self, mcp_config: dict[str, dict[str, Any]]) -> None:
        """Adds a new MCP server configuration.

        Args:
            mcp_config: Dictionary containing server name as key and its configuration as value.

        Raises:
            ValueError: If mcp_config is empty or None, or if any server configuration is invalid.
            KeyError: If any server name already exists in the configuration.
        """
        raise NotImplementedError(
            f"'{self.__class__.__name__}' has not implemented the 'add_mcp_server' method."
        )  # pragma: no cover

    @abstractmethod
    def register_a2a_agents(self, agents: list[AgentCard]):
        """Registers A2A agents from a list of AgentCards.

        Args:
            agents: A list of AgentCard instances.
        """
        raise NotImplementedError(
            f"'{self.__class__.__name__}' has not implemented the 'register_a2a_agents' method."
        )  # pragma: no cover
