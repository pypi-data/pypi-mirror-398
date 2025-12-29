"""Utilities for recovering malformed structured-data payloads emitted by browser-use.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

import json
from typing import Any

from json_repair import repair_json

from aip_agents.utils.logger import get_logger

logger = get_logger(__name__)


def recover_concatenated_json_objects(json_blob: str) -> dict[str, Any] | None:
    """Normalize concatenated JSON object strings into a structured payload.

    Args:
        json_blob: Raw JSON-like string returned by the structured data extractor.

    Returns:
        dict[str, Any] | None: Standardized payload when multiple objects are recovered,
        otherwise None.
    """
    segments = _split_top_level_json_objects(json_blob)
    if len(segments) <= 1:
        return None

    try:
        records = [json.loads(segment) for segment in segments]
    except json.JSONDecodeError:
        return None

    count = len(records)
    logger.info("Structured data extractor returned concatenated JSON objects. recovered=%s", count)
    return {
        "status": "ok",
        "items": records,
        "products": records,
        "count": count,
        "products_found": count,
        "available": bool(records),
    }


def repair_json_blob(json_blob: str) -> str | None:
    """Apply json_repair to malformed JSON strings and return the mutated payload.

    Args:
        json_blob: Raw JSON string that may contain syntax mistakes.

    Returns:
        str | None: Repaired JSON string when modifications were applied, otherwise None.
    """
    try:
        repaired = repair_json(json_blob)
    except Exception:
        logger.debug("json_repair failed to repair structured data output.", exc_info=True)
        return None

    if not repaired or repaired == json_blob:
        return None

    return repaired


def _split_top_level_json_objects(json_blob: str) -> list[str]:
    """Split concatenated JSON objects while respecting string literals.

    Args:
        json_blob: The JSON string containing concatenated objects to split.
    """
    splitter = _JsonObjectSplitter(json_blob)
    return splitter.split_objects()


def _has_only_separators(value: str) -> bool:
    """Return True when the substring only contains whitespace or commas.

    Args:
        value: The string to check for separators only.
    """
    return value.strip(" \t\r\n,") == ""


class _JsonObjectSplitter:
    """Helper class to split JSON objects with reduced cognitive complexity."""

    def __init__(self, json_blob: str) -> None:
        """Initialize the splitter with the raw JSON string.

        Args:
            json_blob: Raw string potentially containing concatenated JSON objects.
        """
        self.json_blob = json_blob
        self.segments: list[str] = []
        self.depth = 0
        self.start: int | None = None
        self.last_end = 0
        self.in_string = False
        self.escaping = False

    def split_objects(self) -> list[str]:
        """Main method to split JSON objects."""
        if not self._parse_characters():
            return []

        if not self._validate_final_state():
            return []

        return self.segments

    def _parse_characters(self) -> bool:
        """Parse each character and build segments. Returns False if invalid."""
        for index, char in enumerate(self.json_blob):
            if not self._process_character(char, index):
                return False
        return True

    def _process_character(self, char: str, index: int) -> bool:
        """Process a single character. Returns False if parsing should stop.

        Args:
            char: The character to process.
            index: The position of the character in the JSON blob.

        Returns:
            True if processing should continue, False if parsing should stop.
        """
        if self.escaping:
            self.escaping = False
            return True

        if char == "\\":
            self.escaping = True
            return True

        if char == '"':
            self.in_string = not self.in_string
            return True

        if self.in_string:
            return True

        return self._process_non_string_char(char, index)

    def _process_non_string_char(self, char: str, index: int) -> bool:
        """Process characters outside of strings.

        Args:
            char: The character to process (not in a string).
            index: The position of the character in the JSON blob.

        Returns:
            True if processing should continue, False if invalid structure found.
        """
        if char == "{":
            return self._handle_open_brace(index)
        if char == "}":
            return self._handle_close_brace(index)
        return True

    def _handle_open_brace(self, index: int) -> bool:
        """Handle opening brace character.

        Args:
            index: The position of the opening brace in the JSON blob.

        Returns:
            True if brace should be processed, False if invalid separators found.
        """
        if self.depth == 0:
            if not _has_only_separators(self.json_blob[self.last_end : index]):
                return False
            self.start = index
        self.depth += 1
        return True

    def _handle_close_brace(self, index: int) -> bool:
        """Handle closing brace character.

        Args:
            index: The position of the closing brace in the JSON blob.

        Returns:
            Always True as closing braces don't cause parsing failures.
        """
        self.depth -= 1
        if self.depth == 0 and self.start is not None:
            end = index + 1
            self.segments.append(self.json_blob[self.start : end])
            self.last_end = end
        return True

    def _validate_final_state(self) -> bool:
        """Validate that parsing completed successfully."""
        if self.depth != 0 or self.in_string:
            return False

        return _has_only_separators(self.json_blob[self.last_end :])
