"""
Full Cycle Example: Web Scraping, Statistics, Insertion, and Hybrid Search

This example demonstrates a complete workflow using ContextNest:
1. Use web_scraper to scrape content from a URL
2. Show summary statistics like the number of characters
3. Use micro_search/insertion.py to insert the content into the database
4. Use hybrid search (vector + BM25 with RRF ranking) to search the content

URL used: https://github.com/scikit-learn/scikit-learn
"""

import asyncio
from contextnest.web_scraper import WebScraper
from contextnest.micro_search.insertion import insert_document
from contextnest.micro_search import is_url_in_metadata, hybrid_search
from contextnest.mcp_logger import info_mcp, debug_mcp


async def full_cycle_example():
    """
    Demonstrate the full cycle: scrape -> stats -> insert -> search
    With URL caching: skip scraping if URL already exists in database
    """
    # URL to scrape
    url = "https://github.com/DataTalksClub/ai-dev-tools-zoomcamp/blob/main/cohorts/2025/03-mcp/homework.md"
    
    info_mcp("=" * 70)
    info_mcp("CONTEXTNEST FULL CYCLE EXAMPLE")
    info_mcp("=" * 70)
    
    try:
        # Check if URL already exists in database
        existing_doc = is_url_in_metadata(url)
        
        if existing_doc:
            # URL already exists, use cached content
            info_mcp(f"✓ URL already exists in database, skipping scraping")
        else:
            # URL not found, need to scrape
            info_mcp(f"Step 1: Scraping content from {url}")
            
            async with WebScraper(
                headless=True,  # Set to False if CAPTCHA handling is needed
            ) as scraper:
                markdown_content = await scraper.scrape(url)
                
                info_mcp("✓ Successfully scraped content")
                
                # Step 2: Show summary statistics
                info_mcp("\nStep 2: Content Statistics")
                char_count = len(markdown_content)
                word_count = len(markdown_content.split())
                line_count = len(markdown_content.split('\n'))
                
                info_mcp(f"  • Characters: {char_count:,}")
                info_mcp(f"  • Words: {word_count:,}")
                info_mcp(f"  • Lines: {line_count:,}")
                info_mcp(f"  • Content preview (first 200 chars): {markdown_content[:200]}...")
                
                # Step 3: Insert content using micro_search/insertion.py
                info_mcp("\nStep 3: Inserting content into database")
                
                # Extract title from content or use a default
                title = "Pandas Github Repo"  # Could extract from content if needed
                
                insert_document(
                    url=url,
                    title=title,
                    content=markdown_content
                )
                
                info_mcp("✓ Successfully inserted content into database")
        
        # Step 4: Hybrid Search (Vector + BM25 with RRF ranking)
        info_mcp("\nStep 4: Performing Hybrid Search (Vector + BM25 with RRF)")
        
        # Generate query embedding using Gemini with Ollama fallback
        from google import genai
        from google.genai import types
        import numpy as np
        import ollama
        
        query = "what's the first question"
        query_embedding = None
        
        # Try Gemini first, fallback to Ollama
        try:
            gemini_client = genai.Client()
            response = gemini_client.models.embed_content(
                model="gemini-embedding-exp-03-07",
                contents=query,
                config=types.EmbedContentConfig(
                    output_dimensionality=768,
                    task_type="RETRIEVAL_QUERY"
                )
            )
            embedding = np.array(response.embeddings[0].values)
            normed_embedding = embedding / np.linalg.norm(embedding)
            query_embedding = normed_embedding.tolist()
            info_mcp("✓ Using Gemini for query embedding")
        except Exception as gemini_error:
            info_mcp(f"⚠ Gemini embedding failed: {gemini_error}. Falling back to Ollama.")
            query_embedding_response = ollama.embeddings(
                model="nomic-embed-text:latest",
                prompt=query
            )
            query_embedding = query_embedding_response.get('embedding')
        
        if query_embedding:
            # Perform hybrid search (combines vector similarity + BM25 with RRF scoring)
            search_results = hybrid_search(
                query=query,
                query_embedding=query_embedding,
                limit=3,
                k=60  # RRF smoothing constant
            )
            
            info_mcp(f"✓ Hybrid search found {len(search_results)} documents for query: '{query}'")
            
            for i, result in enumerate(search_results, 1):
                info_mcp(f"\nResult {i}:")
                info_mcp(f"  Title: {result['title']}")
                info_mcp(f"  URL: {result['url']}")
                info_mcp(f"  RRF Score: {result['rrf_score']:.6f}")
                info_mcp(f"  Vector Rank: {result['vector_rank']} | FTS Rank: {result['fts_rank']}")
                if result['vector_distance'] is not None:
                    info_mcp(f"  Cosine Distance: {result['vector_distance']:.4f}")
                if result['bm25_score'] is not None:
                    info_mcp(f"  BM25 Score: {result['bm25_score']:.4f}")
                info_mcp(f"  Content Preview: {result['content']}...")
        else:
            info_mcp("⚠ Could not generate embedding for search query")
            
    except Exception as e:
        debug_mcp(f"Error during full cycle: {str(e)}")
        raise
    
    info_mcp("\n" + "=" * 70)
    info_mcp("FULL CYCLE COMPLETED SUCCESSFULLY")
    info_mcp("=" * 70)


def run_full_cycle_example():
    """
    Synchronous wrapper to run the async example
    """
    asyncio.run(full_cycle_example())


if __name__ == "__main__":
    run_full_cycle_example()