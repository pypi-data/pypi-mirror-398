#!/usr/bin/env python3
"""Basic usage example for GuruFocus MCP server.

This example shows how to use the MCP server programmatically
with the FastMCP client library.
"""

import asyncio
import os

from fastmcp.client import Client

from gurufocus_mcp import create_server
from gurufocus_mcp.config import MCPServerSettings


async def main():
    """Demonstrate basic MCP server usage."""
    # Ensure API token is set
    api_token = os.getenv("GURUFOCUS_API_TOKEN")
    if not api_token:
        print("Please set GURUFOCUS_API_TOKEN environment variable")
        return

    # Create server with settings
    settings = MCPServerSettings(api_token=api_token)
    server = create_server(settings)

    # Connect client to server
    async with Client(server) as client:
        print("Connected to GuruFocus MCP server\n")

        # List available tools
        print("=== Available Tools ===")
        tools = await client.list_tools()
        for tool in tools:
            print(f"  - {tool.name}: {tool.description[:60]}...")

        print(f"\nTotal tools: {len(tools)}\n")

        # List available prompts
        print("=== Available Prompts ===")
        prompts = await client.list_prompts()
        for prompt in prompts:
            print(f"  - {prompt.name}: {prompt.description[:60]}...")

        print(f"\nTotal prompts: {len(prompts)}\n")

        # List available resources
        print("=== Available Resource Templates ===")
        templates = await client.list_resource_templates()
        for template in templates:
            print(f"  - {template.uriTemplate}")

        print(f"\nTotal templates: {len(templates)}\n")

        # Example: Get a prompt
        print("=== Example: Investment Thesis Prompt for AAPL ===")
        result = await client.get_prompt("investment_thesis", arguments={"symbol": "AAPL"})
        if result.messages:
            content = result.messages[0].content
            if hasattr(content, "text"):
                # Print first 500 chars of the prompt
                print(content.text[:500] + "...")

        print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
