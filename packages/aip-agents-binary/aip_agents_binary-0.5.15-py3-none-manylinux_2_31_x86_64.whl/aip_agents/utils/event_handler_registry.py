"""Shared event handler registry for streaming payload processing."""

from __future__ import annotations

from typing import Any

from aip_agents.schema.a2a import A2AStreamEventType
from aip_agents.utils.logger import get_logger

logger = get_logger(__name__)


class EventHandlerRegistry:
    """Registry for tracking known streaming events with pass-through behaviour."""

    def __init__(self) -> None:
        """Initialize the event handler registry with known event types."""
        self._known_events: set[str] = {self._normalize_event_type(event) for event in A2AStreamEventType}

    def handle(self, event_type: A2AStreamEventType | str | None, payload: dict[str, Any]) -> dict[str, Any]:
        """Return the payload unchanged while logging unknown events.

        Args:
            event_type (A2AStreamEventType | str | None): The type of the streaming event.
            payload (dict[str, Any]): The event payload data.

        Returns:
            dict[str, Any]: The payload unchanged (pass-through).
        """
        normalized = self._normalize_event_type(event_type)
        if normalized not in self._known_events:
            logger.info(
                "Unknown event type encountered in event handler registry; using default passthrough.",
                extra={
                    "event_type": normalized,
                    "metadata_keys": list((payload.get("metadata") or {}).keys()) if isinstance(payload, dict) else [],
                },
            )
        return payload

    @staticmethod
    def _normalize_event_type(event_type: A2AStreamEventType | str | None) -> str:
        """Return a lowercase string for the supplied event type or ``unknown``.

        Args:
            event_type: Enum instance, string literal, or None representing the event.

        Returns:
            str: Normalized event type identifier.
        """
        if isinstance(event_type, A2AStreamEventType):
            return event_type.value
        if isinstance(event_type, str) and event_type:
            return event_type
        return "unknown"


DEFAULT_EVENT_HANDLER_REGISTRY = EventHandlerRegistry()
