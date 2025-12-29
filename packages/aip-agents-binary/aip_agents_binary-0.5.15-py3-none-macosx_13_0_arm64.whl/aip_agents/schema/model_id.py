"""Model identifiers and provider definitions for the AI agent platform."""

from __future__ import annotations

from enum import StrEnum


class ModelProvider(StrEnum):
    """Enumeration of supported model providers for the AI agent platform."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE_OPENAI = "azure-openai"
    GOOGLE_GENAI = "google"
    GROQ = "groq"
    TOGETHER_AI = "together"
    DEEPINFRA = "deepinfra"
    DEEPSEEK = "deepseek"
    OPENAI_COMPATIBLE = "openai-compatible"


class ModelId:
    """Model identifier class for representing language models."""

    def __init__(self, provider: str, name: str, path: str | None = None):
        """Initialize a ModelId.

        Args:
            provider: The model provider (e.g., 'openai', 'anthropic')
            name: The specific model name
            path: Optional path component for some providers
        """
        self.provider = provider
        self.name = name
        self.path = path

    @classmethod
    def from_string(cls, model_string: str) -> ModelId:
        """Create a ModelId from a string representation.

        Args:
            model_string: String in format 'provider:name' or 'provider/path:name'

        Returns:
            ModelId instance

        Raises:
            ValueError: If the string format is invalid
        """
        if ":" not in model_string:
            raise ValueError(
                f"Invalid model string format: {model_string}. Expected 'provider:name' or 'provider/path:name'"
            )

        # Find the last colon to separate provider+path from name
        last_colon_idx = model_string.rindex(":")
        provider_part = model_string[:last_colon_idx]
        name = model_string[last_colon_idx + 1 :]

        # Split provider_part on "/" to separate provider from path
        if "/" in provider_part:
            provider, path = provider_part.split("/", 1)
        else:
            provider = provider_part
            path = None

        return cls(provider, name, path)

    def __str__(self) -> str:
        """String representation of the ModelId."""
        if self.path:
            return f"{self.provider}/{self.path}:{self.name}"
        return f"{self.provider}:{self.name}"

    def __repr__(self) -> str:
        """String representation of the ModelId for debugging."""
        return f"ModelId(provider='{self.provider}', name='{self.name}', path='{self.path}')"

    def __eq__(self, other: object) -> bool:
        """Check equality with another ModelId object.

        Args:
            other (object): The object to compare with.

        Returns:
            bool: True if the objects are equal, False otherwise.
        """
        if not isinstance(other, ModelId):
            return NotImplemented
        return self.provider == other.provider and self.name == other.name and self.path == other.path

    def __hash__(self) -> int:
        """Return hash of the ModelId."""
        return hash((self.provider, self.name, self.path))


__all__ = ["ModelId", "ModelProvider"]
