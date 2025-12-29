"""Tool Configuration Injector for existing LangChain tools.

This module provides utilities to inject Pydantic-based configuration into existing
LangChain tools without requiring inheritance or modification of the tool classes.

The SDK automatically injects configuration capabilities into tools that have a
tool_config_schema attribute, providing:
- Agent-level default configurations
- Runtime configuration overrides via RunnableConfig metadata
- Type-safe validation using Pydantic models
- Support for optional fields with proper default handling

Configuration Extraction Examples:

    Nested format:
        metadata = {"tool_configs": {"tool_name": {"api_key": "secret", "timeout": 30}}}

    Flattened format (only works if ALL required fields are present):
        metadata = {"api_key": "secret", "timeout": 30}  # Optional fields can be omitted

    Required vs Optional fields:
        class ToolConfig(BaseModel):
            api_key: str              # Required - must be provided
            timeout: int = 30         # Optional - will use default if not provided
            retries: Optional[int] = None  # Optional - can be None

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

from typing import Any, TypeVar

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from pydantic import BaseModel

from aip_agents.utils.logger import get_logger

logger = get_logger(__name__)

ConfigSchema = TypeVar("ConfigSchema", bound=BaseModel)

# Public API exports
__all__ = [
    "inject_config_methods_into_tool",
    "CONFIG_SCHEMA_ATTR",
    "CONFIG_ATTR",
    "TOOL_CONFIG_SCHEMA_ATTR",
    "TOOL_CONFIGS_KEY",
]

# Constants for configuration attribute names and keys
CONFIG_SCHEMA_ATTR: str = "_config_schema"
CONFIG_ATTR: str = "_config"
TOOL_CONFIG_SCHEMA_ATTR: str = "tool_config_schema"
TOOL_CONFIGS_KEY: str = "tool_configs"


def _get_config_field_names(schema: type[BaseModel]) -> list[str]:
    """Get field names from a Pydantic model schema.

    Args:
        schema: The Pydantic model schema to get field names from.

    Returns:
        A list of field names.
    """
    if hasattr(schema, "model_fields"):
        return list(schema.model_fields.keys())
    elif hasattr(schema, "__fields__"):
        return list(schema.__fields__.keys())
    else:
        return []


def _get_required_field_names(schema: type[BaseModel]) -> set[str]:
    """Get required field names from a Pydantic model schema.

    Args:
        schema: The Pydantic model schema to get required field names from.

    Returns:
        A set of required field names.
    """
    # Pydantic V2
    if hasattr(schema, "model_fields"):
        return {name for name, field_info in schema.model_fields.items() if field_info.is_required()}

    # Pydantic V1 (fallback)
    elif hasattr(schema, "__fields__"):
        return {name for name, field in schema.__fields__.items() if field.required}

    return set()


def _extract_nested_config(tool: BaseTool, metadata: dict[str, Any]) -> ConfigSchema | None:
    """Extract tool config from nested tool_configs structure.

    Args:
        tool: The tool instance to extract configuration from.
        metadata: The metadata to use.

    Returns:
        The nested configuration.
    """
    tool_configs = metadata.get(TOOL_CONFIGS_KEY, {})
    if not isinstance(tool_configs, dict) or tool.name not in tool_configs:
        return None

    tool_config_data = tool_configs[tool.name]
    try:
        config_schema = getattr(tool, CONFIG_SCHEMA_ATTR)
        if isinstance(tool_config_data, dict):
            return config_schema(**tool_config_data)
        elif isinstance(tool_config_data, config_schema):
            return tool_config_data
    except Exception as e:
        logger.debug(f"Failed to validate nested config for tool '{tool.name}': {e}")

    return None


def _extract_flattened_config(tool: BaseTool, metadata: dict[str, Any]) -> ConfigSchema | None:
    """Extract tool config from flattened metadata keys.

    This function builds a configuration from metadata keys that match the tool's
    config schema field names. Only required fields must be present; optional fields
    with defaults will be handled by Pydantic during instantiation.

    Behavior:
    - Returns None silently if metadata is empty (likely using agent defaults)
    - Logs debug message if metadata exists but contains no matching config fields
    - Logs warning if some required fields are missing from provided config fields

    Args:
        tool: The tool instance to extract configuration from.
        metadata: The metadata to use.

    Returns:
        The flattened configuration if all required fields are present, None otherwise.
    """
    config_schema = getattr(tool, CONFIG_SCHEMA_ATTR)
    config_fields = _get_config_field_names(config_schema)
    required_fields = _get_required_field_names(config_schema)

    if not config_fields:
        return None

    # Extract all available config fields from metadata
    flattened_config = {}
    for field_name in config_fields:
        if field_name in metadata:
            flattened_config[field_name] = metadata[field_name]

    # Only proceed if we have at least some configuration fields
    if not flattened_config:
        if metadata:
            logger.debug(
                f"No valid config fields found in flattened metadata for tool '{tool.name}'. "
                f"Available metadata keys: {list(metadata.keys())}, "
                f"Expected config fields: {config_fields}"
            )
        return None

    # Check if all required fields are present
    provided_fields = set(flattened_config.keys())
    missing_required_fields = required_fields - provided_fields

    if missing_required_fields:
        logger.warning(f"Missing required fields for flattened config in tool '{tool.name}': {missing_required_fields}")
        return None

    try:
        return config_schema(**flattened_config)
    except Exception as e:
        logger.debug(f"Failed to validate flattened config for tool '{tool.name}': {e}")

    return None


def _extract_runtime_config(tool: BaseTool, config: RunnableConfig | None) -> ConfigSchema | None:
    """Extract runtime configuration from RunnableConfig metadata.

    Args:
        tool: The tool instance to extract configuration from.
        config: The configuration to use.

    Returns:
        The runtime configuration.
    """
    if not config or not hasattr(tool, CONFIG_SCHEMA_ATTR):
        return None

    metadata = config.get("metadata", {})
    if not isinstance(metadata, dict):
        return None

    # Try nested structure first
    nested_config = _extract_nested_config(tool, metadata)
    if nested_config is not None:
        return nested_config

    # Try flattened structure
    return _extract_flattened_config(tool, metadata)


def _create_tool_config_methods(tool: BaseTool) -> dict[str, Any]:
    """Create the configuration management methods for a tool.

    Args:
        tool: The tool instance to create methods for.

    Returns:
        Dictionary of method names to method functions.
    """

    def set_tool_config(config: ConfigSchema | dict[str, Any] | None) -> None:
        """Set the tool's agent-level default configuration with validation.

        Args:
            config: The configuration to set.

        Raises:
            ValueError: If the config is not an instance of the tool's config schema or a dictionary.
        """
        if config is None:
            object.__setattr__(tool, CONFIG_ATTR, None)
            return

        config_schema = getattr(tool, CONFIG_SCHEMA_ATTR)
        if isinstance(config, dict):
            object.__setattr__(tool, CONFIG_ATTR, config_schema(**config))
        elif isinstance(config, config_schema):
            object.__setattr__(tool, CONFIG_ATTR, config)
        else:
            config_schema_name = getattr(config_schema, "__name__", repr(config_schema))
            raise ValueError(f"Config must be an instance of {config_schema_name} or dict, got {type(config).__name__}")

    def get_default_config() -> ConfigSchema | None:
        """Get the agent-level default configuration.

        Returns:
            The agent-level default configuration.
        """
        return getattr(tool, CONFIG_ATTR)

    def has_tool_config() -> bool:
        """Check if the tool has an agent-level default configuration set.

        Returns:
            True if the tool has an agent-level default configuration set, False otherwise.
        """
        return getattr(tool, CONFIG_ATTR) is not None

    def get_tool_config(config: RunnableConfig | None = None) -> ConfigSchema | None:
        """Get the effective tool configuration.

        This function extracts the tool configuration from the runnable configuration.
        If the tool configuration is not found in the runnable configuration, it will
        return the agent-level default configuration.

        Args:
            config: The runnable configuration to use from LangGraph.

        Returns:
            The effective tool configuration.
        """
        runtime_config = _extract_runtime_config(tool, config)
        return runtime_config if runtime_config is not None else getattr(tool, CONFIG_ATTR)

    return {
        "set_tool_config": set_tool_config,
        "get_default_config": get_default_config,
        "has_tool_config": has_tool_config,
        "get_tool_config": get_tool_config,
    }


def inject_config_methods_into_tool(tool: BaseTool, config_schema: type[ConfigSchema]) -> None:
    """Inject configuration methods into a tool.

    This function is used by the SDK to automatically inject configuration capabilities
    into tools that have a tool_config_schema attribute. It can also be used directly
    by developers who want to add configuration support to their tools.

    Args:
        tool: The tool to inject configuration capabilities into.
        config_schema: Pydantic model class for configuration validation.

    Raises:
        ValueError: If tool is not a BaseTool instance or config_schema is not a Pydantic BaseModel subclass.
    """
    # Add configuration attributes
    object.__setattr__(tool, CONFIG_SCHEMA_ATTR, config_schema)
    object.__setattr__(tool, CONFIG_ATTR, None)

    # Create and inject methods
    methods = _create_tool_config_methods(tool)
    for method_name, method_func in methods.items():
        object.__setattr__(tool, method_name, method_func)
