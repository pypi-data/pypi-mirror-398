"""Multi-Agent PII Demo Client - Tests PII handling across agent hierarchy.

This client demonstrates connecting to and using a hierarchical agent system
that manages PII across multiple specialist agents through A2A protocol.

To run this client:
1. First start the server:
   export NER_API_URL=http://localhost:8080
   export NER_API_KEY=your-api-key
   python aip_agents/examples/pii_demo_multi_agent_server.py

2. Then run this client:
   python aip_agents/examples/pii_demo_multi_agent_client.py

Authors:
    Fachriza Adhiatma (fachriza.d.adhiatma@gdplabs.id)
"""

import asyncio
from pprint import pprint

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from aip_agents.agent import LangGraphAgent
from aip_agents.schema.agent import A2AClientConfig

load_dotenv()


async def main():
    """Main function demonstrating the Multi-Agent PII Demo client."""
    llm = ChatOpenAI(model="gpt-4.1", streaming=True)

    # Create a simple client agent
    client_agent = LangGraphAgent(
        name="PIIMultiAgentTestClient",
        instruction=(
            "You are a test client that communicates with hierarchical agent systems via A2A. "
            "You will receive responses with PII tags - present them as-is."
        ),
        model=llm,
        tools=[],
    )

    # Discover the coordinator agent
    print("🔍 Discovering PIICoordinator agent...\n")
    config = A2AClientConfig(discovery_urls=["http://localhost:8003"])
    agent_cards = client_agent.discover_agents(config)
    client_agent.register_a2a_agents(agent_cards)
    print(f"✅ Found: {agent_cards[0].name}\n")

    # Example queries demonstrating multi-agent PII handling
    queries = [
        "I need information about customer <PERSON_1> and employee E001",
        "Find me information about customer <PERSON_1>, and then find information about employee E001, don't run tool in paralel",
    ]

    # Stream each query
    for i, query in enumerate(queries, 1):
        print(f"\n{'=' * 80}")
        print(f"Query {i}: {query}")
        print("=" * 80)
        print("\n📡 Streaming chunks:\n")

        try:
            async for chunk in client_agent.astream_to_agent(
                agent_card=agent_cards[0],
                message=query,
                pii_mapping={"<EMAIL_ADDRESS_1>": "john.smith@example.com", "<PERSON_1>": "C001"},
            ):
                pprint(chunk)
                print("-" * 50)

        except Exception as e:
            print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
