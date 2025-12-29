import re
from dataclasses import dataclass
from html import escape
from typing import Optional

from ebooklib import epub

from ..exceptions.epub_exceptions import ChapterError


@dataclass
class Chapter:
    """Represents a chapter in an EPUB book"""

    title: str
    content: str
    level: str  # h1, h2, h3, intro
    file_name: str
    chapter_id: Optional[str] = None
    volume: Optional[str] = None  # Volume name for hierarchical TOC

    def __post_init__(self) -> None:
        """Post-initialization processing"""
        if not self.chapter_id:
            self.chapter_id = f"chapter_{self.file_name.split('.')[0]}"

        if self.level not in ["h1", "h2", "h3", "intro"]:
            raise ChapterError(f"Invalid chapter level: {self.level}")

    def to_epub_item(self) -> epub.EpubHtml:
        """Convert to EpubHtml object"""
        try:
            chapter = epub.EpubHtml(
                title=self.title, file_name=self.file_name, lang="zh"
            )
            chapter.id = self.chapter_id
            chapter.content = self.to_html()
            return chapter
        except Exception as e:
            raise ChapterError(f"Error converting chapter to EPUB format: {e}")

    def to_html(self) -> str:
        """Generate chapter's HTML content"""
        # Only escape the title, content is already properly formatted
        # HTML from ContentGenerator
        escaped_title = escape(self.title, quote=False)

        # Handle different level types
        if self.level == "intro":
            title_tag = f"<h1>{escaped_title}</h1>"
        else:
            title_tag = f"<{self.level}>{escaped_title}</{self.level}>"

        html_content = f"""
        <html xmlns="http://www.w3.org/1999/xhtml">
        <head>
            <title>{escaped_title}</title>
        </head>
        <body>
            {title_tag}
            {self.content}
        </body>
        </html>
        """
        return html_content

    @classmethod
    def create_empty_chapter(cls, title: str, level: str = "h1") -> "Chapter":
        """Create an empty chapter"""
        # Generate safe filename, avoid special characters
        safe_title = re.sub(r"[^\w\-_\.]", "_",
                            title.lower().replace(" ", "_"))
        return cls(
            title=title,
            content="<p>This chapter currently has no content.</p>",
            level=level,
            file_name=f"chapter_{safe_title}.xhtml",
        )
