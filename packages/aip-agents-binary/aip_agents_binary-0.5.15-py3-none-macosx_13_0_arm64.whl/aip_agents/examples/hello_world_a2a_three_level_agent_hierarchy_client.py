"""Three-Level Agent Hierarchy Client.

This client demonstrates connecting to and using a hierarchical agent system
that manages 3 levels of specialized agents through A2A protocol.

This client tests various scenarios:
1. Research-only tasks (Level 1 -> Level 2 Research -> Level 3 Workers)
2. Content-only tasks (Level 1 -> Level 2 Content -> Level 3 Workers)
3. Complex tasks requiring both research and content creation
4. Artifact generation across the hierarchy

To run this client:
1. First start the server: python examples/three_level_agent_hierarchy_server.py
2. Then run this client: python examples/three_level_agent_hierarchy_client.py

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

import asyncio
import base64

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from aip_agents.agent import LangGraphAgent
from aip_agents.schema.agent import A2AClientConfig

load_dotenv()


async def main():
    """Main function demonstrating the Three-Level Agent Hierarchy client."""
    llm = ChatOpenAI(model="gpt-4.1", streaming=True)

    # Create a simple client agent
    client_agent = LangGraphAgent(
        name="HierarchyTestClient",
        instruction="You are a test client that communicates with hierarchical agent systems via A2A.",
        model=llm,
        tools=[],
    )

    # Discover the hierarchical coordinator agent
    client_a2a_config = A2AClientConfig(
        discovery_urls=["http://localhost:8888"],
    )

    print("=== Three-Level Agent Hierarchy Client ===\n")
    print("Discovering hierarchical coordinator...")

    try:
        agent_cards = client_agent.discover_agents(client_a2a_config)
        if not agent_cards:
            print("No agents found. Make sure the server is running on http://localhost:9000")
            print("Start server with: python examples/three_level_agent_hierarchy_server.py")
            return

        coordinator_card = agent_cards[0]
        print(f"Found coordinator: {coordinator_card.name}")
        print(f"Description: {coordinator_card.description}")
        print(f"Skills: {len(coordinator_card.skills)} available")
        print()

        # Run test scenarios
        await test_research_task(client_agent, coordinator_card)
        await test_content_task(client_agent, coordinator_card)
        await test_complex_task(client_agent, coordinator_card)
        await test_artifact_generation(client_agent, coordinator_card)

    except Exception as e:
        print(f"Error connecting to coordinator: {e}")
        print("Make sure the server is running: python examples/three_level_agent_hierarchy_server.py")


async def test_research_task(client_agent, coordinator_card):
    """Test a research-only task that flows through research specialists and workers.

    Args:
        client_agent: The client agent to send the query with.
        coordinator_card: The agent card of the hierarchical coordinator.
    """
    print("--- Test 1: Research Task (Research Specialist -> Data Analysis Worker) ---")
    query = (
        "Research the current trends in renewable energy and create a data table showing "
        "the top 5 technologies with their growth rates and market share."
    )

    print(f"Query: {query}\n")

    result = client_agent.send_to_agent(agent_card=coordinator_card, message=query)
    print(f"Response: {result.get('content', 'No content')}")

    handle_artifacts(result, "Research Task")
    print("\n" + "=" * 80 + "\n")


async def test_content_task(client_agent, coordinator_card):
    """Test a content-only task that flows through content specialists and workers.

    Args:
        client_agent: The client agent to send the query with.
        coordinator_card: The agent card of the hierarchical coordinator.
    """
    print("--- Test 2: Content Creation Task (Content Specialist -> Writing + Formatting Workers) ---")
    query = (
        "Create an engaging blog post about the benefits of remote work, and include "
        "a professional header image with the title 'Future of Work'."
    )

    print(f"Query: {query}\n")

    result = client_agent.send_to_agent(agent_card=coordinator_card, message=query)
    print(f"Response: {result.get('content', 'No content')}")

    handle_artifacts(result, "Content Creation Task")
    print("\n" + "=" * 80 + "\n")


async def test_complex_task(client_agent, coordinator_card):
    """Test a complex task requiring both research and content specialists.

    Args:
        client_agent: The client agent to send the query with.
        coordinator_card: The agent card of the hierarchical coordinator.
    """
    print("--- Test 3: Complex Multi-Level Task (Both Specialists + All Workers) ---")
    query = (
        "Research the impact of AI on healthcare, analyze the data to create a table showing "
        "AI applications and their adoption rates, then write a comprehensive report and "
        "create visual elements including charts and professional graphics."
    )

    print(f"Query: {query}\n")

    result = client_agent.send_to_agent(agent_card=coordinator_card, message=query)
    print(f"Response: {result.get('content', 'No content')}")

    handle_artifacts(result, "Complex Multi-Level Task")
    print("\n" + "=" * 80 + "\n")


async def test_artifact_generation(client_agent, coordinator_card):
    """Test artifact generation across the hierarchy.

    Args:
        client_agent: The client agent to send the query with.
        coordinator_card: The agent card of the hierarchical coordinator.
    """
    print("--- Test 4: Multi-Artifact Generation (Testing All Workers) ---")
    query = (
        "Create a complete analysis package: research cloud computing trends, "
        "generate data tables with market statistics, write executive summary, "
        "and create professional presentation graphics including charts and title slides."
    )

    print(f"Query: {query}\n")

    result = client_agent.send_to_agent(agent_card=coordinator_card, message=query)
    print(f"Response: {result.get('content', 'No content')}")

    handle_artifacts(result, "Multi-Artifact Generation")
    print("\n" + "=" * 80 + "\n")


def handle_artifacts(result, test_name):
    """Handle and display information about artifacts from the result.

    Args:
        result: The result from the agent containing artifacts.
        test_name: The name of the test for display purposes.
    """
    artifacts = result.get("artifacts", [])
    if artifacts:
        print(f"\n--- {len(artifacts)} Artifacts Generated by {test_name} ---")
        for i, artifact in enumerate(artifacts, 1):
            print(f"Artifact {i}:")
            print_artifact_info(artifact)
        print("--- End Artifacts ---")
    else:
        print(f"No artifacts generated for {test_name}")


def print_artifact_info(artifact: dict) -> None:
    """Print information about an artifact.

    Args:
        artifact: Dictionary containing artifact information.
    """
    name = artifact.get("name", "unknown")
    mime_type = artifact.get("mime_type", "unknown")
    file_data = artifact.get("file_data")
    description = artifact.get("description", "No description")

    print(f"  Name: {name}")
    print(f"  Type: {mime_type}")
    print(f"  Description: {description}")

    if file_data:
        try:
            if mime_type == "text/csv":
                decoded_content = base64.b64decode(file_data).decode("utf-8")
                lines = decoded_content.split("\n")
                print(f"  CSV Content ({len(lines)} lines):")
                # Show first few lines
                MAX_PREVIEW_LINES = 3
                for _i, line in enumerate(lines[:MAX_PREVIEW_LINES]):
                    if line.strip():
                        print(f"    {line}")
                if len(lines) > MAX_PREVIEW_LINES:
                    print(f"    ... and {len(lines) - MAX_PREVIEW_LINES} more lines")
            elif mime_type.startswith("image/"):
                file_size = len(base64.b64decode(file_data))
                print(f"  Image size: {file_size} bytes")
                print(f"  Image format: {mime_type}")
            else:
                data_size = len(file_data)
                print(f"  File data size: {data_size} characters (base64 encoded)")
        except Exception as e:
            print(f"  Could not decode file data: {e}")
    else:
        print("  No file data available")
    print()


def print_hierarchy_info():
    """Print information about the 3-level hierarchy being tested."""
    print("=== Agent Hierarchy Structure ===")
    print("Level 1: HierarchicalCoordinator")
    print("├── Level 2: ResearchSpecialist")
    print("│   ├── Level 3: WebSearchWorker")
    print("│   └── Level 3: DataAnalysisWorker (with table_generator)")
    print("└── Level 2: ContentSpecialist")
    print("    ├── Level 3: WritingWorker")
    print("    └── Level 3: FormattingWorker (with image_generator)")
    print("\nTask Flow:")
    print("Client -> Coordinator -> Specialist -> Worker -> Results")
    print("=" * 50)
    print()


if __name__ == "__main__":
    print_hierarchy_info()
    asyncio.run(main())
