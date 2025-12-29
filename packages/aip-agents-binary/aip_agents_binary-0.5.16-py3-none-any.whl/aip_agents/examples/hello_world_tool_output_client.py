"""Simple A2A client demonstrating tool output management.

This client connects to the data visualization server and demonstrates
how tools can reference each other's outputs using the tool output
management system.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

import asyncio

from dotenv import load_dotenv

from aip_agents.agent import LangGraphReactAgent
from aip_agents.schema.agent import A2AClientConfig

load_dotenv()


async def main():
    """Demonstrate tool output management with data visualization."""
    # Create client agent
    client = LangGraphReactAgent(
        name="Client",
        instruction="You request data visualization services.",
        model="openai/gpt-4o-mini",
    )

    # Discover server agent
    agents = client.discover_agents(A2AClientConfig(discovery_urls=["http://localhost:8885"]))
    server_agent = agents[0]

    async for chunk in client.astream_to_agent(
        server_agent,
        "Generate sales data for 1000 months and create a bar chart from it",
    ):
        if chunk.get("content"):
            print(chunk["content"], end="", flush=True)
        if chunk.get("metadata"):
            print(f"\nMetadata: {chunk['metadata']}", end="\n\n", flush=True)
    print("\n")


if __name__ == "__main__":
    asyncio.run(main())
