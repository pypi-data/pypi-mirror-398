import re
from typing import Dict, List

from ..exceptions.epub_exceptions import TextProcessingError


class TextProcessor:
    """Text processing utility class"""

    @staticmethod
    def format_paragraphs(text: str) -> str:
        """Format paragraphs"""
        try:
            paragraphs = text.split("\n")
            formatted = "\n".join(
                f"<p>{p.strip()}</p>" for p in paragraphs if p.strip()
            )
            return formatted or "<p>This paragraph currently has no content.</p>"
        except Exception as e:
            raise TextProcessingError(f"Error formatting paragraphs: {e}")

    @staticmethod
    def clean_text(text: str) -> str:
        """Clean text content"""
        try:
            # Remove extra whitespace
            text = re.sub(r"\s+", " ", text)
            # Remove special control characters
            text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text)
            return text.strip()
        except Exception as e:
            raise TextProcessingError(f"Error cleaning text: {e}")

    @staticmethod
    def convert_tags(text: str) -> str:
        """Convert HTML tags to Chinese book title marks"""
        try:
            return re.sub(r"<(.*?)>", r"《\1》", text)
        except Exception as e:
            raise TextProcessingError(f"Error converting tags: {e}")
