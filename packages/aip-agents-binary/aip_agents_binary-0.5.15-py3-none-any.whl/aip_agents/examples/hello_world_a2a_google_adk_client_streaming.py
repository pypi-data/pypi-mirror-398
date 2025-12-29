"""Example of a General Assistant GoogleADKAgent that can delegate tasks to specialized agents.

This example demonstrates:
1. Configuring A2A settings for a client agent.
2. Creating a general assistant agent that can help with various queries.
3. Delegating specific tasks to specialized agents via A2A with streaming.
4. Handling streaming responses and providing relevant advice.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

import asyncio

from a2a.types import TaskState

from aip_agents.agent.google_adk_agent import GoogleADKAgent
from aip_agents.schema.agent import A2AClientConfig
from aip_agents.utils.logger import get_logger

logger = get_logger(__name__)


async def main():
    """Main function demonstrating the General Assistant agent with streaming A2A capabilities."""
    agent_name = "GoogleADKWeatherAgent"

    # Create the agent with simplified instructions and our tool
    assistant_agent = GoogleADKAgent(
        name=agent_name,
        instruction="You are a helpful assistant that can help with various tasks by delegating to specialized agents.",
        model="gemini-2.0-flash",
        tools=[],
        max_iterations=5,
    )

    # Discover agents
    client_a2a_config = A2AClientConfig(
        discovery_urls=["http://localhost:8002"],
    )
    agent_cards = assistant_agent.discover_agents(client_a2a_config)

    query = "What is the weather in Jakarta?"
    logger.info(f"Processing Query: {query}")

    agent_result = ""
    async for chunk in assistant_agent.astream_to_agent(agent_card=agent_cards[0], message=query):
        task_state = chunk.get("task_state")
        content = chunk.get("content", "")
        if task_state == TaskState.working and content:
            logger.info(f"Event Working: {content}")
        elif task_state == TaskState.completed and content:
            agent_result += content

    logger.info(f"Agent Response: {agent_result}")
    return agent_result


if __name__ == "__main__":
    asyncio.run(main())
