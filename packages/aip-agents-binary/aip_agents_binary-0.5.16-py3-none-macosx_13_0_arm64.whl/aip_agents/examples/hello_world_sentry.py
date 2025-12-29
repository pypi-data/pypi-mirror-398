"""This is a simple FastAPI app to test Sentry with Open Telemetry from BOSA SDK.

To run this example, make sure to set the following environment variables:
    SENTRY_DSN
    SENTRY_ENVIRONMENT
    SENTRY_PROJECT
    VERSION_NUMBER
    BUILD_NUMBER
    USE_OPENTELEMETRY

Authors:
    Saul Sayers (saul.sayers@gdplabs.id)
"""

import io
import os
import subprocess
import sys
import threading
import time

import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from aip_agents.examples.hello_world_langgraph import langgraph_example
from aip_agents.sentry import setup_telemetry
from aip_agents.utils.logger import get_logger

logger = get_logger(__name__)

BASE_URL = "http://localhost:8585"
SENTRY_ENVIRONMENT = os.getenv("SENTRY_ENVIRONMENT", "development")
USE_OPENTELEMETRY = os.getenv("USE_OPENTELEMETRY", "true").lower() == "true"


def fetch_endpoints():
    """Fetch all endpoints from the server."""
    BASE_URL = "http://127.0.0.1:8585"
    endpoints = [
        "/",
        "/langgraph-hello-world",
        "/test-telemetry",
        "/raise-error",
    ]
    for ep in endpoints:
        url = BASE_URL + ep
        try:
            # Because using request.get() will trigger sentry, but the ep name is not saved.
            # Instead of GET /langgraph-hello-world, sentry will save it as GET
            url = f"http://127.0.0.1:8585{ep}"
            result = subprocess.run(["curl", "-i", url], capture_output=True, text=True, check=False)
            logger.info(result.stdout)
        except Exception as e:
            logger.error(f"Error fetching {ep}: {e}")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        FastAPI: The configured FastAPI application.
    """
    app = FastAPI(
        title="Bosa SDK - Sentry with Open Telemetry",
        description="This is a simple FastAPI app to test Sentry with Open Telemetry.",
        version="0.0.1",
        docs_url=None,
        redoc_url="/docs",
    )

    if os.path.isdir("static"):
        app.mount("/static", StaticFiles(directory="static"), name="static")
    setup_telemetry(app)

    @app.get("/", tags=["Root"])
    async def index():
        if USE_OPENTELEMETRY:
            return {
                "message": "Application running with Sentry + OpenTelemetry.",
                "telemetry_mode": "Sentry with OpenTelemetry",
                "environment": SENTRY_ENVIRONMENT,
            }
        else:
            return {
                "message": "Application running with Sentry only (no OpenTelemetry).",
                "telemetry_mode": "Sentry only",
                "environment": SENTRY_ENVIRONMENT,
            }

    @app.get("/langgraph-hello-world", tags=["LangGraph"])
    async def langgraph_hello_world():
        old_stdout = sys.stdout
        sys.stdout = mystdout = io.StringIO()
        try:
            await langgraph_example()
            output = mystdout.getvalue()
        finally:
            sys.stdout = old_stdout
        return JSONResponse(content={"output": output})

    @app.get("/test-telemetry", tags=["Root"])
    async def test_telemetry():
        return {
            "message": "Telemetry test endpoint called.",
            "using_opentelemetry": USE_OPENTELEMETRY,
            "check": "Check your Sentry dashboard for traces.",
        }

    @app.get("/raise-error", tags=["Root"])
    async def raise_error():
        raise RuntimeError("This is a test error for Sentry!")

    return app


def run_server():
    """Run the FastAPI server."""
    uvicorn.run(
        "aip_agents.examples.hello_world_sentry:create_app",
        host="127.0.0.1",
        port=8585,
        factory=True,
        log_level="info",
    )


if __name__ == "__main__":
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    time.sleep(2)
    fetch_endpoints()
