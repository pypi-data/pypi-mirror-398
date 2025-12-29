import uuid
from typing import Optional
from ..mcp_logger import info_mcp, debug_mcp, warning_mcp
from .db_preparation import prepare_micro_search_db


class DocumentDatabase:
    """
    Database module for managing document storage and retrieval with full-text search
    and vector similarity search capabilities.
    """

    def __init__(self, embedding_size: int = 768):
        """
        Initialize the database connection and create tables if they don't exist.

        Args:
            embedding_size: Size of the embedding vector
        """
        self.embedding_size = embedding_size
        self.db_prep = prepare_micro_search_db()
        self.conn = self.db_prep.get_database_connection()
        self._create_tables()
        self._create_indices()

    def _create_tables(self):
        """Create the documents table if it doesn't exist."""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                url TEXT,
                title TEXT,
                content TEXT,
                embedding FLOAT[{embedding_size}]  -- Using FLOAT[] for vector storage
            )
        """.format(embedding_size=self.embedding_size))
        info_mcp("Documents table created or verified")

    def _create_indices(self):
        """Create vector similarity search indices and FTS index."""

        # Check if vector similarity search index already exists
        result = self.conn.execute("""
            SELECT COUNT(*)
            FROM duckdb_indexes
            WHERE index_name = 'documents_vss'
        """).fetchone()

        if result[0] == 0:
            # Create vector similarity search index on embedding if it doesn't exist
            self.conn.execute("""
                CREATE INDEX documents_vss
                ON documents
                USING HNSW (embedding)
                WITH (metric = 'cosine');
            """)
            info_mcp("Vector similarity search index created on embedding")
        else:
            info_mcp("Vector similarity search index already exists, skipping creation")

        # Create FTS index for BM25 full-text search
        self._create_fts_index()

    def _create_fts_index(self):
        """Create Full-Text Search index for BM25 scoring on content and title columns."""
        try:
            # Check if FTS index schema exists
            result = self.conn.execute("""
                SELECT COUNT(*)
                FROM information_schema.schemata
                WHERE schema_name = 'fts_main_documents'
            """).fetchone()

            if result[0] == 0:
                # Create FTS index on content and title columns
                self.conn.execute("""
                    PRAGMA create_fts_index(
                        'documents',
                        'id',
                        'content',
                        'title',
                        stemmer = 'porter',
                        stopwords = 'english',
                        overwrite = 0
                    )
                """)
                info_mcp("FTS index created for BM25 search on content and title")
            else:
                info_mcp("FTS index already exists, skipping creation")
        except Exception as e:
            warning_mcp(f"Could not create FTS index: {e}. Full-text search may not be available.")

    def search_full_text(self, query: str, limit: int = 5):
        """
        Perform full-text search using BM25 scoring.

        Args:
            query: Text query to search for
            limit: Maximum number of results to return

        Returns:
            List of documents with BM25 scores, ordered by relevance
        """
        try:
            result = self.conn.execute(
                """
                SELECT id, url, title, content, embedding, bm25_score
                FROM (
                    SELECT *,
                           fts_main_documents.match_bm25(id, ?) AS bm25_score
                    FROM documents
                ) sq
                WHERE bm25_score IS NOT NULL
                ORDER BY bm25_score DESC
                LIMIT ?
                """,
                [query, limit]
            ).fetchall()
            debug_mcp(f"Full-text search returned {len(result)} results for query: '{query}'")
            return result
        except Exception as e:
            warning_mcp(f"Full-text search failed: {e}. Returning empty results.")
            return []


    def insert_document(self, url: str, title: str, content: str, embedding: Optional[list] = None):
        """
        Insert a document into the database.

        Args:
            url: URL of the document
            title: Title of the document
            content: Content of the document
            embedding: Vector embedding of the document (optional)

        Returns:
            UUID: The ID of the inserted document
        """
        doc_id = uuid.uuid4()
        self.conn.execute(
            """
            INSERT INTO documents (id, url, title, content, embedding)
            VALUES (?, ?, ?, ?, ?)
            """,
            [doc_id, url, title, content, embedding]
        )
        debug_mcp(f"Inserted document with ID: {doc_id}")
        return doc_id

    def search_vector_similarity(self, query_embedding: list, limit: int = 5):
        """
        Perform vector similarity search using cosine distance.

        Args:
            query_embedding: Embedding vector to search for similar documents
            limit: Maximum number of results to return

        Returns:
            List of similar documents with cosine distance
        """
        # Convert query embedding to the same type as stored embeddings (FLOAT)
        query_embedding_float = [float(x) for x in query_embedding]

        # Cast the embedding to FLOAT array to match the stored type
        # Note: DuckDB doesn't support ? placeholders in type definitions, so we use string formatting for embedding_size
        result = self.conn.execute(
            f"""
            SELECT *,
                   array_cosine_distance(embedding, CAST(? AS FLOAT[{self.embedding_size}])) AS cosine_distance
            FROM documents
            WHERE embedding IS NOT NULL
            ORDER BY cosine_distance ASC NULLS LAST
            LIMIT ?
            """,
            [query_embedding_float, limit]
        ).fetchall()
        debug_mcp(f"Vector similarity search returned {len(result)} results")
        return result

    def get_document_by_id(self, doc_id: uuid.UUID):
        """
        Retrieve a document by its ID.

        Args:
            doc_id: UUID of the document

        Returns:
            Document record or None if not found
        """
        result = self.conn.execute(
            "SELECT * FROM documents WHERE id = ?", [doc_id]
        ).fetchone()
        debug_mcp(f"Retrieved document by ID: {doc_id}")
        return result

    def get_document_by_url(self, url: str):
        """
        Retrieve a document by its URL.

        Args:
            url: URL of the document

        Returns:
            Document record or None if not found
        """
        result = self.conn.execute(
            "SELECT * FROM documents WHERE url = ?", [url]
        ).fetchone()
        debug_mcp(f"Retrieved document by URL: {url}")
        return result

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            info_mcp("Database connection closed")


def get_database(embedding_size: int = 768) -> DocumentDatabase:
    """
    Factory function to get a database instance.

    Returns:
        DocumentDatabase instance
    """
    return DocumentDatabase(embedding_size)