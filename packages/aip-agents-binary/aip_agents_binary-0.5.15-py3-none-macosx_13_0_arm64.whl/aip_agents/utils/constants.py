"""Shared constants for AIP Agents.

This module defines commonly used constants across the agents library
to avoid duplication and maintain consistency.

Authors:
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

from enum import StrEnum
from uuid import UUID

__all__ = ["DefaultTimezone", "DEFAULT_PII_TAG_NAMESPACE"]


class DefaultTimezone(StrEnum):
    """Default timezone constants used across the application."""

    JAKARTA = "Asia/Jakarta"


DEFAULT_PII_TAG_NAMESPACE: UUID = UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")
