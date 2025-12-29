"""Defines a logger for logging.

Example of displayed logs using simple format:
    [2025-11-27T15:50:03+0700.643 uvicorn.error INFO] Application startup complete.

Example of displayed logs using JSON format:
    {"timestamp": "2025-11-27T15:51:00+0700", "name": "uvicorn.error", "level": "INFO", "message": "Application startup complete."}

Authors:
    Reinhart Linanda (reinhart.linanda@gdplabs.id)

References:
    [1] https://github.com/GDP-ADMIN/gsdp
    [2] https://docs.google.com/document/d/1RnXbiAGc6vCFt03YPMM8UleRy0h_pRjzqobdb_u8ty0/edit?tab=t.0
        (Proposal for Standardized Log Format)
    [3] https://github.com/GDP-ADMIN/glchat/blob/main/applications/glchat-be/glchat_be/utils/logger.py
"""

import logging
import os
import threading
import warnings

from dotenv import load_dotenv
from gllm_core.utils.logger_manager import LoggerManager

load_dotenv()

LOGGER_NAME = "AIPAgentsLogger"

LOG_LEVEL = os.getenv("LOG_LEVEL", logging.INFO)
if isinstance(LOG_LEVEL, str):
    try:
        LOG_LEVEL = getattr(logging, LOG_LEVEL.upper())
    except AttributeError:
        LOG_LEVEL = logging.INFO


class _GoogleAdkLogFilter(logging.Filter):
    """Suppress noisy Google ADK model registry logs.

    Google ADK emits a burst of INFO logs when registering Gemini model patterns.
    They are redundant (class is unchanged) and clutter our startup output, so we
    drop them at the logging infrastructure level instead of touching ADK internals.
    """

    SUPPRESSED_PREFIX = "Updating LLM class for"

    def filter(self, record: logging.LogRecord) -> bool:
        """Return False when the log should be discarded.

        Args:
            record (logging.LogRecord): The log record to filter.

        Returns:
            bool: True if the log should be processed, False if it should be discarded.
        """
        if not record.name.startswith("google.adk"):
            return True

        try:
            message = record.getMessage()
        except Exception:  # pragma: no cover - defensive fallback
            message = str(record.msg)

        if isinstance(message, str) and message.startswith(self.SUPPRESSED_PREFIX):
            return False

        return True


LOG_FILTERS = [_GoogleAdkLogFilter()]

logger_manager = LoggerManager()
root_logger = logger_manager.get_logger()

_LOGGER_LOCK = threading.Lock()

_LOG_FILTERS_CONFIGURED = False


def _configure_log_filters() -> None:
    """Configure log filters to be applied to all handlers."""
    global _LOG_FILTERS_CONFIGURED

    with _LOGGER_LOCK:
        if _LOG_FILTERS_CONFIGURED:
            return

        for log_filter in LOG_FILTERS:
            root_logger.addFilter(log_filter)
            for handler in root_logger.handlers:
                handler.addFilter(log_filter)

        _LOG_FILTERS_CONFIGURED = True


_configure_log_filters()


def get_logger(name: str = LOGGER_NAME, level: int = LOG_LEVEL) -> logging.Logger:
    """Get a logger instance.

    Args:
        name (str): The name of the logger. Defaults to AIPAgentsLogger.
        level (int): The level of the logger. Defaults to INFO.

    Returns:
        logging.Logger: The logger instance.
    """
    with _LOGGER_LOCK:
        if not name:
            name = LOGGER_NAME
        if logging._levelToName.get(level) is None:
            level = LOG_LEVEL

        logger = logger_manager.get_logger(name)
        logger.setLevel(level)
        logger.propagate = False

        if not logger.hasHandlers():
            logger.handlers = root_logger.handlers

        return logger


logger = get_logger()

THIRD_PARTY_LOGGER_NAMES = [
    "uvicorn",
    "uvicorn.access",
    "uvicorn.error",
    "apscheduler",
    "apscheduler.scheduler",
    "apscheduler.executors.default",
    "apscheduler.jobstores.default",
]

_THIRD_PARTY_LOGGERS_CONFIGURED = False


def _configure_third_party_loggers() -> None:
    """Configure third-party loggers to use the same handlers and settings."""
    global _THIRD_PARTY_LOGGERS_CONFIGURED

    with _LOGGER_LOCK:
        if _THIRD_PARTY_LOGGERS_CONFIGURED:
            return

        for name in THIRD_PARTY_LOGGER_NAMES:
            third_party_logger = logging.getLogger(name)
            third_party_logger.handlers = logger.handlers
            third_party_logger.setLevel(logger.level)
            third_party_logger.propagate = logger.propagate

        _THIRD_PARTY_LOGGERS_CONFIGURED = True


_configure_third_party_loggers()


class LoggerManager:
    """A singleton class to manage logging configuration.

    This class is deprecated and will be removed in a future version.
    Use get_logger() function directly instead.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Initialize the singleton instance."""
        warnings.warn(
            "LoggerManager is deprecated and will be removed in a future version. "
            "Use get_logger() function directly instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def get_logger(self, name: str = LOGGER_NAME, level: int = LOG_LEVEL) -> logging.Logger:
        """Get a logger instance.

        Args:
            name (str): The name of the logger. Defaults to AIPAgentsLogger.
            level (int): The level of the logger. Defaults to INFO.

        Returns:
            logging.Logger: The logger instance.
        """
        return get_logger(name, level)
