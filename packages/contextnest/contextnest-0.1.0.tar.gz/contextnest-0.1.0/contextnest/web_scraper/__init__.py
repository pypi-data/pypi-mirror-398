"""
Web Scraper module for contextnest.

This module provides web scraping functionality with:
- Playwright for browser automation
- BeautifulSoup for DOM parsing
- CAPTCHA detection and handling
- HTML to Markdown conversion
"""

from .scraper import WebScraper, scrape_url
from .captcha_handler import CaptchaHandler, CaptchaStrategy, CaptchaType
from .markdown_converter import MarkdownConverter

__all__ = [
    "WebScraper",
    "scrape_url",
    "CaptchaHandler",
    "CaptchaStrategy",
    "CaptchaType",
    "MarkdownConverter",
]
