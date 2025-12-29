from _typeshed import Incomplete
from abc import ABC
from aip_agents.memory.constants import MemoryDefaults as MemoryDefaults
from aip_agents.tools.memory_search.schema import LongTermMemorySearchInput as LongTermMemorySearchInput, MemoryConfig as MemoryConfig
from aip_agents.utils.logger import get_logger as get_logger
from collections.abc import Callable
from langchain_core.tools import BaseTool
from pydantic import BaseModel as BaseModel
from typing import Any, ClassVar, Protocol

logger: Incomplete

class LongTermMemoryBackend(Protocol):
    """Protocol for memory adapters that support retrieval and formatting."""
    def retrieve(self, *, query: str | None, user_id: str, limit: int | None = None, filters: dict[str, Any] | None = None, page: int | None = None) -> list[dict[str, Any]]:
        """Retrieve memories matching the given query and filters.

        Args:
            query: Optional search query string.
            user_id: User identifier for scoped retrieval.
            limit: Maximum number of results to return.
            filters: Optional filters to apply to the retrieval.
            page: Page number for pagination.

        Returns:
            List of memory hit dictionaries.
        """
    def format_hits(self, hits: list[dict[str, Any]], max_items: int = ..., with_tag: bool = True) -> str:
        """Format memory hits into a readable string.

        Args:
            hits: List of memory hit dictionaries to format.
            max_items: Maximum number of hits to include in output.
            with_tag: Whether to wrap output with memory tags.

        Returns:
            Formatted string representation of memory hits.
        """

class LongTermMemorySearchTool(BaseTool, ABC):
    """Abstract base class for provider-specific long-term memory search tools."""
    name: str
    description: str
    args_schema: type[LongTermMemorySearchInput]
    tool_config_schema: type[BaseModel]
    memory: LongTermMemoryBackend
    default_user_id: str | None
    user_id_provider: Callable[[], str | None] | None
    MINIMUM_MEMORY_RETRIEVAL: ClassVar[int]
    LOG_PREFIX: ClassVar[str]
    def __init__(self, memory: LongTermMemoryBackend, *, default_user_id: str | None = None, user_id_provider: Callable[[], str | None] | None = None, **kwargs: Any) -> None:
        """Initialize the long-term memory search tool.

        Args:
            memory: Memory adapter instance with retrieve() and format_hits() methods.
            default_user_id: Default user ID to use if not provided in metadata.
            user_id_provider: Callable that returns a user ID.
            **kwargs: Additional keyword arguments passed to the parent class.
        """
    def format_hits(self, hits: list[dict[str, Any]], with_tag: bool = False) -> str:
        """Format hits into a string with optional tags.

        Args:
            hits: List of memory hit dictionaries to format.
            with_tag: Whether to wrap the output with memory tags.

        Returns:
            Formatted string representation of the memory hits.
        """
