"""
Test script for hybrid search functionality.
"""
from contextnest.micro_search import HybridSearch, get_database
from contextnest.micro_search.insertion import DocumentInserter

# Test hybrid search with existing data
print('Testing hybrid search...')

# Create a query embedding using Gemini (or Ollama fallback)
query = 'machine learning scikit-learn'

# Use DocumentInserter to get embedding
inserter = DocumentInserter()
query_embedding = inserter.get_embedding(query)
print(f'Generated query embedding of length {len(query_embedding)}')

# Perform hybrid search
searcher = HybridSearch()
results = searcher.search(query, query_embedding, limit=3)

print(f'Hybrid search found {len(results)} results:')
for i, r in enumerate(results, 1):
    title = r["title"][:50] if r["title"] else "Unknown"
    print(f'  {i}. Title: {title}...')
    print(f'     RRF Score: {r["rrf_score"]:.6f}')
    print(f'     Vector Rank: {r["vector_rank"]} | FTS Rank: {r["fts_rank"]}')

searcher.close()
print('Hybrid search test completed successfully!')
