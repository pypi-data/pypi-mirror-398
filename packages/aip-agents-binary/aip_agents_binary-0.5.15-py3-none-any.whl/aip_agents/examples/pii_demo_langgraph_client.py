"""Streaming PII demo client - inspect streaming chunks in real-time.

To run:
    1. Start server:
       export NER_API_URL=http://localhost:8080
       export NER_API_KEY=your-api-key
       python examples/pii_demo_langgraph_server.py

    2. Run client:
       python examples/pii_demo_langgraph_client.py

Authors:
    Fachriza Adhiatma (fachriza.d.adhiatma@gdplabs.id)
"""

import asyncio
from pprint import pprint

from langchain_openai import ChatOpenAI

from aip_agents.agent import LangChainAgent
from aip_agents.schema.agent import A2AClientConfig


async def main():
    """Stream queries and inspect chunks with PII handling."""
    # Setup
    llm = ChatOpenAI(model="gpt-4.1", streaming=True)
    client_agent = LangChainAgent(
        name="PIIDemoClient",
        instruction="""You are a helpful assistant. When asked for customer, employee, or user info, delegate to the PII demo agent.
        You will receive output from tool in masked version, just write the response naturally without revealing or changing the masked values.""",
        model=llm,
    )

    # Discover agents
    print("🔍 Discovering agents...\n")
    config = A2AClientConfig(discovery_urls=["http://localhost:8002"])
    agent_cards = client_agent.discover_agents(config)
    client_agent.register_a2a_agents(agent_cards)
    print(f"✅ Found: {agent_cards[0].name}\n")

    # Example queries
    queries = [
        "Can you get me information about customers <PERSON_1> and <PERSON_2>?",
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
                pii_mapping={"<PERSON_1>": "C001", "<PERSON_2>": "C002"},
            ):
                pprint(chunk)
                print("-" * 50)

        except Exception as e:
            print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
