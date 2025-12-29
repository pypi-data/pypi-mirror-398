"""Simple A2A client demonstrating RunnableConfig tool configuration."""

import asyncio

from dotenv import load_dotenv

from aip_agents.agent import LangGraphReactAgent
from aip_agents.schema.agent import A2AClientConfig

load_dotenv()


async def main():
    """Demonstrate RunnableConfig with agent defaults and runtime overrides."""
    # Create client agent
    client = LangGraphReactAgent(
        name="Client", instruction="You request currency services.", model="openai/gpt-4o-mini"
    )

    # Discover server agent
    agents = client.discover_agents(A2AClientConfig(discovery_urls=["http://localhost:8885"]))
    server_agent = agents[0]

    print("🚀 RunnableConfig Demo: Agent Defaults vs Runtime Overrides")
    print("=" * 60)

    # Test 1: Agent defaults (premium_corp from server)
    print("📊 Test 1: Agent Defaults")
    print("Query: Convert 100 USD to EUR")
    async for chunk in client.astream_to_agent(server_agent, "Convert 100 USD to EUR"):
        if chunk.get("content"):
            print(chunk["content"], end="\n", flush=True)
        if chunk.get("metadata"):
            print(f"Metadata: {chunk['metadata']}", end="\n\n", flush=True)
    print("\n")

    # Test 2: Runtime override (standard_business)
    print("📊 Test 2: Runtime Override")
    print("Query: Convert 100 USD to EUR")
    print("Metadata: Overriding to standard_business tenant")

    metadata = {
        "tool_configs": {"currency_exchange": {"tenant_id": "standard_business", "auth_key": "standard_key_456"}}
    }

    async for chunk in client.astream_to_agent(server_agent, "Convert 100 USD to EUR", metadata=metadata):
        if chunk.get("content"):
            print(chunk["content"], end="\n", flush=True)
        if chunk.get("metadata"):
            print(f"Metadata: {chunk['metadata']}", end="\n\n", flush=True)
    print("\n")

    print("✅ Demo completed! Notice different rates between premium_corp and standard_business.")


if __name__ == "__main__":
    asyncio.run(main())
