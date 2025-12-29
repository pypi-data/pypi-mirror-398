import logging
from _typeshed import Incomplete

LOGGER_NAME: str
LOG_LEVEL: Incomplete

class _GoogleAdkLogFilter(logging.Filter):
    """Suppress noisy Google ADK model registry logs.

    Google ADK emits a burst of INFO logs when registering Gemini model patterns.
    They are redundant (class is unchanged) and clutter our startup output, so we
    drop them at the logging infrastructure level instead of touching ADK internals.
    """
    SUPPRESSED_PREFIX: str
    def filter(self, record: logging.LogRecord) -> bool:
        """Return False when the log should be discarded.

        Args:
            record (logging.LogRecord): The log record to filter.

        Returns:
            bool: True if the log should be processed, False if it should be discarded.
        """

LOG_FILTERS: Incomplete
logger_manager: Incomplete
root_logger: Incomplete

def get_logger(name: str = ..., level: int = ...) -> logging.Logger:
    """Get a logger instance.

    Args:
        name (str): The name of the logger. Defaults to AIPAgentsLogger.
        level (int): The level of the logger. Defaults to INFO.

    Returns:
        logging.Logger: The logger instance.
    """

logger: Incomplete
THIRD_PARTY_LOGGER_NAMES: Incomplete

class LoggerManager:
    """A singleton class to manage logging configuration.

    This class is deprecated and will be removed in a future version.
    Use get_logger() function directly instead.
    """
    def __new__(cls):
        """Initialize the singleton instance."""
    def get_logger(self, name: str = ..., level: int = ...) -> logging.Logger:
        """Get a logger instance.

        Args:
            name (str): The name of the logger. Defaults to AIPAgentsLogger.
            level (int): The level of the logger. Defaults to INFO.

        Returns:
            logging.Logger: The logger instance.
        """
