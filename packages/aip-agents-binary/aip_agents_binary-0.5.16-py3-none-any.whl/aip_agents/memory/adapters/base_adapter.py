"""Base adapter that bridges aip-agents BaseMemory to async memory managers.

This adapter hides the async nature of gllm_memory.MemoryManager (or any future
async provider) behind the existing synchronous BaseMemory contract so downstream
LangGraph/LangChain components can continue using blocking calls.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

import asyncio
import threading
from concurrent.futures import Future, ThreadPoolExecutor
from contextlib import suppress
from dataclasses import dataclass
from datetime import datetime, timedelta
from time import perf_counter
from typing import Any, ClassVar

from gllm_core.schema import Chunk
from gllm_inference.schema.message import Message

try:
    from gllm_memory import MemoryManager
    from gllm_memory.enums import MemoryScope

    _HAS_GLLM_MEMORY = True
except ImportError:  # pragma: no cover
    MemoryManager = Any  # type: ignore[assignment]
    MemoryScope = Any  # type: ignore[assignment]
    _HAS_GLLM_MEMORY = False

from aip_agents.memory.base import BaseMemory
from aip_agents.memory.constants import MemoryDefaults
from aip_agents.types import ChatMessage
from aip_agents.utils.datetime import format_created_updated_label
from aip_agents.utils.logger import get_logger

logger = get_logger(__name__)


def _require_gllm_memory() -> None:
    if not _HAS_GLLM_MEMORY:
        raise ImportError("optional dependency 'gllm-memory' is required for memory adapters")


if _HAS_GLLM_MEMORY:
    DEFAULT_SCOPE: ClassVar[set[MemoryScope]] = {MemoryScope.USER}
else:
    DEFAULT_SCOPE: ClassVar[set[Any]] = set()


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

    def __init__(self) -> None:
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._loop.run_forever, daemon=True)
        self._thread.start()
        self._shutdown = False

    def run(self, awaitable: Any) -> Any:
        """Execute an awaitable on the background loop and block for the result.

        Args:
            awaitable: The coroutine to execute.

        Returns:
            The result of the coroutine execution.
        """
        if self._shutdown:
            raise RuntimeError("AsyncRunner has been shut down")
        future = asyncio.run_coroutine_threadsafe(awaitable, self._loop)
        return future.result()

    def shutdown(self, timeout: float | None = 5.0) -> None:
        """Gracefully stop the event loop thread.

        Args:
            timeout: Maximum time to wait for the thread to stop.
        """
        if self._shutdown:
            return
        self._shutdown = True
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join(timeout)
        with suppress(Exception):
            self._loop.close()

    def __del__(self) -> None:  # pragma: no cover - best effort cleanup
        with suppress(Exception):
            self.shutdown(timeout=0)


class BaseMemoryAdapter(BaseMemory):
    """Provider-agnostic long-term memory adapter backed by gllm_memory."""

    def __init__(
        self,
        *,
        agent_id: str,
        manager: MemoryManager,
        namespace: str | None = None,
        limit: int = MemoryDefaults.RETRIEVAL_LIMIT,
        max_chars: int = MemoryDefaults.MAX_CHARS,
    ) -> None:
        """Initialize the GLLM memory adapter.

        Args:
            agent_id: Unique identifier for the agent using this memory.
            manager: Configured gllm_memory MemoryManager instance.
            namespace: Optional namespace for organizing memories.
            limit: Maximum number of memories to retrieve in search operations.
            max_chars: Maximum character length for text content.
        """
        _require_gllm_memory()

        self.agent_id = agent_id or MemoryDefaults.DEFAULT_USER_ID
        self.namespace = namespace
        self.limit = int(limit)
        self.max_chars = int(max_chars)

        self._manager = manager
        self._runner = _AsyncRunner()
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="memory-save")
        self._pending_futures: set[Future[Any]] = set()
        self._futures_lock = threading.Lock()
        self._closed = False

    @classmethod
    def validate_env(
        cls,
    ) -> None:  # pragma: no cover - base adapter has no env requirements
        """Base adapter does not enforce environment validation."""
        return None

    # ------------------------------------------------------------------ #
    # BaseMemory interface
    # ------------------------------------------------------------------ #

    def get_messages(self) -> list[ChatMessage]:
        """Retrieve all stored chat messages.

        Returns:
            An empty list as GLLM adapter doesn't support message retrieval.
        """
        return []

    def add_message(self, message: ChatMessage) -> None:
        """Best-effort single-message persistence for API parity.

        Args:
            message: The chat message to add to memory.
        """
        try:
            self._runner.run(
                self._manager.add(
                    user_id=self.agent_id,
                    agent_id=self.agent_id,
                    messages=[self._to_message(message)],
                    scopes=DEFAULT_SCOPE,
                    infer=False,
                )
            )
        except Exception as exc:  # noqa: BLE001
            logger.debug("BaseMemoryAdapter.add_message ignored error: %s", exc)

    def clear(self) -> None:
        """Clear all stored memories.

        Raises:
            NotImplementedError: This method is not implemented for GLLM adapter.
        """
        raise NotImplementedError("clear() is not implemented for BaseMemoryAdapter.")

    # ------------------------------------------------------------------ #
    # Legacy Mem0Memory-compatible surface area
    # ------------------------------------------------------------------ #

    def search(
        self,
        query: str,
        *,
        user_id: str,
        limit: int | None = None,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Search for memories using a text query.

        Args:
            query: The search query string.
            user_id: User identifier for the search scope.
            limit: Maximum number of results to return.
            filters: Optional filters to apply to the search.

        Returns:
            List of memory hits matching the search criteria.
        """
        return self.retrieve(query=query, user_id=user_id, limit=limit, filters=filters)

    def retrieve(
        self,
        *,
        query: str | None,
        user_id: str,
        limit: int | None = None,
        filters: dict[str, Any] | None = None,
        page: int | None = None,
    ) -> list[dict[str, Any]]:
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
        options = self._build_retrieve_options(
            user_id=user_id,
            limit=limit,
            filters=filters,
            page=page,
        )
        try:
            start = perf_counter()
            chunks = self._runner.run(self._create_retrieve_task(query, options))
            duration = perf_counter() - start
            logger.info(
                "BaseMemoryAdapter: retrieve user_id='%s' query='%s' limit=%s returned %d hits in %.2fs (filters=%s)",
                user_id,
                query,
                options.top_k,
                len(chunks),
                duration,
                options.metadata,
            )
        except Exception as exc:  # noqa: BLE001
            logger.debug("BaseMemoryAdapter.retrieve ignored error: %s", exc)
            return []

        return [self._chunk_to_hit(chunk) for chunk in chunks]

    def save_interaction(self, *, user_text: str, ai_text: str, user_id: str) -> None:
        """Save a user-AI interaction as memories.

        Args:
            user_text: The user's input text.
            ai_text: The AI's response text.
            user_id: User identifier for the memory storage.
        """
        truncated_user = str(user_text)[: self.max_chars]
        truncated_ai = str(ai_text)[: self.max_chars]
        messages = [
            Message.user(contents=truncated_user),
            Message.assistant(contents=truncated_ai),
        ]
        preview_user = truncated_user[: MemoryDefaults.LOG_PREVIEW_LENGTH]
        preview_ai = truncated_ai[: MemoryDefaults.LOG_PREVIEW_LENGTH]
        logger.info(
            "BaseMemoryAdapter: saving interaction user_id='%s' user_preview='%s%s' ai_preview='%s%s'",
            user_id,
            preview_user,
            "..." if len(truncated_user) > len(preview_user) else "",
            preview_ai,
            "..." if len(truncated_ai) > len(preview_ai) else "",
        )
        try:
            start = perf_counter()
            self._runner.run(
                self._manager.add(
                    user_id=user_id or self.agent_id,
                    agent_id=self.agent_id,
                    messages=messages,
                    scopes=DEFAULT_SCOPE,
                )
            )
            duration = perf_counter() - start
            logger.info(
                "BaseMemoryAdapter: save_interaction completed for user_id='%s' in %.2fs",
                user_id,
                duration,
            )
        except Exception as exc:  # noqa: BLE001
            logger.debug("BaseMemoryAdapter.save_interaction ignored error: %s", exc)

    def save_interaction_async(self, *, user_text: str, ai_text: str, user_id: str) -> Future[Any]:
        """Schedule save_interaction without blocking the caller.

        Args:
            user_text: The user's input text to save.
            ai_text: The AI's response text to save.
            user_id: User identifier for the memory storage.
        """
        future = self._executor.submit(
            self.save_interaction,
            user_text=user_text,
            ai_text=ai_text,
            user_id=user_id,
        )
        with self._futures_lock:
            self._pending_futures.add(future)

        def _on_complete(done: Future[Any]) -> None:
            """Discard a completed future from the pending set and log failures.

            Args:
                done: Future returned by the executor for save_interaction.
            """
            with self._futures_lock:
                self._pending_futures.discard(done)
            exc = done.exception()
            if exc:
                logger.warning(
                    "BaseMemoryAdapter: async save failed for user_id='%s': %s",
                    user_id,
                    exc,
                )

        future.add_done_callback(_on_complete)
        return future

    def format_hits(
        self,
        hits: list[dict[str, Any]],
        max_items: int = MemoryDefaults.MAX_ITEMS,
        with_tag: bool = True,
    ) -> str:
        """Format memory hits into a readable string.

        Args:
            hits: List of memory hit dictionaries to format.
            max_items: Maximum number of hits to include in the output.
            with_tag: Whether to wrap the output with memory tags.

        Returns:
            Formatted string representation of the memory hits.
        """
        lines: list[str] = []
        for hit in hits[:max_items]:
            if not isinstance(hit, dict):
                lines.append(f"- {hit}")
                continue
            text = hit.get("memory") or hit.get("text") or hit.get("content")
            if not text:
                text = str(hit)
            label = format_created_updated_label(hit.get("created_at"), hit.get("updated_at"))
            prefix = f"- [{label}] " if label else "- "
            lines.append(f"{prefix}{text}")

        if not lines:
            logger.info("BaseMemoryAdapter: No memories to format for prompt")
            return ""

        formatted_memory = (
            f"{MemoryDefaults.MEMORY_TAG_OPEN}\n" + "\n".join(lines) + f"\n{MemoryDefaults.MEMORY_TAG_CLOSE}\n\n"
            if with_tag
            else "\n".join(lines)
        )
        logger.info("BaseMemoryAdapter: Formatted %s memories for prompt", len(lines))
        logger.info(
            "BaseMemoryAdapter: Prompt memory block:%s%s",
            "\n" if lines else " ",
            formatted_memory.strip(),
        )
        return formatted_memory

    def flush_pending_writes(self, timeout: float | None = None) -> None:
        """Block until current async writes complete.

        Args:
            timeout: Maximum time to wait for pending writes to complete.
        """
        futures = self._snapshot_pending_futures()
        for future in futures:
            try:
                future.result(timeout=timeout)
            except Exception as exc:  # noqa: BLE001
                logger.warning("BaseMemoryAdapter: Pending async save raised: %s", exc)

    def close(self, *, wait: bool = True, timeout: float | None = None) -> None:
        """Release background resources and optionally wait for pending saves.

        Args:
            wait: Whether to wait for pending async operations to complete.
            timeout: Maximum time to wait when wait=True.
        """
        if self._closed:
            return
        self._closed = True
        if wait:
            self.flush_pending_writes(timeout=timeout)
        self._executor.shutdown(wait=wait, cancel_futures=not wait)
        self._runner.shutdown()

    def __del__(self) -> None:  # pragma: no cover - best effort cleanup
        """Clean up resources when the adapter is garbage collected."""
        with suppress(Exception):
            self.close(wait=False)

    def _snapshot_pending_futures(self) -> list[Future[Any]]:
        with self._futures_lock:
            return list(self._pending_futures)

    def _call_manager_with_optional_categories(
        self,
        func: Any,
        *,
        categories: list[str] | None,
        **kwargs: Any,
    ) -> Any:
        """Invoke a MemoryManager coroutine, retrying without categories if unsupported.

        Args:
            func: The MemoryManager method to call.
            categories: Optional categories to pass to the method.
            **kwargs: Additional keyword arguments to pass to the method.

        Returns:
            The result of calling the MemoryManager method.
        """
        if categories:
            try:
                return func(categories=categories, **kwargs)
            except TypeError:
                logger.debug(
                    "BaseMemoryAdapter: '%s' does not accept categories, retrying without it",
                    getattr(func, "__name__", func),
                )
        return func(**kwargs)

    # ------------------------------------------------------------------ #
    # Helper utilities
    # ------------------------------------------------------------------ #

    def _build_retrieve_options(
        self,
        *,
        user_id: str,
        limit: int | None,
        filters: dict[str, Any] | None,
        page: int | None,
    ) -> _RetrieveOptions:
        """Assemble normalized retrieval options for the MemoryManager.

        Args:
            user_id: Optional user identifier requesting the memory retrieval.
            limit: Maximum number of items to return.
            filters: Raw filter payload supplied by the caller.
            page: Page number for paginated listing operations.

        Returns:
            _RetrieveOptions instance consumed by downstream search/list calls.
        """
        effective_user = user_id or self.agent_id or MemoryDefaults.DEFAULT_USER_ID
        top_k = int(limit) if limit is not None else self.limit
        normalized_filters = self._normalize_filters(filters or {})
        metadata_payload = self._build_metadata_payload(normalized_filters)
        keywords = normalized_filters.get("keywords")
        categories = normalized_filters.get("categories")
        return _RetrieveOptions(
            user_id=effective_user,
            top_k=top_k,
            metadata=metadata_payload,
            keywords=keywords,
            page=page or 1,
            categories=list(categories) if isinstance(categories, list) else categories,
        )

    def _create_retrieve_task(self, query: str | None, options: _RetrieveOptions) -> Any:
        """Build the manager coroutine to execute for search/list requests.

        Args:
            query: Optional search query to execute against the memories.
            options: Prepared retrieval options containing metadata and pagination.

        Returns:
            Awaitable returned by the MemoryManager search or list method.
        """
        if query:
            return self._call_manager_with_optional_categories(
                self._manager.search,
                categories=options.categories,
                query=query,
                user_id=options.user_id,
                agent_id=self.agent_id,
                scopes=DEFAULT_SCOPE,
                metadata=options.metadata,
                top_k=options.top_k,
            )
        return self._call_manager_with_optional_categories(
            self._manager.list_memories,
            categories=options.categories,
            user_id=options.user_id,
            agent_id=self.agent_id,
            scopes=DEFAULT_SCOPE,
            metadata=options.metadata,
            keywords=options.keywords,
            page=options.page,
            page_size=options.top_k,
        )

    def _normalize_filters(self, filters: dict[str, Any]) -> dict[str, Any]:
        """Normalize filters from legacy AND/OR format to the expected structure.

        Args:
            filters: Raw filter dictionary that may use legacy format.

        Returns:
            Normalized filter dictionary.
        """
        if self._is_legacy_filter_format(filters):
            return self._convert_legacy_filters(filters)
        return filters

    @staticmethod
    def _is_legacy_filter_format(filters: dict[str, Any]) -> bool:
        """Return True when the filters dict uses legacy AND/OR syntax.

        Args:
            filters: Filter dictionary to check.

        Returns:
            True if the filters use legacy AND/OR syntax.
        """
        if not isinstance(filters, dict):
            return False
        return "AND" in filters or "OR" in filters

    @staticmethod
    def _convert_legacy_filters(filters: dict[str, Any]) -> dict[str, Any]:
        """Convert AND/OR style legacy filters into the normalized structure.

        Args:
            filters: Legacy filter payload coming from older clients.

        Returns:
            Dictionary with metadata, categories, and date range keys.
        """
        normalized: dict[str, Any] = {
            "metadata": {},
            "categories": None,
            "start_time": None,
            "end_time": None,
        }

        clauses = filters.get("AND", [])
        for clause in clauses:
            if not isinstance(clause, dict):
                continue
            BaseMemoryAdapter._process_clause(clause, normalized)

        return normalized

    @staticmethod
    def _process_clause(clause: dict[str, Any], normalized: dict[str, Any]) -> None:
        """Process a single clause and update the normalized filters.

        Args:
            clause: Single filter clause to process.
            normalized: Dictionary to update with normalized filter values.
        """
        if "created_at" in clause and isinstance(clause["created_at"], dict):
            BaseMemoryAdapter._process_created_at_clause(clause["created_at"], normalized)
        elif "categories" in clause and isinstance(clause["categories"], dict):
            BaseMemoryAdapter._process_categories_clause(clause["categories"], normalized)
        elif "metadata" in clause and isinstance(clause["metadata"], dict):
            normalized["metadata"].update(clause["metadata"])

    @staticmethod
    def _process_created_at_clause(created_filter: dict[str, Any], normalized: dict[str, Any]) -> None:
        """Process created_at clause for date filtering.

        Args:
            created_filter: Created date filter criteria.
            normalized: Dictionary to update with normalized date values.
        """
        start_candidate = created_filter.get("gte") or created_filter.get("gt")
        end_candidate = created_filter.get("lte") or created_filter.get("lt")
        if start_candidate:
            normalized["start_time"] = start_candidate
        if end_candidate:
            normalized["end_time"] = BaseMemoryAdapter._restore_end_date(created_filter)

    @staticmethod
    def _process_categories_clause(categories_filter: dict[str, Any], normalized: dict[str, Any]) -> None:
        """Process categories clause for category filtering.

        Args:
            categories_filter: Categories filter criteria.
            normalized: Dictionary to update with normalized category values.
        """
        cats = categories_filter.get("in")
        if cats:
            normalized["categories"] = list(cats)

    @staticmethod
    def _restore_end_date(created_filter: dict[str, Any]) -> str | None:
        """Convert exclusive lt filters back to the user's original end date.

        Args:
            created_filter: Dictionary containing date filter criteria.

        Returns:
            The restored end date string, or None if not applicable.
        """
        end_candidate = created_filter.get("lte") or created_filter.get("lt")
        if end_candidate is None:
            return None
        if "lt" in created_filter and "lte" not in created_filter:
            try:
                dt = datetime.strptime(end_candidate, "%Y-%m-%d") - timedelta(days=1)
                return dt.date().isoformat()
            except ValueError:
                return end_candidate
        return end_candidate

    @staticmethod
    def _build_metadata_payload(
        filters: dict[str, Any] | None,
    ) -> dict[str, str] | None:
        """Create the metadata payload expected by the MemoryManager APIs.

        Args:
            filters: Normalized filter dictionary built from user input.

        Returns:
            Dictionary of metadata strings or None when no metadata was provided.
        """
        if not filters:
            return None

        metadata: dict[str, str] = {}

        raw_metadata = filters.get("metadata") or {}
        for key, value in raw_metadata.items():
            if value is None:
                continue
            metadata[key] = str(value)

        start_time = filters.get("start_time")
        end_time = filters.get("end_time")
        if start_time:
            metadata["start_time"] = str(start_time)
        if end_time:
            metadata["end_time"] = str(end_time)

        categories = filters.get("categories")
        if categories:
            metadata["category"] = ",".join(str(cat) for cat in categories)

        return metadata or None

    @staticmethod
    def _to_message(message: ChatMessage) -> Message:
        """Convert a MemoryManager ChatMessage into the shared Message schema.

        Args:
            message: ChatMessage returned from the memory service.

        Returns:
            Message: Structured message with normalized role and content.
        """
        role = (message.role or "user").lower()
        content = str(message.content) if message.content is not None else ""
        if role == "assistant":
            return Message.assistant(contents=content)
        if role == "system":
            return Message.system(contents=content)
        return Message.user(contents=content)

    @staticmethod
    def _chunk_to_hit(chunk: Chunk) -> dict[str, Any]:
        """Transform a Chunk record into the hit dict consumed by callers.

        Args:
            chunk: Chunk object returned by the retriever.

        Returns:
            dict[str, Any]: Serializable hit payload.
        """
        metadata = dict(chunk.metadata or {})
        content = chunk.content
        if isinstance(content, bytes):
            try:
                content = content.decode("utf-8")
            except Exception:  # noqa: BLE001
                content = content.decode("utf-8", "ignore")
        if content is None:
            content = ""

        hit = {
            "id": chunk.id,
            "memory": content,
            "score": chunk.score,
            "metadata": metadata,
            "created_at": metadata.get("created_at"),
            "updated_at": metadata.get("updated_at"),
            "user_id": metadata.get("user_id"),
            "agent_id": metadata.get("agent_id"),
        }
        return hit
