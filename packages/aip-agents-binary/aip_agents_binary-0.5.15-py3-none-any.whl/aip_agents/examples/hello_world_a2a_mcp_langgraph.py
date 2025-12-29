"""Example demonstrating integration of A2A and MCP servers with LangGraphAgent.

This script shows how to create a LangGraphAgent that connects to:
1. An MCP server with weather forecast tool (must be running on port 8000)
2. An A2A server with weather capabilities (must be running on port 8001)

To run this example:
1. Start the MCP server: python aip_agents/examples/mcp_servers/mcp_server_sse.py
2. Start the A2A server: python aip_agents/examples/hello_world_a2a_langgraph_server.py
3. Set your OPENAI_API_KEY environment variable
4. Run this script: python examples/hello_world_a2a_mcp_langgraph.py

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

import asyncio
import os
import sys
import traceback

from langchain_openai import ChatOpenAI

from aip_agents.agent import LangGraphAgent
from aip_agents.schema.agent import A2AClientConfig

# Configuration
A2A_SERVER_PORT = 8002  # Port for StockAgent A2A server
A2A_AGENT_NAME = "StockAgent"  # Must match the agent name in A2A server
MCP_SERVER_PORT = 8000  # Port for MCP server (weather tools)
MCP_AGENT_NAME = "weather_tools"  # Must match the agent name in MCP server
MODEL_NAME = "gpt-4.1"


async def create_agent() -> tuple[LangGraphAgent, dict[str, bool]]:
    """Create and configure the LangGraphAgent with MCP and A2A connections.

    Returns:
        tuple: (agent, connected_servers) where connected_servers is a dict
        showing which servers were successfully connected.
    """
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY environment variable not set")

    print("\nCreating LangGraphAgent...")
    llm = ChatOpenAI(model=MODEL_NAME, temperature=0, openai_api_key=os.getenv("OPENAI_API_KEY"))

    agent = LangGraphAgent(
        name="IntegrationAgent",
        instruction="""You are a helpful assistant that can use various tools.
        For stock-related queries (price, news, etc.), use the StockAgent tool.
        For weather-related queries, use the get_weather_forecast tool.
        Choose the appropriate tool based on the user's request.""",
        model=llm,
        tools=[],  # We'll add tools dynamically
    )

    return agent, {"mcp": False, "a2a": False}


async def connect_to_mcp_server(agent: LangGraphAgent) -> bool:
    """Connect to the MCP server and register tools.

    Args:
        agent: The LangGraphAgent instance to configure.

    Returns:
        bool: True if connection was successful, False otherwise.
    """
    try:
        print(f"\nConnecting to MCP server on port {MCP_SERVER_PORT}...")
        agent.add_mcp_server(
            {
                MCP_AGENT_NAME: {
                    "url": f"http://localhost:{MCP_SERVER_PORT}/sse",
                    "transport": "sse",
                    "api_key": "",  # No auth for test server
                }
            }
        )
        print(f"✅ Successfully connected to MCP server: {MCP_AGENT_NAME}")
        return True
    except Exception as e:
        print(f"⚠️ Failed to connect to MCP server: {e}")
        print("Continuing without MCP tools...")
        return False


async def connect_to_a2a_server(agent: LangGraphAgent) -> bool:
    """Connect to the A2A server and register agents.

    Args:
        agent: The LangGraphAgent instance to configure.

    Returns:
        bool: True if connection was successful, False otherwise.
    """
    try:
        print(f"\nConnecting to A2A server on port {A2A_SERVER_PORT}...")
        client_a2a_config = A2AClientConfig(
            discovery_urls=[f"http://localhost:{A2A_SERVER_PORT}"],
        )

        print("Discovering A2A agents...")
        agent_cards = agent.discover_agents(client_a2a_config)
        print(f"Discovered {len(agent_cards)} A2A agents")

        if not agent_cards:
            print("⚠️ No A2A agents discovered")
            return False

        print(f"Registering A2A agent: {agent_cards[0].name}")
        agent.register_a2a_agents(agent_cards)
        print("✅ Successfully registered A2A agent")
        return True

    except Exception as e:
        print(f"⚠️ Failed to connect to A2A server: {e}")
        print("Continuing without A2A tools...")
        return False


async def test_mcp_weather_tool(agent: LangGraphAgent) -> None:
    """Test the MCP weather tool if available.

    Args:
        agent: The configured LangGraphAgent instance.
    """
    print("\n=== Testing MCP Weather Tool ===")
    weather_query = "What's the weather forecast for tomorrow in London?"
    print(f"\nQuery: {weather_query}")
    try:
        response = await agent.arun(weather_query)
        print(f"✅ Response: {response.get('output', 'No output')}")
    except Exception as e:
        print(f"❌ Error testing MCP weather tool: {e}")


async def test_stock_agent(agent: LangGraphAgent) -> None:
    """Test the A2A Stock Agent if available.

    Args:
        agent: The configured LangGraphAgent instance.
    """
    print("\n=== Testing Stock Agent ===")
    stock_agent_tool = next((t for t in agent._tools if t.name == "StockAgent"), None)

    if not stock_agent_tool:
        print("⚠️ StockAgent tool not found in agent's tools")
        return

    stock_query = "What is the current stock price of AAPL?"
    print(f"\nQuery: {stock_query}")

    try:
        tool_input = {"query": "Get current stock price for AAPL"}
        response = await stock_agent_tool.arun(tool_input)
        print(f"✅ Response: {response}")
    except Exception as e:
        print(f"❌ Error testing Stock Agent: {e}")
        traceback.print_exc()


async def main():
    """Main function to run the A2A and MCP integration example."""
    try:
        # Create and configure agent
        agent, connected_servers = await create_agent()

        # Connect to servers
        connected_servers["mcp"] = await connect_to_mcp_server(agent)
        connected_servers["a2a"] = await connect_to_a2a_server(agent)

        # Verify at least one server is connected
        if not any(connected_servers.values()):
            print("❌ Error: Could not connect to any servers. Exiting...")
            sys.exit(1)

        # Run tests for connected services
        if connected_servers["mcp"]:
            await test_mcp_weather_tool(agent)
        else:
            print("\nSkipping MCP weather tool tests - MCP server not connected")

        if connected_servers["a2a"]:
            await test_stock_agent(agent)
        else:
            print("\nSkipping Stock Agent tests - A2A server not connected")

    except Exception as e:
        print(f"\nError: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
