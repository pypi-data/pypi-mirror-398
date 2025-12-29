"""Mem0-specific implementation of the long-term memory search tool.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

import json
from typing import Any, ClassVar

from langchain_core.runnables import RunnableConfig

from aip_agents.memory.constants import MemoryDefaults
from aip_agents.tools.memory_search.base import LongTermMemorySearchTool
from aip_agents.tools.memory_search.schema import LongTermMemorySearchInput
from aip_agents.utils.datetime import is_valid_date_string, next_day_iso
from aip_agents.utils.logger import get_logger

logger = get_logger(__name__)

MEMORY_SEARCH_TOOL_NAME = "built_in_mem0_search"


class Mem0SearchTool(LongTermMemorySearchTool):
    """Mem0-specific implementation of the long-term memory search tool."""

    name: str = MEMORY_SEARCH_TOOL_NAME
    description: str = (
        "Search or retrieve memories from long-term mem0 storage. Supports two modes:\n"
        "1. SEMANTIC SEARCH: Provide 'query' to search for relevant memories by content\n"
        "2. DATE-BASED RECALL: Omit 'query' to get all memories from an explicit date period\n\n"
        "Time periods only support explicit dates ('start_date'/'end_date' in YYYY-MM-DD format).\n\n"
        "Use for: names, preferences, past plans, conversations, or when user asks "
        "'What did we discuss last week?' or 'Search for project notes'"
    )
    args_schema: type[LongTermMemorySearchInput] = LongTermMemorySearchInput
    LOG_PREFIX: ClassVar[str] = "Mem0SearchTool"
    METADATA_FILTER_BLOCKLIST: ClassVar[set[str]] = {"user_id", "memory_user_id"}

    async def _arun(
        self,
        query: str | None = None,
        config: RunnableConfig | None = None,
        run_manager: Any | None = None,
        **kwargs: Any,
    ) -> str:
        """Execute the memory search asynchronously for LangChain.

        Args:
            query: Semantic search query when provided.
            config: Runnable configuration containing LangChain metadata.
            run_manager: LangChain callbacks (unused).
            **kwargs: Additional filters such as ``start_date``, ``end_date``, ``limit``, ``categories``, ``metadata``.

        Returns:
            str: JSON-encoded retrieval results or an error message.
        """
        logger.info("%s: Received config: %s", self.LOG_PREFIX, config)

        start_date: str | None = kwargs.get("start_date")
        end_date: str | None = kwargs.get("end_date")
        limit: int | None = kwargs.get("limit")
        categories: list[str] | None = kwargs.get("categories")
        metadata: dict[str, Any] | None = kwargs.get("metadata")

        user_id = self._resolve_user_id(metadata=metadata, config=config)

        metadata_filter = None
        if isinstance(metadata, dict):
            metadata_filter = {k: v for k, v in metadata.items() if k not in self.METADATA_FILTER_BLOCKLIST} or None

        date_filter_result = self._parse_date_filters(
            start_date=start_date,
            end_date=end_date,
            user_id=user_id,
        )

        if "error" in date_filter_result:
            return f"Error: {date_filter_result['error']}"

        filters = self._add_additional_filters(
            filters=date_filter_result["filters"],
            categories=categories,
            metadata=metadata_filter,
            user_id=user_id,
        )

        time_spec = f"{start_date or 'unbounded'} to {end_date or 'unbounded'}"

        raw_results = self._perform_retrieval(
            query=query,
            user_id=user_id,
            limit=limit,
            filters=filters,
            time_spec=time_spec,
        )

        return json.dumps(raw_results)

    def _parse_date_filters(
        self,
        *,
        start_date: str | None,
        end_date: str | None,
        user_id: str,
    ) -> dict[str, Any]:
        """Build normalized date filters validated against YYYY-MM-DD strings.

        Args:
            start_date: Inclusive start date for recall filtering.
            end_date: Inclusive end date for recall filtering.
            user_id: User identifier to scope the memories.

        Returns:
            dict[str, Any]: Payload including ``filters`` or an ``error`` entry when validation fails.
        """
        filters: dict[str, Any] = {"AND": [{"user_id": user_id}]}
        if start_date or end_date:
            try:
                date_range_filter = self._build_explicit_date_filter(start_date, end_date)
                if date_range_filter:
                    filters["AND"].append(date_range_filter)
                    logger.info(
                        "%s: Using explicit date range [%s, %s] for user_id='%s'",
                        self.LOG_PREFIX,
                        start_date or "unbounded",
                        end_date or "unbounded",
                        user_id,
                    )
            except ValueError as exc:
                logger.warning("%s: Invalid explicit date range: %s", self.LOG_PREFIX, exc)
                return {"error": str(exc), "hits": [], "count": 0}

        return {"filters": filters}

    def _build_explicit_date_filter(self, start_date: str | None, end_date: str | None) -> dict[str, Any] | None:
        """Return the mem0-compatible date clause for explicit ranges.

        Args:
            start_date: Inclusive start date string.
            end_date: Inclusive end date string.

        Returns:
            dict[str, Any] | None: Date filter clause or None when no bounds were provided.

        Raises:
            ValueError: If either date fails the YYYY-MM-DD validation.
        """
        if not start_date and not end_date:
            return None

        date_filter: dict[str, Any] = {}

        if start_date:
            if not is_valid_date_string(start_date, "%Y-%m-%d"):
                raise ValueError(f"Invalid start_date format '{start_date}'. Expected YYYY-MM-DD.")
            date_filter["gte"] = start_date

        if end_date:
            if not is_valid_date_string(end_date, "%Y-%m-%d"):
                raise ValueError(f"Invalid end_date format '{end_date}'. Expected YYYY-MM-DD.")
            date_filter["lt"] = next_day_iso(end_date)

        return {"created_at": date_filter}

    def _add_additional_filters(
        self,
        *,
        filters: dict[str, Any],
        categories: list[str] | None,
        metadata: dict[str, Any] | None,
        user_id: str,
    ) -> dict[str, Any]:
        """Augment filters with categories and metadata selections.

        Args:
            filters: Existing filter payload (mutated in place).
            categories: Optional category list attached to the request.
            metadata: Additional metadata equality filters.
            user_id: User identifier for logging context.

        Returns:
            dict[str, Any]: Updated filters object.
        """
        if categories:
            filters["AND"].append({"categories": {"in": categories}})
            logger.info("%s: Added categories filter %s for user_id='%s'", self.LOG_PREFIX, categories, user_id)

        if metadata:
            filters["AND"].append({"metadata": metadata})
            logger.info("%s: Added metadata filter %s for user_id='%s'", self.LOG_PREFIX, metadata, user_id)

        return filters

    def _perform_retrieval(
        self,
        *,
        query: str | None,
        user_id: str,
        limit: int | None,
        filters: dict[str, Any],
        time_spec: str,
    ) -> list[dict[str, Any]]:
        """Execute the underlying memory retrieval call with guardrails.

        Args:
            query: Semantic query string or None for chronological listing.
            user_id: Identifier associated with the stored memories.
            limit: Requested number of memories to fetch.
            filters: Filter payload produced by ``_add_additional_filters``.
            time_spec: Human-readable time range string used for logging.

        Returns:
            list[dict[str, Any]]: Retrieved memories or empty list on failure.
        """
        effective_limit = max(limit or MemoryDefaults.RETRIEVAL_LIMIT, self.MINIMUM_MEMORY_RETRIEVAL)
        if limit is not None and effective_limit != limit:
            logger.info(
                "%s: Enforced minimum limit of %s (requested: %s, using: %s)",
                self.LOG_PREFIX,
                self.MINIMUM_MEMORY_RETRIEVAL,
                limit,
                effective_limit,
            )

        try:
            results = self.memory.retrieve(
                query=query,
                user_id=user_id,
                limit=effective_limit,
                filters=filters,
            )

            retrieval_mode = "semantic search" if query else "date-based recall"

            logger.info(
                "%s: %s complete for user_id='%s', query='%s', time_spec='%s', "
                "limit=%s (effective: %s), filters=%s, results_count=%s",
                self.LOG_PREFIX,
                retrieval_mode.title(),
                user_id,
                query or "None",
                time_spec,
                limit,
                effective_limit,
                filters,
                len(results),
            )

            return results

        except Exception as exc:  # noqa: BLE001
            logger.error("%s: Retrieval failed for user_id='%s': %s", self.LOG_PREFIX, user_id, exc)
            return []


Mem0SearchInput = LongTermMemorySearchInput
