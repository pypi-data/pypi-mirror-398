from src.myepubapp.utils.text_processor import TextProcessor


class TestTextProcessor:
    """Test cases for TextProcessor"""

    def test_format_paragraphs_basic(self):
        """Test basic paragraph formatting"""
        text = """第一段內容。

第二段內容。

第三段內容。"""

        formatted = TextProcessor.format_paragraphs(text)

        expected = "<p>第一段內容。</p>\n<p>第二段內容。</p>\n" "<p>第三段內容。</p>"
        assert formatted == expected

    def test_format_paragraphs_empty_lines(self):
        """Test paragraph formatting with empty lines"""
        text = """第一段




第二段"""

        formatted = TextProcessor.format_paragraphs(text)

        expected = "<p>第一段</p>\n<p>第二段</p>"
        assert formatted == expected

    def test_format_paragraphs_empty_text(self):
        """Test paragraph formatting with empty text"""
        text = ""
        formatted = TextProcessor.format_paragraphs(text)

        assert formatted == "<p>This paragraph currently has no content.</p>"

    def test_format_paragraphs_whitespace_only(self):
        """Test paragraph formatting with whitespace only"""
        text = "   \n\n  \n  "
        formatted = TextProcessor.format_paragraphs(text)

        assert formatted == "<p>This paragraph currently has no content.</p>"

    def test_clean_text_basic(self):
        """Test basic text cleaning"""
        text = "  這是   測試  文本  "
        cleaned = TextProcessor.clean_text(text)

        assert cleaned == "這是 測試 文本"

    def test_clean_text_special_characters(self):
        """Test text cleaning with special characters"""
        text = "測試\x00文\x01本\x7f"
        cleaned = TextProcessor.clean_text(text)

        assert cleaned == "測試文本"

    def test_clean_text_multiple_spaces(self):
        """Test text cleaning with multiple spaces"""
        text = "這是    多個    空格    的文本"
        cleaned = TextProcessor.clean_text(text)

        assert cleaned == "這是 多個 空格 的文本"

    def test_convert_tags_basic(self):
        """Test basic tag conversion"""
        text = "這本書是<書名>的介紹。"
        converted = TextProcessor.convert_tags(text)

        assert converted == "這本書是《書名》的介紹。"

    def test_convert_tags_multiple(self):
        """Test multiple tag conversion"""
        text = "<書名1>和<書名2>都是好書。"
        converted = TextProcessor.convert_tags(text)

        assert converted == "《書名1》和《書名2》都是好書。"

    def test_convert_tags_empty(self):
        """Test tag conversion with empty tags"""
        text = "這是<>空的標籤。"
        converted = TextProcessor.convert_tags(text)

        assert converted == "這是《》空的標籤。"

    def test_convert_tags_nested(self):
        """Test tag conversion with nested content"""
        text = "這是<包含<嵌套>標籤>的文本。"
        converted = TextProcessor.convert_tags(text)

        # re.sub with non-greedy matching replaces outermost tags first
        assert converted == "這是《包含<嵌套》標籤>的文本。"

    def test_format_paragraphs_exception(self):
        """Test exception handling in format_paragraphs"""
        # This should not raise an exception for normal text
        text = "正常文本"
        result = TextProcessor.format_paragraphs(text)
        assert "<p>正常文本</p>" in result

    def test_clean_text_exception(self):
        """Test exception handling in clean_text"""
        # This should not raise an exception for normal text
        text = "正常文本"
        result = TextProcessor.clean_text(text)
        assert result == "正常文本"

    def test_convert_tags_exception(self):
        """Test exception handling in convert_tags"""
        # This should not raise an exception for normal text
        text = "正常文本"
        result = TextProcessor.convert_tags(text)
        assert result == "正常文本"
