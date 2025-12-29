"""GL Connector tool wrapper for BOSA connector tools.

Authors:
    Saul Sayers (saul.sayers@gdplabs.id)

Reference:
    https://gl-docs.gitbook.io/bosa/gl-connector/gl-connector
"""

from __future__ import annotations

import os
from collections.abc import Iterable
from typing import Any

from bosa_connectors import BosaConnector, BOSAConnectorToolGenerator
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from pydantic import ConfigDict, PrivateAttr

from aip_agents.tools.constants import ToolType

_REQUIRED_ENV_VARS: tuple[str, ...] = (
    "BOSA_BASE_URL",
    "BOSA_API_KEY",
    "BOSA_USERNAME",
    "BOSA_PASSWORD",
)
_TOP_LEVEL_KEYS: tuple[str, ...] = (
    "token",
    "identifier",
    "timeout",
    "request",
)


class _InjectedTool(BaseTool):
    """Wrap a BaseTool to inject token and optional identifier into inputs."""

    _base_tool: BaseTool = PrivateAttr()
    _token: str = PrivateAttr()
    _identifier: str | None = PrivateAttr(default=None)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def __init__(self, base_tool: BaseTool, token: str, identifier: str | None) -> None:
        """Initialize the injected tool wrapper.

        Args:
            base_tool: The base tool to wrap.
            token: Authentication token to inject into tool inputs.
            identifier: Optional identifier to inject into tool inputs.

        Returns:
            None
        """
        base_fields = {field: getattr(base_tool, field) for field in BaseTool.model_fields}
        super().__init__(**base_fields)
        self._base_tool = base_tool
        self._token = token
        self._identifier = identifier

    def _run(self, *args: Any, **kwargs: Any) -> Any:
        """Execute the wrapped tool synchronously.

        Args:
            *args: Positional arguments to pass to the base tool.
            **kwargs: Keyword arguments to pass to the base tool.

        Returns:
            The result of executing the base tool.
        """
        return self._base_tool._run(*args, **kwargs)

    async def _arun(self, *args: Any, **kwargs: Any) -> Any:
        """Execute the wrapped tool asynchronously.

        Args:
            *args: Positional arguments to pass to the base tool.
            **kwargs: Keyword arguments to pass to the base tool.

        Returns:
            The result of executing the base tool.
        """
        return await self._base_tool._arun(*args, **kwargs)

    def invoke(self, input: Any, config: RunnableConfig | None = None, **kwargs: Any) -> Any:
        """Invoke the tool with token and optional identifier injected.

        Args:
            input: Tool input to process.
            config: Optional runnable configuration.
            **kwargs: Additional keyword arguments.

        Returns:
            The result of invoking the tool with injected parameters.
        """
        injected = _inject_params(input, self._token, self._identifier, self._base_tool)
        return super().invoke(injected, config=config, **kwargs)

    async def ainvoke(self, input: Any, config: RunnableConfig | None = None, **kwargs: Any) -> Any:
        """Invoke the tool asynchronously with token and optional identifier injected.

        Args:
            input: Tool input to process.
            config: Optional runnable configuration.
            **kwargs: Additional keyword arguments.

        Returns:
            The result of invoking the tool with injected parameters.
        """
        injected = _inject_params(input, self._token, self._identifier, self._base_tool)
        return await super().ainvoke(injected, config=config, **kwargs)

    def run(self, tool_input: Any, **kwargs: Any) -> Any:
        """Run the tool with token and optional identifier injected.

        Args:
            tool_input: Tool input to process.
            **kwargs: Additional keyword arguments.

        Returns:
            The result of running the tool with injected parameters.
        """
        injected = _inject_params(tool_input, self._token, self._identifier, self._base_tool)
        return super().run(injected, **kwargs)

    async def arun(self, tool_input: Any, **kwargs: Any) -> Any:
        """Run the tool asynchronously with token and optional identifier injected.

        Args:
            tool_input: Tool input to process.
            **kwargs: Additional keyword arguments.

        Returns:
            The result of running the tool with injected parameters.
        """
        injected = _inject_params(tool_input, self._token, self._identifier, self._base_tool)
        return await super().arun(injected, **kwargs)


def GLConnectorTool(
    tool_name: str,
    *,
    api_key: str | None = None,
    identifier: str | None = None,
) -> BaseTool:
    """Create a single GL Connector tool by exact tool name.

    Args:
        tool_name: Exact tool name (not module name).
        api_key: Optional override for BOSA API key.
        identifier: Optional override for BOSA identifier.

    Returns:
        A single LangChain BaseTool with token injection.
    """
    if not tool_name or not tool_name.strip():
        raise ValueError("tool_name must be a non-empty string")

    env_values = _load_env(api_key=api_key, identifier=identifier)
    connector = BosaConnector(api_base_url=env_values["BOSA_BASE_URL"], api_key=env_values["BOSA_API_KEY"])

    modules = _get_available_modules(connector)
    module_name = _resolve_module(tool_name, modules)

    generator = BOSAConnectorToolGenerator(
        api_base_url=env_values["BOSA_BASE_URL"],
        api_key=env_values["BOSA_API_KEY"],
        app_name=module_name,
    )
    tools = generator.generate_tools(tool_type=ToolType.LANGCHAIN)

    matching = [tool for tool in tools if getattr(tool, "name", None) == tool_name]
    if not matching:
        raise ValueError(f"Tool '{tool_name}' not found in module '{module_name}'")
    if len(matching) > 1:
        raise ValueError(f"Multiple tools named '{tool_name}' found in module '{module_name}'")

    token = _create_token(connector, env_values["BOSA_USERNAME"], env_values["BOSA_PASSWORD"])
    return _InjectedTool(matching[0], token, env_values.get("BOSA_IDENTIFIER"))


def _load_env(*, api_key: str | None, identifier: str | None) -> dict[str, str]:
    """Load and validate environment configuration for connector access.

    Args:
        api_key: Optional override for BOSA API key.
        identifier: Optional override for BOSA identifier.

    Returns:
        Dictionary containing environment configuration values.

    Raises:
        ValueError: If required environment variables are missing.
    """
    env = {key: os.getenv(key) for key in _REQUIRED_ENV_VARS}

    resolved_api_key = api_key or env["BOSA_API_KEY"]
    env["BOSA_API_KEY"] = resolved_api_key

    optional_identifier = identifier or os.getenv("BOSA_IDENTIFIER")

    if optional_identifier:
        env["BOSA_IDENTIFIER"] = optional_identifier

    missing = [key for key, value in env.items() if key in _REQUIRED_ENV_VARS and not value]
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

    return {key: value for key, value in env.items() if value is not None}


def _get_available_modules(connector: BosaConnector) -> list[str]:
    """Return available connector modules or raise an actionable error.

    Args:
        connector: BOSA connector instance to query for modules.

    Returns:
        List of available module names.

    Raises:
        ValueError: If module fetching fails or no modules are available.
    """
    try:
        modules = list(connector.get_available_modules())
    except Exception as exc:
        raise ValueError("Failed to fetch available connector modules") from exc

    if not modules:
        raise ValueError("No connector modules available")
    return modules


def _resolve_module(tool_name: str, modules: Iterable[str]) -> str:
    """Resolve the module name by longest prefix match.

    Args:
        tool_name: Name of the tool to resolve module for.
        modules: Iterable of available module names.

    Returns:
        The resolved module name.

    Raises:
        ValueError: If no matching module is found or multiple ambiguous matches exist.
    """
    candidates = [module for module in modules if tool_name == module or tool_name.startswith(f"{module}_")]
    if not candidates:
        raise ValueError(f"Unable to resolve module for tool '{tool_name}'. Available modules: {', '.join(modules)}")

    candidates.sort(key=len, reverse=True)
    if len(candidates) > 1 and len(candidates[0]) == len(candidates[1]):
        raise ValueError(f"Ambiguous module match for tool '{tool_name}'. Matches: {', '.join(candidates)}")
    return candidates[0]


def _create_token(connector: BosaConnector, username: str, password: str) -> str:
    """Authenticate the connector user and return a user token.

    Args:
        connector: BOSA connector instance for authentication.
        username: BOSA username for authentication.
        password: BOSA password for authentication.

    Returns:
        Authentication token string.

    Raises:
        ValueError: If authentication fails or token is missing.
    """
    try:
        user = connector.authenticate_bosa_user(username, password)
    except Exception as exc:
        raise ValueError("Failed to authenticate BOSA user") from exc

    token = getattr(user, "token", None)
    if not token:
        raise ValueError("BOSA user token missing after authentication")
    return token


def _inject_params(tool_input: Any, token: str, identifier: str | None, base_tool: BaseTool) -> dict[str, Any]:
    """Inject token and optional identifier into tool input.

    Args:
        tool_input: Original tool input dictionary.
        token: Authentication token to inject.
        identifier: Optional identifier to inject.
        base_tool: Base tool instance for schema inspection.

    Returns:
        Dictionary with token and optional identifier injected.

    Raises:
        TypeError: If tool_input is not a dictionary.
    """
    if tool_input is None:
        tool_input = {}

    if not isinstance(tool_input, dict):
        raise TypeError("Connector tool input must be a dict to inject token")

    if "args" in tool_input and isinstance(tool_input.get("args"), dict):
        injected_args = dict(tool_input["args"])
        injected_args["token"] = token
        if identifier:
            injected_args["identifier"] = identifier
        injected = dict(tool_input)
        injected["args"] = injected_args
        return injected

    injected = dict(tool_input)
    injected = _wrap_request_if_needed(injected, base_tool)
    injected["token"] = token
    if identifier:
        injected["identifier"] = identifier
    return injected


def _wrap_request_if_needed(tool_input: dict[str, Any], base_tool: BaseTool) -> dict[str, Any]:
    """Wrap flat inputs into a 'request' payload when required by schema.

    Args:
        tool_input: Tool input dictionary to potentially wrap.
        base_tool: Base tool instance for schema inspection.

    Returns:
        Dictionary with inputs wrapped in 'request' key if needed, otherwise unchanged.
    """
    args_schema = getattr(base_tool, "args_schema", None)
    if not (isinstance(args_schema, dict) and "request" in args_schema.get("properties", {})):
        return tool_input

    request_payload = {}
    existing_request = tool_input.get("request")
    if isinstance(existing_request, dict):
        request_payload.update(existing_request)

    for key, value in tool_input.items():
        if key in _TOP_LEVEL_KEYS:
            continue
        request_payload.setdefault(key, value)

    wrapped = dict(tool_input)
    wrapped["request"] = request_payload
    for key in list(wrapped.keys()):
        if key not in _TOP_LEVEL_KEYS:
            wrapped.pop(key, None)
    return wrapped
