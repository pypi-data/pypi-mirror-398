"""Base class for LangGraph tool managers.

This module provides the abstract base class for managing specialized tools
in LangGraph agents. Tool managers convert different capabilities (A2A, delegation) into unified LangChain tools.
"""

from abc import ABC, abstractmethod
from typing import Any

from langchain_core.tools import BaseTool

from aip_agents.utils.logger import get_logger

logger = get_logger(__name__)


class BaseLangGraphToolManager(ABC):
    """Base class for managing specialized tools in LangGraph agents.

    This abstract base class provides a common interface for tool managers
    that convert different types of capabilities into LangChain tools for
    use in LangGraph agents.

    The design follows a simple pattern:
    1. Register resources (agents, cards, etc.)
    2. Convert resources to LangChain tools
    3. Provide access to created tools
    """

    def __init__(self):
        """Initialize the tool manager."""
        self.created_tools: list[BaseTool] = []

    @abstractmethod
    def register_resources(self, resources: list[Any]) -> list[BaseTool]:
        """Register resources and convert them to LangChain tools.

        Args:
            resources: List of resources to convert to tools.

        Returns:
            List of created tools.
        """
        pass  # pragma: no cover - abstract method, pass statement never executed

    def get_tools(self) -> list[BaseTool]:
        """Get all created tools.

        Returns:
            Copy of created tools list.
        """
        return self.created_tools.copy()

    def clear_tools(self) -> None:
        """Clear all created tools."""
        self.created_tools.clear()
        logger.debug(f"{self.__class__.__name__}: Cleared all tools")

    @abstractmethod
    def get_resource_names(self) -> list[str]:
        """Get names of all registered resources.

        Returns:
            List of resource names.
        """
        pass  # pragma: no cover - abstract method, pass statement never executed
