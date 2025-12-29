from _typeshed import Incomplete
from collections.abc import Callable

__all__ = ['ArgsFormatter', 'OutputFormatter', 'SensitiveInfoFilter']

JSONScalar = str | int | float | bool | None

class SensitiveInfoFilter:
    """Redact sensitive argument/output values before rendering or sending to LLMs."""
    REDACTED: str
    SENSITIVE_KEY_PATTERNS: Incomplete
    def __init__(self) -> None:
        """Initialize the sensitive info filter."""
    def sanitize(self, args: dict[str, JSONValue] | None, output: JSONValue | None, tool_sanitizer: Callable[[dict[str, JSONValue] | None, JSONValue | None], dict[str, JSONValue]] | None = None) -> tuple[dict[str, JSONValue] | None, JSONValue | None]:
        """Return sanitized arguments/output with optional tool overrides.

        Args:
            args: Raw arguments dictionary emitted by the tool.
            output: Raw tool output which may be nested JSON.
            tool_sanitizer: Optional callable that can override sanitized values.

        Returns:
            tuple: Sanitized args and output payloads.
        """

class ArgsFormatter:
    """Simple formatter that surfaces at most two argument key/value pairs."""
    def format(self, args: dict[str, JSONValue] | None) -> str | None:
        """Format tool arguments into a short excerpt.

        Args:
            args: Tool arguments dictionary.

        Returns:
            str | None: Concise representation of up to two key/value pairs.
        """

class OutputFormatter:
    """Lightweight formatter that truncates serialized output."""
    def format(self, output: JSONValue | None) -> str | None:
        """Format tool output into a readable excerpt.

        Args:
            output: Raw tool output.

        Returns:
            str | None: Truncated representation suitable for logs.
        """
