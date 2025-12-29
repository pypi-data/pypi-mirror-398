"""Pydantic schemas shared by memory search tools.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from typing import Any

from pydantic import BaseModel, Field


class MemoryConfig(BaseModel):
    """Tool configuration schema for memory operations."""

    user_id: str = Field(description="User identifier for memory scoping")


class LongTermMemorySearchInput(BaseModel):
    """Input schema for unified long-term memory retrieval."""

    query: str | None = Field(
        None,
        description="Optional semantic query for searching memories. If provided, performs semantic search. "
        "If omitted, performs pure date-based recall using time filters.",
    )
    start_date: str | None = Field(
        None,
        description="Explicit start date in YYYY-MM-DD format. Used with end_date for precise date ranges. "
        "If omitted, recall is unbounded at the start.",
    )
    end_date: str | None = Field(
        None,
        description="Explicit end date in YYYY-MM-DD format. Used with start_date for precise date ranges. "
        "If omitted, recall is unbounded at the end.",
    )
    limit: int | None = Field(
        None,
        description="Maximum number of memories to retrieve. If not specified, uses default. "
        "Values below 5 are automatically increased to ensure adequate context.",
    )
    categories: list[str] | None = Field(
        None,
        description="Optional categories to filter by (uses 'in' operator).",
    )
    metadata: dict[str, Any] | None = Field(
        None,
        description="Optional metadata dict to filter by (exact key-value match).",
    )
