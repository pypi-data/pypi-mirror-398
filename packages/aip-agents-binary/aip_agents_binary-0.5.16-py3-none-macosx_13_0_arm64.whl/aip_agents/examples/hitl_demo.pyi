import asyncio
import httpx
from _typeshed import Incomplete
from aip_agents.agent import LangGraphReactAgent as LangGraphReactAgent
from aip_agents.schema.hitl import ApprovalRequest as ApprovalRequest
from aip_agents.utils.env_loader import load_local_env as load_local_env
from aip_agents.utils.logger import get_logger as get_logger
from dataclasses import dataclass
from langchain_core.tools import tool
from starlette.applications import Starlette

logger: Incomplete

@tool
def check_candidate_inbox(candidate_email: str) -> str:
    """Retrieve the latest email from a candidate (safe tool).

    Args:
        candidate_email (str): The email address of the candidate.

    Returns:
        str: The latest email content from the candidate.
    """
@tool
def validate_candidate(candidate_name: str, role: str, score: int) -> str:
    """Record the candidate decision in the applicant tracking system.

    Args:
        candidate_name (str): The name of the candidate.
        role (str): The role the candidate is being evaluated for.
        score (int): The evaluation score for the candidate.

    Returns:
        str: The validation result with recommendation and notes.
    """
@tool
def send_candidate_email(candidate_email: str, subject: str, body: str) -> str:
    """Send an email update to the candidate.

    Args:
        candidate_email (str): The email address of the candidate.
        subject (str): The subject line of the email.
        body (str): The body content of the email.

    Returns:
        str: Confirmation message that the email was sent.
    """

CANDIDATE_PROFILES: dict[str, dict[str, str | int | bool]]
CANDIDATE_SEQUENCE: list[dict[str, str | int | bool]]
NAME_INDEX: Incomplete

class _ServerContext:
    def __init__(self, app: Starlette, host: str, port: int) -> None: ...
    async def __aenter__(self) -> _ServerContext: ...
    async def __aexit__(self, exc_type, exc, _tb) -> None: ...

@dataclass
class RunContext:
    """Context object containing runtime dependencies for the HITL demo server."""
    http_client: httpx.AsyncClient
    host: str
    port: int
    pending_queue: asyncio.Queue[ApprovalRequest]

async def main() -> None:
    """Interactive HITL approval demo."""
