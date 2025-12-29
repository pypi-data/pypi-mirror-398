"""
Pydantic models for ContextNest MCP tools.
"""
from pydantic import BaseModel, Field
from pydantic.config import ConfigDict

class WebScrapeInput(BaseModel):
    """Input for web scraping tool."""
    url: str = Field(..., description="The URL to scrape.", min_length=1)

class SearchInput(BaseModel):
    """Input for hybrid search tool."""
    query: str = Field(..., description="The search query.", min_length=1)
    limit: int = Field(5, description="Maximum number of results to return.")

class InsertKnowledgeInput(BaseModel):
    """Input for inserting knowledge into the database."""
    url: str = Field(..., description="The source URL of the content.", min_length=1)

class ReadMetadataInput(BaseModel):
    """Input for reading metadata. Currently empty as no parameters are needed."""
    model_config = ConfigDict(extra='forbid')
