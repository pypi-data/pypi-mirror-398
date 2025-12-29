"""Tool to read and extract content from Excel files using gllm_docproc.

This tool uses the gllm_docproc loader pipeline to extract content from Excel files,
providing a consistent interface with other document reader tools (PDF, DOCX).

Authors:
    Douglas Raevan Faisal (douglas.raevan.faisal@gdplabs.id)
"""

import zipfile
from pathlib import Path

try:
    from gllm_docproc.loader.xlsx import OpenpyxlLoader
except ImportError as exc:
    OpenpyxlLoader = None  # type: ignore[assignment]
    _DOCPROC_IMPORT_ERROR: Exception | None = exc
else:
    _DOCPROC_IMPORT_ERROR = None

from aip_agents.tools.document_loader.base_reader import DOCPROC_MISSING_MESSAGE, BaseDocumentReaderTool
from aip_agents.utils.logger import get_logger

logger = get_logger(__name__)


class ExcelReaderTool(BaseDocumentReaderTool):
    """Tool to read and extract content from Excel files.

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
    """

    name: str = "excel_reader_tool"
    description: str = (
        "Read an Excel file and extract its content as Markdown tables. "
        "Input should be the path to the Excel file (.xlsx or .xlsm format). "
        "Each sheet will be formatted as a Markdown table with the sheet name as a header."
    )

    def _setup_loader(self) -> None:
        """Set up the XLSX loader for the pipeline.

        This method initializes the OpenpyxlLoader which handles extraction
        of content from Excel files and formatting as Markdown tables.
        """
        if OpenpyxlLoader is None:
            logger.warning(DOCPROC_MISSING_MESSAGE)
            if _DOCPROC_IMPORT_ERROR is not None:
                logger.debug("gllm_docproc import failed: %s", _DOCPROC_IMPORT_ERROR)
            return
        self.loader.add_loader(OpenpyxlLoader())

    def _run_with_batching(self, file_path: str, batch_size: int) -> str:
        """Run without batching until Excel splitting is implemented.

        Args:
            file_path: Path to the Excel file to be processed
            batch_size: Number of sheets to include in each batch (not used currently)

        Returns:
            Extracted text content from the document
        """
        # TODO: implement Excel batching with real splits before enabling batching flow.
        return self._run_standard(file_path)

    def _split_file(self, file_path: str, batch_size: int) -> list[str]:
        """Split Excel file for batch processing.

        Note: This is a placeholder implementation. Excel batching by sheets
        could be implemented in the future, but for now we process the entire
        file at once as Excel files are typically smaller than PDFs.

        Args:
            file_path: Path to the Excel file to be split
            batch_size: Number of sheets to include in each split file (not used currently)

        Returns:
            List containing the original file path (no splitting performed)
        """
        # Placeholder implementation - Excel batching not implemented
        # Excel files are typically smaller and batching by sheets would require
        # more complex logic to split workbooks
        logger.info(f"Excel batching not implemented, processing entire file: {file_path}")
        return [file_path]

    def _validate_excel_file(self, file_path: str) -> str | None:
        """Validate Excel file and check for potential issues.

        Args:
            file_path: Path to the Excel file

        Returns:
            Error message if validation fails, None if successful
        """
        path = Path(file_path)

        # Check file extension
        if path.suffix.lower() not in [".xlsx", ".xlsm"]:
            return f"Invalid file extension: {path.suffix}. Only .xlsx and .xlsm files are supported."

        # Check for macro-enabled files and warn
        if path.suffix.lower() == ".xlsm":
            logger.warning(f"Macro-enabled file detected: {file_path}")
            # Check if file actually contains macros
            try:
                with zipfile.ZipFile(file_path, "r") as zip_file:
                    if "xl/vbaProject.bin" in zip_file.namelist():
                        logger.warning(
                            f"VBA macros found in {file_path}. "
                            f"Macros will not be executed; only data will be extracted."
                        )
            except Exception as e:
                logger.debug(f"Could not check for macros: {e}")

        return None

    def _run_standard(self, file_path: str) -> str:
        """Override standard processing to add Excel-specific error handling.

        Args:
            file_path: Path to the Excel file to be read

        Returns:
            Extracted text content from the document
        """
        # Validate Excel file
        validation_error = self._validate_excel_file(file_path)
        if validation_error:
            return f"Validation Error: {validation_error}"

        try:
            return self._process_single_file(file_path)

        except PermissionError:
            return f"Error: Permission denied accessing file: {file_path}"

        except zipfile.BadZipFile:
            return (
                "Error: File appears to be corrupted or is not a valid Excel format. "
                "Please check the file and try again."
            )

        except Exception as e:
            error_msg = str(e).lower()

            # Check for specific Excel errors
            if "password" in error_msg or "encrypted" in error_msg:
                return "Error: File is password-protected or encrypted. Please provide an unprotected file."

            elif "invalid" in error_msg or "corrupt" in error_msg:
                return "Error: File appears to be corrupted or invalid Excel format. Please verify the file integrity."

            elif "not supported" in error_msg or "unsupported" in error_msg:
                return f"Error: File contains unsupported features: {str(e)}"

            else:
                logger.exception(f"Unexpected error processing Excel file: {file_path}")
                return f"Error processing Excel file: {str(e)}"
