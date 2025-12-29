"""
Example script demonstrating the ContextNest MCP Client.

This script shows how to:
1. Connect to the MCP server
2. List available capabilities
3. Call tools interactively
4. Access resources
5. Retrieve prompts
"""
import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from contextnest.mcp_client import ContextNestClient
from contextnest.mcp_logger import info_mcp, warning_mcp


async def main():
    """
    Main example demonstrating ContextNest MCP Client usage.
    """
    info_mcp("=" * 70)
    info_mcp("CONTEXTNEST MCP CLIENT EXAMPLE")
    info_mcp("=" * 70)
    
    try:
        # Connect to the MCP server using async context manager
        async with ContextNestClient() as client:
            info_mcp("\n📋 Listing Server Capabilities...")
            
            # List available tools
            tools = await client.list_tools()
            info_mcp(f"\n✓ Available Tools ({len(tools)}):")
            for tool in tools:
                info_mcp(f"  • {tool}")
            
            # List available resources
            resources = await client.list_resources()
            info_mcp(f"\n✓ Available Resources ({len(resources)}):")
            for resource in resources:
                info_mcp(f"  • {resource}")
            
            # List available prompts
            prompts = await client.list_prompts()
            info_mcp(f"\n✓ Available Prompts ({len(prompts)}):")
            for prompt in prompts:
                info_mcp(f"  • {prompt}")
            
            # --- Example 1: Get Search Guide Prompt ---
            info_mcp("\n" + "=" * 70)
            info_mcp("EXAMPLE 1: Retrieving Search Guide Prompt")
            info_mcp("=" * 70)
            
            search_guide = await client.get_search_guide()
            info_mcp(f"\n✓ Search Guide:")
            info_mcp(f"  Description: {search_guide.get('description', 'No description')}")
            info_mcp(f"\n  Messages:")
            for msg in search_guide.get('messages', []):
                info_mcp(f"    Role: {msg['role']}")
                info_mcp(f"    Content preview: {msg['content'][:200]}...")
            
            # --- Example 2: Access Metadata Resource ---
            info_mcp("\n" + "=" * 70)
            info_mcp("EXAMPLE 2: Accessing Metadata Resource")
            info_mcp("=" * 70)
            
            try:
                metadata = await client.get_metadata()
                info_mcp(f"\n✓ Metadata Resource:")
                info_mcp(f"  {metadata[:500]}...")  # Show first 500 chars
            except Exception as e:
                warning_mcp(f"Could not access metadata: {e}")
            
            # --- Example 3: Interactive Tool Calling ---
            info_mcp("\n" + "=" * 70)
            info_mcp("EXAMPLE 3: Interactive Tool Calling")
            info_mcp("=" * 70)
            info_mcp("\nYou can now choose to test one of the interactive tools:")
            info_mcp("  1. web_scrape - Scrape a URL and save as markdown")
            info_mcp("  2. search - Search the knowledge base")
            info_mcp("  3. insert_knowledge - Insert a document")
            info_mcp("  4. read_metadata - Read metadata with optional filter")
            info_mcp("  5. Skip interactive testing")
            
            choice = input("\nEnter your choice (1-5): ").strip()
            
            try:
                if choice == "1":
                    info_mcp("\n📝 Calling web_scrape tool...")
                    info_mcp("  This will prompt you for URL and other parameters...")
                    result = await client.web_scrape()
                    info_mcp(f"\n✓ Result:\n{result}")
                    
                elif choice == "2":
                    info_mcp("\n🔍 Calling search tool...")
                    info_mcp("  This will prompt you for search query and limit...")
                    result = await client.search()
                    info_mcp(f"\n✓ Result:\n{result}")
                    
                elif choice == "3":
                    info_mcp("\n📥 Calling insert_knowledge tool...")
                    info_mcp("  This is a background task and may take time...")
                    result = await client.insert_knowledge()
                    info_mcp(f"\n✓ Result:\n{result}")
                    
                elif choice == "4":
                    info_mcp("\n📊 Calling read_metadata tool...")
                    result = await client.read_metadata()
                    info_mcp(f"\n✓ Result:\n{result[:1000]}...")  # Truncate for display
                    
                elif choice == "5":
                    info_mcp("\n⏭️  Skipping interactive tool testing...")
                    
                else:
                    info_mcp("\n❌ Invalid choice. Skipping.")
                    
            except Exception as e:
                warning_mcp(f"Error calling tool: {e}")
            
            # --- Example 4: List Output Files (if any) ---
            info_mcp("\n" + "=" * 70)
            info_mcp("EXAMPLE 4: Checking Output Directory")
            info_mcp("=" * 70)
            
            # Try to access a common output file
            output_dir = Path.home() / ".contextnest" / "output"
            if output_dir.exists():
                files = list(output_dir.glob("*.md"))
                if files:
                    info_mcp(f"\n✓ Found {len(files)} markdown file(s) in output directory:")
                    for file in files[:3]:  # Show first 3
                        info_mcp(f"  • {file.name}")
                    
                    # Try to read the first one
                    if files:
                        try:
                            first_file = files[0].name
                            content = await client.get_output_file(first_file)
                            info_mcp(f"\n✓ Content of {first_file} (first 300 chars):")
                            info_mcp(f"  {content[:300]}...")
                        except Exception as e:
                            warning_mcp(f"Could not read output file: {e}")
                else:
                    info_mcp("\n  No markdown files found in output directory.")
            else:
                info_mcp("\n  Output directory does not exist yet.")
                info_mcp("  Run web_scrape to create it.")
            
    except Exception as e:
        warning_mcp(f"Error in example: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    info_mcp("\n" + "=" * 70)
    info_mcp("EXAMPLE COMPLETED SUCCESSFULLY")
    info_mcp("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
