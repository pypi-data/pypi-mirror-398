"""Multi-Agent PII Demo Server - Demonstrates PII handling across agent hierarchy.

This server hosts a hierarchical agent system demonstrating PII propagation:
1. Level 1 (Coordinator): Main orchestrator that routes requests
2. Level 2 (Specialists): Domain-specific agents with PII-returning tools
   - CustomerServiceAgent: Handles customer inquiries
   - HRAgent: Handles employee data requests
   - UserSupportAgent: Handles user profile requests

Architecture:
PIICoordinator (A2A Server)
├── CustomerServiceAgent (with get_customer_info tool)
├── HRAgent (with get_employee_data tool)
└── UserSupportAgent (with get_user_profile tool)

Features demonstrated:
- PII anonymization in tool outputs
- PII propagation from child agents to parent
- Multi-agent delegation with PII mapping merge
- Collision handling when multiple agents discover PII

To run this server:
    export NER_API_URL=http://localhost:8080
    export NER_API_KEY=your-api-key
    python aip_agents/examples/pii_demo_multi_agent_server.py

It will listen on http://localhost:8003 by default.

Authors:
    Fachriza Adhiatma (fachriza.d.adhiatma@gdplabs.id)
"""

import click
import uvicorn
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from aip_agents.agent import LangGraphAgent
from aip_agents.examples.tools.pii_demo_tools import (
    get_customer_info,
    get_employee_data,
    get_user_profile,
)
from aip_agents.utils.logger import LoggerManager

load_dotenv()

logger = LoggerManager().get_logger(__name__)

SERVER_AGENT_NAME = "PIICoordinator"


def create_specialist_agents(llm: ChatOpenAI) -> tuple[LangGraphAgent, LangGraphAgent, LangGraphAgent]:
    """Create Level 2 specialist agents with PII-returning tools.

    Args:
        llm: The language model to use for the specialist agents.

    Returns:
        Tuple of (customer_service_agent, hr_agent, user_support_agent).
    """
    # Customer Service Agent - handles customer inquiries
    customer_service_agent = LangGraphAgent(
        name="CustomerServiceAgent",
        instruction="""You are a customer service specialist. You help retrieve customer information.

You have access to the get_customer_info tool to retrieve customer details.
When asked about customers, use this tool to get their information.

You will receive output from tools in masked version with PII tags like <PERSON_xxx>, <EMAIL_ADDRESS_xxx>.
Present the information as-is without trying to reveal or change the masked values.

Always be helpful and professional in your responses.""",
        model=llm,
        tools=[get_customer_info],
    )

    # HR Agent - handles employee data requests
    hr_agent = LangGraphAgent(
        name="HRAgent",
        instruction="""You are an HR specialist. You help retrieve employee information.

You have access to the get_employee_data tool to retrieve employee details.
When asked about employees, use this tool to get their information.

You will receive output from tools in masked version with PII tags like <PERSON_xxx>, <EMAIL_ADDRESS_xxx>.
Present the information as-is without trying to reveal or change the masked values.

Always maintain confidentiality and professionalism.""",
        model=llm,
        tools=[get_employee_data],
    )

    # User Support Agent - handles user profile requests
    user_support_agent = LangGraphAgent(
        name="UserSupportAgent",
        instruction="""You are a user support specialist. You help retrieve user profile information.

You have access to the get_user_profile tool to retrieve user details.
When asked about users, use this tool to get their profile information.

You will receive output from tools in masked version with PII tags like <PERSON_xxx>, <EMAIL_ADDRESS_xxx>.
Present the information as-is without trying to reveal or change the masked values.

Always be helpful and respect user privacy.""",
        model=llm,
        tools=[get_user_profile],
    )

    return customer_service_agent, hr_agent, user_support_agent


def create_coordinator_agent(
    llm: ChatOpenAI,
    specialist_agents: tuple[LangGraphAgent, LangGraphAgent, LangGraphAgent],
) -> LangGraphAgent:
    """Create Level 1 coordinator agent that orchestrates specialist agents.

    Args:
        llm: The language model to use for the coordinator agent.
        specialist_agents: Tuple of specialist agents.

    Returns:
        The configured coordinator agent.
    """
    customer_service_agent, hr_agent, user_support_agent = specialist_agents

    coordinator = LangGraphAgent(
        name=SERVER_AGENT_NAME,
        instruction="""You are a coordinator that manages requests across different departments.

You oversee three specialist teams:
- CustomerServiceAgent: Handles customer information requests (customer IDs like C001, C002, C003)
- HRAgent: Handles employee data requests (employee IDs like E001, E002, E003)
- UserSupportAgent: Handles user profile requests (user IDs like U001, U002, U003)

For each request, analyze what type of information is needed and delegate appropriately:
- Customer-related requests -> CustomerServiceAgent
- Employee/HR-related requests -> HRAgent
- User profile requests -> UserSupportAgent
- Complex requests may require multiple specialists

You will receive responses with PII tags like <PERSON_xxx>, <EMAIL_ADDRESS_xxx>.
Present the information as-is without trying to reveal or change the masked values.

Always provide a clear summary of the information gathered from your specialists.""",
        model=llm,
        agents=[customer_service_agent, hr_agent, user_support_agent],
    )

    return coordinator


@click.command()
@click.option("--host", "host", default="localhost", help="Host to bind the server to.")
@click.option("--port", "port", default=8003, help="Port to bind the server to.")
def main(host: str, port: int):
    """Runs the Multi-Agent PII Demo A2A server.

    This server demonstrates PII handling across a multi-agent hierarchy:
    - PII anonymization in tool outputs
    - PII propagation from child agents to parent
    - Multi-agent delegation with PII mapping merge

    Args:
        host: Host to bind the server to.
        port: Port to bind the server to.
    """
    logger.info(f"Starting {SERVER_AGENT_NAME} on http://{host}:{port}")
    logger.info("Multi-agent PII handling demo with 3 specialist agents")

    agent_card = AgentCard(
        name=SERVER_AGENT_NAME,
        description=(
            "A coordinator agent managing 3 specialist agents for customer, employee, "
            "and user information with automatic PII handling across the hierarchy."
        ),
        url=f"http://{host}:{port}",
        version="1.0.0",
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[
            AgentSkill(
                id="multi_agent_coordination",
                name="Multi-Agent PII Coordination",
                description="Coordinates requests across multiple specialist agents with PII handling.",
                examples=[
                    "Get information for customer C001 and employee E001",
                    "Compare customer C002 with user U002",
                    "Get all available information about John",
                ],
                tags=["coordination", "multi-agent", "pii"],
            ),
            AgentSkill(
                id="customer_service",
                name="Customer Service",
                description="Retrieves customer information via CustomerServiceAgent.",
                examples=[
                    "Get customer info for C001",
                    "What is the email for customer C002?",
                ],
                tags=["customer", "pii"],
            ),
            AgentSkill(
                id="hr_services",
                name="HR Services",
                description="Retrieves employee data via HRAgent.",
                examples=[
                    "Get employee data for E001",
                    "What department is employee E002 in?",
                ],
                tags=["employee", "hr", "pii"],
            ),
            AgentSkill(
                id="user_support",
                name="User Support",
                description="Retrieves user profile information via UserSupportAgent.",
                examples=[
                    "Get user profile for U001",
                    "What city does user U002 live in?",
                ],
                tags=["user", "profile", "pii"],
            ),
        ],
        tags=["pii", "demo", "multi-agent", "hierarchy"],
    )

    llm = ChatOpenAI(model="gpt-4.1", temperature=0, streaming=True)

    # Build the 2-level hierarchy
    logger.info("Creating Level 2 specialist agents...")
    specialist_agents = create_specialist_agents(llm)

    logger.info("Creating Level 1 coordinator agent...")
    coordinator_agent = create_coordinator_agent(llm, specialist_agents)

    app = coordinator_agent.to_a2a(agent_card=agent_card)

    logger.info("A2A application configured. Starting Uvicorn server...")
    logger.info("Hierarchy: 1 Coordinator -> 3 Specialists (each with PII tools)")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
