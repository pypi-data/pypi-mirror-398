"""
Main web scraper class using Playwright and BeautifulSoup.
"""

import asyncio
from pathlib import Path
from typing import Optional

from playwright.async_api import async_playwright, Browser, Page, BrowserContext

from .utils import (
    apply_stealth,
    random_delay,
    human_like_scroll,
    get_browser_context_options,
)
from .captcha_handler import CaptchaHandler, CaptchaStrategy, CaptchaType
from .markdown_converter import MarkdownConverter
from ..mcp_logger import info_mcp, log_error


class WebScraper:
    """
    Web scraper with Playwright, BeautifulSoup, CAPTCHA handling,
    and Ollama-powered Markdown conversion.
    
    Features:
    - Stealth mode to avoid bot detection
    - CAPTCHA detection and handling
    - Human-like behavior simulation
    - DOM content extraction with BeautifulSoup
    - HTML to Markdown conversion
    
    Example:
        ```python
        async with WebScraper() as scraper:
            markdown = await scraper.scrape("https://example.com")
            print(markdown)
        ```
    """
    
    def __init__(
        self,
        headless: bool = True,
        captcha_strategy: CaptchaStrategy = CaptchaStrategy.MANUAL,
        output_dir: Optional[Path] = None,
        timeout: int = 30000,
    ):
        """
        Initialize the web scraper.
        
        Args:
            headless: Run browser in headless mode (set False for CAPTCHA solving)
            captcha_strategy: Strategy for handling CAPTCHAs
            ollama_model: Ollama model for Markdown conversion
            output_dir: Directory to save markdown files
            timeout: Default timeout in milliseconds
        """
        self.headless = headless
        self.timeout = timeout
        
        self.captcha_handler = CaptchaHandler(strategy=captcha_strategy)
        self.markdown_converter = MarkdownConverter(
            output_dir=output_dir,
        )
        
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def start(self) -> None:
        """Start the browser."""
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
            ]
        )
    
    async def close(self) -> None:
        """Close the browser and cleanup resources."""
        if self._context:
            await self._context.close()
            self._context = None
        
        if self._browser:
            await self._browser.close()
            self._browser = None
        
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
    
    async def _create_context(self) -> BrowserContext:
        """Create a new browser context with stealth settings."""
        context_options = get_browser_context_options()
        context = await self._browser.new_context(**context_options)
        return context
    
    async def _create_page(self) -> Page:
        """Create a new page with stealth settings."""
        if not self._context:
            self._context = await self._create_context()
        
        page = await self._context.new_page()
        
        # Apply stealth settings
        await apply_stealth(page)
        
        # Set default timeout
        page.set_default_timeout(self.timeout)
        
        return page
    
    async def scrape(
        self,
        url: str,
        save_path: Optional[str] = None,
        wait_for_selector: Optional[str] = None,
        scroll: bool = True,
    ) -> str:
        """
        Scrape a URL and return markdown content.
        
        Args:
            url: URL to scrape
            save_path: Optional custom path to save markdown file
            wait_for_selector: Optional CSS selector to wait for before scraping
            scroll: Whether to scroll the page before scraping
            
        Returns:
            Markdown content of the scraped page
        """
        if not self._browser:
            await self.start()
        
        page = await self._create_page()
        
        try:
            info_mcp(f"Navigating to: {url}")
            
            # Navigate to URL
            response = await page.goto(url, wait_until='domcontentloaded')
            
            if not response:
                raise Exception(f"Failed to load {url}")
            
            info_mcp(f"Page loaded with status: {response.status}")
            
            # Wait for content to load
            await random_delay(1000, 2000)
            
            # Check for CAPTCHA
            captcha_type = await self.captcha_handler.detect_captcha(page)
            
            if captcha_type:
                # Handle Cloudflare challenges automatically first
                if captcha_type in [CaptchaType.CLOUDFLARE_CHALLENGE, CaptchaType.CLOUDFLARE_TURNSTILE]:
                    success = await self.captcha_handler.wait_for_cloudflare(page)
                    if not success:
                        success = await self.captcha_handler.handle_captcha(page, captcha_type)
                else:
                    success = await self.captcha_handler.handle_captcha(page, captcha_type)
                
                if not success:
                    raise Exception(f"Failed to handle CAPTCHA: {captcha_type.value}")
            
            # Wait for specific selector if provided
            if wait_for_selector:
                info_mcp(f"Waiting for selector: {wait_for_selector}")
                await page.wait_for_selector(wait_for_selector)
            
            # Simulate human behavior
            if scroll:
                await human_like_scroll(page)
            
            await random_delay(500, 1000)
            
            # Extract page content
            info_mcp("Extracting page content...")
            html_content = await page.content()

            # Get page title for context
            title = await page.title()
            info_mcp(f"Page title: {title}")

            # Convert to Markdown
            info_mcp("Converting to Markdown...")
            markdown = self.markdown_converter.convert_to_markdown(html_content, url)

            # Save to file
            if save_path:
                filepath = Path(save_path)
                filepath.parent.mkdir(parents=True, exist_ok=True)
                filepath.write_text(markdown, encoding='utf-8')
                info_mcp(f"Saved to: {filepath}")
            else:
                filepath = self.markdown_converter.save_markdown(markdown, url)
                info_mcp(f"Saved to: {filepath}")
            
            return markdown
            
        finally:
            await page.close()
    
    async def scrape_multiple(
        self,
        urls: list[str],
        concurrent: int = 3,
    ) -> dict[str, str]:
        """
        Scrape multiple URLs concurrently.
        
        Args:
            urls: List of URLs to scrape
            concurrent: Maximum concurrent scrapes
            
        Returns:
            Dictionary mapping URLs to their markdown content
        """
        semaphore = asyncio.Semaphore(concurrent)
        results = {}
        
        async def scrape_with_semaphore(url: str):
            async with semaphore:
                try:
                    content = await self.scrape(url)
                    results[url] = content
                except Exception as e:
                    log_error("scrape_multiple", e, url)
                    results[url] = f"Error: {e}"
        
        tasks = [scrape_with_semaphore(url) for url in urls]
        await asyncio.gather(*tasks)
        
        return results
    
    async def take_screenshot(
        self,
        url: str,
        output_path: str,
        full_page: bool = True,
    ) -> Path:
        """
        Take a screenshot of a URL.
        
        Args:
            url: URL to capture
            output_path: Path to save screenshot
            full_page: Whether to capture full page or just viewport
            
        Returns:
            Path to saved screenshot
        """
        if not self._browser:
            await self.start()
        
        page = await self._create_page()
        
        try:
            await page.goto(url, wait_until='networkidle')
            await random_delay(1000, 2000)
            
            output = Path(output_path)
            output.parent.mkdir(parents=True, exist_ok=True)
            
            await page.screenshot(path=str(output), full_page=full_page)
            
            return output
            
        finally:
            await page.close()


# Convenience function for simple scraping
async def scrape_url(
    url: str,
    headless: bool = True,
    save_path: Optional[str] = None,
) -> str:
    """
    Convenience function to scrape a single URL.
    
    Args:
        url: URL to scrape
        headless: Run browser in headless mode
        save_path: Optional path to save markdown
        
    Returns:
        Markdown content
    """
    async with WebScraper(headless=headless) as scraper:
        return await scraper.scrape(url, save_path=save_path)
