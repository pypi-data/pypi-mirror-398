"""Helper utilities used across the activity narrative package.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

import re

from aip_agents.utils.metadata.activity_narrative.constants import DELEGATE_PREFIX


def _format_tool_or_subagent_name(name: str, remove_delegate_prefix: bool = False) -> str:
    """Format tool/agent names to 'Camel Case' consistently.

    Args:
        name: Raw tool or sub-agent identifier.
        remove_delegate_prefix: Whether to strip the ``delegate::`` prefix before formatting.

    Returns:
        str: Display-friendly tool or agent name.
    """
    clean_name = name.replace(DELEGATE_PREFIX, "") if remove_delegate_prefix else name
    s = clean_name.replace("_", " ")

    if s == s.lower():
        return " ".join(w.capitalize() for w in s.split())

    s = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", s)
    s = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", " ", s)
    return " ".join(word if word.isupper() else (word[:1].upper() + word[1:].lower()) for word in s.split())


__all__ = ["_format_tool_or_subagent_name"]
