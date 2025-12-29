from _typeshed import Incomplete
from aip_agents.examples.hello_world_langgraph import langgraph_example as langgraph_example
from aip_agents.sentry import setup_telemetry as setup_telemetry
from aip_agents.utils.logger import get_logger as get_logger
from fastapi import FastAPI

logger: Incomplete
BASE_URL: str
SENTRY_ENVIRONMENT: Incomplete
USE_OPENTELEMETRY: Incomplete

def fetch_endpoints() -> None:
    """Fetch all endpoints from the server."""
def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        FastAPI: The configured FastAPI application.
    """
def run_server() -> None:
    """Run the FastAPI server."""
