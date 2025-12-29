"""
Unit tests for mcp_client.py module.
Tests the ContextNestClient class with async context managers, connection methods, and tool/resource methods.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, AsyncMock
from pathlib import Path

from contextnest.mcp_client import ContextNestClient


@pytest.fixture
def mock_client():
    """Mock fastmcp Client for testing."""
    with patch('contextnest.mcp_client.Client') as mock_client_class:
        mock_client_instance = AsyncMock()
        mock_client_class.return_value = mock_client_instance
        yield mock_client_instance


@pytest.fixture
def mock_std_io_transport():
    """Mock StdioTransport for testing."""
    with patch('fastmcp.client.transports.StdioTransport') as mock_transport:
        # Ensure the mock is properly set up to avoid AttributeError
        yield mock_transport


@pytest.mark.asyncio
class TestContextNestClient:
    """Test cases for ContextNestClient class."""

    async def test_initialization_with_default_server_script_path(self):
        """Test initialization with default server script path."""
        client = ContextNestClient()
        expected_path = str(Path(__file__).parent.parent.parent / "contextnest" / "mcp_server.py")
        assert client.server_script_path == expected_path
        assert client.elicitation_handler == client._default_elicitation_handler

    async def test_initialization_with_custom_server_script_path(self):
        """Test initialization with custom server script path."""
        custom_path = "/custom/path/server.py"
        client = ContextNestClient(server_script_path=custom_path)
        assert client.server_script_path == custom_path

    async def test_initialization_with_custom_elicitation_handler(self):
        """Test initialization with custom elicitation handler."""
        custom_handler = lambda: "test"
        client = ContextNestClient(elicitation_handler=custom_handler)
        assert client.elicitation_handler == custom_handler

    async def test_async_context_manager(self, mock_client, mock_std_io_transport):
        """Test async context manager functionality."""
        async with ContextNestClient() as client:
            # Connect should have been called
            assert client.client is not None
            # Disconnect should be called when exiting
        mock_client.__aexit__.assert_called_once()

    async def test_connect_method(self, mock_client, mock_std_io_transport):
        """Test the connect method."""
        client = ContextNestClient()
        
        with patch('os.environ.copy', return_value={'TEST': 'value'}):
            await client.connect()
            
        assert client.client is not None
        mock_std_io_transport.assert_called_once()
        mock_client.__aenter__.assert_called_once()

    async def test_disconnect_method(self, mock_client):
        """Test the disconnect method."""
        client = ContextNestClient()
        client.client = mock_client
        
        await client.disconnect()
        
        mock_client.__aexit__.assert_called_once()
        assert client.client is None

    async def test_ensure_connected_when_connected(self):
        """Test _ensure_connected when client is connected."""
        client = ContextNestClient()
        client.client = MagicMock()
        
        # Should not raise an exception
        client._ensure_connected()

    async def test_ensure_connected_when_not_connected(self):
        """Test _ensure_connected when client is not connected."""
        client = ContextNestClient()
        client.client = None
        
        with pytest.raises(RuntimeError, match="Client is not connected"):
            client._ensure_connected()

    async def test_web_scrape_method(self, mock_client):
        """Test the web_scrape method."""
        client = ContextNestClient()
        client.client = mock_client
        
        mock_result = MagicMock()
        mock_result.content = [MagicMock(text="Scrape result")]
        mock_client.call_tool.return_value = mock_result
        
        result = await client.web_scrape()
        
        mock_client.call_tool.assert_called_once_with("web_scrape", arguments={})
        assert result == "Scrape result"

    async def test_search_method(self, mock_client):
        """Test the search method."""
        client = ContextNestClient()
        client.client = mock_client
        
        mock_result = MagicMock()
        mock_result.content = [MagicMock(text="Search results")]
        mock_client.call_tool.return_value = mock_result
        
        result = await client.search()
        
        mock_client.call_tool.assert_called_once_with("search", arguments={})
        assert result == "Search results"

    async def test_insert_knowledge_method(self, mock_client):
        """Test the insert_knowledge method."""
        client = ContextNestClient()
        client.client = mock_client
        
        mock_result = MagicMock()
        mock_result.content = [MagicMock(text="Insert result")]
        mock_client.call_tool.return_value = mock_result
        
        result = await client.insert_knowledge()
        
        mock_client.call_tool.assert_called_once_with("insert_knowledge", arguments={})
        assert result == "Insert result"

    async def test_read_metadata_method(self, mock_client):
        """Test the read_metadata method."""
        client = ContextNestClient()
        client.client = mock_client
        
        mock_result = MagicMock()
        mock_result.content = [MagicMock(text='{"key": "value"}')]
        mock_client.call_tool.return_value = mock_result
        
        result = await client.read_metadata()
        
        mock_client.call_tool.assert_called_once_with("read_metadata", arguments={})
        assert result == '{"key": "value"}'

    async def test_read_metadata_method_with_filter(self, mock_client):
        """Test the read_metadata method with filter."""
        client = ContextNestClient()
        client.client = mock_client
        
        mock_result = MagicMock()
        mock_result.content = [MagicMock(text='{"key": "value"}')]
        mock_client.call_tool.return_value = mock_result
        
        result = await client.read_metadata(filter_by="test_filter")
        
        mock_client.call_tool.assert_called_once_with("read_metadata", arguments={"filter_by": "test_filter"})
        assert result == '{"key": "value"}'

    async def test_get_output_file_method(self, mock_client):
        """Test the get_output_file method."""
        client = ContextNestClient()
        client.client = mock_client
        
        mock_resource = MagicMock()
        mock_resource.contents = [MagicMock(text="File content")]
        mock_client.read_resource.return_value = mock_resource
        
        result = await client.get_output_file("test.md")
        
        mock_client.read_resource.assert_called_once_with("contextnest://output/test.md")
        assert result == "File content"

    async def test_get_metadata_method(self, mock_client):
        """Test the get_metadata method."""
        client = ContextNestClient()
        client.client = mock_client
        
        mock_resource = MagicMock()
        mock_resource.contents = [MagicMock(text='{"metadata": "content"}')]
        mock_client.read_resource.return_value = mock_resource
        
        result = await client.get_metadata()
        
        mock_client.read_resource.assert_called_once_with("contextnest://metadata")
        assert result == '{"metadata": "content"}'

    async def test_list_resources_method(self, mock_client):
        """Test the list_resources method."""
        client = ContextNestClient()
        client.client = mock_client
        
        mock_resource1 = MagicMock()
        mock_resource1.uri = "uri1"
        mock_resource2 = MagicMock()
        mock_resource2.uri = "uri2"
        mock_client.list_resources.return_value = [mock_resource1, mock_resource2]
        
        result = await client.list_resources()
        
        mock_client.list_resources.assert_called_once()
        assert result == ["uri1", "uri2"]

    async def test_get_search_guide_method(self, mock_client):
        """Test the get_search_guide method."""
        client = ContextNestClient()
        client.client = mock_client
        
        mock_prompt = MagicMock()
        mock_prompt.description = "A search guide"
        mock_message = MagicMock()
        mock_message.role = "user"
        mock_message.content.text = "Search instructions"
        mock_prompt.messages = [mock_message]
        mock_client.get_prompt.return_value = mock_prompt
        
        result = await client.get_search_guide()
        
        mock_client.get_prompt.assert_called_once_with("search_guide")
        assert result["description"] == "A search guide"
        assert result["messages"][0]["role"] == "user"
        assert result["messages"][0]["content"] == "Search instructions"

    async def test_list_prompts_method(self, mock_client):
        """Test the list_prompts method."""
        client = ContextNestClient()
        client.client = mock_client
        
        mock_prompt1 = MagicMock()
        mock_prompt1.name = "prompt1"
        mock_prompt2 = MagicMock()
        mock_prompt2.name = "prompt2"
        mock_client.list_prompts.return_value = [mock_prompt1, mock_prompt2]
        
        result = await client.list_prompts()
        
        mock_client.list_prompts.assert_called_once()
        assert result == ["prompt1", "prompt2"]

    async def test_list_tools_method(self, mock_client):
        """Test the list_tools method."""
        client = ContextNestClient()
        client.client = mock_client
        
        mock_tool1 = MagicMock()
        mock_tool1.name = "tool1"
        mock_tool2 = MagicMock()
        mock_tool2.name = "tool2"
        mock_client.list_tools.return_value = [mock_tool1, mock_tool2]
        
        result = await client.list_tools()
        
        mock_client.list_tools.assert_called_once()
        assert result == ["tool1", "tool2"]