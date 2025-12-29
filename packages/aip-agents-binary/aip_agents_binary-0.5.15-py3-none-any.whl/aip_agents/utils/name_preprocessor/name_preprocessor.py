"""Utility functions for name preprocessing.

This module provides functions to preprocess names according to Google's name requirements.

References:
    https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/function-calling

Rules:
- For GoogleADK Agent Name:
    - Must start with a letter (a-z, A-Z) or an underscore (_),
    - Can only contain letters, digits (0-9), and underscores.
    - Has no length limit.
- For Tool Name:
    - Must start with a letter (a-z, A-Z) or an underscore (_),
    - Can only contain letters, digits (0-9), underscores, and dashes.
    - Has a length limit of 64 characters, but google throws error if the length is exactly 64, so cut to 63.
- For OpenAI,
    - they only have rule for tool name, and it is the same as Google's tool name rule,
    - except it can start with any character as long as it is a valid character (alphanumeric, _, -)

Authors:
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

from aip_agents.utils.logger import get_logger
from aip_agents.utils.name_preprocessor.base_name_preprocessor import BaseNamePreprocessor
from aip_agents.utils.name_preprocessor.google_name_preprocessor import GoogleNamePreprocessor
from aip_agents.utils.name_preprocessor.openai_name_preprocessor import OpenAINamePreprocessor

logger = get_logger(__name__)


class NamePreprocessor:
    """Name Preprocessor for Google ADK and OpenAI compatible models.

    Args:
        provider: The provider of the model.
    """

    PROVIDER_TO_NAME_PREPROCESSOR_MAP = {
        "openai": OpenAINamePreprocessor,
        "openai-compatible": OpenAINamePreprocessor,
        "google": GoogleNamePreprocessor,
    }

    def __init__(self, provider: str):
        """Initialize the name preprocessor.

        Args:
            provider: The provider of the model.
        """
        self.provider = provider
        self.preprocessor = self._get_preprocessor()

    def _get_preprocessor(self) -> BaseNamePreprocessor:
        """Get the name processor for the given provider.

        Args:
            provider: The provider of the model, i.e. openai, google, etc.
            This is used to determine which name processor to use.

        Returns:
            A name processor for the given provider.
        """
        return self.PROVIDER_TO_NAME_PREPROCESSOR_MAP.get(self.provider, GoogleNamePreprocessor)()

    def sanitize_agent_name(self, name: str) -> str:
        """Preprocess an input name according to the rules of the name processor.

        Args:
            name: The input name to preprocess.

        Returns:
            A name that is valid for the name processor.
        """
        return self.preprocessor.sanitize_agent_name(name)

    def sanitize_tool_name(self, name: str) -> str:
        """Preprocess an input name according to the rules of the name processor.

        Args:
            name: The input name to preprocess.

        Returns:
            A name that is valid for the name processor.
        """
        return self.preprocessor.sanitize_tool_name(name)
