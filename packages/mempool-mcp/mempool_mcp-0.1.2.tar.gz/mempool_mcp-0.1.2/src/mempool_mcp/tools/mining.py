"""Mining-related tools."""

import json
from mcp.types import Tool, TextContent

from ..client import MempoolClient


def get_mining_tools() -> list[Tool]:
    """Return mining tool definitions."""
    return [
        Tool(
            name="get_mining_pools",
            description="Get mining pool statistics for a time interval. Shows pool distribution, block counts, and hashrate share.",
            inputSchema={
                "type": "object",
                "properties": {
                    "interval": {
                        "type": "string",
                        "description": "Time interval: 24h, 3d, 1w, 1m, 3m, 6m, 1y, 2y, 3y, all (default: 1w)",
                        "default": "1w",
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="get_mining_pool",
            description="Get detailed info for a specific mining pool.",
            inputSchema={
                "type": "object",
                "properties": {
                    "slug": {
                        "type": "string",
                        "description": "Pool slug (e.g., 'foundryusa', 'antpool', 'f2pool', 'binance-pool')",
                    },
                },
                "required": ["slug"],
            },
        ),
        Tool(
            name="get_mining_pool_hashrate",
            description="Get historical hashrate for a specific mining pool.",
            inputSchema={
                "type": "object",
                "properties": {
                    "slug": {
                        "type": "string",
                        "description": "Pool slug",
                    },
                },
                "required": ["slug"],
            },
        ),
        Tool(
            name="get_mining_pool_blocks",
            description="Get blocks mined by a specific pool.",
            inputSchema={
                "type": "object",
                "properties": {
                    "slug": {
                        "type": "string",
                        "description": "Pool slug",
                    },
                    "height": {
                        "type": "integer",
                        "description": "Starting height for pagination (optional)",
                    },
                },
                "required": ["slug"],
            },
        ),
        Tool(
            name="get_hashrate",
            description="Get network hashrate history.",
            inputSchema={
                "type": "object",
                "properties": {
                    "interval": {
                        "type": "string",
                        "description": "Time interval: 1m, 3m, 6m, 1y, 2y, 3y, all (default: 1m)",
                        "default": "1m",
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="get_difficulty_adjustments",
            description="Get difficulty adjustment history.",
            inputSchema={
                "type": "object",
                "properties": {
                    "interval": {
                        "type": "string",
                        "description": "Time interval (optional)",
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="get_reward_stats",
            description="Get mining reward statistics over recent blocks.",
            inputSchema={
                "type": "object",
                "properties": {
                    "block_count": {
                        "type": "integer",
                        "description": "Number of blocks to analyze (default: 100)",
                        "default": 100,
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="get_block_fees",
            description="Get historical block fee data.",
            inputSchema={
                "type": "object",
                "properties": {
                    "interval": {
                        "type": "string",
                        "description": "Time interval (default: 1m)",
                        "default": "1m",
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="get_block_rewards",
            description="Get historical block reward data.",
            inputSchema={
                "type": "object",
                "properties": {
                    "interval": {
                        "type": "string",
                        "description": "Time interval (default: 1m)",
                        "default": "1m",
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="get_block_sizes",
            description="Get historical block sizes and weights.",
            inputSchema={
                "type": "object",
                "properties": {
                    "interval": {
                        "type": "string",
                        "description": "Time interval (default: 1m)",
                        "default": "1m",
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="get_block_fee_rates",
            description="Get historical block fee rates.",
            inputSchema={
                "type": "object",
                "properties": {
                    "interval": {
                        "type": "string",
                        "description": "Time interval (default: 1m)",
                        "default": "1m",
                    },
                },
                "required": [],
            },
        ),
    ]


async def handle_mining_tool(name: str, arguments: dict, client: MempoolClient) -> list[TextContent] | None:
    """Handle mining tool calls. Returns None if tool not handled."""
    try:
        if name == "get_mining_pools":
            interval = arguments.get("interval", "1w")
            result = await client.get_mining_pools(interval)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_mining_pool":
            slug = arguments["slug"]
            result = await client.get_mining_pool(slug)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_mining_pool_hashrate":
            slug = arguments["slug"]
            result = await client.get_mining_pool_hashrate(slug)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_mining_pool_blocks":
            slug = arguments["slug"]
            height = arguments.get("height")
            result = await client.get_mining_pool_blocks(slug, height)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_hashrate":
            interval = arguments.get("interval", "1m")
            result = await client.get_hashrate(interval)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_difficulty_adjustments":
            interval = arguments.get("interval")
            result = await client.get_difficulty_adjustments(interval)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_reward_stats":
            block_count = arguments.get("block_count", 100)
            result = await client.get_reward_stats(block_count)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_block_fees":
            interval = arguments.get("interval", "1m")
            result = await client.get_block_fees(interval)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_block_rewards":
            interval = arguments.get("interval", "1m")
            result = await client.get_block_rewards(interval)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_block_sizes":
            interval = arguments.get("interval", "1m")
            result = await client.get_block_sizes(interval)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_block_fee_rates":
            interval = arguments.get("interval", "1m")
            result = await client.get_block_fee_rates(interval)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]

    return None
