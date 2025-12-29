from _typeshed import Incomplete
from aip_agents.tools.document_loader.base_reader import BaseDocumentReaderTool as BaseDocumentReaderTool, DOCPROC_MISSING_MESSAGE as DOCPROC_MISSING_MESSAGE
from aip_agents.tools.document_loader.pdf_splitter import PDFSplitter as PDFSplitter
from aip_agents.utils.logger import get_logger as get_logger

logger: Incomplete

class PDFReaderTool(BaseDocumentReaderTool):
    """Tool to read and extract text from PDF files."""
    name: str
    description: str
