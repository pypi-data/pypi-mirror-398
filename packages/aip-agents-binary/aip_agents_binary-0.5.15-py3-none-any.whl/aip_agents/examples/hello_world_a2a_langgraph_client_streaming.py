"""Example of a General Assistant LangGraphAgent that can delegate tasks to specialized agents.

This example demonstrates:
1. Configuring A2A settings for a client agent.
2. Creating a general assistant agent that can help with various queries.
3. Delegating specific tasks to specialized agents via A2A with streaming.
4. Handling streaming responses and providing relevant advice.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

import asyncio

from langchain_openai import ChatOpenAI

from aip_agents.agent import LangGraphAgent
from aip_agents.schema.agent import A2AClientConfig
from aip_agents.utils.logger import get_logger

logger = get_logger(__name__)


async def main():
    """Main function demonstrating the General Assistant agent with streaming A2A capabilities."""
    llm = ChatOpenAI(model="gpt-4.1", streaming=True)
    assistant_agent = LangGraphAgent(
        name="AssistantAgent",
        instruction="""You are a helpful assistant that can help with various tasks
        by delegating to specialized agents.""",
        model=llm,
        tools=[],
    )

    # Discover agents
    client_a2a_config = A2AClientConfig(
        discovery_urls=["http://localhost:8001"],
    )
    agent_cards = assistant_agent.discover_agents(client_a2a_config)

    query = "What is the weather in Jakarta?"
    logger.info(f"Processing Query: {query}")

    async for chunk in assistant_agent.astream_to_agent(agent_card=agent_cards[0], message=query):
        print(chunk.get("content", ""))


if __name__ == "__main__":
    asyncio.run(main())
