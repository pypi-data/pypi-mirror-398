"""
Utility functions for web scraping with stealth settings and human-like behavior.
"""

import asyncio
import random
from typing import Optional

from playwright.async_api import Page
from playwright_stealth import Stealth

# Create a global stealth instance
_stealth = Stealth()


# Common user agents for rotation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
]


def get_random_user_agent() -> str:
    """Get a random user agent string."""
    return random.choice(USER_AGENTS)


async def apply_stealth(page: Page) -> None:
    """
    Apply stealth settings to a Playwright page to reduce bot detection.
    
    This uses playwright-stealth to modify browser properties that
    are commonly checked by anti-bot systems.
    """
    await _stealth.apply_stealth_async(page)


async def random_delay(min_ms: int = 500, max_ms: int = 2000) -> None:
    """
    Wait for a random amount of time to simulate human behavior.
    
    Args:
        min_ms: Minimum delay in milliseconds
        max_ms: Maximum delay in milliseconds
    """
    delay = random.randint(min_ms, max_ms) / 1000
    await asyncio.sleep(delay)


async def human_like_scroll(page: Page, scroll_count: int = 3) -> None:
    """
    Simulate human-like scrolling behavior on a page.
    
    Args:
        page: Playwright page instance
        scroll_count: Number of scroll actions to perform
    """
    for _ in range(scroll_count):
        # Random scroll distance
        scroll_distance = random.randint(200, 500)
        
        await page.evaluate(f"window.scrollBy(0, {scroll_distance})")
        await random_delay(300, 800)


async def human_like_mouse_move(page: Page, target_x: int, target_y: int) -> None:
    """
    Simulate human-like mouse movement to a target position.
    
    Args:
        page: Playwright page instance  
        target_x: Target X coordinate
        target_y: Target Y coordinate
    """
    # Get current viewport size
    viewport = page.viewport_size
    if not viewport:
        return
    
    # Start from a random position
    start_x = random.randint(0, viewport['width'])
    start_y = random.randint(0, viewport['height'])
    
    # Move in steps
    steps = random.randint(5, 15)
    for i in range(steps):
        progress = (i + 1) / steps
        current_x = start_x + (target_x - start_x) * progress
        current_y = start_y + (target_y - start_y) * progress
        
        # Add some randomness to the path
        current_x += random.randint(-10, 10)
        current_y += random.randint(-10, 10)
        
        await page.mouse.move(current_x, current_y)
        await asyncio.sleep(random.uniform(0.01, 0.05))


def get_browser_context_options(user_agent: Optional[str] = None) -> dict:
    """
    Get browser context options with realistic settings.
    
    Args:
        user_agent: Optional specific user agent to use
        
    Returns:
        Dictionary of browser context options
    """
    return {
        "user_agent": user_agent or get_random_user_agent(),
        "viewport": {"width": 1920, "height": 1080},
        "locale": "en-US",
        "timezone_id": "America/New_York",
        "permissions": ["geolocation"],
        "geolocation": {"latitude": 40.7128, "longitude": -74.0060},  # New York
        "color_scheme": "light",
    }
