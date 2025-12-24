"""HTTP client for Mempool API with Tor and .local support."""

import asyncio
import atexit
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from typing import Any
from urllib.parse import urlparse

import httpx
from httpx_socks import AsyncProxyTransport


def get_default_base_url() -> str:
    """Get the base URL from environment. Raises if not configured."""
    url = os.getenv("MEMPOOL_API_URL")
    if not url:
        raise RuntimeError(
            "MEMPOOL_API_URL environment variable is required. "
            "Set it in your MCP server configuration."
        )
    return url


def get_tor_proxy() -> str | None:
    """Get Tor SOCKS proxy from environment."""
    return os.getenv("MEMPOOL_TOR_PROXY", "socks5://127.0.0.1:9050")


def get_tor_auto_start() -> bool:
    """Check if Tor auto-start is enabled (default: True)."""
    return os.getenv("MEMPOOL_TOR_AUTO_START", "true").lower() in ("true", "1", "yes")


def requires_tor(url: str) -> bool:
    """Check if URL requires Tor (onion address)."""
    parsed = urlparse(url)
    return parsed.hostname and parsed.hostname.endswith(".onion")


def get_ssl_verify() -> bool | str:
    """Get SSL verification setting.

    Returns:
        - False if MEMPOOL_SSL_VERIFY is "false" (disable verification)
        - Path to CA cert if MEMPOOL_CA_CERT is set
        - True otherwise (default SSL verification)
    """
    ssl_verify = os.getenv("MEMPOOL_SSL_VERIFY", "true").lower()
    if ssl_verify in ("false", "0", "no"):
        return False

    ca_cert = os.getenv("MEMPOOL_CA_CERT")
    if ca_cert:
        return ca_cert

    return True


class TorManager:
    """Manages a Tor subprocess for SOCKS proxy connections."""

    _instance: "TorManager | None" = None
    _process: subprocess.Popen | None = None
    _data_dir: str | None = None
    _socks_port: int = 9050

    @classmethod
    def get_instance(cls) -> "TorManager":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _is_port_open(self, host: str, port: int, timeout: float = 1.0) -> bool:
        """Check if a port is open and accepting connections."""
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except (OSError, socket.timeout):
            return False

    def _parse_proxy_url(self, proxy_url: str) -> tuple[str, int]:
        """Parse proxy URL to get host and port."""
        parsed = urlparse(proxy_url)
        host = parsed.hostname or "127.0.0.1"
        port = parsed.port or 9050
        return host, port

    def is_tor_running(self, proxy_url: str) -> bool:
        """Check if Tor is already running on the configured proxy."""
        host, port = self._parse_proxy_url(proxy_url)
        return self._is_port_open(host, port)

    def start_tor(self, proxy_url: str, timeout: int = 30) -> bool:
        """Start Tor if not already running. Returns True if Tor is available."""
        host, port = self._parse_proxy_url(proxy_url)

        # Check if already running
        if self.is_tor_running(proxy_url):
            return True

        # Only auto-start for localhost
        if host not in ("127.0.0.1", "localhost", "::1"):
            raise RuntimeError(
                f"Tor proxy at {host}:{port} is not reachable and auto-start "
                "is only supported for localhost. Please start Tor manually."
            )

        # Check if tor binary exists
        tor_path = shutil.which("tor")
        if not tor_path:
            if sys.platform == "win32":
                raise RuntimeError(
                    "Tor is not installed or not in PATH. Install Tor Expert Bundle:\n"
                    "  1. Download: www.torproject.org/download/tor/\n"
                    "  2. Extract to C:\\tor\n"
                    "  3. Add C:\\tor to your system PATH\n"
                    "  4. Restart your terminal\n\n"
                    "Or use Chocolatey: choco install tor\n\n"
                    "Alternative: Use Tor Browser (port 9150) with these env vars:\n"
                    "  MEMPOOL_TOR_PROXY=socks5://127.0.0.1:9150\n"
                    "  MEMPOOL_TOR_AUTO_START=false"
                )
            else:
                raise RuntimeError(
                    "Tor is not installed. Please install it:\n"
                    "  Ubuntu/Debian: sudo apt install tor\n"
                    "  Fedora: sudo dnf install tor\n"
                    "  Arch: sudo pacman -S tor\n"
                    "  macOS: brew install tor"
                )

        # Create temp directory for Tor data
        self._data_dir = tempfile.mkdtemp(prefix="mempool_tor_")
        self._socks_port = port

        # Write minimal torrc
        torrc_path = os.path.join(self._data_dir, "torrc")
        with open(torrc_path, "w") as f:
            f.write(f"SocksPort {port}\n")
            f.write(f"DataDirectory {self._data_dir}\n")
            f.write("Log notice stderr\n")

        # Start Tor process
        try:
            self._process = subprocess.Popen(
                [tor_path, "-f", torrc_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except Exception as e:
            self._cleanup()
            raise RuntimeError(f"Failed to start Tor: {e}")

        # Register cleanup on exit
        atexit.register(self.stop_tor)

        # Wait for Tor to be ready
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self._is_port_open(host, port):
                return True

            # Check if process died
            if self._process.poll() is not None:
                stderr = self._process.stderr.read().decode() if self._process.stderr else ""
                self._cleanup()
                raise RuntimeError(f"Tor process exited unexpectedly: {stderr}")

            time.sleep(0.5)

        # Timeout
        self.stop_tor()
        raise RuntimeError(f"Tor failed to start within {timeout} seconds")

    def stop_tor(self) -> None:
        """Stop the Tor subprocess if we started it."""
        if self._process is not None:
            try:
                self._process.terminate()
                self._process.wait(timeout=5)
            except Exception:
                self._process.kill()
            self._process = None
        self._cleanup()

    def _cleanup(self) -> None:
        """Clean up temp directory."""
        if self._data_dir and os.path.exists(self._data_dir):
            try:
                shutil.rmtree(self._data_dir)
            except Exception:
                pass
            self._data_dir = None


async def ensure_tor_available(proxy_url: str) -> None:
    """Ensure Tor is available, starting it if necessary and enabled."""
    if not get_tor_auto_start():
        return

    manager = TorManager.get_instance()
    if not manager.is_tor_running(proxy_url):
        # Run in thread to avoid blocking async loop
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, manager.start_tor, proxy_url)


class MempoolClient:
    """Async HTTP client for Mempool API."""

    def __init__(self, base_url: str | None = None):
        self.base_url = (base_url or get_default_base_url()).rstrip("/")
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None:
            transport = None
            ssl_verify = get_ssl_verify()

            if requires_tor(self.base_url):
                proxy = get_tor_proxy()
                if proxy:
                    # Ensure Tor is running (auto-start if needed)
                    await ensure_tor_available(proxy)
                    transport = AsyncProxyTransport.from_url(proxy)

            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                transport=transport,
                timeout=httpx.Timeout(30.0),
                follow_redirects=True,
                verify=ssl_verify,
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def get(self, endpoint: str, params: dict[str, Any] | None = None) -> Any:
        """Make a GET request to the API."""
        client = await self._get_client()
        response = await client.get(endpoint, params=params)
        response.raise_for_status()
        return response.json()

    async def get_text(self, endpoint: str) -> str:
        """Make a GET request and return raw text."""
        client = await self._get_client()
        response = await client.get(endpoint)
        response.raise_for_status()
        return response.text

    async def post(self, endpoint: str, data: Any = None) -> Any:
        """Make a POST request to the API."""
        client = await self._get_client()
        if isinstance(data, str):
            response = await client.post(
                endpoint,
                content=data,
                headers={"Content-Type": "text/plain"},
            )
        else:
            response = await client.post(endpoint, json=data)
        response.raise_for_status()
        try:
            return response.json()
        except Exception:
            return response.text

    # === General/Fees ===

    async def get_difficulty_adjustment(self) -> dict:
        """Get current difficulty adjustment progress."""
        return await self.get("/v1/difficulty-adjustment")

    async def get_recommended_fees(self) -> dict:
        """Get recommended transaction fees."""
        return await self.get("/v1/fees/recommended")

    async def get_mempool_blocks(self) -> list:
        """Get projected mempool blocks."""
        return await self.get("/v1/fees/mempool-blocks")

    async def validate_address(self, address: str) -> dict:
        """Validate a Bitcoin address."""
        return await self.get(f"/v1/validate-address/{address}")

    # === Mempool ===

    async def get_mempool(self) -> dict:
        """Get mempool statistics."""
        return await self.get("/mempool")

    async def get_mempool_txids(self) -> list:
        """Get all transaction IDs in the mempool."""
        return await self.get("/mempool/txids")

    async def get_mempool_recent(self) -> list:
        """Get recent mempool transactions."""
        return await self.get("/mempool/recent")

    # === Transactions ===

    async def get_transaction(self, txid: str) -> dict:
        """Get transaction details."""
        return await self.get(f"/tx/{txid}")

    async def get_transaction_hex(self, txid: str) -> str:
        """Get raw transaction hex."""
        return await self.get_text(f"/tx/{txid}/hex")

    async def get_transaction_status(self, txid: str) -> dict:
        """Get transaction confirmation status."""
        return await self.get(f"/tx/{txid}/status")

    async def get_transaction_outspends(self, txid: str) -> list:
        """Get spending status of transaction outputs."""
        return await self.get(f"/tx/{txid}/outspends")

    async def get_transaction_merkle_proof(self, txid: str) -> dict:
        """Get merkle proof for transaction."""
        return await self.get(f"/tx/{txid}/merkle-proof")

    async def get_rbf_history(self, txid: str) -> dict:
        """Get RBF replacement history."""
        return await self.get(f"/tx/{txid}/rbf")

    async def get_cpfp_info(self, txid: str) -> dict:
        """Get CPFP (Child Pays For Parent) info."""
        return await self.get(f"/v1/cpfp/{txid}")

    async def push_transaction(self, tx_hex: str) -> str:
        """Broadcast a raw transaction."""
        return await self.post("/tx", tx_hex)

    async def get_rbf_replacements(self) -> dict:
        """Get recent RBF replacements."""
        return await self.get("/v1/replacements")

    async def get_fullrbf_replacements(self) -> dict:
        """Get full-RBF replacements."""
        return await self.get("/v1/fullrbf/replacements")

    # === Blocks ===

    async def get_block(self, hash: str) -> dict:
        """Get block details by hash."""
        return await self.get(f"/block/{hash}")

    async def get_block_header(self, hash: str) -> str:
        """Get block header hex."""
        return await self.get_text(f"/block/{hash}/header")

    async def get_block_height(self, height: int) -> str:
        """Get block hash by height."""
        return await self.get_text(f"/block-height/{height}")

    async def get_block_txids(self, hash: str) -> list:
        """Get transaction IDs in a block."""
        return await self.get(f"/block/{hash}/txids")

    async def get_block_txs(self, hash: str, start_index: int = 0) -> list:
        """Get transactions in a block (paginated, 25 per page)."""
        return await self.get(f"/block/{hash}/txs/{start_index}")

    async def get_blocks(self, start_height: int | None = None) -> list:
        """Get recent blocks (10 blocks before start_height or tip)."""
        if start_height is not None:
            return await self.get(f"/v1/blocks/{start_height}")
        return await self.get("/v1/blocks")

    async def get_block_tip_height(self) -> int:
        """Get current block height."""
        return await self.get("/blocks/tip/height")

    async def get_block_tip_hash(self) -> str:
        """Get current block hash."""
        return await self.get_text("/blocks/tip/hash")

    async def get_block_audit_summary(self, hash: str) -> dict:
        """Get block audit summary."""
        return await self.get(f"/v1/block/{hash}/audit-summary")

    # === Addresses ===

    async def get_address(self, address: str) -> dict:
        """Get address info (balance, tx count)."""
        return await self.get(f"/address/{address}")

    async def get_address_txs(self, address: str) -> list:
        """Get address transaction history."""
        return await self.get(f"/address/{address}/txs")

    async def get_address_txs_chain(self, address: str, last_seen_txid: str | None = None) -> list:
        """Get confirmed address transactions (paginated)."""
        endpoint = f"/address/{address}/txs/chain"
        if last_seen_txid:
            endpoint += f"/{last_seen_txid}"
        return await self.get(endpoint)

    async def get_address_txs_mempool(self, address: str) -> list:
        """Get unconfirmed address transactions."""
        return await self.get(f"/address/{address}/txs/mempool")

    async def get_address_utxos(self, address: str) -> list:
        """Get address UTXOs."""
        return await self.get(f"/address/{address}/utxo")

    # === Scripthash (for advanced users) ===

    async def get_scripthash(self, scripthash: str) -> dict:
        """Get scripthash info."""
        return await self.get(f"/scripthash/{scripthash}")

    async def get_scripthash_txs(self, scripthash: str) -> list:
        """Get scripthash transaction history."""
        return await self.get(f"/scripthash/{scripthash}/txs")

    async def get_scripthash_utxos(self, scripthash: str) -> list:
        """Get scripthash UTXOs."""
        return await self.get(f"/scripthash/{scripthash}/utxo")

    # === Mining ===

    async def get_mining_pools(self, interval: str = "1w") -> dict:
        """Get mining pool statistics. Interval: 24h, 3d, 1w, 1m, 3m, 6m, 1y, 2y, 3y, all."""
        return await self.get(f"/v1/mining/pools/{interval}")

    async def get_mining_pool(self, slug: str) -> dict:
        """Get specific mining pool info."""
        return await self.get(f"/v1/mining/pool/{slug}")

    async def get_mining_pool_hashrate(self, slug: str) -> dict:
        """Get mining pool hashrate history."""
        return await self.get(f"/v1/mining/pool/{slug}/hashrate")

    async def get_mining_pool_blocks(self, slug: str, height: int | None = None) -> list:
        """Get blocks mined by a pool."""
        if height is not None:
            return await self.get(f"/v1/mining/pool/{slug}/blocks/{height}")
        return await self.get(f"/v1/mining/pool/{slug}/blocks")

    async def get_hashrate(self, interval: str = "1m") -> dict:
        """Get network hashrate history."""
        return await self.get(f"/v1/mining/hashrate/{interval}")

    async def get_difficulty_adjustments(self, interval: str | None = None) -> list:
        """Get difficulty adjustment history."""
        if interval:
            return await self.get(f"/v1/mining/difficulty-adjustments/{interval}")
        return await self.get("/v1/mining/difficulty-adjustments")

    async def get_reward_stats(self, block_count: int = 100) -> dict:
        """Get mining reward statistics."""
        return await self.get(f"/v1/mining/reward-stats/{block_count}")

    async def get_block_fees(self, interval: str = "1m") -> list:
        """Get historical block fees."""
        return await self.get(f"/v1/mining/blocks/fees/{interval}")

    async def get_block_rewards(self, interval: str = "1m") -> list:
        """Get historical block rewards."""
        return await self.get(f"/v1/mining/blocks/rewards/{interval}")

    async def get_block_sizes(self, interval: str = "1m") -> list:
        """Get historical block sizes and weights."""
        return await self.get(f"/v1/mining/blocks/sizes-weights/{interval}")

    async def get_block_fee_rates(self, interval: str = "1m") -> list:
        """Get historical block fee rates."""
        return await self.get(f"/v1/mining/blocks/fee-rates/{interval}")

    # === Price ===

    async def get_historical_price(self, currency: str = "USD", timestamp: int | None = None) -> dict:
        """Get historical Bitcoin price."""
        params = {"currency": currency}
        if timestamp:
            params["timestamp"] = timestamp
        return await self.get("/v1/historical-price", params)

    # === Lightning (if available) ===

    async def get_lightning_statistics(self) -> dict:
        """Get Lightning Network statistics."""
        return await self.get("/v1/lightning/statistics/latest")

    async def get_lightning_nodes_rankings(self, metric: str = "capacity") -> list:
        """Get top Lightning nodes. Metric: capacity, channels, age."""
        return await self.get(f"/v1/lightning/nodes/rankings/{metric}")

    async def get_lightning_node(self, public_key: str) -> dict:
        """Get Lightning node info."""
        return await self.get(f"/v1/lightning/nodes/{public_key}")

    async def search_lightning_nodes(self, query: str) -> list:
        """Search Lightning nodes."""
        return await self.get(f"/v1/lightning/search", {"searchText": query})

    async def get_lightning_channels(self, public_key: str) -> list:
        """Get channels for a Lightning node."""
        return await self.get(f"/v1/lightning/nodes/{public_key}/channels")

    async def get_lightning_channel(self, short_id: str) -> dict:
        """Get Lightning channel info."""
        return await self.get(f"/v1/lightning/channels/{short_id}")