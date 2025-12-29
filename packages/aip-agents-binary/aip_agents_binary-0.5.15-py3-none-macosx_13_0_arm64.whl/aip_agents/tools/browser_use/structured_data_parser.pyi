from aip_agents.tools.browser_use.types import ToolCallInfo
from collections.abc import Callable, Sequence
from typing import Any

__all__ = ['attempt_json_recovery', 'detect_structured_data_failure', 'extract_content_after_marker', 'extract_json_blob', 'parse_structured_data', 'payload_reports_empty', 'payload_reports_error', 'structured_data_failure_for_call']

def detect_structured_data_failure(tool_calls: Sequence[ToolCallInfo], summarize_error: Callable[[str], str]) -> str | None:
    """Return a descriptive error when structured data extraction yields no results.

    Args:
        tool_calls: Tool call descriptors extracted from the latest agent step.
        summarize_error: Function to summarize error messages.

    Returns:
        str | None: Failure reason when extraction yielded nothing, otherwise None.
    """
def structured_data_failure_for_call(call: ToolCallInfo, summarize_error: Callable[[str], str]) -> str | None:
    """Evaluate a single tool call for extractor failures.

    Args:
        call: Tool call descriptor encapsulating name/args/output.
        summarize_error: Function to summarize error messages.

    Returns:
        str | None: Failure message when the call represents a bad extraction.
    """
def payload_reports_error(payload: dict[str, Any], raw_output: str, summarize_error: Callable[[str], str]) -> str | None:
    """Return a formatted error message when extractor status indicates failure.

    Args:
        payload: Parsed JSON payload emitted by the extractor.
        raw_output: Original extractor output (used for fallback summaries).
        summarize_error: Function to summarize error messages.

    Returns:
        str | None: Human-readable failure string when extraction failed.
    """
def payload_reports_empty(payload: dict[str, Any], raw_output: str, summarize_error: Callable[[str], str]) -> str | None:
    """Return a formatted message when the extractor returned no usable data.

    Args:
        payload: Parsed JSON payload emitted by the extractor.
        raw_output: Original extractor output string.
        summarize_error: Function to summarize error messages.

    Returns:
        str | None: Human-readable failure message when no content was extracted.
    """
def parse_structured_data(output: str, summarize_error: Callable[[str], str]) -> tuple[dict[str, Any] | list[Any] | None, str | None]:
    """Extract the JSON blob emitted by extract_structured_data if present.

    Args:
        output: Raw string payload returned by extract_structured_data.
        summarize_error: Function to summarize error messages.

    Returns:
        tuple[dict[str, Any] | list[Any] | None, str | None]: Parsed JSON payload when extraction succeeds,
            otherwise a tuple containing None and a diagnostic string on failure.
    """
def extract_content_after_marker(output: str) -> str | None:
    """Extract content after the 'Extracted Content:' marker and clean trailing metadata.

    Args:
        output: Raw string payload returned by extract_structured_data.

    Returns:
        str | None: Cleaned content after the marker, or None if marker not found.
    """
def extract_json_blob(content: str) -> str | None:
    """Extract the JSON blob from content by finding delimiters and trimming trailing content.

    Args:
        content: Content string potentially containing JSON.

    Returns:
        str | None: Extracted JSON blob, or None if no valid JSON delimiters found.
    """
def attempt_json_recovery(json_blob: str) -> dict[str, Any] | list[Any] | None:
    """Attempt to parse JSON blob, with recovery strategies for common issues.

    Args:
        json_blob: JSON string to attempt parsing.

    Returns:
        dict[str, Any] | list[Any] | None: Parsed JSON data if successful, None if all recovery attempts fail.
    """
