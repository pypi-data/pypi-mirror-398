from datetime import datetime

__all__ = ['get_timezone_aware_now', 'ensure_utc_datetime']

def get_timezone_aware_now(timezone: str, fallback_timezone: str = 'UTC') -> tuple[datetime, str, bool]:
    '''Return a timezone-aware datetime alongside a timezone label.

    This function creates a timezone-aware datetime object using the modern
    zoneinfo module (Python 3.9+). It gracefully falls back to UTC if the
    requested timezone is invalid.

    Args:
        timezone: Desired timezone name in IANA format (e.g., "America/New_York",
            "Europe/London", "Asia/Tokyo"). Must be a non-empty string.
        fallback_timezone: Fallback timezone name to use when the primary
            timezone is invalid. Defaults to "UTC". Must be a non-empty string.

    Returns:
        tuple[datetime, str, bool]: A 3-tuple containing:
            - now: A timezone-aware datetime object representing the current time
            - timezone_label: A human-readable timezone label (e.g., "EST", "UTC")
            - used_fallback: Boolean indicating whether the fallback timezone was used

    Raises:
        ValueError: If timezone or fallback_timezone are empty/invalid, or if both
            the requested timezone and fallback timezone are invalid.

    Examples:
        >>> now, label, fallback = get_timezone_aware_now("America/New_York")
        >>> print(f"Current time: {now}, Timezone: {label}, Used fallback: {fallback}")
        Current time: 2024-01-15 10:30:00-05:00, Timezone: EST, Used fallback: False

        >>> now, label, fallback = get_timezone_aware_now("Invalid/Timezone")
        >>> print(f"Used fallback: {fallback}, Label: {label}")
        Used fallback: True, Label: UTC
    '''
def ensure_utc_datetime(value: datetime) -> datetime:
    """Normalize a datetime to UTC (attaching UTC to naive values).

    Args:
        value: Datetime to normalize.

    Returns:
        datetime: Timezone-aware datetime expressed in UTC.

    Raises:
        TypeError: If ``value`` is not a ``datetime`` instance.
    """
