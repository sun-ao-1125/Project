#!/usr/bin/env python3
"""
System MCP Manager - Unified Communication Abstraction and Security Control Layer

This module provides:
1. Communication Abstraction Layer - Decouples transport methods (stdio, HTTP, WebSocket, etc.)
2. Security Control Layer - Permission levels, validation, confirmation, and audit logging
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, List, Any, Callable
from dataclasses import dataclass, field
from mcp import StdioServerParameters
import sys

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


def _sanitize_sensitive_data(data: Any, keys_to_mask: List[str] = None) -> Any:
    """
    Recursively sanitize sensitive data from dictionaries for logging.
    
    Args:
        data: Data to sanitize (dict, list, or primitive)
        keys_to_mask: List of key names to mask (case-insensitive)
        
    Returns:
        Sanitized copy of the data
    """
    if keys_to_mask is None:
        keys_to_mask = [
            'api_key', 'apikey', 'key', 'token', 'password', 'secret',
            'authorization', 'auth', 'credential', 'access_token',
            'refresh_token', 'bearer', 'ak', 'sk'
        ]
    
    def should_mask(key: str) -> bool:
        key_lower = key.lower()
        return any(sensitive in key_lower for sensitive in keys_to_mask)
    
    def mask_value(value: Any) -> str:
        if isinstance(value, str):
            if len(value) <= 8:
                return '***'
            return f"{value[:4]}...{value[-4:]}"
        return '***'
    
    if isinstance(data, dict):
        sanitized = {}
        for key, value in data.items():
            if should_mask(key):
                sanitized[key] = mask_value(value)
            elif isinstance(value, (dict, list)):
                sanitized[key] = _sanitize_sensitive_data(value, keys_to_mask)
            else:
                sanitized[key] = value
        return sanitized
    elif isinstance(data, list):
        return [_sanitize_sensitive_data(item, keys_to_mask) for item in data]
    else:
        return data


class PermissionLevel(Enum):
    """Permission levels for MCP tools"""
    SAFE = "safe"
    NORMAL = "normal"
    DANGEROUS = "dangerous"
    CRITICAL = "critical"


class TransportMethod(Enum):
    """Transport methods for MCP communication"""
    STDIO = "stdio"
    HTTP = "http"
    WEBSOCKET = "websocket"
    REMOTE = "remote"


@dataclass
class ToolMetadata:
    """Metadata for an MCP tool including security information"""
    name: str
    server_name: str
    description: str
    permission_level: PermissionLevel
    requires_confirmation: bool = False
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AuditLogEntry:
    """Audit log entry for tracking tool calls"""
    timestamp: str
    server_name: str
    tool_name: str
    permission_level: str
    arguments: Dict[str, Any]
    result_status: str
    result_message: str
    user_confirmed: bool = False


class SecurityValidator:
    """Security validation and confirmation for tool calls"""
    
    def __init__(self, auto_confirm_safe: bool = True, enable_confirmation: bool = True):
        self.auto_confirm_safe = auto_confirm_safe
        self.enable_confirmation = enable_confirmation
        self.confirmed_operations: List[str] = []
    
    def validate_permission(self, tool_meta: ToolMetadata, arguments: Dict[str, Any]) -> tuple[bool, str]:
        """
        Validate if a tool call should be allowed based on permission level.
        
        Returns:
            (allowed, reason) - tuple of whether call is allowed and reason
        """
        if tool_meta.permission_level == PermissionLevel.SAFE:
            return True, "Safe operation"
        
        if tool_meta.permission_level == PermissionLevel.NORMAL:
            return True, "Normal operation"
        
        if tool_meta.permission_level == PermissionLevel.DANGEROUS:
            if tool_meta.requires_confirmation and self.enable_confirmation:
                return False, "Requires user confirmation (dangerous operation)"
            return True, "Dangerous operation (auto-allowed)"
        
        if tool_meta.permission_level == PermissionLevel.CRITICAL:
            return False, "Critical operation requires explicit confirmation"
        
        return False, "Unknown permission level"
    
    def request_confirmation(self, tool_meta: ToolMetadata, arguments: Dict[str, Any]) -> bool:
        """
        Request user confirmation for dangerous/critical operations.
        
        Returns:
            True if user confirms, False otherwise
        """
        if not self.enable_confirmation:
            return True
        
        operation_key = f"{tool_meta.server_name}.{tool_meta.name}"
        if operation_key in self.confirmed_operations:
            return True
        
        print(f"\n⚠️  WARNING: {tool_meta.permission_level.value.upper()} OPERATION")
        print(f"Server: {tool_meta.server_name}")
        print(f"Tool: {tool_meta.name}")
        print(f"Description: {tool_meta.description}")
        sanitized_args = _sanitize_sensitive_data(arguments)
        print(f"Arguments: {json.dumps(sanitized_args, indent=2, ensure_ascii=False)}")
        print(f"\nAllow this operation? (yes/no/always): ", end='')
        
        response = input().strip().lower()
        
        if response == "always":
            self.confirmed_operations.append(operation_key)
            return True
        
        return response in ["yes", "y"]


class AuditLogger:
    """Audit logger for tracking all MCP tool calls"""
    
    def __init__(self, log_file: str = "mcp_audit.log"):
        self.log_file = log_file
        self._ensure_log_file()
    
    def _ensure_log_file(self):
        """Ensure audit log file exists"""
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w') as f:
                f.write("# MCP Audit Log\n")
                f.write(f"# Created: {datetime.now().isoformat()}\n\n")
    
    def log_call(self, entry: AuditLogEntry):
        """Log a tool call to the audit log"""
        entry_dict = entry.__dict__.copy()
        entry_dict['arguments'] = _sanitize_sensitive_data(entry_dict.get('arguments', {}))
        
        with open(self.log_file, 'a') as f:
            f.write(f"{json.dumps(entry_dict, ensure_ascii=False)}\n")
        
        logger.info(f"Audit: {entry.server_name}.{entry.tool_name} - {entry.result_status}")
    
    def get_recent_logs(self, count: int = 10) -> List[AuditLogEntry]:
        """Get recent audit log entries"""
        entries = []
        
        if not os.path.exists(self.log_file):
            return entries
        
        with open(self.log_file, 'r') as f:
            lines = f.readlines()
        
        for line in reversed(lines):
            if line.startswith('#') or not line.strip():
                continue
            
            try:
                data = json.loads(line)
                entries.append(AuditLogEntry(**data))
                
                if len(entries) >= count:
                    break
            except json.JSONDecodeError:
                continue
        
        return entries


class MCPServerConnection:
    """Abstraction for MCP server connection with transport method decoupling"""
    
    def __init__(
        self,
        name: str,
        server_path: str,
        transport: TransportMethod = TransportMethod.STDIO,
        server_url: Optional[str] = None,
        **kwargs
    ):
        self.name = name
        self.server_path = server_path
        self.transport = transport
        self.server_url = server_url
        self.process = None
        self.request_id = 0
        self.connected = False
        self.tools_metadata: Dict[str, ToolMetadata] = {}
        self.kwargs = kwargs
    
    async def connect(self) -> bool:
        """Connect to MCP server using configured transport method"""
        try:
            if self.transport == TransportMethod.STDIO:
                return await self._connect_stdio()
            elif self.transport == TransportMethod.HTTP:
                return await self._connect_http()
            elif self.transport == TransportMethod.WEBSOCKET:
                return await self._connect_websocket()
            elif self.transport == TransportMethod.REMOTE:
                return await self._connect_remote()
            else:
                logger.error(f"Unsupported transport method: {self.transport}")
                return False
        except Exception as e:
            logger.error(f"Failed to connect to {self.name}: {e}")
            return False
    
    async def _connect_stdio(self) -> bool:
        """Connect via stdio transport (local process)"""
        try:
            # Support custom command from kwargs
            command = self.kwargs.get("command", sys.executable)
            logger.info(f"Using Python executable: {command}")
            
            # Create subprocess for MCP server
            self.process = await asyncio.create_subprocess_exec(
                command,
                self.server_path,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=os.environ.copy()
            )
            
            # Send JSON-RPC initialize request
            init_request = {
                "jsonrpc": "2.0",
                "id": self._get_next_id(),
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "SystemMCPManager",
                        "version": "1.0.0"
                    }
                }
            }
            
            await self._send_request(init_request)
            response = await self._receive_response()
            
            if not response or "result" not in response:
                raise RuntimeError(f"Invalid initialize response: {response}")
            
            self.connected = True
            logger.info(f"Connected to {self.name} via stdio")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect via stdio: {e}")
            await self._cleanup_stdio()
            return False
    
    async def _connect_http(self) -> bool:
        """Connect via HTTP transport (remote server)"""
        logger.warning(f"HTTP transport not yet implemented for {self.name}")
        return False
    
    async def _connect_websocket(self) -> bool:
        """Connect via WebSocket transport (remote server)"""
        logger.warning(f"WebSocket transport not yet implemented for {self.name}")
        return False
    
    async def _connect_remote(self) -> bool:
        """Connect to remote/containerized server"""
        logger.warning(f"Remote transport not yet implemented for {self.name}")
        return False
    
    def _get_next_id(self) -> int:
        """Get next request ID for JSON-RPC"""
        self.request_id += 1
        return self.request_id
    
    async def _send_request(self, request: Dict[str, Any]):
        """Send JSON-RPC request to MCP server"""
        if not self.process or not self.process.stdin:
            raise RuntimeError("Process not available")
        
        message = json.dumps(request) + "\n"
        self.process.stdin.write(message.encode())
        await self.process.stdin.drain()
        sanitized_request = _sanitize_sensitive_data(request)
        logger.debug(f"Sent request: {sanitized_request}")
    
    async def _receive_response(self) -> Optional[Dict[str, Any]]:
        """Receive JSON-RPC response from MCP server"""
        if not self.process or not self.process.stdout:
            raise RuntimeError("Process not available")
        
        try:
            line = await self.process.stdout.readline()
            if line:
                response = json.loads(line.decode().strip())
                sanitized_response = _sanitize_sensitive_data(response)
                logger.debug(f"Received response: {sanitized_response}")
                return response
            else:
                logger.warning("Received empty response")
                return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON response: {e}")
            return None
        except Exception as e:
            logger.error(f"Error receiving response: {e}")
            return None
    
    async def _cleanup_stdio(self):
        """Clean up stdio connection resources"""
        try:
            if self.process:
                self.process.terminate()
                await self.process.wait()
        except Exception as e:
            logger.error(f"Error terminating process: {e}")
        finally:
            self.process = None
            self.connected = False
    
    async def disconnect(self):
        """Disconnect from MCP server"""
        await self._cleanup_stdio()
        logger.info(f"Disconnected from {self.name}")
    
    async def discover_tools(self) -> List[ToolMetadata]:
        """Discover available tools from the server"""
        if not self.connected:
            raise RuntimeError(f"Not connected to {self.name}")
        
        try:
            # Send tools/list request
            request = {
                "jsonrpc": "2.0",
                "id": self._get_next_id(),
                "method": "tools/list",
                "params": {}
            }
            
            await self._send_request(request)
            response = await self._receive_response()
            
            if not response or "result" not in response:
                logger.error(f"Invalid tools/list response: {response}")
                return []
            
            tools = response["result"].get("tools", [])
            
            for tool in tools:
                tool_name = tool.get("name", "")
                permission_level = self._infer_permission_level(tool_name)
                requires_confirmation = permission_level in [
                    PermissionLevel.DANGEROUS,
                    PermissionLevel.CRITICAL
                ]
                
                tool_meta = ToolMetadata(
                    name=tool_name,
                    server_name=self.name,
                    description=tool.get("description", ""),
                    permission_level=permission_level,
                    requires_confirmation=requires_confirmation,
                    parameters=tool.get("inputSchema", {})
                )
                
                self.tools_metadata[tool_name] = tool_meta
            
            logger.info(f"Discovered {len(self.tools_metadata)} tools from {self.name}")
            return list(self.tools_metadata.values())
        
        except Exception as e:
            logger.error(f"Failed to discover tools from {self.name}: {e}")
            return []
    
    def _infer_permission_level(self, tool_name: str) -> PermissionLevel:
        """Infer permission level based on tool name"""
        dangerous_keywords = ["delete", "remove", "close", "kill", "terminate"]
        critical_keywords = ["format", "wipe", "destroy", "shutdown", "reboot"]
        safe_keywords = ["get", "read", "list", "search", "find", "open_url", "open_map"]
        
        tool_lower = tool_name.lower()
        
        for keyword in critical_keywords:
            if keyword in tool_lower:
                return PermissionLevel.CRITICAL
        
        for keyword in dangerous_keywords:
            if keyword in tool_lower:
                return PermissionLevel.DANGEROUS
        
        for keyword in safe_keywords:
            if keyword in tool_lower:
                return PermissionLevel.SAFE
        
        return PermissionLevel.NORMAL
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool on this server"""
        if not self.connected:
            raise RuntimeError(f"Not connected to {self.name}")
        
        if tool_name not in self.tools_metadata:
            raise ValueError(f"Tool '{tool_name}' not found in {self.name}")
        
        try:
            # Send tools/call request
            request = {
                "jsonrpc": "2.0",
                "id": self._get_next_id(),
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            
            await self._send_request(request)
            response = await self._receive_response()
            
            if not response:
                raise RuntimeError(f"No response received for tool call: {tool_name}")
            
            if "error" in response:
                error = response["error"]
                raise RuntimeError(f"Tool call error: {error.get('message', str(error))}")
            
            if "result" not in response:
                raise RuntimeError(f"Invalid response format: {response}")
            
            return response["result"]
            
        except Exception as e:
            logger.error(f"Failed to call tool {tool_name}: {e}")
            raise


class SystemMCPManager:
    """
    Unified MCP Client Manager with Communication Abstraction and Security Control
    
    Features:
    - Communication abstraction: Supports stdio, HTTP, WebSocket, remote transports
    - Security control: Permission levels, validation, confirmation, audit logging
    - Tool discovery: Automatic tool registration and capability discovery
    - Unified interface: Call any tool from any server through a single interface
    """
    
    def __init__(
        self,
        enable_security: bool = True,
        enable_confirmation: bool = True,
        audit_log_file: str = "mcp_audit.log"
    ):
        self.servers: Dict[str, MCPServerConnection] = {}
        self.enable_security = enable_security
        self.security_validator = SecurityValidator(enable_confirmation=enable_confirmation)
        self.audit_logger = AuditLogger(log_file=audit_log_file)
    
    async def register_server(
        self,
        name: str,
        server_path: str,
        transport: TransportMethod = TransportMethod.STDIO,
        server_url: Optional[str] = None,
        auto_connect: bool = True,
        **kwargs
    ) -> bool:
        """
        Register and connect to an MCP server
        
        Args:
            name: Unique name for this server
            server_path: Path to server executable/script
            transport: Transport method (stdio, http, websocket, remote)
            server_url: URL for remote servers
            auto_connect: Whether to connect immediately
            **kwargs: Additional server-specific configuration
            
        Returns:
            True if registration and connection successful
        """
        if name in self.servers:
            logger.warning(f"Server '{name}' already registered")
            return False
        
        connection = MCPServerConnection(
            name=name,
            server_path=server_path,
            transport=transport,
            server_url=server_url,
            **kwargs
        )
        
        if auto_connect:
            if not await connection.connect():
                logger.error(f"Failed to connect to server '{name}'")
                return False
            
            await connection.discover_tools()
        
        self.servers[name] = connection
        logger.info(f"Registered server '{name}' with transport {transport.value}")
        return True
    
    async def unregister_server(self, name: str):
        """Unregister and disconnect from a server"""
        if name not in self.servers:
            logger.warning(f"Server '{name}' not registered")
            return
        
        await self.servers[name].disconnect()
        del self.servers[name]
        logger.info(f"Unregistered server '{name}'")
    
    async def call_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: Dict[str, Any],
        skip_confirmation: bool = False
    ) -> Any:
        """
        Call a tool through the unified interface with security controls
        
        Args:
            server_name: Name of the registered server
            tool_name: Name of the tool to call
            arguments: Tool arguments
            skip_confirmation: Skip user confirmation (for automated workflows)
            
        Returns:
            Tool result
            
        Raises:
            ValueError: If server or tool not found
            PermissionError: If security validation fails
        """
        if server_name not in self.servers:
            raise ValueError(f"Server '{server_name}' not registered")
        
        server = self.servers[server_name]
        
        if tool_name not in server.tools_metadata:
            raise ValueError(f"Tool '{tool_name}' not found in server '{server_name}'")
        
        tool_meta = server.tools_metadata[tool_name]
        
        audit_entry = AuditLogEntry(
            timestamp=datetime.now().isoformat(),
            server_name=server_name,
            tool_name=tool_name,
            permission_level=tool_meta.permission_level.value,
            arguments=arguments,
            result_status="pending",
            result_message="",
            user_confirmed=False
        )
        
        if self.enable_security:
            allowed, reason = self.security_validator.validate_permission(tool_meta, arguments)
            
            if not allowed:
                if not skip_confirmation and tool_meta.requires_confirmation:
                    confirmed = self.security_validator.request_confirmation(tool_meta, arguments)
                    audit_entry.user_confirmed = confirmed
                    
                    if not confirmed:
                        audit_entry.result_status = "denied"
                        audit_entry.result_message = "User denied confirmation"
                        self.audit_logger.log_call(audit_entry)
                        raise PermissionError(f"Operation denied: {reason}")
                else:
                    audit_entry.result_status = "denied"
                    audit_entry.result_message = reason
                    self.audit_logger.log_call(audit_entry)
                    raise PermissionError(f"Operation not allowed: {reason}")
        
        try:
            result = await server.call_tool(tool_name, arguments)
            
            audit_entry.result_status = "success"
            audit_entry.result_message = "Tool call completed"
            self.audit_logger.log_call(audit_entry)
            
            return result
        
        except Exception as e:
            audit_entry.result_status = "error"
            audit_entry.result_message = str(e)
            self.audit_logger.log_call(audit_entry)
            raise
    
    def list_all_tools(self) -> Dict[str, List[ToolMetadata]]:
        """List all available tools from all registered servers"""
        all_tools = {}
        
        for server_name, server in self.servers.items():
            all_tools[server_name] = list(server.tools_metadata.values())
        
        return all_tools
    
    def get_server_capabilities(self, server_name: str) -> List[ToolMetadata]:
        """Get capabilities (tools) of a specific server"""
        if server_name not in self.servers:
            raise ValueError(f"Server '{server_name}' not registered")
        
        return list(self.servers[server_name].tools_metadata.values())
    
    def get_audit_logs(self, count: int = 10) -> List[AuditLogEntry]:
        """Get recent audit log entries"""
        return self.audit_logger.get_recent_logs(count)
    
    async def disconnect_all(self):
        """Disconnect from all registered servers"""
        for server_name in list(self.servers.keys()):
            await self.unregister_server(server_name)
        
        logger.info("Disconnected from all servers")
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect_all()
