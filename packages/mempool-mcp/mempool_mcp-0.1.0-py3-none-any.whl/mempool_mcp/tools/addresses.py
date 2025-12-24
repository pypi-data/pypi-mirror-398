"""Address-related tools."""

import json
from mcp.types import Tool, TextContent

from ..client import MempoolClient


def get_address_tools() -> list[Tool]:
    """Return address tool definitions."""
    return [
        Tool(
            name="get_address",
            description="Get address information including balance (confirmed/unconfirmed), transaction count, and chain stats.",
            inputSchema={
                "type": "object",
                "properties": {
                    "address": {
                        "type": "string",
                        "description": "Bitcoin address",
                    },
                },
                "required": ["address"],
            },
        ),
        Tool(
            name="get_address_txs",
            description="Get transaction history for an address (up to 50 most recent).",
            inputSchema={
                "type": "object",
                "properties": {
                    "address": {
                        "type": "string",
                        "description": "Bitcoin address",
                    },
                },
                "required": ["address"],
            },
        ),
        Tool(
            name="get_address_txs_chain",
            description="Get confirmed transactions for an address with pagination.",
            inputSchema={
                "type": "object",
                "properties": {
                    "address": {
                        "type": "string",
                        "description": "Bitcoin address",
                    },
                    "last_seen_txid": {
                        "type": "string",
                        "description": "Last seen txid for pagination (optional)",
                    },
                },
                "required": ["address"],
            },
        ),
        Tool(
            name="get_address_txs_mempool",
            description="Get unconfirmed (mempool) transactions for an address.",
            inputSchema={
                "type": "object",
                "properties": {
                    "address": {
                        "type": "string",
                        "description": "Bitcoin address",
                    },
                },
                "required": ["address"],
            },
        ),
        Tool(
            name="get_address_utxos",
            description="Get unspent transaction outputs (UTXOs) for an address.",
            inputSchema={
                "type": "object",
                "properties": {
                    "address": {
                        "type": "string",
                        "description": "Bitcoin address",
                    },
                },
                "required": ["address"],
            },
        ),
        Tool(
            name="get_scripthash",
            description="Get scripthash information (for advanced users).",
            inputSchema={
                "type": "object",
                "properties": {
                    "scripthash": {
                        "type": "string",
                        "description": "Scripthash (SHA256 of output script, reversed)",
                    },
                },
                "required": ["scripthash"],
            },
        ),
        Tool(
            name="get_scripthash_utxos",
            description="Get UTXOs for a scripthash.",
            inputSchema={
                "type": "object",
                "properties": {
                    "scripthash": {
                        "type": "string",
                        "description": "Scripthash",
                    },
                },
                "required": ["scripthash"],
            },
        ),
    ]


async def handle_address_tool(name: str, arguments: dict, client: MempoolClient) -> list[TextContent] | None:
    """Handle address tool calls. Returns None if tool not handled."""
    try:
        if name == "get_address":
            address = arguments["address"]
            result = await client.get_address(address)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_address_txs":
            address = arguments["address"]
            result = await client.get_address_txs(address)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_address_txs_chain":
            address = arguments["address"]
            last_seen = arguments.get("last_seen_txid")
            result = await client.get_address_txs_chain(address, last_seen)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_address_txs_mempool":
            address = arguments["address"]
            result = await client.get_address_txs_mempool(address)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_address_utxos":
            address = arguments["address"]
            result = await client.get_address_utxos(address)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_scripthash":
            scripthash = arguments["scripthash"]
            result = await client.get_scripthash(scripthash)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_scripthash_utxos":
            scripthash = arguments["scripthash"]
            result = await client.get_scripthash_utxos(scripthash)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]

    return None
