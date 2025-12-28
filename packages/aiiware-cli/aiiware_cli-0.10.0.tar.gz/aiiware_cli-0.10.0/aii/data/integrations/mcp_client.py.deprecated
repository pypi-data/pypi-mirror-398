"""MCP (Model Context Protocol) Client Integration"""

import asyncio
import json
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import aiohttp


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server"""

    name: str
    url: str
    auth_token: str | None = None
    timeout: int = 30
    retries: int = 3


@dataclass
class MCPResult:
    """Result from MCP server query"""

    success: bool
    data: Any
    server_name: str
    query: str
    timestamp: datetime
    error: str | None = None

    @classmethod
    def from_response(
        cls, response: dict[str, Any], server_name: str, query: str
    ) -> "MCPResult":
        """Create MCPResult from server response"""
        return cls(
            success=response.get("success", False),
            data=response.get("data"),
            server_name=server_name,
            query=query,
            timestamp=datetime.now(),
            error=response.get("error"),
        )


class MCPServer:
    """Individual MCP server connection"""

    def __init__(self, config: MCPServerConfig):
        self.config = config
        self.session: aiohttp.ClientSession | None = None
        self.connected = False
        self.capabilities: list[str] = []

    async def connect(self) -> bool:
        """Establish connection to MCP server"""
        if not self.session:
            connector = aiohttp.TCPConnector(limit=10)
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self.session = aiohttp.ClientSession(connector=connector, timeout=timeout)

        try:
            # Test connection and get capabilities
            response = await self._make_request("GET", "/capabilities")
            if response.get("success"):
                self.capabilities = response.get("capabilities", [])
                self.connected = True
                return True

        except Exception as e:
            print(f"Failed to connect to MCP server {self.config.name}: {e}")

        return False

    async def execute_query(
        self, query: str, context: dict[str, Any] = None
    ) -> MCPResult:
        """Execute query against MCP server"""
        if not self.connected:
            await self.connect()

        if not self.connected:
            return MCPResult(
                success=False,
                data=None,
                server_name=self.config.name,
                query=query,
                timestamp=datetime.now(),
                error="Not connected to server",
            )

        try:
            payload = {"query": query, "context": context or {}}

            response = await self._make_request("POST", "/query", payload)
            return MCPResult.from_response(response, self.config.name, query)

        except Exception as e:
            return MCPResult(
                success=False,
                data=None,
                server_name=self.config.name,
                query=query,
                timestamp=datetime.now(),
                error=str(e),
            )

    async def stream_query(
        self, query: str, context: dict[str, Any] = None
    ) -> AsyncIterator[dict[str, Any]]:
        """Execute streaming query against MCP server"""
        if not self.connected:
            await self.connect()

        if not self.connected:
            return

        try:
            payload = {"query": query, "context": context or {}, "stream": True}

            async with self.session.post(
                f"{self.config.url}/stream", json=payload, headers=self._get_headers()
            ) as response:
                if response.status == 200:
                    async for line in response.content:
                        try:
                            data = json.loads(line.decode().strip())
                            yield data
                        except json.JSONDecodeError:
                            continue

        except Exception as e:
            yield {"error": str(e), "success": False}

    async def get_capabilities(self) -> list[str]:
        """Get server capabilities"""
        if not self.connected:
            await self.connect()

        return self.capabilities

    async def close(self) -> None:
        """Close connection to MCP server"""
        if self.session:
            await self.session.close()
            self.session = None
        self.connected = False

    async def _make_request(
        self, method: str, endpoint: str, data: dict[str, Any] = None
    ) -> dict[str, Any]:
        """Make HTTP request to MCP server"""
        if not self.session:
            raise RuntimeError("Session not initialized")

        url = f"{self.config.url.rstrip('/')}{endpoint}"
        headers = self._get_headers()

        for attempt in range(self.config.retries):
            try:
                if method.upper() == "GET":
                    async with self.session.get(url, headers=headers) as response:
                        return await self._handle_response(response)
                elif method.upper() == "POST":
                    async with self.session.post(
                        url, json=data, headers=headers
                    ) as response:
                        return await self._handle_response(response)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

            except Exception as e:
                if attempt == self.config.retries - 1:
                    raise e
                await asyncio.sleep(2**attempt)  # Exponential backoff

    def _get_headers(self) -> dict[str, str]:
        """Get HTTP headers for requests"""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "AII-MCP-Client/1.0",
        }

        if self.config.auth_token:
            headers["Authorization"] = f"Bearer {self.config.auth_token}"

        return headers

    async def _handle_response(
        self, response: aiohttp.ClientResponse
    ) -> dict[str, Any]:
        """Handle HTTP response"""
        if response.status == 200:
            return await response.json()
        else:
            error_text = await response.text()
            raise RuntimeError(f"HTTP {response.status}: {error_text}")


class MCPClient:
    """Main MCP client managing multiple server connections"""

    def __init__(self, server_configs: list[MCPServerConfig] = None):
        """Initialize MCP client with server configurations"""
        self.servers: dict[str, MCPServer] = {}
        self.active_connections: dict[str, bool] = {}

        if server_configs:
            for config in server_configs:
                self.add_server(config)

    def add_server(self, config: MCPServerConfig) -> bool:
        """Add MCP server configuration"""
        try:
            server = MCPServer(config)
            self.servers[config.name] = server
            self.active_connections[config.name] = False
            return True
        except Exception as e:
            print(f"Failed to add MCP server {config.name}: {e}")
            return False

    async def connect_all(self) -> dict[str, bool]:
        """Connect to all configured servers"""
        connection_results = {}

        for name, server in self.servers.items():
            try:
                success = await server.connect()
                self.active_connections[name] = success
                connection_results[name] = success
            except Exception as e:
                print(f"Failed to connect to {name}: {e}")
                connection_results[name] = False

        return connection_results

    async def query(
        self, server_name: str, query: str, context: dict[str, Any] = None
    ) -> MCPResult:
        """Query a specific MCP server"""
        if server_name not in self.servers:
            return MCPResult(
                success=False,
                data=None,
                server_name=server_name,
                query=query,
                timestamp=datetime.now(),
                error=f"Server '{server_name}' not configured",
            )

        server = self.servers[server_name]
        return await server.execute_query(query, context)

    async def query_all(
        self, query: str, context: dict[str, Any] = None, parallel: bool = True
    ) -> dict[str, MCPResult]:
        """Query all available servers"""
        if parallel:
            # Execute queries in parallel
            tasks = []
            for name, server in self.servers.items():
                if self.active_connections.get(name, False):
                    task = server.execute_query(query, context)
                    tasks.append((name, task))

            results = {}
            if tasks:
                completed_tasks = await asyncio.gather(
                    *[task for _, task in tasks], return_exceptions=True
                )

                for (name, _), result in zip(tasks, completed_tasks, strict=False):
                    if isinstance(result, Exception):
                        results[name] = MCPResult(
                            success=False,
                            data=None,
                            server_name=name,
                            query=query,
                            timestamp=datetime.now(),
                            error=str(result),
                        )
                    else:
                        results[name] = result

            return results

        else:
            # Execute queries sequentially
            results = {}
            for name, server in self.servers.items():
                if self.active_connections.get(name, False):
                    results[name] = await server.execute_query(query, context)

            return results

    async def stream_query(
        self, server_name: str, query: str, context: dict[str, Any] = None
    ) -> AsyncIterator[dict[str, Any]]:
        """Execute streaming query against specific server"""
        if server_name not in self.servers:
            yield {"error": f"Server '{server_name}' not configured", "success": False}
            return

        server = self.servers[server_name]
        async for data in server.stream_query(query, context):
            yield data

    async def list_capabilities(
        self, server_name: str | None = None
    ) -> dict[str, list[str]]:
        """List capabilities of servers"""
        capabilities = {}

        if server_name:
            if server_name in self.servers:
                caps = await self.servers[server_name].get_capabilities()
                capabilities[server_name] = caps
        else:
            for name, server in self.servers.items():
                if self.active_connections.get(name, False):
                    caps = await server.get_capabilities()
                    capabilities[name] = caps

        return capabilities

    def get_server_status(self) -> dict[str, dict[str, Any]]:
        """Get status of all servers"""
        status = {}
        for name, server in self.servers.items():
            status[name] = {
                "connected": self.active_connections.get(name, False),
                "url": server.config.url,
                "capabilities": server.capabilities if server.connected else [],
            }
        return status

    async def close_all(self) -> None:
        """Close all server connections"""
        for server in self.servers.values():
            await server.close()

        self.active_connections = dict.fromkeys(self.active_connections, False)

    async def close(self) -> None:
        """Close MCP client"""
        await self.close_all()
