"""Concrete implementation of NamePreprocessor according to OpenAI's name requirements.

Authors:
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

from aip_agents.utils.logger import get_logger
from aip_agents.utils.name_preprocessor import BaseNamePreprocessor

logger = get_logger(__name__)


class OpenAINamePreprocessor(BaseNamePreprocessor):
    """Concrete implementation of NamePreprocessor according to OpenAI's name requirements."""

    CUT_OFF_INDEX = 64

    def sanitize_agent_name(self, name: str) -> str:
        """Preprocess an input name according to OpenAI's name requirements for agents.

        As of now, OpenAI only has rule for tool name, and it is the same as Google's tool name rule,
        so just return the name as is.

        Args:
            name: The input name to preprocess.

        Returns:
            A name that is valid for OpenAI.
        """
        return name

    def sanitize_tool_name(self, name: str) -> str:
        """Preprocess an input name according to OpenAI's name requirements for tools.

        Args:
            name: The input name to preprocess.

        Returns:
            A name that is valid for OpenAI.

        Notes:
            Only contain letters (a-z, A-Z), digits (0-9), underscores (_), and dashes (-).
            It has a length limit of 64 characters.
        """
        name = self.regex_substitute(name, r"[^a-zA-Z0-9_-]", "_")
        name = self.clean_up_name(name)
        name = name[: self.CUT_OFF_INDEX]
        return name
