"""
Unit tests for web_scraper.markdown_converter module.
Tests HTML to Markdown conversion functionality.
"""
import pytest
from unittest.mock import Mock, patch, mock_open
from pathlib import Path
from contextnest.web_scraper.markdown_converter import MarkdownConverter


class TestMarkdownConverter:
    """Test cases for MarkdownConverter class."""

    def test_initialization_with_default_output_dir(self):
        """Test initialization with default output directory."""
        converter = MarkdownConverter()
        expected_dir = Path.home() / ".contextnest" / "output"
        assert converter.output_dir == expected_dir

    def test_initialization_with_custom_output_dir(self):
        """Test initialization with custom output directory."""
        custom_dir = Path("/custom/output")
        converter = MarkdownConverter(output_dir=custom_dir)
        assert converter.output_dir == custom_dir

    def test_convert_to_markdown_basic_html(self):
        """Test basic HTML to Markdown conversion."""
        converter = MarkdownConverter()
        html_content = "<h1>Test Title</h1><p>Test paragraph.</p>"
        
        markdown = converter.convert_to_markdown(html_content, "https://example.com")
        
        assert "# Test Title" in markdown
        assert "Test paragraph." in markdown

    def test_convert_to_markdown_with_url_for_filename(self):
        """Test HTML to Markdown conversion with URL for filename generation."""
        converter = MarkdownConverter()
        html_content = "<h1>Test Title</h1><p>Test paragraph.</p>"
        
        markdown = converter.convert_to_markdown(html_content, "https://example.com/path/to/page")
        
        assert "# Test Title" in markdown
        assert "Test paragraph." in markdown

    def test_convert_to_markdown_with_special_characters(self):
        """Test HTML to Markdown conversion with special characters."""
        converter = MarkdownConverter()
        html_content = "<h1>Test &amp; Special &lt;Chars&gt;</h1><p>Quote: &quot;Hello&quot;</p>"
        
        markdown = converter.convert_to_markdown(html_content, "https://example.com")
        
        assert "Test & Special <Chars>" in markdown
        assert 'Quote: "Hello"' in markdown

    def test_save_markdown(self):
        """Test saving markdown to file."""
        markdown_content = "# Test Content\n\nThis is a test."
        
        with patch.object(Path, 'mkdir') as mock_mkdir:
            with patch.object(Path, 'write_text') as mock_write_text:
                converter = MarkdownConverter()
                filepath = converter.save_markdown(markdown_content, "https://example.com/test-page")
        
        mock_mkdir.assert_called_with(parents=True, exist_ok=True)
        mock_write_text.assert_called_once()
        assert ".md" in str(filepath)

    def test_save_markdown_with_path_cleanup(self):
        """Test saving markdown with URL path cleanup."""
        markdown_content = "# Test Content\n\nThis is a test."
        
        with patch.object(Path, 'mkdir') as mock_mkdir:
            with patch.object(Path, 'write_text') as mock_write_text:
                converter = MarkdownConverter()
                filepath = converter.save_markdown(markdown_content, "https://example.com/path/with/slashes?param=value#section")
        
        mock_mkdir.assert_called_with(parents=True, exist_ok=True)
        mock_write_text.assert_called_once()
        # The filename should have special characters replaced
        assert ".md" in str(filepath)

    def test_save_markdown_with_custom_output_dir(self):
        """Test saving markdown with custom output directory."""
        custom_dir = Path("/custom/output")
        markdown_content = "# Test Content\n\nThis is a test."
        
        with patch.object(Path, 'mkdir') as mock_mkdir:
            with patch.object(Path, 'write_text') as mock_write_text:
                converter = MarkdownConverter(output_dir=custom_dir)
                filepath = converter.save_markdown(markdown_content, "https://example.com/test")
        
        mock_mkdir.assert_called_with(parents=True, exist_ok=True)
        mock_write_text.assert_called_once()
        assert str(custom_dir) in str(filepath)

    def test_convert_to_markdown_empty_content(self):
        """Test HTML to Markdown conversion with empty content."""
        converter = MarkdownConverter()
        html_content = ""
        
        markdown = converter.convert_to_markdown(html_content, "https://example.com")
        
        assert markdown == ""

    def test_convert_to_markdown_complex_html(self):
        """Test HTML to Markdown conversion with complex HTML."""
        converter = MarkdownConverter()
        html_content = """
        <html>
            <head><title>Page Title</title></head>
            <body>
                <h1>Main Title</h1>
                <p>This is a <strong>bold</strong> paragraph with <em>italic</em> text.</p>
                <ul>
                    <li>Item 1</li>
                    <li>Item 2</li>
                </ul>
                <a href="https://example.com">Link Text</a>
            </body>
        </html>
        """
        
        markdown = converter.convert_to_markdown(html_content, "https://example.com")
        
        assert "# Main Title" in markdown
        assert "**bold**" in markdown
        assert "*italic*" in markdown
        # The html_to_markdown library uses '- Item' format for unordered lists
        assert "- Item 1" in markdown
        assert "- Item 2" in markdown
        assert "[Link Text](https://example.com)" in markdown

    @patch('contextnest.web_scraper.markdown_converter.convert')
    def test_convert_to_markdown_with_conversion_error(self, mock_convert):
        """Test HTML to Markdown conversion with conversion error."""
        mock_convert.side_effect = Exception("Conversion error")
        
        # Need to patch during init to avoid mkdir issue
        with patch.object(Path, 'mkdir'):
            converter = MarkdownConverter()
            html_content = "<h1>Test</h1>"
            
            with pytest.raises(Exception, match="Conversion error"):
                converter.convert_to_markdown(html_content, "https://example.com")

    def test_save_markdown_with_file_write_error(self):
        """Test saving markdown with file write error."""
        markdown_content = "# Test Content"
        
        with patch.object(Path, 'mkdir'):
            with patch.object(Path, 'write_text', side_effect=IOError("Write error")):
                converter = MarkdownConverter()
                with pytest.raises(IOError, match="Write error"):
                    converter.save_markdown(markdown_content, "https://example.com/test")