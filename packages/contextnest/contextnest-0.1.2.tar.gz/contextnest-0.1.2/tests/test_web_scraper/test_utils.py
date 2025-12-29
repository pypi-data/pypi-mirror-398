"""
Unit tests for web_scraper.utils module.
Tests utility functions for browser configuration, stealth, and human-like behavior.
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from contextnest.web_scraper.utils import (
    apply_stealth,
    random_delay,
    human_like_scroll,
    get_browser_context_options
)


@pytest.mark.asyncio
async def test_apply_stealth():
    """Test apply_stealth function."""
    mock_page = AsyncMock()
    
    # Mock the _stealth.apply_stealth_async which is the actual method called
    with patch('contextnest.web_scraper.utils._stealth.apply_stealth_async', new_callable=AsyncMock) as mock_stealth:
        await apply_stealth(mock_page)
        
        # Verify that apply_stealth_async was called with the page
        mock_stealth.assert_called_once_with(mock_page)


@pytest.mark.asyncio
async def test_random_delay():
    """Test random_delay function."""
    # Test that it doesn't raise an exception and completes
    await random_delay(10, 50)
    
    # We can't easily test the exact delay, but we can test that it completes


@pytest.mark.asyncio
async def test_human_like_scroll():
    """Test human_like_scroll function."""
    mock_page = AsyncMock()
    mock_page.evaluate.return_value = 1000  # Simulate page height
    mock_page.evaluate_on_new_document.return_value = None
    
    # Mock the scroll behavior
    with patch('asyncio.sleep', new_callable=AsyncMock):
        await human_like_scroll(mock_page)
    
    # Verify that evaluate was called to get page height
    mock_page.evaluate.assert_called()


def test_get_browser_context_options():
    """Test get_browser_context_options function."""
    options = get_browser_context_options()
    
    # Verify that it returns a dictionary
    assert isinstance(options, dict)
    
    # Verify that it contains expected keys from the implementation
    expected_keys = [
        'user_agent',
        'viewport',
        'locale',
        'timezone_id',
    ]
    for key in expected_keys:
        assert key in options
    
    # Verify that viewport is a dictionary with expected structure
    assert isinstance(options['viewport'], dict)
    assert 'width' in options['viewport']
    assert 'height' in options['viewport']
    
    # Verify that viewport dimensions are reasonable
    assert options['viewport']['width'] > 0
    assert options['viewport']['height'] > 0