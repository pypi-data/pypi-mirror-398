"""General and fee-related tools."""

import json
import os
from mcp.types import Tool, TextContent

from ..client import MempoolClient, requires_tor, get_ssl_verify


def get_general_tools() -> list[Tool]:
    """Return general/fee tool definitions."""
    return [
        Tool(
            name="get_server_info",
            description="Get information about the MCP server configuration, including the API URL being used and whether Tor is enabled.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="get_difficulty_adjustment",
            description="Get current Bitcoin difficulty adjustment progress, including estimated retarget date, remaining blocks, and percentage change.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="get_recommended_fees",
            description="Get recommended transaction fee rates in sat/vB for fastest, half-hour, hour, economy, and minimum confirmation targets.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="get_mempool_blocks",
            description="Get projected mempool blocks showing fee ranges and transaction counts for upcoming blocks.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="validate_address",
            description="Validate a Bitcoin address and get its type (P2PKH, P2SH, P2WPKH, P2WSH, P2TR).",
            inputSchema={
                "type": "object",
                "properties": {
                    "address": {
                        "type": "string",
                        "description": "Bitcoin address to validate",
                    },
                },
                "required": ["address"],
            },
        ),
        Tool(
            name="get_historical_price",
            description="Get historical Bitcoin price data.",
            inputSchema={
                "type": "object",
                "properties": {
                    "currency": {
                        "type": "string",
                        "description": "Currency code (default: USD)",
                        "default": "USD",
                    },
                    "timestamp": {
                        "type": "integer",
                        "description": "Unix timestamp for historical price (optional)",
                    },
                },
                "required": [],
            },
        ),
    ]


async def handle_general_tool(name: str, arguments: dict, client: MempoolClient) -> list[TextContent] | None:
    """Handle general/fee tool calls. Returns None if tool not handled."""
    try:
        if name == "get_server_info":
            ssl_verify = get_ssl_verify()
            info = {
                "api_url": client.base_url,
                "using_tor": requires_tor(client.base_url),
                "tor_proxy": os.getenv("MEMPOOL_TOR_PROXY"),
                "ssl_verify": ssl_verify if isinstance(ssl_verify, bool) else f"CA cert: {ssl_verify}",
            }
            return [TextContent(type="text", text=json.dumps(info, indent=2))]

        elif name == "get_difficulty_adjustment":
            result = await client.get_difficulty_adjustment()
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_recommended_fees":
            result = await client.get_recommended_fees()
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_mempool_blocks":
            result = await client.get_mempool_blocks()
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "validate_address":
            address = arguments["address"]
            result = await client.validate_address(address)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_historical_price":
            currency = arguments.get("currency", "USD")
            timestamp = arguments.get("timestamp")
            result = await client.get_historical_price(currency, timestamp)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]

    return None
