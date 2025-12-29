from enum import StrEnum
from uuid import UUID

__all__ = ['DefaultTimezone', 'DEFAULT_PII_TAG_NAMESPACE']

class DefaultTimezone(StrEnum):
    """Default timezone constants used across the application."""
    JAKARTA: str

DEFAULT_PII_TAG_NAMESPACE: UUID
