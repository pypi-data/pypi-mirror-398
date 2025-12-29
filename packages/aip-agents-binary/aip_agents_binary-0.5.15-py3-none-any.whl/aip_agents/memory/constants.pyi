from _typeshed import Incomplete

class MemoryMethod:
    """Constants for memory method names used in hasattr checks."""
    SEARCH: str
    SAVE_INTERACTION: str
    FORMAT_HITS: str

class MemoryDefaults:
    """Default values for memory configuration parameters."""
    MAX_ITEMS: int
    RETRIEVAL_LIMIT: int
    MAX_CHARS: int
    LOG_PREVIEW_LENGTH: int
    SMALL_PREVIEW_LENGTH: int
    AGENT_ID_PREFIX: str
    MEMORY_TAG_OPEN: str
    MEMORY_TAG_CLOSE: str
    DEFAULT_USER_ID: str
    DATE_STRING_LENGTH: int

class MemoryBackends:
    """Supported memory backend identifiers."""
    MEM0: str
    SUPPORTED: Incomplete
