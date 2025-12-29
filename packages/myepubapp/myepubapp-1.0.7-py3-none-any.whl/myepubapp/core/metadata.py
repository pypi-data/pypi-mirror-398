import uuid
import zipfile
from dataclasses import dataclass
from typing import Optional

from bs4 import BeautifulSoup


@dataclass
class Metadata:
    """Represents EPUB book metadata"""

    title: str
    language: str
    author: str
    identifier: Optional[str] = None

    def __post_init__(self) -> None:
        """Post-initialization processing"""
        if not self.identifier:
            self.identifier = str(uuid.uuid4())

    @classmethod
    def from_epub(cls, epub_file: zipfile.ZipFile) -> "Metadata":
        """Extract metadata from existing EPUB file"""
        try:
            # Read content.opf file
            opf_files = [name for name in epub_file.namelist()
                         if name.endswith(".opf")]
            if not opf_files:
                raise ValueError("OPF file not found")

            with epub_file.open(opf_files[0]) as f:
                content = f.read().decode("utf-8")
                soup = BeautifulSoup(content, "xml")

                # Extract necessary metadata
                metadata_tag = soup.find("metadata")
                if not metadata_tag:
                    raise ValueError("Metadata tag not found")

                # Extract title
                title = metadata_tag.find("dc:title")
                title = title.text if title else "Unknown Title"

                # Extract language
                language = metadata_tag.find("dc:language")
                language = language.text if language else "zh"

                # Extract author
                creator = metadata_tag.find("dc:creator")
                author = creator.text if creator else "Unknown Author"

                # Extract identifier
                identifier = metadata_tag.find("dc:identifier")
                identifier = identifier.text if identifier else str(
                    uuid.uuid4())

                return cls(
                    title=title, language=language, author=author, identifier=identifier
                )

        except Exception as e:
            raise ValueError(f"Error extracting metadata from EPUB: {e}")
