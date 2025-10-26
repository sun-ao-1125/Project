#!/usr/bin/env python3
"""
File Operations MCP Server

This MCP server provides tools for file system operations including:
- Reading files
- Writing files
- Listing directories
- Creating directories
- Deleting files
- Moving files
- Copying files

Following the Model Context Protocol (MCP) specification.
"""

import asyncio
import json
import os
import shutil
from pathlib import Path
from typing import Any
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

server = Server("file-operations")

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available file operation tools."""
    return [
        Tool(
            name="read_file",
            description="Read contents of a file",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file to read"
                    },
                    "encoding": {
                        "type": "string",
                        "description": "File encoding (default: utf-8)",
                        "default": "utf-8"
                    }
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="write_file",
            description="Write content to a file (creates file if it doesn't exist)",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file to write"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write to the file"
                    },
                    "encoding": {
                        "type": "string",
                        "description": "File encoding (default: utf-8)",
                        "default": "utf-8"
                    },
                    "append": {
                        "type": "boolean",
                        "description": "Append to file instead of overwriting (default: false)",
                        "default": False
                    }
                },
                "required": ["path", "content"]
            }
        ),
        Tool(
            name="list_directory",
            description="List contents of a directory",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the directory to list"
                    },
                    "recursive": {
                        "type": "boolean",
                        "description": "List directories recursively (default: false)",
                        "default": False
                    },
                    "include_hidden": {
                        "type": "boolean",
                        "description": "Include hidden files (default: false)",
                        "default": False
                    }
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="create_directory",
            description="Create a new directory",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the directory to create"
                    },
                    "parents": {
                        "type": "boolean",
                        "description": "Create parent directories if they don't exist (default: true)",
                        "default": True
                    }
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="delete_file",
            description="Delete a file or directory",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file or directory to delete"
                    },
                    "recursive": {
                        "type": "boolean",
                        "description": "Delete directories recursively (default: false)",
                        "default": False
                    }
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="move_file",
            description="Move or rename a file or directory",
            inputSchema={
                "type": "object",
                "properties": {
                    "source": {
                        "type": "string",
                        "description": "Source path"
                    },
                    "destination": {
                        "type": "string",
                        "description": "Destination path"
                    }
                },
                "required": ["source", "destination"]
            }
        ),
        Tool(
            name="copy_file",
            description="Copy a file or directory",
            inputSchema={
                "type": "object",
                "properties": {
                    "source": {
                        "type": "string",
                        "description": "Source path"
                    },
                    "destination": {
                        "type": "string",
                        "description": "Destination path"
                    },
                    "recursive": {
                        "type": "boolean",
                        "description": "Copy directories recursively (default: true)",
                        "default": True
                    }
                },
                "required": ["source", "destination"]
            }
        ),
        Tool(
            name="file_info",
            description="Get information about a file or directory",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file or directory"
                    }
                },
                "required": ["path"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool execution requests."""
    
    try:
        if name == "read_file":
            path = arguments.get("path")
            encoding = arguments.get("encoding", "utf-8")
            
            if not os.path.exists(path):
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "success": False,
                        "error": f"File not found: {path}"
                    })
                )]
            
            if not os.path.isfile(path):
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "success": False,
                        "error": f"Not a file: {path}"
                    })
                )]
            
            with open(path, 'r', encoding=encoding) as f:
                content = f.read()
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "content": content,
                    "path": path,
                    "size": len(content)
                })
            )]
        
        elif name == "write_file":
            path = arguments.get("path")
            content = arguments.get("content")
            encoding = arguments.get("encoding", "utf-8")
            append = arguments.get("append", False)
            
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            
            mode = 'a' if append else 'w'
            with open(path, mode, encoding=encoding) as f:
                f.write(content)
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "message": f"{'Appended to' if append else 'Wrote'} file: {path}",
                    "path": path,
                    "size": len(content)
                })
            )]
        
        elif name == "list_directory":
            path = arguments.get("path")
            recursive = arguments.get("recursive", False)
            include_hidden = arguments.get("include_hidden", False)
            
            if not os.path.exists(path):
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "success": False,
                        "error": f"Directory not found: {path}"
                    })
                )]
            
            if not os.path.isdir(path):
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "success": False,
                        "error": f"Not a directory: {path}"
                    })
                )]
            
            entries = []
            
            if recursive:
                for root, dirs, files in os.walk(path):
                    if not include_hidden:
                        dirs[:] = [d for d in dirs if not d.startswith('.')]
                        files = [f for f in files if not f.startswith('.')]
                    
                    for name in dirs:
                        full_path = os.path.join(root, name)
                        entries.append({
                            "name": name,
                            "path": full_path,
                            "type": "directory",
                            "size": 0
                        })
                    
                    for name in files:
                        full_path = os.path.join(root, name)
                        try:
                            size = os.path.getsize(full_path)
                        except:
                            size = 0
                        entries.append({
                            "name": name,
                            "path": full_path,
                            "type": "file",
                            "size": size
                        })
            else:
                for entry in os.listdir(path):
                    if not include_hidden and entry.startswith('.'):
                        continue
                    
                    full_path = os.path.join(path, entry)
                    is_dir = os.path.isdir(full_path)
                    try:
                        size = 0 if is_dir else os.path.getsize(full_path)
                    except:
                        size = 0
                    
                    entries.append({
                        "name": entry,
                        "path": full_path,
                        "type": "directory" if is_dir else "file",
                        "size": size
                    })
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "entries": entries,
                    "count": len(entries),
                    "path": path
                })
            )]
        
        elif name == "create_directory":
            path = arguments.get("path")
            parents = arguments.get("parents", True)
            
            if parents:
                os.makedirs(path, exist_ok=True)
            else:
                os.mkdir(path)
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "message": f"Created directory: {path}",
                    "path": path
                })
            )]
        
        elif name == "delete_file":
            path = arguments.get("path")
            recursive = arguments.get("recursive", False)
            
            if not os.path.exists(path):
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "success": False,
                        "error": f"Path not found: {path}"
                    })
                )]
            
            if os.path.isdir(path):
                if recursive:
                    shutil.rmtree(path)
                else:
                    os.rmdir(path)
            else:
                os.remove(path)
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "message": f"Deleted: {path}",
                    "path": path
                })
            )]
        
        elif name == "move_file":
            source = arguments.get("source")
            destination = arguments.get("destination")
            
            if not os.path.exists(source):
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "success": False,
                        "error": f"Source not found: {source}"
                    })
                )]
            
            shutil.move(source, destination)
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "message": f"Moved from {source} to {destination}",
                    "source": source,
                    "destination": destination
                })
            )]
        
        elif name == "copy_file":
            source = arguments.get("source")
            destination = arguments.get("destination")
            recursive = arguments.get("recursive", True)
            
            if not os.path.exists(source):
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "success": False,
                        "error": f"Source not found: {source}"
                    })
                )]
            
            if os.path.isdir(source):
                if recursive:
                    shutil.copytree(source, destination)
                else:
                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            "success": False,
                            "error": "Source is a directory. Set recursive=true to copy directories."
                        })
                    )]
            else:
                os.makedirs(os.path.dirname(destination) or ".", exist_ok=True)
                shutil.copy2(source, destination)
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "message": f"Copied from {source} to {destination}",
                    "source": source,
                    "destination": destination
                })
            )]
        
        elif name == "file_info":
            path = arguments.get("path")
            
            if not os.path.exists(path):
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "success": False,
                        "error": f"Path not found: {path}"
                    })
                )]
            
            stat_info = os.stat(path)
            is_dir = os.path.isdir(path)
            
            info = {
                "success": True,
                "path": path,
                "name": os.path.basename(path),
                "type": "directory" if is_dir else "file",
                "size": 0 if is_dir else stat_info.st_size,
                "created": stat_info.st_ctime,
                "modified": stat_info.st_mtime,
                "accessed": stat_info.st_atime,
                "permissions": oct(stat_info.st_mode)[-3:],
                "is_readable": os.access(path, os.R_OK),
                "is_writable": os.access(path, os.W_OK),
                "is_executable": os.access(path, os.X_OK)
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(info)
            )]
        
        else:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": f"Unknown tool: {name}"
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
                server_name="file-operations",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
