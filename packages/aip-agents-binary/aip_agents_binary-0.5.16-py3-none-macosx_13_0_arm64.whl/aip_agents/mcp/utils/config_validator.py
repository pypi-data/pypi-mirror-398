"""Configuration validation utilities for MCP.

This module provides validation logic for MCP server configurations,
specifically for the allowed_tools feature.

Authors:
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

from typing import Any

from aip_agents.utils.logger import get_logger

logger = get_logger(__name__)


def validate_allowed_tools_list(
    allowed_tools: list[str] | None,
    context: str,
) -> list[str] | None:
    """Validate that allowed_tools is a list of strings or None.

    This function validates the type and contents of allowed_tools parameter.
    It can be used to validate allowed_tools from any source (config dict, function parameter, etc).

    Args:
        allowed_tools: The allowed_tools value to validate (can be any type)
        context: Context string for error messages (e.g., "Server 'my_server'", "'allowed_tools' parameter")

    Returns:
        Validated list of allowed tool names, or None if allowed_tools is None or empty.
        None/empty means no restriction (all tools allowed).

    Raises:
        ValueError: If allowed_tools is not None/list or contains non-string elements

    Examples:
        >>> validate_allowed_tools_list(None, "test")
        None
        >>> validate_allowed_tools_list([], "test")
        None
        >>> validate_allowed_tools_list(["tool1", "tool2"], "test")
        ['tool1', 'tool2']
        >>> validate_allowed_tools_list("invalid", "test")  # doctest: +SKIP
        ValueError: test: 'allowed_tools' must be a list of strings, got str
    """
    # None or empty list is valid and means no restriction
    if allowed_tools is None or allowed_tools == []:
        return None

    # Validate that it's a list
    if not isinstance(allowed_tools, list):
        raise ValueError(f"{context}: 'allowed_tools' must be a list of strings, got {type(allowed_tools).__name__}")

    # Validate that all elements are strings
    for idx, tool_name in enumerate(allowed_tools):
        if not isinstance(tool_name, str):
            raise ValueError(f"{context}: 'allowed_tools[{idx}]' must be a string, got {type(tool_name).__name__}")
        if not tool_name.strip():
            raise ValueError(f"{context}: 'allowed_tools[{idx}]' must be a non-empty string")

    return allowed_tools


def validate_allowed_tools_config(config: dict[str, Any], server_name: str) -> list[str] | None:
    """Validate and extract allowed_tools configuration from server config.

    This function validates that the allowed_tools field, if present, is a list of strings.
    It returns a normalized list of allowed tool names, or None if not specified/empty.

    Args:
        config: Server configuration dictionary that may contain 'allowed_tools' field
        server_name: Name of the server (for error messages)

    Returns:
        List of allowed tool names, or None if allowed_tools is not specified or is empty.
        None means no restriction (all tools allowed).

    Raises:
        ValueError: If allowed_tools is present but not a list
        ValueError: If allowed_tools contains non-string elements

    Examples:
        >>> validate_allowed_tools_config({"url": "..."}, "my_server")
        None
        >>> validate_allowed_tools_config({"url": "...", "allowed_tools": []}, "my_server")
        None
        >>> validate_allowed_tools_config({"url": "...", "allowed_tools": ["tool1", "tool2"]}, "my_server")
        ['tool1', 'tool2']
    """
    if "allowed_tools" not in config:
        return None

    allowed_tools = config["allowed_tools"]

    # Use common validation logic
    return validate_allowed_tools_list(allowed_tools, f"Server '{server_name}'")


def validate_mcp_server_config(config: dict[str, Any], server_name: str) -> dict[str, Any]:
    """Validate complete MCP server configuration including allowed_tools.

    This function performs comprehensive validation on an MCP server configuration,
    ensuring all required fields are present and allowed_tools (if present) is valid.
    Unknown configuration fields (such as any leftover disabled_tools) are silently ignored.

    Args:
        config: Server configuration dictionary
        server_name: Name of the server (for error messages)

    Returns:
        Validated configuration dictionary (same as input, after validation)

    Raises:
        ValueError: If configuration is invalid

    Examples:
        >>> validate_mcp_server_config({"url": "http://localhost:8080"}, "my_server")
        {'url': 'http://localhost:8080'}
        >>> validate_mcp_server_config({"command": "python", "args": ["server.py"]}, "my_server")
        {'command': 'python', 'args': ['server.py']}
    """
    if not isinstance(config, dict):
        raise ValueError(f"Server '{server_name}': configuration must be a dictionary")

    if not config:
        raise ValueError(f"Server '{server_name}': configuration must not be empty")

    # Validate required fields (url OR command)
    has_url = "url" in config
    has_command = "command" in config

    if not (has_url or has_command):
        raise ValueError(f"Server '{server_name}': must have either 'url' or 'command' field")

    # Validate allowed_tools if present (ignore unknown fields like disabled_tools)
    validate_allowed_tools_config(config, server_name)

    return config
