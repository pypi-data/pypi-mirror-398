"""High-level helpers for parsing and validating structured data extractor output.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from typing import Any

from aip_agents.tools.browser_use.structured_data_recovery import (
    recover_concatenated_json_objects,
    repair_json_blob,
)
from aip_agents.tools.browser_use.types import ToolCallInfo
from aip_agents.utils.logger import get_logger

logger = get_logger(__name__)


def detect_structured_data_failure(
    tool_calls: Sequence[ToolCallInfo],
    summarize_error: Callable[[str], str],
) -> str | None:
    """Return a descriptive error when structured data extraction yields no results.

    Args:
        tool_calls: Tool call descriptors extracted from the latest agent step.
        summarize_error: Function to summarize error messages.

    Returns:
        str | None: Failure reason when extraction yielded nothing, otherwise None.
    """
    for call in tool_calls:
        failure = structured_data_failure_for_call(call, summarize_error)
        if failure:
            return failure
    return None


def structured_data_failure_for_call(
    call: ToolCallInfo,
    summarize_error: Callable[[str], str],
) -> str | None:
    """Evaluate a single tool call for extractor failures.

    Args:
        call: Tool call descriptor encapsulating name/args/output.
        summarize_error: Function to summarize error messages.

    Returns:
        str | None: Failure message when the call represents a bad extraction.
    """
    if call.name != "extract_structured_data":
        return None

    payload, parse_error = parse_structured_data(call.output or "", summarize_error)
    if parse_error:
        summary = summarize_error(parse_error)
        return f"Structured data extraction emitted invalid JSON. Decoder reported: {summary}"
    if payload is None:
        return None

    raw_output = call.output or ""
    if isinstance(payload, dict):
        error_message = payload_reports_error(payload, raw_output, summarize_error)
        if error_message:
            return error_message

        empty_message = payload_reports_empty(payload, raw_output, summarize_error)
        if empty_message:
            return empty_message

    return None


def payload_reports_error(
    payload: dict[str, Any],
    raw_output: str,
    summarize_error: Callable[[str], str],
) -> str | None:
    """Return a formatted error message when extractor status indicates failure.

    Args:
        payload: Parsed JSON payload emitted by the extractor.
        raw_output: Original extractor output (used for fallback summaries).
        summarize_error: Function to summarize error messages.

    Returns:
        str | None: Human-readable failure string when extraction failed.
    """
    status = payload.get("status")
    if isinstance(status, str) and status.lower() == "error":
        message = payload.get("message") or payload.get("error") or raw_output
        summary = summarize_error(message)
        return f"Structured data extraction failed: {summary}"
    return None


def payload_reports_empty(
    payload: dict[str, Any],
    raw_output: str,
    summarize_error: Callable[[str], str],
) -> str | None:
    """Return a formatted message when the extractor returned no usable data.

    Args:
        payload: Parsed JSON payload emitted by the extractor.
        raw_output: Original extractor output string.
        summarize_error: Function to summarize error messages.

    Returns:
        str | None: Human-readable failure message when no content was extracted.
    """
    products = payload.get("products")
    count = payload.get("count")
    available = payload.get("available")
    products_found = payload.get("products_found")

    no_products = isinstance(products, list) and len(products) == 0
    explicit_zero = count == 0 or products_found == 0
    explicitly_unavailable = available is False

    if no_products or explicit_zero or explicitly_unavailable:
        summary = summarize_error(raw_output)
        return f"Structured data extraction returned no usable entries. Extractor response: {summary}"
    return None


def parse_structured_data(
    output: str,
    summarize_error: Callable[[str], str],
) -> tuple[dict[str, Any] | list[Any] | None, str | None]:
    """Extract the JSON blob emitted by extract_structured_data if present.

    Args:
        output: Raw string payload returned by extract_structured_data.
        summarize_error: Function to summarize error messages.

    Returns:
        tuple[dict[str, Any] | list[Any] | None, str | None]: Parsed JSON payload when extraction succeeds,
            otherwise a tuple containing None and a diagnostic string on failure.
    """
    content = extract_content_after_marker(output)
    if not content:
        return None, None

    json_blob = extract_json_blob(content)
    if not json_blob:
        return None, None

    parsed_data = attempt_json_recovery(json_blob)
    if parsed_data is not None:
        return parsed_data, None

    snippet = summarize_error(json_blob)
    error_msg = "JSON parsing failed after all recovery attempts"
    logger.warning(
        "Structured data extractor emitted malformed JSON: %s. snippet=%s",
        error_msg,
        snippet,
    )
    return None, f"{error_msg}: {snippet}"


def extract_content_after_marker(output: str) -> str | None:
    """Extract content after the 'Extracted Content:' marker and clean trailing metadata.

    Args:
        output: Raw string payload returned by extract_structured_data.

    Returns:
        str | None: Cleaned content after the marker, or None if marker not found.
    """
    if "Extracted Content:" not in output:
        return None

    _, remainder = output.split("Extracted Content:", 1)

    for marker in ("</extracted_content>", "<file_system>", "</file_system>"):
        marker_index = remainder.find(marker)
        if marker_index != -1:
            remainder = remainder[:marker_index]
            break

    remainder = remainder.strip()
    return remainder if remainder else None


def extract_json_blob(content: str) -> str | None:
    """Extract the JSON blob from content by finding delimiters and trimming trailing content.

    Args:
        content: Content string potentially containing JSON.

    Returns:
        str | None: Extracted JSON blob, or None if no valid JSON delimiters found.
    """
    first_bracket = content.find("[")
    first_brace = content.find("{")
    candidates = [index for index in (first_bracket, first_brace) if index != -1]
    if not candidates:
        return None

    start = min(candidates)
    json_blob = content[start:]

    closing_char = "]" if json_blob.startswith("[") else "}"
    end = json_blob.rfind(closing_char)
    if end == -1:
        return None
    return json_blob[: end + 1].strip()


def attempt_json_recovery(json_blob: str) -> dict[str, Any] | list[Any] | None:
    """Attempt to parse JSON blob, with recovery strategies for common issues.

    Args:
        json_blob: JSON string to attempt parsing.

    Returns:
        dict[str, Any] | list[Any] | None: Parsed JSON data if successful, None if all recovery attempts fail.
    """
    try:
        return json.loads(json_blob)
    except json.JSONDecodeError as error:
        recovered_payload = recover_concatenated_json_objects(json_blob)
        if recovered_payload is not None:
            return recovered_payload

        repaired = repair_json_blob(json_blob)
        if repaired:
            try:
                payload = json.loads(repaired)
            except json.JSONDecodeError:
                logger.debug("json_repair returned unrecoverable payload for structured data output.")
            else:
                logger.info(
                    "Structured data extractor output repaired via json_repair and parsed successfully. original_error=%s",
                    error.msg,
                )
                return payload
    return None


__all__ = [
    "attempt_json_recovery",
    "detect_structured_data_failure",
    "extract_content_after_marker",
    "extract_json_blob",
    "parse_structured_data",
    "payload_reports_empty",
    "payload_reports_error",
    "structured_data_failure_for_call",
]
