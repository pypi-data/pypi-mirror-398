# Web Scraper Module

A comprehensive web scraping tool using Playwright for browser automation, BeautifulSoup for DOM parsing, with CAPTCHA handling and Ollama-powered Markdown conversion.

## Features

- **Browser Automation**: Playwright for rendering JavaScript-heavy pages
- **DOM Parsing**: BeautifulSoup for efficient HTML parsing and content extraction
- **CAPTCHA Handling**: Detection and handling strategies for reCAPTCHA, hCaptcha, Cloudflare
- **Markdown Conversion**: Ollama LLM integration (`gpt-oss:120b-cloud`) for HTML to Markdown
- **Stealth Mode**: playwright-stealth to avoid bot detection

## Installation

Ensure you have the required dependencies:

```bash
uv add beautifulsoup4 lxml playwright-stealth
uv run playwright install chromium
```

## Quick Start

### Basic Usage

```python
import asyncio
from contextnest.web_scraper import WebScraper

async def main():
    async with WebScraper(headless=True) as scraper:
        markdown = await scraper.scrape("https://example.com")
        print(markdown)

asyncio.run(main())
```

### CAPTCHA-Protected Sites

For sites with CAPTCHA, use headed mode for manual solving:

```python
from contextnest.web_scraper import WebScraper, CaptchaStrategy

async with WebScraper(
    headless=False,  # Show browser for manual CAPTCHA solving
    captcha_strategy=CaptchaStrategy.MANUAL,
) as scraper:
    markdown = await scraper.scrape("https://protected-site.com")
```

### Scrape Multiple URLs

```python
async with WebScraper() as scraper:
    results = await scraper.scrape_multiple([
        "https://example.com",
        "https://httpbin.org/html",
    ], concurrent=2)
```

### Convenience Function

```python
from contextnest.web_scraper import scrape_url

markdown = asyncio.run(scrape_url("https://example.com"))
```

## Module Structure

| File | Purpose |
|------|---------|
| `scraper.py` | Main `WebScraper` class with full scraping workflow |
| `captcha_handler.py` | CAPTCHA detection for reCAPTCHA, hCaptcha, Cloudflare |
| `markdown_converter.py` | Ollama integration for HTML to Markdown conversion |
| `utils.py` | Stealth settings, random delays, human-like behavior |
| `example.py` | Usage examples |

## Output

Markdown files are saved to the `output/` directory with YAML frontmatter:

```markdown
---
source: https://example.com
scraped_at: 2025-12-19T17:37:24.215958
---

# Example Domain

This domain is for use in documentation examples...
```

## Configuration Options

### WebScraper Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `headless` | bool | `True` | Run browser in headless mode |
| `captcha_strategy` | CaptchaStrategy | `MANUAL` | How to handle CAPTCHAs |
| `ollama_model` | str | `gpt-oss:120b-cloud` | Ollama model for conversion |
| `output_dir` | Path | `./output` | Directory for markdown files |
| `timeout` | int | `30000` | Default timeout in milliseconds |

### CAPTCHA Strategies

| Strategy | Description |
|----------|-------------|
| `STEALTH` | Try to avoid triggering CAPTCHA |
| `MANUAL` | Wait for user to solve manually |
| `RETRY` | Retry with different settings |
| `SKIP` | Skip the page if CAPTCHA detected |

## Architecture

```
URL → Playwright Browser → Stealth Mode → CAPTCHA Check
                                              ↓
                         ┌──────────────────────────────────┐
                         │  CAPTCHA Detected?               │
                         │  → Manual: Wait for user         │
                         │  → Skip: Abort scraping          │
                         └──────────────────────────────────┘
                                              ↓
              Extract DOM → BeautifulSoup → Clean HTML
                                              ↓
                         Ollama LLM → Markdown → Save to File
```

## Running the Example

```bash
uv run python contextnest/web_scraper/example.py
```
