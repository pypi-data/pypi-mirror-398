"""Centralized Steel/browser session error policies used by BrowserUseTool.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class SessionErrorCategory:
    """Represents a fatal Steel/browser disconnect classification."""

    name: str
    markers: tuple[str, ...]
    fatal: bool
    retryable: bool


_FATAL_SESSION_ERROR_CATEGORIES: tuple[SessionErrorCategory, ...] = (
    SessionErrorCategory(
        name="browser_closed",
        markers=(
            "browser has been closed",
            "target page, context or browser has been closed",
        ),
        fatal=True,
        retryable=True,
    ),
    SessionErrorCategory(
        name="websocket_disconnect",
        markers=(
            "code=1006",
            "websocket was closed before the connection was established",
            "websocket error",
        ),
        fatal=True,
        retryable=True,
    ),
)

_WARNING_MARKERS: dict[str, str] = {
    "502 bad gateway": "page_load_warning",
    "page link: about:blank": "blank_page_warning",
    "no webpage content": "blank_page_warning",
    "scroll_into_view_if_needed": "element_interaction_warning",
}

_FATAL_LOOKUP: dict[str, SessionErrorCategory] = {
    marker.lower(): category for category in _FATAL_SESSION_ERROR_CATEGORIES for marker in category.markers
}


def categorize_fatal_message(message: str) -> SessionErrorCategory | None:
    """Return the fatal session category associated with the given message, if any.

    Args:
        message: The error message to categorize.

    Returns:
        The SessionErrorCategory if the message matches a fatal error pattern,
        None otherwise.
    """
    if not message:
        return None

    lowered = message.lower()
    for marker, category in _FATAL_LOOKUP.items():
        if marker in lowered:
            return category
    return None


def categorize_warning_message(message: str) -> str | None:
    """Return the name of a known non-fatal warning when present in the message.

    Args:
        message: The error message to check for warning patterns.

    Returns:
        The warning name if the message matches a known warning pattern,
        None otherwise.
    """
    if not message:
        return None

    lowered = message.lower()
    for marker, warning_name in _WARNING_MARKERS.items():
        if marker in lowered:
            return warning_name
    return None


def find_fatal_message(messages: Iterable[str]) -> tuple[str, SessionErrorCategory] | None:
    """Return the first fatal message detected in the iterable.

    Args:
        messages: An iterable of error messages to search through.

    Returns:
        A tuple of (message, category) for the first fatal message found,
        None if no fatal messages are detected.
    """
    for message in messages:
        category = categorize_fatal_message(message)
        if category:
            return message, category
    return None


def is_recoverable_message(message: str) -> bool:
    """Return True when the message maps to a retryable session disconnect.

    Args:
        message: The error message to check for recoverability.

    Returns:
        True if the message corresponds to a retryable fatal error,
        False otherwise.
    """
    category = categorize_fatal_message(message)
    return bool(category and category.retryable)


__all__ = [
    "SessionErrorCategory",
    "categorize_fatal_message",
    "categorize_warning_message",
    "find_fatal_message",
    "is_recoverable_message",
]
