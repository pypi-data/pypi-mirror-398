"""Example A2A streaming client for the Google Search Tool and Time Tool Server.

This client demonstrates streaming interaction with the reference server
that provides time and mock Google search functionality via A2A protocol.

To use this client:
1. First start the reference server: python hello_world_a2a_langchain_reference_server.py
2. Then run this client: python hello_world_a2a_langchain_reference_client_streaming.py

Authors:
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

import asyncio
import pprint

from langchain_openai import ChatOpenAI

from aip_agents.agent import LangChainAgent
from aip_agents.schema.agent import A2AClientConfig


async def main():
    """Main function demonstrating streaming A2A client for the reference server."""
    agent = LangChainAgent(
        name="ReferenceClientAgent",
        instruction="""You are a helpful assistant that can delegate tasks to specialized agents.
        You can ask the mock retrieval server for mock data or mock Google search results.""",
        model=ChatOpenAI(model="gpt-4.1", streaming=True, temperature=0),
    )

    # Discover agents
    client_a2a_config = A2AClientConfig(
        discovery_urls=["http://localhost:8455"],
    )
    agent_cards = agent.discover_agents(client_a2a_config)

    if not agent_cards:
        print("No agents discovered. Make sure the reference server is running on http://localhost:8455")
        return

    print(f"Discovered agent: {agent_cards[0].name}")
    print(f"Description: {agent_cards[0].description}")
    print(f"Skills: {[skill.name for skill in agent_cards[0].skills]}")

    # Test queries to demonstrate the server's capabilities
    test_queries = "Search for information about NeoAI and retrieve some mock data about artificial intelligence"

    print(f"\n{'=' * 60}")
    print(f"Query: {test_queries}")
    print(f"{'=' * 60}")

    async for chunk in agent.astream_to_agent(agent_card=agent_cards[0], message=test_queries):
        print("-" * 50)
        pprint.pprint(chunk)
        print("-" * 50)


if __name__ == "__main__":
    asyncio.run(main())
