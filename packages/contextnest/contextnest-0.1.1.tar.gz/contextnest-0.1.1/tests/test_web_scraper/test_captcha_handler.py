"""
Unit tests for web_scraper.captcha_handler module.
Tests CAPTCHA detection and handling functionality.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from contextnest.web_scraper.captcha_handler import CaptchaHandler, CaptchaStrategy, CaptchaType


class TestCaptchaHandler:
    """Test cases for CaptchaHandler class."""

    def test_initialization_with_manual_strategy(self):
        """Test initialization with manual strategy."""
        handler = CaptchaHandler(strategy=CaptchaStrategy.MANUAL)
        assert handler.strategy == CaptchaStrategy.MANUAL

    def test_initialization_with_auto_strategy(self):
        """Test initialization with auto strategy."""
        handler = CaptchaHandler(strategy=CaptchaStrategy.AUTO)
        assert handler.strategy == CaptchaStrategy.AUTO

    async def test_detect_captcha_no_captcha(self):
        """Test CAPTCHA detection when no CAPTCHA is present."""
        handler = CaptchaHandler()
        mock_page = AsyncMock()
        
        # Mock query_selector to return None (no elements found)
        mock_page.query_selector.return_value = None
        # Mock page.content to return clean HTML
        mock_page.content.return_value = "<html><body>Clean page</body></html>"
        
        result = await handler.detect_captcha(mock_page)
        
        assert result is None

    async def test_detect_captcha_cloudflare_challenge(self):
        """Test CAPTCHA detection for Cloudflare challenge."""
        handler = CaptchaHandler()
        mock_page = AsyncMock()
        
        # Mock the page to return an element for cloudflare challenge selector
        async def mock_query_selector(selector):
            if '#challenge-running' in selector or '#challenge-form' in selector:
                return AsyncMock()  # Element exists
            return None
        mock_page.query_selector.side_effect = mock_query_selector
        
        result = await handler.detect_captcha(mock_page)
        
        assert result == CaptchaType.CLOUDFLARE_CHALLENGE

    async def test_detect_captcha_cloudflare_turnstile(self):
        """Test CAPTCHA detection for Cloudflare Turnstile."""
        handler = CaptchaHandler()
        mock_page = AsyncMock()
        
        # Mock the page to return an element only for cloudflare turnstile selector
        async def mock_query_selector(selector):
            if 'challenges.cloudflare.com' in selector:
                return AsyncMock()  # Element exists
            return None
        mock_page.query_selector.side_effect = mock_query_selector
        
        result = await handler.detect_captcha(mock_page)
        
        assert result == CaptchaType.CLOUDFLARE_TURNSTILE

    async def test_detect_captcha_recaptcha(self):
        """Test CAPTCHA detection for reCAPTCHA."""
        handler = CaptchaHandler()
        mock_page = AsyncMock()
        
        # Mock the page to return an element only for recaptcha selector
        async def mock_query_selector(selector):
            if 'google.com/recaptcha' in selector or 'g-recaptcha' in selector:
                return AsyncMock()  # Element exists
            return None
        mock_page.query_selector.side_effect = mock_query_selector
        
        result = await handler.detect_captcha(mock_page)
        
        assert result == CaptchaType.RECAPTCHA

    async def test_detect_captcha_hcaptcha(self):
        """Test CAPTCHA detection for hCAPTCHA."""
        handler = CaptchaHandler()
        mock_page = AsyncMock()
        
        # Mock the page to return an element only for hcaptcha selector
        async def mock_query_selector(selector):
            if 'hcaptcha.com' in selector or 'h-captcha' in selector:
                return AsyncMock()  # Element exists
            return None
        mock_page.query_selector.side_effect = mock_query_selector
        
        result = await handler.detect_captcha(mock_page)
        
        assert result == CaptchaType.HCAPTCHA

    async def test_check_cloudflare_challenge(self):
        """Test Cloudflare challenge detection."""
        handler = CaptchaHandler()
        mock_page = AsyncMock()
        mock_page.query_selector.return_value = AsyncMock()  # Element exists
        
        result = await handler._check_cloudflare_challenge(mock_page)
        
        assert result is True
        mock_page.query_selector.assert_called_with('#challenge-running, #challenge-form, .cf-browser-verification')

    async def test_check_cloudflare_challenge_not_found(self):
        """Test Cloudflare challenge detection when not found."""
        handler = CaptchaHandler()
        mock_page = AsyncMock()
        mock_page.query_selector.return_value = None  # Element doesn't exist
        
        result = await handler._check_cloudflare_challenge(mock_page)
        
        assert result is False

    async def test_check_cloudflare_turnstile(self):
        """Test Cloudflare Turnstile detection."""
        handler = CaptchaHandler()
        mock_page = AsyncMock()
        mock_page.query_selector.return_value = AsyncMock()  # Element exists
        
        result = await handler._check_cloudflare_turnstile(mock_page)
        
        assert result is True
        mock_page.query_selector.assert_called_with('iframe[src*="challenges.cloudflare.com"]')

    async def test_check_recaptcha(self):
        """Test reCAPTCHA detection."""
        handler = CaptchaHandler()
        mock_page = AsyncMock()
        mock_page.query_selector.return_value = AsyncMock()  # Element exists
        
        result = await handler._check_recaptcha(mock_page)
        
        assert result is True
        mock_page.query_selector.assert_called_with('iframe[src*="google.com/recaptcha"], .g-recaptcha')

    async def test_check_hcaptcha(self):
        """Test hCAPTCHA detection."""
        handler = CaptchaHandler()
        mock_page = AsyncMock()
        mock_page.query_selector.return_value = AsyncMock()  # Element exists
        
        result = await handler._check_hcaptcha(mock_page)
        
        assert result is True
        mock_page.query_selector.assert_called_with('iframe[src*="hcaptcha.com"], .h-captcha')

    async def test_handle_captcha_manual_strategy(self):
        """Test CAPTCHA handling with manual strategy."""
        handler = CaptchaHandler(strategy=CaptchaStrategy.MANUAL, manual_timeout=1)  # Short timeout for test
        mock_page = AsyncMock()
        
        # Mock detect_captcha to return None (CAPTCHA solved) after first check
        handler.detect_captcha = AsyncMock(return_value=None)
        
        result = await handler.handle_captcha(mock_page, CaptchaType.RECAPTCHA)
        
        # Manual strategy should return True when CAPTCHA is solved
        assert result is True

    async def test_handle_captcha_auto_strategy_recaptcha(self):
        """Test CAPTCHA handling with auto strategy for reCAPTCHA."""
        handler = CaptchaHandler(strategy=CaptchaStrategy.AUTO)
        mock_page = AsyncMock()
        
        # For reCAPTCHA with AUTO strategy, the implementation returns False since it can't auto-solve
        result = await handler.handle_captcha(mock_page, CaptchaType.RECAPTCHA)
        
        # AUTO strategy can't solve reCAPTCHA automatically, so result should be False
        assert result is False

    async def test_handle_captcha_auto_strategy_hcaptcha(self):
        """Test CAPTCHA handling with auto strategy for hCAPTCHA."""
        handler = CaptchaHandler(strategy=CaptchaStrategy.AUTO)
        mock_page = AsyncMock()
        
        # For hCAPTCHA with AUTO strategy, the implementation returns False since it can't auto-solve
        result = await handler.handle_captcha(mock_page, CaptchaType.HCAPTCHA)
        
        # AUTO strategy can't solve hCAPTCHA automatically, so result should be False
        assert result is False

    async def test_handle_captcha_auto_strategy_cloudflare_challenge(self):
        """Test CAPTCHA handling with auto strategy for Cloudflare challenge."""
        handler = CaptchaHandler(strategy=CaptchaStrategy.AUTO)
        mock_page = AsyncMock()
        
        # Mock wait_for_cloudflare which is called for CLOUDFLARE_CHALLENGE type
        handler.wait_for_cloudflare = AsyncMock(return_value=True)
        
        result = await handler.handle_captcha(mock_page, CaptchaType.CLOUDFLARE_CHALLENGE)
        
        handler.wait_for_cloudflare.assert_called_once_with(mock_page)
        assert result is True

    async def test_handle_captcha_auto_strategy_cloudflare_turnstile(self):
        """Test CAPTCHA handling with auto strategy for Cloudflare Turnstile."""
        handler = CaptchaHandler(strategy=CaptchaStrategy.AUTO)
        mock_page = AsyncMock()
        
        # For CLOUDFLARE_TURNSTILE with AUTO strategy, implementation returns False
        result = await handler.handle_captcha(mock_page, CaptchaType.CLOUDFLARE_TURNSTILE)
        
        # AUTO strategy can't solve Cloudflare Turnstile automatically
        assert result is False

    async def test_handle_captcha_unknown_type(self):
        """Test CAPTCHA handling with unknown CAPTCHA type."""
        handler = CaptchaHandler(strategy=CaptchaStrategy.MANUAL, manual_timeout=1)
        mock_page = AsyncMock()
        
        # Mock detect_captcha to return None (CAPTCHA solved)
        handler.detect_captcha = AsyncMock(return_value=None)
        
        result = await handler.handle_captcha(mock_page, "UNKNOWN_CAPTCHA")
        
        # Unknown types get converted to CaptchaType.UNKNOWN and handled via manual strategy
        assert result is True

    async def test_wait_for_cloudflare(self):
        """Test waiting for Cloudflare to resolve."""
        handler = CaptchaHandler()
        mock_page = AsyncMock()

        # The wait_for_cloudflare method uses wait_for_selector, not query_selector
        mock_page.wait_for_selector.return_value = None  # Simulate successful wait

        result = await handler.wait_for_cloudflare(mock_page)

        assert result is True
        mock_page.wait_for_selector.assert_called_once()

    async def test_wait_for_cloudflare_timeout(self):
        """Test waiting for Cloudflare with timeout."""
        handler = CaptchaHandler()
        mock_page = AsyncMock()

        # Mock the page.wait_for_selector to raise an exception (timeout)
        mock_page.wait_for_selector.side_effect = Exception("Timeout")

        result = await handler.wait_for_cloudflare(mock_page, timeout=1)  # Use short timeout for test

        assert result is False