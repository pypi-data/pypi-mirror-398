"""Example demonstrating basic Langflow agent usage.

This example shows how to create and use a LangflowAgent for both
synchronous and asynchronous execution modes.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

import asyncio
import os
import uuid

from dotenv import load_dotenv

from aip_agents.agent.langflow_agent import LangflowAgent
from aip_agents.clients.langflow import LangflowApiClient

load_dotenv()


async def fetch_flow_id() -> tuple[str, str]:
    """Fetch available flows and return the first flow ID and name."""
    print("Fetching available flows...")
    temp_client = LangflowApiClient(base_url="https://langflow.obrol.id", api_key=os.getenv("LANGFLOW_API_KEY"))

    try:
        flows = await temp_client.get_all_flows(remove_example_flows=True)
        print(flows)

        if not flows:
            print("❌ No flows found!")
            return "", ""

        print(f"Found {len(flows)} flows:")
        for i, flow in enumerate(flows[:5]):  # Show first 5 flows
            flow_name = flow.get("name", "Unnamed")
            flow_id = flow.get("id", "No ID")
            print(f"  {i + 1}. {flow_name} (ID: {flow_id})")

        selected_flow = flows[2]
        flow_id = selected_flow.get("id")
        flow_name = selected_flow.get("name", "Unknown Flow")

        if not flow_id:
            print("❌ Selected flow has no ID!")
            return "", ""

        print(f"✅ Selected flow: {flow_name} (ID: {flow_id})")
        print("-" * 50)
        return flow_id, flow_name

    except Exception as e:
        print(f"❌ Error fetching flows: {e}")
        print("Falling back to hardcoded flow ID...")
        return "6dd45ac0-5c05-44c1-9825-66c6c6e516f7", "Fallback Flow"


async def create_agent(flow_id: str, flow_name: str) -> LangflowAgent:
    """Create and configure the Langflow agent.

    Args:
        flow_id (str): The flow ID to use for the agent.
        flow_name (str): The name of the flow.

    Returns:
        LangflowAgent: The configured Langflow agent.
    """
    agent = LangflowAgent(
        name="HelloWorldLangflow",
        flow_id=flow_id,
        description=f"A Langflow agent using flow: {flow_name}",
        base_url="https://langflow.obrol.id",
    )

    print(f"Created agent: {agent.name}")
    print(f"Flow ID: {flow_id}")
    print(f"API Base URL: {agent.api_client.base_url}")

    # Test health check
    print("Testing health check...")
    is_healthy = await agent.health_check()
    print(f"API Health: {'✓ Healthy' if is_healthy else '✗ Unhealthy'}")
    print("-" * 50)

    return agent


async def demonstrate_regular_execution(agent: LangflowAgent) -> None:
    """Demonstrate regular execution.

    Args:
        agent (LangflowAgent): The Langflow agent to demonstrate with.
    """
    print("Example 1: Regular execution")
    result1 = await agent.arun("Hello, how are you?")
    print(f"Message 1: {result1}")
    print("-" * 50)


async def demonstrate_streaming(agent: LangflowAgent) -> None:
    """Demonstrate streaming execution.

    Args:
        agent (LangflowAgent): The Langflow agent to demonstrate with.
    """
    print("Example 2: Regular streaming")
    try:
        print("Streaming response:")
        async for chunk in agent.arun_stream("Hello, how are you?"):
            print(chunk)
        print()  # New line after streaming
    except Exception as e:
        print(f"Streaming Error: {e}")
    print("-" * 50)


async def demonstrate_session_management(agent: LangflowAgent) -> None:
    """Demonstrate session management.

    Args:
        agent (LangflowAgent): The Langflow agent to demonstrate with.
    """
    print("Example 3: Session management")
    session_id = f"conversation-{uuid.uuid4()}"
    try:
        # First message with thread_id
        result1 = await agent.arun("My name is Alice", configurable={"thread_id": session_id})
        print(f"Message 1: {result1}")

        # Second message in same thread - should remember context
        result2 = await agent.arun("What's my name?", configurable={"thread_id": session_id})
        print(f"Message 2: {result2}")

        # Third message in different thread - should not remember
        result3 = await agent.arun("What's my name?", configurable={"thread_id": f"new-conversation-{uuid.uuid4()}"})
        print(f"Message 3 (new thread): {result3}")

    except Exception as e:
        print(f"Session Error: {e}")
    print("-" * 50)


async def main():
    """Demonstrate basic Langflow agent usage."""
    # Fetch flow ID and name
    flow_id, flow_name = await fetch_flow_id()
    if not flow_id:
        return

    # Create agent
    agent = await create_agent(flow_id, flow_name)

    # Run demonstrations
    await demonstrate_regular_execution(agent)
    await demonstrate_streaming(agent)
    await demonstrate_session_management(agent)

    print("Demo completed!")


if __name__ == "__main__":
    asyncio.run(main())
