"""Lightning Network tools."""

import json
from mcp.types import Tool, TextContent

from ..client import MempoolClient


def get_lightning_tools() -> list[Tool]:
    """Return Lightning Network tool definitions."""
    return [
        Tool(
            name="get_lightning_statistics",
            description="Get Lightning Network statistics including node count, channel count, and total capacity.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="get_lightning_nodes_rankings",
            description="Get top Lightning nodes ranked by a metric.",
            inputSchema={
                "type": "object",
                "properties": {
                    "metric": {
                        "type": "string",
                        "description": "Ranking metric: capacity, channels, or age (default: capacity)",
                        "default": "capacity",
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="get_lightning_node",
            description="Get detailed information about a Lightning node.",
            inputSchema={
                "type": "object",
                "properties": {
                    "public_key": {
                        "type": "string",
                        "description": "Node public key (66 hex characters)",
                    },
                },
                "required": ["public_key"],
            },
        ),
        Tool(
            name="search_lightning_nodes",
            description="Search for Lightning nodes by alias or public key.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (node alias or public key prefix)",
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="get_lightning_channels",
            description="Get channels for a Lightning node.",
            inputSchema={
                "type": "object",
                "properties": {
                    "public_key": {
                        "type": "string",
                        "description": "Node public key",
                    },
                },
                "required": ["public_key"],
            },
        ),
        Tool(
            name="get_lightning_channel",
            description="Get information about a specific Lightning channel.",
            inputSchema={
                "type": "object",
                "properties": {
                    "short_id": {
                        "type": "string",
                        "description": "Channel short ID (e.g., '123456x789x0')",
                    },
                },
                "required": ["short_id"],
            },
        ),
    ]


async def handle_lightning_tool(name: str, arguments: dict, client: MempoolClient) -> list[TextContent] | None:
    """Handle Lightning Network tool calls. Returns None if tool not handled."""
    try:
        if name == "get_lightning_statistics":
            result = await client.get_lightning_statistics()
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_lightning_nodes_rankings":
            metric = arguments.get("metric", "capacity")
            result = await client.get_lightning_nodes_rankings(metric)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_lightning_node":
            public_key = arguments["public_key"]
            result = await client.get_lightning_node(public_key)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "search_lightning_nodes":
            query = arguments["query"]
            result = await client.search_lightning_nodes(query)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_lightning_channels":
            public_key = arguments["public_key"]
            result = await client.get_lightning_channels(public_key)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_lightning_channel":
            short_id = arguments["short_id"]
            result = await client.get_lightning_channel(short_id)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]

    return None
