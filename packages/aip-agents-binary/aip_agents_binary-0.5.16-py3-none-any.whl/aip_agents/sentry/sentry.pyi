from _typeshed import Incomplete
from aip_agents.agent import BaseAgent as BaseAgent, GoogleADKAgent as GoogleADKAgent, LangChainAgent as LangChainAgent, LangGraphAgent as LangGraphAgent
from aip_agents.utils.logger import get_logger as get_logger
from fastapi import FastAPI

logger: Incomplete
SENTRY_DSN: Incomplete
SENTRY_ENVIRONMENT: Incomplete
SENTRY_PROJECT: Incomplete
VERSION_NUMBER: Incomplete
BUILD_NUMBER: Incomplete
USE_OPENTELEMETRY: Incomplete
CLASSES_TO_INSTRUMENT: Incomplete

def get_all_methods(cls) -> list:
    """Get all methods from a class.

    Args:
        cls: The class to get methods from.

    Returns:
        list: A list of methods.
    """
def instrument_bosa_functions() -> None:
    """Instrument BOSA functions."""
def traces_sampler(*args) -> float:
    """Determine appropriate sampling rate for Sentry transactions.

    Args:
        *args: Additional positional arguments

    Returns:
        float: Sampling rate between 0 and 1
    """
def setup_sentry_with_open_telemetry(app: FastAPI) -> None:
    """Configure telemetry with both Sentry and OpenTelemetry.

    Args:
        app: FastAPI application instance
    """
def setup_sentry_only() -> None:
    """Configure telemetry with Sentry only (no OpenTelemetry)."""
def setup_telemetry(app: FastAPI) -> None:
    """Configure and initialize telemetry based on configuration.

    Args:
        app: FastAPI application instance
    """
