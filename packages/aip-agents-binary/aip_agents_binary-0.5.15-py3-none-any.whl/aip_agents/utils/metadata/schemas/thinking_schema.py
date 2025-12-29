"""Pydantic schemas for thinking metadata.

Authors:
    Fachriza Adhiatma (fachriza.d.adhiatma@gdplabs.id)
"""

from enum import StrEnum

from pydantic import BaseModel, Field


class ThinkingDataType(StrEnum):
    """Enum for thinking data types."""

    THINKING = "thinking"
    THINKING_START = "thinking_start"
    THINKING_END = "thinking_end"


class Thinking(BaseModel):
    """Schema for thinking info payload.

    Fields:
    - data_type: type of thinking event
    - id: UUID string identifying this thinking event
    - data_value: JSON string with additional info (e.g., {"message": "..."})
    """

    data_type: ThinkingDataType = Field(default=ThinkingDataType.THINKING)
    id: str
    data_value: str
