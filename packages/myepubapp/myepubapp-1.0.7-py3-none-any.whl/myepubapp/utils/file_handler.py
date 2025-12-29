from pathlib import Path
from typing import TYPE_CHECKING

from ..exceptions.epub_exceptions import FileHandlerError
from .logger import setup_logger

if TYPE_CHECKING:
    from ..core.book import Book

logger = setup_logger()


class FileHandler:
    """Utility class for handling file operations"""

    def read_file(self, file_path: str) -> str:
        """Read text file"""
        try:
            path = Path(file_path)
            if not path.exists():
                raise FileHandlerError(f"File does not exist: {file_path}")

            with path.open("r", encoding="utf-8") as f:
                content = f.read()

            logger.info(f"Successfully read file: {file_path}")
            return content

        except Exception as e:
            raise FileHandlerError(f"Error reading file: {e}")

    def write_epub(self, output_path: str, book: "Book") -> None:
        """Write EPUB file"""
        try:
            from ebooklib import epub

            epub.write_epub(output_path, book._epub_book, {})
            logger.info(f"Successfully wrote EPUB file: {output_path}")

        except Exception as e:
            raise FileHandlerError(f"Error writing EPUB file: {e}")

    @staticmethod
    def ensure_directory(file_path: str) -> None:
        """Ensure target directory exists"""
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
