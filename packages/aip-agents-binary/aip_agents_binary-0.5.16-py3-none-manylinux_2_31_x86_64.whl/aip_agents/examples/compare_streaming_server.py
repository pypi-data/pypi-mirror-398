"""A2A server with artifact and reference tools for streaming comparison tests.

This server provides an agent with:
- table_generator tool: Returns artifacts (CSV files)
- mock_retrieval tool: Returns references

To run this server:
    cd libs/aip_agents
    poetry run python -m aip_agents.examples.compare_streaming_server

It will listen on http://localhost:18999 by default.

Authors:
    AI Agent Platform Team
"""

import click
import uvicorn
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from langchain_openai import ChatOpenAI

from aip_agents.agent import LangGraphAgent
from aip_agents.examples.tools.mock_retrieval_tool import MockRetrievalTool
from aip_agents.examples.tools.pii_demo_tools import (
    get_customer_info,
    get_employee_data,
    get_user_profile,
)
from aip_agents.examples.tools.random_chart_tool import RandomChartTool
from aip_agents.examples.tools.table_generator_tool import TableGeneratorTool
from aip_agents.utils.logger import get_logger

logger = get_logger(__name__)

SERVER_AGENT_NAME = "StreamingComparisonAgent"


@click.command()
@click.option("--host", "host", default="localhost", help="Host to bind the server to.")
@click.option("--port", "port", default=18999, help="Port to bind the server to.")
def main(host: str, port: int):
    """Runs the streaming comparison A2A server.

    Args:
        host: Host to bind the server to.
        port: Port to bind the server to.
    """
    print(f"Starting {SERVER_AGENT_NAME} on http://{host}:{port}")

    agent_card = AgentCard(
        name=SERVER_AGENT_NAME,
        description="Agent for comparing direct vs connector streaming with artifacts and references.",
        url=f"http://{host}:{port}",
        version="1.0.0",
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[
            AgentSkill(
                id="table_generation",
                name="Table Generation",
                description="Generates data tables as CSV artifacts.",
                examples=["Generate a table with 3 rows"],
                tags=["table", "artifact"],
            ),
            AgentSkill(
                id="mock_retrieval",
                name="Mock Retrieval",
                description="Retrieves mock data with references.",
                examples=["Search for test data"],
                tags=["retrieval", "references"],
            ),
            AgentSkill(
                id="customer_info",
                name="Get Customer Information",
                description="Retrieves customer information including email and phone number (PII masked).",
                examples=["Get customer info for C001", "What is the email for customer C002?"],
                tags=["customer", "pii"],
            ),
            AgentSkill(
                id="employee_data",
                name="Get Employee Data",
                description="Retrieves employee data including name, email, and salary (PII masked).",
                examples=["Get employee data for E001", "What is the salary for employee E002?"],
                tags=["employee", "pii"],
            ),
            AgentSkill(
                id="user_profile",
                name="Get User Profile",
                description="Retrieves user profile information with personal details (PII masked).",
                examples=["Get user profile for U001", "What is the email for user U002?"],
                tags=["user", "pii"],
            ),
        ],
        tags=["test", "comparison", "artifacts", "references", "pii"],
    )

    # Token streaming disabled for now - will compare token streaming later
    llm = ChatOpenAI(model="gpt-4.1", temperature=0, streaming=False)
    table_tool = TableGeneratorTool()
    mock_retrieval_tool = MockRetrievalTool()
    random_chart_tool = RandomChartTool()
    tools = [table_tool, mock_retrieval_tool, get_customer_info, get_employee_data, get_user_profile]

    visualization_agent = LangGraphAgent(
        name="RandomChartAgent",
        instruction=(
            "You are a visualization specialist. Whenever asked to produce a chart, visualization, or images "
            "that summarize insights, call the random_chart_tool to generate a bar chart artifact. "
            "Describe what the generated image represents."
        ),
        model=llm,
        tools=[random_chart_tool],
    )

    agent = LangGraphAgent(
        name=SERVER_AGENT_NAME,
        instruction=(
            "You are a helpful assistant for testing streaming comparison. "
            "When asked for a table, use the table_generator tool. "
            "When asked to search or retrieve, use the mock_retrieval tool. "
            "When asked for customer information, use the get_customer_info tool. "
            "When asked for employee data, use the get_employee_data tool. "
            "When asked for user profile, use the get_user_profile tool. "
            "IMPORTANT: When you receive PII placeholders like <PERSON_1>, pass them WITH the angle brackets <> "
            "to the tools - they are required for the PII system to work correctly. "
            "Always use the tools when relevant to demonstrate artifacts, references, and PII masking."
        ),
        model=llm,
        tools=tools,
        enable_a2a_token_streaming=False,
        agents=[visualization_agent],
    )

    app = agent.to_a2a(agent_card=agent_card)

    print("A2A application configured. Starting Uvicorn server...")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
