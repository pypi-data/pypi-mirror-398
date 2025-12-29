"""
Main MCP server implementation for ContextNest.
Exposes tools and resources using FastMCP.
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from fastmcp import FastMCP
from fastmcp.server.context import Context
from fastmcp.dependencies import CurrentContext
from contextnest.mcp_models import WebScrapeInput, SearchInput, InsertKnowledgeInput, ReadMetadataInput
from contextnest.server_tools import web_scrape_logic, search_logic, insert_knowledge_logic, read_metadata_logic, get_output_file_logic

# Initialize FastMCP
mcp = FastMCP("ContextNest 🦅")

# --- Resources ---

@mcp.resource("contextnest://output/{filename}")
async def get_output_file(filename: str, ctx: Context = CurrentContext()) -> str:
    """Read a markdown file from the ContextNest output directory."""
    return await get_output_file_logic(filename, ctx)

@mcp.resource("contextnest://metadata")
def get_metadata_resource() -> str:
    """Read the ContextNest metadata file."""
    metadata_file = Path.home() / ".contextnest" / "metadata.json"
    if not metadata_file.exists():
         return "{}"
    return metadata_file.read_text(encoding="utf-8")


# --- Tools ---

@mcp.tool()
async def web_scrape(ctx: Context) -> str:
    """
    Scrape a URL and convert it to markdown.
    Automatically saves the result to the default output directory (~/.contextnest/output).
    """
    await ctx.info("Requesting Web Scrape Input from user")
    result = await ctx.elicit(
        message="Please provide Web Scrape parameters:",
        response_type=WebScrapeInput
    )
    
    if result.action == "accept":
        return await web_scrape_logic(result.data, ctx)
    else:
        return "Operation cancelled or declined."

@mcp.tool()
async def search(ctx: Context) -> str:
    """
    Perform a hybrid search (Vector + BM25) on the knowledge base.
    """
    await ctx.info("Requesting Search Input from user")
    result = await ctx.elicit(
        message="Please provide Search parameters:",
        response_type=SearchInput
    )
    
    if result.action == "accept":
        return await search_logic(result.data, ctx)
    else:
        return "Operation cancelled or declined."

# takes seconds to minutes must be converted into background task.
@mcp.tool(task=True)
async def insert_knowledge(ctx: Context) -> str:
    """
    Insert a document into the knowledge base.
    This process chunks, embeds, and stores the content in DuckDB.
    """
    await ctx.info("Requesting Insert Knowledge Input from user")
    result = await ctx.elicit(
        message="Please provide Knowledge Insertion parameters:",
        response_type=InsertKnowledgeInput
    )
    
    if result.action == "accept":
        return await insert_knowledge_logic(result.data, ctx)
    else:
        return "Operation cancelled or declined."

@mcp.tool()
def read_metadata(input: ReadMetadataInput = None) -> str:
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
