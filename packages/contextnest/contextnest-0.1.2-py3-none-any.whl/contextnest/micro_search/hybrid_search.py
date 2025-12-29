"""
Hybrid Search module for ContextNest.
Combines vector similarity search and full-text search (BM25) using 
Reciprocal Rank Fusion (RRF) to produce ranked results.
"""
from typing import Optional
from ..mcp_logger import info_mcp, debug_mcp
from .database import get_database, DocumentDatabase


class HybridSearch:
    """
    Hybrid search combining vector similarity and BM25 full-text search
    using Reciprocal Rank Fusion (RRF) scoring.
    """

    def __init__(self, embedding_size: int = 768):
        """
        Initialize hybrid search with database connection.

        Args:
            embedding_size: Size of the embedding vector (default: 768)
        """
        self.embedding_size = embedding_size
        self.db: Optional[DocumentDatabase] = None

    def _get_db(self) -> DocumentDatabase:
        """Get or create database connection."""
        if self.db is None:
            self.db = get_database(self.embedding_size)
        return self.db

    def _calculate_rrf_scores(
        self, 
        vector_results: list, 
        fts_results: list, 
        k: int = 60
    ) -> dict:
        """
        Calculate Reciprocal Rank Fusion (RRF) scores for documents.

        RRF Formula: RRF_score(d) = sum(1 / (k + rank_i(d)))
        where k is a smoothing constant (default: 60)

        Args:
            vector_results: Results from vector similarity search
            fts_results: Results from full-text search
            k: Smoothing constant for RRF (default: 60)

        Returns:
            Dictionary mapping document IDs to their RRF scores
        """
        rrf_scores = {}
        doc_data = {}  # Store full document data for later retrieval

        # Process vector search results (rank starts at 1)
        for rank, result in enumerate(vector_results, start=1):
            doc_id = str(result[0])  # UUID to string for consistent keys
            rrf_scores[doc_id] = 1 / (k + rank)
            doc_data[doc_id] = {
                'id': result[0],
                'url': result[1],
                'title': result[2],
                'content': result[3],
                'embedding': result[4],
                'vector_rank': rank,
                'vector_distance': result[5] if len(result) > 5 else None,
                'fts_rank': None,
                'bm25_score': None
            }
            debug_mcp(f"Vector result #{rank}: doc_id={doc_id[:8]}..., rrf_contribution={1/(k+rank):.6f}")

        # Process FTS results and add to existing scores
        for rank, result in enumerate(fts_results, start=1):
            doc_id = str(result[0])  # UUID to string for consistent keys
            rrf_contribution = 1 / (k + rank)
            
            if doc_id in rrf_scores:
                rrf_scores[doc_id] += rrf_contribution
                doc_data[doc_id]['fts_rank'] = rank
                doc_data[doc_id]['bm25_score'] = result[5] if len(result) > 5 else None
                debug_mcp(f"FTS result #{rank}: doc_id={doc_id[:8]}... (found in vector), added rrf={rrf_contribution:.6f}")
            else:
                rrf_scores[doc_id] = rrf_contribution
                doc_data[doc_id] = {
                    'id': result[0],
                    'url': result[1],
                    'title': result[2],
                    'content': result[3],
                    'embedding': result[4],
                    'vector_rank': None,
                    'vector_distance': None,
                    'fts_rank': rank,
                    'bm25_score': result[5] if len(result) > 5 else None
                }
                debug_mcp(f"FTS result #{rank}: doc_id={doc_id[:8]}... (new), rrf={rrf_contribution:.6f}")

        return rrf_scores, doc_data

    def search(
        self,
        query: str,
        query_embedding: list,
        limit: int = 5,
        k: int = 60,
        vector_weight: float = 1.0,
        fts_weight: float = 1.0
    ) -> list:
        """
        Perform hybrid search combining vector and full-text search.

        Args:
            query: Text query for full-text search
            query_embedding: Embedding vector for similarity search
            limit: Maximum number of results to return
            k: Smoothing constant for RRF (default: 60)
            vector_weight: Weight for vector search results (default: 1.0)
            fts_weight: Weight for FTS results (default: 1.0)

        Returns:
            List of tuples: (doc_id, url, title, content, rrf_score, vector_rank, fts_rank)
        """
        db = self._get_db()
        
        # Fetch more results than needed for better fusion
        fetch_limit = limit * 3

        info_mcp(f"Performing hybrid search for query: '{query[:50]}...'")

        # Perform vector similarity search
        vector_results = db.search_vector_similarity(query_embedding, limit=fetch_limit)
        info_mcp(f"Vector search returned {len(vector_results)} results")

        # Perform full-text search with BM25
        fts_results = db.search_full_text(query, limit=fetch_limit)
        info_mcp(f"Full-text search returned {len(fts_results)} results")

        # Calculate RRF scores
        rrf_scores, doc_data = self._calculate_rrf_scores(vector_results, fts_results, k)

        # Apply weights if specified
        if vector_weight != 1.0 or fts_weight != 1.0:
            for doc_id in rrf_scores:
                weighted_score = 0
                data = doc_data[doc_id]
                if data['vector_rank'] is not None:
                    weighted_score += vector_weight * (1 / (k + data['vector_rank']))
                if data['fts_rank'] is not None:
                    weighted_score += fts_weight * (1 / (k + data['fts_rank']))
                rrf_scores[doc_id] = weighted_score

        # Sort by RRF score (descending) and limit results
        sorted_results = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:limit]

        # Build final result list with full document data
        final_results = []
        for doc_id, rrf_score in sorted_results:
            data = doc_data[doc_id]
            final_results.append({
                'id': data['id'],
                'url': data['url'],
                'title': data['title'],
                'content': data['content'],
                'rrf_score': rrf_score,
                'vector_rank': data['vector_rank'],
                'fts_rank': data['fts_rank'],
                'vector_distance': data['vector_distance'],
                'bm25_score': data['bm25_score']
            })

        info_mcp(f"Hybrid search returned {len(final_results)} results")
        return final_results

    def close(self):
        """Close the database connection."""
        if self.db:
            self.db.close()
            self.db = None
            info_mcp("Hybrid search database connection closed")


def hybrid_search(
    query: str,
    query_embedding: list,
    limit: int = 5,
    k: int = 60,
    embedding_size: int = 768
) -> list:
    """
    Convenience function to perform hybrid search.

    Args:
        query: Text query for full-text search
        query_embedding: Embedding vector for similarity search
        limit: Maximum number of results to return
        k: Smoothing constant for RRF (default: 60)
        embedding_size: Size of the embedding vector (default: 768)

    Returns:
        List of result dictionaries with document data and scores
    """
    searcher = HybridSearch(embedding_size=embedding_size)
    try:
        results = searcher.search(query, query_embedding, limit=limit, k=k)
        return results
    finally:
        searcher.close()
