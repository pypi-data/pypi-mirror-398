from _typeshed import Incomplete
from aip_agents.tools.constants import ToolType as ToolType
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from typing import Any

class _InjectedTool(BaseTool):
    """Wrap a BaseTool to inject token and optional identifier into inputs."""
    model_config: Incomplete
    def __init__(self, base_tool: BaseTool, token: str, identifier: str | None) -> None:
        """Initialize the injected tool wrapper.

        Args:
            base_tool: The base tool to wrap.
            token: Authentication token to inject into tool inputs.
            identifier: Optional identifier to inject into tool inputs.

        Returns:
            None
        """
    def invoke(self, input: Any, config: RunnableConfig | None = None, **kwargs: Any) -> Any:
        """Invoke the tool with token and optional identifier injected.

        Args:
            input: Tool input to process.
            config: Optional runnable configuration.
            **kwargs: Additional keyword arguments.

        Returns:
            The result of invoking the tool with injected parameters.
        """
    async def ainvoke(self, input: Any, config: RunnableConfig | None = None, **kwargs: Any) -> Any:
        """Invoke the tool asynchronously with token and optional identifier injected.

        Args:
            input: Tool input to process.
            config: Optional runnable configuration.
            **kwargs: Additional keyword arguments.

        Returns:
            The result of invoking the tool with injected parameters.
        """
    def run(self, tool_input: Any, **kwargs: Any) -> Any:
        """Run the tool with token and optional identifier injected.

        Args:
            tool_input: Tool input to process.
            **kwargs: Additional keyword arguments.

        Returns:
            The result of running the tool with injected parameters.
        """
    async def arun(self, tool_input: Any, **kwargs: Any) -> Any:
        """Run the tool asynchronously with token and optional identifier injected.

        Args:
            tool_input: Tool input to process.
            **kwargs: Additional keyword arguments.

        Returns:
            The result of running the tool with injected parameters.
        """

def GLConnectorTool(tool_name: str, *, api_key: str | None = None, identifier: str | None = None) -> BaseTool:
    """Create a single GL Connector tool by exact tool name.

    Args:
        tool_name: Exact tool name (not module name).
        api_key: Optional override for BOSA API key.
        identifier: Optional override for BOSA identifier.

    Returns:
        A single LangChain BaseTool with token injection.
    """
