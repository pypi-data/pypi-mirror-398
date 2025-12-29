"""Example of a General Assistant LangChainAgent that can delegate tasks to specialized agents.

This example demonstrates:
1. Configuring A2A settings for a client agent.
2. Creating a general assistant agent that can help with various queries.
3. Delegating specific tasks to specialized agents via A2A.
4. Handling responses and providing relevant advice.

Authors:
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

from aip_agents.agent import LangChainAgent
from aip_agents.schema.agent import A2AClientConfig


def main():
    """Main function demonstrating the General Assistant agent with A2A capabilities."""
    assistant_agent = LangChainAgent(
        name="AssistantAgentLangChain",
        instruction="""You are a helpful assistant that can help with various tasks
        by delegating to specialized agents.""",
        model="openai/gpt-4o",
    )

    # Discover agents
    client_a2a_config = A2AClientConfig(
        discovery_urls=["http://localhost:8001"],
    )
    agent_cards = assistant_agent.discover_agents(client_a2a_config)

    response = assistant_agent.send_to_agent(agent_cards[0], message="What is the weather in Jakarta?")
    print(response.get("content", str(response)))


if __name__ == "__main__":
    main()
