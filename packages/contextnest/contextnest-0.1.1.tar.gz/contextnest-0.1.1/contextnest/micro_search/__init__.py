"""
Micro-search module for ContextNest.
This module provides functionality for preparing and managing DuckDB databases
with vector search, full-text search (BM25), and hybrid search capabilities.
"""

from .db_preparation import DatabasePreparation, prepare_micro_search_db, is_url_in_metadata 
from .database import DocumentDatabase, get_database
from .insertion import insert_document, DocumentInserter
from .hybrid_search import HybridSearch, hybrid_search

__all__ = [
    "DatabasePreparation",
    "prepare_micro_search_db",
    "DocumentDatabase",
    "get_database",
    "insert_document",
    "DocumentInserter",
    "is_url_in_metadata",
    "HybridSearch",
    "hybrid_search"
]