"""
Unit tests for micro_search module.
Tests database operations, hybrid search, and document insertion.
"""
import pytest
import asyncio
from unittest.mock import Mock, MagicMock, patch, mock_open
from contextnest.micro_search.database import DocumentDatabase, get_database
from contextnest.micro_search.hybrid_search import HybridSearch, hybrid_search
from contextnest.micro_search.insertion import DocumentInserter, insert_document


class TestDocumentDatabase:
    """Test cases for DocumentDatabase class."""

    @patch('contextnest.micro_search.database.prepare_micro_search_db')
    def test_initialization(self, mock_db_prep):
        """Test DocumentDatabase initialization."""
        mock_db_instance = Mock()
        mock_db_prep.return_value = mock_db_instance
        mock_conn = Mock()
        mock_db_instance.get_database_connection.return_value = mock_conn

        # Mock the fetchone return values to be compatible with subscriptable access
        mock_conn.execute.return_value.fetchone.return_value = (0,)

        db = DocumentDatabase(embedding_size=128)

        assert db.embedding_size == 128
        assert db.conn is mock_conn
        assert db.db_prep is mock_db_instance

    @patch('contextnest.micro_search.database.prepare_micro_search_db')
    def test_create_tables(self, mock_db_prep):
        """Test table creation."""
        mock_db_instance = Mock()
        mock_db_prep.return_value = mock_db_instance
        mock_conn = Mock()
        mock_db_instance.get_database_connection.return_value = mock_conn

        # Mock the fetchone return values to be compatible with subscriptable access
        mock_conn.execute.return_value.fetchone.return_value = (0,)

        db = DocumentDatabase(embedding_size=128)
        db._create_tables()

        # Verify the CREATE TABLE statement was executed
        mock_conn.execute.assert_called()
        # Check that at least one call contains CREATE TABLE
        calls = mock_conn.execute.call_args_list
        create_table_called = any("CREATE TABLE" in str(call) for call in calls)
        assert create_table_called

    @patch('contextnest.micro_search.database.prepare_micro_search_db')
    def test_create_indices(self, mock_db_prep):
        """Test index creation."""
        mock_db_instance = Mock()
        mock_db_prep.return_value = mock_db_instance
        mock_conn = Mock()
        mock_conn.execute.return_value.fetchone.return_value = (0,)  # Index doesn't exist (tuple instead of list)
        mock_db_instance.get_database_connection.return_value = mock_conn

        db = DocumentDatabase(embedding_size=128)
        db._create_indices()

        # Verify index creation statements were executed
        assert mock_conn.execute.call_count >= 1

    @patch('contextnest.micro_search.database.prepare_micro_search_db')
    def test_search_full_text(self, mock_db_prep):
        """Test full-text search."""
        mock_db_instance = Mock()
        mock_db_prep.return_value = mock_db_instance
        mock_conn = Mock()
        mock_result = Mock()
        mock_result.fetchall.return_value = [('id1', 'url1', 'title1', 'content1', [0.1, 0.2], 0.5)]

        def execute_side_effect(*args, **kwargs):
            if 'SELECT COUNT(*)' in str(args[0]) if args else False:
                mock_cursor = Mock()
                mock_cursor.fetchone.return_value = (0,)
                return mock_cursor
            else:
                return mock_result

        mock_conn.execute.side_effect = execute_side_effect
        mock_db_instance.get_database_connection.return_value = mock_conn

        db = DocumentDatabase(embedding_size=128)
        results = db.search_full_text("test query", limit=5)

        assert len(results) == 1
        assert results[0][0] == 'id1'
        assert mock_conn.execute.call_count >= 1

    @patch('contextnest.micro_search.database.prepare_micro_search_db')
    def test_search_full_text_error(self, mock_db_prep):
        """Test full-text search with error."""
        mock_db_instance = Mock()
        mock_db_prep.return_value = mock_db_instance
        mock_conn = Mock()
        
        # Track the call count to return different values
        call_count = [0]
        def execute_side_effect(*args, **kwargs):
            call_count[0] += 1
            mock_cursor = Mock()
            # First calls are for table/index creation
            if call_count[0] <= 3:  # Allow init calls to succeed
                mock_cursor.fetchone.return_value = (0,)
                return mock_cursor
            else:
                # FTS query should fail
                raise Exception("FTS error")

        mock_conn.execute.side_effect = execute_side_effect
        mock_db_instance.get_database_connection.return_value = mock_conn

        db = DocumentDatabase(embedding_size=128)
        results = db.search_full_text("test query", limit=5)

        assert results == []

    @patch('contextnest.micro_search.database.prepare_micro_search_db')
    def test_insert_document(self, mock_db_prep):
        """Test document insertion."""
        mock_db_instance = Mock()
        mock_db_prep.return_value = mock_db_instance
        mock_conn = Mock()
        mock_conn.execute.return_value.fetchone.return_value = (0,)  # For index check
        mock_db_instance.get_database_connection.return_value = mock_conn

        db = DocumentDatabase(embedding_size=128)
        doc_id = db.insert_document("https://example.com", "Test Title", "Test content", [0.1, 0.2])

        # Check that execute was called at least once for insert
        assert mock_conn.execute.call_count >= 1
        # Verify that a UUID was generated and used
        assert doc_id is not None

    @patch('contextnest.micro_search.database.prepare_micro_search_db')
    def test_search_vector_similarity(self, mock_db_prep):
        """Test vector similarity search."""
        mock_db_instance = Mock()
        mock_db_prep.return_value = mock_db_instance
        mock_conn = Mock()
        mock_result = Mock()
        mock_result.fetchall.return_value = [('id1', 'url1', 'title1', 'content1', [0.1, 0.2], 0.3)]

        def execute_side_effect(*args, **kwargs):
            if 'SELECT COUNT(*)' in str(args[0]) if args else False:
                mock_cursor = Mock()
                mock_cursor.fetchone.return_value = (0,)
                return mock_cursor
            else:
                return mock_result

        mock_conn.execute.side_effect = execute_side_effect
        mock_db_instance.get_database_connection.return_value = mock_conn

        db = DocumentDatabase(embedding_size=2)
        results = db.search_vector_similarity([0.1, 0.2], limit=5)

        assert len(results) == 1
        assert results[0][0] == 'id1'
        # The execute method is called multiple times for index creation/checks
        assert mock_conn.execute.call_count >= 1

    @patch('contextnest.micro_search.database.prepare_micro_search_db')
    def test_get_document_by_id(self, mock_db_prep):
        """Test getting document by ID."""
        mock_db_instance = Mock()
        mock_db_prep.return_value = mock_db_instance
        mock_conn = Mock()
        mock_result = Mock()
        mock_result.fetchone.return_value = ('id1', 'url1', 'title1', 'content1', [0.1, 0.2])
        def execute_side_effect(*args, **kwargs):
            if 'SELECT COUNT(*)' in str(args[0]) if args else False:
                mock_cursor = Mock()
                mock_cursor.fetchone.return_value = (0,)
                return mock_cursor
            else:
                return mock_result
        mock_conn.execute.side_effect = execute_side_effect
        mock_db_instance.get_database_connection.return_value = mock_conn

        db = DocumentDatabase(embedding_size=128)
        result = db.get_document_by_id('test-uuid')

        assert result is not None
        assert result[0] == 'id1'
        # Execute is called multiple times for index creation/checks
        assert mock_conn.execute.call_count >= 1

    @patch('contextnest.micro_search.database.prepare_micro_search_db')
    def test_get_document_by_url(self, mock_db_prep):
        """Test getting document by URL."""
        mock_db_instance = Mock()
        mock_db_prep.return_value = mock_db_instance
        mock_conn = Mock()
        mock_result = Mock()
        mock_result.fetchone.return_value = ('id1', 'url1', 'title1', 'content1', [0.1, 0.2])
        def execute_side_effect(*args, **kwargs):
            if 'SELECT COUNT(*)' in str(args[0]) if args else False:
                mock_cursor = Mock()
                mock_cursor.fetchone.return_value = (0,)
                return mock_cursor
            else:
                return mock_result
        mock_conn.execute.side_effect = execute_side_effect
        mock_db_instance.get_database_connection.return_value = mock_conn

        db = DocumentDatabase(embedding_size=128)
        result = db.get_document_by_url('https://example.com')

        assert result is not None
        assert result[0] == 'id1'
        # Execute is called multiple times for index creation/checks
        assert mock_conn.execute.call_count >= 1

    @patch('contextnest.micro_search.database.prepare_micro_search_db')
    def test_close(self, mock_db_prep):
        """Test closing database connection."""
        mock_db_instance = Mock()
        mock_db_prep.return_value = mock_db_instance
        mock_conn = Mock()

        def execute_side_effect(*args, **kwargs):
            # For index check during init
            mock_cursor = Mock()
            mock_cursor.fetchone.return_value = (0,)
            return mock_cursor

        mock_conn.execute.side_effect = execute_side_effect
        mock_db_instance.get_database_connection.return_value = mock_conn

        db = DocumentDatabase(embedding_size=128)
        db.close()

        mock_conn.close.assert_called_once()


def test_get_database():
    """Test the get_database factory function."""
    with patch('contextnest.micro_search.database.DocumentDatabase') as mock_db_class:
        mock_instance = Mock()
        mock_db_class.return_value = mock_instance

        db = get_database(embedding_size=256)

        # The constructor is called with positional argument, not keyword
        mock_db_class.assert_called_once_with(256)
        assert db is mock_instance