"""Block-related tools."""

import json
from mcp.types import Tool, TextContent

from ..client import MempoolClient


def get_block_tools() -> list[Tool]:
    """Return block tool definitions."""
    return [
        Tool(
            name="get_block",
            description="Get block details by block hash including header info, transaction count, size, and weight.",
            inputSchema={
                "type": "object",
                "properties": {
                    "hash": {
                        "type": "string",
                        "description": "Block hash (64 hex characters)",
                    },
                },
                "required": ["hash"],
            },
        ),
        Tool(
            name="get_block_by_height",
            description="Get block hash by block height.",
            inputSchema={
                "type": "object",
                "properties": {
                    "height": {
                        "type": "integer",
                        "description": "Block height",
                    },
                },
                "required": ["height"],
            },
        ),
        Tool(
            name="get_block_header",
            description="Get raw block header in hex format.",
            inputSchema={
                "type": "object",
                "properties": {
                    "hash": {
                        "type": "string",
                        "description": "Block hash",
                    },
                },
                "required": ["hash"],
            },
        ),
        Tool(
            name="get_block_txids",
            description="Get all transaction IDs in a block.",
            inputSchema={
                "type": "object",
                "properties": {
                    "hash": {
                        "type": "string",
                        "description": "Block hash",
                    },
                },
                "required": ["hash"],
            },
        ),
        Tool(
            name="get_block_txs",
            description="Get transactions in a block (paginated, 25 per page).",
            inputSchema={
                "type": "object",
                "properties": {
                    "hash": {
                        "type": "string",
                        "description": "Block hash",
                    },
                    "start_index": {
                        "type": "integer",
                        "description": "Starting index for pagination (default: 0)",
                        "default": 0,
                    },
                },
                "required": ["hash"],
            },
        ),
        Tool(
            name="get_blocks",
            description="Get recent blocks (10 blocks before start_height, or most recent if not specified).",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_height": {
                        "type": "integer",
                        "description": "Starting block height (optional, defaults to tip)",
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="get_block_tip_height",
            description="Get the current block height (chain tip).",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="get_block_tip_hash",
            description="Get the current block hash (chain tip).",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="get_block_audit_summary",
            description="Get block audit summary comparing expected vs actual transactions.",
            inputSchema={
                "type": "object",
                "properties": {
                    "hash": {
                        "type": "string",
                        "description": "Block hash",
                    },
                },
                "required": ["hash"],
            },
        ),
    ]


async def handle_block_tool(name: str, arguments: dict, client: MempoolClient) -> list[TextContent] | None:
    """Handle block tool calls. Returns None if tool not handled."""
    try:
        if name == "get_block":
            hash = arguments["hash"]
            result = await client.get_block(hash)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_block_by_height":
            height = arguments["height"]
            result = await client.get_block_height(height)
            return [TextContent(type="text", text=f"Block hash at height {height}: {result}")]

        elif name == "get_block_header":
            hash = arguments["hash"]
            result = await client.get_block_header(hash)
            return [TextContent(type="text", text=result)]

        elif name == "get_block_txids":
            hash = arguments["hash"]
            result = await client.get_block_txids(hash)
            summary = f"Block {hash[:16]}... contains {len(result)} transactions\n\nFirst 20 txids:\n"
            summary += "\n".join(result[:20])
            if len(result) > 20:
                summary += f"\n... and {len(result) - 20} more"
            return [TextContent(type="text", text=summary)]

        elif name == "get_block_txs":
            hash = arguments["hash"]
            start_index = arguments.get("start_index", 0)
            result = await client.get_block_txs(hash, start_index)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_blocks":
            start_height = arguments.get("start_height")
            result = await client.get_blocks(start_height)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_block_tip_height":
            result = await client.get_block_tip_height()
            return [TextContent(type="text", text=f"Current block height: {result}")]

        elif name == "get_block_tip_hash":
            result = await client.get_block_tip_hash()
            return [TextContent(type="text", text=f"Current block hash: {result}")]

        elif name == "get_block_audit_summary":
            hash = arguments["hash"]
            result = await client.get_block_audit_summary(hash)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]

    return None
