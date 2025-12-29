"""A2A client for the planning LangGraphReactAgent.

Run the planning server first:
    poetry run python -m aip_agents.examples.todolist_planning_a2a_langgraph_server

Then run this client:
    poetry run python -m aip_agents.examples.todolist_planning_a2a_langchain_client

You should see streaming output, including when write_todos_tool is called.
"""

import asyncio
import json

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from aip_agents.agent import LangChainAgent
from aip_agents.schema.agent import A2AClientConfig

load_dotenv()


async def main() -> None:
    """Connect to the planning A2A server and stream a planning query."""
    assistant_agent = LangChainAgent(
        name="PlanningClientAgent",
        instruction=(
            "You are a user-facing assistant that asks a planning agent "
            "to break work into a todo list before executing it."
        ),
        model=ChatOpenAI(model="gpt-4.1", temperature=0),
    )

    client_a2a_config = A2AClientConfig(
        discovery_urls=["http://localhost:8002"],
    )

    agent_cards = assistant_agent.discover_agents(client_a2a_config)
    if not agent_cards:
        print("No agents discovered at http://localhost:8002")
        return

    agent_card = agent_cards[0]
    print(f"Discovered agent: {agent_card.name} @ {agent_card.url}")

    query = "Research the latest advances in AI-driven drug discovery for oncology and synthesize findings into a comprehensive report—drawing on recent web-sourced literature and relevant company/market context—highlighting key breakthroughs, potential future directions, and a dedicated section on ethical considerations."

    print("\nSending query to planning agent (streaming)...\n")

    async for chunk in assistant_agent.astream_to_agent(agent_card, message=query):
        content = chunk.get("content")
        metadata = chunk.get("metadata", {})
        status = metadata.get("status") or metadata.get("state")

        if status and status.lower() in ("running", "processing"):
            print("Query:", query)
            if "tool_info" in metadata:
                print("Tool Info:", json.dumps(metadata["tool_info"], indent=2))

        if status and status.lower() in ("finished", "completed"):
            print("\n=== Completed — final output ===\n")
            if content:
                print(content)
            elif metadata.get("output"):
                print(metadata.get("output"))


if __name__ == "__main__":  # pragma: no cover - manual smoke script
    asyncio.run(main())
