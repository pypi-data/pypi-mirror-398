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
from fastmcp.client.elicitation import ElicitResult
from contextnest.mcp_logger import info_mcp, debug_mcp, warning_mcp


class ContextNestClient:
    """
    Client for interacting with the ContextNest MCP server.
    
    Example usage:
        async with ContextNestClient() as client:
            results = await client.search()
            print(results)
    """
    
    def __init__(self, server_script_path: Optional[str] = None, elicitation_handler = None):
        """
        Initialize the ContextNest MCP client.
        
        Args:
            server_script_path: Path to the MCP server script. 
                              Defaults to contextnest/mcp_server.py
            elicitation_handler: Optional custom elicitation handler function.
                               If None, uses the default handler.
        """
        if server_script_path is None:
            server_script_path = str(Path(__file__).parent / "mcp_server.py")
        
        self.server_script_path = server_script_path
        self.client: Optional[Client] = None
        self.elicitation_handler = elicitation_handler or self._default_elicitation_handler
        
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
        
        # Create and initialize the client with elicitation handler
        self.client = Client(transport, elicitation_handler=self.elicitation_handler)
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
    
    async def _default_elicitation_handler(self, message: str, response_type: type, params, context):
        """
        Default elicitation handler that prompts for user input in the terminal.
        
        Args:
            message: The message displayed to the user
            response_type: The dataclass type for the expected response (converted from JSON schema)
            params: Additional parameters including requestedSchema
            context: Elicitation context information
            
        Returns:
            ElicitResult or response_type instance
        """
        info_mcp(f"\n{message}")
        
        # Check if response_type is a Pydantic model or a simple dataclass
        # FastMCP converts the JSON schema to a dataclass type
        # For Pydantic models, we need to collect field values interactively
        
        try:
            # Get the type hints/fields from the response_type
            if hasattr(response_type, '__annotations__'):
                # This is a structured type (Pydantic model or dataclass)
                fields = response_type.__annotations__
                field_values = {}
                
                info_mcp("Please provide the following information:")
                for field_name, field_type in fields.items():
                    # Get field description if available
                    field_info = ""
                    if hasattr(response_type, '__fields__'):
                        # Pydantic model
                        field_obj = response_type.__fields__.get(field_name)
                        if field_obj and field_obj.field_info.description:
                            field_info = f" ({field_obj.field_info.description})"
                    
                    # Prompt for the field value
                    prompt = f"  {field_name}{field_info}: "
                    user_input = input(prompt)
                    
                    # Handle empty input for optional fields
                    if not user_input and hasattr(field_type, '__origin__'):
                        # Check if it's Optional
                        import typing
                        if typing.get_origin(field_type) is typing.Union:
                            field_values[field_name] = None
                            continue
                    
                    # Basic type conversion
                    if user_input:
                        if field_type is int or (hasattr(field_type, '__origin__') and 'int' in str(field_type)):
                            field_values[field_name] = int(user_input)
                        elif field_type is float or (hasattr(field_type, '__origin__') and 'float' in str(field_type)):
                            field_values[field_name] = float(user_input)
                        elif field_type is bool or (hasattr(field_type, '__origin__') and 'bool' in str(field_type)):
                            field_values[field_name] = user_input.lower() in ('true', 'yes', '1', 't', 'y')
                        else:
                            field_values[field_name] = user_input
                    else:
                        field_values[field_name] = user_input if user_input else None
                
                # Create the response using the collected field values
                response_data = response_type(**field_values)
                return response_data
            else:
                # Simple type (str, int, etc.) - wrapped in a dataclass by FastMCP
                user_input = input("Your response: ")
                if not user_input:
                    return ElicitResult(action="decline")
                
                # FastMCP wraps simple types in dataclasses with a 'value' field
                return response_type(value=user_input)
                
        except KeyboardInterrupt:
            info_mcp("\nOperation cancelled by user.")
            return ElicitResult(action="cancel")
        except Exception as e:
            warning_mcp(f"Error in elicitation handler: {e}")
            return ElicitResult(action="decline")
    
    # --- Tool Methods ---
    
    async def web_scrape(self) -> str:
        """
        Scrape a URL and convert it to markdown.
        
        This tool will interactively prompt for:
        - URL to scrape
        - Output directory (optional)
        
        Returns:
            str: Result message from the server
        """
        self._ensure_connected()
        info_mcp("Calling web_scrape tool...")
        
        result = await self.client.call_tool("web_scrape", arguments={})
        return result.content[0].text if result.content else "No response"
    
    async def search(self) -> str:
        """
        Perform a hybrid search (Vector + BM25) on the knowledge base.
        
        This tool will interactively prompt for:
        - Search query
        - Number of results (limit)
        
        Returns:
            str: Search results formatted as text
        """
        self._ensure_connected()
        info_mcp("Calling search tool...")
        
        result = await self.client.call_tool("search", arguments={})
        return result.content[0].text if result.content else "No response"
    
    async def insert_knowledge(self) -> str:
        """
        Insert a document into the knowledge base.
        
        This tool will interactively prompt for:
        - Document path or URL
        - Title
        - Content (if applicable)
        
        Note: This is a background task and may take time to complete.
        
        Returns:
            str: Result message from the server
        """
        self._ensure_connected()
        info_mcp("Calling insert_knowledge tool (background task)...")
        
        result = await self.client.call_tool("insert_knowledge", arguments={})
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
