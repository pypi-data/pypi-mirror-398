# ContextNest Documentation

Welcome to the ContextNest documentation. This guide provides comprehensive information about the ContextNest project and its components.

## Table of Contents

1. [Main Project Documentation (README)](../README.md)
2. [Web Scraper Module](web_scraper.md)
3. [Micro Search Module](micro_search.md)
4. [MCP Server Implementation](#mcp-server)
5. [Models and Data Structures](#models)
6. [Logging System](#logging)

## MCP Server

The MCP (Model Context Protocol) server implementation is in `contextnest/mcp_server.py`. It exposes the following tools and resources:

### Tools
- `web_scrape`: Scrapes URLs and converts to Markdown
- `search`: Performs hybrid search (vector + full-text)
- `insert_knowledge`: Inserts documents into the knowledge base
- `read_metadata`: Reads metadata file

### Resources
- `contextnest://output/{filename}`: Reads markdown files from output directory
- `contextnest://metadata`: Reads metadata file

## Models

The Pydantic models in `contextnest/mcp_models.py` define the input schemas for all tools:

- `WebScrapeInput`: Input for web scraping tool
- `SearchInput`: Input for search tool
- `InsertKnowledgeInput`: Input for knowledge insertion tool
- `ReadMetadataInput`: Input for metadata reading tool

## Logging

The logging system in `contextnest/mcp_logger.py` provides structured logging for MCP operations using loguru. It includes convenience functions for logging requests, responses, and errors.