from enum import StrEnum

class LangflowEventType(StrEnum):
    """Enum for Langflow event types as received from the API."""
    ADD_MESSAGE: str
    END: str
    UNKNOWN: str
