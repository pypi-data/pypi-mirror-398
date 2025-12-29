"""Manages credentials for different model providers."""

from __future__ import annotations

import os

from aip_agents.schema.model_id import ModelId, ModelProvider
from aip_agents.utils.logger import get_logger

logger = get_logger(__name__)


class CredentialsManager:
    """Manages credentials for different model providers."""

    _ENV_VAR_MAP: dict[ModelProvider, str] = {
        ModelProvider.OPENAI: "OPENAI_API_KEY",
        ModelProvider.ANTHROPIC: "ANTHROPIC_API_KEY",
        ModelProvider.AZURE_OPENAI: "AZURE_OPENAI_API_KEY",
        ModelProvider.OPENAI_COMPATIBLE: "OPENAI_COMPATIBLE_API_KEY",
    }

    _ENV_VAR_MAP_OPENAI_COMPATIBLE: dict[str, str] = {
        "deepseek": "DEEPSEEK_API_KEY",
        "groq": "GROQ_DEEPSEEK_API_KEY",
        "deepinfra": "DEEPINFRA_API_KEY",
        "together": "TOGETHER_API_KEY",
    }

    @classmethod
    def get_credentials(cls, model: str | ModelId, explicit_credentials: str | None = None) -> str | None:
        """Get credentials for a given model.

        Args:
            model: The model identifier (string or ModelId object).
            explicit_credentials: Optional explicit credentials to use instead of environment lookup.

        Returns:
            The credentials string if found, None otherwise.
        """
        if explicit_credentials:
            logger.debug("Using explicitly provided credentials.")
            return explicit_credentials

        provider, path = cls._extract_provider(model)
        if provider is None:
            return None

        return cls._get_env_credentials(provider, path or "")

    @staticmethod
    def _extract_provider(model: str | ModelId) -> tuple[ModelProvider | None, str | None]:
        """Parse a model string or ModelId and return the provider metadata.

        Args:
            model: Raw model identifier or parsed ModelId.

        Returns:
            Tuple of provider and remaining model path when available, otherwise (None, None).
        """
        try:
            if isinstance(model, str):
                model_id_obj = ModelId.from_string(model)
                provider = model_id_obj.provider
                path = model_id_obj.path
            elif isinstance(model, ModelId):
                provider = model.provider
                path = model.path
            else:
                logger.warning("Unexpected model type: %s", type(model))
                return None, None

            return provider, path
        except ValueError:
            logger.warning("Could not parse provider from model string: %s", model)
            return None, None

    @classmethod
    def _extract_env_var_name(cls, provider: ModelProvider, path: str | None) -> str | None:
        """Resolve the environment variable name to use for the given provider.

        Args:
            provider: Provider enum extracted from the model id.
            path: Optional model path used to disambiguate OpenAI compatible providers.

        Returns:
            The name of the environment variable to load or None when no mapping exists.
        """
        if provider not in cls._ENV_VAR_MAP:
            logger.info(
                "Provider '%s' identified, but no known environment variable mapping in CredentialsManager.",
                getattr(provider, "value", provider),
            )
            return None

        if provider == ModelProvider.OPENAI_COMPATIBLE and path:
            for key, env_var in cls._ENV_VAR_MAP_OPENAI_COMPATIBLE.items():
                if key in path:
                    return env_var

        return cls._ENV_VAR_MAP[provider]

    @classmethod
    def _get_env_credentials(cls, provider: ModelProvider, path: str | None) -> str | None:
        """Fetch credentials for the provider from the environment.

        Args:
            provider: Provider used to determine the environment variable.
            path: Optional additional path information for provider-specific overrides.

        Returns:
            The credential string from the environment or None if it was not set.
        """
        env_var_name = cls._extract_env_var_name(provider, path)
        if not env_var_name:
            return None

        env_credentials = os.environ.get(env_var_name)
        if env_credentials:
            logger.info(
                "Using credentials for %s from environment variable '%s'.",
                getattr(provider, "value", provider),
                env_var_name,
            )
            return env_credentials

        logger.warning(
            "Environment variable '%s' not found for %s.",
            env_var_name,
            getattr(provider, "value", provider),
        )
        return None
