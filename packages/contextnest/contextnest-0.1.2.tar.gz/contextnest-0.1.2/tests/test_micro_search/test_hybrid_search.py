"""
Unit tests for micro_search.hybrid_search module.
Tests hybrid search functionality, RRF scoring, and search methods.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from contextnest.micro_search.hybrid_search import HybridSearch, hybrid_search


class TestHybridSearch:
    """Test cases for HybridSearch class."""

    def test_initialization(self):
        """Test HybridSearch initialization."""
        searcher = HybridSearch(embedding_size=256)
        assert searcher.embedding_size == 256
        assert searcher.db is None

    @patch('contextnest.micro_search.hybrid_search.get_database')
    def test_get_db(self, mock_get_database):
        """Test _get_db method."""
        mock_db = Mock()
        mock_get_database.return_value = mock_db
        
        searcher = HybridSearch()
        db = searcher._get_db()
        
        assert db is mock_db
        mock_get_database.assert_called_once_with(768)

    @patch('contextnest.micro_search.hybrid_search.get_database')
    def test_calculate_rrf_scores(self, mock_get_database):
        """Test _calculate_rrf_scores method."""
        mock_db = Mock()
        mock_get_database.return_value = mock_db
        
        searcher = HybridSearch()
        vector_results = [
            ('id1', 'url1', 'title1', 'content1', [0.1, 0.2], 0.3),  # id, url, title, content, embedding, distance
            ('id2', 'url2', 'title2', 'content2', [0.2, 0.3], 0.4)
        ]
        fts_results = [
            ('id1', 'url1', 'title1', 'content1', [0.1, 0.2], 0.8),  # id, url, title, content, embedding, bm25_score
            ('id3', 'url3', 'title3', 'content3', [0.3, 0.4], 0.6)
        ]
        
        rrf_scores, doc_data = searcher._calculate_rrf_scores(vector_results, fts_results, k=60)
        
        # Verify RRF scores are calculated correctly
        assert 'id1' in rrf_scores
        assert 'id2' in rrf_scores
        assert 'id3' in rrf_scores
        
        # id1 appears in both results, so its score should be the sum
        expected_id1_score = 1/(60+1) + 1/(60+1)  # rank 1 in both
        assert abs(rrf_scores['id1'] - expected_id1_score) < 0.0001
        
        # id2 appears only in vector results
        expected_id2_score = 1/(60+2)  # rank 2
        assert abs(rrf_scores['id2'] - expected_id2_score) < 0.0001
        
        # id3 appears only in FTS results
        expected_id3_score = 1/(60+2)  # rank 2
        assert abs(rrf_scores['id3'] - expected_id3_score) < 0.0001

    @patch('contextnest.micro_search.hybrid_search.get_database')
    def test_search_method(self, mock_get_database):
        """Test search method."""
        mock_db = Mock()
        mock_db.search_vector_similarity.return_value = [
            ('id1', 'url1', 'title1', 'content1', [0.1, 0.2], 0.3),
            ('id2', 'url2', 'title2', 'content2', [0.2, 0.3], 0.4)
        ]
        mock_db.search_full_text.return_value = [
            ('id1', 'url1', 'title1', 'content1', [0.1, 0.2], 0.8),
            ('id3', 'url3', 'title3', 'content3', [0.3, 0.4], 0.6)
        ]
        mock_get_database.return_value = mock_db
        
        searcher = HybridSearch()
        results = searcher.search(
            query="test query",
            query_embedding=[0.1, 0.2],
            limit=5,
            k=60,
            vector_weight=1.0,
            fts_weight=1.0
        )
        
        # Verify database methods were called
        mock_db.search_vector_similarity.assert_called_once()
        mock_db.search_full_text.assert_called_once()
        
        # Verify results structure
        assert isinstance(results, list)
        for result in results:
            assert 'id' in result
            assert 'url' in result
            assert 'title' in result
            assert 'content' in result
            assert 'rrf_score' in result

    @patch('contextnest.micro_search.hybrid_search.get_database')
    def test_search_method_with_weights(self, mock_get_database):
        """Test search method with custom weights."""
        mock_db = Mock()
        mock_db.search_vector_similarity.return_value = [
            ('id1', 'url1', 'title1', 'content1', [0.1, 0.2], 0.3)
        ]
        mock_db.search_full_text.return_value = [
            ('id1', 'url1', 'title1', 'content1', [0.1, 0.2], 0.8)
        ]
        mock_get_database.return_value = mock_db
        
        searcher = HybridSearch()
        results = searcher.search(
            query="test query",
            query_embedding=[0.1, 0.2],
            limit=5,
            k=60,
            vector_weight=2.0,  # Higher weight
            fts_weight=0.5    # Lower weight
        )
        
        # Verify results were computed with weights
        assert isinstance(results, list)

    @patch('contextnest.micro_search.hybrid_search.get_database')
    def test_close_method(self, mock_get_database):
        """Test close method."""
        mock_db = Mock()
        mock_get_database.return_value = mock_db
        
        searcher = HybridSearch()
        searcher.db = mock_db
        searcher.close()
        
        mock_db.close.assert_called_once()
        assert searcher.db is None


def test_hybrid_search_convenience_function():
    """Test the hybrid_search convenience function."""
    with patch('contextnest.micro_search.hybrid_search.HybridSearch') as mock_searcher_class:
        mock_searcher = Mock()
        mock_searcher.search.return_value = [{"result": "test"}]
        mock_searcher_class.return_value = mock_searcher
        
        results = hybrid_search(
            query="test query",
            query_embedding=[0.1, 0.2],
            limit=5,
            k=60,
            embedding_size=128
        )
        
        mock_searcher_class.assert_called_once_with(embedding_size=128)
        mock_searcher.search.assert_called_once_with("test query", [0.1, 0.2], limit=5, k=60)
        mock_searcher.close.assert_called_once()
        assert results == [{"result": "test"}]