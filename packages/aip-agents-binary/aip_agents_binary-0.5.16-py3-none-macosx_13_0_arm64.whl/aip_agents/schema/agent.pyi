from _typeshed import Incomplete
from a2a.types import AgentCard
from enum import StrEnum
from gllm_core.utils.retry import RetryConfig
from pydantic import BaseModel
from typing import Any

__all__ = ['CredentialType', 'StreamMode', 'HttpxClientOptions', 'A2AClientConfig', 'BaseAgentConfig', 'AgentConfig', 'LangflowAgentConfig']

class CredentialType(StrEnum):
    """Credential type enumeration for type safety and better developer experience."""
    API_KEY: str
    FILE: str
    DICT: str

class StreamMode(StrEnum):
    """LangGraph stream modes for astream operations."""
    VALUES: str
    CUSTOM: str
    MESSAGES: str

class HttpxClientOptions(BaseModel):
    """Options for the HTTP client."""
    timeout: float
    trust_env: bool
    follow_redirects: bool
    model_config: Incomplete
    class Config:
        """Pydantic v1 fallback config for HttpxClientOptions."""
        extra: str

class A2AClientConfig(BaseModel):
    """Configuration for A2A client."""
    discovery_urls: list[str] | None
    known_agents: dict[str, AgentCard]
    httpx_client_options: HttpxClientOptions | None

class BaseAgentConfig(BaseModel):
    """Base configuration for agent implementations."""
    tools: list[Any] | None
    default_hyperparameters: dict[str, Any] | None
    model_config: Incomplete
    class Config:
        """Pydantic v1 fallback config for BaseAgentConfig."""
        extra: str

class AgentConfig(BaseAgentConfig):
    """Configuration for agent implementations with language model settings."""
    lm_name: str | None
    lm_hyperparameters: dict[str, Any] | None
    lm_provider: str | None
    lm_base_url: str | None
    lm_api_key: str | None
    lm_credentials: str | dict[str, Any] | None
    lm_retry_config: RetryConfig | None

class LangflowAgentConfig(BaseAgentConfig):
    """Configuration for Langflow agent implementations."""
    flow_id: str
    base_url: str | None
    api_key: str | None
    model_config: Incomplete
    class Config:
        """Pydantic v1 fallback config for LangflowAgentConfig."""
        extra: str
