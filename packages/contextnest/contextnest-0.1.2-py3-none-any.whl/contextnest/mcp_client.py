"""
MCP Client for ContextNest.
Provides programmatic access to the ContextNest MCP server.
"""
import sys
from pathlib import Path
from typing import Optional, Any, Dict, List

project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from fastmcp.client import Client
from contextnest.mcp_logger import info_mcp, debug_mcp


class ContextNestClient:
    """
    Client for interacting with the ContextNest MCP server.
    
    Example usage:
        async with ContextNestClient() as client:
            results = await client.search()
            print(results)
    """
    
    def __init__(self, server_script_path: Optional[str] = None):
        """
        Initialize the ContextNest MCP client.
        
        Args:
            server_script_path: Path to the MCP server script. 
                              Defaults to contextnest/mcp_server.py
        """
        if server_script_path is None:
            server_script_path = str(Path(__file__).parent / "mcp_server.py")
        
        self.server_script_path = server_script_path
        self.client: Optional[Client] = None
        
    async def __aenter__(self):
        """Async context manager entry - connect to the server."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - disconnect from the server."""
        await self.disconnect()
        
    async def connect(self):
        """Establish connection to the MCP server."""
        info_mcp("Connecting to ContextNest MCP Server...")
        
        # Import StdioTransport
        import os
        from fastmcp.client.transports import StdioTransport
        
        # Create stdio transport to launch the server as a subprocess
        # Pass environment variables so the server can access GOOGLE_API_KEY and other env vars
        transport = StdioTransport(
            command="uv",
            args=["run", "python", self.server_script_path],
            env=os.environ.copy()  # Pass environment variables to subprocess
        )
        
        # Create and initialize the client
        self.client = Client(transport)
        await self.client.__aenter__()
        
        info_mcp("✓ Connected to ContextNest MCP Server")
        
        # Log available capabilities
        try:
            tools = await self.client.list_tools()
            resources = await self.client.list_resources()
            prompts = await self.client.list_prompts()
            
            debug_mcp(f"Available tools: {[t.name for t in tools]}")
            debug_mcp(f"Available resources: {[r.name for r in resources]}")
            debug_mcp(f"Available prompts: {[p.name for p in prompts]}")
        except Exception as e:
            debug_mcp(f"Could not list server capabilities: {e}")
        
        return self
    
    async def disconnect(self):
        """Close connection to the MCP server."""
        if self.client:
            await self.client.__aexit__(None, None, None)
            info_mcp("✓ Disconnected from ContextNest MCP Server")
            self.client = None
    
    def _ensure_connected(self):
        """Ensure the client is connected to the server."""
        if not self.client:
            raise RuntimeError("Client is not connected. Use 'async with ContextNestClient()' or call connect() first.")
    
    
    # --- Tool Methods ---
    
    async def web_scrape(self, url: str) -> str:
        """
        Scrape a URL and convert it to markdown.
        
        Args:
            url: The URL to scrape.
        
        Returns:
            str: Result message from the server
        """
        self._ensure_connected()
        info_mcp(f"Calling web_scrape tool for URL: {url}")
        
        arguments = {"url": url}
        
        result = await self.client.call_tool("web_scrape", arguments=arguments)
        return result.content[0].text if result.content else "No response"
    
    async def search(self, query: str, limit: int = 5) -> str:
        """
        Perform a hybrid search (Vector + BM25) on the knowledge base.
        
        Args:
            query: The search query.
            limit: Maximum number of results to return (default: 5).
        
        Returns:
            str: Search results formatted as text
        """
        self._ensure_connected()
        info_mcp(f"Calling search tool with query: '{query}'")
        
        arguments = {
            "query": query,
            "limit": limit,
        }
        
        result = await self.client.call_tool("search", arguments=arguments)
        return result.content[0].text if result.content else "No response"
    
    async def insert_knowledge(self, url: str) -> str:
        """
        Insert a document into the knowledge base.
        
        Args:
            url: The source URL of the content.
        
        Note: This is a background task and may take time to complete.
        
        Returns:
            str: Result message from the server
        """
        self._ensure_connected()
        info_mcp(f"Calling insert_knowledge tool for URL: {url}")
        
        arguments = {"url": url}
        
        result = await self.client.call_tool("insert_knowledge", arguments=arguments)
        return result.content[0].text if result.content else "No response"
    
    async def read_metadata(self, filter_by: Optional[str] = None) -> str:
        """
        Read the application's metadata file.
        
        Args:
            filter_by: Optional filter string for metadata
            
        Returns:
            str: Metadata content as JSON string
        """
        self._ensure_connected()
        info_mcp("Calling read_metadata tool...")
        
        arguments = {}
        if filter_by:
            arguments["filter_by"] = filter_by
        
        result = await self.client.call_tool("read_metadata", arguments=arguments)
        return result.content[0].text if result.content else "No response"
    
    # --- Resource Methods ---
    
    async def get_output_file(self, filename: str) -> str:
        """
        Read a markdown file from the ContextNest output directory.
        
        Args:
            filename: Name of the file in ~/.contextnest/output/
            
        Returns:
            str: File contents
        """
        self._ensure_connected()
        info_mcp(f"Reading resource: contextnest://output/{filename}")
        
        uri = f"contextnest://output/{filename}"
        resource = await self.client.read_resource(uri)
        
        return resource.contents[0].text if resource.contents else ""
    
    async def get_metadata(self) -> str:
        """
        Read the ContextNest metadata resource.
        
        Returns:
            str: Metadata JSON content
        """
        self._ensure_connected()
        info_mcp("Reading resource: contextnest://metadata")
        
        resource = await self.client.read_resource("contextnest://metadata")
        return resource.contents[0].text if resource.contents else "{}"
    
    async def list_resources(self) -> List[str]:
        """
        List all available resources.
        
        Returns:
            List[str]: List of resource URIs
        """
        self._ensure_connected()
        resources = await self.client.list_resources()
        return [r.uri for r in resources]
    
    # --- Prompt Methods ---
    
    async def get_search_guide(self) -> Dict[str, Any]:
        """
        Get the search guide prompt.
        
        Returns:
            Dict: Prompt information including messages
        """
        self._ensure_connected()
        info_mcp("Getting search_guide prompt...")
        
        prompt = await self.client.get_prompt("search_guide")
        return {
            "description": prompt.description,
            "messages": [{"role": msg.role, "content": msg.content.text if hasattr(msg.content, 'text') else str(msg.content)} 
                        for msg in prompt.messages]
        }
    
    async def list_prompts(self) -> List[str]:
        """
        List all available prompts.
        
        Returns:
            List[str]: List of prompt names
        """
        self._ensure_connected()
        prompts = await self.client.list_prompts()
        return [p.name for p in prompts]
    
    # --- Tool Methods ---
    
    async def list_tools(self) -> List[str]:
        """
        List all available tools.
        
        Returns:
            List[str]: List of tool names
        """
        self._ensure_connected()
        tools = await self.client.list_tools()
        return [t.name for t in tools]
