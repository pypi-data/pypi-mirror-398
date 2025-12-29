"""Types and enums for Langflow client module.

This module contains type definitions, enums, and data structures
specific to Langflow API communication and event handling.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

from enum import StrEnum


class LangflowEventType(StrEnum):
    """Enum for Langflow event types as received from the API."""

    ADD_MESSAGE = "add_message"
    END = "end"
    UNKNOWN = "unknown"
