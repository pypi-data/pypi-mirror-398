__all__ = ['_format_tool_or_subagent_name']

def _format_tool_or_subagent_name(name: str, remove_delegate_prefix: bool = False) -> str:
    """Format tool/agent names to 'Camel Case' consistently.

    Args:
        name: Raw tool or sub-agent identifier.
        remove_delegate_prefix: Whether to strip the ``delegate::`` prefix before formatting.

    Returns:
        str: Display-friendly tool or agent name.
    """
