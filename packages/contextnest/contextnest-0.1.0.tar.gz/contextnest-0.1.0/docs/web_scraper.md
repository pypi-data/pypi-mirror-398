# Web Scraper Module Documentation

The web scraper module provides functionality for extracting content from web pages using Playwright browser automation. It includes CAPTCHA handling, stealth techniques, and HTML to Markdown conversion.

## Features

- **Playwright Integration**: Uses Playwright for browser automation and dynamic content loading
- **CAPTCHA Handling**: Automatic detection and handling of common CAPTCHA challenges
- **Stealth Techniques**: Anti-bot detection evasion to avoid being blocked
- **Markdown Conversion**: Converts HTML content to clean Markdown format
- **Human-like Behavior**: Simulates realistic user interactions

## API Reference

### WebScraper Class

The main class for web scraping operations:

```python
from contextnest.web_scraper import WebScraper

async with WebScraper(headless=True) as scraper:
    markdown = await scraper.scrape("https://example.com")
```

#### Constructor Parameters

- `headless` (bool, default=True): Whether to run the browser in headless mode
- `timeout` (int, default=30000): Page timeout in milliseconds
- `wait_for_selector` (str, optional): Wait for a specific selector to appear before scraping

#### Methods

- `scrape(url: str) -> str`: Scrapes content from the given URL and returns Markdown
- `scrape_to_file(url: str, file_path: str) -> None`: Scrapes content and saves to a file

### scrape_url Function

A convenience function for simple scraping:

```python
from contextnest.web_scraper import scrape_url

markdown = await scrape_url("https://example.com", headless=True)
```

#### Parameters

- `url` (str): The URL to scrape
- `headless` (bool, default=True): Whether to run the browser in headless mode
- `save_path` (str, optional): Path to save the markdown content

## CAPTCHA Handling

The scraper includes CAPTCHA detection and handling mechanisms:

- Automatic detection of common CAPTCHA providers
- Human-like behavior simulation during CAPTCHA solving
- Retry mechanisms for failed CAPTCHA attempts

## Stealth Techniques

To avoid bot detection, the scraper implements:

- Browser fingerprinting evasion
- Realistic mouse movements and clicks
- Randomized timing between actions
- User agent rotation

## Configuration

The scraper can be configured through environment variables:

- `SCRAPER_HEADLESS`: Whether to run in headless mode (default: true)
- `SCRAPER_TIMEOUT`: Page timeout in milliseconds (default: 30000)
- `SCRAPER_WAIT_FOR_SELECTOR`: Selector to wait for before scraping (default: None)