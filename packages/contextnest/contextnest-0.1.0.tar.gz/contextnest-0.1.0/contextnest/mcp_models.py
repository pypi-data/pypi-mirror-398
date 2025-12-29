"""
Pydantic models for ContextNest MCP tools.
"""
from typing import Optional
from pydantic import BaseModel, Field
from pydantic.config import ConfigDict

class WebScrapeInput(BaseModel):
    """Input for web scraping tool."""
    url: str = Field(..., description="The URL to scrape.", min_length=1)
    save_path: Optional[str] = Field(None, description="Optional path to save the markdown locally. If not provided, saves to default output directory.")

class SearchInput(BaseModel):
    """Input for hybrid search tool."""
    query: str = Field(..., description="The search query.", min_length=1)
    limit: int = Field(5, description="Maximum number of results to return.")
    k: int = Field(60, description="Smoothing constant for RRF.")
    vector_weight: float = Field(1.0, description="Weight for vector search results.")
    fts_weight: float = Field(1.0, description="Weight for full-text search results.")

class InsertKnowledgeInput(BaseModel):
    """Input for inserting knowledge into the database."""
    url: str = Field(..., description="The source URL of the content.", min_length=1)
    title: str = Field("", description="The title of the content. If not provided, it will be extracted from the URL.")
    content: str = Field("", description="The actual text content to insert. If not provided, the URL will be scraped.")

class ReadMetadataInput(BaseModel):
    """Input for reading metadata. Currently empty as no parameters are needed."""
    model_config = ConfigDict(extra='forbid')
