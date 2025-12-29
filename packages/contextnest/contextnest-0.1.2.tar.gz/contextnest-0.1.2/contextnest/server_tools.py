"""
Core logic for ContextNest MCP server tools.
Separated from the MCP server definition for easier testing and reuse.
"""
import json
from pathlib import Path
from contextnest.web_scraper import scrape_url
from contextnest.micro_search import insert_document, hybrid_search, DocumentInserter
from contextnest.mcp_models import WebScrapeInput, SearchInput, InsertKnowledgeInput, ReadMetadataInput


async def web_scrape_logic(input: WebScrapeInput) -> str:
    """Logic for web_scrape tool."""
    try:
        markdown = await scrape_url(
            url=input.url
        )
        # Return the expected format for test compatibility
        return f"Successfully scraped {input.url}. Content length: {len(markdown)}."
    except Exception as e:
        error_msg = f"Error scraping {input.url}: {str(e)}"
        return error_msg

async def search_logic(input: SearchInput) -> str:
    """Logic for search tool."""
    try:
        # We need to generate the query embedding first
        inserter = DocumentInserter()
        query_embedding = inserter.get_embedding(input.query)
        
        results = hybrid_search(
            query=input.query,
            query_embedding=query_embedding,
            limit=input.limit,
            k=60,
        )

        return json.dumps(results, indent=2, default=str)
    except Exception as e:
        error_msg = f"Error searching for '{input.query}': {str(e)}"
        return error_msg

async def insert_knowledge_logic(input: InsertKnowledgeInput) -> str:
    """Logic for insert_knowledge tool."""
    try:
        # Always scrape content
        print(f"Scraping content from {input.url}...")
        content = await scrape_url(input.url)
        
        # Simple heuristic: first line of markdown is often the title (e.g. # Title)
        title = None
        lines = content.splitlines()
        if lines and lines[0].startswith("# "):
            title = lines[0][2:].strip()
        
        # Ensure we have a title
        if not title:
             title = f"Document from {input.url}"

        insert_document(
            url=input.url,
            title=title,
            content=content
        )
        msg = f"Successfully inserted content from {input.url} ('{title}')."
        return msg
    except Exception as e:
        error_msg = f"Error inserting knowledge: {str(e)}"
        return error_msg

def read_metadata_logic(input: ReadMetadataInput = None) -> str:
    """Logic for read_metadata tool."""
    try:
        metadata_file = Path.home() / ".contextnest" / "metadata.json"
        if not metadata_file.exists():
            return "No metadata file found."
        # Use open() to make it more testable with mock_open
        with open(metadata_file, 'r', encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading metadata: {str(e)}"

async def get_output_file_logic(filename: str) -> str:
    """Logic for get_output_file resource."""
    output_dir = Path.home() / ".contextnest" / "output"
    file_path = output_dir / filename
    
    if not file_path.exists():
        # Check if any files are available first to provide appropriate error message
        available_files = list(output_dir.glob("*.md"))
        if not available_files:
            raise FileNotFoundError(f"File not found: {filename} and no other files available.")
        else:
            raise FileNotFoundError(f"File not found: {filename}. Available files: {[f.name for f in available_files]}")

    return file_path.read_text(encoding="utf-8")
