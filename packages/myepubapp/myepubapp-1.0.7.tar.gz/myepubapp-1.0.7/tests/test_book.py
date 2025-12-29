import os
import tempfile

from src.myepubapp.core.book import Book
from src.myepubapp.core.metadata import Metadata
from src.myepubapp.generators.content import ContentGenerator
from src.myepubapp.utils.epub_validator import EPUBValidator


class TestBook:
    """Test cases for Book class"""

    def setup_method(self):
        """Setup for each test method"""
        self.metadata = Metadata(
            title="Test Book", author="Test Author", language="zh", identifier="test-id"
        )

    def test_no_default_intro_when_no_intro_marker(self):
        """Test that no default introduction is added when content has no ※☆ marker"""
        book = Book(self.metadata)

        # Create chapters without intro
        generator = ContentGenerator()
        content = """※ⅰ 第一章
這是第一章的內容。

※ⅱ 第二章
這是第二章的內容。
"""
        chapters = generator.generate_chapters(content)
        for chapter in chapters:
            book.add_chapter(chapter)

        # Check that no intro exists initially
        assert not any(ch.level == "intro" for ch in book.chapters)

        # Generate EPUB (this calls _add_toc_and_nav internally)
        with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as tmp:
            try:
                book.generate_epub(tmp.name)

                # Check that no intro was added
                assert not any(ch.level == "intro" for ch in book.chapters)

            finally:
                if os.path.exists(tmp.name):
                    os.unlink(tmp.name)

    def test_only_level3_chapters_no_intro(self):
        """Test that no default intro is added when file has only ※ⅲ chapters without ※☆"""
        book = Book(self.metadata)

        # Create chapters with only ※ⅲ (level 3)
        generator = ContentGenerator()
        content = """※ⅲ 第一章第一節第一小節
這是第一小節的內容。

※ⅲ 第二章第一節第一小節
這是第二小節的內容。
"""
        chapters = generator.generate_chapters(content)
        for chapter in chapters:
            book.add_chapter(chapter)

        # Check that no intro exists initially
        assert not any(ch.level == "intro" for ch in book.chapters)
        # All should be h3
        assert all(ch.level == "h3" for ch in book.chapters)

        # Generate EPUB (this calls _add_toc_and_nav internally)
        with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as tmp:
            try:
                book.generate_epub(tmp.name)

                # Check that no intro was added
                assert not any(ch.level == "intro" for ch in book.chapters)

                # Check spine includes nav + chapters (no intro)
                spine = book.get_spine()
                assert len(spine) == 3  # nav + 2 chapters

            finally:
                if os.path.exists(tmp.name):
                    os.unlink(tmp.name)

    def test_epub3_compliance(self):
        """Test that generated EPUB is EPUB 3 compliant"""
        book = Book(self.metadata)

        # Create chapters without intro
        generator = ContentGenerator()
        content = """※ⅰ 第一章
這是第一章的內容。

※ⅱ 第二章
這是第二章的內容。
"""
        chapters = generator.generate_chapters(content)
        for chapter in chapters:
            book.add_chapter(chapter)

        # Generate EPUB
        with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as tmp:
            try:
                book.generate_epub(tmp.name)

                # Validate EPUB
                validator = EPUBValidator()
                results = validator.validate_epub(tmp.name)

                # Check basic compliance
                assert results[
                    "is_valid"
                ], f"EPUB validation failed: {results['errors']}"
                assert (
                    results["version"] == "3.0"
                ), f"Expected EPUB 3.0, got {results['version']}"

                # Check that NCX exists in manifest
                # Note: EPUB 3 doesn't require NCX, but our implementation includes it for compatibility
                ncx_items = [
                    item
                    for item in book._epub_book.get_items()
                    if hasattr(item, "id") and item.id == "ncx"
                ]
                assert len(
                    ncx_items) == 1, "NCX should be present with correct ID"

            finally:
                if os.path.exists(tmp.name):
                    os.unlink(tmp.name)

    def test_ncx_has_correct_id(self):
        """Test that NCX has the correct ID in manifest"""
        book = Book(self.metadata)

        # Create a simple chapter
        generator = ContentGenerator()
        content = """※ⅰ 第一章
這是第一章的內容。
"""
        chapters = generator.generate_chapters(content)
        for chapter in chapters:
            book.add_chapter(chapter)

        # Generate EPUB
        with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as tmp:
            try:
                book.generate_epub(tmp.name)

                # Check NCX ID
                ncx_items = [
                    item
                    for item in book._epub_book.get_items()
                    if hasattr(item, "id") and item.id == "ncx"
                ]
                assert len(ncx_items) == 1
                assert ncx_items[0].id == "ncx"

            finally:
                if os.path.exists(tmp.name):
                    os.unlink(tmp.name)

    def test_spine_includes_nav_and_chapters(self):
        """Test that spine includes nav and all chapters"""
        book = Book(self.metadata)

        # Create chapters
        generator = ContentGenerator()
        content = """※ⅰ 第一章
內容1

※ⅱ 第二章
內容2
"""
        chapters = generator.generate_chapters(content)
        for chapter in chapters:
            book.add_chapter(chapter)

        # Generate EPUB to trigger _add_toc_and_nav
        with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as tmp:
            try:
                book.generate_epub(tmp.name)

                spine = book.get_spine()
                assert len(spine) == 3  # nav + 2 chapters (no intro)
                assert spine[0] == "nav"  # Nav item
                assert spine[1] == "chapter_001"
                assert spine[2] == "chapter_002"

            finally:
                if os.path.exists(tmp.name):
                    os.unlink(tmp.name)
