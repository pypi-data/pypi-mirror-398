"""
Unit tests for server_tools.py module.
Tests the core logic functions (web_scrape_logic, search_logic, insert_knowledge_logic, read_metadata_logic, get_output_file_logic).
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from pathlib import Path
from contextnest.server_tools import (
    web_scrape_logic, 
    search_logic, 
    insert_knowledge_logic, 
    read_metadata_logic, 
    get_output_file_logic
)
from contextnest.mcp_models import WebScrapeInput, SearchInput, InsertKnowledgeInput, ReadMetadataInput


@pytest.mark.asyncio
class TestWebScrapeLogic:
    """Test cases for web_scrape_logic function."""

    async def test_web_scrape_logic_success(self):
        """Test successful web scraping."""
        input_data = WebScrapeInput(url="https://example.com", save_path="/path/to/save")
        
        with patch('contextnest.server_tools.scrape_url', return_value="Mocked content"):
            result = await web_scrape_logic(input_data)
        
        assert "Successfully scraped https://example.com" in result

    async def test_web_scrape_logic_with_context_success(self):
        """Test successful web scraping with context."""
        input_data = WebScrapeInput(url="https://example.com")
        mock_ctx = AsyncMock()
        
        with patch('contextnest.server_tools.scrape_url', return_value="Mocked content"):
            result = await web_scrape_logic(input_data, ctx=mock_ctx)
        
        mock_ctx.info.assert_called()
        assert "Successfully scraped https://example.com" in result

    async def test_web_scrape_logic_error(self):
        """Test web scraping with error."""
        input_data = WebScrapeInput(url="https://example.com")
        
        with patch('contextnest.server_tools.scrape_url', side_effect=Exception("Scraping failed")):
            result = await web_scrape_logic(input_data)
        
        assert "Error scraping https://example.com: Scraping failed" in result

    async def test_web_scrape_logic_with_context_error(self):
        """Test web scraping with error and context."""
        input_data = WebScrapeInput(url="https://example.com")
        mock_ctx = AsyncMock()
        
        with patch('contextnest.server_tools.scrape_url', side_effect=Exception("Scraping failed")):
            result = await web_scrape_logic(input_data, ctx=mock_ctx)
        
        mock_ctx.error.assert_called_once()
        assert "Error scraping https://example.com: Scraping failed" in result


@pytest.mark.asyncio
class TestSearchLogic:
    """Test cases for search_logic function."""

    async def test_search_logic_success(self):
        """Test successful search."""
        input_data = SearchInput(query="test query", limit=5)
        
        with patch('contextnest.server_tools.DocumentInserter') as mock_inserter_class:
            mock_inserter = MagicMock()
            mock_inserter.get_embedding.return_value = [0.1, 0.2, 0.3]
            mock_inserter_class.return_value = mock_inserter
            
            with patch('contextnest.server_tools.hybrid_search', return_value=[{"result": "test"}]):
                result = await search_logic(input_data)
        
        assert '"result": "test"' in result

    async def test_search_logic_with_context_success(self):
        """Test successful search with context."""
        input_data = SearchInput(query="test query", limit=5)
        mock_ctx = AsyncMock()
        
        with patch('contextnest.server_tools.DocumentInserter') as mock_inserter_class:
            mock_inserter = MagicMock()
            mock_inserter.get_embedding.return_value = [0.1, 0.2, 0.3]
            mock_inserter_class.return_value = mock_inserter
            
            with patch('contextnest.server_tools.hybrid_search', return_value=[{"result": "test"}]):
                result = await search_logic(input_data, ctx=mock_ctx)
        
        mock_ctx.info.assert_called()
        assert '"result": "test"' in result

    async def test_search_logic_error(self):
        """Test search with error."""
        input_data = SearchInput(query="test query", limit=5)
        
        with patch('contextnest.server_tools.DocumentInserter') as mock_inserter_class:
            mock_inserter = MagicMock()
            mock_inserter.get_embedding.side_effect = Exception("Embedding failed")
            mock_inserter_class.return_value = mock_inserter
            
            result = await search_logic(input_data)
        
        assert "Error searching for 'test query': Embedding failed" in result

    async def test_search_logic_with_context_error(self):
        """Test search with error and context."""
        input_data = SearchInput(query="test query", limit=5)
        mock_ctx = AsyncMock()
        
        with patch('contextnest.server_tools.DocumentInserter') as mock_inserter_class:
            mock_inserter = MagicMock()
            mock_inserter.get_embedding.side_effect = Exception("Embedding failed")
            mock_inserter_class.return_value = mock_inserter
            
            result = await search_logic(input_data, ctx=mock_ctx)
        
        mock_ctx.error.assert_called_once()
        assert "Error searching for 'test query': Embedding failed" in result


@pytest.mark.asyncio
class TestInsertKnowledgeLogic:
    """Test cases for insert_knowledge_logic function."""

    async def test_insert_knowledge_logic_with_content(self):
        """Test inserting knowledge with provided content."""
        input_data = InsertKnowledgeInput(
            url="https://example.com", 
            title="Test Title", 
            content="Test content"
        )
        
        with patch('contextnest.server_tools.insert_document') as mock_insert:
            result = await insert_knowledge_logic(input_data)
        
        mock_insert.assert_called_once_with(
            url="https://example.com",
            title="Test Title",
            content="Test content"
        )
        assert "Successfully inserted content from https://example.com ('Test Title')" in result

    async def test_insert_knowledge_logic_with_context_success(self):
        """Test inserting knowledge with context."""
        input_data = InsertKnowledgeInput(
            url="https://example.com", 
            title="Test Title", 
            content="Test content"
        )
        mock_ctx = AsyncMock()
        
        with patch('contextnest.server_tools.insert_document') as mock_insert:
            result = await insert_knowledge_logic(input_data, ctx=mock_ctx)
        
        mock_ctx.info.assert_called()
        assert "Successfully inserted content from https://example.com ('Test Title')" in result

    async def test_insert_knowledge_logic_scraping_content(self):
        """Test inserting knowledge by scraping content."""
        input_data = InsertKnowledgeInput(
            url="https://example.com", 
            title="Test Title"
            # content omitted - defaults to empty string, triggering scraping
        )
        
        with patch('contextnest.server_tools.scrape_url', return_value="Scraped content"):
            with patch('contextnest.server_tools.insert_document') as mock_insert:
                result = await insert_knowledge_logic(input_data)
        
        mock_insert.assert_called_once_with(
            url="https://example.com",
            title="Test Title",
            content="Scraped content"
        )
        assert "Successfully inserted content from https://example.com ('Test Title')" in result

    async def test_insert_knowledge_logic_extract_title_from_markdown(self):
        """Test inserting knowledge with title extracted from markdown."""
        input_data = InsertKnowledgeInput(
            url="https://example.com"
            # title and content omitted - defaults to empty strings
        )
        
        with patch('contextnest.server_tools.scrape_url', return_value="# Scraped Title\nContent here"):
            with patch('contextnest.server_tools.insert_document') as mock_insert:
                result = await insert_knowledge_logic(input_data)
        
        mock_insert.assert_called_once_with(
            url="https://example.com",
            title="Scraped Title",
            content="# Scraped Title\nContent here"
        )
        assert "Successfully inserted content from https://example.com ('Scraped Title')" in result

    async def test_insert_knowledge_logic_use_url_as_title(self):
        """Test inserting knowledge using URL as title when no title and no markdown title."""
        input_data = InsertKnowledgeInput(
            url="https://example.com"
            # title and content omitted - defaults to empty strings
        )
        
        with patch('contextnest.server_tools.scrape_url', return_value="Just content"):
            with patch('contextnest.server_tools.insert_document') as mock_insert:
                result = await insert_knowledge_logic(input_data)
        
        mock_insert.assert_called_once_with(
            url="https://example.com",
            title="Document from https://example.com",
            content="Just content"
        )
        assert "Successfully inserted content from https://example.com ('Document from https://example.com')" in result

    async def test_insert_knowledge_logic_error(self):
        """Test inserting knowledge with error."""
        input_data = InsertKnowledgeInput(
            url="https://example.com", 
            title="Test Title", 
            content="Test content"
        )
        
        with patch('contextnest.server_tools.insert_document', side_effect=Exception("Insert failed")):
            result = await insert_knowledge_logic(input_data)
        
        assert "Error inserting knowledge: Insert failed" in result

    async def test_insert_knowledge_logic_with_context_error(self):
        """Test inserting knowledge with error and context."""
        input_data = InsertKnowledgeInput(
            url="https://example.com", 
            title="Test Title", 
            content="Test content"
        )
        mock_ctx = AsyncMock()
        
        with patch('contextnest.server_tools.insert_document', side_effect=Exception("Insert failed")):
            result = await insert_knowledge_logic(input_data, ctx=mock_ctx)
        
        mock_ctx.error.assert_called_once()
        assert "Error inserting knowledge: Insert failed" in result


class TestReadMetadataLogic:
    """Test cases for read_metadata_logic function."""

    def test_read_metadata_logic_success(self):
        """Test successful metadata reading."""
        mock_metadata_content = '{"key": "value"}'
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=mock_metadata_content)):
                result = read_metadata_logic()
        
        assert result == '{"key": "value"}'

    def test_read_metadata_logic_file_not_found(self):
        """Test metadata reading when file doesn't exist."""
        with patch('pathlib.Path.exists', return_value=False):
            result = read_metadata_logic()
        
        assert result == "No metadata file found."

    def test_read_metadata_logic_error(self):
        """Test metadata reading with error."""
        with patch('pathlib.Path.exists', return_value=True):
            with patch('builtins.open', side_effect=Exception("File read error")):
                result = read_metadata_logic()
        
        assert "Error reading metadata: File read error" in result


@pytest.mark.asyncio
class TestGetOutputFileLogic:
    """Test cases for get_output_file_logic function."""

    async def test_get_output_file_logic_success(self):
        """Test successful output file reading."""
        mock_file_content = "# Test content"
        
        with patch.object(Path, 'exists', return_value=True):
            with patch.object(Path, 'read_text', return_value=mock_file_content):
                result = await get_output_file_logic("test.md")
        
        assert result == "# Test content"

    async def test_get_output_file_logic_file_not_found(self):
        """Test output file reading when file doesn't exist."""
        with patch.object(Path, 'exists', return_value=False):
            with patch.object(Path, 'glob', return_value=[]):
                with pytest.raises(FileNotFoundError, match="File not found: test.md and no other files available."):
                    await get_output_file_logic("test.md")

    async def test_get_output_file_logic_with_context_and_available_files(self):
        """Test output file reading with context when file doesn't exist but alternatives are available."""
        mock_ctx = AsyncMock()
        mock_elicit_result = MagicMock()
        mock_elicit_result.action = "accept"
        mock_elicit_result.data = "alternative.md"
        mock_ctx.elicit.return_value = mock_elicit_result
        
        # Mock exists to return: False (original), True (alternative exists)
        mock_file = MagicMock()
        mock_file.name = "alternative.md"
        
        with patch.object(Path, 'exists', side_effect=[False, True]):
            with patch.object(Path, 'glob', return_value=[mock_file]):
                with patch.object(Path, 'read_text', return_value="# Alternative content"):
                    result = await get_output_file_logic("test.md", ctx=mock_ctx)
        
        assert result == "# Alternative content"
        mock_ctx.elicit.assert_called_once()

    async def test_get_output_file_logic_with_context_declined(self):
        """Test output file reading with context when user declines alternative."""
        mock_ctx = AsyncMock()
        mock_elicit_result = MagicMock()
        mock_elicit_result.action = "decline"
        mock_ctx.elicit.return_value = mock_elicit_result
        
        mock_file = MagicMock()
        mock_file.name = "alternative.md"
        
        with patch.object(Path, 'exists', return_value=False):
            with patch.object(Path, 'glob', return_value=[mock_file]):
                with pytest.raises(FileNotFoundError, match="File not found: test.md and user declined to choose another."):
                    await get_output_file_logic("test.md", ctx=mock_ctx)

    async def test_get_output_file_logic_error(self):
        """Test output file reading with error."""
        with patch('pathlib.Path.exists', side_effect=Exception("File access error")):
            with pytest.raises(Exception, match="File access error"):
                await get_output_file_logic("test.md")