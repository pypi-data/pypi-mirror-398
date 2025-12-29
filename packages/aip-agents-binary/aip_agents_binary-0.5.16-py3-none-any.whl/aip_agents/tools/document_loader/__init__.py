"""Document loader tools package.

This package provides tools for reading and extracting content from various document formats.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
    Douglas Raevan Faisal (douglas.raevan.faisal@gdplabs.id)

References:
    NONE
"""

try:
    from aip_agents.tools.document_loader.base_reader import (  # noqa: F401
        DOCPROC_AVAILABLE,
        DOCPROC_MISSING_MESSAGE,
        BaseDocumentReaderTool,
        DocumentReaderInput,
    )
    from aip_agents.tools.document_loader.docx_reader_tool import DocxReaderTool  # noqa: F401
    from aip_agents.tools.document_loader.excel_reader_tool import ExcelReaderTool  # noqa: F401
    from aip_agents.tools.document_loader.pdf_reader_tool import PDFReaderTool  # noqa: F401
    from aip_agents.tools.document_loader.pdf_splitter import PDFSplitter  # noqa: F401

    __all__ = [
        "BaseDocumentReaderTool",
        "DocumentReaderInput",
        "PDFReaderTool",
        "DocxReaderTool",
        "ExcelReaderTool",
        "PDFSplitter",
    ]
    if not DOCPROC_AVAILABLE:
        import warnings

        warnings.warn(DOCPROC_MISSING_MESSAGE, ImportWarning)
except ImportError:
    import warnings

    warnings.warn(
        "Document loader tools not available. Install gllm-docproc to enable them.",
        ImportWarning,
    )
    __all__ = []
