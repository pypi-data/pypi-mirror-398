"""This file contains the Sentry and OpenTelemetry configuration for BOSA SDK.

Authors:
    Saul Sayers (saul.sayers@gdplabs.id)
"""

import inspect
import os

from bosa_core.telemetry import (
    FastAPIConfig,
    OpenTelemetryConfig,
    SentryConfig,
    TelemetryConfig,
    init_telemetry,
)
from bosa_core.telemetry.opentelemetry.instrument.functions import (
    BOSAFunctionsInstrumentor,
)
from dotenv import load_dotenv
from fastapi import FastAPI

from aip_agents.agent import BaseAgent, GoogleADKAgent, LangChainAgent, LangGraphAgent
from aip_agents.utils.logger import get_logger

load_dotenv()


logger = get_logger(__name__)

SENTRY_DSN = os.getenv("SENTRY_DSN")
SENTRY_ENVIRONMENT = os.getenv("SENTRY_ENVIRONMENT", "development")
SENTRY_PROJECT = os.getenv("SENTRY_PROJECT")
VERSION_NUMBER = os.getenv("VERSION_NUMBER", "0.0.0")
BUILD_NUMBER = os.getenv("BUILD_NUMBER", "0")
USE_OPENTELEMETRY = os.getenv("USE_OPENTELEMETRY", "true").lower() == "true"

CLASSES_TO_INSTRUMENT = [
    BaseAgent,
    LangGraphAgent,
    LangChainAgent,
    GoogleADKAgent,
]


def get_all_methods(cls: type) -> list:
    """Get all methods from a class.

    Args:
        cls: The class to get methods from.

    Returns:
        list: A list of methods.
    """
    methods = []
    for name, member in inspect.getmembers(cls):
        if name.startswith("_"):
            continue  # skip dunder and private
        if inspect.isfunction(member) or inspect.ismethod(member) or inspect.iscoroutinefunction(member):
            methods.append(member)
    return methods


def instrument_bosa_functions() -> None:
    """Instrument BOSA functions."""
    if BOSAFunctionsInstrumentor is None:
        return
    agent_methods = []
    for cls in CLASSES_TO_INSTRUMENT:
        agent_methods.extend(get_all_methods(cls))
    BOSAFunctionsInstrumentor().instrument(methods=agent_methods)


def traces_sampler(*args) -> float:
    """Determine appropriate sampling rate for Sentry transactions.

    Args:
        *args: Additional positional arguments

    Returns:
        float: Sampling rate between 0 and 1
    """
    # TODO: Dont sample healthcheck endpoints (return 0.0)
    return 1.0


def setup_sentry_with_open_telemetry(app: FastAPI) -> None:
    """Configure telemetry with both Sentry and OpenTelemetry.

    Args:
        app: FastAPI application instance
    """
    try:
        fastapi_config = FastAPIConfig(app)

        # Create OpenTelemetry configuration
        opentelemetry_init = OpenTelemetryConfig(
            use_langchain=True,
            fastapi_config=fastapi_config,
        )

        # Sentry configuration with OpenTelemetry
        sentry_config = SentryConfig(
            dsn=SENTRY_DSN,
            traces_sampler=traces_sampler,
            environment=SENTRY_ENVIRONMENT,
            release=f"{SENTRY_PROJECT}@{VERSION_NUMBER}+{BUILD_NUMBER}",
            send_default_pii=True,
            open_telemetry_config=opentelemetry_init,
        )

        telemetry_config = TelemetryConfig(sentry_config=sentry_config)
        init_telemetry(telemetry_config)
        logger.info(f"Telemetry initialized with OpenTelemetry for environment: {SENTRY_ENVIRONMENT}")
    except Exception as e:
        logger.error(f"Failed to initialize telemetry with OpenTelemetry: {e}")


def setup_sentry_only() -> None:
    """Configure telemetry with Sentry only (no OpenTelemetry)."""
    try:
        # Sentry configuration without OpenTelemetry
        sentry_config = SentryConfig(
            dsn=SENTRY_DSN,
            traces_sampler=traces_sampler,
            environment=SENTRY_ENVIRONMENT,
            release=f"{SENTRY_PROJECT}@{VERSION_NUMBER}+{BUILD_NUMBER}",
            send_default_pii=True,
        )

        telemetry_config = TelemetryConfig(sentry_config=sentry_config)
        init_telemetry(telemetry_config)
        logger.info(f"Telemetry initialized with Sentry only for environment: {SENTRY_ENVIRONMENT}")
    except Exception as e:
        logger.error(f"Failed to initialize telemetry with Sentry only: {e}")


def setup_telemetry(app: FastAPI) -> None:
    """Configure and initialize telemetry based on configuration.

    Args:
        app: FastAPI application instance
    """
    if not SENTRY_DSN:
        logger.warning("Warning: SENTRY_DSN not set. Sentry will not be enabled.")
        return
    if USE_OPENTELEMETRY:
        setup_sentry_with_open_telemetry(app)
    else:
        setup_sentry_only()
    instrument_bosa_functions()
