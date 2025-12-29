import threading
from _typeshed import Incomplete
from aip_agents.middleware.base import ModelRequest as ModelRequest
from aip_agents.utils.logger import get_logger as get_logger
from enum import StrEnum
from langchain_core.tools import BaseTool
from pydantic import BaseModel, SkipValidation
from typing import Any

logger: Incomplete

class TodoStatus(StrEnum):
    """Enumeration of possible todo item statuses."""
    PENDING: str
    IN_PROGRESS: str
    COMPLETED: str

WRITE_TODOS_SYSTEM_PROMPT: str
EMPTY_TODO_REMINDER: str

class TodoItem(BaseModel):
    """Represents a single todo item in the agent's plan.

    Attributes:
        content: Human-readable description of the task.
        active_form: Short imperative phrase for UI display.
        status: Current status of the todo item.
    """
    content: str
    active_form: str
    status: TodoStatus

class TodoList(BaseModel):
    """Represents a complete todo list for a thread.

    Attributes:
        items: List of todo items in order.
    """
    items: list[TodoItem]

WRITE_TODOS_TOOL_DESCRIPTION: str

class WriteTodosInput(BaseModel):
    """Input schema for the write_todos tool."""
    todos: TodoList

class WriteTodosTool(BaseTool):
    """LangChain-compatible tool for managing todo lists via TodoListMiddleware."""
    name: str
    description: str
    args_schema: type[BaseModel]
    storage: SkipValidation[dict[str, TodoList]]
    storage_lock: SkipValidation[threading.RLock]

class TodoListMiddleware:
    """Middleware that provides planning capabilities via todo list management.

    Adds the write_todos tool and enhances the system prompt with planning
    instructions, encouraging agents to break down complex tasks.

    This middleware maintains thread-isolated todo lists, ensuring that
    different conversation threads don't interfere with each other.

    Each middleware instance has its own storage, preventing race conditions
    when multiple agent instances are used concurrently.
    """
    tools: Incomplete
    system_prompt_additions: Incomplete
    def __init__(self) -> None:
        """Initialize the TodoList middleware with planning tools and instructions."""
    def before_model(self, state: dict[str, Any]) -> dict[str, Any]:
        """Hook executed before model invocation.

        Syncs todos FROM state TO internal storage for LangGraph agents.
        This allows todos to be persisted via LangGraph checkpointer.

        Args:
            state: Current agent state (may contain 'todos' key).

        Returns:
            Empty dict (no state updates needed).
        """
    def modify_model_request(self, request: ModelRequest, state: dict[str, Any]) -> ModelRequest:
        """Hook to modify model request before invocation.

        Injects current todo list status into the system prompt, ensuring
        the agent has visibility into its current plan on every turn.
        This follows Claude Code's pattern of injecting system reminders.

        Args:
            request: The model request.
            state: Current agent state.

        Returns:
            Modified request with todo status injected into system prompt.
        """
    def after_model(self, state: dict[str, Any]) -> dict[str, Any]:
        """Hook executed after model invocation.

        Syncs todos FROM internal storage TO state for LangGraph agents.
        This ensures any tool updates are reflected in the checkpointed state.

        Args:
            state: Current agent state.

        Returns:
            Dict with 'todos' key containing updated TodoList, or empty dict.
        """
    def get_todos(self, thread_id: str = 'default') -> TodoList:
        '''Retrieve the todo list for a specific thread.

        Args:
            thread_id: Thread identifier. Defaults to "default".

        Returns:
            TodoList for the thread, or empty list if none exists.
        '''
    def clear_todos(self, thread_id: str = 'default') -> None:
        '''Clear the todo list for a specific thread.

        Useful for cleanup between test runs or conversation resets.

        Args:
            thread_id: Thread identifier. Defaults to "default".
        '''
