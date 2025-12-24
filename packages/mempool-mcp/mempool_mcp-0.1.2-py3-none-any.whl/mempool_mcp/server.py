"""MCP server for Mempool.space Bitcoin explorer API."""

import asyncio
import logging
import os
import sys

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .client import MempoolClient
from .tools.general import get_general_tools, handle_general_tool
from .tools.mempool import get_mempool_tools, handle_mempool_tool
from .tools.transactions import get_transaction_tools, handle_transaction_tool
from .tools.blocks import get_block_tools, handle_block_tool
from .tools.addresses import get_address_tools, handle_address_tool
from .tools.mining import get_mining_tools, handle_mining_tool
from .tools.lightning import get_lightning_tools, handle_lightning_tool

# Disable logging to avoid interfering with MCP stdio communication
logging.basicConfig(level=logging.CRITICAL)


def get_all_tools() -> list[Tool]:
    """Get all tool definitions from all modules."""
    tools = []
    tools.extend(get_general_tools())
    tools.extend(get_mempool_tools())
    tools.extend(get_transaction_tools())
    tools.extend(get_block_tools())
    tools.extend(get_address_tools())
    tools.extend(get_mining_tools())
    tools.extend(get_lightning_tools())
    return tools


async def handle_tool(name: str, arguments: dict, client: MempoolClient) -> list[TextContent]:
    """Route tool calls to the appropriate handler."""
    # Try each handler in order until one handles the tool
    handlers = [
        handle_general_tool,
        handle_mempool_tool,
        handle_transaction_tool,
        handle_block_tool,
        handle_address_tool,
        handle_mining_tool,
        handle_lightning_tool,
    ]

    for handler in handlers:
        result = await handler(name, arguments, client)
        if result is not None:
            return result

    return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def run_server() -> None:
    """Run the MCP server."""
    # Get base URL from environment (required)
    base_url = os.getenv("MEMPOOL_API_URL")

    if not base_url:
        print("ERROR: MEMPOOL_API_URL not set!", file=sys.stderr)
        sys.exit(1)

    # Initialize the API client
    client = MempoolClient(base_url)

    # Create the MCP server
    server = Server("mempool")

    # Register single consolidated list_tools handler
    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return get_all_tools()

    # Register single consolidated call_tool handler
    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        return await handle_tool(name, arguments, client)

    # Run the server over stdio
    try:
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options(),
            )
    finally:
        await client.close()


def main() -> None:
    """Entry point for the MCP server."""
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
