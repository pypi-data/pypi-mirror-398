"""Example of a General Assistant LangChainAgent that delegates time and weather tasks to specialized agents.

This example demonstrates:
1. Configuring A2A settings for a client agent to connect to time/weather services.
2. Creating a general assistant agent that can help with time and weather queries.
3. Delegating specific time and weather tasks to specialized agents via A2A with streaming.
4. Handling streaming responses from time and weather tasks.
5. Real-time display of time and weather information and agent thinking process.

The client requests the time/weather agent to get current time and weather forecast,
demonstrating streaming capabilities of the LangGraph agent wrapper.

To run this example:
1. First start the time/weather agent server:
   python examples/hello_world_a2a_langgraph_server_tool_streaming.py --port 8003
2. Then run this client:
   python examples/hello_world_a2a_langgraph_client_streaming_tool_streaming.py

Environment Variables Required:
    OPENAI_API_KEY: OpenAI API key for the LLM

Authors:
    Fachriza Adhiatma (fachriza.d.adhiatma@gdplabs.id)
"""

import asyncio
from pprint import pprint

from aip_agents.agent import LangChainAgent
from aip_agents.schema.agent import A2AClientConfig


async def main():
    """Main function demonstrating the General Assistant agent with streaming A2A time/weather capabilities."""
    print("🚀 Starting Time & Weather Agent Client Demo")
    print("=" * 60)

    # Create a general assistant agent
    agent = LangChainAgent(
        name="TimeWeatherAssistantAgentLangChain",
        instruction="""You are a helpful assistant that can help with various tasks
        by delegating to specialized agents. You have access to time and weather
        agents that can provide current time information and weather data
        for specific cities.

        When users ask for time or weather-related tasks, delegate them to the
        time/weather agent. Provide clear summaries of the results and help
        interpret the information that's provided.""",
        model="openai/gpt-4o",
    )

    # Configure A2A client to discover time/weather agents
    client_a2a_config = A2AClientConfig(
        discovery_urls=["http://localhost:8003"],  # Time/weather agent server
    )

    print("🔍 Discovering available time & weather agents...")
    try:
        agent_cards = agent.discover_agents(client_a2a_config)

        if not agent_cards:
            print("❌ No time & weather agents found!")
            print("   Make sure the agent server is running on http://localhost:8003")
            return

        print(f"✅ Found {len(agent_cards)} time & weather agent(s)")

        for i, card in enumerate(agent_cards):
            print(f"   {i + 1}. {card.name}: {card.description}")
            if card.skills:
                print(f"      Skills: {', '.join([skill.name for skill in card.skills])}")

        task = "what time is it and what is the weather in jakarta?"

        print(f"📝 Task: {task}")

        async for chunk in agent.astream_to_agent(agent_card=agent_cards[0], message=task):
            print("-" * 40)
            pprint(chunk)

        print("\n" + "=" * 60)
        print("\n🎉 Time & Weather agent task finished!")

    except Exception as e:
        print(f"❌ Error during time & weather query: {str(e)}")
        print("   Make sure:")
        print("   1. The time & weather server is running (python hello_world_a2a_langgraph_server_agent_wrapper.py)")
        print("   2. OPENAI_API_KEY is set in your environment")


if __name__ == "__main__":
    asyncio.run(main())
