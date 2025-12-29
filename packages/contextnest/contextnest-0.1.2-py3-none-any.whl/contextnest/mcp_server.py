"""
Main MCP server implementation for ContextNest.
Exposes tools and resources using FastMCP.
"""
import sys
from pathlib import Path
from typing import Optional

project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from fastmcp import FastMCP
from contextnest.mcp_models import WebScrapeInput, SearchInput, InsertKnowledgeInput, ReadMetadataInput
from contextnest.server_tools import web_scrape_logic, search_logic, insert_knowledge_logic, read_metadata_logic, get_output_file_logic

# Initialize FastMCP
mcp = FastMCP("ContextNest 🦅")

# --- Resources ---

@mcp.resource("contextnest://output/{filename}")
async def get_output_file(filename: str) -> str:
    """Read a markdown file from the ContextNest output directory."""
    return await get_output_file_logic(filename)

@mcp.resource("contextnest://metadata")
def get_metadata_resource() -> str:
    """Read the ContextNest metadata file."""
    metadata_file = Path.home() / ".contextnest" / "metadata.json"
    if not metadata_file.exists():
         return "{}"
    return metadata_file.read_text(encoding="utf-8")


# --- Tools ---

@mcp.tool()
async def web_scrape(input: WebScrapeInput) -> str:
    """
    Scrape a URL and convert it to markdown.
    Automatically saves the result to the default output directory (~/.contextnest/output).
    """
    return await web_scrape_logic(input)

@mcp.tool()
async def search(input: SearchInput) -> str:
    """
    Perform a hybrid search (Vector + BM25) on the knowledge base.
    """
    return await search_logic(input)

# takes seconds to minutes must be converted into background task.
@mcp.tool(task=True)
async def insert_knowledge(input: InsertKnowledgeInput) -> str:
    """
    Insert a document into the knowledge base.
    This process chunks, embeds, and stores the content in DuckDB.
    """
    return await insert_knowledge_logic(input)

@mcp.tool()
def read_metadata(input: Optional[ReadMetadataInput] = None) -> str:
    """
    Read the application's metadata file to see database logical links and configurations.
    """
    return read_metadata_logic(input)

from fastmcp.prompts.prompt import Message

@mcp.prompt()
def search_guide() -> Message:
    """Returns a system prompt guiding the LLM on how to use ContextNest search tools."""
    prompt_text = (
        "You are an intelligent assistant with access to the ContextNest knowledge base.\n"
        "Use the available tools to answer requests:\n"
        "- Use 'search' for finding relevant documents using hybrid search (Vector + BM25).\n"
        "- Use 'web_scrape' to ingest new content from URLs if the search yields insufficient results.\n"
        "- Use 'insert_knowledge' to explicitly save important information.\n"
        "- Always cite your sources when providing answers from the knowledge base."
    )
    return Message(role="user", content=prompt_text)

if __name__ == "__main__":
    mcp.run()
