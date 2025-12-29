"""Timestamp normalization helpers.

Authors:
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Final

from aip_agents.utils.logger import get_logger

__all__ = [
    "normalize_timestamp_to_date",
    "format_created_updated_label",
    "is_valid_date_string",
    "next_day_iso",
]


logger: Final = get_logger(__name__)

DEFAULT_DATE_FORMAT: Final[str] = "%Y-%m-%d"
DATETIME_FORMAT: Final[str] = "%Y-%m-%d %H:%M:%S"
ISO_FORMATS: Final[list[str | None]] = [
    None,  # ISO format
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%S.%f",
    "%Y-%m-%dT%H:%M:%S.%f%z",
]


def normalize_timestamp_to_date(value: Any) -> str | None:
    """Normalize various timestamp representations into a YYYY-MM-DD string.

    This function handles multiple input types and formats, converting them to
    a standardized ISO date string. It gracefully handles invalid inputs by
    returning None or the string representation.

    Args:
        value: The timestamp value to normalize. Can be:
            - None or empty string: Returns None
            - int/float: Unix timestamp (seconds since epoch)
            - str: ISO format, datetime string, or other string representation
            - Other types: Converted to string representation

    Returns:
        str | None: A YYYY-MM-DD formatted date string, or None if the input
            cannot be parsed as a valid date.

    Raises:
        ValueError: If the timestamp value is invalid (e.g., negative timestamp).

    Examples:
        >>> normalize_timestamp_to_date(1640995200)  # Unix timestamp
        '2022-01-01'
        >>> normalize_timestamp_to_date("2022-01-01T12:00:00")
        '2022-01-01'
        >>> normalize_timestamp_to_date("invalid")
        'invalid'
        >>> normalize_timestamp_to_date(None)
        None
    """
    # Handle None and empty values
    if value in (None, ""):
        return None

    if isinstance(value, int | float):
        return _normalize_numeric_timestamp(value)
    elif isinstance(value, str):
        return _normalize_string_timestamp(value)
    else:
        # For any other type, convert to string
        return str(value)


def _normalize_numeric_timestamp(value: int | float) -> str | None:
    """Normalize numeric timestamp to ISO date string.

    Args:
        value: Numeric timestamp (seconds since epoch).

    Returns:
        ISO date string or None if invalid.

    Raises:
        ValueError: If timestamp is negative.
    """
    try:
        if value < 0:
            raise ValueError(f"Negative timestamp value: {value}")
        return datetime.fromtimestamp(value).date().isoformat()
    except (OSError, OverflowError, ValueError):
        logger.warning(f"Invalid timestamp value: {value}")
        return None


def _normalize_string_timestamp(ts: str) -> str | None:
    """Normalize string timestamp to ISO date string.

    Args:
        ts: String timestamp in various formats.

    Returns:
        ISO date string, original string if unparseable, or None if empty.
    """
    ts = ts.strip()
    if not ts:
        return None

    # Handle ISO format with timezone
    iso_candidate = ts.replace("Z", "+00:00") if ts.endswith("Z") else ts

    # Try different parsing strategies
    for fmt in ISO_FORMATS:
        try:
            if fmt is None:
                dt = datetime.fromisoformat(iso_candidate)
            else:
                dt = datetime.strptime(ts, fmt)
            return dt.date().isoformat()
        except ValueError:
            continue

    # If no format worked, return the original string
    # This preserves the original behavior for unparseable strings
    return ts


def format_created_updated_label(created_at: Any | None, updated_at: Any | None) -> str | None:
    """Build a compact label combining created/updated timestamps when available.

    Creates a human-readable label that shows creation and update timestamps
    in a compact format. If both dates are the same, only shows one date.

    Args:
        created_at: The creation timestamp (any format supported by normalize_timestamp_to_date).
        updated_at: The update timestamp (any format supported by normalize_timestamp_to_date).

    Returns:
        str | None: A formatted label string, or None if both inputs are invalid/empty.
            Examples: "2022-01-01", "2022-01-01 (updated 2022-01-02)", "updated 2022-01-01"

    Examples:
        >>> format_created_updated_label("2022-01-01", "2022-01-02")
        '2022-01-01 (updated 2022-01-02)'
        >>> format_created_updated_label("2022-01-01", "2022-01-01")
        '2022-01-01'
        >>> format_created_updated_label(None, "2022-01-01")
        'updated 2022-01-01'
        >>> format_created_updated_label("2022-01-01", None)
        '2022-01-01'
    """
    created = normalize_timestamp_to_date(created_at)
    updated = normalize_timestamp_to_date(updated_at)

    if created and updated:
        if created == updated:
            return created
        return f"{created} (updated {updated})"
    if created:
        return created
    if updated:
        return f"updated {updated}"
    return None


def is_valid_date_string(date_str: str, fmt: str = DEFAULT_DATE_FORMAT) -> bool:
    """Validate that a date string matches the provided strftime format.

    Args:
        date_str: The date string to validate. Must be a non-empty string.
        fmt: The strftime format pattern to validate against.
            Defaults to YYYY-MM-DD format.

    Returns:
        bool: True if the date string matches the format, False otherwise.

    Raises:
        ValueError: If the format string is empty or invalid, or if date_str is not a string.

    Examples:
        >>> is_valid_date_string("2022-01-01")
        True
        >>> is_valid_date_string("2022-13-01")
        False
        >>> is_valid_date_string("01-01-2022", "%m-%d-%Y")
        True
        >>> is_valid_date_string("", "%Y-%m-%d")
        False
    """
    if not isinstance(date_str, str):
        raise ValueError(f"date_str must be a string, got {type(date_str).__name__}")

    if not fmt or not fmt.strip():
        raise ValueError("Format string cannot be empty")

    if not date_str or not date_str.strip():
        return False

    try:
        datetime.strptime(date_str.strip(), fmt)
        return True
    except (ValueError, TypeError) as e:
        logger.debug(f"Date string '{date_str}' does not match format '{fmt}': {e}")
        return False


def next_day_iso(date_str: str) -> str:
    """Return the ISO date string for the day after the given ``YYYY-MM-DD`` date.

    Args:
        date_str: A date string in ``YYYY-MM-DD`` format.

    Returns:
        str: The next day's date in ``YYYY-MM-DD`` format.

    Raises:
        ValueError: If ``date_str`` is not a valid ``YYYY-MM-DD`` date string.
    """
    try:
        pivot = datetime.strptime(date_str.strip(), "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(f"Invalid date string '{date_str}'. Expected YYYY-MM-DD.") from exc

    next_day = pivot + timedelta(days=1)
    return next_day.date().isoformat()
