from collections.abc import Iterable
from dataclasses import dataclass

__all__ = ['SessionErrorCategory', 'categorize_fatal_message', 'categorize_warning_message', 'find_fatal_message', 'is_recoverable_message']

@dataclass(frozen=True)
class SessionErrorCategory:
    """Represents a fatal Steel/browser disconnect classification."""
    name: str
    markers: tuple[str, ...]
    fatal: bool
    retryable: bool

def categorize_fatal_message(message: str) -> SessionErrorCategory | None:
    """Return the fatal session category associated with the given message, if any.

    Args:
        message: The error message to categorize.

    Returns:
        The SessionErrorCategory if the message matches a fatal error pattern,
        None otherwise.
    """
def categorize_warning_message(message: str) -> str | None:
    """Return the name of a known non-fatal warning when present in the message.

    Args:
        message: The error message to check for warning patterns.

    Returns:
        The warning name if the message matches a known warning pattern,
        None otherwise.
    """
def find_fatal_message(messages: Iterable[str]) -> tuple[str, SessionErrorCategory] | None:
    """Return the first fatal message detected in the iterable.

    Args:
        messages: An iterable of error messages to search through.

    Returns:
        A tuple of (message, category) for the first fatal message found,
        None if no fatal messages are detected.
    """
def is_recoverable_message(message: str) -> bool:
    """Return True when the message maps to a retryable session disconnect.

    Args:
        message: The error message to check for recoverability.

    Returns:
        True if the message corresponds to a retryable fatal error,
        False otherwise.
    """
