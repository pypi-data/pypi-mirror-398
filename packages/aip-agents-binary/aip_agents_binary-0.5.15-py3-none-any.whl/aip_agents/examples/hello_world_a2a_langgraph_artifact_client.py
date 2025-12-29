"""Example of a General Assistant LangGraphAgent that can delegate tasks to specialized agents.

This example demonstrates:
1. Configuring A2A settings for a client agent.
2. Creating a general assistant agent that can help with various queries.
3. Delegating specific tasks to specialized agents via A2A.
4. Handling artifacts in the response.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

import asyncio
import base64

from langchain_openai import ChatOpenAI

from aip_agents.agent import LangGraphAgent
from aip_agents.schema.agent import A2AClientConfig


async def main():
    """Main function demonstrating the General Assistant agent with A2A capabilities."""
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
        discovery_urls=["http://localhost:8999"],
    )
    agent_cards = assistant_agent.discover_agents(client_a2a_config)

    # Test query
    query = "Generate a data table with 5 rows and 3 columns showing Name, Age, and City and Create a simple image."
    result = assistant_agent.send_to_agent(agent_card=agent_cards[0], message=query)
    print(f"Result: {result}")

    # Handle artifacts from result
    artifacts = result.get("artifacts", [])
    if artifacts:
        print(f"\n--- {len(artifacts)} Artifacts Received ---")
        for artifact in artifacts:
            name = artifact.get("name", "unknown")
            mime_type = artifact.get("mime_type", "unknown")
            file_data = artifact.get("file_data")

            print(f"Name: {name}")
            print(f"Type: {mime_type}")

            if file_data:
                try:
                    if mime_type == "text/csv":
                        decoded_content = base64.b64decode(file_data).decode("utf-8")
                        print(f"CSV Preview (first 200 chars): {decoded_content[:200]}...")
                    elif mime_type.startswith("image/"):
                        file_size = len(base64.b64decode(file_data))
                        print(f"Image size: {file_size} bytes")
                    else:
                        print("File data available (base64 encoded)")
                except Exception as e:
                    print(f"Could not decode file data: {e}")
            print("---")
        print("--- End Artifacts ---\n")


if __name__ == "__main__":
    asyncio.run(main())
