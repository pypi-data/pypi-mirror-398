from enum import StrEnum
from pydantic import BaseModel

class ThinkingDataType(StrEnum):
    """Enum for thinking data types."""
    THINKING: str
    THINKING_START: str
    THINKING_END: str

class Thinking(BaseModel):
    '''Schema for thinking info payload.

    Fields:
    - data_type: type of thinking event
    - id: UUID string identifying this thinking event
    - data_value: JSON string with additional info (e.g., {"message": "..."})
    '''
    data_type: ThinkingDataType
    id: str
    data_value: str
