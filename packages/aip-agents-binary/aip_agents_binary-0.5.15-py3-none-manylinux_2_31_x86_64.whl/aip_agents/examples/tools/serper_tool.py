"""Tool to search Google Serper API.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
    Fachriza Adhiatma (fachriza.d.adhiatma@gdplabs.id)
"""

import json
import logging
from typing import Any

from gllm_core.schema import Chunk
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class GoogleSerperInput(BaseModel):
    """Input schema for the GoogleSerperTool."""

    query: str = Field(..., description="Search query")


class MockGoogleSerperTool(BaseTool):
    """Mock Tool to simulate Google Serper API results for testing."""

    name: str = "google_serper"
    description: str = """
    Useful for searching the web using the Google Serper API (mocked).
    Input should be a search query.
    """
    save_output_history: bool = True
    args_schema: type[BaseModel] = GoogleSerperInput

    def _run(self, query: str) -> str:
        """Return a hardcoded mock response as a JSON string.

        Args:
            query (str): The search query to process.

        Returns:
            str: JSON string containing mock search results.
        """
        normalized_query = query.lower()

        # Special-case oncology AI drug discovery queries so the agent
        # naturally sees stock-oriented company context and can call
        # stock tools (get_stock_price, get_stock_news) afterwards.
        if "oncology" in normalized_query or "drug discovery" in normalized_query:
            mock_result = {
                "organic": [
                    {
                        "title": "NVIDIA (NVDA) - AI infrastructure for healthcare and drug discovery",
                        "link": "https://nvidia.example.com/healthcare-ai",
                        "snippet": (
                            "NVIDIA (ticker: NVDA) provides GPU-accelerated platforms widely used in AI-driven "
                            "drug discovery and oncology research. Investors closely watch NVDA stock as demand "
                            "for healthcare and life-sciences AI workloads grows."
                        ),
                    },
                    {
                        "title": "Microsoft (MSFT) - Azure AI partnerships with pharma and oncology",
                        "link": "https://microsoft.example.com/azure-health",
                        "snippet": (
                            "Microsoft (MSFT) collaborates with leading pharma companies to apply Azure AI to "
                            "oncology and drug discovery workflows. Analysts frequently reference MSFT stock when "
                            "discussing enterprise AI in healthcare."
                        ),
                    },
                    {
                        "title": "Apple (AAPL) - Devices and AI ecosystems in digital health",
                        "link": "https://apple.example.com/health-ai",
                        "snippet": (
                            "Apple (AAPL) integrates AI into health and wellness features that support oncology "
                            "patients and clinical research. Market commentary often links AAPL stock to long-term "
                            "growth in digital health and AI."
                        ),
                    },
                ],
                "news": [
                    {
                        "title": "NVDA rallies on new healthcare AI partnerships",
                        "link": "https://news.example.com/nvda-oncology-ai",
                        "snippet": (
                            "NVIDIA (NVDA) announced expanded collaborations focused on oncology and AI-driven "
                            "drug discovery, prompting renewed interest in NVDA stock among growth investors."
                        ),
                    },
                    {
                        "title": "MSFT deepens AI oncology collaborations on Azure",
                        "link": "https://news.example.com/msft-azure-oncology",
                        "snippet": (
                            "Microsoft (MSFT) reported new Azure AI partnerships with oncology research centers, "
                            "and analysts highlighted MSFT stock as a key AI infrastructure play in healthcare."
                        ),
                    },
                    {
                        "title": "AAPL explores AI-enabled health insights for cancer care",
                        "link": "https://news.example.com/aapl-health-oncology",
                        "snippet": (
                            "Apple (AAPL) is reportedly piloting AI-enabled health features that could support "
                            "oncology patient monitoring, adding another angle to the long-term AAPL stock story."
                        ),
                    },
                ],
            }
        else:
            # Default mock result used for generic queries.
            mock_result = {
                "organic": [
                    {
                        "title": "NeoAI - Artificial Intelligence Research",
                        "link": "https://neoai.example.com/",
                        "snippet": (
                            "NeoAI is an AI research and deployment company. Our mission is to ensure that "
                            "artificial general intelligence benefits all of humanity."
                        ),
                    },
                    {
                        "title": "Wikipedia - NeoAI",
                        "link": "https://en.wikipedia.org/wiki/NeoAI",
                        "snippet": (
                            "NeoAI is a fictional artificial intelligence research organization consisting of the "
                            "for-profit NeoAI LP and its parent company, the non-profit NeoAI Foundation."
                        ),
                    },
                ],
                "news": [
                    {
                        "title": "NeoAI unveils new LLM model",
                        "link": "https://news.example.com/neoai-llm",
                        "snippet": (
                            "NeoAI has announced the release of NeoAI-LLM, a new large multimodal model that accepts "
                            "image and text inputs."
                        ),
                    }
                ],
            }

        return json.dumps(mock_result)

    def _format_agent_reference(self, tool_output: str) -> list[Chunk]:
        parsed_output = self._parse_tool_output(tool_output)
        if not parsed_output:
            return []
        formatted_chunks = []
        file_id_counter = 0
        for section_name, section_data in parsed_output.items():
            if not isinstance(section_data, list):
                continue
            results = self._process_section_items(section_name, section_data, file_id_counter)
            formatted_chunks.extend(results["chunks"])
            file_id_counter = results["counter"]
        return formatted_chunks

    def _parse_tool_output(self, tool_output: str) -> dict[str, Any]:
        if isinstance(tool_output, str):
            try:
                return json.loads(tool_output)
            except json.JSONDecodeError:
                logger.error("Error: Unable to parse tool_output as JSON when formatting agent references.")
                return {}
        return tool_output

    def _process_section_items(self, section_name: str, section_data: list[dict], start_counter: int) -> dict[str, Any]:
        chunks = []
        counter = start_counter
        for item in section_data:
            if not isinstance(item, dict):
                continue
            try:
                chunk = self._create_chunk_from_item(section_name, item, counter)
                if chunk:
                    chunks.append(chunk)
                    counter += 1
            except Exception as e:
                logger.error(f"Error processing {section_name} result: {e}")
        return {"chunks": chunks, "counter": counter}

    def _create_chunk_from_item(self, section_name: str, item: dict[str, Any], file_id: int) -> Chunk | None:
        link = item.get("link")
        if not link:
            logger.warning(f"Skipping item {file_id} from {section_name} result: Missing link")
            return None
        content = ""
        if "snippet" in item:
            content = item["snippet"]
        elif "title" in item:
            content = item["title"]
        if not content:
            logger.warning(f"Skipping item {file_id} from {section_name} result: Missing content")
            return None
        metadata = {
            "source": item.get("title", "Untitled Source"),
            "section_type": section_name,
            "source_type": "website",
            "title": item.get("title", "Untitled"),
            "link": link,
            "file_id": str(file_id),
        }
        return Chunk(content=content, metadata=metadata)
