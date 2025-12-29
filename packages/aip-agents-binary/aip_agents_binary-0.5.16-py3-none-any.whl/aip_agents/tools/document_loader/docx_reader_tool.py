"""Base tool to read and extract text from document files.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)

References:
    https://github.com/GDP-ADMIN/gdplabs-exploration/blob/ai-agent-app/backend/aip_agents/tools/
      reader/docx_reader_tool.py
"""

try:
    from gllm_docproc.loader.docx import DOCX2PythonLoader, PythonDOCXTableLoader
except ImportError as exc:
    DOCX2PythonLoader = None  # type: ignore[assignment]
    PythonDOCXTableLoader = None  # type: ignore[assignment]
    _DOCPROC_IMPORT_ERROR: Exception | None = exc
else:
    _DOCPROC_IMPORT_ERROR = None

from aip_agents.tools.document_loader.base_reader import DOCPROC_MISSING_MESSAGE, BaseDocumentReaderTool
from aip_agents.utils.logger import get_logger

logger = get_logger(__name__)


class DocxReaderTool(BaseDocumentReaderTool):
    """Tool to read and extract text from Word documents."""

    name: str = "docx_reader_tool"
    description: str = "Read a Word document and extract its text content. Input should be the path to the Word file."

    def _setup_loader(self):
        if DOCX2PythonLoader is None or PythonDOCXTableLoader is None:
            logger.warning(DOCPROC_MISSING_MESSAGE)
            if _DOCPROC_IMPORT_ERROR is not None:
                logger.debug("gllm_docproc import failed: %s", _DOCPROC_IMPORT_ERROR)
            return
        self.loader.add_loader(DOCX2PythonLoader())
        self.loader.add_loader(PythonDOCXTableLoader())

    def _run_with_batching(self, file_path: str, batch_size: int) -> str:
        """Run without batching until DOCX splitting is implemented.

        Args:
            file_path: Path to the DOCX file to be processed
            batch_size: Number of pages to include in each batch (not used currently)

        Returns:
            Extracted text content from the document
        """
        # TODO: implement DOCX batching with real splits before enabling batching flow.
        return self._run_standard(file_path)

    def _split_file(self, file_path: str, batch_size: int) -> list[str]:
        """Split DOCX file into temporary files for batch processing.

        Note: This is a placeholder implementation. DOCX batching is not
        implemented in this feature but the method is required by the abstract base class.

        Args:
            file_path: Path to the DOCX file to be split
            batch_size: Number of pages to include in each split file

        Returns:
            List of temporary file paths containing the split content
        """
        # Placeholder implementation - DOCX batching not implemented in this feature
        return [file_path]
