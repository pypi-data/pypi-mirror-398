"""Helpers for configuring browser-use LLM instances and environment flags.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

import os
from typing import Any

from browser_use.llm import ChatOpenAI
from browser_use.logging_config import setup_logging


def model_disallows_tunable_params(model: Any) -> bool:
    """Return True if the provider forbids temperature/frequency overrides for the model.

    Args:
        model: The model name or identifier to check.

    Returns:
        bool: True if the model disallows tunable parameters, False otherwise.
    """
    model_name = str(model).lower()

    if model_name.startswith("gpt-5"):
        return True

    short_name = model_name.split("-", 1)[0]
    return short_name.startswith("o") and short_name[1:].isdigit()


def supports_temperature_override(model: Any) -> bool:
    """Return True when the given model supports setting a custom temperature.

    Args:
        model: The model name or identifier to check.

    Returns:
        bool: True if the model supports temperature override, False otherwise.
    """
    return not model_disallows_tunable_params(model)


def supports_frequency_penalty(model: Any) -> bool:
    """Return True when the given model supports custom frequency penalties.

    Args:
        model: The model name or identifier to check.

    Returns:
        bool: True if the model supports frequency penalty override, False otherwise.
    """
    return not model_disallows_tunable_params(model)


def build_browser_use_llm(
    *,
    model: Any,
    reasoning_effort: Any,
    temperature: float | None,
    api_key: str,
    base_url: str | None = None,
) -> ChatOpenAI:
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
    llm_kwargs: dict[str, Any] = {
        "model": model,
        "reasoning_effort": reasoning_effort,
        "api_key": api_key,
        "base_url": base_url,
    }

    if temperature is not None and supports_temperature_override(model):
        llm_kwargs["temperature"] = temperature
    else:
        llm_kwargs["temperature"] = None

    if not supports_frequency_penalty(model):
        llm_kwargs["frequency_penalty"] = None

    return ChatOpenAI(**llm_kwargs)


def configure_browser_use_environment(enable_cloud_sync: bool, logging_level: str) -> None:
    """Ensure Browser Use environment flags are aligned with tool configuration.

    Args:
        enable_cloud_sync: Whether to enable cloud synchronization for browser sessions.
        logging_level: The desired logging level for browser use operations.
    """
    desired_sync = "true" if enable_cloud_sync else "false"
    if os.environ.get("BROWSER_USE_CLOUD_SYNC") != desired_sync:
        os.environ["BROWSER_USE_CLOUD_SYNC"] = desired_sync

    desired_level = logging_level.lower()
    current_level = os.environ.get("BROWSER_USE_LOGGING_LEVEL")
    if not current_level or current_level.lower() != desired_level:
        os.environ["BROWSER_USE_LOGGING_LEVEL"] = desired_level
        setup_logging(log_level=desired_level, force_setup=True)


__all__ = [
    "build_browser_use_llm",
    "configure_browser_use_environment",
    "model_disallows_tunable_params",
    "supports_frequency_penalty",
    "supports_temperature_override",
]
