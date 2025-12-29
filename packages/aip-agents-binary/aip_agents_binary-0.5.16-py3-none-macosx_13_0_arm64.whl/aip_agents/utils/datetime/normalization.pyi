from typing import Any

__all__ = ['normalize_timestamp_to_date', 'format_created_updated_label', 'is_valid_date_string', 'next_day_iso']

def normalize_timestamp_to_date(value: Any) -> str | None:
    '''Normalize various timestamp representations into a YYYY-MM-DD string.

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
        \'2022-01-01\'
        >>> normalize_timestamp_to_date("2022-01-01T12:00:00")
        \'2022-01-01\'
        >>> normalize_timestamp_to_date("invalid")
        \'invalid\'
        >>> normalize_timestamp_to_date(None)
        None
    '''
def format_created_updated_label(created_at: Any | None, updated_at: Any | None) -> str | None:
    '''Build a compact label combining created/updated timestamps when available.

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
        \'2022-01-01 (updated 2022-01-02)\'
        >>> format_created_updated_label("2022-01-01", "2022-01-01")
        \'2022-01-01\'
        >>> format_created_updated_label(None, "2022-01-01")
        \'updated 2022-01-01\'
        >>> format_created_updated_label("2022-01-01", None)
        \'2022-01-01\'
    '''
def is_valid_date_string(date_str: str, fmt: str = ...) -> bool:
    '''Validate that a date string matches the provided strftime format.

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
    '''
def next_day_iso(date_str: str) -> str:
    """Return the ISO date string for the day after the given ``YYYY-MM-DD`` date.

    Args:
        date_str: A date string in ``YYYY-MM-DD`` format.

    Returns:
        str: The next day's date in ``YYYY-MM-DD`` format.

    Raises:
        ValueError: If ``date_str`` is not a valid ``YYYY-MM-DD`` date string.
    """
