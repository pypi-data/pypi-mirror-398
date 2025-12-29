"""
Unit tests for mcp_models.py module.
Tests the Pydantic models for validation.
"""
import pytest
from pydantic import ValidationError
from contextnest.mcp_models import WebScrapeInput, SearchInput, InsertKnowledgeInput, ReadMetadataInput


class TestWebScrapeInput:
    """Test cases for WebScrapeInput model."""

    def test_web_scrape_input_valid(self):
        """Test valid WebScrapeInput."""
        data = {
            "url": "https://example.com"
        }
        model = WebScrapeInput(**data)
        assert model.url == "https://example.com"

    def test_web_scrape_input_missing_url(self):
        """Test WebScrapeInput with missing URL (should raise ValidationError)."""
        with pytest.raises(ValidationError):
            WebScrapeInput()

    def test_web_scrape_input_empty_url(self):
        """Test WebScrapeInput with empty URL (should raise ValidationError)."""
        with pytest.raises(ValidationError):
            WebScrapeInput(url="")


class TestSearchInput:
    """Test cases for SearchInput model."""

    def test_search_input_valid(self):
        """Test valid SearchInput with default values."""
        data = {
            "query": "test query"
        }
        model = SearchInput(**data)
        assert model.query == "test query"
        assert model.limit == 5

    def test_search_input_with_custom_values(self):
        """Test SearchInput with custom values."""
        data = {
            "query": "test query",
            "limit": 10
        }
        model = SearchInput(**data)
        assert model.query == "test query"
        assert model.limit == 10

    def test_search_input_missing_query(self):
        """Test SearchInput with missing query (should raise ValidationError)."""
        with pytest.raises(ValidationError):
            SearchInput()

    def test_search_input_empty_query(self):
        """Test SearchInput with empty query (should raise ValidationError)."""
        with pytest.raises(ValidationError):
            SearchInput(query="")


class TestInsertKnowledgeInput:
    """Test cases for InsertKnowledgeInput model."""

    def test_insert_knowledge_input_valid(self):
        """Test valid InsertKnowledgeInput."""
        data = {
            "url": "https://example.com"
        }
        model = InsertKnowledgeInput(**data)
        assert model.url == "https://example.com"

    def test_insert_knowledge_input_missing_url(self):
        """Test InsertKnowledgeInput with missing URL (should raise ValidationError)."""
        with pytest.raises(ValidationError):
            InsertKnowledgeInput()

    def test_insert_knowledge_input_empty_url(self):
        """Test InsertKnowledgeInput with empty URL (should raise ValidationError)."""
        with pytest.raises(ValidationError):
            InsertKnowledgeInput(url="")


class TestReadMetadataInput:
    """Test cases for ReadMetadataInput model."""

    def test_read_metadata_input_valid(self):
        """Test valid ReadMetadataInput (empty model)."""
        model = ReadMetadataInput()
        # Since this model has no fields, just ensure it can be created
        assert model is not None

    def test_read_metadata_input_with_extra_data(self):
        """Test ReadMetadataInput with extra data (should raise ValidationError)."""
        with pytest.raises(ValidationError):
            ReadMetadataInput(extra_field="value")


def test_all_models_field_descriptions():
    """Test that all models have proper field descriptions."""
    # Check WebScrapeInput
    assert WebScrapeInput.model_fields['url'].description == "The URL to scrape."
    
    # Check SearchInput
    assert SearchInput.model_fields['query'].description == "The search query."
    assert SearchInput.model_fields['limit'].description == "Maximum number of results to return."
    
    # Check InsertKnowledgeInput
    assert InsertKnowledgeInput.model_fields['url'].description == "The source URL of the content."
    
    # ReadMetadataInput has no fields, so no descriptions to check