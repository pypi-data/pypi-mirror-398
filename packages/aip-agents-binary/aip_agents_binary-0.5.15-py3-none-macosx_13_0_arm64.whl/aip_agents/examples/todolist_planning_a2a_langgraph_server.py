"""A2A server exposing a LangGraphReactAgent with planning (TodoListMiddleware).

Run:
    poetry run python -m aip_agents.examples.todolist_planning_a2a_langgraph_server \
        --host localhost --port 8002

Then connect with the matching A2A client to observe write_todos_tool calls.
"""

import click
import langchain
import uvicorn
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from aip_agents.agent import LangGraphReactAgent
from aip_agents.examples.tools.serper_tool import MockGoogleSerperTool
from aip_agents.examples.tools.stock_tools import get_stock_price
from aip_agents.utils.logger import get_logger

langchain.debug = True

load_dotenv()

logger = get_logger(__name__)

SERVER_AGENT_NAME = "PlanningTodoAgent"


@click.command()
@click.option("--host", "host", default="localhost", help="Host to bind the server to.")
@click.option("--port", "port", default=8002, help="Port to bind the server to.")
def main(host: str, port: int) -> None:
    """Run an A2A server with a planning-enabled LangGraphReactAgent.

    The agent has TodoListMiddleware attached via planning=True and will
    expose the write_todos_tool over A2A with token streaming enabled.

    Args:
        host: The host to bind the server to.
        port: The port to bind the server to.
    """
    logger.info(f"Starting {SERVER_AGENT_NAME} on http://{host}:{port}")

    agent_card = AgentCard(
        name=SERVER_AGENT_NAME,
        description="Planning agent that breaks tasks into todos using write_todos.",
        url=f"http://{host}:{port}",
        version="1.0.0",
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[
            AgentSkill(
                id="planning",
                name="Planning and Todo Management",
                description="Breaks high-level tasks into a todo list and tracks progress.",
                examples=[
                    "Plan a 3-step migration task and show the todo list.",
                    "Create a todo list for building a small feature.",
                ],
                tags=["planning", "todos"],
            )
        ],
        tags=["planning", "todos"],
    )

    llm = ChatOpenAI(model="gpt-4.1", temperature=0, streaming=True)

    # No custom tools; planning=True will attach TodoListMiddleware and
    # provide write_todos_tool automatically.
    agent = LangGraphReactAgent(
        name=SERVER_AGENT_NAME,
        instruction=("You are an Assistant Agent, your job is to answer based on a query."),
        model=llm,
        tools=[MockGoogleSerperTool(), get_stock_price],
        planning=True,
    )

    app = agent.to_a2a(agent_card=agent_card)

    logger.info("Planning A2A application configured. Starting Uvicorn server...")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":  # pragma: no cover - manual smoke script
    main()
