"""Formatting and sanitization helpers for activity narratives.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable

from aip_agents.utils.logger import get_logger
from aip_agents.utils.metadata.activity_narrative.constants import OUTPUT_EXCERPT_MAX_CHARS

logger = get_logger(__name__)

JSONScalar = str | int | float | bool | None
JSONValue = JSONScalar | dict[str, "JSONValue"] | list["JSONValue"]


class SensitiveInfoFilter:
    """Redact sensitive argument/output values before rendering or sending to LLMs."""

    REDACTED = "<redacted>"
    SENSITIVE_KEY_PATTERNS = (
        "token",
        "secret",
        "password",
        "api_key",
        "apikey",
        "credential",
        "auth",
    )

    def __init__(self) -> None:
        """Initialize the sensitive info filter."""
        self._logger = logger

    def sanitize(
        self,
        args: dict[str, JSONValue] | None,
        output: JSONValue | None,
        tool_sanitizer: Callable[[dict[str, JSONValue] | None, JSONValue | None], dict[str, JSONValue]] | None = None,
    ) -> tuple[dict[str, JSONValue] | None, JSONValue | None]:
        """Return sanitized arguments/output with optional tool overrides.

        Args:
            args: Raw arguments dictionary emitted by the tool.
            output: Raw tool output which may be nested JSON.
            tool_sanitizer: Optional callable that can override sanitized values.

        Returns:
            tuple: Sanitized args and output payloads.
        """
        sanitized_args = self._sanitize_structure(args)
        sanitized_output = self._sanitize_structure(output)

        if callable(tool_sanitizer):
            try:
                replacement = tool_sanitizer(args, output) or {}
                if isinstance(replacement, dict):
                    if "args" in replacement:
                        sanitized_args = replacement.get("args")
                    if "output" in replacement:
                        sanitized_output = replacement.get("output")
            except Exception as exc:  # pragma: no cover - defensive
                self._logger.warning("activity sanitizer hook failed: %s", exc)

        return sanitized_args, sanitized_output

    def _sanitize_structure(self, value: JSONValue) -> JSONValue:
        """Recursively sanitize nested structures by redacting sensitive data.

        Args:
            value: Arbitrary nested JSON-esque payload.

        Returns:
            JSONValue: Sanitized structure with sensitive values redacted.
        """
        if value is None:
            return None
        if isinstance(value, dict):
            sanitized: dict[str, JSONValue] = {}
            for key, val in value.items():
                sanitized[key] = self.REDACTED if self._is_sensitive_key(key) else self._sanitize_structure(val)
            return sanitized
        if isinstance(value, list):
            return [self._sanitize_structure(item) for item in value]
        if isinstance(value, str):
            return self._sanitize_string(value)
        return value

    def _sanitize_string(self, value: str) -> str:
        """Sanitize a string value by checking if it looks like a secret.

        Args:
            value: Raw string to inspect.

        Returns:
            str: Either the original trimmed string or ``<redacted>``.
        """
        stripped = value.strip()
        if self._looks_like_secret(stripped):
            return self.REDACTED
        return stripped

    def _is_sensitive_key(self, key: str) -> bool:
        """Check if a key name indicates sensitive data.

        Args:
            key: Key name from the argument/output structure.

        Returns:
            bool: True when the key hints at credentials or tokens.
        """
        lowered = key.lower()
        return any(pattern in lowered for pattern in self.SENSITIVE_KEY_PATTERNS)

    def _looks_like_secret(self, value: str) -> bool:
        """Check if a string value looks like a secret or API key.

        Args:
            value: Text candidate to evaluate.

        Returns:
            bool: True when the string matches secret heuristics.
        """
        if not value:
            return False
        if value.startswith("sk-") or value.startswith("rk-"):
            return True
        if len(value) >= 64 and re.fullmatch(r"[A-Za-z0-9+/=_-]+", value):
            return True
        return False


class ArgsFormatter:
    """Simple formatter that surfaces at most two argument key/value pairs."""

    def format(self, args: dict[str, JSONValue] | None) -> str | None:
        """Format tool arguments into a short excerpt.

        Args:
            args: Tool arguments dictionary.

        Returns:
            str | None: Concise representation of up to two key/value pairs.
        """
        if not args:
            return None
        parts: list[str] = []
        for key in sorted(args.keys()):
            if len(parts) >= 2:
                break
            value = self._stringify(args[key])
            if value:
                parts.append(f"{key}: {value}")
        return "; ".join(parts) if parts else None

    def _stringify(self, value: JSONValue) -> str | None:
        """Convert a value to a string representation.

        Args:
            value: Value lifted from the arguments dictionary.

        Returns:
            str | None: Stringified value truncated when overly long.
        """
        if value is None:
            return None
        if isinstance(value, str):
            value = value.strip()
            return value or None
        try:
            text = json.dumps(value, ensure_ascii=False)
        except Exception:
            text = str(value)
        text = text.strip()
        if not text:
            return None
        if len(text) > 200:
            return text[:199].rstrip() + "…"
        return text


class OutputFormatter:
    """Lightweight formatter that truncates serialized output."""

    def format(self, output: JSONValue | None) -> str | None:
        """Format tool output into a readable excerpt.

        Args:
            output: Raw tool output.

        Returns:
            str | None: Truncated representation suitable for logs.
        """
        if output is None:
            return None
        if isinstance(output, str):
            text = output.strip()
            if not text:
                return None
            return self._truncate(text)
        try:
            text = json.dumps(output, ensure_ascii=False)
        except Exception:
            text = str(output)
        text = text.strip()
        if not text:
            return None
        return self._truncate(text)

    def _truncate(self, text: str, limit: int = OUTPUT_EXCERPT_MAX_CHARS) -> str:
        """Truncate text to a maximum length with ellipsis.

        Args:
            text: Text value to truncate.
            limit: Maximum permitted character count.

        Returns:
            str: Text clipped to the configured limit.
        """
        if len(text) <= limit:
            return text
        return text[: limit - 1].rstrip() + "…"


__all__ = ["ArgsFormatter", "OutputFormatter", "SensitiveInfoFilter"]
