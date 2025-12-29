"""Pydantic schemas for activity metadata.

Authors:
    Fachriza Adhiatma (fachriza.d.adhiatma@gdplabs.id)
"""

from enum import StrEnum

from pydantic import BaseModel, Field


class ActivityDataType(StrEnum):
    """Enumeration of activity data types."""

    ACTIVITY = "activity"


class Activity(BaseModel):
    """Schema for activity info payload.

    Fields:
    - data_type: always "activity"
    - id: UUID string identifying this activity event
    - data_value: JSON string with additional info (e.g., {"message": "..."})
    """

    data_type: ActivityDataType = Field(default=ActivityDataType.ACTIVITY)
    id: str
    data_value: str
