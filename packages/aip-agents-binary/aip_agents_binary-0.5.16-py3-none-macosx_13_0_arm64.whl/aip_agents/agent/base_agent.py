"""Base class for concrete agent implementations.

This class provides common functionalities like A2A client capabilities.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

import asyncio
from collections.abc import AsyncGenerator
from importlib import import_module
from pathlib import Path
from typing import Any
from warnings import warn

import httpx
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCard
from gllm_core.utils.retry import RetryConfig
from gllm_inference.builder import build_lm_invoker
from gllm_inference.lm_invoker.lm_invoker import BaseLMInvoker
from langchain_core.language_models import BaseChatModel
from starlette.applications import Starlette

from aip_agents.agent.interface import AgentInterface
from aip_agents.credentials.manager import CredentialsManager
from aip_agents.mcp.client.base_mcp_client import BaseMCPClient
from aip_agents.schema.agent import A2AClientConfig, AgentConfig, BaseAgentConfig, CredentialType
from aip_agents.schema.model_id import ModelId, ModelProvider
from aip_agents.utils.a2a_connector import A2AConnector
from aip_agents.utils.logger import get_logger
from aip_agents.utils.name_preprocessor.name_preprocessor import NamePreprocessor

logger = get_logger(__name__)


def _get_agent_executor_mapping() -> dict[str, str]:
    """Map agent class names to their executor import paths."""
    return {
        "LangGraphReactAgent": "aip_agents.a2a.server.langgraph_executor.LangGraphA2AExecutor",
        "LangGraphAgent": "aip_agents.a2a.server.langgraph_executor.LangGraphA2AExecutor",
        "LangChainAgent": "aip_agents.a2a.server.langgraph_executor.LangGraphA2AExecutor",
        "LangflowAgent": "aip_agents.a2a.server.langflow_executor.LangflowA2AExecutor",
        "GoogleADKAgent": "aip_agents.a2a.server.google_adk_executor.GoogleADKExecutor",
    }


AGENT_EXECUTOR_MAPPING = _get_agent_executor_mapping()


def _load_executor_class(candidate: Any) -> type[Any]:
    """Resolve an executor class from a dotted path or a direct reference.

    Args:
        candidate (Any): Either a string path (e.g., "module.Class") or a class/type object.

    Returns:
        type[Any]: The resolved executor class.
    """
    if isinstance(candidate, str):
        module_name, class_name = candidate.rsplit(".", 1)
        module = import_module(module_name)
        return getattr(module, class_name)

    if isinstance(candidate, type):  # Already a class reference
        return candidate

    if callable(candidate):
        return candidate  # type: ignore[return-value]

    raise TypeError(f"Unsupported executor mapping entry: {candidate!r}")


def _get_executor_class_for_agent(agent: "BaseAgent") -> type[Any]:
    """Resolve the appropriate executor class for the given agent instance.

    Args:
        agent (BaseAgent): The agent instance to find an executor for.

    Returns:
        type[Any]: The appropriate executor class for the agent.
    """
    for cls in agent.__class__.__mro__:
        executor_path = AGENT_EXECUTOR_MAPPING.get(cls.__name__)
        if executor_path:
            return _load_executor_class(executor_path)
    raise KeyError(f"No A2A executor registered for agent class '{agent.__class__.__name__}'")


DEFAULT_RETRY_CONFIG = RetryConfig(max_retries=5, timeout=240.0)

LM_EXCLUDE_FIELDS = {
    "lm_base_url",
    "lm_api_key",
    "lm_name",
    "lm_provider",
    "lm_hyperparameters",
    "lm_retry_config",
    "lm_credentials",
}

CUSTOM_PROVIDERS = {
    "openai-compatible/": ModelProvider.OPENAI_COMPATIBLE,
    "azure-openai/": ModelProvider.AZURE_OPENAI,
}

OUTPUT_ANALYTICS_KEY = "output_analytics"


class BaseAgent(AgentInterface):
    """Base class for agents, providing common A2A client method implementations.

    Concrete agent implementations (e.g., LangGraphAgent, GoogleADKAgent)
    should inherit from this class if they need to utilize the shared A2A
    client functionalities.

    This class now supports flexible model handling:
    - model: Optional[Any] - can be an lm_invoker, string/ModelId, LangChain BaseChatModel, or other types
    - Automatically sets self.lm_invoker if an lm_invoker is provided or can be built
    - Stores the original model in self.model for subclass use
    - Enhanced credential support with automatic type detection
    """

    def __init__(  # noqa: PLR0913
        self,
        name: str,
        instruction: str,
        description: str | None = None,
        model: Any | None = None,
        tools: list[Any] | None = None,
        config: BaseAgentConfig | dict[str, Any] | None = None,
        tool_configs: dict[str, Any] | None = None,
        **kwargs: Any,
    ):
        """Initializes the BaseAgent.

        Args:
            name: The name of the agent.
            instruction: The core directive or system prompt for the agent.
            description: Human-readable description. Defaults to instruction if not provided.
            model: The model to use. Can be:
                - BaseLMInvoker instance (will be set as self.lm_invoker)
                - String or ModelId (will build an lm_invoker)
                - LangChain BaseChatModel (will be stored in self.model)
                - Any other type (will be stored in self.model)
            tools: List of tools available to the agent.
            config: Additional configuration for the agent. Can be a BaseAgentConfig instance or dict.
            tool_configs: Default tool configurations applied to all tool calls from this agent.
            **kwargs: Additional keyword arguments for AgentInterface.
        """
        # Convert config to BaseAgentConfig if it's a dict (backward compatibility)
        processed_config = self._process_config(config, tools)

        # Process model parameter to set up lm_invoker and model attributes
        processed_lm_invoker, processed_model = self._process_model_parameter(
            name, model, tools or [], processed_config
        )

        # Pass the lm_invoker to the parent class
        super().__init__(
            name=name,
            instruction=instruction,
            description=description,
            lm_invoker=processed_lm_invoker,
            config=processed_config,
            **kwargs,
        )

        # Store processed model and other attributes
        self.model = processed_model
        self.tools = tools or []
        # Private MCP configuration to prevent tampering and maintain sync
        self._mcp_config: dict[str, dict[str, Any]] = {}
        self.tool_configs = tool_configs or {}

        self._mcp_tools_initialized: bool = False
        self.mcp_client: BaseMCPClient | None = None
        self._mcp_init_lock: asyncio.Lock = asyncio.Lock()

        self.name_preprocessor = self.get_name_preprocessor()

    def get_name_preprocessor(self) -> NamePreprocessor:
        """Get the name preprocessor based on the provider.

        This will be used to correct the agent name and tool name. (mostly tool name)

        Returns:
            NamePreprocessor: The name preprocessor for the model.
        """
        return NamePreprocessor(self.model_provider)

    @property
    def model_provider(self) -> str:
        """Get the provider of the model with simplified logic.

        Returns:
            str: The provider of the model.
        """
        if hasattr(self, "lm_invoker") and self.lm_invoker is not None:
            return self.lm_invoker.model_provider

        if hasattr(self, "model") and self.model is not None:
            return self._detect_provider_from_model(self.model)

        return "unknown"

    def _detect_provider_from_model(self, model: Any) -> str:
        """Detect provider from model object.

        Args:
            model: The model object.

        Returns:
            str: The provider of the model.
        """
        if isinstance(model, str):
            return self._detect_provider_from_string(model)

        if hasattr(model, "__class__"):
            return self._detect_provider_from_class(model.__class__.__name__)

        return "unknown"

    def _detect_provider_from_string(self, model_str: str) -> str:
        """Detect provider from model string.

        Args:
            model_str: The model string.

        Returns:
            str: The provider of the model.
        """
        model_lower = model_str.lower()

        if model_lower.startswith(("gemini", "google")):
            return "google"

        return model_str.split("/")[0] if "/" in model_str else model_str

    def _detect_provider_from_class(self, class_name: str) -> str:
        """Detect provider from class name.

        Args:
            class_name: The class name.

        Returns:
            str: The provider of the model.
        """
        class_name_lower = class_name.lower()

        provider_mappings = {"openai": "openai", "google": "google", "vertex": "google", "anthropic": "anthropic"}

        for keyword, provider in provider_mappings.items():
            if keyword in class_name_lower:
                return provider

        return "unknown"

    def _process_config(
        self, config: BaseAgentConfig | dict[str, Any] | None, tools: list[Any] | None = None
    ) -> BaseAgentConfig | None:
        """Process config parameter to ensure it's a BaseAgentConfig instance.

        Args:
            config: Configuration parameter that can be dict, BaseAgentConfig, or None.
            tools: List of tools to include in config if not already present.

        Returns:
            BaseAgentConfig instance or None.
        """
        if config is None:
            if tools:
                return AgentConfig(tools=tools)
            return None

        if isinstance(config, BaseAgentConfig):
            if tools and not config.tools:
                config.tools = tools
            return config

        if isinstance(config, dict):
            config_dict = config.copy()

            if tools and "tools" not in config_dict:
                config_dict["tools"] = tools

            if "lm_hyperparameters" in config_dict and "default_hyperparameters" not in config_dict:
                config_dict["default_hyperparameters"] = config_dict.pop("lm_hyperparameters")

            return AgentConfig(**config_dict)

        raise TypeError(f"Config must be BaseAgentConfig, dict, or None, got {type(config)}")

    def _extract_credentials_from_config(
        self, config: BaseAgentConfig | None
    ) -> tuple[CredentialType, str | dict[str, Any] | None]:
        """Extract and auto-detect credentials from config with ultra-simple logic.

        This method supports multiple credential formats with automatic type detection:
        - New lm_credentials field: Auto-detects type based on content
        - Legacy lm_api_key field: For backward compatibility

        Auto-detection logic:
        - Dict: Passed through as-is (CredentialType.DICT)
        - String + file exists: Treated as file path (CredentialType.FILE)
        - String + file doesn't exist: Treated as API key (CredentialType.API_KEY)

        Args:
            config: Configuration object.

        Returns:
            Tuple containing:
                - credential_type: CredentialType enum value
                - credentials: The extracted credentials or None if not found
        """
        if not config:
            return CredentialType.API_KEY, None

        if hasattr(config, "lm_credentials") and config.lm_credentials is not None:
            detected_type, formatted_creds = self._auto_detect_credential_type(config.lm_credentials)
            return detected_type, formatted_creds

        if hasattr(config, "lm_api_key") and config.lm_api_key:
            warn(
                (
                    "The lm_api_key is deprecated as of version 0.5.0. "
                    "Use lm_credentials instead which supports auto-detection of API keys, "
                    "file paths, and dictionary credentials."
                ),
                DeprecationWarning,
                stacklevel=2,
            )
            return CredentialType.API_KEY, config.lm_api_key

        return CredentialType.API_KEY, None

    def _auto_detect_credential_type(self, credentials: Any) -> tuple[CredentialType, Any]:
        """Automatically detect credential type using simple file existence rules.

        This method uses ultra-simple detection logic:
        1. If credentials is dict -> CredentialType.DICT (Bedrock, LangChain credentials)
        2. If credentials is string and exists on disk -> CredentialType.FILE
        3. Everything else -> CredentialType.API_KEY (simple fallback)

        Args:
            credentials: Raw credentials from config.

        Returns:
            Tuple containing:
                - credential_type: CredentialType enum value
                - formatted_credentials: The credentials in the detected format
        """
        if isinstance(credentials, dict):
            return CredentialType.DICT, credentials

        if isinstance(credentials, str):
            if not credentials.strip():
                return CredentialType.API_KEY, credentials

            try:
                path = Path(credentials)
                if path.exists():
                    return CredentialType.FILE, credentials
            except (ValueError, OSError):
                pass

            return CredentialType.API_KEY, credentials

        return CredentialType.API_KEY, str(credentials)

    @property
    def mcp_config(self) -> dict[str, dict[str, Any]]:
        """Read-only view of MCP configuration.

        Returns a copy to prevent direct mutation; use add_mcp_server() for changes.
        """
        return self._mcp_config.copy()

    @mcp_config.setter
    def mcp_config(self, value: dict[str, dict[str, Any]]) -> None:
        """Set MCP configuration and maintain synchronization.

        Automatically resets initialization flag and recreates client to ensure consistency.
        Prefer using add_mcp_server() for proper validation.

        Args:
            value (dict[str, dict[str, Any]]): The MCP configuration to set.
        """
        if not isinstance(value, dict):
            raise ValueError("mcp_config must be a dict[str, dict[str, Any]]")
        self._mcp_config = value.copy()
        # Reset flag and recreate client object to maintain sync. This is lightweight
        # (no connections created) and safe to perform synchronously. Actual session
        # initialization remains lazy in the event loop via _ensure_mcp_tools_initialized().
        self._mcp_tools_initialized = False
        if self._mcp_config:
            self._initialize_mcp_client()
        else:
            # Clear client for empty config
            self.mcp_client = None

    def _get_credentials(self, model: str | ModelId, config: BaseAgentConfig | None) -> str | dict[str, Any] | None:
        """Get credentials for the model with enhanced type support.

        This method now supports multiple credential formats through the new
        _extract_credentials_from_config method while maintaining backward compatibility.

        Args:
            model: Model identifier.
            config: Configuration object.

        Returns:
            Credentials if found, None otherwise. Can be:
            - str: For API keys or file paths
            - dict: For structured credentials (Bedrock, LangChain)
        """
        credentials = None

        if config:
            _, credentials = self._extract_credentials_from_config(config)

        if not credentials:
            credentials = CredentialsManager.get_credentials(model)

        return credentials

    def _extract_retry_config(self, config: BaseAgentConfig | None, use_default: bool = True) -> RetryConfig | None:
        """Extract and process retry config from agent config.

        Args:
            config: Configuration object.
            use_default: If True, return a default RetryConfig when none is found.

        Returns:
            RetryConfig instance if found, default RetryConfig if use_default=True and none found, None otherwise.
        """
        if config and isinstance(config, AgentConfig) and config.lm_retry_config:
            if isinstance(config.lm_retry_config, dict):
                return RetryConfig(**config.lm_retry_config)
            return config.lm_retry_config

        if use_default:
            return DEFAULT_RETRY_CONFIG

        return None

    def _update_config_with_tools(
        self, tools: list[Any], config: BaseAgentConfig | None = None
    ) -> dict[str, Any] | None:
        """Update config with tools if not already present and convert to dict for lm_invoker.

        Args:
            tools: List of tools.
            config: Configuration object.

        Returns:
            Configuration dictionary for lm_invoker.
        """
        if config is None:
            config_dict = {"tools": tools} if tools else {}
            config_dict["retry_config"] = self._extract_retry_config(config)
            return config_dict

        # Convert BaseAgentConfig to dict, excluding LM-specific fields
        config_dict = config.model_dump(
            exclude_none=True,
            exclude=LM_EXCLUDE_FIELDS,
        )
        if isinstance(config, AgentConfig) and config.lm_hyperparameters:
            config_dict["default_hyperparameters"] = config.lm_hyperparameters

        config_dict["retry_config"] = self._extract_retry_config(config)

        if tools:
            config_dict["tools"] = tools

        return config_dict if config_dict else None

    def _finalize_lm_invoker_config(self, tools: list[Any], config: BaseAgentConfig | None) -> dict[str, Any]:
        """Finalize lm_invoker config by adding tools and output analytics.

        Args:
            tools: List of tools.
            config: Configuration object for lm_invoker.

        Returns:
            Configuration dictionary for lm_invoker.
        """
        processed_config = self._update_config_with_tools(tools, config)
        if processed_config is None:
            processed_config = {}

        if OUTPUT_ANALYTICS_KEY not in processed_config:
            processed_config[OUTPUT_ANALYTICS_KEY] = True

        return processed_config

    def _setup_lm_invoker_param(
        self, model: str | ModelId, tools: list[Any], config: BaseAgentConfig | None = None
    ) -> tuple[ModelId | str, str | None, dict[str, Any] | None]:
        """Setup parameter for build_lm_invoker.

        Args:
            model (str | ModelId): The model identifier.
            tools (list[Any]): List of tools.
            config (BaseAgentConfig | None): Configuration object.

        Returns:
            - model_id: ModelId | str
            - credentials: str | None
            - config: dict[str, Any] | None
            as tuple
        """
        model_id: str | ModelId = model
        credentials: str | None = None
        processed_as_custom = False

        if isinstance(model, str):
            for prefix, provider in CUSTOM_PROVIDERS.items():
                if model.startswith(prefix):
                    processed_as_custom = True

                    if not config or not isinstance(config, AgentConfig):
                        raise ValueError(f"AgentConfig is required for model '{model}'")

                    try:
                        model_id = ModelId.from_string(model)
                    except ValueError as e:
                        base_url = config.lm_base_url
                        if not base_url:
                            raise ValueError(f"lm_base_url in AgentConfig is required for model '{model}'") from e

                        model_name = model.removeprefix(prefix)
                        model_id = ModelId(provider=provider, name=model_name, path=base_url)

                    # Extract credentials using new enhanced method
                    _, credentials = self._extract_credentials_from_config(config)
                    break

        if not processed_as_custom or credentials is None:
            credentials = self._get_credentials(model_id, config)

        processed_config = self._finalize_lm_invoker_config(tools, config)
        return model_id, credentials, processed_config

    def _process_model_parameter(
        self, agent_name: str, model: Any | None, tools: list[Any], config: BaseAgentConfig | None = None
    ) -> tuple[Any | None, Any | None]:
        """Process the model parameter and determine lm_invoker and model attributes.

        Args:
            agent_name: The name of the agent (for logging).
            model: The model parameter from initialization.
            tools: List of tools for lm_invoker configuration.
            config: Configuration object.

        Returns:
            Tuple of (lm_invoker, processed_model) where:
            - lm_invoker: Built LM Invoker if model is string/ModelId or existing BaseLMInvoker, None otherwise
            - processed_model: LangChain model if it's a BaseChatModel,
                original model for other types, None if lm_invoker was created
                or if model is None
        """
        # If model is already an lm_invoker instance
        if BaseLMInvoker and isinstance(model, BaseLMInvoker):
            logger.debug(f"Agent '{agent_name}': Using provided LM Invoker: {model.__class__.__name__}")
            return model, None

        # Check if model is a string or ModelId - build lm_invoker
        if isinstance(model, str) or (ModelId and isinstance(model, ModelId)):
            if not build_lm_invoker:
                logger.warning(
                    f"Agent '{agent_name}': gllm-inference not available, cannot build LM Invoker from {model}"
                )
                return None, model

            logger.info(f"Agent '{agent_name}': Building LM Invoker from model identifier: {model}")
            try:
                model_id, credentials, preprocessed_config = self._setup_lm_invoker_param(model, tools, config)

                lm_invoker = build_lm_invoker(
                    model_id=model_id,
                    credentials=credentials,
                    config=preprocessed_config,
                )
                return lm_invoker, None
            except Exception as e:
                logger.error(f"Agent '{agent_name}': Failed to build LM Invoker from {model}: {e}")
                raise RuntimeError(f"Failed to build LM Invoker from model '{model}': {e}") from e

        # If it's a LangChain model, use it directly
        elif BaseChatModel and hasattr(model, "__class__") and issubclass(model.__class__, BaseChatModel):
            logger.debug(f"Agent '{agent_name}': Using provided LangChain model: {model.__class__.__name__}")
            return None, model

        # If model is None, that's acceptable for some use cases
        elif model is None:
            logger.debug(f"Agent '{agent_name}': No model provided")
            return None, None

        # For any other type, store as model (e.g., Google ADK agent instance)
        else:
            logger.debug(f"Agent '{agent_name}': Using provided model of type: {type(model)}")
            return None, model

    def to_a2a(self, agent_card: AgentCard, **kwargs: Any) -> Starlette:
        """Converts the agent to an A2A-compatible ASGI application.

        This implementation provides a base setup for A2A server components.
        Subclasses can override this method if they need custom executor
        or task store implementations.

        Args:
            agent_card: The agent card to use for the A2A application.
            **kwargs: Additional keyword arguments for ASGI application configuration.

        Returns:
            A Starlette ASGI application that can be used with any ASGI server.
        """
        # Use provided task store or create default in-memory store
        task_store = kwargs.get("task_store", InMemoryTaskStore())

        # Create default request handler if not provided
        try:
            executor_cls = _get_executor_class_for_agent(self)
        except KeyError as exc:
            raise ValueError(f"No A2A executor registered for agent type '{self.__class__.__name__}'.") from exc

        agent_executor = executor_cls(self)
        request_handler = kwargs.get(
            "request_handler",
            DefaultRequestHandler(
                agent_executor=agent_executor,
                task_store=task_store,
            ),
        )

        # Create A2A application
        a2a_app = A2AStarletteApplication(agent_card=agent_card, http_handler=request_handler)

        # Get base routes from A2A app
        routes = a2a_app.routes()

        # Add any additional routes if provided
        if "routes" in kwargs:
            routes.extend(kwargs["routes"])

        # Create and return Starlette application
        return Starlette(routes=routes)

    @classmethod
    def discover_agents(cls, a2a_config: A2AClientConfig, **kwargs: Any) -> list[AgentCard]:
        """Discover agents from the URLs specified in a2a_config.discovery_urls.

        This concrete implementation fetches and parses .well-known/agent.json
        from each discovery URL to build a list of available agents.

        Args:
            a2a_config: Configuration containing discovery URLs and other A2A settings.
            **kwargs: Additional keyword arguments (unused in this implementation).

        Returns:
            A list of AgentCard objects representing discovered agents.
        """
        discovered_cards: list[AgentCard] = []

        if not a2a_config or not a2a_config.discovery_urls:
            logger.debug("No discovery URLs configured")
            return discovered_cards

        httpx_client_options = {}
        if a2a_config.httpx_client_options:
            httpx_client_options = a2a_config.httpx_client_options.model_dump(exclude_none=True)

        with httpx.Client(**httpx_client_options) as client:
            for base_url in a2a_config.discovery_urls:
                try:
                    agent_json_url = f"{base_url.rstrip('/')}/.well-known/agent.json"

                    response = client.get(agent_json_url)
                    response.raise_for_status()

                    try:
                        agent_card = AgentCard.model_validate(response.json())
                        discovered_cards.append(agent_card)
                        logger.info(f"Successfully discovered agent '{agent_card.name}' at {base_url}")
                    except Exception as parse_error:
                        logger.error(f"Error parsing agent card from {agent_json_url}: {parse_error}")
                        continue

                except Exception as e:
                    logger.error(f"Unexpected error discovering agents from {base_url}: {e}")
                    continue

        agent_list = "\n".join([f"{i + 1}. {agent.name}" for i, agent in enumerate(discovered_cards)])
        logger.info(f"Discovered agents ({len(discovered_cards)} Agents): \n{agent_list}")
        return discovered_cards

    def send_to_agent(
        self,
        agent_card: AgentCard,
        message: str | dict[str, Any],
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Synchronously sends a message to another agent using the A2A protocol.

        This method is a synchronous wrapper around asend_to_agent. It handles the creation
        of an event loop if one doesn't exist, and manages the asynchronous call internally.

        Args:
            agent_card: The AgentCard instance containing the target agent's details including
                URL, authentication requirements, and capabilities.
            message: The message to send to the agent. Can be either a string for simple text
                messages or a dictionary for structured data.
            **kwargs: Additional keyword arguments passed to asend_to_agent.

        Returns:
            A dictionary containing the response details:
                - status (str): 'success' or 'error'
                - content (str): Extracted text content from the response
                - task_id (str, optional): ID of the created/updated task
                - task_state (str, optional): Current state of the task
                - raw_response (str): Complete JSON response from the A2A client
                - error_type (str, optional): Type of error if status is 'error'
                - message (str, optional): Error message if status is 'error'

        Raises:
            RuntimeError: If called from within an existing event loop or if asend_to_agent
                encounters an unhandled exception.
        """
        try:
            return A2AConnector.send_to_agent(agent_card, message, **kwargs)
        except RuntimeError as e:
            raise RuntimeError(f"Agent '{self.name}': Error in sync 'send_to_agent'. Original error: {e}") from e

    async def asend_to_agent(
        self,
        agent_card: AgentCard,
        message: str | dict[str, Any],
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Asynchronously sends a message to another agent using the A2A protocol.

        This method handles the core A2A communication logic, creating and sending properly
        formatted A2A messages and processing the responses.

        Args:
            agent_card: The AgentCard instance containing the target agent's details including
                URL, authentication requirements, and capabilities.
            message: The message to send to the agent. Can be either a string for simple text
                messages or a dictionary for structured data.
            **kwargs: Additional keyword arguments.

        Returns:
            A dictionary containing the response details:
                - status (str): 'success' or 'error'
                - content (str): Extracted text content from the response
                - task_id (str, optional): ID of the created/updated task
                - task_state (str, optional): Current state of the task
                - raw_response (str): Complete JSON response from the A2A client
                - error_type (str, optional): Type of error if status is 'error'
                - message (str, optional): Error message if status is 'error'

        Raises:
            httpx.HTTPError: If there's an HTTP-related error during the request.
            Exception: For any other unexpected errors during message sending or processing.
        """
        return await A2AConnector.asend_to_agent(agent_card, message, **kwargs)

    async def astream_to_agent(
        self,
        agent_card: AgentCard,
        message: str | dict[str, Any],
        **kwargs: Any,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Asynchronously sends a streaming message to another agent using the A2A protocol.

        This method supports streaming responses from the target agent, yielding chunks of
        the response as they become available. It handles various types of streaming events
        including task status updates, artifact updates, and message parts.

        Args:
            agent_card: The AgentCard instance containing the target agent's details including
                URL, authentication requirements, and capabilities.
            message: The message to send to the agent. Can be either a string for simple text
                messages or a dictionary for structured data.
            **kwargs: Additional keyword arguments.

        Yields:
            Dictionaries containing streaming response chunks:
                For successful chunks:
                    - status (str): 'success'
                    - content (str): Extracted text content from the chunk
                    - task_id (str): ID of the associated task
                    - task_state (str): Current state of the task
                    - final (bool): Whether this is the final chunk
                    - artifact_name (str, optional): Name of the artifact if chunk is an artifact update
                For error chunks:
                    - status (str): 'error'
                    - error_type (str): Type of error encountered
                    - message (str): Error description

        Raises:
            httpx.HTTPError: If there's an HTTP-related error during the streaming request.
            Exception: For any other unexpected errors during message streaming or processing.
        """
        # Default to the richer A2A event payload so integrations (e.g. HITL streaming) receive
        async for chunk in A2AConnector.astream_to_agent(agent_card, message, **kwargs):
            yield chunk

    @staticmethod
    def format_agent_description(agent_card: AgentCard) -> str:
        """Format the description of an agent card including skills information.

        Args:
            agent_card (AgentCard): The agent card to format.

        Returns:
            str: The formatted description including skills.
        """
        # Start with the base description
        formatted_description = agent_card.description or ""

        if agent_card.skills:
            formatted_description += "\n\nSkills:"
            for skill in agent_card.skills:
                formatted_description += f"\n• {skill.name}: {skill.description}"

                if skill.tags:
                    tags_str = ", ".join(skill.tags)
                    formatted_description += f" (Tags: {tags_str})"

                if skill.examples:
                    formatted_description += "\n  Examples:"
                    for example in skill.examples:
                        formatted_description += f"\n    - {example}"

        return formatted_description

    def add_mcp_server(self, mcp_config: dict[str, dict[str, Any]]) -> None:
        """Adds MCP servers to the agent.

        Args:
            mcp_config: A dictionary containing MCP server configurations.

        Raises:
            ValueError: If the MCP configuration is empty or None.
            KeyError: If a server with the same name already exists in the MCP configuration.
        """
        if not mcp_config:
            raise ValueError("MCP configuration must not be empty or None")

        for server_name, config in mcp_config.items():
            if server_name in self.mcp_config:
                raise KeyError(f"Server '{server_name}' already exists in MCP configuration")
            if not isinstance(config, dict):
                raise ValueError(f"Configuration for server '{server_name}' must be a dictionary")
            if not config:
                raise ValueError(f"Configuration for server '{server_name}' must not be empty")

            # Validate that either URL or command is present
            required_keys = ["url"] if "url" in config else ["command"]
            if not any(key in config for key in required_keys):
                raise ValueError(
                    f"Server '{server_name}' missing required configuration: must have either 'url' or 'command'"
                )

        self._mcp_config.update(mcp_config)
        # Initialize/recreate MCP client object (lightweight, no sessions yet)
        # This satisfies existing unit tests and keeps lazy async session init intact.
        self._initialize_mcp_client()
        # Mark that we need to initialize MCP tools (lazy initialization)
        self._mcp_tools_initialized = False

    def _initialize_mcp_client(self) -> None:
        """Initialize/recreate MCP client with current config.

        To be implemented by child agents as each agent type has its own MCP client.
        For agents that don't support MCP (e.g., LangflowAgent), this can be a no-op.
        """
        # Default implementation is no-op for agents that don't support MCP
        pass

    def _set_mcp_client_safely(self, new_client: BaseMCPClient | None) -> None:
        """Replace current MCP client with cleanup of the previous instance.

        This helper ensures we don't leak persistent sessions when recreating the client.
        It attempts asynchronous cleanup when an event loop is running, otherwise performs
        a synchronous cleanup using asyncio.run.

        Args:
            new_client (BaseMCPClient | None): The new MCP client to set, or None to clear the current client.
        """
        prev_client = self.mcp_client
        self.mcp_client = new_client
        if prev_client is not None and prev_client is not new_client:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(prev_client.cleanup())
            except RuntimeError:
                try:
                    asyncio.run(prev_client.cleanup())
                except Exception:
                    # Best-effort cleanup; ignore failures
                    pass

    async def _ensure_mcp_tools_initialized(self) -> None:
        """Ensure MCP tools are initialized lazily (one-time operation).

        This method ensures MCP tools are initialized only once during the first run,
        avoiding event loop issues by doing initialization in the correct event loop.
        """
        if self._mcp_tools_initialized:
            return

        # Prevent concurrent initialization across simultaneous runs
        async with self._mcp_init_lock:
            if self._mcp_tools_initialized:
                return

            await self._handle_mcp_client_initialization()

            # If we have a client at this point, proceed with tool registration
            if self.mcp_client is not None:
                await self._perform_mcp_tool_registration()

    async def _handle_mcp_client_initialization(self) -> None:
        """Handle MCP client initialization based on current state.

        Sets the initialization flag appropriately for different scenarios.
        """
        if self.mcp_client is not None:
            return  # Client already exists

        if not self._mcp_config:
            # No config at all - skip and mark as initialized to avoid repeated logs
            logger.debug(f"Agent '{self.name}': MCP client not configured; skipping MCP tool registration")
            self._mcp_tools_initialized = True
            return

        # Config exists but no client - try to initialize
        self._initialize_mcp_client()
        if self.mcp_client is None:
            # Still no client after init - agent type doesn't support MCP
            logger.warning(f"Agent '{self.name}': MCP config present but agent type doesn't support MCP")

    async def _perform_mcp_tool_registration(self) -> None:
        """Perform the actual MCP tool registration.

        Raises:
            RuntimeError: If tool registration fails
        """
        try:
            await self._register_mcp_tools()
            self._mcp_tools_initialized = True
        except Exception as e:
            logger.error(f"Agent '{self.name}': Failed to initialize MCP tools: {e}", exc_info=True)
            raise RuntimeError(f"Agent '{self.name}': MCP tool initialization failed: {e}") from e

    async def _register_mcp_tools(self) -> None:
        """Register MCP tools with the agent.

        To be implemented by child agents as each agent type has its own way
        of registering tools. For agents that don't support MCP, this can be a no-op.
        """
        # Default implementation is no-op for agents that don't support MCP
        pass
