"""This module provides a centralized way to handle Sentry and OpenTelemetry configuration for BOSA SDK.

Authors:
    Saul Sayers (saul.sayers@gdplabs.id)
"""

from aip_agents.sentry.sentry import setup_telemetry

__all__ = [
    "setup_telemetry",
]
