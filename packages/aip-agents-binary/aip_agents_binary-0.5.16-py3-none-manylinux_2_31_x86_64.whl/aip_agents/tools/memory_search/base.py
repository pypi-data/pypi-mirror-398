"""Abstract base class for long-term memory search tools.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any, ClassVar, Protocol, runtime_checkable

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from pydantic import BaseModel

from aip_agents.memory.constants import MemoryDefaults
from aip_agents.tools.memory_search.schema import LongTermMemorySearchInput, MemoryConfig
from aip_agents.utils.logger import get_logger

logger = get_logger(__name__)


@runtime_checkable
class LongTermMemoryBackend(Protocol):
    """Protocol for memory adapters that support retrieval and formatting."""

    def retrieve(
        self,
        *,
        query: str | None,
        user_id: str,
        limit: int | None = None,
        filters: dict[str, Any] | None = None,
        page: int | None = None,
    ) -> list[dict[str, Any]]:
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
        ...

    def format_hits(
        self,
        hits: list[dict[str, Any]],
        max_items: int = MemoryDefaults.MAX_ITEMS,
        with_tag: bool = True,
    ) -> str:
        """Format memory hits into a readable string.

        Args:
            hits: List of memory hit dictionaries to format.
            max_items: Maximum number of hits to include in output.
            with_tag: Whether to wrap output with memory tags.

        Returns:
            Formatted string representation of memory hits.
        """
        ...


class LongTermMemorySearchTool(BaseTool, ABC):
    """Abstract base class for provider-specific long-term memory search tools."""

    name: str = "long_term_memory_search"
    description: str = "Abstract interface for tools that retrieve long-term memories."
    args_schema: type[LongTermMemorySearchInput] = LongTermMemorySearchInput
    tool_config_schema: type[BaseModel] = MemoryConfig
    memory: LongTermMemoryBackend
    default_user_id: str | None = None
    user_id_provider: Callable[[], str | None] | None = None
    MINIMUM_MEMORY_RETRIEVAL: ClassVar[int] = 5
    LOG_PREFIX: ClassVar[str] = "LongTermMemorySearchTool"

    def __init__(
        self,
        memory: LongTermMemoryBackend,
        *,
        default_user_id: str | None = None,
        user_id_provider: Callable[[], str | None] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the long-term memory search tool.

        Args:
            memory: Memory adapter instance with retrieve() and format_hits() methods.
            default_user_id: Default user ID to use if not provided in metadata.
            user_id_provider: Callable that returns a user ID.
            **kwargs: Additional keyword arguments passed to the parent class.
        """
        required_attributes = {"retrieve", "format_hits"}
        if not all(hasattr(memory, attr) for attr in required_attributes):
            raise ValueError(
                "LongTermMemorySearchTool requires a memory instance that implements retrieve() and format_hits()."
            )

        super().__init__(
            memory=memory,
            default_user_id=default_user_id,
            user_id_provider=user_id_provider,
            **kwargs,
        )

    @abstractmethod
    async def _arun(
        self,
        query: str | None = None,
        config: RunnableConfig | None = None,
        run_manager: Any | None = None,
        **kwargs: Any,
    ) -> str:
        """Execute provider-specific retrieval logic.

        Args:
            query: Optional search query string.
            config: Runnable configuration for the execution.
            run_manager: Optional run manager for execution tracking.
            **kwargs: Additional keyword arguments.

        Returns:
            Formatted string of retrieved memories.
        """

    def _run(
        self,
        query: str | None = None,
        config: RunnableConfig | None = None,
        run_manager: Any | None = None,
        **kwargs: Any,
    ) -> str:
        """Synchronous wrapper that delegates to `_arun` using `asyncio.run`.

        Args:
            query: Optional search query string.
            config: Runnable configuration for the execution.
            run_manager: Optional run manager for execution tracking.
            **kwargs: Additional keyword arguments.

        Returns:
            Formatted string of retrieved memories.
        """
        return asyncio.run(self._arun(query=query, config=config, run_manager=run_manager, **kwargs))

    def _resolve_user_id(self, metadata: dict[str, Any] | None, config: RunnableConfig | None = None) -> str:
        """Resolve the user ID for memory operations in a provider-agnostic way.

        Args:
            metadata: Optional metadata dictionary that may contain user_id.
            config: Optional runnable configuration for tool context.

        Returns:
            The resolved user ID string.
        """
        user_id: str | None = None

        if isinstance(metadata, dict):
            user_id = metadata.get("user_id")

        if not user_id and config and hasattr(self, "get_tool_config"):
            logger.info("%s: Resolving user_id from RunnableConfig", self.LOG_PREFIX)
            try:
                tool_config = self.get_tool_config(config)  # injected by tool_config_injector
                logger.info("%s: Injected tool_config: %s", self.LOG_PREFIX, tool_config)
                if tool_config and hasattr(tool_config, "user_id"):
                    user_id = tool_config.user_id
                    logger.info("%s: Using user_id from tool config: %s", self.LOG_PREFIX, user_id)
            except Exception as exc:  # noqa: BLE001
                logger.warning("%s: get_tool_config failed: %s", self.LOG_PREFIX, exc)

        if not user_id and self.user_id_provider:
            try:
                user_id = self.user_id_provider()
                logger.info("%s: Using user_id from provider: %s", self.LOG_PREFIX, user_id)
            except Exception as exc:  # noqa: BLE001
                logger.warning("%s: user_id_provider failed: %s", self.LOG_PREFIX, exc)

        resolved_user_id = user_id or self.default_user_id or MemoryDefaults.DEFAULT_USER_ID
        logger.info("%s: Resolved user_id: %s", self.LOG_PREFIX, resolved_user_id)
        return resolved_user_id

    def format_hits(self, hits: list[dict[str, Any]], with_tag: bool = False) -> str:
        """Format hits into a string with optional tags.

        Args:
            hits: List of memory hit dictionaries to format.
            with_tag: Whether to wrap the output with memory tags.

        Returns:
            Formatted string representation of the memory hits.
        """
        return self.memory.format_hits(hits, max_items=len(hits), with_tag=with_tag)
