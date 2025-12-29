"""Tool to read and extract text from PDF files.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)

References:
    https://github.com/GDP-ADMIN/gdplabs-exploration/blob/ai-agent-app/backend/aip_agents/tools/
      reader/pdf_reader_tool.py
"""

try:
    from gllm_docproc.loader.pdf import PDFPlumberLoader, PyMuPDFLoader
except ImportError as exc:
    PDFPlumberLoader = None  # type: ignore[assignment]
    PyMuPDFLoader = None  # type: ignore[assignment]
    _DOCPROC_IMPORT_ERROR: Exception | None = exc
else:
    _DOCPROC_IMPORT_ERROR = None

from aip_agents.tools.document_loader.base_reader import DOCPROC_MISSING_MESSAGE, BaseDocumentReaderTool
from aip_agents.tools.document_loader.pdf_splitter import PDFSplitter
from aip_agents.utils.logger import get_logger

logger = get_logger(__name__)


class PDFReaderTool(BaseDocumentReaderTool):
    """Tool to read and extract text from PDF files."""

    name: str = "pdf_reader_tool"
    description: str = "Read a PDF file and extract its text content. Input should be the path to the PDF file."

    def _setup_loader(self):
        if PDFPlumberLoader is None or PyMuPDFLoader is None:
            logger.warning(DOCPROC_MISSING_MESSAGE)
            if _DOCPROC_IMPORT_ERROR is not None:
                logger.debug("gllm_docproc import failed: %s", _DOCPROC_IMPORT_ERROR)
            return
        self.loader.add_loader(PyMuPDFLoader())
        self.loader.add_loader(PDFPlumberLoader())

    def _split_file(self, file_path: str, batch_size: int) -> list[str]:
        """Split PDF file into temporary files for batch processing.

        This method uses PDFSplitter.split_by_pages to split the PDF into
        temporary files containing the specified number of pages per batch.

        Args:
            file_path: Path to the PDF file to be split
            batch_size: Number of pages to include in each split file (1-10)

        Returns:
            List of temporary file paths containing the split content

        Raises:
            FileNotFoundError: If the input PDF file doesn't exist
            ValueError: If batch_size is invalid or PDF processing fails
            RuntimeError: For other unexpected errors during PDF splitting
        """
        logger.info(f"Splitting PDF file '{file_path}' with batch_size={batch_size}")

        try:
            # Use PDFSplitter utility to split the PDF by pages
            temp_files = PDFSplitter.split_by_pages(file_path, batch_size)

            logger.info(f"Successfully split PDF into {len(temp_files)} batch files")
            logger.debug(f"Created temporary files: {temp_files}")

            return temp_files

        except FileNotFoundError:
            logger.error(f"PDF file not found: {file_path}")
            raise
        except ValueError as e:
            logger.error(f"Invalid parameters or corrupted PDF: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error splitting PDF '{file_path}': {str(e)}")
            raise RuntimeError(f"Failed to split PDF file: {str(e)}") from e
