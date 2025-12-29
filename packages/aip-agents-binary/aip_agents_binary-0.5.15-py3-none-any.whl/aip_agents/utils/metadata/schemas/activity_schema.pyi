from enum import StrEnum
from pydantic import BaseModel

class ActivityDataType(StrEnum):
    """Enumeration of activity data types."""
    ACTIVITY: str

class Activity(BaseModel):
    '''Schema for activity info payload.

    Fields:
    - data_type: always "activity"
    - id: UUID string identifying this activity event
    - data_value: JSON string with additional info (e.g., {"message": "..."})
    '''
    data_type: ActivityDataType
    id: str
    data_value: str
