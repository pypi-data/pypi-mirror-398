"""Tests for text formatting functions."""

import pytest
from zerox_sync.processor.text import format_markdown


class TestFormatMarkdown:
    """Tests for format_markdown function."""

    def test_removes_markdown_code_blocks(self):
        text = "```markdown\n# Heading\n\nContent here\n```"
        result = format_markdown(text)
        assert result == "# Heading\n\nContent here"

    def test_removes_generic_code_blocks(self):
        text = "```\n# Heading\n\nContent here\n```"
        result = format_markdown(text)
        assert result == "# Heading\n\nContent here"

    def test_removes_html_code_blocks(self):
        text = "```html\n<h1>Heading</h1>\n```"
        result = format_markdown(text)
        assert result == "<h1>Heading</h1>"

    def test_no_code_blocks(self):
        text = "# Heading\n\nContent here"
        result = format_markdown(text)
        assert result == "# Heading\n\nContent here"

    def test_strips_whitespace(self):
        text = "  \n# Heading\n\n  "
        result = format_markdown(text)
        assert result == "# Heading"

    def test_empty_string(self):
        text = ""
        result = format_markdown(text)
        assert result == ""

    def test_only_whitespace(self):
        text = "   \n\n   "
        result = format_markdown(text)
        assert result == ""
