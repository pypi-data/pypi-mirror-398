from browser_use.llm import ChatOpenAI
from typing import Any

__all__ = ['build_browser_use_llm', 'configure_browser_use_environment', 'model_disallows_tunable_params', 'supports_frequency_penalty', 'supports_temperature_override']

def model_disallows_tunable_params(model: Any) -> bool:
    """Return True if the provider forbids temperature/frequency overrides for the model.

    Args:
        model: The model name or identifier to check.

    Returns:
        bool: True if the model disallows tunable parameters, False otherwise.
    """
def supports_temperature_override(model: Any) -> bool:
    """Return True when the given model supports setting a custom temperature.

    Args:
        model: The model name or identifier to check.

    Returns:
        bool: True if the model supports temperature override, False otherwise.
    """
def supports_frequency_penalty(model: Any) -> bool:
    """Return True when the given model supports custom frequency penalties.

    Args:
        model: The model name or identifier to check.

    Returns:
        bool: True if the model supports frequency penalty override, False otherwise.
    """
def build_browser_use_llm(*, model: Any, reasoning_effort: Any, temperature: float | None, api_key: str, base_url: str | None = None) -> ChatOpenAI:
    """Construct a ChatOpenAI instance with browser-use specific safeguards.

    Args:
        model: The model name or identifier to use.
        reasoning_effort: The reasoning effort level for the model.
        temperature: Optional temperature setting for the model. Can be None.
        api_key: The API key for authentication.
        base_url: The base URL for the model.

    Returns:
        ChatOpenAI: The configured ChatOpenAI instance.
    """
def configure_browser_use_environment(enable_cloud_sync: bool, logging_level: str) -> None:
    """Ensure Browser Use environment flags are aligned with tool configuration.

    Args:
        enable_cloud_sync: Whether to enable cloud synchronization for browser sessions.
        logging_level: The desired logging level for browser use operations.
    """
