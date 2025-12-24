"""Transaction-related tools."""

import json
from mcp.types import Tool, TextContent

from ..client import MempoolClient


def get_transaction_tools() -> list[Tool]:
    """Return transaction tool definitions."""
    return [
        Tool(
            name="get_transaction",
            description="Get full transaction details including inputs, outputs, fees, and confirmation status.",
            inputSchema={
                "type": "object",
                "properties": {
                    "txid": {
                        "type": "string",
                        "description": "Transaction ID (64 hex characters)",
                    },
                },
                "required": ["txid"],
            },
        ),
        Tool(
            name="get_transaction_hex",
            description="Get raw transaction in hex format.",
            inputSchema={
                "type": "object",
                "properties": {
                    "txid": {
                        "type": "string",
                        "description": "Transaction ID",
                    },
                },
                "required": ["txid"],
            },
        ),
        Tool(
            name="get_transaction_status",
            description="Get transaction confirmation status (confirmed, block height, block hash).",
            inputSchema={
                "type": "object",
                "properties": {
                    "txid": {
                        "type": "string",
                        "description": "Transaction ID",
                    },
                },
                "required": ["txid"],
            },
        ),
        Tool(
            name="get_transaction_outspends",
            description="Get spending status for each output of a transaction.",
            inputSchema={
                "type": "object",
                "properties": {
                    "txid": {
                        "type": "string",
                        "description": "Transaction ID",
                    },
                },
                "required": ["txid"],
            },
        ),
        Tool(
            name="get_transaction_merkle_proof",
            description="Get merkle inclusion proof for a confirmed transaction.",
            inputSchema={
                "type": "object",
                "properties": {
                    "txid": {
                        "type": "string",
                        "description": "Transaction ID",
                    },
                },
                "required": ["txid"],
            },
        ),
        Tool(
            name="get_rbf_history",
            description="Get RBF replacement history for a transaction.",
            inputSchema={
                "type": "object",
                "properties": {
                    "txid": {
                        "type": "string",
                        "description": "Transaction ID",
                    },
                },
                "required": ["txid"],
            },
        ),
        Tool(
            name="get_cpfp_info",
            description="Get CPFP (Child Pays For Parent) fee information for a transaction.",
            inputSchema={
                "type": "object",
                "properties": {
                    "txid": {
                        "type": "string",
                        "description": "Transaction ID",
                    },
                },
                "required": ["txid"],
            },
        ),
        Tool(
            name="push_transaction",
            description="Broadcast a signed raw transaction to the Bitcoin network.",
            inputSchema={
                "type": "object",
                "properties": {
                    "tx_hex": {
                        "type": "string",
                        "description": "Signed raw transaction in hex format",
                    },
                },
                "required": ["tx_hex"],
            },
        ),
    ]


async def handle_transaction_tool(name: str, arguments: dict, client: MempoolClient) -> list[TextContent] | None:
    """Handle transaction tool calls. Returns None if tool not handled."""
    try:
        if name == "get_transaction":
            txid = arguments["txid"]
            result = await client.get_transaction(txid)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_transaction_hex":
            txid = arguments["txid"]
            result = await client.get_transaction_hex(txid)
            return [TextContent(type="text", text=result)]

        elif name == "get_transaction_status":
            txid = arguments["txid"]
            result = await client.get_transaction_status(txid)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_transaction_outspends":
            txid = arguments["txid"]
            result = await client.get_transaction_outspends(txid)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_transaction_merkle_proof":
            txid = arguments["txid"]
            result = await client.get_transaction_merkle_proof(txid)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_rbf_history":
            txid = arguments["txid"]
            result = await client.get_rbf_history(txid)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_cpfp_info":
            txid = arguments["txid"]
            result = await client.get_cpfp_info(txid)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "push_transaction":
            tx_hex = arguments["tx_hex"]
            result = await client.push_transaction(tx_hex)
            return [TextContent(type="text", text=f"Transaction broadcast result: {result}")]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]

    return None
