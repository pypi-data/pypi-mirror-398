"""PDF splitting utility for batching optimization.

Authors
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

import os
import tempfile

from PyPDF2 import PdfReader, PdfWriter


class PDFSplitter:
    """Utility class for splitting PDF files into page-based temporary files."""

    @staticmethod
    def split_by_pages(file_path: str, batch_size: int) -> list[str]:
        """Split PDF into temporary files containing batch_size pages each.

        Args:
            file_path: Path to the PDF file to split
            batch_size: Number of pages to include in each batch (1-10)

        Returns:
            List of temporary file paths containing the split PDF batches

        Raises:
            FileNotFoundError: If the input PDF file doesn't exist
            ValueError: If batch_size is invalid or PDF is corrupted
            Exception: For other PDF processing errors
        """
        PDFSplitter._validate_inputs(file_path, batch_size)

        try:
            reader = PdfReader(file_path)
            PDFSplitter._validate_pdf_content(reader, file_path)

            temp_files = []

            # Split PDF into batches
            for i in range(0, len(reader.pages), batch_size):
                batch_number = i // batch_size + 1
                temp_path = PDFSplitter._create_batch_file(reader, i, batch_size, batch_number, temp_files)
                temp_files.append(temp_path)

            return temp_files

        except Exception as e:
            # Handle corrupted or invalid PDF files
            if "temp_files" in locals():
                PDFSplitter._cleanup_temp_files(temp_files)

            if isinstance(e, FileNotFoundError | ValueError):
                raise
            else:
                raise ValueError(f"Error processing PDF file {file_path}: {str(e)}") from e

    @staticmethod
    def _validate_inputs(file_path: str, batch_size: int) -> None:
        """Validate input parameters.

        Args:
            file_path: Path to the PDF file to validate
            batch_size: Batch size to validate

        Raises:
            FileNotFoundError: If the input PDF file doesn't exist
            ValueError: If batch_size is invalid
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {file_path}")

    @staticmethod
    def _validate_pdf_content(reader: PdfReader, file_path: str) -> None:
        """Validate PDF content has pages.

        Args:
            reader: PdfReader instance to validate
            file_path: Path to the PDF file for error messages

        Raises:
            ValueError: If PDF has no pages
        """
        if len(reader.pages) == 0:
            raise ValueError(f"PDF file has no pages: {file_path}")

    @staticmethod
    def _create_batch_file(
        reader: PdfReader,
        start_page: int,
        batch_size: int,
        batch_number: int,
        temp_files: list[str],
    ) -> str:
        """Create a temporary file containing a batch of PDF pages.

        Args:
            reader: PdfReader instance containing the source pages
            start_page: Starting page index for this batch
            batch_size: Number of pages to include in the batch
            batch_number: Batch number for file naming
            temp_files: List of existing temp files for cleanup on error

        Returns:
            Path to the created temporary file

        Raises:
            ValueError: If page processing or file writing fails
        """
        writer = PdfWriter()

        # Add pages to this batch
        batch_end = min(start_page + batch_size, len(reader.pages))
        for j in range(start_page, batch_end):
            try:
                writer.add_page(reader.pages[j])
            except Exception as e:
                # Clean up any created temp files before re-raising
                PDFSplitter._cleanup_temp_files(temp_files)
                raise ValueError(f"Error processing page {j + 1}: {str(e)}") from e

        # Create and write temporary file
        return PDFSplitter._write_batch_to_temp_file(writer, batch_number, temp_files)

    @staticmethod
    def _write_batch_to_temp_file(writer: PdfWriter, batch_number: int, temp_files: list[str]) -> str:
        """Write a PDF batch to a temporary file.

        Args:
            writer: PdfWriter instance containing the batch pages
            batch_number: Batch number for file naming
            temp_files: List of existing temp files for cleanup on error

        Returns:
            Path to the created temporary file

        Raises:
            ValueError: If file writing fails
        """
        # Create temporary file with proper naming
        temp_fd, temp_path = tempfile.mkstemp(suffix=f"_batch_{batch_number}.pdf", prefix="pdf_split_")

        try:
            with os.fdopen(temp_fd, "wb") as temp_file:
                writer.write(temp_file)
            return temp_path
        except Exception as e:
            # Close the file descriptor if write fails
            try:
                os.close(temp_fd)
            except OSError:
                pass
            # Clean up any created temp files
            PDFSplitter._cleanup_temp_files(temp_files)
            raise ValueError(f"Error writing batch {batch_number}: {str(e)}") from e

    @staticmethod
    def _cleanup_temp_files(temp_files: list[str]) -> None:
        """Clean up temporary files.

        Args:
            temp_files: List of temporary file paths to clean up
        """
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except OSError:
                pass
