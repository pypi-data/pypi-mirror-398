from _typeshed import Incomplete
from enum import StrEnum

__all__ = ['ModelId', 'ModelProvider']

class ModelProvider(StrEnum):
    """Enumeration of supported model providers for the AI agent platform."""
    OPENAI: str
    ANTHROPIC: str
    AZURE_OPENAI: str
    GOOGLE_GENAI: str
    GROQ: str
    TOGETHER_AI: str
    DEEPINFRA: str
    DEEPSEEK: str
    OPENAI_COMPATIBLE: str

class ModelId:
    """Model identifier class for representing language models."""
    provider: Incomplete
    name: Incomplete
    path: Incomplete
    def __init__(self, provider: str, name: str, path: str | None = None) -> None:
        """Initialize a ModelId.

        Args:
            provider: The model provider (e.g., 'openai', 'anthropic')
            name: The specific model name
            path: Optional path component for some providers
        """
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
    def __eq__(self, other: object) -> bool:
        """Check equality with another ModelId object.

        Args:
            other (object): The object to compare with.

        Returns:
            bool: True if the objects are equal, False otherwise.
        """
    def __hash__(self) -> int:
        """Return hash of the ModelId."""
