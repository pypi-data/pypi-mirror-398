"""Base protocol and types for agent middleware.

This module defines the core AgentMiddleware protocol that all middleware components
must implement, along with the ModelRequest type for model invocations.
"""

from typing import Any, Protocol, TypedDict

from langchain_core.tools import BaseTool


class ModelRequest(TypedDict, total=False):
    """Represents parameters for a model invocation that middleware can modify.

    This TypedDict defines the structure of requests passed to the LLM, allowing
    middleware to add tools or modify prompts before each invocation.

    Attributes:
        messages: List of messages in the conversation.
        tools: List of tools available to the model.
        system_prompt: System-level instruction for the model.
    """

    messages: list[Any]
    tools: list[BaseTool]
    system_prompt: str


class AgentMiddleware(Protocol):
    """Protocol defining the interface for composable agent middleware.

    Middleware components can contribute tools, enhance system prompts, and provide
    lifecycle hooks that execute before, during, and after model invocations.

    All middleware must implement this protocol to be compatible with MiddlewareManager.

    Attributes:
        tools: List of tools contributed by this middleware.
        system_prompt_additions: Optional text to append to the agent's system prompt.
    """

    tools: list[BaseTool]
    system_prompt_additions: str | None

    def before_model(self, state: dict[str, Any]) -> dict[str, Any]:
        """Hook executed before each model invocation.

        Use this hook to prepare state, log context, or perform setup tasks
        before the model is called.

        Args:
            state: Current agent state containing messages and other context.

        Returns:
            Dict of state updates to merge into the agent state. Return empty dict
            if no updates are needed.
        """
        return {}  # pragma: no cover  # Protocol default - cannot be executed directly

    def modify_model_request(self, request: ModelRequest, state: dict[str, Any]) -> ModelRequest:
        """Hook to modify the model request before invocation.

        Use this hook to add tools, modify the system prompt, adjust model parameters,
        or change tool selection strategy.

        Args:
            request: The model request that will be sent to the LLM.
            state: Current agent state for context.

        Returns:
            Modified ModelRequest. Can return the same request if no changes needed.
        """
        return request  # pragma: no cover  # Protocol default - cannot be executed directly  # pragma: no cover  # Protocol default - cannot be executed directly

    def after_model(self, state: dict[str, Any]) -> dict[str, Any]:
        """Hook executed after each model invocation.

        Use this hook for cleanup, logging, state updates, or post-processing
        of model outputs.

        Args:
            state: Current agent state after model invocation.

        Returns:
            Dict of state updates to merge into the agent state. Return empty dict
            if no updates are needed.
        """
        return {}  # pragma: no cover  # Protocol default - cannot be executed directly
