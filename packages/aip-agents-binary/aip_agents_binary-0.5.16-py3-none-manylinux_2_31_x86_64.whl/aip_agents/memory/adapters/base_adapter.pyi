from _typeshed import Incomplete
from aip_agents.memory.base import BaseMemory as BaseMemory
from aip_agents.memory.constants import MemoryDefaults as MemoryDefaults
from aip_agents.types import ChatMessage as ChatMessage
from aip_agents.utils.datetime import format_created_updated_label as format_created_updated_label
from aip_agents.utils.logger import get_logger as get_logger
from concurrent.futures import Future
from dataclasses import dataclass
from gllm_memory import MemoryManager
from gllm_memory.enums import MemoryScope
from typing import Any, ClassVar

MemoryManager = Any
MemoryScope = Any
logger: Incomplete
DEFAULT_SCOPE: ClassVar[set[MemoryScope]]

@dataclass(frozen=True)
class _RetrieveOptions:
    user_id: str
    top_k: int
    metadata: dict[str, str] | None
    keywords: Any
    page: int
    categories: list[str] | None

class _AsyncRunner:
    """Runs async coroutines on a dedicated background event loop."""
    def __init__(self) -> None: ...
    def run(self, awaitable: Any) -> Any:
        """Execute an awaitable on the background loop and block for the result.

        Args:
            awaitable: The coroutine to execute.

        Returns:
            The result of the coroutine execution.
        """
    def shutdown(self, timeout: float | None = 5.0) -> None:
        """Gracefully stop the event loop thread.

        Args:
            timeout: Maximum time to wait for the thread to stop.
        """
    def __del__(self) -> None: ...

class BaseMemoryAdapter(BaseMemory):
    """Provider-agnostic long-term memory adapter backed by gllm_memory."""
    agent_id: Incomplete
    namespace: Incomplete
    limit: Incomplete
    max_chars: Incomplete
    def __init__(self, *, agent_id: str, manager: MemoryManager, namespace: str | None = None, limit: int = ..., max_chars: int = ...) -> None:
        """Initialize the GLLM memory adapter.

        Args:
            agent_id: Unique identifier for the agent using this memory.
            manager: Configured gllm_memory MemoryManager instance.
            namespace: Optional namespace for organizing memories.
            limit: Maximum number of memories to retrieve in search operations.
            max_chars: Maximum character length for text content.
        """
    @classmethod
    def validate_env(cls) -> None:
        """Base adapter does not enforce environment validation."""
    def get_messages(self) -> list[ChatMessage]:
        """Retrieve all stored chat messages.

        Returns:
            An empty list as GLLM adapter doesn't support message retrieval.
        """
    def add_message(self, message: ChatMessage) -> None:
        """Best-effort single-message persistence for API parity.

        Args:
            message: The chat message to add to memory.
        """
    def clear(self) -> None:
        """Clear all stored memories.

        Raises:
            NotImplementedError: This method is not implemented for GLLM adapter.
        """
    def search(self, query: str, *, user_id: str, limit: int | None = None, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Search for memories using a text query.

        Args:
            query: The search query string.
            user_id: User identifier for the search scope.
            limit: Maximum number of results to return.
            filters: Optional filters to apply to the search.

        Returns:
            List of memory hits matching the search criteria.
        """
    def retrieve(self, *, query: str | None, user_id: str, limit: int | None = None, filters: dict[str, Any] | None = None, page: int | None = None) -> list[dict[str, Any]]:
        """Retrieve memories with optional search query and filters.

        Args:
            query: Optional search query string. If None, retrieves all memories.
            user_id: User identifier for the retrieval scope.
            limit: Maximum number of results to return.
            filters: Optional filters to apply to the retrieval.
            page: Page number for pagination.

        Returns:
            List of memory hits matching the criteria.
        """
    def save_interaction(self, *, user_text: str, ai_text: str, user_id: str) -> None:
        """Save a user-AI interaction as memories.

        Args:
            user_text: The user's input text.
            ai_text: The AI's response text.
            user_id: User identifier for the memory storage.
        """
    def save_interaction_async(self, *, user_text: str, ai_text: str, user_id: str) -> Future[Any]:
        """Schedule save_interaction without blocking the caller.

        Args:
            user_text: The user's input text to save.
            ai_text: The AI's response text to save.
            user_id: User identifier for the memory storage.
        """
    def format_hits(self, hits: list[dict[str, Any]], max_items: int = ..., with_tag: bool = True) -> str:
        """Format memory hits into a readable string.

        Args:
            hits: List of memory hit dictionaries to format.
            max_items: Maximum number of hits to include in the output.
            with_tag: Whether to wrap the output with memory tags.

        Returns:
            Formatted string representation of the memory hits.
        """
    def flush_pending_writes(self, timeout: float | None = None) -> None:
        """Block until current async writes complete.

        Args:
            timeout: Maximum time to wait for pending writes to complete.
        """
    def close(self, *, wait: bool = True, timeout: float | None = None) -> None:
        """Release background resources and optionally wait for pending saves.

        Args:
            wait: Whether to wait for pending async operations to complete.
            timeout: Maximum time to wait when wait=True.
        """
    def __del__(self) -> None:
        """Clean up resources when the adapter is garbage collected."""
