from _typeshed import Incomplete
from aip_agents.tools.document_loader.base_reader import BaseDocumentReaderTool as BaseDocumentReaderTool, DOCPROC_MISSING_MESSAGE as DOCPROC_MISSING_MESSAGE
from aip_agents.utils.logger import get_logger as get_logger

logger: Incomplete

class ExcelReaderTool(BaseDocumentReaderTool):
    '''Tool to read and extract content from Excel files.

    This tool reads Excel files (.xlsx, .xlsm) and extracts their content using
    the gllm_docproc loader pipeline. The content is formatted as Markdown tables
    for easy readability.

    Features:
    - Supports .xlsx and .xlsm formats
    - Extracts all sheets or specific sheets
    - Formats output as Markdown tables
    - Configurable row limits and file size limits

    Examples:
        >>> tool = ExcelReaderTool()
        >>> result = tool._run("/tmp/data.xlsx")
        >>> print(result)
    '''
    name: str
    description: str
