from aip_agents.tools.document_loader.base_reader import BaseDocumentReaderTool as BaseDocumentReaderTool

class DocxReaderTool(BaseDocumentReaderTool):
    """Tool to read and extract text from Word documents."""
    name: str
    description: str
