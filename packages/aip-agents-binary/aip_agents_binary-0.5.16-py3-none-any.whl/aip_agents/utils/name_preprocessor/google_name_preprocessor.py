"""Concrete implementation of NamePreprocessor according to Google's name requirements.

This implementation provides the correction of name according to Google's name requirements.

Authors:
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

from aip_agents.utils.logger import get_logger
from aip_agents.utils.name_preprocessor import BaseNamePreprocessor

logger = get_logger(__name__)


class GoogleNamePreprocessor(BaseNamePreprocessor):
    """Concrete implementation of NamePreprocessor according to Google's name requirements."""

    NAME_SETTINGS = {
        "tool": {
            "prefix_fix": "Tool_",
            "regex": r"[^a-zA-Z0-9_-]",
        },
        "agent": {
            "prefix_fix": "Agent_",
            "regex": r"\W",
        },
    }
    CUT_OFF_INDEX = 63

    def _ensure_name_starts_with_letter_or_underscore(self, prefix_fix: str, name: str) -> str:
        """Preprocess an input name to be fixed if it doesn't start with a letter or an underscore.

        Args:
            prefix_fix: The prefix to add to the name if it doesn't start with a letter or an underscore.
            name: The input name to preprocess.

        Returns:
            A name that starts with a letter or an underscore.

        Notes:
            Name should start with a letter (a-z, A-Z) or an underscore (_),
            and can only contain letters, digits (0-9), and underscores.
        """
        if not name or (not name[0].isalpha() and name[0] != "_"):
            logger.warning(f"Invalid agent name: {name}. Agent name should start with a letter or an underscore.")
            prefix_fix = self._ensure_name_starts_with_letter_or_underscore("_", prefix_fix)
            name = prefix_fix + name
        return name

    def _common_process(self, name_type: str, name: str) -> str:
        """Preprocess an input name according to Google's name requirements.

        Args:
            name_type: The type of the name to preprocess ("tool" or "agent").
            name: The input name to preprocess.

        Returns:
            A name that is valid for Google.
        """
        prefix_fix = self.NAME_SETTINGS[name_type]["prefix_fix"]
        regex = self.NAME_SETTINGS[name_type]["regex"]
        name = self._ensure_name_starts_with_letter_or_underscore(prefix_fix, name)
        name = self.regex_substitute(name, regex, "_")
        name = self.clean_up_name(name)
        return name

    def sanitize_agent_name(self, name: str) -> str:
        """Preprocess an input name according to Google's name requirements for agents.

        Args:
            name: The input name to preprocess.

        Returns:
            A name that is valid for Google.

        Notes:
            Name should start with a letter (a-z, A-Z) or an underscore (_),
            and can only contain letters, digits (0-9), and underscores.
            It has no length limit. ( based on experiment )
        """
        name = self._common_process("agent", name)
        return name

    def sanitize_tool_name(self, name: str) -> str:
        """Preprocess an input name according to Google's name requirements for tools.

        Args:
            name: The input name to preprocess.

        Returns:
            A name that is valid for Google.

        Notes:
            Name should start with a letter (a-z, A-Z) or an underscore (_),
            and can only contain letters, digits (0-9), underscores, and dashes.
            It has a length limit of 64 characters, but google throws error if the length is exactly 64, so cut to 63.
        """
        name = self._common_process("tool", name)
        name = name[: self.CUT_OFF_INDEX]
        return name
