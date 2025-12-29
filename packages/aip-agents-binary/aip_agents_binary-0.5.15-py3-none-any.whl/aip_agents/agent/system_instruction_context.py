"""Utilities for constructing agent system instructions.

Authors:
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

from __future__ import annotations

from aip_agents.utils.constants import DefaultTimezone
from aip_agents.utils.datetime import get_timezone_aware_now

__all__ = ["get_current_date_context", "DefaultTimezone"]


def get_current_date_context(timezone: str = DefaultTimezone.JAKARTA) -> str:
    """Generate current date context for system prompts.

    Args:
        timezone: IANA timezone name for date formatting.

    Returns:
        Formatted date context string for inclusion in system prompts.
    """
    now, timezone_label, used_fallback = get_timezone_aware_now(timezone)
    display_timezone = "UTC" if used_fallback else timezone_label
    current_date = now.strftime("%Y-%m-%d")

    return (
        f"Very important: The user's timezone is {display_timezone}. "
        f"The current date is {current_date}\n\n"
        "Any dates before this are in the past, and any dates after this are in the future. "
        "When the user asks for the 'latest', 'most recent', 'today's', etc. don't assume\n"
        "your knowledge is up to date."
    )
