from _typeshed import Incomplete
from aip_agents.middleware.base import AgentMiddleware as AgentMiddleware, ModelRequest as ModelRequest
from langchain_core.tools import BaseTool as BaseTool
from typing import Any

class MiddlewareManager:
    """Orchestrates multiple middleware components and manages hook execution.

    The manager collects tools from all middleware, builds enhanced system prompts,
    and executes lifecycle hooks in the correct order (forward for setup, reverse
    for cleanup).

    Attributes:
        middleware: List of middleware components in registration order.
    """
    middleware: Incomplete
    def __init__(self, middleware: list[AgentMiddleware]) -> None:
        """Initialize the middleware manager.

        Args:
            middleware: List of middleware components to manage. Order matters:
                       hooks execute forward (first to last) for before/modify,
                       and reverse (last to first) for after.
        """
    def get_all_tools(self) -> list[BaseTool]:
        """Collect tools from all registered middleware.

        Returns:
            Combined list of all tools contributed by all middleware components.
            Empty list if no middleware or if middleware provide no tools.
        """
    def build_system_prompt(self, base_instruction: str) -> str:
        """Build enhanced system prompt by concatenating base instruction with middleware additions.

        Args:
            base_instruction: The base system prompt for the agent.

        Returns:
            Enhanced system prompt with all middleware additions appended.
            If no middleware provide additions, returns base_instruction unchanged.
        """
    def before_model(self, state: dict[str, Any]) -> dict[str, Any]:
        """Execute before_model hooks for all middleware in forward order.

        Hooks run first to last, allowing earlier middleware to prepare state
        for later middleware.

        Args:
            state: Current agent state.

        Returns:
            Merged dictionary of all state updates from all middleware.
            Updates are accumulated in order of execution.
        """
    def modify_model_request(self, request: ModelRequest, state: dict[str, Any]) -> ModelRequest:
        """Execute modify_model_request hooks for all middleware in forward order.

        Each middleware receives the request modified by previous middleware,
        allowing them to build on each other's changes.

        Args:
            request: The model request to be modified.
            state: Current agent state for context.

        Returns:
            Final modified request after all middleware have processed it.
        """
    def after_model(self, state: dict[str, Any]) -> dict[str, Any]:
        """Execute after_model hooks for all middleware in reverse order.

        Hooks run last to first (reverse of registration order), allowing
        proper cleanup and unwinding of middleware operations.

        Args:
            state: Current agent state after model invocation.

        Returns:
            Merged dictionary of all state updates from all middleware.
            Updates are accumulated in reverse order of execution.
        """
