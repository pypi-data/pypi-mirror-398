"""
Unit tests for web_scraper.scraper module.
Tests scraping functionality, CAPTCHA handling, and markdown conversion.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from pathlib import Path
from contextnest.web_scraper.scraper import WebScraper, scrape_url


@pytest.mark.asyncio
class TestWebScraper:
    """Test cases for WebScraper class."""

    async def test_initialization(self):
        """Test WebScraper initialization."""
        scraper = WebScraper(headless=True, output_dir=Path("/tmp"))
        
        assert scraper.headless is True
        assert scraper.timeout == 30000
        assert scraper.captcha_handler is not None
        assert scraper.markdown_converter is not None

    @patch('contextnest.web_scraper.scraper.async_playwright')
    async def test_start_method(self, mock_async_playwright):
        """Test start method."""
        mock_pw_instance = AsyncMock()
        mock_browser = AsyncMock()
        mock_async_playwright.return_value.start = AsyncMock(return_value=mock_pw_instance)
        mock_pw_instance.chromium.launch = AsyncMock(return_value=mock_browser)
        
        scraper = WebScraper()
        await scraper.start()
        
        assert scraper._playwright is mock_pw_instance
        assert scraper._browser is mock_browser
        mock_async_playwright.return_value.start.assert_called_once()

    @patch('contextnest.web_scraper.scraper.async_playwright')
    async def test_close_method(self, mock_async_playwright):
        """Test close method."""
        mock_pw_instance = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_async_playwright.return_value.start = AsyncMock(return_value=mock_pw_instance)
        mock_pw_instance.chromium.launch = AsyncMock(return_value=mock_browser)
        
        scraper = WebScraper()
        await scraper.start()
        scraper._context = mock_context
        
        await scraper.close()
        
        mock_context.close.assert_called_once()
        mock_browser.close.assert_called_once()
        mock_pw_instance.stop.assert_called_once()
        assert scraper._context is None
        assert scraper._browser is None
        assert scraper._playwright is None

    @patch('contextnest.web_scraper.scraper.async_playwright')
    @patch('contextnest.web_scraper.scraper.apply_stealth')
    @patch('contextnest.web_scraper.scraper.random_delay')
    @patch('contextnest.web_scraper.scraper.human_like_scroll')
    @patch('contextnest.web_scraper.captcha_handler.CaptchaHandler.detect_captcha')
    @patch('contextnest.web_scraper.captcha_handler.CaptchaHandler.handle_captcha')
    @patch('contextnest.web_scraper.markdown_converter.MarkdownConverter.convert_to_markdown')
    @patch('contextnest.web_scraper.markdown_converter.MarkdownConverter.save_markdown')
    async def test_scrape_method_success(
        self, 
        mock_save_markdown, 
        mock_convert_to_markdown,
        mock_handle_captcha,
        mock_detect_captcha,
        mock_human_like_scroll,
        mock_random_delay,
        mock_apply_stealth,
        mock_async_playwright
    ):
        """Test successful scraping."""
        mock_pw_instance = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        mock_response = AsyncMock()
        
        mock_async_playwright.return_value.start = AsyncMock(return_value=mock_pw_instance)
        mock_pw_instance.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_page.goto = AsyncMock(return_value=mock_response)
        mock_page.content = AsyncMock(return_value="<html><body>Test content</body></html>")
        mock_page.title = AsyncMock(return_value="Test Page")
        mock_response.status = 200
        mock_detect_captcha.return_value = None  # No CAPTCHA
        mock_convert_to_markdown.return_value = "# Test content"
        mock_save_markdown.return_value = Path("/tmp/test.md")
        
        scraper = WebScraper(headless=True)
        result = await scraper.scrape("https://example.com")
        
        assert result == "# Test content"
        mock_page.goto.assert_called_once()
        mock_convert_to_markdown.assert_called_once()
        mock_page.close.assert_called_once()

    @patch('contextnest.web_scraper.scraper.async_playwright')
    @patch('contextnest.web_scraper.scraper.apply_stealth')
    @patch('contextnest.web_scraper.scraper.random_delay')
    @patch('contextnest.web_scraper.scraper.human_like_scroll')
    @patch('contextnest.web_scraper.captcha_handler.CaptchaHandler.detect_captcha')
    @patch('contextnest.web_scraper.captcha_handler.CaptchaHandler.handle_captcha')
    @patch('contextnest.web_scraper.markdown_converter.MarkdownConverter.convert_to_markdown')
    @patch('contextnest.web_scraper.markdown_converter.MarkdownConverter.save_markdown')
    async def test_scrape_method_with_captcha(
        self, 
        mock_save_markdown, 
        mock_convert_to_markdown,
        mock_handle_captcha,
        mock_detect_captcha,
        mock_human_like_scroll,
        mock_random_delay,
        mock_apply_stealth,
        mock_async_playwright
    ):
        """Test scraping with CAPTCHA handling."""
        from contextnest.web_scraper.captcha_handler import CaptchaType
        
        mock_pw_instance = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        mock_response = AsyncMock()
        
        mock_async_playwright.return_value.start = AsyncMock(return_value=mock_pw_instance)
        mock_pw_instance.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_page.goto = AsyncMock(return_value=mock_response)
        mock_page.content = AsyncMock(return_value="<html><body>Test content</body></html>")
        mock_page.title = AsyncMock(return_value="Test Page")
        mock_response.status = 200
        mock_detect_captcha.return_value = CaptchaType.RECAPTCHA  # CAPTCHA detected
        mock_handle_captcha.return_value = True  # CAPTCHA handled successfully
        mock_convert_to_markdown.return_value = "# Test content"
        mock_save_markdown.return_value = Path("/tmp/test.md")
        
        scraper = WebScraper(headless=True)
        result = await scraper.scrape("https://example.com")
        
        assert result == "# Test content"
        mock_detect_captcha.assert_called_once()
        mock_handle_captcha.assert_called_once()
        mock_page.close.assert_called_once()

    @patch('contextnest.web_scraper.scraper.async_playwright')
    @patch('contextnest.web_scraper.scraper.apply_stealth')
    @patch('contextnest.web_scraper.scraper.random_delay')
    @patch('contextnest.web_scraper.scraper.human_like_scroll')
    @patch('contextnest.web_scraper.captcha_handler.CaptchaHandler.detect_captcha')
    @patch('contextnest.web_scraper.captcha_handler.CaptchaHandler.handle_captcha')
    @patch('contextnest.web_scraper.markdown_converter.MarkdownConverter.convert_to_markdown')
    @patch('contextnest.web_scraper.markdown_converter.MarkdownConverter.save_markdown')
    async def test_scrape_method_captcha_failure(
        self, 
        mock_save_markdown, 
        mock_convert_to_markdown,
        mock_handle_captcha,
        mock_detect_captcha,
        mock_human_like_scroll,
        mock_random_delay,
        mock_apply_stealth,
        mock_async_playwright
    ):
        """Test scraping with CAPTCHA handling failure."""
        from contextnest.web_scraper.captcha_handler import CaptchaType
        
        mock_pw_instance = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        mock_response = AsyncMock()
        
        mock_async_playwright.return_value.start = AsyncMock(return_value=mock_pw_instance)
        mock_pw_instance.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_page.goto = AsyncMock(return_value=mock_response)
        mock_response.status = 200
        mock_detect_captcha.return_value = CaptchaType.RECAPTCHA  # CAPTCHA detected
        mock_handle_captcha.return_value = False  # CAPTCHA handling failed
        
        scraper = WebScraper(headless=True)
        with pytest.raises(Exception, match="Failed to handle CAPTCHA"):
            await scraper.scrape("https://example.com")

    @patch('contextnest.web_scraper.scraper.async_playwright')
    async def test_scrape_method_page_load_failure(self, mock_async_playwright):
        """Test scraping with page load failure."""
        mock_pw_instance = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        
        mock_async_playwright.return_value.start = AsyncMock(return_value=mock_pw_instance)
        mock_pw_instance.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_page.goto = AsyncMock(return_value=None)  # Page failed to load
        
        scraper = WebScraper(headless=True)
        with pytest.raises(Exception, match="Failed to load"):
            await scraper.scrape("https://example.com")

    @patch('contextnest.web_scraper.scraper.async_playwright')
    @patch('contextnest.web_scraper.scraper.apply_stealth')
    @patch('contextnest.web_scraper.scraper.random_delay')
    @patch('contextnest.web_scraper.scraper.human_like_scroll')
    @patch('contextnest.web_scraper.captcha_handler.CaptchaHandler.detect_captcha')
    @patch('contextnest.web_scraper.markdown_converter.MarkdownConverter.convert_to_markdown')
    @patch.object(Path, 'mkdir')
    @patch.object(Path, 'write_text')
    async def test_scrape_method_with_save_path(
        self, 
        mock_write_text,
        mock_mkdir,
        mock_convert_to_markdown,
        mock_detect_captcha,
        mock_human_like_scroll,
        mock_random_delay,
        mock_apply_stealth,
        mock_async_playwright
    ):
        """Test scraping with custom save path."""
        mock_pw_instance = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        mock_response = AsyncMock()
        
        mock_async_playwright.return_value.start = AsyncMock(return_value=mock_pw_instance)
        mock_pw_instance.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_page.goto = AsyncMock(return_value=mock_response)
        mock_page.content = AsyncMock(return_value="<html><body>Test content</body></html>")
        mock_page.title = AsyncMock(return_value="Test Page")
        mock_response.status = 200
        mock_detect_captcha.return_value = None  # No CAPTCHA
        mock_convert_to_markdown.return_value = "# Test content"
        
        scraper = WebScraper(headless=True)
        result = await scraper.scrape("https://example.com", save_path="/custom/path/test.md")
        
        assert result == "# Test content"
        # mkdir is called multiple times (once by MarkdownConverter init, once by save_path)
        assert mock_mkdir.call_count >= 1
        mock_write_text.assert_called_once()

    async def test_async_context_manager(self):
        """Test async context manager functionality."""
        with patch('contextnest.web_scraper.scraper.async_playwright') as mock_async_playwright:
            mock_pw_instance = AsyncMock()
            mock_browser = AsyncMock()
            mock_async_playwright.return_value.start = AsyncMock(return_value=mock_pw_instance)
            mock_pw_instance.chromium.launch = AsyncMock(return_value=mock_browser)
            
            async with WebScraper(headless=True) as scraper:
                assert scraper._browser is not None
            
            # Verify cleanup happened
            mock_browser.close.assert_called_once()
            mock_pw_instance.stop.assert_called_once()

    @patch('contextnest.web_scraper.scraper.async_playwright')
    @patch('contextnest.web_scraper.scraper.apply_stealth')
    @patch('contextnest.web_scraper.scraper.random_delay')
    @patch('contextnest.web_scraper.scraper.human_like_scroll')
    @patch('contextnest.web_scraper.captcha_handler.CaptchaHandler.detect_captcha')
    @patch('contextnest.web_scraper.markdown_converter.MarkdownConverter.convert_to_markdown')
    @patch('contextnest.web_scraper.markdown_converter.MarkdownConverter.save_markdown')
    async def test_scrape_multiple_method(
        self, 
        mock_save_markdown, 
        mock_convert_to_markdown,
        mock_detect_captcha,
        mock_human_like_scroll,
        mock_random_delay,
        mock_apply_stealth,
        mock_async_playwright
    ):
        """Test scraping multiple URLs."""
        mock_pw_instance = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        mock_response = AsyncMock()
        
        mock_async_playwright.return_value.start = AsyncMock(return_value=mock_pw_instance)
        mock_pw_instance.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_page.goto = AsyncMock(return_value=mock_response)
        mock_page.content = AsyncMock(return_value="<html><body>Test content</body></html>")
        mock_page.title = AsyncMock(return_value="Test Page")
        mock_response.status = 200
        mock_detect_captcha.return_value = None  # No CAPTCHA
        mock_convert_to_markdown.return_value = "# Test content"
        mock_save_markdown.return_value = Path("/tmp/test.md")
        
        scraper = WebScraper(headless=True)
        urls = ["https://example1.com", "https://example2.com"]
        results = await scraper.scrape_multiple(urls, concurrent=2)
        
        assert len(results) == 2
        assert results["https://example1.com"] == "# Test content"
        assert results["https://example2.com"] == "# Test content"

    @patch('contextnest.web_scraper.scraper.async_playwright')
    @patch('contextnest.web_scraper.scraper.apply_stealth')
    async def test_take_screenshot_method(self, mock_apply_stealth, mock_async_playwright):
        """Test taking a screenshot."""
        mock_pw_instance = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        mock_response = AsyncMock()
        
        mock_async_playwright.return_value.start = AsyncMock(return_value=mock_pw_instance)
        mock_pw_instance.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_page.goto = AsyncMock(return_value=mock_response)
        mock_response.status = 200
        
        with patch.object(Path, 'mkdir'):
            scraper = WebScraper(headless=True)
            screenshot_path = await scraper.take_screenshot(
                "https://example.com", 
                "/tmp/screenshot.png", 
                full_page=True
            )
        
        mock_page.screenshot.assert_called_once()
        assert screenshot_path == Path("/tmp/screenshot.png")


@pytest.mark.asyncio
async def test_scrape_url_convenience_function():
    """Test the scrape_url convenience function."""
    with patch('contextnest.web_scraper.scraper.WebScraper') as mock_scraper_class:
        mock_scraper_instance = AsyncMock()
        mock_scraper_instance.scrape = AsyncMock(return_value="# Test content")
        mock_scraper_class.return_value = mock_scraper_instance
        
        # Mock the async context manager
        mock_scraper_class.return_value.__aenter__ = AsyncMock(return_value=mock_scraper_instance)
        mock_scraper_class.return_value.__aexit__ = AsyncMock(return_value=None)
        
        result = await scrape_url("https://example.com", headless=True)
        
        assert result == "# Test content"
        mock_scraper_instance.scrape.assert_called_once_with("https://example.com", save_path=None)