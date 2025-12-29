"""Base document reader tool.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)

References:
    https://github.com/GDP-ADMIN/gdplabs-exploration/blob/ai-agent-app/backend/aip_agents/tools/reader/base_reader.py
"""

import gc
import os
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from unidecode import unidecode

from aip_agents.utils.logger import get_logger

logger = get_logger(__name__)

DOCPROC_MISSING_MESSAGE = (
    "gllm-docproc is required for document loader tools but is not installed. "
    "Install it from your internal registry to enable document processing."
)

try:
    from gllm_docproc.loader.pipeline_loader import PipelineLoader
except ImportError:
    PipelineLoader = None  # type: ignore[assignment]

if TYPE_CHECKING:
    from gllm_docproc.loader.pipeline_loader import PipelineLoader as PipelineLoaderType
else:
    PipelineLoaderType = Any


class _MissingDocprocLoader:
    """Fallback loader that errors when document processing is attempted."""

    def __init__(self) -> None:
        self.loaders: list[object] = []

    def add_loader(self, loader: object) -> None:
        self.loaders.append(loader)

    def load(self, *_args: object, **_kwargs: object) -> list[dict[str, str]]:
        raise ImportError(DOCPROC_MISSING_MESSAGE)

    def clear_cache(self) -> None:
        self.loaders.clear()


def _build_pipeline_loader() -> "PipelineLoader":
    if PipelineLoader is None:
        return _MissingDocprocLoader()
    return PipelineLoader()  # type: ignore[misc]


DOCPROC_AVAILABLE = PipelineLoader is not None


class BaseDocumentConfig(BaseModel):
    """Base tool configuration schema for document processing with batching functionality.

    This configuration enables page-by-page batching to optimize memory usage when
    processing large document files. When batching is enabled, documents are processed
    sequentially by pages rather than loading the entire document into memory at once.

    Attributes:
        batching (bool): Enable page-by-page batching to reduce memory usage.
            When True, documents are processed page by page sequentially.
            When False, maintains current behavior of loading entire document.
            Defaults to False for backward compatibility.
        batch_size (int): Number of pages to process in each batch.
            Must be between 1 and 100 pages inclusive.
            Larger batch sizes may use more memory but could be more efficient.
            Smaller batch sizes use less memory but may have more overhead.
            Defaults to 10 for balanced memory usage and efficiency.

    Examples:
        >>> # Default configuration (no batching)
        >>> config = BaseDocumentConfig()
        >>> print(config.batching)  # False
        >>> print(config.batch_size)  # 10

        >>> # Enable batching with single page processing
        >>> config = BaseDocumentConfig(batching=True, batch_size=1)

        >>> # Enable batching with multi-page batches
        >>> config = BaseDocumentConfig(batching=True, batch_size=3)
    """

    batching: bool = Field(
        default=False,
        description="Enable page-by-page batching to reduce memory usage when processing large documents",
    )
    batch_size: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Number of pages to process per batch (1-100 pages)",
    )


class DocumentReaderInput(BaseModel):
    """Input schema for the DocumentReader tool."""

    file_path: str = Field(..., description="Path to the document file to be read")


class BaseDocumentReaderTool(BaseTool, ABC):
    """Base tool to read and extract text from document files."""

    name: str = "base_document_reader_tool"
    description: str = "Read a document file and extract its text content."
    args_schema: type[BaseModel] = DocumentReaderInput
    tool_config_schema: type[BaseModel] = BaseDocumentConfig
    loader: PipelineLoaderType = Field(default_factory=_build_pipeline_loader)

    def __init__(self):
        """Initialize the base document reader tool."""
        super().__init__()
        self._setup_loader()

    @abstractmethod
    def _setup_loader(self):
        """Set up the specific loaders for each document type."""
        pass  # pragma: no cover

    def _run(self, file_path: str, config: RunnableConfig | None = None) -> str:
        """Run with optional batching based on configuration.

        Args:
            file_path: Path to the document file to be read
            config: Optional RunnableConfig containing tool configuration

        Returns:
            Extracted text content from the document
        """
        tool_config = None
        if hasattr(self, "get_tool_config"):
            tool_config = self.get_tool_config(config)

        tool_config = tool_config or BaseDocumentConfig()

        logger.info(f"Batching: {tool_config.batching}, Batch size: {tool_config.batch_size}")
        if tool_config.batching:
            return self._run_with_batching(file_path, tool_config.batch_size)
        else:
            return self._run_standard(file_path)

    def _run_standard(self, file_path: str) -> str:
        """Standard processing (existing behavior).

        Args:
            file_path: Path to the document file to be read

        Returns:
            Extracted text content from the document
        """
        try:
            return self._process_single_file(file_path)
        except Exception as e:
            return f"Error reading file: {str(e)}"

    def _run_with_batching(self, file_path: str, batch_size: int) -> str:
        """Process file using batching with existing loader.

        Args:
            file_path: Path to the document file to be read
            batch_size: Number of pages to process per batch

        Returns:
            Extracted text content from the document
        """
        try:
            logger.info(f"Splitting file: {file_path} into {batch_size} pages per batch")
            split_files = self._split_file(file_path, batch_size)
            return self._process_file_batch(split_files)
        except Exception as e:
            return f"Error reading file: {str(e)}"

    def _process_single_file(self, file_path: str) -> str:
        """Process a single file and return extracted text.

        Args:
            file_path: Path to the document file to be read

        Returns:
            Extracted text content from the document (ASCII-normalized)
        """
        try:
            # Load and process the file
            loaded_elements = self.loader.load(file_path)
            full_text = "\n".join(element["text"] for element in loaded_elements)

            # Apply unidecode to convert non-ASCII characters to ASCII equivalents
            # This prevents encoding errors by transliterating characters like:
            # "Café" -> "Cafe", "François" -> "Francois", "北京" -> "Bei Jing"
            result = unidecode(full_text).strip()

            # Explicit memory cleanup
            del loaded_elements
            del full_text

            # Force garbage collection to free memory immediately
            gc.collect()

            return result

        except Exception:
            # Ensure cleanup even on error
            gc.collect()
            raise

    def _process_file_batch(self, split_files: list[str]) -> str:
        """Process a batch of split files and return combined text.

        Args:
            split_files: List of temporary file paths to process

        Returns:
            Combined extracted text content from all files
        """
        results = []
        errors = []

        for split_file in split_files:
            try:
                text = self._process_single_file(split_file)
                results.append(text)

                # Clear the text variable to free memory immediately
                del text

            except Exception as e:
                error_msg = f"Error processing batch: {str(e)}"
                errors.append(error_msg)
            finally:
                self._cleanup_temp_file(split_file)
                # Force garbage collection after each file to minimize memory usage
                gc.collect()

        # Combine results
        full_text = "\n".join(results).strip()

        # Clear intermediate results to free memory
        del results
        gc.collect()

        if errors:
            error_summary = f"\n\nProcessing completed with {len(errors)} errors:\n" + "\n".join(errors)
            full_text += error_summary

        return full_text

    def _cleanup_temp_file(self, file_path: str) -> None:
        """Clean up temporary file.

        Args:
            file_path: Path to the temporary file to clean up
        """
        try:
            os.unlink(file_path)
        except OSError:
            pass

    def cleanup_memory(self) -> None:
        """Explicitly clean up memory and force garbage collection.

        This method can be called after processing to minimize memory usage.
        While it won't reset memory to exactly 0, it will free up as much
        memory as possible by clearing internal caches and forcing garbage collection.
        """
        # Clear any cached data in the loader if it has a cleanup method
        if hasattr(self.loader, "clear_cache"):
            self.loader.clear_cache()

        # Force garbage collection multiple times to ensure cleanup
        for _ in range(3):
            gc.collect()

        # Optional: Clear loader entirely and reinitialize (more aggressive)
        # This is commented out as it may affect performance for subsequent calls
        # self.loader = PipelineLoader()
        # self._setup_loader()

    @abstractmethod
    def _split_file(self, file_path: str, batch_size: int) -> list[str]:
        """Split file into temporary files for batch processing.

        Args:
            file_path: Path to the document file to be split
            batch_size: Number of pages to include in each split file

        Returns:
            List of temporary file paths containing the split content
        """
        pass  # pragma: no cover
