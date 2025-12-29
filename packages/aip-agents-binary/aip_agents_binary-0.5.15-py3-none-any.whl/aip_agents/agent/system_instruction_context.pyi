from aip_agents.utils.constants import DefaultTimezone as DefaultTimezone

__all__ = ['get_current_date_context', 'DefaultTimezone']

def get_current_date_context(timezone: str = ...) -> str:
    """Generate current date context for system prompts.

    Args:
        timezone: IANA timezone name for date formatting.

    Returns:
        Formatted date context string for inclusion in system prompts.
    """
