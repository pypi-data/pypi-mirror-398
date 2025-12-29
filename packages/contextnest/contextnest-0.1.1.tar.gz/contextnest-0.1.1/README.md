# ContextNest 🦅

A cozy `nest` where all needed context is pre-assembled for the LLM. ContextNest provides a Model Context Protocol (MCP) server that enables AI assistants to access web scraping, knowledge base search, and document management capabilities.

## Table of Contents

- [Project Overview](#project-overview)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Examples](#examples)
- [Detailed Module Documentation](#detailed-module-documentation)
- [Contributing](#contributing)
- [License](#license)

## Project Overview

ContextNest is a Python-based MCP (Model Context Protocol) server that provides AI assistants with powerful context management capabilities. The system combines:

- **Web Scraping**: Automated content extraction from URLs using Playwright and BeautifulSoup
- **Knowledge Base**: Vector and full-text search capabilities with hybrid ranking
- **Document Management**: Storage and retrieval of documents in a DuckDB database
- **MCP Integration**: Seamless integration with AI assistants through the Model Context Protocol

### Key Features

- **Web Scraping**: Extract content from web pages and convert to Markdown format
- **Hybrid Search**: Combine vector similarity search with full-text search (BM25) using Reciprocal Rank Fusion (RRF)
- **CAPTCHA Handling**: Automatic detection and handling of common CAPTCHA challenges
- **Stealth Browsing**: Anti-bot detection evasion techniques
- **Resource Management**: MCP resources for accessing stored files and metadata
- **Logging**: Comprehensive logging with structured messages using loguru

## Architecture

The ContextNest architecture is modular and consists of several key components:

```
contextnest/
├── mcp_server.py     # Main MCP server implementation
├── mcp_models.py     # Pydantic models for tool inputs
├── mcp_logger.py     # Structured logging implementation
├── server_tools.py   # Core tool logic implementations
├── web_scraper/      # Web scraping functionality
│   ├── scraper.py    # Main scraper class
│   ├── captcha_handler.py  # CAPTCHA detection and handling
│   └── markdown_converter.py  # HTML to Markdown conversion
└── micro_search/     # Search functionality
    ├── database.py   # DuckDB database management
    ├── insertion.py  # Document insertion logic
    ├── hybrid_search.py  # Vector + BM25 search with RRF
    └── db_preparation.py  # Database setup and preparation
```

### Core Components

#### MCP Server (`mcp_server.py`)
The main server implementation using FastMCP that exposes tools and resources to AI assistants. It defines the MCP endpoints and handles the communication protocol.

#### Web Scraper (`web_scraper/`)
A comprehensive web scraping module that includes:
- Playwright-based browser automation
- CAPTCHA detection and handling
- Stealth techniques to avoid bot detection
- HTML to Markdown conversion
- Human-like behavior simulation

#### Micro Search (`micro_search/`)
A powerful search module that provides:
- Vector similarity search using embeddings
- Full-text search with BM25 ranking
- Hybrid search combining both approaches with Reciprocal Rank Fusion
- DuckDB-based storage for documents and embeddings

#### MCP Logger (`mcp_logger.py`)
Specialized logging for MCP operations with structured, configurable output using loguru.

## Installation

### Prerequisites

- Python 3.13 or higher
- Node.js (for Playwright dependencies)
- System dependencies for Playwright (Chromium browser)

### Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd contextnest
   ```

2. Install dependencies using uv (recommended):
   ```bash
   uv sync
   ```

   Or using pip:
   ```bash
   pip install -r requirements.txt
   ```

3. Install Playwright browser dependencies:
   ```bash
   playwright install chromium
   ```

4. Set up the database:
   ```bash
   python -m contextnest.micro_search.db_preparation
   ```

### Install from PyPI

You can also install ContextNest directly from PyPI:

```bash
pip install contextnest
```

Or use `uvx` to run the MCP server directly:

```bash
uvx contextnest
```

### MCP Client Configuration

To use ContextNest with MCP-compatible clients (Claude Desktop, Cursor, etc.), add this to your MCP configuration:

```json
{
  "mcpServers": {
    "ContextNest": {
      "command": "uvx",
      "args": ["contextnest"]
    }
  }
}
```

### Dependencies

ContextNest requires the following key dependencies:

- `fastmcp`: Model Context Protocol implementation
- `playwright`: Browser automation for web scraping
- `duckdb`: Database for document storage and search
- `beautifulsoup4`: HTML parsing
- `loguru`: Structured logging
- `ollama`: Optional LLM integration for embeddings
- `google-genai`: Google AI client for embeddings

## Configuration

ContextNest uses default configurations that work out of the box, but can be customized:

### Configuration Files

Configuration is handled through the MCP protocol, with default settings in the code. The database schema and search parameters are configured in the `micro_search` module.

## Usage

### Running the MCP Server

To start the ContextNest MCP server:

```bash
python -m contextnest.mcp_server
```

The server will start and wait for MCP client connections. It provides the following tools and resources:

### Available Tools

#### 1. Web Scraping (`web_scrape`)

Scrapes a URL and converts it to Markdown format, automatically saving the result to the default output directory.

**Input Parameters:**
- `url` (required): The URL to scrape
- `save_path` (optional): Custom path to save the markdown locally

**Example Usage:**
```python
# When prompted by the MCP client
{
  "url": "https://example.com/article",
  "save_path": "/custom/path/article.md"
}
```

#### 2. Search (`search`)

Performs a hybrid search (Vector + BM25) on the knowledge base.

**Input Parameters:**
- `query` (required): The search query
- `limit` (optional): Maximum number of results to return (default: 5)
- `k` (optional): Smoothing constant for RRF (default: 60)
- `vector_weight` (optional): Weight for vector search results (default: 1.0)
- `fts_weight` (optional): Weight for full-text search results (default: 1.0)

**Example Usage:**
```python
# When prompted by the MCP client
{
  "query": "machine learning algorithms",
  "limit": 10,
  "k": 60,
  "vector_weight": 1.0,
  "fts_weight": 1.0
}
```

#### 3. Insert Knowledge (`insert_knowledge`)

Inserts a document into the knowledge base. This process chunks, embeds, and stores the content in DuckDB.
This tool runs as a background task since it can take seconds to minutes to complete.

**Input Parameters:**
- `url` (required): The source URL of the content
- `title` (optional): The title of the content (extracted from content if not provided)
- `content` (optional): The actual text content (scraped from URL if not provided)

**Example Usage:**
```python
# When prompted by the MCP client
{
  "url": "https://example.com/important-document",
  "title": "Important Document Title",
  "content": "Full text content here..."
}
```

#### 4. Read Metadata (`read_metadata`)

Reads the application's metadata file to see database logical links and configurations.

**Input Parameters:** None

### Available Resources

#### 1. Output File Resource (`contextnest://output/{filename}`)

Reads a markdown file from the ContextNest output directory.

**Usage:**
```
contextnest://output/filename.md
```

#### 2. Metadata Resource (`contextnest://metadata`)

Reads the ContextNest metadata file.

**Usage:**
```
contextnest://metadata
```

### MCP Prompt

ContextNest also provides a system prompt to guide LLMs on how to use the available tools:

> You are an intelligent assistant with access to the ContextNest knowledge base.
> Use the available tools to answer requests:
> - Use 'search' for finding relevant documents using hybrid search (Vector + BM25).
> - Use 'web_scrape' to ingest new content from URLs if the search yields insufficient results.
> - Use 'insert_knowledge' to explicitly save important information.
> - Always cite your sources when providing answers from the knowledge base.

## API Documentation

### MCPLogger

Specialized logger for MCP operations with structured, configurable logging.

```python
from contextnest.mcp_logger import MCPLogger, log_request, log_response, log_error

# Create a logger instance
logger = MCPLogger(level="INFO")

# Log MCP operations
logger.log_request("web_scrape", {"url": "https://example.com"})
logger.log_response("search", {"results": 5})
logger.log_error("insert_knowledge", Exception("Database error"))

# Use convenience functions that use the global logger
from contextnest.mcp_logger import info_mcp, debug_mcp, warning_mcp

info_mcp("Processing search query")
debug_mcp("Detailed debug information", query_time=0.123)
warning_mcp("Potential issue detected")
```

### Web Scraper API

The web scraper provides both class-based and function-based interfaces:

```python
from contextnest.web_scraper import WebScraper, scrape_url

# Class-based approach with full control
async with WebScraper(headless=True) as scraper:
    markdown = await scraper.scrape("https://example.com")

# Function-based approach for simple scraping
markdown = await scrape_url("https://example.com", headless=True)
```

### Micro Search API

The search functionality includes vector search, full-text search, and hybrid search:

```python
from contextnest.micro_search import HybridSearch, hybrid_search, insert_document

# Insert a document
insert_document(
    url="https://example.com/doc",
    title="Document Title",
    content="Document content..."
)

# Perform hybrid search using convenience function
query_embedding = [0.1, 0.2, 0.3, ...]  # 768-dimensional vector
results = hybrid_search(
    query="search query",
    query_embedding=query_embedding,
    limit=5
)

# Or use the class directly for more control
searcher = HybridSearch()
results = searcher.search(
    query="search query",
    query_embedding=query_embedding,
    limit=5,
    k=60,
    vector_weight=1.0,
    fts_weight=1.0
)
```

### Server Tools API

The server tools module contains the core logic for all MCP operations:

```python
from contextnest.server_tools import (
    web_scrape_logic,
    search_logic,
    insert_knowledge_logic,
    read_metadata_logic
)

# Each logic function can be called independently
result = await web_scrape_logic(input_data, ctx)
result = await search_logic(input_data, ctx)
result = await insert_knowledge_logic(input_data, ctx)
result = read_metadata_logic(input_data)
```

## Examples

### Full Cycle Example

The repository includes a full cycle example that demonstrates:

1. Web scraping from a URL
2. Content statistics analysis
3. Document insertion into the database
4. Hybrid search with vector + BM25 ranking

```python
from examples.full_cycle_example import run_full_cycle_example

run_full_cycle_example()
```

The example uses the GitHub repository page for the AI Dev Tools Zoomcamp as a source, and performs a search for "what's the first question" to demonstrate the complete workflow. The example includes URL caching to skip scraping if the URL already exists in the database.

### Custom Usage

```python
import asyncio
from contextnest.web_scraper import WebScraper
from contextnest.micro_search import insert_document, hybrid_search
from contextnest.mcp_logger import info_mcp

async def custom_workflow():
    # Scrape content from a URL
    content = await scrape_url("https://example.com/article")

    # Insert into knowledge base
    insert_document(
        url="https://example.com/article",
        title="Example Article",
        content=content
    )

    # Search for relevant content
    query_embedding = [0.1, 0.2, 0.3]  # Generated embedding
    results = hybrid_search(
        query="relevant topic",
        query_embedding=query_embedding,
        limit=3
    )

    info_mcp(f"Found {len(results)} results")

# Run the workflow
asyncio.run(custom_workflow())
```

## Detailed Module Documentation

For more detailed information about specific modules, see the documentation in the `docs/` directory:

- [Web Scraper Module](docs/web_scraper.md): Documentation for the web scraping functionality
- [Micro Search Module](docs/micro_search.md): Documentation for the hybrid search system
- [Main Documentation Index](docs/index.md): Complete documentation index

## Contributing

We welcome contributions to ContextNest! Here's how you can help:

### Development Setup

1. Fork the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -e .
   ```
4. Install Playwright dependencies:
   ```bash
   playwright install
   ```

### Code Standards

- Follow PEP 8 style guidelines
- Write type hints for all public functions
- Include docstrings for all classes and functions
- Add tests for new functionality
- Keep dependencies minimal and well-justified

### Pull Request Process

1. Create a feature branch from the main branch
2. Make your changes with clear, descriptive commit messages
3. Add tests if applicable
4. Update documentation as needed
5. Submit a pull request with a clear description of your changes

### Reporting Issues

When reporting issues, please include:

- Python version
- Operating system
- Steps to reproduce the issue
- Expected vs. actual behavior
- Any relevant error messages

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support, please open an issue in the GitHub repository. For questions about the Model Context Protocol, refer to the official MCP documentation.

---

Made with ❤️ for the AI development community.