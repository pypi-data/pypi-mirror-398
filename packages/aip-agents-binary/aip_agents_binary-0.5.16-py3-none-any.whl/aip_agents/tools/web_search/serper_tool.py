"""Tool to search Google Serper API.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
    Raymond Christopher (raymond.christopher@gdplabs.id)
    Fachriza Adhiatma (fachriza.d.adhiatma@gdplabs.id)
"""

import json
from json import dumps
from typing import Any

from gllm_core.schema import Chunk
from langchain_community.utilities.google_serper import GoogleSerperAPIWrapper
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from aip_agents.utils.logger import get_logger

logger = get_logger(__name__)


class GoogleSerperInput(BaseModel):
    """Input schema for the GoogleSerperTool."""

    query: str = Field(..., description="Search query", min_length=1)


class GoogleSerperTool(BaseTool):
    """Tool to search Google Serper API."""

    name: str = "google_serper"
    description: str = """
    Useful for searching the web using the Google Serper API.
    Input should be a search query.
    """
    save_output_history: bool = Field(default=True)
    args_schema: type[BaseModel] = GoogleSerperInput
    api_wrapper: GoogleSerperAPIWrapper = Field(default_factory=GoogleSerperAPIWrapper, exclude=True)

    def _run(
        self,
        query: str,
    ) -> str:
        """Executes a query using the API wrapper and returns the result as a JSON string.

        Args:
            query (str): The query string to be executed.
            run_manager (Optional[CallbackManagerForToolRun], optional): An optional callback manager for the tool run.
                Defaults to None.

        Returns:
            str: The result of the query execution, serialized as a JSON string.
        """
        result = self.api_wrapper.results(query)
        return dumps(result)

    def _format_agent_reference(self, tool_output: str) -> list[Chunk]:
        """Format tool output into agent references.

        Args:
            tool_output (str): The output from the tool, which is expected to be a JSON string.

        Returns:
            list[Chunk]: Formatted tool output as agent references
        """
        # Parse the tool output if it's a string
        parsed_output = self._parse_tool_output(tool_output)
        if not parsed_output:
            return []

        formatted_chunks = []
        file_id_counter = 0

        for section_name, section_data in parsed_output.items():
            # Process only list-type sections
            if not isinstance(section_data, list):
                continue

            # Process each item in the section
            results = self._process_section_items(section_name, section_data, file_id_counter)
            formatted_chunks.extend(results["chunks"])
            file_id_counter = results["counter"]

        return formatted_chunks

    def _parse_tool_output(self, tool_output: str) -> dict[str, Any]:
        """Parses the tool output to ensure it is in dictionary format.

        This method attempts to convert string outputs to JSON dictionaries and handles
        potential JSON parsing errors gracefully.

        Args:
            tool_output (str): The output from a tool, which is expected to be a JSON string.

        Returns:
            dict[str, Any]: The parsed output as a dictionary. Returns an empty
            dictionary if parsing fails.
        """
        if isinstance(tool_output, str):
            try:
                return json.loads(tool_output)
            except json.JSONDecodeError:
                logger.warning("Error: Unable to parse tool_output as JSON when formatting agent references.")
                return {}
        return tool_output

    def _process_section_items(self, section_name: str, section_data: list[dict], start_counter: int) -> dict[str, Any]:
        """Process items from a specific section of search results and create chunks.

        Args:
            section_name (str): Name of the section being processed (e.g., 'organic', 'news').
            section_data (list): List of items to process from the section.
            start_counter (int): Initial counter value for chunk numbering.

        Returns:
            dict[str, Any]: Dictionary containing:
                - chunks (list): List of processed chunks extracted from the section items.
                - counter (int): Updated counter after processing all items.

        Raises:
            Exception: Logs errors that occur during processing of individual items.
        """
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
                logger.warning(f"Error processing {section_name} result: {e}")

        return {"chunks": chunks, "counter": counter}

    def _create_chunk_from_item(self, section_name: str, item: dict[str, Any], file_id: int) -> Chunk | None:
        """Creates a Chunk object from a search result item.

        This method extracts content and metadata from a search result item and creates
        a Chunk object. It prioritizes snippet over title for content and includes various
        metadata fields.

        Args:
            section_name (str): The name of the section this item belongs to.
            item (dict[str, Any]): The search result item containing information like
                snippet, title, and link.
            file_id (int): The ID of the file associated with this chunk.

        Returns:
            Optional[Chunk]: A Chunk object containing the extracted content and metadata,
                or None if the item lacks essential information (link or content).
        """
        # First check if link exists
        link = item.get("link")
        if not link:
            logger.warning(f"Skipping item {file_id} from {section_name} result: Missing link")
            return None

        # Then extract and check content
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
            "url": link,
            "start_index": 0,
            "end_index": 0,
        }

        return Chunk(content=content, metadata=metadata)
