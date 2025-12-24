"""Mempool-related tools."""

import json
from mcp.types import Tool, TextContent

from ..client import MempoolClient


def get_mempool_tools() -> list[Tool]:
    """Return mempool tool definitions."""
    return [
        Tool(
            name="get_mempool",
            description="Get mempool statistics including transaction count, total vsize, and fee histogram.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="get_mempool_txids",
            description="Get all transaction IDs currently in the mempool. Warning: returns a large list.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="get_mempool_recent",
            description="Get the 10 most recent transactions in the mempool.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="get_rbf_replacements",
            description="Get recent RBF (Replace-By-Fee) transaction replacements.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="get_fullrbf_replacements",
            description="Get recent full-RBF transaction replacements (transactions replaced without signaling RBF).",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
    ]


async def handle_mempool_tool(name: str, arguments: dict, client: MempoolClient) -> list[TextContent] | None:
    """Handle mempool tool calls. Returns None if tool not handled."""
    try:
        if name == "get_mempool":
            result = await client.get_mempool()
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_mempool_txids":
            result = await client.get_mempool_txids()
            summary = f"Total transactions in mempool: {len(result)}\n\nFirst 20 txids:\n"
            summary += "\n".join(result[:20])
            if len(result) > 20:
                summary += f"\n... and {len(result) - 20} more"
            return [TextContent(type="text", text=summary)]

        elif name == "get_mempool_recent":
            result = await client.get_mempool_recent()
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_rbf_replacements":
            result = await client.get_rbf_replacements()
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_fullrbf_replacements":
            result = await client.get_fullrbf_replacements()
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]

    return None
