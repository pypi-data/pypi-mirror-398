from src.myepubapp.core.chapter import Chapter
from src.myepubapp.generators.content import ContentGenerator


class TestContentGenerator:
    """Test cases for ContentGenerator"""

    def setup_method(self):
        """Setup for each test method"""
        self.generator = ContentGenerator()

    def test_split_into_chapters_basic(self):
        """Test basic chapter splitting"""
        content = """※ⅰ 第一章
這是第一章的內容。

※ⅱ 第一章第一節
這是第一節的內容。

※ⅲ 第一章第一節第一小節
這是第一小節的內容。
"""

        chapters_data = self.generator._split_into_chapters(content)

        assert len(chapters_data) == 3
        assert chapters_data[0]["title"] == "第一章"
        assert chapters_data[0]["level"] == "h1"
        assert "這是第一章的內容" in chapters_data[0]["content"]

        assert chapters_data[1]["title"] == "第一章第一節"
        assert chapters_data[1]["level"] == "h2"

        assert chapters_data[2]["title"] == "第一章第一節第一小節"
        assert chapters_data[2]["level"] == "h3"

    def test_split_into_chapters_with_intro(self):
        """Test chapter splitting with introduction"""
        content = """※☆ 書籍介紹
這是書籍的介紹內容。

※ⅰ 第一章
這是第一章的內容。
"""

        chapters_data = self.generator._split_into_chapters(content)

        assert len(chapters_data) == 2
        assert chapters_data[0]["title"] == "Introduction"
        assert chapters_data[0]["level"] == "intro"
        assert "這是書籍的介紹內容" in chapters_data[0]["content"]

        assert chapters_data[1]["title"] == "第一章"
        assert chapters_data[1]["level"] == "h1"

    def test_convert_tags(self):
        """Test tag conversion"""
        content = "這本書是<書名>的介紹。"
        converted = self.generator._convert_tags(content)
        assert converted == "這本書是《書名》的介紹。"

    def test_create_chapter(self):
        """Test chapter creation"""
        chapter_data = {"title": "測試章節", "content": "這是測試內容", "level": "h1"}

        chapter = self.generator._create_chapter(chapter_data, 1)

        assert isinstance(chapter, Chapter)
        assert chapter.title == "測試章節"
        assert chapter.level == "h1"
        assert chapter.file_name == "chapter_001.xhtml"
        assert "<p>這是測試內容</p>" in chapter.content

    def test_create_chapter_empty_content(self):
        """Test chapter creation with empty content"""
        chapter_data = {"title": "空章節", "content": "", "level": "h2"}

        chapter = self.generator._create_chapter(chapter_data, 2)

        assert chapter.content == "<p>This chapter currently has no content.</p>"

    def test_generate_chapters_integration(self):
        """Test full chapter generation integration"""
        content = """※ⅰ 第一章
第一章的內容。

※ⅱ 第二章
第二章的內容。
"""

        chapters = self.generator.generate_chapters(content)

        assert len(chapters) == 2
        assert all(isinstance(ch, Chapter) for ch in chapters)
        assert chapters[0].title == "第一章"
        assert chapters[1].title == "第二章"

    def test_generate_chapters_with_convert_tags(self):
        """Test chapter generation with tag conversion"""
        content = """※ⅰ 第一章 <書名>
包含<標籤>的內容。
"""

        chapters = self.generator.generate_chapters(content, convert_tags=True)

        assert len(chapters) == 1
        assert chapters[0].title == "第一章 《書名》"  # Title gets converted
        assert "《標籤》" in chapters[0].content  # Content gets converted
