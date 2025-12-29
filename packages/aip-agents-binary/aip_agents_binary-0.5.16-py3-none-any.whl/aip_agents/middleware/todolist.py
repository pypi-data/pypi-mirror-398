"""TodoList middleware for agent planning and task decomposition.

Provides a write_todos tool that allows agents to break down complex tasks
into discrete, trackable steps with status management.
"""

import threading
from enum import StrEnum
from typing import Any

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field, SkipValidation

from aip_agents.middleware.base import ModelRequest
from aip_agents.utils.logger import get_logger

logger = get_logger(__name__)


class TodoStatus(StrEnum):
    """Enumeration of possible todo item statuses."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


WRITE_TODOS_SYSTEM_PROMPT = """## Task Planning with `write_todos`

Use `write_todos` to plan and track complex multi-step objectives (3+ steps, multiple deliverables, or tasks described as "comprehensive"). Skip for trivial single-action requests.

**Execution rules:**
1. Create the plan with `write_todos` BEFORE executing work
2. Execute ALL tasks autonomously—do NOT pause to ask "should I continue?" or "would you like a preview?"
3. Revise the plan as needed when new information emerges
4. Mark tasks completed as you finish them
5. **CRITICAL: Before your final response, call `write_todos` one last time to mark ALL tasks as `completed`. Never respond to the user while any task is `pending` or `in_progress`.**
"""

EMPTY_TODO_REMINDER = (
    "\n\n**Todo List Reminder:** Your todo list is currently empty. "
    "If you are working on tasks that would benefit from a todo list, "
    "use the write_todos tool to create one. This helps track progress "
    "and ensures you don't forget important steps.\n"
)


class TodoItem(BaseModel):
    """Represents a single todo item in the agent's plan.

    Attributes:
        content: Human-readable description of the task.
        active_form: Short imperative phrase for UI display.
        status: Current status of the todo item.
    """

    content: str = Field(description="Description of what needs to be done")
    active_form: str = Field(description="Short active form for display (e.g., 'researching topic')")
    status: TodoStatus = Field(default=TodoStatus.PENDING, description="Current status of this todo")


class TodoList(BaseModel):
    """Represents a complete todo list for a thread.

    Attributes:
        items: List of todo items in order.
    """

    items: list[TodoItem] = Field(default_factory=list)


WRITE_TODOS_TOOL_DESCRIPTION = """Create and manage a structured task list for complex work sessions (3+ steps).

## When to Use
- Multi-step tasks with 3+ distinct steps
- Requests with multiple deliverables
- User provides a list of tasks
- User explicitly requests a todo list

## When to Skip
- Single straightforward action
- Trivial tasks with no tracking benefit

## Task States
- `pending`: Not started
- `in_progress`: Currently working
- `completed`: Fully finished

## Workflow
1. **Plan first**: Call `write_todos` before executing work. Mark first task(s) as `in_progress`.
2. **Stay autonomous**: Execute all tasks without pausing for user confirmation.
3. **Adapt the plan**: Add new tasks as discovered, remove irrelevant ones.
4. **Mark progress**: Update task status as you complete work.
5. **Final update**: Before responding to user, call `write_todos` to mark ALL remaining tasks `completed`.

## CRITICAL: Final Response Rule
You must NOT respond to the user until EVERY task is marked `completed`. Your final action before responding should be a `write_todos` call that marks the last task(s) complete. If any task remains `pending` or `in_progress`, you are not done—keep working or update the plan."""


class WriteTodosInput(BaseModel):
    """Input schema for the write_todos tool."""

    todos: TodoList = Field(
        ...,
        description="List of todo items, each with 'content' and 'activeForm' keys.",
    )


class WriteTodosTool(BaseTool):
    """LangChain-compatible tool for managing todo lists via TodoListMiddleware."""

    name: str = "write_todos_tool"
    description: str = WRITE_TODOS_TOOL_DESCRIPTION
    args_schema: type[BaseModel] = WriteTodosInput

    # Instance reference to middleware storage (excluded from serialization, skip validation)
    storage: SkipValidation[dict[str, TodoList]] = Field(default_factory=dict, exclude=True)
    storage_lock: SkipValidation[threading.RLock] = Field(default_factory=threading.RLock, exclude=True)

    def _run(self, todos: TodoList, config: RunnableConfig | None = None) -> str:  # type: ignore[override]
        """Synchronous entrypoint used by generic tool runners.

        Args:
            todos: The todo list to write.
            config: Optional configuration for the tool run.

        Returns:
            str: A success message indicating the number of todo items written.
        """
        tid = "default"
        if config and "configurable" in config:
            tid = config["configurable"].get("thread_id", "default")

        try:
            # Store in thread-safe manner
            with self.storage_lock:
                self.storage[tid] = todos

            return f"Successfully wrote {len(todos.items)} todo items to your plan."
        except Exception as e:  # pragma: no cover - defensive
            return f"Error writing todos: {str(e)}"


class TodoListMiddleware:
    """Middleware that provides planning capabilities via todo list management.

    Adds the write_todos tool and enhances the system prompt with planning
    instructions, encouraging agents to break down complex tasks.

    This middleware maintains thread-isolated todo lists, ensuring that
    different conversation threads don't interfere with each other.

    Each middleware instance has its own storage, preventing race conditions
    when multiple agent instances are used concurrently.
    """

    def __init__(self) -> None:
        """Initialize the TodoList middleware with planning tools and instructions."""
        # Instance-level storage to prevent race conditions across agent instances
        self._storage: dict[str, TodoList] = {}
        self._storage_lock = threading.RLock()

        # Create tool with reference to this instance's storage
        self.tools = [WriteTodosTool(storage=self._storage, storage_lock=self._storage_lock)]
        self.system_prompt_additions = WRITE_TODOS_SYSTEM_PROMPT

    def before_model(self, state: dict[str, Any]) -> dict[str, Any]:
        """Hook executed before model invocation.

        Syncs todos FROM state TO internal storage for LangGraph agents.
        This allows todos to be persisted via LangGraph checkpointer.

        Args:
            state: Current agent state (may contain 'todos' key).

        Returns:
            Empty dict (no state updates needed).
        """
        # Sync from LangGraph state to internal storage (if state has todos)
        if "todos" in state and state["todos"] is not None:
            thread_id = state.get("thread_id", "default")

            # Deep copy to prevent mutation issues between state and storage
            with self._storage_lock:
                self._storage[thread_id] = state["todos"].model_copy(deep=True)

        return {}

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
        thread_id = state.get("thread_id", "default")

        # Get current todos from storage
        with self._storage_lock:
            current_todos = self._storage.get(thread_id)

        # Inject todo status into system prompt
        if current_todos and current_todos.items:
            # Build todo status reminder
            todo_reminder = "\n\n## Current Todo List Status\n\n"
            todo_reminder += "Your current todo list:\n"

            for item in current_todos.items:
                todo_reminder += f"[{item.status.value.upper()}] {item.content}\n"

            todo_reminder += "\n**Remember to update the todo list as you complete tasks using write_todos.**\n"

            # Append to system prompt
            current_system_prompt = request.get("system_prompt", "")
            request["system_prompt"] = current_system_prompt + todo_reminder
        else:
            # Static reminder when no todos exist
            current_system_prompt = request.get("system_prompt", "")
            request["system_prompt"] = current_system_prompt + EMPTY_TODO_REMINDER

        return request

    def after_model(self, state: dict[str, Any]) -> dict[str, Any]:
        """Hook executed after model invocation.

        Syncs todos FROM internal storage TO state for LangGraph agents.
        This ensures any tool updates are reflected in the checkpointed state.

        Args:
            state: Current agent state.

        Returns:
            Dict with 'todos' key containing updated TodoList, or empty dict.
        """
        thread_id = state.get("thread_id", "default")

        with self._storage_lock:
            if thread_id in self._storage:
                # Deep copy to prevent mutation issues between storage and state
                return {"todos": self._storage[thread_id].model_copy(deep=True)}

        return {}

    def get_todos(self, thread_id: str = "default") -> TodoList:
        """Retrieve the todo list for a specific thread.

        Args:
            thread_id: Thread identifier. Defaults to "default".

        Returns:
            TodoList for the thread, or empty list if none exists.
        """
        with self._storage_lock:
            return self._storage.get(thread_id, TodoList())

    def clear_todos(self, thread_id: str = "default") -> None:
        """Clear the todo list for a specific thread.

        Useful for cleanup between test runs or conversation resets.

        Args:
            thread_id: Thread identifier. Defaults to "default".
        """
        with self._storage_lock:
            if thread_id in self._storage:
                del self._storage[thread_id]
