#!/usr/bin/env python3
"""
Browser Control MCP Server
This MCP server provides tools to control browser operations.
"""

import asyncio
import json
import webbrowser
from typing import Any
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

server = Server("browser-control")

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available browser control tools."""
    return [
        Tool(
            name="open_url",
            description="Open a URL in the default web browser",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to open in the browser"
                    }
                },
                "required": ["url"]
            }
        ),
        Tool(
            name="open_map_navigation",
            description="Open map navigation in browser with start and end coordinates",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_lng": {
                        "type": "number",
                        "description": "Start point longitude"
                    },
                    "start_lat": {
                        "type": "number",
                        "description": "Start point latitude"
                    },
                    "end_lng": {
                        "type": "number",
                        "description": "End point longitude"
                    },
                    "end_lat": {
                        "type": "number",
                        "description": "End point latitude"
                    },
                    "start_name": {
                        "type": "string",
                        "description": "Start point name (optional)"
                    },
                    "end_name": {
                        "type": "string",
                        "description": "End point name (optional)"
                    }
                },
                "required": ["start_lng", "start_lat", "end_lng", "end_lat"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool execution requests."""
    
    if name == "open_url":
        url = arguments.get("url")
        if not url:
            return [TextContent(
                type="text",
                text=json.dumps({"error": "URL is required"})
            )]
        
        try:
            webbrowser.open(url)
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "message": f"Opened URL: {url}"
                })
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": str(e)
                })
            )]
    
    elif name == "open_map_navigation":
        start_lng = arguments.get("start_lng")
        start_lat = arguments.get("start_lat")
        end_lng = arguments.get("end_lng")
        end_lat = arguments.get("end_lat")
        start_name = arguments.get("start_name", "起点")
        end_name = arguments.get("end_name", "终点")
        
        try:
            url = f"https://uri.amap.com/navigation?from={start_lng},{start_lat}&to={end_lng},{end_lat}&mode=car&policy=1&src=myapp&coordinate=gaode&callnative=0"
            
            webbrowser.open(url)
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "message": f"Opened navigation from {start_name} to {end_name}",
                    "url": url
                })
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": str(e)
                })
            )]
    
    else:
        return [TextContent(
            type="text",
            text=json.dumps({"error": f"Unknown tool: {name}"})
        )]

async def main():
    """Main entry point for the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="browser-control",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
