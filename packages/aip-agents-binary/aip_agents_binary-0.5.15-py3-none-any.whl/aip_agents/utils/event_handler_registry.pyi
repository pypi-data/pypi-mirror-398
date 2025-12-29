from _typeshed import Incomplete
from aip_agents.schema.a2a import A2AStreamEventType as A2AStreamEventType
from aip_agents.utils.logger import get_logger as get_logger
from typing import Any

logger: Incomplete

class EventHandlerRegistry:
    """Registry for tracking known streaming events with pass-through behaviour."""
    def __init__(self) -> None:
        """Initialize the event handler registry with known event types."""
    def handle(self, event_type: A2AStreamEventType | str | None, payload: dict[str, Any]) -> dict[str, Any]:
        """Return the payload unchanged while logging unknown events.

        Args:
            event_type (A2AStreamEventType | str | None): The type of the streaming event.
            payload (dict[str, Any]): The event payload data.

        Returns:
            dict[str, Any]: The payload unchanged (pass-through).
        """

DEFAULT_EVENT_HANDLER_REGISTRY: Incomplete
