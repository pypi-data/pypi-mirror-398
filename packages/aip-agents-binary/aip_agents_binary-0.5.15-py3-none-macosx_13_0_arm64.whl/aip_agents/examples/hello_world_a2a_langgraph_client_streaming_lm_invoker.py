"""Example of a General Assistant LangChainAgent that can delegate tasks to specialized agents.

This example demonstrates:
1. Configuring A2A settings for a client agent.
2. Creating a general assistant agent that can help with various queries.
3. Delegating specific tasks to specialized agents via A2A with streaming.
4. Handling streaming responses and providing relevant advice.

Authors:
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

import asyncio
from pprint import pprint

from aip_agents.agent import LangChainAgent
from aip_agents.schema.agent import A2AClientConfig


async def main():
    """Main function demonstrating the General Assistant agent with streaming A2A capabilities."""
    agent = LangChainAgent(
        name="AssistantAgentLangChain",
        instruction="""You are a helpful assistant that can help with various tasks
        by delegating to specialized agents.""",
        model="openai/gpt-4.1",
    )

    # Discover agents
    client_a2a_config = A2AClientConfig(
        discovery_urls=["http://localhost:8001"],
    )
    agent_cards = agent.discover_agents(client_a2a_config)

    async for chunk in agent.astream_to_agent(
        agent_card=agent_cards[0], message="What is the weather in Jakarta and London?"
    ):
        pprint(chunk)
        print("-" * 50)


if __name__ == "__main__":
    asyncio.run(main())
