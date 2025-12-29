"""Timezone-related helper functions."""

from __future__ import annotations

from datetime import datetime
from typing import Final
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from aip_agents.utils.logger import get_logger

__all__ = ["get_timezone_aware_now", "ensure_utc_datetime"]

logger: Final = get_logger(__name__)


def get_timezone_aware_now(timezone: str, fallback_timezone: str = "UTC") -> tuple[datetime, str, bool]:
    """Return a timezone-aware datetime alongside a timezone label.

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
    """
    timezone = _normalize_timezone("timezone", timezone)
    fallback_timezone = _normalize_timezone("fallback_timezone", fallback_timezone)

    tz, used_fallback = _load_timezone_with_case_enforcement(timezone, fallback_timezone)
    now = datetime.now(tz)
    timezone_label = _resolve_timezone_label(now, timezone, fallback_timezone, used_fallback)

    return now, timezone_label, used_fallback


def ensure_utc_datetime(value: datetime) -> datetime:
    """Normalize a datetime to UTC (attaching UTC to naive values).

    Args:
        value: Datetime to normalize.

    Returns:
        datetime: Timezone-aware datetime expressed in UTC.

    Raises:
        TypeError: If ``value`` is not a ``datetime`` instance.
    """
    if not isinstance(value, datetime):
        raise TypeError(f"Expected datetime, received {type(value).__name__}")

    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        return value.replace(tzinfo=ZoneInfo("UTC"))

    return value.astimezone(ZoneInfo("UTC"))


def _normalize_timezone(param_name: str, value: str) -> str:
    """Validate and normalize a timezone parameter.

    Args:
        param_name: Name of the parameter being validated, used in error messages.
        value: Raw timezone string provided by the caller.

    Returns:
        A stripped, non-empty timezone string.

    Raises:
        ValueError: If ``value`` is not a non-empty string.
    """
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{param_name} must be a non-empty string")
    return value.strip()


def _load_timezone_with_case_enforcement(timezone: str, fallback_timezone: str) -> tuple[ZoneInfo, bool]:
    """Load timezone ensuring case-sensitive behavior, falling back when needed.

    Args:
        timezone: Requested timezone name in IANA format.
        fallback_timezone: Fallback timezone to use when the requested one is invalid.

    Returns:
        A tuple containing the resolved ``ZoneInfo`` object and a boolean indicating
        whether the fallback timezone was used.

    Raises:
        ValueError: If both ``timezone`` and ``fallback_timezone`` are invalid.
    """
    requested_tz = _load_requested_timezone(timezone)
    if requested_tz is not None:
        return requested_tz, False

    logger.warning(
        "Timezone '%s' unavailable, attempting fallback to '%s'",
        timezone,
        fallback_timezone,
    )
    return _load_fallback_timezone(timezone, fallback_timezone)


def _load_requested_timezone(timezone: str) -> ZoneInfo | None:
    """Attempt to load the requested timezone with case enforcement.

    Args:
        timezone: Requested timezone name in IANA format.

    Returns:
        The corresponding ``ZoneInfo`` if the timezone exists and matches case,
        otherwise ``None``.
    """
    try:
        candidate_tz = ZoneInfo(timezone)
    except ZoneInfoNotFoundError:
        logger.warning("Timezone '%s' was not found", timezone)
        return None

    canonical_key = getattr(candidate_tz, "key", None)
    if canonical_key and canonical_key.lower() == timezone.lower() and canonical_key != timezone:
        logger.warning(
            "Timezone '%s' resolved to canonical key '%s'; case-sensitive handling requires an exact match",
            timezone,
            canonical_key,
        )
        return None

    logger.debug("Successfully loaded timezone: %s", timezone)
    return candidate_tz


def _load_fallback_timezone(timezone: str, fallback_timezone: str) -> tuple[ZoneInfo, bool]:
    """Load the fallback timezone or raise a descriptive error.

    Args:
        timezone: Original requested timezone name, used for error messaging.
        fallback_timezone: Fallback timezone to attempt loading.

    Returns:
        A tuple containing the fallback ``ZoneInfo`` and ``True`` to indicate that the
        fallback was used.

    Raises:
        ValueError: If the fallback timezone is also invalid.
    """
    try:
        fallback_tz = ZoneInfo(fallback_timezone)
    except ZoneInfoNotFoundError as ex:
        error_msg = (
            f"Both requested timezone '{timezone}' and fallback timezone "
            f"'{fallback_timezone}' are invalid. Please provide valid IANA timezone names."
        )
        logger.error(error_msg)
        raise ValueError(error_msg) from ex

    logger.debug("Successfully loaded fallback timezone: %s", fallback_timezone)
    return fallback_tz, True


def _resolve_timezone_label(
    now: datetime,
    timezone: str,
    fallback_timezone: str,
    used_fallback: bool,
) -> str:
    """Determine the human-readable label for the timezone used.

    Args:
        now: The timezone-aware datetime generated using the resolved timezone.
        timezone: Requested timezone name in IANA format.
        fallback_timezone: Fallback timezone name in IANA format.
        used_fallback: Whether the fallback timezone was used.

    Returns:
        A human-readable timezone label for display purposes.
    """
    if used_fallback:
        return fallback_timezone

    try:
        timezone_label = now.strftime("%Z")
        if not timezone_label:
            return timezone
        return timezone_label
    except (ValueError, OSError):
        return timezone
