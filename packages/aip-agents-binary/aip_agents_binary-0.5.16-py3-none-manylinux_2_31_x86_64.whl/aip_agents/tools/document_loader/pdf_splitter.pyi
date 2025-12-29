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
