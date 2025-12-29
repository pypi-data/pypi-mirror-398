"""Example of a LangflowAgent client that can interact with A2A servers via streaming.

This example demonstrates:
1. Configuring A2A settings for a client agent.
2. Discovering and communicating with Langflow agents via A2A.
3. Using streaming A2A communication for real-time responses.
4. Handling streaming responses and providing relevant interactions.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

import asyncio

from dotenv import load_dotenv

from aip_agents.agent.langflow_agent import LangflowAgent
from aip_agents.schema.agent import A2AClientConfig
from aip_agents.utils.logger import get_logger

logger = get_logger(__name__)
load_dotenv()


async def main():
    """Main function demonstrating the Langflow client with streaming A2A capabilities."""
    # Create the LangflowAgent client
    client_agent = LangflowAgent(
        name="LangflowA2AClient",
        flow_id="dummy-flow-id",  # Not used for client operations
        description="Client agent for A2A streaming testing",
    )

    # Discover agents
    client_a2a_config = A2AClientConfig(
        discovery_urls=["http://localhost:8787"],
    )

    print("🔍 Discovering A2A agents...")
    agent_cards = client_agent.discover_agents(client_a2a_config)

    if not agent_cards:
        logger.error("❌ No agents discovered!")
        print("💡 Make sure the A2A server is running:")
        print("   python aip_agents/examples/hello_world_a2a_langflow_server.py")
        return

    print(f"✅ Discovered {len(agent_cards)} agent(s):")
    for i, agent_card in enumerate(agent_cards, 1):
        print(f"  {i}. {agent_card.name} - {agent_card.description}")

    # Use streaming A2A communication
    query = "Tell me a short story about a robot learning to paint"
    print(f"\n📡 Streaming Query: {query}")
    print("🎯 Response (streaming):")
    print("-" * 50)

    try:
        chunk_count = 0

        async for chunk in client_agent.astream_to_agent(agent_card=agent_cards[0], message=query):
            chunk_count += 1
            content = chunk.get("content", "")
            status = chunk.get("status", "unknown")
            is_final = chunk.get("final", False)

            if content:
                if status == "success":
                    print(content)
                else:
                    print(f"\n[{status}] {content}")

            # Log completion but don't break - let stream finish naturally
            if is_final:
                print(f"\n\n✅ Stream completed! ({chunk_count} chunks received)")

    except Exception as e:
        logger.error(f"❌ Streaming error: {e}")
        print(f"Error during A2A streaming: {e}")


if __name__ == "__main__":
    asyncio.run(main())
