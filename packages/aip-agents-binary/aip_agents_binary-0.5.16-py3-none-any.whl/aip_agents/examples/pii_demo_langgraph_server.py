"""Example A2A server demonstrating PII handling in LangGraph agents.

This server instantiates a LangGraph ReAct agent with tools that return personally
identifiable information (PII). The agent demonstrates automatic PII anonymization
and deanonymization during parallel tool execution.

Features demonstrated:
- Automatic PII detection and anonymization in tool outputs
- Deanonymization of PII for tool input arguments
- Collision detection and resolution in parallel tool execution
- Hybrid tag strategy (sequential tags preserved, UUID tags for collisions)

To run this server:
    export NER_API_URL=http://localhost:8080
    export NER_API_KEY=your-api-key
    python examples/pii_demo_langgraph_server.py

It will listen on http://localhost:8002 by default.

Authors:
    Fachriza Adhiatma (fachriza.d.adhiatma@gdplabs.id)
"""

import click
import uvicorn
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from dotenv import load_dotenv

from aip_agents.agent import LangChainAgent
from aip_agents.examples.tools.pii_demo_tools import (
    get_customer_info,
    get_employee_data,
    get_user_profile,
)
from aip_agents.utils.logger import LoggerManager

load_dotenv()

logger = LoggerManager().get_logger(__name__)


SERVER_AGENT_NAME = "PIIDemoAgentLangGraph"


@click.command()
@click.option("--host", "host", default="localhost", help="Host to bind the server to.")
@click.option("--port", "port", default=8002, help="Port to bind the server to.")
def main(host: str, port: int):
    """Runs the PII Demo LangGraph A2A server.

    This server demonstrates PII handling capabilities including:
    - Automatic anonymization of sensitive data in tool outputs
    - Deanonymization of PII for tool inputs
    - Collision detection and resolution in parallel tool execution

    Args:
        host (str): Host to bind the server to.
        port (int): Port to bind the server to.
    """
    logger.info(f"Starting {SERVER_AGENT_NAME} on http://{host}:{port}")
    logger.info("PII handling is enabled. Sensitive data will be automatically anonymized.")

    agent_card = AgentCard(
        name=SERVER_AGENT_NAME,
        description="A LangGraph ReAct agent demonstrating PII handling with automatic anonymization and deanonymization",
        url=f"http://{host}:{port}",
        version="1.0.0",
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[
            AgentSkill(
                id="customer_info",
                name="Get Customer Information",
                description="Retrieves customer information including email and phone number",
                examples=["Get customer info for C001", "What is the email for customer C002?"],
                tags=["customer", "pii"],
            ),
            AgentSkill(
                id="employee_data",
                name="Get Employee Data",
                description="Retrieves employee data including name, email, and salary",
                examples=["Get employee data for E001", "What is the salary for employee E002?"],
                tags=["employee", "pii"],
            ),
            AgentSkill(
                id="user_profile",
                name="Get User Profile",
                description="Retrieves user profile information with personal details",
                examples=["Get user profile for U001", "What is the email for user U002?"],
                tags=["user", "pii"],
            ),
        ],
        tags=["pii", "demo", "langgraph"],
    )

    langgraph_agent = LangChainAgent(
        name=SERVER_AGENT_NAME,
        instruction="""You are a helpful assistant that can retrieve customer, employee, and user information.

You have access to three tools:
1. get_customer_info: Retrieves customer information (email, phone, address)
2. get_employee_data: Retrieves employee data (email, phone, salary, department)
3. get_user_profile: Retrieves user profile information (email, phone, date of birth, city)

When users ask for information, use the appropriate tool to retrieve the data.
The system will automatically handle PII anonymization and deanonymization.

You will receive output from tool in masked version,
just write the response as it is without revealing or changing the masked values.

Always be helpful and provide the requested information clearly.""",
        model="openai/gpt-4.1",
        tools=[get_customer_info, get_employee_data, get_user_profile],
    )

    app = langgraph_agent.to_a2a(
        agent_card=agent_card,
    )

    logger.info("A2A application configured. Starting Uvicorn server...")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
