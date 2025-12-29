"""Middleware orchestration and lifecycle management.

This module provides MiddlewareManager, which coordinates multiple middleware
components and manages their lifecycle hooks.
"""

from typing import Any

from langchain_core.tools import BaseTool

from aip_agents.middleware.base import AgentMiddleware, ModelRequest


class MiddlewareManager:
    """Orchestrates multiple middleware components and manages hook execution.

    The manager collects tools from all middleware, builds enhanced system prompts,
    and executes lifecycle hooks in the correct order (forward for setup, reverse
    for cleanup).

    Attributes:
        middleware: List of middleware components in registration order.
    """

    def __init__(self, middleware: list[AgentMiddleware]) -> None:
        """Initialize the middleware manager.

        Args:
            middleware: List of middleware components to manage. Order matters:
                       hooks execute forward (first to last) for before/modify,
                       and reverse (last to first) for after.
        """
        self.middleware = middleware

    def get_all_tools(self) -> list[BaseTool]:
        """Collect tools from all registered middleware.

        Returns:
            Combined list of all tools contributed by all middleware components.
            Empty list if no middleware or if middleware provide no tools.
        """
        tools: list[BaseTool] = []
        for mw in self.middleware:
            tools.extend(mw.tools)
        return tools

    def build_system_prompt(self, base_instruction: str) -> str:
        """Build enhanced system prompt by concatenating base instruction with middleware additions.

        Args:
            base_instruction: The base system prompt for the agent.

        Returns:
            Enhanced system prompt with all middleware additions appended.
            If no middleware provide additions, returns base_instruction unchanged.
        """
        parts = [base_instruction]

        for mw in self.middleware:
            if mw.system_prompt_additions:
                parts.append(mw.system_prompt_additions)

        return "\n\n".join(parts)

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
        state_updates: dict[str, Any] = {}

        for mw in self.middleware:
            mw_updates = mw.before_model(state)
            if mw_updates:
                state_updates.update(mw_updates)

        return state_updates

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
        current_request = request

        for mw in self.middleware:
            current_request = mw.modify_model_request(current_request, state)

        return current_request

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
        updates: dict[str, Any] = {}

        # Execute in reverse order
        for mw in reversed(self.middleware):
            mw_updates = mw.after_model(state)
            if mw_updates:
                updates.update(mw_updates)

        return updates
