"""
Unit tests for micro_search.insertion module.
Tests document processing, chunking, embedding, and database insertion.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch, mock_open
from contextnest.micro_search.insertion import DocumentInserter, insert_document


class TestDocumentInserter:
    """Test cases for DocumentInserter class."""

    @patch('contextnest.micro_search.insertion.genai')
    def test_initialization(self, mock_genai):
        """Test DocumentInserter initialization."""
        inserter = DocumentInserter(max_characters=1000)
        assert inserter.max_characters == 1000
        assert inserter.splitter is not None

    @patch('contextnest.micro_search.insertion.genai')
    def test_split_content(self, mock_genai):
        """Test content splitting."""
        # max_characters must be larger than chunk_overlap (500) to be valid
        inserter = DocumentInserter(max_characters=1000)
        content = "This is a test content that will be split into chunks. " * 50  # Make it long enough to split
        
        chunks = inserter.split_content(content)
        
        assert isinstance(chunks, list)
        assert len(chunks) > 0
        # Just verify we got chunks
        for chunk in chunks:
            assert isinstance(chunk, str)
            assert len(chunk) > 0

    @patch('contextnest.micro_search.insertion.genai')
    @patch('contextnest.micro_search.insertion.ollama')
    def test_get_ollama_embedding(self, mock_ollama, mock_genai):
        """Test Ollama embedding generation."""
        mock_ollama.embeddings.return_value = {'embedding': [0.1, 0.2, 0.3]}
        
        inserter = DocumentInserter()
        embedding = inserter._get_ollama_embedding("test text")
        
        assert embedding == [0.1, 0.2, 0.3]
        mock_ollama.embeddings.assert_called_once_with(
            model="nomic-embed-text:latest",
            prompt="test text"
        )

    @patch('contextnest.micro_search.insertion.genai')
    @patch('contextnest.micro_search.insertion.ollama')
    def test_get_ollama_embedding_missing_result(self, mock_ollama, mock_genai):
        """Test Ollama embedding with missing result."""
        mock_ollama.embeddings.return_value = {'other_field': 'value'}
        
        inserter = DocumentInserter()
        with pytest.raises(ValueError, match="No embedding returned for text"):
            inserter._get_ollama_embedding("test text")

    @patch('contextnest.micro_search.insertion.genai')
    @patch('contextnest.micro_search.insertion.np')
    def test_get_gemini_embedding(self, mock_np, mock_genai):
        """Test Gemini embedding generation."""
        mock_client = Mock()
        mock_response = Mock()
        mock_embeddings_obj = Mock()
        mock_embeddings_obj.values = [0.1, 0.2, 0.3]
        mock_response.embeddings = [mock_embeddings_obj]
        mock_client.models.embed_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client

        # Create a proper mock numpy array that supports tolist()
        mock_array = Mock()
        mock_normed_array = Mock()
        mock_normed_array.tolist.return_value = [0.1, 0.2, 0.3]
        mock_array.__truediv__ = Mock(return_value=mock_normed_array)
        mock_np.array.return_value = mock_array
        mock_np.linalg.norm.return_value = 1.0

        inserter = DocumentInserter()
        embedding = inserter._get_gemini_embedding("test text")

        assert embedding == [0.1, 0.2, 0.3]

    @patch('contextnest.micro_search.insertion.genai')
    @patch('contextnest.micro_search.insertion.np')
    @patch('contextnest.micro_search.insertion.ollama')
    def test_get_embedding_with_local_model(self, mock_ollama, mock_np, mock_genai):
        """Test get_embedding with local model (Ollama)."""
        mock_ollama.embeddings.return_value = {'embedding': [0.4, 0.5, 0.6]}
        
        inserter = DocumentInserter()
        embedding = inserter.get_embedding("test text", local_model=True)
        
        assert embedding == [0.4, 0.5, 0.6]
        mock_ollama.embeddings.assert_called_once()

    @patch('contextnest.micro_search.insertion.genai')
    @patch('contextnest.micro_search.insertion.np')
    @patch('contextnest.micro_search.insertion.ollama')
    def test_get_embedding_with_remote_model_success(self, mock_ollama, mock_np, mock_genai):
        """Test get_embedding with remote model (Gemini) success."""
        mock_client = Mock()
        mock_response = Mock()
        mock_embeddings_obj = Mock()
        mock_embeddings_obj.values = [0.1, 0.2, 0.3]
        mock_response.embeddings = [mock_embeddings_obj]
        mock_client.models.embed_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client
        
        # Create a proper mock numpy array that supports tolist()
        mock_array = Mock()
        mock_normed_array = Mock()
        mock_normed_array.tolist.return_value = [0.1, 0.2, 0.3]
        mock_array.__truediv__ = Mock(return_value=mock_normed_array)
        mock_np.array.return_value = mock_array
        mock_np.linalg.norm.return_value = 1.0
        
        inserter = DocumentInserter()
        embedding = inserter.get_embedding("test text", local_model=False)
        
        assert embedding == [0.1, 0.2, 0.3]
        mock_client.models.embed_content.assert_called_once()

    @patch('contextnest.micro_search.insertion.genai')
    @patch('contextnest.micro_search.insertion.np')
    @patch('contextnest.micro_search.insertion.ollama')
    def test_get_embedding_with_remote_model_fallback(self, mock_ollama, mock_np, mock_genai):
        """Test get_embedding with remote model fallback to Ollama."""
        # Create a mock client instance that will throw an exception when embed_content is called
        mock_client = Mock()
        mock_client.models.embed_content.side_effect = Exception("Gemini error")
        mock_genai.Client.return_value = mock_client

        mock_np.array.return_value = [0.7, 0.8, 0.9]
        mock_np.linalg.norm.return_value = 1.0
        mock_ollama.embeddings.return_value = {'embedding': [0.7, 0.8, 0.9]}

        inserter = DocumentInserter()
        embedding = inserter.get_embedding("test text", local_model=False)

        assert embedding == [0.7, 0.8, 0.9]
        mock_client.models.embed_content.assert_called_once()
        mock_ollama.embeddings.assert_called_once()

    @patch('contextnest.micro_search.insertion.genai')
    @patch('contextnest.micro_search.insertion.get_database')
    @patch('contextnest.micro_search.insertion.DocumentInserter.get_embedding')
    @patch('contextnest.micro_search.insertion.DocumentInserter.split_content')
    def test_insert_document_chunks(self, mock_split_content, mock_get_embedding, mock_get_database, mock_genai):
        """Test document chunk insertion."""
        # Mock the database
        mock_db = Mock()
        mock_db.db_prep.is_url_in_database.return_value = False
        mock_db.db_prep.add_links_to_db_metadata.return_value = None
        mock_get_database.return_value = mock_db
        
        # Mock the embedding and splitting
        mock_split_content.return_value = ["chunk1", "chunk2"]
        mock_get_embedding.return_value = [0.1, 0.2, 0.3]
        
        inserter = DocumentInserter()
        inserter.insert_document_chunks(
            url="https://example.com",
            title="Test Title",
            content="Test content"
        )
        
        # Verify database methods were called
        mock_db.db_prep.is_url_in_database.assert_called_once_with("https://example.com")
        mock_db.db_prep.add_links_to_db_metadata.assert_called_once()
        mock_split_content.assert_called_once_with("Test content")
        assert mock_get_embedding.call_count == 2  # Called for each chunk
        assert mock_db.insert_document.call_count == 2  # Called for each chunk

    @patch('contextnest.micro_search.insertion.genai')
    @patch('contextnest.micro_search.insertion.get_database')
    @patch('contextnest.micro_search.insertion.DocumentInserter.get_embedding')
    @patch('contextnest.micro_search.insertion.DocumentInserter.split_content')
    def test_insert_document_chunks_url_exists(self, mock_split_content, mock_get_embedding, mock_get_database, mock_genai):
        """Test document chunk insertion when URL already exists."""
        # Mock the database
        mock_db = Mock()
        mock_db.db_prep.is_url_in_database.return_value = True
        mock_get_database.return_value = mock_db
        
        inserter = DocumentInserter()
        inserter.insert_document_chunks(
            url="https://example.com",
            title="Test Title",
            content="Test content"
        )
        
        # Verify that document processing was skipped
        mock_split_content.assert_not_called()
        mock_get_embedding.assert_not_called()
        mock_db.insert_document.assert_not_called()

    @patch('contextnest.micro_search.insertion.genai')
    @patch('contextnest.micro_search.insertion.get_database')
    @patch('contextnest.micro_search.insertion.DocumentInserter.get_embedding')
    @patch('contextnest.micro_search.insertion.DocumentInserter.split_content')
    def test_insert_document_chunks_with_error(self, mock_split_content, mock_get_embedding, mock_get_database, mock_genai):
        """Test document chunk insertion with error."""
        # Mock the database
        mock_db = Mock()
        mock_db.db_prep.is_url_in_database.return_value = False
        mock_db.db_prep.add_links_to_db_metadata.return_value = None
        mock_get_database.return_value = mock_db
        
        # Mock the splitting to raise an error
        mock_split_content.side_effect = Exception("Split error")
        
        inserter = DocumentInserter()
        with pytest.raises(Exception, match="Split error"):
            inserter.insert_document_chunks(
                url="https://example.com",
                title="Test Title",
                content="Test content"
            )


def test_insert_document_convenience_function():
    """Test the insert_document convenience function."""
    with patch('contextnest.micro_search.insertion.DocumentInserter') as mock_inserter_class:
        mock_inserter = Mock()
        mock_inserter_class.return_value = mock_inserter
        
        insert_document("https://example.com", "Test Title", "Test content")
        
        mock_inserter_class.assert_called_once()
        mock_inserter.insert_document_chunks.assert_called_once_with(
            "https://example.com", "Test Title", "Test content"
        )