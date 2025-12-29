#!/usr/bin/env python3
"""Interactive HITL (Human-in-the-Loop) Approval Demo.

This demo creates a recruitment-focused LangGraph agent that requires human approval for
critical steps in a candidate workflow.
You'll be prompted to approve/reject tool calls in real-time.

Usage:
    python -m aip_agents.examples.hitl_demo

Requirements:
    - OPENAI_API_KEY in environment variables or .env file (auto-loaded)
    - Internet connection for LLM API calls
"""

import asyncio
import contextlib
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from http import HTTPStatus

import httpx
import uvicorn
from langchain_core.tools import tool
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from aip_agents.agent import LangGraphReactAgent
from aip_agents.schema.hitl import ApprovalRequest
from aip_agents.utils.env_loader import load_local_env
from aip_agents.utils.logger import get_logger

# Load environment variables for local development
load_local_env()

# Get logger instance for this demo
logger = get_logger("aip_agents.examples.hitl_demo", logging.CRITICAL)


@tool
def check_candidate_inbox(candidate_email: str) -> str:
    """Retrieve the latest email from a candidate (safe tool).

    Args:
        candidate_email (str): The email address of the candidate.

    Returns:
        str: The latest email content from the candidate.
    """
    profile = CANDIDATE_PROFILES.get(candidate_email.lower())
    if profile and isinstance(profile.get("inbox"), str):
        return profile["inbox"]
    return f"Email from {candidate_email}: Thank you for the update. Looking forward to next steps."


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
    profile = NAME_INDEX.get(candidate_name.lower())
    if profile is None:
        return (
            f"Candidate {candidate_name} evaluated for {role}. Final assessment score: {score}. "
            "Recommendation data not found; manual review required."
        )

    recommendation = profile.get("recommendation", "pending")
    summary = profile.get("notes", "No additional notes provided.")
    actual_score = profile.get("score", score)
    if recommendation == "approved":
        status_text = "ATS recommendation: move forward"
    elif recommendation == "rejected":
        status_text = "ATS recommendation: do not proceed"
    else:
        status_text = "ATS recommendation: pending hiring committee review"

    return (
        f"Candidate {profile['name']} evaluated for {role}. Final assessment score: {actual_score}. "
        f"{summary} {status_text}."
    )


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
    profile = CANDIDATE_PROFILES.get(candidate_email.lower())
    if profile is not None:
        profile["last_email_subject"] = subject
        profile["last_email_body"] = body
    return f"Email sent to {candidate_email} with subject '{subject}'"


CANDIDATE_PROFILES: dict[str, dict[str, str | int | bool]] = {
    "jane.doe@example.com": {
        "email": "jane.doe@example.com",
        "name": "Jane Doe",
        "role": "Senior Backend Engineer",
        "score": 87,
        "recommendation": "approved",
        "inbox": (
            "Hi team, thanks for the update! I'm excited about the opportunity and available for a call next week."
        ),
        "notes": "Strong performance in system design and coding exercises.",
        "offer_subject": "Offer Confirmation — Senior Backend Engineer",
        "pending_subject": "Interview Update — Senior Backend Engineer",
        "rejection_subject": "Application Update — Senior Backend Engineer",
    },
    "sam.lee@example.com": {
        "email": "sam.lee@example.com",
        "name": "Sam Lee",
        "role": "Senior Backend Engineer",
        "score": 68,
        "recommendation": "rejected",
        "inbox": (
            "Hello recruiter, I appreciate the opportunity. Please let me know if you need any "
            "additional information from my end."
        ),
        "notes": "Great collaboration skills but struggled with distributed systems questions.",
        "offer_subject": "Offer Confirmation — Senior Backend Engineer",
        "pending_subject": "Interview Update — Senior Backend Engineer",
        "rejection_subject": "Application Update — Senior Backend Engineer",
    },
}

CANDIDATE_SEQUENCE: list[dict[str, str | int | bool]] = [
    CANDIDATE_PROFILES["jane.doe@example.com"],
    CANDIDATE_PROFILES["sam.lee@example.com"],
]

NAME_INDEX = {profile["name"].lower(): profile for profile in CANDIDATE_SEQUENCE}


def _normalize_timeout_decision(decision: str | None) -> str:
    """Treat timeout (or missing) decisions as skips for downstream handling.

    Args:
        decision (str | None): The decision to normalize, or None if timed out.

    Returns:
        str: The normalized decision ("approved", "rejected", or "skipped").
    """
    if decision in {None, "timeout"}:
        return "skipped"
    return decision


def _summarize_outcome(
    name: str,
    validation: str,
    email: str,
    *,
    validation_timeout: bool,
    email_timeout: bool,
) -> str:
    if validation_timeout:
        validation_text = f"left {name}'s hiring decision pending (timed out)"
    elif validation == "approved":
        validation_text = f"approved {name}'s hiring decision"
    elif validation == "rejected":
        validation_text = f"rejected {name}'s hiring decision"
    else:
        validation_text = f"left {name}'s hiring decision pending"

    if email_timeout:
        email_text = "no email update was sent (skipped due to timeout)"
    elif email == "approved":
        email_text = "an email update was sent"
    elif email == "skipped":
        email_text = "no email update was sent yet"
    else:
        email_text = f"email outcome recorded as '{email}'"

    return f"  - You {validation_text}; {email_text}."


def _print_intro() -> None:
    print("🚀 HITL Approval Demo")
    print("This demo requires real LLM API access and will prompt for human input.")
    print(
        "Scenario: recruitment coordinator processing candidate updates."
        " Steps: check candidate inbox (safe), validate candidate (approval), send candidate email (approval)."
    )
    print("This demo walks through two candidates: one recommended to move forward and one declined.")
    print(
        "Commands are shown for each step (e.g., a/r or send/cancel). "
        "You can append optional comments like 'send looks good'."
    )
    print()


def _format_json_block(raw: str) -> str:
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError):
        return raw
    return json.dumps(parsed, indent=2, ensure_ascii=False)


def _format_timeout(request: ApprovalRequest) -> str:
    if request.timeout_at and isinstance(request.timeout_at, datetime):
        return request.timeout_at.isoformat()
    return "n/a"


def _print_multiline(label: str, content: str) -> None:
    print(f"{label}:")
    if not content.strip():
        print("    (none)")
        return
    for line in content.splitlines():
        print(f"    {line}")


def _print_command_help(tool_name: str) -> None:
    print("Commands:")
    if tool_name == "validate_candidate":
        options = [
            ("a", "approve"),
            ("r", "reject"),
        ]
    elif tool_name == "send_candidate_email":
        options = [
            ("send", "send email"),
            ("cancel", "cancel email"),
        ]
    else:
        options = [
            ("a", "approve"),
            ("s", "skip"),
            ("r", "reject"),
        ]

    for key, description in options:
        print(f"  [{key}] {description}")
    print("  (optional comment after command, e.g. 'send looks good')")


def _decision_mapping(tool_name: str) -> tuple[dict[str, str], str]:
    if tool_name == "validate_candidate":
        return (
            {
                "a": "approved",
                "approve": "approved",
                "approved": "approved",
                "r": "rejected",
                "reject": "rejected",
                "rejected": "rejected",
            },
            "Please enter a or r.",
        )

    if tool_name == "send_candidate_email":
        return (
            {
                "send": "approved",
                "s": "approved",
                "approved": "approved",
                "cancel": "skipped",
                "c": "skipped",
                "skip": "skipped",
            },
            "Please enter send or cancel.",
        )

    return (
        {
            "a": "approved",
            "approve": "approved",
            "approved": "approved",
            "s": "skipped",
            "skip": "skipped",
            "skipped": "skipped",
            "r": "rejected",
            "reject": "rejected",
            "rejected": "rejected",
        },
        "Please enter a, s, or r.",
    )


def _print_pending_request(request: ApprovalRequest) -> None:
    border = "═" * 70
    print(f"\n{border}")
    print("🔒  Approval Required")
    print(border)
    print(f"Tool       : {request.tool_name}")
    print(f"Request ID : {request.request_id}")
    print(f"Timeout At : {_format_timeout(request)}")

    arguments_block = _format_json_block(request.arguments_preview)
    _print_multiline("Arguments", arguments_block)

    context_text = json.dumps(request.context, indent=2, ensure_ascii=False) if request.context else ""
    _print_multiline("Context", context_text)

    print()
    _print_command_help(request.tool_name)
    print(border)


def _build_demo_agent() -> "LangGraphReactAgent":
    return LangGraphReactAgent(
        name="HITL Demo Agent",
        instruction=(
            "You are a recruitment coordinator preparing a candidate update. "
            "When asked for the latest message from a candidate, call check_candidate_inbox with their email. "
            "When directed to record the hiring decision, you must call validate_candidate "
            "before taking any other action. "
            "If the validation is rejected you must halt the workflow and inform the user; if it is skipped, "
            "you may continue but clarify in follow-up actions that the decision remains pending "
            "and do not attempt to validate again unless explicitly asked. "
            "Use send_candidate_email to notify the candidate once the decision status is settled."
        ),
        model="openai/gpt-4.1",
        tools=[
            check_candidate_inbox,
            validate_candidate,
            send_candidate_email,
        ],
        tool_configs={
            "tool_configs": {
                "send_candidate_email": {"hitl": {"timeout_seconds": 30}},
                "validate_candidate": {"hitl": {"timeout_seconds": 10}},
            }
        },
    )


def _candidate_inbox_query(profile: dict[str, str | int | bool]) -> str:
    return (
        f"Check the candidate inbox for {profile['email']} using check_candidate_inbox and "
        "summarise key information they provided."
    )


def _validate_candidate_query(profile: dict[str, str | int | bool]) -> str:
    return (
        f"Validate {profile['name']} for the {profile['role']} role using validate_candidate "
        f"with a final score of {profile['score']}. Highlight the main strengths noted during interviews."
    )


def _candidate_email_query(
    profile: dict[str, str | int | bool],
    validation_status: str | None,
) -> str:
    if validation_status == "approved":
        subject = profile.get("offer_subject", "Offer Confirmation")
        return (
            "You must notify the candidate of the offer. "
            f"Call send_candidate_email to send an offer confirmation to {profile['email']} with subject '{subject}'. "
            "Do not call validate_candidate again; the decision has already been recorded."
        )

    if validation_status in {"skipped", "timeout", None}:
        subject = profile.get("pending_subject", "Interview Update")
        return (
            "The decision is still pending. "
            f"Call send_candidate_email to provide an update to {profile['email']} with subject '{subject}'. "
            "Do not attempt to re-run validate_candidate; simply let the candidate know the decision is pending."
        )

    subject = profile.get("rejection_subject", "Application Update")
    return (
        "The candidate has been declined. "
        f"Call send_candidate_email to send a polite rejection email to {profile['email']} with subject '{subject}'. "
        "Do not call validate_candidate again during this follow-up."
    )


def _create_server_app(agent: "LangGraphReactAgent") -> tuple[Starlette, asyncio.Queue[ApprovalRequest]]:
    pending_queue: asyncio.Queue[ApprovalRequest] = asyncio.Queue()

    def notifier(request: ApprovalRequest) -> None:
        try:
            loop = asyncio.get_running_loop()
            loop.call_soon_threadsafe(pending_queue.put_nowait, request)
        except RuntimeError:
            pending_queue.put_nowait(request)

    agent.register_hitl_notifier(notifier)
    _ = agent.hitl_manager

    async def run_agent(request: Request) -> JSONResponse:
        payload = await request.json()
        message = payload.get("message", "")
        result = await agent.arun(message, recursion_limit=5)
        output = result.get("output")
        serialized_state = repr(result.get("full_final_state"))
        return JSONResponse({"output": output, "state": serialized_state})

    async def hitl_decision(request: Request) -> JSONResponse:
        payload = await request.json()
        request_id = payload.get("request_id")
        decision = payload.get("decision")
        operator_input = payload.get("operator_input", "")
        try:
            agent.hitl_manager.resolve_pending_request(request_id, decision, operator_input=operator_input)
            return JSONResponse({"status": "ok"})
        except KeyError as exc:
            return JSONResponse({"error": str(exc)}, status_code=404)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)

    routes = [
        Route("/agent/run", run_agent, methods=["POST"]),
        Route("/hitl/decision", hitl_decision, methods=["POST"]),
    ]

    app = Starlette(routes=routes)
    return app, pending_queue


class _ServerContext:
    def __init__(self, app: Starlette, host: str, port: int) -> None:
        config = uvicorn.Config(app, host=host, port=port, log_level="warning")
        self._server = uvicorn.Server(config)
        self._server.install_signal_handlers = False
        self._task: asyncio.Task | None = None

    async def __aenter__(self) -> "_ServerContext":
        self._task = asyncio.create_task(self._server.serve())
        while not self._server.started:
            await asyncio.sleep(0.05)
        return self

    async def __aexit__(self, exc_type, exc, _tb) -> None:
        self._server.should_exit = True
        if self._task:
            await self._task


def _drain_queue(queue: asyncio.Queue[ApprovalRequest]) -> None:
    try:
        while True:
            queue.get_nowait()
    except asyncio.QueueEmpty:
        pass


async def _invoke_run_endpoint(
    http_client: httpx.AsyncClient,
    host: str,
    port: int,
    message: str,
) -> dict[str, str]:
    response = await http_client.post(
        f"http://{host}:{port}/agent/run",
        json={"message": message},
        timeout=None,
    )
    response.raise_for_status()
    return response.json()


async def _prompt_and_send_decision(
    http_client: httpx.AsyncClient,
    host: str,
    port: int,
    request: ApprovalRequest,
) -> str:
    _print_pending_request(request)
    mapping, invalid_message = _decision_mapping(request.tool_name)

    while True:
        user_input = await asyncio.to_thread(input, "> ")
        stripped = user_input.strip()
        if not stripped:
            print(invalid_message)
            continue

        first_token, *rest = stripped.split(maxsplit=1)
        token = first_token.lower()
        decision = mapping.get(token)

        if decision is None:
            print(invalid_message)
            continue

        resp = await http_client.post(
            f"http://{host}:{port}/hitl/decision",
            json={
                "request_id": request.request_id,
                "decision": decision,
                "operator_input": stripped,
            },
            timeout=None,
        )
        if resp.status_code != HTTPStatus.OK:
            if resp.status_code in {HTTPStatus.NOT_FOUND, HTTPStatus.GONE}:
                print(f"⏱️  Request {request.request_id} expired (status {resp.status_code}). Skipping this action.")
                return "timeout"

            print(f"Failed to submit decision ({resp.status_code}): {resp.text}")
            continue

        comment = rest[0] if rest else ""
        base_msg = f"Submitted '{decision}' for request {request.request_id}"
        if comment:
            base_msg += f" with comment: {comment}"
        print(base_msg + ". Waiting for agent...\n")
        return decision


@dataclass
class RunContext:
    """Context object containing runtime dependencies for the HITL demo server."""

    http_client: httpx.AsyncClient
    host: str
    port: int
    pending_queue: asyncio.Queue[ApprovalRequest]


async def _run_step(
    context: RunContext,
    message: str,
    *,
    step_name: str,
    allowed_tools: set[str] | None = None,
) -> tuple[str, dict[str, str]]:
    print(f"\n—— {step_name} ——")

    _drain_queue(context.pending_queue)

    run_task = asyncio.create_task(_invoke_run_endpoint(context.http_client, context.host, context.port, message))
    queue_task = asyncio.create_task(context.pending_queue.get())
    decisions: dict[str, str] = {}

    try:
        while True:
            done, _ = await asyncio.wait({run_task, queue_task}, return_when=asyncio.FIRST_COMPLETED)

            if run_task in done:
                result = run_task.result()
                queue_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await queue_task

                output = result.get("output", "No output")
                if output:
                    print("🤖 AI response:")
                    print(output)
                else:
                    print("🤖 AI response: (no message returned)")
                if decisions:
                    print("📝 HITL decisions during this step:")
                    for tool, decision in decisions.items():
                        print(f"  - {tool}: {decision}")
                return output, decisions

            if queue_task in done:
                request = queue_task.result()

                if allowed_tools is not None and request.tool_name not in allowed_tools:
                    print(f"⚙️  Auto-skipping unexpected tool '{request.tool_name}' during {step_name}.")
                    await context.http_client.post(
                        f"http://{context.host}:{context.port}/hitl/decision",
                        json={
                            "request_id": request.request_id,
                            "decision": "skipped",
                            "operator_input": "AUTO_SKIP_UNEXPECTED_TOOL",
                        },
                        timeout=None,
                    )
                else:
                    decision = await _prompt_and_send_decision(context.http_client, context.host, context.port, request)
                    decisions[request.tool_name] = decision

                queue_task = asyncio.create_task(context.pending_queue.get())

    except Exception as exc:  # noqa: BLE001
        run_task.cancel()
        queue_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await run_task
            await queue_task
        _handle_run_error(exc)
        return "", {}


async def _run_workflow(context: RunContext) -> None:
    summaries: list[dict[str, str | bool]] = []

    print("🤖 Workflow starting.")
    print("   Step 1 (candidate inbox) runs automatically without approval.")
    print(
        "   Steps 2 and 3 will prompt you for HITL decisions; use the keys listed in the command panel "
        "(e.g., a/r or send/cancel)."
    )

    for profile in CANDIDATE_SEQUENCE:
        name = profile["name"]
        email = profile["email"]

        print("\n==================================================")
        print(f"Processing candidate: {name} ({email}) — {profile['role']}")
        print("==================================================")
        recommendation = profile.get("recommendation", "pending")
        score = profile.get("score", "n/a")
        print(f"ATS recommendation: {recommendation} (score: {score})")

        await _run_step(
            context,
            _candidate_inbox_query(profile),
            step_name=f"{name}: Inbox review (no approval)",
            allowed_tools=None,
        )

        _, validation_decisions = await _run_step(
            context,
            _validate_candidate_query(profile),
            step_name=f"{name}: Validation (approval required)",
            allowed_tools={"validate_candidate"},
        )

        raw_validation_status = validation_decisions.get("validate_candidate")
        validation_status = _normalize_timeout_decision(raw_validation_status)

        if raw_validation_status == "timeout":
            print("⏱️ Validation timed out — treating as skipped; the decision remains pending.")
        elif validation_status == "rejected":
            print("❌ Validation rejected — the candidate will be notified of the decision.")
        elif validation_status == "skipped":
            print("⚠️ Validation skipped — notification will indicate the decision is still pending.")
        else:
            print("✅ Candidate validation approved — proceeding to send offer confirmation.")

        _, email_decisions = await _run_step(
            context,
            _candidate_email_query(profile, validation_status),
            step_name=f"{name}: Candidate email (approval required)",
            allowed_tools={"send_candidate_email"},
        )

        raw_email_status = email_decisions.get("send_candidate_email")
        email_status = _normalize_timeout_decision(raw_email_status)

        if raw_email_status == "timeout":
            print("⏱️ Email send timed out — treating as skipped; no notification was sent.")

        summaries.append(
            {
                "name": name,
                "validation": validation_status,
                "validation_timeout": raw_validation_status == "timeout",
                "email_decision": email_status,
                "email_timeout": raw_email_status == "timeout",
            }
        )

    summary_messages: list[str] = [
        _summarize_outcome(
            name=summary["name"],
            validation=summary["validation"],
            email=summary["email_decision"],
            validation_timeout=bool(summary.get("validation_timeout", False)),
            email_timeout=bool(summary.get("email_timeout", False)),
        )
        for summary in summaries
    ]

    print("\n📋 What happened:")
    for message in summary_messages:
        print(message)

    print("\n🎉 Workflow completed successfully!")


def _handle_run_error(error: Exception) -> None:
    message = str(error)
    if "api_key" in message.lower():
        print("\n❌ Error: OpenAI API key not found!")
        print("Make sure OPENAI_API_KEY is set in your environment or .env file.")
        print("The demo automatically loads from .env files, so create one with:")
        print("  echo 'OPENAI_API_KEY=your-key-here' > .env")
    else:
        print(f"\n❌ Error: {error}")


async def main():
    """Interactive HITL approval demo."""
    _print_intro()
    agent = _build_demo_agent()
    app, pending_queue = _create_server_app(agent)
    host, port = "127.0.0.1", 8787

    async with _ServerContext(app, host, port):
        print(f"🖥️  HITL API listening on http://{host}:{port}")
        print('    POST /agent/run        {"message": ...}')
        print('    POST /hitl/decision    {"request_id": ..., "decision": ...}')
        async with httpx.AsyncClient(timeout=None) as http_client:
            context = RunContext(
                http_client=http_client,
                host=host,
                port=port,
                pending_queue=pending_queue,
            )
            await _run_workflow(context)


if __name__ == "__main__":
    asyncio.run(main())
