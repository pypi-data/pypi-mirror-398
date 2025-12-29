"""Schema definitions for agent configuration types."""

from enum import StrEnum
from typing import Any

from a2a.types import AgentCard
from gllm_core.utils.retry import RetryConfig
from pydantic import BaseModel, Field

try:
    # Pydantic v2 preferred config
    from pydantic import ConfigDict  # type: ignore
except Exception:  # pragma: no cover
    ConfigDict = None  # type: ignore

__all__ = [
    "CredentialType",
    "StreamMode",
    "HttpxClientOptions",
    "A2AClientConfig",
    "BaseAgentConfig",
    "AgentConfig",
    "LangflowAgentConfig",
]


class CredentialType(StrEnum):
    """Credential type enumeration for type safety and better developer experience."""

    API_KEY = "api_key"
    FILE = "file"
    DICT = "dict"


class StreamMode(StrEnum):
    """LangGraph stream modes for astream operations."""

    VALUES = "values"
    CUSTOM = "custom"
    MESSAGES = "messages"


class HttpxClientOptions(BaseModel):
    """Options for the HTTP client."""

    timeout: float = 360.0
    trust_env: bool = False
    follow_redirects: bool = True

    if ConfigDict is not None:
        # Pydantic v2 style config
        model_config = ConfigDict(extra="allow")  # type: ignore[assignment]
    else:  # pragma: no cover

        class Config:  # type: ignore[no-redef]
            """Pydantic v1 fallback config for HttpxClientOptions."""

            extra = "allow"


class A2AClientConfig(BaseModel):
    """Configuration for A2A client."""

    discovery_urls: list[str] | None = None
    known_agents: dict[str, AgentCard] = Field(default_factory=dict)
    httpx_client_options: HttpxClientOptions | None = HttpxClientOptions()


class BaseAgentConfig(BaseModel):
    """Base configuration for agent implementations."""

    tools: list[Any] | None = None
    default_hyperparameters: dict[str, Any] | None = None

    if ConfigDict is not None:
        model_config = ConfigDict(extra="allow")  # type: ignore[assignment]
    else:  # pragma: no cover

        class Config:  # type: ignore[no-redef]
            """Pydantic v1 fallback config for BaseAgentConfig."""

            extra = "allow"


class AgentConfig(BaseAgentConfig):
    """Configuration for agent implementations with language model settings."""

    lm_name: str | None = None
    lm_hyperparameters: dict[str, Any] | None = None
    lm_provider: str | None = None
    lm_base_url: str | None = None
    lm_api_key: str | None = None
    lm_credentials: str | dict[str, Any] | None = None
    lm_retry_config: RetryConfig | None = None


class LangflowAgentConfig(BaseAgentConfig):
    """Configuration for Langflow agent implementations."""

    flow_id: str
    base_url: str | None = None
    api_key: str | None = None

    if ConfigDict is not None:
        model_config = ConfigDict(extra="allow")  # type: ignore[assignment]
    else:  # pragma: no cover

        class Config:  # type: ignore[no-redef]
            """Pydantic v1 fallback config for LangflowAgentConfig."""

            extra = "allow"
