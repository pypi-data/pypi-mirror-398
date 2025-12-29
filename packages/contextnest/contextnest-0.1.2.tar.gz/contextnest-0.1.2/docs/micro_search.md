# Micro Search Module Documentation

The micro search module provides powerful search capabilities using a hybrid approach that combines vector similarity search with full-text search (BM25) using Reciprocal Rank Fusion (RRF).

## Features

- **Vector Search**: Semantic search using embeddings
- **Full-Text Search**: Traditional keyword-based search using BM25
- **Hybrid Search**: Combines both approaches using Reciprocal Rank Fusion
- **DuckDB Storage**: Efficient storage and retrieval using DuckDB
- **Embedding Generation**: Supports multiple embedding models

## Architecture

The micro search module consists of several components:

- `database.py`: DuckDB database management
- `insertion.py`: Document insertion logic with chunking and embedding
- `hybrid_search.py`: Vector + BM25 search with RRF ranking
- `db_preparation.py`: Database setup and preparation

## API Reference

### insert_document Function

Inserts a document into the knowledge base:

```python
from contextnest.micro_search import insert_document

insert_document(
    url="https://example.com/doc",
    title="Document Title",
    content="Document content..."
)
```

#### Parameters

- `url` (str): The source URL of the document
- `title` (str): The title of the document
- `content` (str): The full text content of the document

### hybrid_search Function

Performs a hybrid search using vector similarity and BM25:

```python
from contextnest.micro_search import hybrid_search

results = hybrid_search(
    query="search query",
    query_embedding=[0.1, 0.2, 0.3, ...],  # 768-dimensional vector
    limit=5
)
```

#### Parameters

- `query` (str): The search query
- `query_embedding` (list): The embedding vector for the query
- `limit` (int): Maximum number of results to return
- `k` (int): Smoothing constant for RRF (default: 60)
- `embedding_size` (int): Size of the embedding vectors (default: 768)

### HybridSearch Class

For more control over the search process:

```python
from contextnest.micro_search import HybridSearch

searcher = HybridSearch()
results = searcher.search(
    query="search query",
    query_embedding=[0.1, 0.2, 0.3, ...],
    limit=5,
    k=60,
    vector_weight=1.0,
    fts_weight=1.0
)
```

#### Parameters

- `query` (str): The search query
- `query_embedding` (list): The embedding vector for the query
- `limit` (int): Maximum number of results to return
- `k` (int): Smoothing constant for RRF
- `vector_weight` (float): Weight for vector search results
- `fts_weight` (float): Weight for full-text search results

## Embedding Models

The module supports multiple embedding models:

- **Google Gemini**: Uses `gemini-embedding-exp-03-07` model with 768-dimensional vectors
- **Ollama**: Falls back to `nomic-embed-text:latest` model

The system automatically tries Google Gemini first and falls back to Ollama if needed.

## Database Schema

The DuckDB database contains the following tables:

- `documents`: Stores document metadata (URL, title, content)
- `embeddings`: Stores document embeddings for vector search
- `fts_index`: Full-text search index for BM25 search

## Reciprocal Rank Fusion (RRF)

RRF combines results from vector search and full-text search using the formula:

```
RRF_score = 1 / (k + rank)
```

Where `k` is a smoothing constant (default: 60) and `rank` is the position of the document in the ranked list.

The final score is computed as:

```
final_score = vector_weight * vector_rrf_score + fts_weight * fts_rrf_score
```

## Configuration

The search module can be configured through environment variables:

- `SEARCH_DB_PATH`: Path to the DuckDB database (default: `~/.contextnest/documents.duckdb`)
- `SEARCH_EMBEDDING_SIZE`: Size of embedding vectors (default: 768)
- `SEARCH_RRF_K`: Smoothing constant for RRF (default: 60)