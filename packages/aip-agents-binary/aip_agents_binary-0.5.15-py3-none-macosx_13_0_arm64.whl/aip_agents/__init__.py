"""AIP Agents package entrypoint."""

from __future__ import annotations

import importlib
import sys
from typing import Any

__all__: list[str] = []


def _export(module_name: str) -> None:
    """Export a submodule to package level.

    Args:
        module_name: Name of the submodule to export.
    """
    module = importlib.import_module(f"{__name__}.{module_name}")
    globals()[module_name] = module
    __all__.append(module_name)


for _mod in [
    "a2a",
    "agent",
    "clients",
    "constants",
    "credentials",
    "executor",
    "memory",
    "mcp",
    "schema",
    "sentry",
    "storage",
    "tools",
    "types",
    "utils",
]:
    try:
        _export(_mod)
    except ModuleNotFoundError:
        continue

__version__ = "0.0.0"
__all__.append("__version__")


def __getattr__(name: str) -> Any:  # pragma: no cover
    """Get attribute dynamically for lazy module loading.

    Args:
        name: Attribute name to retrieve.

    Returns:
        Attribute value from globals.

    Raises:
        AttributeError: If attribute is not found.
    """
    if name in globals():
        return globals()[name]
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


sys.modules.setdefault("aip_agents", sys.modules[__name__])
