from _typeshed import Incomplete
from abc import ABC
from aip_agents.utils.logger import get_logger as get_logger
from gllm_docproc.loader.pipeline_loader import PipelineLoader as PipelineLoaderType
from langchain_core.tools import BaseTool
from pydantic import BaseModel
from typing import Any

logger: Incomplete
DOCPROC_MISSING_MESSAGE: str
PipelineLoaderType = Any

class _MissingDocprocLoader:
    """Fallback loader that errors when document processing is attempted."""
    loaders: list[object]
    def __init__(self) -> None: ...
    def add_loader(self, loader: object) -> None: ...
    def load(self, *_args: object, **_kwargs: object) -> list[dict[str, str]]: ...
    def clear_cache(self) -> None: ...

DOCPROC_AVAILABLE: Incomplete

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
    batching: bool
    batch_size: int

class DocumentReaderInput(BaseModel):
    """Input schema for the DocumentReader tool."""
    file_path: str

class BaseDocumentReaderTool(BaseTool, ABC):
    """Base tool to read and extract text from document files."""
    name: str
    description: str
    args_schema: type[BaseModel]
    tool_config_schema: type[BaseModel]
    loader: PipelineLoaderType
    def __init__(self) -> None:
        """Initialize the base document reader tool."""
    def cleanup_memory(self) -> None:
        """Explicitly clean up memory and force garbage collection.

        This method can be called after processing to minimize memory usage.
        While it won't reset memory to exactly 0, it will free up as much
        memory as possible by clearing internal caches and forcing garbage collection.
        """
