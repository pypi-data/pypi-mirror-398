from dataclasses import dataclass, field
from typing import List, Optional

from ebooklib import epub
from bs4 import BeautifulSoup

from ..exceptions.epub_exceptions import EPUBError
from ..utils.logger import setup_logger
from .chapter import Chapter
from .metadata import Metadata

logger = None  # Will be initialized when needed
_debug_mode = False  # Class variable to track debug mode


def _get_logger():
    """Get or create logger with current debug mode"""
    global logger
    if logger is None:
        logger = setup_logger(debug=_debug_mode)
    return logger


def set_debug_mode(debug: bool) -> None:
    """Set debug mode for logging"""
    global _debug_mode, logger
    _debug_mode = debug
    # Reset logger so it gets recreated with new debug mode
    logger = None


@dataclass
class Book:
    """Core class representing an EPUB book"""

    metadata: Metadata
    chapters: List[Chapter] = field(default_factory=list)
    _epub_book: Optional[epub.EpubBook] = field(default=None, init=False)

    def __post_init__(self) -> None:
        """Initialize EPUB book object"""
        self._epub_book = epub.EpubBook()
        self._initialize_metadata()

    def _initialize_metadata(self) -> None:
        """Initialize book metadata"""
        self._epub_book.set_identifier(self.metadata.identifier)
        self._epub_book.set_title(self.metadata.title)
        self._epub_book.set_language(self.metadata.language)
        self._epub_book.add_author(self.metadata.author)

    def add_chapter(self, chapter: Chapter) -> None:
        """Add chapter to the book"""
        self.chapters.append(chapter)
        epub_chapter = chapter.to_epub_item()
        self._epub_book.add_item(epub_chapter)

    def add_cover(self, cover_path: str) -> None:
        """Add cover image to the book"""
        try:
            from pathlib import Path

            cover_file = Path(cover_path)
            if not cover_file.exists():
                _get_logger().warning(f"Cover image not found: {cover_path}")
                return

            # Read cover image
            with cover_file.open("rb") as f:
                cover_content = f.read()

            # Use ebooklib's set_cover method which handles everything properly
            self._epub_book.set_cover(
                "images/cover" + cover_file.suffix, cover_content)

            _get_logger().info(f"Cover image added: {cover_path}")

        except Exception as e:
            _get_logger().error(f"Error adding cover image: {e}")

    def generate_epub(self, output_path: str) -> None:
        """Generate final EPUB file"""
        try:
            # Add TOC and navigation
            self._add_toc_and_nav()

            # Set spine with proper structure
            self._set_spine()

            # Write EPUB file
            epub.write_epub(output_path, self._epub_book, {})
            _get_logger().info(
                f"Successfully generated EPUB file: {output_path}")

        except Exception as e:
            raise EPUBError(f"Error generating EPUB file: {e}")

    def _add_toc_and_nav(self) -> None:
        """Add table of contents and navigation to EPUB"""
        from ..generators.toc import TOCGenerator

        toc_generator = TOCGenerator()

        # Ensure chapters are in the correct order for EPUB generation
        # Separate chapters by type and ensure correct order
        original_chapters = []
        new_chapters = []
        intro_chapter = None

        for chapter in self.chapters:
            if chapter.level == "intro":
                intro_chapter = chapter
            elif chapter.chapter_id and chapter.chapter_id.startswith("chapter_"):
                # All chapter_xxx are considered original chapters from existing EPUB
                original_chapters.append(chapter)
            else:
                new_chapters.append(chapter)

        # Sort original chapters
        original_chapters.sort(key=lambda c: c.chapter_id)

        # Reorder self.chapters to match spine order: nav, intro, original + new
        self.chapters = []
        if intro_chapter:
            self.chapters.append(intro_chapter)
        self.chapters.extend(original_chapters + new_chapters)

        # Re-add all chapters to the book in the correct order
        # First, remove existing chapter items to avoid duplicates
        items_to_remove = []
        for item in self._epub_book.get_items():
            if isinstance(item, epub.EpubHtml) and item.file_name.startswith(
                "chapter_"
            ):
                items_to_remove.append(item)
            elif isinstance(item, epub.EpubHtml) and item.file_name == "intro.xhtml":
                items_to_remove.append(item)

        for item in items_to_remove:
            self._epub_book.items.remove(item)

        # Re-add chapters in correct order
        for chapter in self.chapters:
            epub_chapter = chapter.to_epub_item()
            self._epub_book.add_item(epub_chapter)

        # Generate navigation content
        _get_logger().debug(
            f"Generating nav content for {len(self.chapters)} chapters")
        for i, ch in enumerate(self.chapters):
            _get_logger().debug(
                f"Chapter {i}: {ch.title} ({ch.file_name}) - Level: {ch.level}"
            )
        nav_content = toc_generator.create_nav_content(self.chapters)

        # Create navigation document with proper properties
        nav = epub.EpubHtml(
            title="Table of Contents", file_name="nav.xhtml", content=nav_content
        )
        nav.id = "nav"
        nav.properties.append("nav")

        # Add nav at the end to ensure it's added last
        # This will affect the order in the EPUB zip file
        self._epub_book.add_item(nav)

        # Nav content generated successfully

        # Create and add NCX for EPUB2 compatibility (not in spine for EPUB 3)
        ncx_content = self._generate_ncx_content()
        ncx = epub.EpubItem(
            uid="ncx",
            file_name="toc.ncx",
            media_type="application/x-dtbncx+xml",
            content=ncx_content.encode("utf-8"),
        )
        self._epub_book.add_item(ncx)

        # Set TOC structure for ebooklib
        toc_sections = []
        for chapter in self.chapters:
            toc_sections.append(epub.Section(
                chapter.title, href=chapter.file_name))

        self._epub_book.toc = toc_sections

    def _set_spine(self) -> None:
        """Set the spine structure properly"""
        spine_items = []

        # Add navigation to spine
        spine_items.append("nav")

        # Separate chapters by type and ensure correct order
        original_chapters = []
        new_chapters = []
        intro_chapter = None

        for chapter in self.chapters:
            if chapter.level == "intro":
                intro_chapter = chapter
            elif chapter.chapter_id and chapter.chapter_id.startswith("chapter_"):
                # All chapter_xxx are considered original chapters from existing EPUB
                original_chapters.append(chapter)
            else:
                new_chapters.append(chapter)

        # Sort original chapters
        original_chapters.sort(key=lambda c: c.chapter_id)

        # Add intro first
        if intro_chapter and intro_chapter.chapter_id:
            spine_items.append(intro_chapter.chapter_id)

        # Add chapters in correct order: original + new
        for chapter in original_chapters + new_chapters:
            if chapter.chapter_id and chapter.chapter_id != "nav":
                spine_items.append(chapter.chapter_id)

        # Set spine (NCX not included in EPUB 3 spine)
        self._epub_book.spine = spine_items

    def get_spine(self) -> List[str]:
        """Get book's spine structure"""
        return self._epub_book.spine

    def _generate_ncx_content(self) -> str:
        """Generate NCX content manually for EPUB2 compatibility"""
        if not self._epub_book:
            return ""
        ncx_content = [
            '<?xml version="1.0" encoding="utf-8"?>',
            '<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">',
            "<head>",
            f'<meta content="{self.metadata.identifier}" name="dtb:uid"/>',
            '<meta content="1" name="dtb:depth"/>',
            '<meta content="0" name="dtb:totalPageCount"/>',
            '<meta content="0" name="dtb:maxPageNumber"/>',
            "</head>",
            "<docTitle>",
            f"<text>{self.metadata.title}</text>",
            "</docTitle>",
            "<navMap>",
        ]

        # Add navPoints for each chapter
        for i, chapter in enumerate(self.chapters, 1):
            ncx_content.append(f'<navPoint id="navpoint-{i}" playOrder="{i}">')
            ncx_content.append(
                f"<navLabel><text>{chapter.title}</text></navLabel>")
            ncx_content.append(f'<content src="{chapter.file_name}"/>')
            ncx_content.append("</navPoint>")

        ncx_content.extend(["</navMap>", "</ncx>"])

        return "\n".join(ncx_content)

    def _extract_chapters_from_epub(
        self, existing_book: epub.EpubBook
    ) -> List[Chapter]:
        """Extract chapters from existing EPUB"""
        chapters = []
        seen_files = set()  # Track files we've already processed

        # Get all items from existing EPUB
        items = existing_book.get_items()

        for item in items:
            if isinstance(item, epub.EpubHtml) and item.file_name.endswith(".xhtml"):
                # Skip navigation and cover pages
                if item.file_name in ["nav.xhtml", "cover.xhtml"]:
                    continue

                # Skip if we've already processed this file
                if item.file_name in seen_files:
                    continue
                seen_files.add(item.file_name)

                try:
                    # Parse HTML content to extract title and content
                    soup = BeautifulSoup(item.content, "html.parser")

                    # Extract title from the first heading tag
                    title = item.title or "Unknown Title"
                    heading = soup.find(["h1", "h2", "h3"])
                    if heading:
                        title = heading.get_text().strip()

                    # Remove the title from content (first heading)
                    if heading:
                        heading.extract()

                    # Get the remaining content
                    content = str(soup.body) if soup.body else str(soup)

                    # Determine level based on filename or heading tag
                    level = "h1"  # default
                    if item.file_name == "intro.xhtml":
                        level = "intro"
                    elif heading and heading.name in ["h2", "h3"]:
                        level = heading.name
                    elif (
                        "sub" in item.file_name.lower() or item.file_name.count("_") > 1
                    ):
                        level = "h2"  # Assume subsections are h2

                    # Create chapter object
                    chapter = Chapter(
                        title=title,
                        content=content,
                        level=level,
                        file_name=item.file_name,
                        chapter_id=item.id,
                    )
                    chapters.append(chapter)

                except Exception as e:
                    _get_logger().warning(
                        f"Error extracting chapter from {item.file_name}: {e}"
                    )
                    continue

        # Separate chapters by type and sort appropriately
        spine_order = existing_book.spine
        original_chapters = []
        new_chapters = []
        intro_chapter = None

        for chapter in chapters:
            if chapter.level == "intro":
                intro_chapter = chapter
            elif chapter.chapter_id and chapter.chapter_id.startswith("chapter_"):
                # All chapter_xxx are considered original chapters from existing EPUB
                original_chapters.append(chapter)
            else:
                new_chapters.append(chapter)

        # Sort original chapters by their spine order (excluding intro)
        if original_chapters:
            try:
                # spine_order is a list of tuples (id, linear), extract just the ids
                spine_ids = [item[0] for item in spine_order]
                original_chapters.sort(
                    key=lambda c: spine_ids.index(c.chapter_id))
            except (ValueError, IndexError) as e:
                _get_logger().warning(
                    f"Could not sort by spine order: {e}, sorting by chapter_id instead"
                )
                original_chapters.sort(key=lambda c: c.chapter_id)

        # Combine: original chapters (excluding intro) + new chapters + intro
        chapters = original_chapters + new_chapters
        if intro_chapter:
            chapters.append(intro_chapter)

        return chapters

    @classmethod
    def merge_existing_epub_with_new_chapters(
        cls,
        input_epub: str,
        new_text_file: str,
        output_file: str,
        convert_tags: bool = False,
    ) -> None:
        """Merge new chapters into existing EPUB file"""
        try:
            from ..utils.file_handler import FileHandler

            file_handler = FileHandler()

            # Use ebooklib to read existing EPUB directly
            existing_book = epub.read_epub(input_epub)

            # Extract metadata from existing EPUB
            title_meta = existing_book.get_metadata("DC", "title")
            author_meta = existing_book.get_metadata("DC", "creator")
            lang_meta = existing_book.get_metadata("DC", "language")
            id_meta = existing_book.get_metadata("DC", "identifier")

            metadata = Metadata(
                title=title_meta[0][0] if title_meta else "Unknown Title",
                author=author_meta[0][0] if author_meta else "Unknown Author",
                language=lang_meta[0][0] if lang_meta else "zh",
                identifier=id_meta[0][0] if id_meta else "unknown-id",
            )

            # Create new Book instance
            new_book = cls(metadata)
            new_book._epub_book = existing_book  # Use existing EpubBook object

            # Remove existing nav and ncx items to avoid duplicates
            items_to_remove = []
            for item in existing_book.get_items():
                if (
                    isinstance(
                        item, epub.EpubHtml) and item.file_name == "nav.xhtml"
                ) or (isinstance(item, epub.EpubItem) and item.file_name == "toc.ncx"):
                    items_to_remove.append(item)

            for item in items_to_remove:
                existing_book.items.remove(item)

            # Update spine to remove nav and ncx references
            updated_spine = []
            for spine_item in existing_book.spine:
                if spine_item not in ["nav", "ncx"]:
                    updated_spine.append(spine_item)
            existing_book.spine = updated_spine
            _get_logger().debug(
                f"Updated spine after removing nav/ncx: {existing_book.spine}"
            )

            # Extract existing chapters from EPUB
            existing_chapters = new_book._extract_chapters_from_epub(
                existing_book)
            new_book.chapters = existing_chapters

            # Process new text content
            new_content = file_handler.read_file(new_text_file)
            if new_content:
                from ..generators.content import ContentGenerator

                content_generator = ContentGenerator()
                # Calculate existing chapter count
                existing_chapter_count = len(
                    [
                        ch
                        for ch in existing_chapters
                        if ch.file_name.startswith("chapter_")
                    ]
                )
                # Check if existing EPUB already has introduction
                has_existing_intro = any(
                    chapter.level == "intro" for chapter in existing_chapters)
                new_chapters = content_generator.generate_chapters(
                    new_content, convert_tags, start_index=existing_chapter_count + 1, skip_intro=has_existing_intro
                )

                for chapter in new_chapters:
                    new_book.add_chapter(chapter)

            # Generate new EPUB file
            new_book.generate_epub(output_file)
            _get_logger().info(
                f"Successfully merged chapters and generated new EPUB file: {output_file}"
            )

        except Exception as e:
            raise EPUBError(f"Error occurred while merging EPUB file: {e}")
