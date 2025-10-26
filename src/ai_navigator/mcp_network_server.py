#!/usr/bin/env python3
"""
Network Requests MCP Server

This MCP server provides tools for network operations including:
- HTTP GET, POST, PUT, DELETE requests
- WebSocket connections
- File downloads
- Request headers and authentication support

Following the Model Context Protocol (MCP) specification.
"""

import asyncio
import json
import aiohttp
import websockets
from typing import Any, Optional
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

server = Server("network-operations")

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available network operation tools."""
    return [
        Tool(
            name="http_get",
            description="Send an HTTP GET request",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL to send the GET request to"
                    },
                    "headers": {
                        "type": "object",
                        "description": "Optional HTTP headers as key-value pairs",
                        "additionalProperties": {"type": "string"}
                    },
                    "params": {
                        "type": "object",
                        "description": "Optional query parameters as key-value pairs",
                        "additionalProperties": {"type": "string"}
                    },
                    "timeout": {
                        "type": "number",
                        "description": "Request timeout in seconds (default: 30)",
                        "default": 30
                    }
                },
                "required": ["url"]
            }
        ),
        Tool(
            name="http_post",
            description="Send an HTTP POST request",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL to send the POST request to"
                    },
                    "data": {
                        "type": ["object", "string"],
                        "description": "Data to send in the request body (JSON object or string)"
                    },
                    "headers": {
                        "type": "object",
                        "description": "Optional HTTP headers as key-value pairs",
                        "additionalProperties": {"type": "string"}
                    },
                    "json_data": {
                        "type": "boolean",
                        "description": "Whether to send data as JSON (default: true)",
                        "default": True
                    },
                    "timeout": {
                        "type": "number",
                        "description": "Request timeout in seconds (default: 30)",
                        "default": 30
                    }
                },
                "required": ["url"]
            }
        ),
        Tool(
            name="http_put",
            description="Send an HTTP PUT request",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL to send the PUT request to"
                    },
                    "data": {
                        "type": ["object", "string"],
                        "description": "Data to send in the request body (JSON object or string)"
                    },
                    "headers": {
                        "type": "object",
                        "description": "Optional HTTP headers as key-value pairs",
                        "additionalProperties": {"type": "string"}
                    },
                    "json_data": {
                        "type": "boolean",
                        "description": "Whether to send data as JSON (default: true)",
                        "default": True
                    },
                    "timeout": {
                        "type": "number",
                        "description": "Request timeout in seconds (default: 30)",
                        "default": 30
                    }
                },
                "required": ["url"]
            }
        ),
        Tool(
            name="http_delete",
            description="Send an HTTP DELETE request",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL to send the DELETE request to"
                    },
                    "headers": {
                        "type": "object",
                        "description": "Optional HTTP headers as key-value pairs",
                        "additionalProperties": {"type": "string"}
                    },
                    "timeout": {
                        "type": "number",
                        "description": "Request timeout in seconds (default: 30)",
                        "default": 30
                    }
                },
                "required": ["url"]
            }
        ),
        Tool(
            name="websocket_send",
            description="Send a message via WebSocket and receive response",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "WebSocket URL (ws:// or wss://)"
                    },
                    "message": {
                        "type": "string",
                        "description": "Message to send"
                    },
                    "wait_for_response": {
                        "type": "boolean",
                        "description": "Wait for a response message (default: true)",
                        "default": True
                    },
                    "timeout": {
                        "type": "number",
                        "description": "Connection timeout in seconds (default: 30)",
                        "default": 30
                    }
                },
                "required": ["url", "message"]
            }
        ),
        Tool(
            name="download_file",
            description="Download a file from a URL",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL of the file to download"
                    },
                    "destination": {
                        "type": "string",
                        "description": "Local path where the file should be saved"
                    },
                    "headers": {
                        "type": "object",
                        "description": "Optional HTTP headers as key-value pairs",
                        "additionalProperties": {"type": "string"}
                    },
                    "chunk_size": {
                        "type": "number",
                        "description": "Download chunk size in bytes (default: 8192)",
                        "default": 8192
                    },
                    "timeout": {
                        "type": "number",
                        "description": "Request timeout in seconds (default: 300)",
                        "default": 300
                    }
                },
                "required": ["url", "destination"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool execution requests."""
    
    try:
        if name == "http_get":
            url = arguments.get("url")
            headers = arguments.get("headers", {})
            params = arguments.get("params", {})
            timeout = arguments.get("timeout", 30)
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers=headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as response:
                    content_type = response.headers.get('Content-Type', '')
                    
                    if 'application/json' in content_type:
                        data = await response.json()
                    else:
                        data = await response.text()
                    
                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            "success": True,
                            "status": response.status,
                            "headers": dict(response.headers),
                            "data": data,
                            "url": str(response.url)
                        })
                    )]
        
        elif name == "http_post":
            url = arguments.get("url")
            data = arguments.get("data")
            headers = arguments.get("headers", {})
            json_data = arguments.get("json_data", True)
            timeout = arguments.get("timeout", 30)
            
            async with aiohttp.ClientSession() as session:
                kwargs = {
                    "headers": headers,
                    "timeout": aiohttp.ClientTimeout(total=timeout)
                }
                
                if json_data and isinstance(data, (dict, list)):
                    kwargs["json"] = data
                else:
                    kwargs["data"] = data
                
                async with session.post(url, **kwargs) as response:
                    content_type = response.headers.get('Content-Type', '')
                    
                    if 'application/json' in content_type:
                        response_data = await response.json()
                    else:
                        response_data = await response.text()
                    
                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            "success": True,
                            "status": response.status,
                            "headers": dict(response.headers),
                            "data": response_data,
                            "url": str(response.url)
                        })
                    )]
        
        elif name == "http_put":
            url = arguments.get("url")
            data = arguments.get("data")
            headers = arguments.get("headers", {})
            json_data = arguments.get("json_data", True)
            timeout = arguments.get("timeout", 30)
            
            async with aiohttp.ClientSession() as session:
                kwargs = {
                    "headers": headers,
                    "timeout": aiohttp.ClientTimeout(total=timeout)
                }
                
                if json_data and isinstance(data, (dict, list)):
                    kwargs["json"] = data
                else:
                    kwargs["data"] = data
                
                async with session.put(url, **kwargs) as response:
                    content_type = response.headers.get('Content-Type', '')
                    
                    if 'application/json' in content_type:
                        response_data = await response.json()
                    else:
                        response_data = await response.text()
                    
                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            "success": True,
                            "status": response.status,
                            "headers": dict(response.headers),
                            "data": response_data,
                            "url": str(response.url)
                        })
                    )]
        
        elif name == "http_delete":
            url = arguments.get("url")
            headers = arguments.get("headers", {})
            timeout = arguments.get("timeout", 30)
            
            async with aiohttp.ClientSession() as session:
                async with session.delete(
                    url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as response:
                    content_type = response.headers.get('Content-Type', '')
                    
                    if 'application/json' in content_type:
                        data = await response.json()
                    else:
                        data = await response.text()
                    
                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            "success": True,
                            "status": response.status,
                            "headers": dict(response.headers),
                            "data": data,
                            "url": str(response.url)
                        })
                    )]
        
        elif name == "websocket_send":
            url = arguments.get("url")
            message = arguments.get("message")
            wait_for_response = arguments.get("wait_for_response", True)
            timeout = arguments.get("timeout", 30)
            
            try:
                async with websockets.connect(url, open_timeout=timeout) as websocket:
                    await websocket.send(message)
                    
                    response_message = None
                    if wait_for_response:
                        try:
                            response_message = await asyncio.wait_for(
                                websocket.recv(),
                                timeout=timeout
                            )
                        except asyncio.TimeoutError:
                            response_message = None
                    
                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            "success": True,
                            "message_sent": message,
                            "response": response_message,
                            "url": url
                        })
                    )]
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "success": False,
                        "error": str(e),
                        "type": type(e).__name__
                    })
                )]
        
        elif name == "download_file":
            url = arguments.get("url")
            destination = arguments.get("destination")
            headers = arguments.get("headers", {})
            chunk_size = arguments.get("chunk_size", 8192)
            timeout = arguments.get("timeout", 300)
            
            import os
            os.makedirs(os.path.dirname(destination) or ".", exist_ok=True)
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as response:
                    if response.status != 200:
                        return [TextContent(
                            type="text",
                            text=json.dumps({
                                "success": False,
                                "error": f"HTTP {response.status}: Failed to download file",
                                "status": response.status
                            })
                        )]
                    
                    total_size = 0
                    with open(destination, 'wb') as f:
                        async for chunk in response.content.iter_chunked(chunk_size):
                            f.write(chunk)
                            total_size += len(chunk)
                    
                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            "success": True,
                            "message": f"Downloaded file to {destination}",
                            "url": url,
                            "destination": destination,
                            "size": total_size,
                            "content_type": response.headers.get('Content-Type', 'unknown')
                        })
                    )]
        
        else:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": f"Unknown tool: {name}"
                })
            )]
    
    except aiohttp.ClientError as e:
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": str(e),
                "type": "NetworkError"
            })
        )]
    
    except asyncio.TimeoutError:
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": "Request timeout",
                "type": "TimeoutError"
            })
        )]
    
    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": str(e),
                "type": type(e).__name__
            })
        )]

async def main():
    """Main entry point for the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="network-operations",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
