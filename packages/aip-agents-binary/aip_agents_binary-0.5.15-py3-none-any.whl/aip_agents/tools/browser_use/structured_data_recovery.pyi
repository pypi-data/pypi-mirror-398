from _typeshed import Incomplete
from aip_agents.utils.logger import get_logger as get_logger
from typing import Any

logger: Incomplete

def recover_concatenated_json_objects(json_blob: str) -> dict[str, Any] | None:
    """Normalize concatenated JSON object strings into a structured payload.

    Args:
        json_blob: Raw JSON-like string returned by the structured data extractor.

    Returns:
        dict[str, Any] | None: Standardized payload when multiple objects are recovered,
        otherwise None.
    """
def repair_json_blob(json_blob: str) -> str | None:
    """Apply json_repair to malformed JSON strings and return the mutated payload.

    Args:
        json_blob: Raw JSON string that may contain syntax mistakes.

    Returns:
        str | None: Repaired JSON string when modifications were applied, otherwise None.
    """

class _JsonObjectSplitter:
    """Helper class to split JSON objects with reduced cognitive complexity."""
    json_blob: Incomplete
    segments: list[str]
    depth: int
    start: int | None
    last_end: int
    in_string: bool
    escaping: bool
    def __init__(self, json_blob: str) -> None:
        """Initialize the splitter with the raw JSON string.

        Args:
            json_blob: Raw string potentially containing concatenated JSON objects.
        """
    def split_objects(self) -> list[str]:
        """Main method to split JSON objects."""
