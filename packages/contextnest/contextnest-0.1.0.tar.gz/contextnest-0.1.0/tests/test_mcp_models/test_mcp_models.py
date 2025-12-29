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
        assert model.save_path is None

    def test_web_scrape_input_with_save_path(self):
        """Test WebScrapeInput with save_path."""
        data = {
            "url": "https://example.com",
            "save_path": "/path/to/save"
        }
        model = WebScrapeInput(**data)
        assert model.url == "https://example.com"
        assert model.save_path == "/path/to/save"

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
        assert model.k == 60
        assert model.vector_weight == 1.0
        assert model.fts_weight == 1.0

    def test_search_input_with_custom_values(self):
        """Test SearchInput with custom values."""
        data = {
            "query": "test query",
            "limit": 10,
            "k": 100,
            "vector_weight": 0.8,
            "fts_weight": 0.2
        }
        model = SearchInput(**data)
        assert model.query == "test query"
        assert model.limit == 10
        assert model.k == 100
        assert model.vector_weight == 0.8
        assert model.fts_weight == 0.2

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
        # title and content now default to empty strings (not None) for MCP elicitation compatibility
        assert model.title == ""
        assert model.content == ""

    def test_insert_knowledge_input_with_optional_fields(self):
        """Test InsertKnowledgeInput with optional fields."""
        data = {
            "url": "https://example.com",
            "title": "Test Title",
            "content": "Test content"
        }
        model = InsertKnowledgeInput(**data)
        assert model.url == "https://example.com"
        assert model.title == "Test Title"
        assert model.content == "Test content"

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
    assert WebScrapeInput.model_fields['save_path'].description == "Optional path to save the markdown locally. If not provided, saves to default output directory."
    
    # Check SearchInput
    assert SearchInput.model_fields['query'].description == "The search query."
    assert SearchInput.model_fields['limit'].description == "Maximum number of results to return."
    assert SearchInput.model_fields['k'].description == "Smoothing constant for RRF."
    assert SearchInput.model_fields['vector_weight'].description == "Weight for vector search results."
    assert SearchInput.model_fields['fts_weight'].description == "Weight for full-text search results."
    
    # Check InsertKnowledgeInput
    assert InsertKnowledgeInput.model_fields['url'].description == "The source URL of the content."
    assert InsertKnowledgeInput.model_fields['title'].description == "The title of the content. If not provided, it will be extracted from the URL."
    assert InsertKnowledgeInput.model_fields['content'].description == "The actual text content to insert. If not provided, the URL will be scraped."
    
    # ReadMetadataInput has no fields, so no descriptions to check