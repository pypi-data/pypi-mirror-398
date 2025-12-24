# Mempool MCP Server

An MCP server that connects AI assistants like Claude to mempool.space or your own self-hosted instance. Query blockchain data, mempool statistics, fees, mining pools, and Lightning Network information directly through natural language.

## What is this?

This server acts as a bridge between AI assistants and Bitcoin blockchain data. Once configured, you can ask questions like:

- "What's the current Bitcoin block height?"
- "What are the recommended transaction fees right now?"
- "Show me the details of this transaction: [txid]"
- "What's the balance of address bc1q...?"
- "Which mining pools mined the most blocks this week?"
- "What's the current Lightning Network capacity?"

The server supports connecting to:
- **Public API**: mempool.space (default)
- **Self-hosted**: Your own Mempool instance
- **Tor**: .onion hidden services for privacy

## Features

- **50+ tools** covering all Mempool API endpoints
- **Flexible connectivity**: Public API, local instances, or Tor
- **Auto Tor support**: Automatically starts Tor when connecting to .onion addresses
- **Custom SSL certificates**: Support for self-signed certs on local instances

---

## Public API vs Self-Hosted

### Why Self-Host?

The public mempool.space API has rate limits that may interrupt heavy usage. **Running your own Mempool instance has no rate limits**—query as fast and as often as you want.

### Benefits of Self-Hosting

Running your own mempool instance eliminates these restrictions:

| | Public API | Self-Hosted |
|---|---|---|
| **Rate limits** | Yes (shared with all users) | None |
| **Query speed** | Depends on server load | As fast as your hardware |
| **Privacy** | Queries visible to mempool.space | Fully private |
| **Uptime** | Depends on mempool.space | You control it |
| **Data freshness** | Real-time | Real-time (your own node) |
| **Network support** | None | Strengthens Bitcoin decentralization |

Running a full Bitcoin node to power your Mempool instance also directly supports the network—every node helps validate and relay transactions, improving Bitcoin's decentralization and resilience.

### Self-Hosted Options

- **[Mempool](https://github.com/mempool/mempool)** - Run the full stack yourself
- **[Start9](https://start9.com/)** - One-click install on Start9 Embassy
- **[Umbrel](https://umbrel.com/)** - One-click install on Umbrel
- **[RaspiBlitz](https://raspiblitz.org/)** - Included in RaspiBlitz
- **[MyNode](https://mynodebtc.com/)** - Included in MyNode

Once you have a self-hosted instance, just point `MEMPOOL_API_URL` to it and enjoy unlimited queries.

---

## Requirements

### Required
- **Python 3.11+**
- **Claude Code** or another MCP-compatible client

### Optional (for Tor connectivity)
- **Tor** - Required only if connecting to .onion addresses

#### Installing Tor

**Linux (Debian/Ubuntu):**
```bash
sudo apt update && sudo apt install tor
```

**Linux (Fedora):**
```bash
sudo dnf install tor
```

**Linux (Arch):**
```bash
sudo pacman -S tor
```

**macOS:**
```bash
brew install tor
```

**Windows:**

There are two options for Tor on Windows:

**Option A: Tor Expert Bundle (Recommended for MCP)**

The Expert Bundle runs Tor as a background daemon on port 9050. This is what the MCP server expects by default.

1. Download from [torproject.org/download/tor](www.torproject.org/download/tor/)
2. Extract to `C:\tor`
3. Add `C:\tor` to your system PATH
4. Restart your terminal

Or use Chocolatey:
```powershell
choco install tor
```

**Option B: Tor Browser**

If you already have Tor Browser installed, you can use it instead. Tor Browser runs on port **9150** (not 9050), so you need to configure the MCP server accordingly:

```powershell
claude mcp add mempool-tor mempool-mcp --scope user --env MEMPOOL_API_URL=mempoolhqx4isw62xs7ldayuidyx2v2oethdhhj6mlo2r6ad.onion/api --env MEMPOOL_TOR_PROXY=socks5://127.0.0.1:9150 --env MEMPOOL_TOR_AUTO_START=false
```

> **Important:** Tor Browser must be running when you use the MCP server with this configuration.

---

## Installation

**Linux (Debian/Ubuntu):**
```bash
sudo apt install pipx
pipx install mempool-mcp
```

**Linux (other) / macOS:**
```bash
pip install mempool-mcp
# Or use pipx if pip is blocked
```

**Windows:**
```powershell
pip install mempool-mcp
```

---

## Configuration

### Quick Start (Public API)

**Linux/macOS:**
```bash
claude mcp add mempool mempool-mcp --scope user --env MEMPOOL_API_URL=mempool.space/api
```

**Windows (PowerShell):**
```powershell
claude mcp add mempool mempool-mcp --scope user --env MEMPOOL_API_URL=mempool.space/api
```

> **Note:** On Windows, if `mempool-mcp` is not found, use the full path:
> ```powershell
> claude mcp add mempool "$env:APPDATA\Python\Python313\Scripts\mempool-mcp.exe" --scope user --env MEMPOOL_API_URL=mempool.space/api
> ```

Restart Claude Code, then ask: *"What's the current Bitcoin block height?"*

### Manual Configuration

Add to your `~/.claude.json` (global) or project `.mcp.json`:

---

### Option 1: Public API (mempool.space)

Use the public mempool.space API. No additional setup required.

```json
{
  "mcpServers": {
    "mempool": {
      "type": "stdio",
      "command": "mempool-mcp",
      "env": {
        "MEMPOOL_API_URL": "mempool.space/api"
      }
    }
  }
}
```

---

### Option 2: Self-Hosted Mempool Instance

Connect to your own Mempool instance running locally or on your network.

```json
{
  "mcpServers": {
    "mempool": {
      "type": "stdio",
      "command": "mempool-mcp",
      "env": {
        "MEMPOOL_API_URL": "http://localhost:8999/api"
      }
    }
  }
}
```

**With custom SSL certificate (e.g., Start9, Umbrel):**
```json
{
  "env": {
    "MEMPOOL_API_URL": "https://your-node.local/api",
    "MEMPOOL_CA_CERT": "/path/to/your-ca-certificate.crt"
  }
}
```

**Disable SSL verification (not recommended for production):**
```json
{
  "env": {
    "MEMPOOL_API_URL": "https://your-node.local/api",
    "MEMPOOL_SSL_VERIFY": "false"
  }
}
```

---

### Option 3: Tor Hidden Service (.onion)

Connect to Mempool via Tor for maximum privacy. The server will **automatically start Tor** if it's installed and not already running.

```json
{
  "mcpServers": {
    "mempool": {
      "type": "stdio",
      "command": "mempool-mcp",
      "env": {
        "MEMPOOL_API_URL": "mempoolhqx4isw62xs7ldayuidyx2v2oethdhhj6mlo2r6ad.onion/api"
      }
    }
  }
}
```

**With custom Tor proxy port:**
```json
{
  "env": {
    "MEMPOOL_API_URL": "mempoolhqx4isw62xs7ldayuidyx2v2oethdhhj6mlo2r6ad.onion/api",
    "MEMPOOL_TOR_PROXY": "socks5://127.0.0.1:9150"
  }
}
```

**Disable Tor auto-start (use existing Tor instance):**
```json
{
  "env": {
    "MEMPOOL_TOR_AUTO_START": "false"
  }
}
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MEMPOOL_API_URL` | *(required)* | Base URL for Mempool API |
| `MEMPOOL_TOR_PROXY` | `socks5://127.0.0.1:9050` | SOCKS5 proxy for .onion addresses |
| `MEMPOOL_TOR_AUTO_START` | `true` | Auto-start Tor if not running |
| `MEMPOOL_CA_CERT` | *(none)* | Path to CA certificate for self-signed SSL |
| `MEMPOOL_SSL_VERIFY` | `true` | Set to `false` to disable SSL verification |

---

## Available Tools

### General (6 tools)
| Tool | Description |
|------|-------------|
| `get_server_info` | Show current MCP server configuration |
| `get_difficulty_adjustment` | Current difficulty adjustment progress |
| `get_recommended_fees` | Recommended fee rates (sat/vB) |
| `get_mempool_blocks` | Projected mempool blocks with fee ranges |
| `validate_address` | Validate Bitcoin address and get type |
| `get_historical_price` | Historical Bitcoin price data |

### Mempool (5 tools)
| Tool | Description |
|------|-------------|
| `get_mempool` | Mempool statistics (tx count, vsize, fees) |
| `get_mempool_txids` | All transaction IDs in mempool |
| `get_mempool_recent` | Recent mempool transactions |
| `get_rbf_replacements` | Recent RBF replacements |
| `get_fullrbf_replacements` | Full-RBF replacements |

### Transactions (8 tools)
| Tool | Description |
|------|-------------|
| `get_transaction` | Full transaction details |
| `get_transaction_hex` | Raw transaction hex |
| `get_transaction_status` | Confirmation status |
| `get_transaction_outspends` | Output spending status |
| `get_transaction_merkle_proof` | Merkle inclusion proof |
| `get_rbf_history` | RBF replacement history |
| `get_cpfp_info` | CPFP fee information |
| `push_transaction` | Broadcast raw transaction |

### Blocks (9 tools)
| Tool | Description |
|------|-------------|
| `get_block` | Block details by hash |
| `get_block_by_height` | Block hash by height |
| `get_block_header` | Raw block header hex |
| `get_block_txids` | Transaction IDs in block |
| `get_block_txs` | Block transactions (paginated) |
| `get_blocks` | Recent blocks |
| `get_block_tip_height` | Current block height |
| `get_block_tip_hash` | Current block hash |
| `get_block_audit_summary` | Block audit summary |

### Addresses (7 tools)
| Tool | Description |
|------|-------------|
| `get_address` | Address info (balance, tx count) |
| `get_address_txs` | Address transaction history |
| `get_address_txs_chain` | Confirmed transactions (paginated) |
| `get_address_txs_mempool` | Unconfirmed transactions |
| `get_address_utxos` | Address UTXOs |
| `get_scripthash` | Scripthash info |
| `get_scripthash_utxos` | Scripthash UTXOs |

### Mining (11 tools)
| Tool | Description |
|------|-------------|
| `get_mining_pools` | Pool statistics by interval |
| `get_mining_pool` | Specific pool info |
| `get_mining_pool_hashrate` | Pool hashrate history |
| `get_mining_pool_blocks` | Blocks mined by pool |
| `get_hashrate` | Network hashrate history |
| `get_difficulty_adjustments` | Difficulty adjustment history |
| `get_reward_stats` | Mining reward statistics |
| `get_block_fees` | Historical block fees |
| `get_block_rewards` | Historical block rewards |
| `get_block_sizes` | Historical block sizes/weights |
| `get_block_fee_rates` | Historical fee rates |

### Lightning Network (6 tools)
| Tool | Description |
|------|-------------|
| `get_lightning_statistics` | Network statistics |
| `get_lightning_nodes_rankings` | Top nodes by capacity/channels/age |
| `get_lightning_node` | Node details by public key |
| `search_lightning_nodes` | Search nodes by alias |
| `get_lightning_channels` | Node channels |
| `get_lightning_channel` | Channel details |

---

## Usage Examples

Once configured, ask your AI assistant:

**Fees & Mempool:**
- "What are the current recommended fees?"
- "How congested is the mempool right now?"
- "Show me the projected next blocks"

**Transactions:**
- "Look up transaction abc123..."
- "Is this transaction confirmed yet?"
- "What outputs from this tx have been spent?"

**Addresses:**
- "What's the balance of bc1q...?"
- "Show me the UTXOs for this address"
- "List recent transactions for this address"

**Blocks:**
- "What's the current block height?"
- "Show me details for block 800000"
- "Which transactions are in the latest block?"

**Mining:**
- "Which pools mined the most blocks this week?"
- "What's Foundry's current hashrate?"
- "Show me the network hashrate over the past month"

**Lightning:**
- "What's the total Lightning Network capacity?"
- "Find Lightning nodes with 'ACINQ' in the name"
- "Show me the top 10 nodes by capacity"

---

## Troubleshooting

### "MEMPOOL_API_URL not set"
Make sure your MCP configuration includes the `env` section with `MEMPOOL_API_URL`.

### MCP server not connecting / command not found (Windows)

After `pip install mempool-mcp`, the executable may not be in your PATH. Solutions:

**Option 1: Use the full path in the MCP config:**
```powershell
claude mcp add mempool "$env:APPDATA\Python\Python313\Scripts\mempool-mcp.exe" --scope user --env MEMPOOL_API_URL=mempool.space/api
```

**Option 2: Add Python Scripts to PATH:**
```powershell
[Environment]::SetEnvironmentVariable("Path", $env:Path + ";$env:APPDATA\Python\Python313\Scripts", "User")
```
Then restart your terminal.

### Tor connection issues

**"Tor is not installed" error:**
- **Linux/macOS:** Install with your package manager (apt, dnf, pacman, brew)
- **Windows:** Install [Tor Expert Bundle](www.torproject.org/download/tor/) and add to PATH

**Tor proxy connection failed:**
1. Verify Tor is installed: `which tor` (Linux/macOS) or `where tor` (Windows)
2. Check the port:
   - Tor daemon/Expert Bundle uses port **9050** (default)
   - Tor Browser uses port **9150**
3. Test connectivity:
   ```bash
   # Linux/macOS
   curl --socks5-hostname 127.0.0.1:9050 check.torproject.org

   # Windows PowerShell
   Test-NetConnection -ComputerName 127.0.0.1 -Port 9050
   ```

**Using Tor Browser instead of Tor daemon:**

Set these environment variables in your MCP config:
```json
{
  "env": {
    "MEMPOOL_TOR_PROXY": "socks5://127.0.0.1:9150",
    "MEMPOOL_TOR_AUTO_START": "false"
  }
}
```

### SSL certificate errors
For self-hosted instances with self-signed certificates:
- Set `MEMPOOL_CA_CERT` to your CA certificate path, OR
- Set `MEMPOOL_SSL_VERIFY=false` (not recommended for production)

### Server not showing in Claude
1. Restart Claude Code after modifying `~/.claude.json`
2. Make sure `mempool-mcp` is in your PATH (try running `mempool-mcp --help`)
3. Run `/mcp` in Claude to see server status

---

## License

MIT

---

## Links

- [PyPI Package](pypi.org/project/mempool-mcp/)
- [Mempool.space](mempool.space)
- [Mempool API Documentation](mempool.space/docs/api/rest)
- [MCP Protocol](modelcontextprotocol.io)
- [Claude Code](claude.ai/code)