"""Memory constants for AIP Agents.

This module defines constants for memory-related method names and other
memory-related constants to avoid magic strings and numbers throughout the codebase.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""


class MemoryMethod:
    """Constants for memory method names used in hasattr checks."""

    SEARCH = "search"
    SAVE_INTERACTION = "save_interaction"
    FORMAT_HITS = "format_hits"


class MemoryDefaults:
    """Default values for memory configuration parameters."""

    # Memory retrieval and formatting limits
    MAX_ITEMS = 8  # Maximum number of memory items to include in formatted output
    RETRIEVAL_LIMIT = 5  # Default number of memories to retrieve per search
    MAX_CHARS = 1500  # Maximum characters per memory entry when saving

    # Logging and display
    LOG_PREVIEW_LENGTH = 100  # Length of text preview in logs
    SMALL_PREVIEW_LENGTH = 16  # Length of text preview in logs

    # Agent ID generation
    AGENT_ID_PREFIX = "agent-"  # Prefix for generated agent IDs

    # Memory formatting
    MEMORY_TAG_OPEN = "<RELEVANT_MEMORY>"
    MEMORY_TAG_CLOSE = "</RELEVANT_MEMORY>"

    # Default user ID for compatibility
    DEFAULT_USER_ID = "default"

    # Date format constants
    DATE_STRING_LENGTH = 10  # Length of "YYYY-MM-DD" format strings


class MemoryBackends:
    """Supported memory backend identifiers."""

    MEM0 = "mem0"
    SUPPORTED = frozenset({MEM0})
