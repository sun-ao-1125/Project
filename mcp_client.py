"""
Generic MCP (Model Context Protocol) Client

A flexible and extensible client for interacting with MCP servers following
the official MCP specification. Supports multiple transport methods, capability
discovery, tool invocation, resource access, and comprehensive error handling.
"""

import json
import logging
from typing import Optional, Dict, List, Any, Callable, Union
from enum import Enum
from dataclasses import dataclass, field
import asyncio
from abc import ABC, abstractmethod
import httpx
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TransportType(Enum):
    STDIO = "stdio"
    HTTP_SSE = "http_sse"
    HTTP_STREAM = "streamable_http"
    WEBSOCKET = "websocket"


class AuthType(Enum):
    NONE = "none"
    BEARER = "bearer"
    OAUTH2 = "oauth2"
    API_KEY = "api_key"


@dataclass
class MCPConfig:
    server_url: Optional[str] = None
    transport_type: TransportType = TransportType.HTTP_SSE
    auth_type: AuthType = AuthType.NONE
    auth_token: Optional[str] = None
    client_info: Dict[str, str] = field(default_factory=lambda: {
        "name": "generic-mcp-client",
        "version": "1.0.0"
    })
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0


@dataclass
class Tool:
    name: str
    description: str
    parameters: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class Resource:
    uri: str
    name: str
    description: Optional[str] = None
    mime_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class Prompt:
    name: str
    description: str
    parameters: Optional[Dict[str, Any]] = None


class MCPTransport(ABC):
    
    @abstractmethod
    async def connect(self) -> bool:
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        pass
    
    @abstractmethod
    async def send_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    async def receive_event(self) -> Optional[Dict[str, Any]]:
        pass


class HTTPSSETransport(MCPTransport):
    
    def __init__(self, config: MCPConfig):
        self.config = config
        self.client = None
        self.connected = False
    
    async def connect(self) -> bool:
        try:
            logger.info(f"Connecting to MCP server via HTTP+SSE: {self.config.server_url}")
            self.client = httpx.AsyncClient(timeout=self.config.timeout)
            self.connected = True
            return True
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False
    
    async def disconnect(self) -> None:
        if self.client:
            await self.client.aclose()
            self.client = None
        self.connected = False
        logger.info("Disconnected from MCP server")
    
    async def send_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if not self.connected or not self.client:
            raise ConnectionError("Not connected to server")
        
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": self._generate_request_id()
        }
        
        logger.debug(f"Sending request: {method}")
        
        try:
            # Prepare headers
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream"
            }
            
            # Add authentication if configured
            if self.config.auth_type == AuthType.BEARER and self.config.auth_token:
                headers["Authorization"] = f"Bearer {self.config.auth_token}"
            elif self.config.auth_type == AuthType.API_KEY and self.config.auth_token:
                headers["X-API-Key"] = self.config.auth_token
            
            # Send HTTP POST request
            response = await self.client.post(
                self.config.server_url,
                json=request,
                headers=headers
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Handle JSON-RPC response
            if "result" in result:
                return result["result"]
            elif "error" in result:
                error = result["error"]
                raise Exception(f"Server error: {error.get('message', 'Unknown error')}")
            else:
                return result
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP request failed: {e}")
            raise ConnectionError(f"HTTP request failed: {e}")
        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise
    
    async def receive_event(self) -> Optional[Dict[str, Any]]:
        # For HTTP+SSE, we don't receive events in this implementation
        # This would require Server-Sent Events handling
        return None
    
    def _generate_request_id(self) -> str:
        return str(uuid.uuid4())


class StreamableHTTPTransport(MCPTransport):
    
    def __init__(self, config: MCPConfig):
        self.config = config
        self.client = None
        self.connected = False
    
    async def connect(self) -> bool:
        try:
            logger.info(f"Connecting to MCP server via Streamable HTTP: {self.config.server_url}")
            self.client = httpx.AsyncClient(timeout=self.config.timeout)
            self.connected = True
            return True
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False
    
    async def disconnect(self) -> None:
        if self.client:
            await self.client.aclose()
            self.client = None
        self.connected = False
        logger.info("Disconnected from MCP server")
    
    async def send_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if not self.connected or not self.client:
            raise ConnectionError("Not connected to server")
        
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": self._generate_request_id()
        }
        
        logger.debug(f"Sending streamable request: {method}")
        
        try:
            # Prepare headers for streamable HTTP
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive"
            }
            
            # Add authentication if configured
            if self.config.auth_type == AuthType.BEARER and self.config.auth_token:
                headers["Authorization"] = f"Bearer {self.config.auth_token}"
            elif self.config.auth_type == AuthType.API_KEY and self.config.auth_token:
                headers["X-API-Key"] = self.config.auth_token
            
            # Send HTTP POST request with streaming support
            async with self.client.stream(
                "POST",
                self.config.server_url,
                json=request,
                headers=headers
            ) as response:
                response.raise_for_status()
                
                # Handle streaming response
                content = b""
                async for chunk in response.aiter_bytes():
                    content += chunk
                
                result = json.loads(content.decode('utf-8'))
                
                # Handle JSON-RPC response
                if "result" in result:
                    return result["result"]
                elif "error" in result:
                    error = result["error"]
                    raise Exception(f"Server error: {error.get('message', 'Unknown error')}")
                else:
                    return result
                
        except httpx.HTTPError as e:
            logger.error(f"Streamable HTTP request failed: {e}")
            raise ConnectionError(f"Streamable HTTP request failed: {e}")
        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise
    
    async def receive_event(self) -> Optional[Dict[str, Any]]:
        # For streamable HTTP, events are handled in the response stream
        return None
    
    def _generate_request_id(self) -> str:
        return str(uuid.uuid4())


class StdioTransport(MCPTransport):
    
    def __init__(self, config: MCPConfig):
        self.config = config
        self.process = None
        self.connected = False
    
    async def connect(self) -> bool:
        try:
            logger.info("Connecting to MCP server via stdio")
            # For stdio transport, we would need to start a subprocess
            # This is a placeholder implementation
            self.connected = True
            return True
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False
    
    async def disconnect(self) -> None:
        if self.process:
            self.process.terminate()
            await self.process.wait()
            self.process = None
        self.connected = False
        logger.info("Disconnected from MCP server")
    
    async def send_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if not self.connected:
            raise ConnectionError("Not connected to server")
        
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": self._generate_request_id()
        }
        
        logger.debug(f"Sending request: {method}")
        # For stdio transport, we would write to stdin and read from stdout
        # This is a placeholder implementation
        return {}
    
    async def receive_event(self) -> Optional[Dict[str, Any]]:
        return None
    
    def _generate_request_id(self) -> str:
        return str(uuid.uuid4())


class WebSocketTransport(MCPTransport):
    
    def __init__(self, config: MCPConfig):
        self.config = config
        self.websocket = None
        self.connected = False
    
    async def connect(self) -> bool:
        try:
            logger.info(f"Connecting to MCP server via WebSocket: {self.config.server_url}")
            # For WebSocket transport, we would need to establish a WebSocket connection
            # This is a placeholder implementation
            self.connected = True
            return True
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False
    
    async def disconnect(self) -> None:
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
        self.connected = False
        logger.info("Disconnected from MCP server")
    
    async def send_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if not self.connected:
            raise ConnectionError("Not connected to server")
        
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": self._generate_request_id()
        }
        
        logger.debug(f"Sending request: {method}")
        # For WebSocket transport, we would send JSON over the WebSocket
        # This is a placeholder implementation
        return {}
    
    async def receive_event(self) -> Optional[Dict[str, Any]]:
        return None
    
    def _generate_request_id(self) -> str:
        return str(uuid.uuid4())


class MCPClient:
    
    def __init__(self, config: MCPConfig):
        self.config = config
        self.transport: Optional[MCPTransport] = None
        self.tools: Dict[str, Tool] = {}
        self.resources: Dict[str, Resource] = {}
        self.prompts: Dict[str, Prompt] = {}
        self.server_info: Dict[str, Any] = {}
        self.capabilities: Dict[str, Any] = {}
        self.connected = False
        self.retry_count = 0
    
    async def connect(self) -> bool:
        try:
            self.transport = self._create_transport()
            
            if not await self.transport.connect():
                return False
            
            if not await self._handshake():
                return False
            
            await self._discover_capabilities()
            
            self.connected = True
            self.retry_count = 0
            logger.info("MCP client connected successfully")
            return True
            
        except Exception as e:
            logger.error(f"Connection error: {e}")
            await self._handle_reconnect()
            return False
    
    async def disconnect(self) -> None:
        if self.transport:
            await self.transport.disconnect()
        self.connected = False
        logger.info("MCP client disconnected")
    
    def _create_transport(self) -> MCPTransport:
        transport_map = {
            TransportType.HTTP_SSE: HTTPSSETransport,
            TransportType.HTTP_STREAM: StreamableHTTPTransport,
            TransportType.STDIO: StdioTransport,
            TransportType.WEBSOCKET: WebSocketTransport
        }
        
        transport_class = transport_map.get(self.config.transport_type)
        if not transport_class:
            raise ValueError(f"Unsupported transport type: {self.config.transport_type}")
        
        return transport_class(self.config)
    
    async def _handshake(self) -> bool:
        try:
            logger.info("Initiating handshake with MCP server")
            
            response = await self.transport.send_request("initialize", {
                "protocolVersion": "2024-11-05",
                "clientInfo": self.config.client_info,
                "capabilities": {
                    "experimental": {},
                    "sampling": {}
                }
            })
            
            self.server_info = response.get("serverInfo", {})
            self.capabilities = response.get("capabilities", {})
            
            logger.info(f"Handshake successful. Server: {self.server_info.get('name', 'unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"Handshake failed: {e}")
            return False
    
    async def _discover_capabilities(self) -> None:
        try:
            logger.info("Discovering server capabilities")
            
            if self.capabilities.get("tools"):
                await self._discover_tools()
            
            if self.capabilities.get("resources"):
                await self._discover_resources()
            
            if self.capabilities.get("prompts"):
                await self._discover_prompts()
            
            logger.info(f"Discovered {len(self.tools)} tools, {len(self.resources)} resources, {len(self.prompts)} prompts")
            
        except Exception as e:
            logger.error(f"Capability discovery error: {e}")
    
    async def _discover_tools(self) -> None:
        try:
            response = await self.transport.send_request("tools/list", {})
            tools_data = response.get("tools", [])
            
            for tool_data in tools_data:
                tool = Tool(
                    name=tool_data["name"],
                    description=tool_data.get("description", ""),
                    parameters=tool_data.get("inputSchema", {}),
                    metadata=tool_data.get("metadata")
                )
                self.tools[tool.name] = tool
            
            logger.info(f"Discovered {len(self.tools)} tools")
            
        except Exception as e:
            logger.error(f"Tool discovery error: {e}")
    
    async def _discover_resources(self) -> None:
        try:
            response = await self.transport.send_request("resources/list", {})
            resources_data = response.get("resources", [])
            
            for resource_data in resources_data:
                resource = Resource(
                    uri=resource_data["uri"],
                    name=resource_data["name"],
                    description=resource_data.get("description"),
                    mime_type=resource_data.get("mimeType"),
                    metadata=resource_data.get("metadata")
                )
                self.resources[resource.uri] = resource
            
            logger.info(f"Discovered {len(self.resources)} resources")
            
        except Exception as e:
            logger.error(f"Resource discovery error: {e}")
    
    async def _discover_prompts(self) -> None:
        try:
            response = await self.transport.send_request("prompts/list", {})
            prompts_data = response.get("prompts", [])
            
            for prompt_data in prompts_data:
                prompt = Prompt(
                    name=prompt_data["name"],
                    description=prompt_data.get("description", ""),
                    parameters=prompt_data.get("arguments")
                )
                self.prompts[prompt.name] = prompt
            
            logger.info(f"Discovered {len(self.prompts)} prompts")
            
        except Exception as e:
            logger.error(f"Prompt discovery error: {e}")
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if not self.connected:
            raise ConnectionError("Not connected to MCP server")
        
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found. Available tools: {list(self.tools.keys())}")
        
        try:
            logger.info(f"Calling tool: {tool_name}")
            
            response = await self.transport.send_request("tools/call", {
                "name": tool_name,
                "arguments": arguments
            })
            
            return response
            
        except Exception as e:
            logger.error(f"Tool call error: {e}")
            raise
    
    async def get_resource(self, uri: str) -> Dict[str, Any]:
        if not self.connected:
            raise ConnectionError("Not connected to MCP server")
        
        try:
            logger.info(f"Getting resource: {uri}")
            
            response = await self.transport.send_request("resources/read", {
                "uri": uri
            })
            
            return response
            
        except Exception as e:
            logger.error(f"Resource retrieval error: {e}")
            raise
    
    async def get_prompt(self, name: str, arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not self.connected:
            raise ConnectionError("Not connected to MCP server")
        
        if name not in self.prompts:
            raise ValueError(f"Prompt '{name}' not found. Available prompts: {list(self.prompts.keys())}")
        
        try:
            logger.info(f"Getting prompt: {name}")
            
            params = {"name": name}
            if arguments:
                params["arguments"] = arguments
            
            response = await self.transport.send_request("prompts/get", params)
            
            return response
            
        except Exception as e:
            logger.error(f"Prompt retrieval error: {e}")
            raise
    
    def list_tools(self) -> List[Tool]:
        return list(self.tools.values())
    
    def list_resources(self) -> List[Resource]:
        return list(self.resources.values())
    
    def list_prompts(self) -> List[Prompt]:
        return list(self.prompts.values())
    
    def get_tool_info(self, tool_name: str) -> Optional[Tool]:
        return self.tools.get(tool_name)
    
    def get_resource_info(self, uri: str) -> Optional[Resource]:
        return self.resources.get(uri)
    
    def get_prompt_info(self, name: str) -> Optional[Prompt]:
        return self.prompts.get(name)
    
    async def _handle_reconnect(self) -> None:
        if self.retry_count >= self.config.max_retries:
            logger.error(f"Max retries ({self.config.max_retries}) reached. Giving up.")
            return
        
        self.retry_count += 1
        logger.info(f"Attempting reconnection {self.retry_count}/{self.config.max_retries}")
        
        await asyncio.sleep(self.config.retry_delay * self.retry_count)
        
        await self.connect()
    
    def set_auth_token(self, token: str, auth_type: AuthType = AuthType.BEARER) -> None:
        self.config.auth_token = token
        self.config.auth_type = auth_type
        logger.info(f"Authentication token updated: {auth_type.value}")
    
    def get_server_info(self) -> Dict[str, Any]:
        return self.server_info
    
    def get_capabilities(self) -> Dict[str, Any]:
        return self.capabilities
    
    def is_connected(self) -> bool:
        return self.connected


async def create_mcp_client(
    server_url: Optional[str] = None,
    transport_type: TransportType = TransportType.HTTP_SSE,
    auth_token: Optional[str] = None,
    auth_type: AuthType = AuthType.NONE,
    **kwargs
) -> MCPClient:
    config = MCPConfig(
        server_url=server_url,
        transport_type=transport_type,
        auth_token=auth_token,
        auth_type=auth_type,
        **kwargs
    )
    
    client = MCPClient(config)
    await client.connect()
    
    return client
