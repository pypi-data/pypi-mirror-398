"""
CAPTCHA detection and handling strategies for web scraping.
"""

import asyncio
from enum import Enum
from typing import Optional, Callable, Awaitable

from playwright.async_api import Page
from ..mcp_logger import info_mcp, warning_mcp


class CaptchaType(Enum):
    """Types of CAPTCHA that can be detected."""
    RECAPTCHA_V2 = "recaptcha_v2"
    RECAPTCHA_V3 = "recaptcha_v3"
    RECAPTCHA = "recaptcha"  # General recaptcha type
    HCAPTCHA = "hcaptcha"
    CLOUDFLARE_TURNSTILE = "cloudflare_turnstile"
    CLOUDFLARE_CHALLENGE = "cloudflare_challenge"
    UNKNOWN = "unknown"


class CaptchaStrategy(Enum):
    """Strategies for handling CAPTCHA."""
    STEALTH = "stealth"  # Try to avoid triggering CAPTCHA
    MANUAL = "manual"    # Wait for user to solve manually
    RETRY = "retry"      # Retry with different settings
    SKIP = "skip"        # Skip the page if CAPTCHA detected
    AUTO = "auto"        # Automatically handle various CAPTCHA types


class CaptchaHandler:
    """
    Handler for detecting and managing CAPTCHA challenges.
    
    This class provides detection for common CAPTCHA types and
    various strategies for handling them.
    """
    
    # CSS selectors for CAPTCHA detection
    CAPTCHA_SELECTORS = {
        CaptchaType.RECAPTCHA_V2: [
            'iframe[src*="recaptcha"]',
            'iframe[src*="google.com/recaptcha"]',
            '.g-recaptcha',
            '#recaptcha',
        ],
        CaptchaType.RECAPTCHA_V3: [
            'script[src*="recaptcha/api.js?render"]',
        ],
        CaptchaType.HCAPTCHA: [
            'iframe[src*="hcaptcha.com"]',
            '.h-captcha',
            '#hcaptcha',
        ],
        CaptchaType.CLOUDFLARE_TURNSTILE: [
            'iframe[src*="challenges.cloudflare.com"]',
            '.cf-turnstile',
        ],
        CaptchaType.CLOUDFLARE_CHALLENGE: [
            '#challenge-running',
            '#challenge-form',
            '.cf-browser-verification',
            'div[id="cf-please-wait"]',
        ],
    }
    
    # Text patterns indicating CAPTCHA presence
    CAPTCHA_TEXT_PATTERNS = [
        "verify you are human",
        "are you a robot",
        "captcha",
        "security check",
        "please wait",
        "checking your browser",
        "just a moment",
        "attention required",
    ]
    
    def __init__(
        self,
        strategy: CaptchaStrategy = CaptchaStrategy.MANUAL,
        manual_timeout: int = 120,
        on_captcha_detected: Optional[Callable[[CaptchaType], Awaitable[None]]] = None,
    ):
        """
        Initialize the CAPTCHA handler.
        
        Args:
            strategy: Strategy to use when CAPTCHA is detected
            manual_timeout: Timeout in seconds for manual solving
            on_captcha_detected: Optional callback when CAPTCHA is detected
        """
        self.strategy = strategy
        self.manual_timeout = manual_timeout
        self.on_captcha_detected = on_captcha_detected
    
    async def detect_captcha(self, page: Page) -> Optional[CaptchaType]:
        """
        Detect if a CAPTCHA is present on the page.

        Args:
            page: Playwright page to check

        Returns:
            CaptchaType if detected, None otherwise
        """
        # Check for specific CAPTCHA types using dedicated methods
        if await self._check_cloudflare_challenge(page):
            return CaptchaType.CLOUDFLARE_CHALLENGE

        if await self._check_cloudflare_turnstile(page):
            return CaptchaType.CLOUDFLARE_TURNSTILE

        if await self._check_recaptcha(page):
            return CaptchaType.RECAPTCHA

        if await self._check_hcaptcha(page):
            return CaptchaType.HCAPTCHA

        # Check for known CAPTCHA selectors as fallback
        for captcha_type, selectors in self.CAPTCHA_SELECTORS.items():
            for selector in selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        return captcha_type
                except Exception:
                    continue

        # Check page content for CAPTCHA text patterns
        try:
            content = await page.content()
            content_lower = content.lower()

            for pattern in self.CAPTCHA_TEXT_PATTERNS:
                if pattern in content_lower:
                    return CaptchaType.UNKNOWN
        except Exception:
            pass

        return None
    
    async def handle_captcha(self, page: Page, captcha_type: CaptchaType) -> bool:
        """
        Handle a detected CAPTCHA based on the configured strategy.

        Args:
            page: Playwright page with CAPTCHA
            captcha_type: Type of CAPTCHA detected

        Returns:
            True if CAPTCHA was handled successfully, False otherwise
        """
        # Handle the case where captcha_type might be a string instead of enum
        if isinstance(captcha_type, str):
            # Try to convert to CaptchaType enum, or create a temporary value
            try:
                captcha_type = CaptchaType(captcha_type)
            except ValueError:
                # If it's not a known type, treat as unknown
                captcha_type = CaptchaType.UNKNOWN

        if self.on_captcha_detected:
            await self.on_captcha_detected(captcha_type)

        if self.strategy == CaptchaStrategy.SKIP:
            warning_mcp(f"CAPTCHA detected ({captcha_type.value}), skipping page...")
            return False

        elif self.strategy == CaptchaStrategy.MANUAL:
            return await self._handle_manual(page, captcha_type)

        elif self.strategy == CaptchaStrategy.RETRY:
            info_mcp(f"CAPTCHA detected ({captcha_type.value}), will retry...")
            return False

        elif self.strategy == CaptchaStrategy.AUTO:
            # Handle CAPTCHA automatically based on type
            return await self._handle_auto(page, captcha_type)

        elif self.strategy == CaptchaStrategy.STEALTH:
            # Stealth mode is preventive, not reactive
            warning_mcp(f"CAPTCHA detected ({captcha_type.value}) despite stealth mode")
            return await self._handle_manual(page, captcha_type)

        return False
    
    async def _handle_auto(self, page: Page, captcha_type: CaptchaType) -> bool:
        """
        Handle CAPTCHA automatically based on type.

        Args:
            page: Playwright page with CAPTCHA
            captcha_type: Type of CAPTCHA detected

        Returns:
            True if CAPTCHA was handled, False otherwise
        """
        if captcha_type == CaptchaType.CLOUDFLARE_CHALLENGE:
            # For Cloudflare challenges, wait for them to resolve automatically
            return await self.wait_for_cloudflare(page)
        elif captcha_type in [CaptchaType.CLOUDFLARE_TURNSTILE, CaptchaType.RECAPTCHA, CaptchaType.HCAPTCHA]:
            # For other CAPTCHAs, we can't solve them automatically, so return False
            info_mcp(f"Cannot automatically handle {captcha_type.value}, CAPTCHA remains unsolved")
            return False
        else:
            # For unknown CAPTCHAs, try waiting to see if it resolves
            info_mcp(f"Waiting to see if {captcha_type.value} resolves automatically...")
            await asyncio.sleep(5)
            # Check if it's still present
            current_captcha = await self.detect_captcha(page)
            return current_captcha is None

    async def _handle_manual(self, page: Page, captcha_type: CaptchaType) -> bool:
        """
        Wait for user to manually solve the CAPTCHA.

        Args:
            page: Playwright page with CAPTCHA
            captcha_type: Type of CAPTCHA detected

        Returns:
            True if CAPTCHA was solved, False if timeout
        """
        info_mcp(f"\nCAPTCHA detected: {captcha_type.value}")
        info_mcp("Please solve the CAPTCHA in the browser window...")
        info_mcp(f"Waiting up to {self.manual_timeout} seconds...")

        start_time = asyncio.get_event_loop().time()
        check_interval = 2  # Check every 2 seconds

        while True:
            elapsed = asyncio.get_event_loop().time() - start_time

            if elapsed >= self.manual_timeout:
                warning_mcp("CAPTCHA solving timeout!")
                return False

            # Check if CAPTCHA is still present
            current_captcha = await self.detect_captcha(page)

            if current_captcha is None:
                info_mcp("CAPTCHA solved successfully!")
                return True

            await asyncio.sleep(check_interval)
    
    async def _check_cloudflare_challenge(self, page: Page) -> bool:
        """
        Check for Cloudflare challenge elements.

        Args:
            page: Playwright page to check

        Returns:
            True if Cloudflare challenge is detected, False otherwise
        """
        try:
            element = await page.query_selector('#challenge-running, #challenge-form, .cf-browser-verification')
            return element is not None
        except Exception:
            return False

    async def _check_cloudflare_turnstile(self, page: Page) -> bool:
        """
        Check for Cloudflare Turnstile elements.

        Args:
            page: Playwright page to check

        Returns:
            True if Cloudflare Turnstile is detected, False otherwise
        """
        try:
            element = await page.query_selector('iframe[src*="challenges.cloudflare.com"]')
            return element is not None
        except Exception:
            return False

    async def _check_recaptcha(self, page: Page) -> bool:
        """
        Check for reCAPTCHA elements.

        Args:
            page: Playwright page to check

        Returns:
            True if reCAPTCHA is detected, False otherwise
        """
        try:
            element = await page.query_selector('iframe[src*="google.com/recaptcha"], .g-recaptcha')
            return element is not None
        except Exception:
            return False

    async def _check_hcaptcha(self, page: Page) -> bool:
        """
        Check for hCAPTCHA elements.

        Args:
            page: Playwright page to check

        Returns:
            True if hCAPTCHA is detected, False otherwise
        """
        try:
            element = await page.query_selector('iframe[src*="hcaptcha.com"], .h-captcha')
            return element is not None
        except Exception:
            return False

    async def wait_for_cloudflare(self, page: Page, timeout: int = 30) -> bool:
        """
        Wait for Cloudflare challenge to complete automatically.

        Some Cloudflare challenges resolve without user interaction
        when using proper browser settings.

        Args:
            page: Playwright page
            timeout: Maximum wait time in seconds

        Returns:
            True if challenge passed, False otherwise
        """
        info_mcp("Waiting for Cloudflare challenge to complete...")

        try:
            # Wait for challenge elements to disappear
            await page.wait_for_selector(
                '#challenge-running, #challenge-form',
                state='hidden',
                timeout=timeout * 1000
            )
            info_mcp("Cloudflare challenge passed!")
            return True
        except Exception as e:
            warning_mcp("Cloudflare challenge did not complete automatically", error=str(e))
            return False
