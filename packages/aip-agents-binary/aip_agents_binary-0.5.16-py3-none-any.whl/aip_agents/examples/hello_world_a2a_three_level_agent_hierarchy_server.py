#!/usr/bin/env python3
"""Three-Level Agent Hierarchy Server.

This server hosts a hierarchical agent system with three levels:
1. Level 1 (Coordinator): Main orchestrator agent that handles complex requests
2. Level 2 (Specialists): Domain-specific agents that handle specialized tasks
3. Level 3 (Workers): Task-specific agents that perform atomic operations

Architecture:
Coordinator Agent (A2A Server)
├── Research Specialist Agent
│   ├── Web Search Worker Agent
│   └── Data Analysis Worker Agent
└── Content Specialist Agent
    ├── Writing Worker Agent
    └── Formatting Worker Agent

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

import click
import uvicorn
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from aip_agents.agent import LangGraphAgent
from aip_agents.examples.tools.image_artifact_tool import ImageArtifactTool
from aip_agents.examples.tools.table_generator_tool import TableGeneratorTool
from aip_agents.utils.logger import get_logger

logger = get_logger(__name__)
load_dotenv()

SERVER_AGENT_NAME = "HierarchicalCoordinator"


def create_worker_agents(llm) -> tuple[LangGraphAgent, LangGraphAgent, LangGraphAgent, LangGraphAgent]:
    """Create Level 3 worker agents that perform atomic operations.

    Args:
        llm: The language model to use for the worker agents.

    Returns:
        tuple[LangGraphAgent, LangGraphAgent, LangGraphAgent, LangGraphAgent]: Tuple of (web_search_worker, data_analysis_worker, writing_worker, formatting_worker).
    """
    # Research Workers
    web_search_worker = LangGraphAgent(
        name="WebSearchWorker",
        instruction=(
            "You are a web search specialist. You excel at finding information online. "
            "When given a topic, provide comprehensive research findings with sources and key insights. "
            "Format your responses clearly with bullet points and structured information."
        ),
        model=llm,
        tools=[],
    )

    data_analysis_worker = LangGraphAgent(
        name="DataAnalysisWorker",
        instruction=(
            "You are a data analysis expert. You specialize in creating tables, charts, and analyzing patterns. "
            "Use the table_generator tool to create structured data representations. "
            "Always provide insights and interpretations of the data you generate."
        ),
        model=llm,
        tools=[TableGeneratorTool()],
    )

    # Content Workers
    writing_worker = LangGraphAgent(
        name="WritingWorker",
        instruction=(
            "You are a content writing specialist. You excel at creating engaging, well-structured content. "
            "Focus on clarity, readability, and meeting the specific requirements provided. "
            "Always maintain a professional yet engaging tone."
        ),
        model=llm,
        tools=[],
    )

    formatting_worker = LangGraphAgent(
        name="FormattingWorker",
        instruction=(
            "You are a formatting and presentation specialist. You excel at creating visual content. "
            "Use the image_generator tool to create visual elements and graphics. "
            "Focus on clean, professional layouts and visual appeal."
        ),
        model=llm,
        tools=[ImageArtifactTool()],
    )

    return web_search_worker, data_analysis_worker, writing_worker, formatting_worker


def create_specialist_agents(llm, worker_agents) -> tuple[LangGraphAgent, LangGraphAgent]:
    """Create Level 2 specialist agents that coordinate worker agents.

    Args:
        llm: The language model to use for the specialist agents.
        worker_agents: Tuple of worker agents from create_worker_agents function.

    Returns:
        tuple[LangGraphAgent, LangGraphAgent]: Tuple of (research_specialist, content_specialist).
    """
    web_search_worker, data_analysis_worker, writing_worker, formatting_worker = worker_agents

    research_specialist = LangGraphAgent(
        name="ResearchSpecialist",
        instruction=(
            "You are a research coordinator who manages research and data analysis tasks. "
            "You delegate web research to WebSearchWorker and data analysis to DataAnalysisWorker. "
            "For research requests, use WebSearchWorker to gather information. "
            "For data analysis or table creation requests, use DataAnalysisWorker. "
            "Synthesize results from your workers into comprehensive research reports."
        ),
        model=llm,
        agents=[web_search_worker, data_analysis_worker],
    )

    content_specialist = LangGraphAgent(
        name="ContentSpecialist",
        instruction=(
            "You are a content creation coordinator who manages writing and formatting tasks. "
            "You delegate writing tasks to WritingWorker and visual/formatting tasks to FormattingWorker. "
            "For text content requests, use WritingWorker to create written material. "
            "For visual content or formatting requests, use FormattingWorker. "
            "Ensure all content is cohesive and meets quality standards."
        ),
        model=llm,
        agents=[writing_worker, formatting_worker],
    )

    return research_specialist, content_specialist


def create_coordinator_agent(llm, specialist_agents) -> LangGraphAgent:
    """Create Level 1 coordinator agent that orchestrates everything.

    Args:
        llm: The language model to use for the coordinator agent.
        specialist_agents: Tuple of specialist agents from create_specialist_agents function.

    Returns:
        LangGraphAgent: The configured coordinator agent.
    """
    research_specialist, content_specialist = specialist_agents

    coordinator = LangGraphAgent(
        name=SERVER_AGENT_NAME,
        instruction=(
            "You are a hierarchical coordinator that manages complex multi-step projects. "
            "You oversee two specialist teams:\n"
            "- ResearchSpecialist: Handles research, data analysis, and information gathering\n"
            "- ContentSpecialist: Handles content creation, writing, and visual formatting\n\n"
            "For each request, analyze what needs to be done and delegate appropriately:\n"
            "- Research tasks -> ResearchSpecialist\n"
            "- Content creation tasks -> ContentSpecialist\n"
            "- Complex requests may require both specialists\n\n"
            "Always provide a comprehensive summary of the coordinated work and ensure "
            "all deliverables meet the user's requirements."
        ),
        model=llm,
        agents=[research_specialist, content_specialist],
    )

    return coordinator


@click.command()
@click.option("--host", "host", default="localhost", help="Host to bind the server to.")
@click.option("--port", "port", default=8888, help="Port to bind the server to.")
def main(host: str, port: int):
    """Runs the Three-Level Agent Hierarchy A2A server.

    Args:
        host (str): Host to bind the server to.
        port (int): Port to bind the server to.
    """
    logger.info(f"Starting {SERVER_AGENT_NAME} on http://{host}:{port}")

    agent_card = AgentCard(
        name=SERVER_AGENT_NAME,
        description=(
            "A hierarchical coordinator managing 3 levels of specialized agents for complex research and content tasks."
        ),
        url=f"http://{host}:{port}",
        version="1.0.0",
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[
            AgentSkill(
                id="hierarchical_coordination",
                name="Hierarchical Task Coordination",
                description="Coordinates complex multi-step projects across 3 levels of specialized agents.",
                examples=[
                    "Research market trends and create a presentation",
                    "Analyze data and write a comprehensive report",
                    "Create educational content with visuals and data tables",
                ],
                tags=["coordination", "hierarchy", "multi-level", "delegation"],
            ),
            AgentSkill(
                id="research_management",
                name="Research & Analysis Management",
                description="Manages research specialists and data analysis workers for information gathering.",
                examples=[
                    "Research renewable energy trends and create data tables",
                    "Analyze market competition and generate insights",
                    "Gather information on AI developments",
                ],
                tags=["research", "analysis", "data", "information"],
            ),
            AgentSkill(
                id="content_management",
                name="Content Creation Management",
                description="Manages content specialists and formatting workers for content creation.",
                examples=[
                    "Create engaging blog posts with visual elements",
                    "Develop training materials with graphics",
                    "Write reports with professional formatting",
                ],
                tags=["content", "writing", "formatting", "visual"],
            ),
        ],
        tags=["hierarchical", "coordination", "multi-agent", "complex-tasks"],
    )

    llm = ChatOpenAI(model="gpt-4.1", temperature=0, streaming=True)

    # Build the 3-level hierarchy
    logger.info("Creating Level 3 worker agents...")
    worker_agents = create_worker_agents(llm)

    logger.info("Creating Level 2 specialist agents...")
    specialist_agents = create_specialist_agents(llm, worker_agents)

    logger.info("Creating Level 1 coordinator agent...")
    coordinator_agent = create_coordinator_agent(llm, specialist_agents)

    app = coordinator_agent.to_a2a(agent_card=agent_card)

    logger.info("A2A application configured. Starting Uvicorn server...")
    logger.info("Hierarchy: 1 Coordinator -> 2 Specialists -> 4 Workers")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
