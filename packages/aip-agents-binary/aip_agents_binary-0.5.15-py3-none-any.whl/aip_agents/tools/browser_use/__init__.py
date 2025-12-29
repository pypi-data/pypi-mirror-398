# flake8: noqa: F401
"""Browser use tools package for AI Agent Platform.

Authors:
    Reinhart Linanda (reinhart.linanda@gdplabs.id)
"""

import warnings
from enum import StrEnum

try:
    import json_repair
    import minio
    from browser_use import Agent
    from steel import Steel

    _TOOL_AVAILABLE = True

except ImportError:
    _TOOL_AVAILABLE = False
    warnings.warn(
        "Browser use tools not available. Install with: pip install aip-agents[browser-use-tool]",
        ImportWarning,
        stacklevel=2,
    )


class ImportableName(StrEnum):
    """Names of the importable attributes."""

    BROWSER_USE_TOOL = "BrowserUseTool"
    BROWSER_USE_TOOL_INPUT = "BrowserUseToolInput"
    BROWSER_USE_TOOL_CONFIG = "BrowserUseToolConfig"


if _TOOL_AVAILABLE:
    __all__ = [
        ImportableName.BROWSER_USE_TOOL,
        ImportableName.BROWSER_USE_TOOL_INPUT,
        ImportableName.BROWSER_USE_TOOL_CONFIG,
    ]

    _LAZY_IMPORTS = {}
else:
    # No tools available
    __all__ = []


def __getattr__(name: str):
    """Lazy import to avoid circular dependencies and import errors in tests.

    Args:
        name (str): The name of the attribute to get.

    Returns:
        The attribute value.
    """
    if not _TOOL_AVAILABLE:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    if name in _LAZY_IMPORTS:
        return _LAZY_IMPORTS[name]

    if name == ImportableName.BROWSER_USE_TOOL:
        from aip_agents.tools.browser_use.browser_use_tool import BrowserUseTool

        _LAZY_IMPORTS[name] = BrowserUseTool
        return BrowserUseTool

    if name == ImportableName.BROWSER_USE_TOOL_INPUT:
        from aip_agents.tools.browser_use.schemas import BrowserUseToolInput

        _LAZY_IMPORTS[name] = BrowserUseToolInput
        return BrowserUseToolInput

    if name == ImportableName.BROWSER_USE_TOOL_CONFIG:
        from aip_agents.tools.browser_use.schemas import BrowserUseToolConfig

        _LAZY_IMPORTS[name] = BrowserUseToolConfig
        return BrowserUseToolConfig

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
