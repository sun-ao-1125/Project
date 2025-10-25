"""
Example usage of the generic MCP Client

This file demonstrates how to use the generic MCP client to interact
with various MCP servers.
"""

import asyncio
from mcp_client import (
    MCPClient,
    MCPConfig,
    TransportType,
    AuthType,
    create_mcp_client
)


async def example_basic_usage():
    config = MCPConfig(
        server_url="http://localhost:3000",
        transport_type=TransportType.HTTP_SSE
    )
    
    client = MCPClient(config)
    
    if await client.connect():
        print(f"Connected to: {client.get_server_info()}")
        
        tools = client.list_tools()
        print(f"\nAvailable tools ({len(tools)}):")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")
        
        resources = client.list_resources()
        print(f"\nAvailable resources ({len(resources)}):")
        for resource in resources:
            print(f"  - {resource.name} ({resource.uri})")
        
        prompts = client.list_prompts()
        print(f"\nAvailable prompts ({len(prompts)}):")
        for prompt in prompts:
            print(f"  - {prompt.name}: {prompt.description}")
        
        await client.disconnect()


async def example_tool_invocation():
    client = await create_mcp_client(
        server_url="http://localhost:3000",
        transport_type=TransportType.HTTP_SSE
    )
    
    try:
        result = await client.call_tool(
            tool_name="search",
            arguments={
                "query": "Python MCP examples",
                "limit": 10
            }
        )
        print(f"Tool result: {result}")
        
    except Exception as e:
        print(f"Error calling tool: {e}")
    
    finally:
        await client.disconnect()


async def example_resource_access():
    client = await create_mcp_client(
        server_url="http://localhost:3000",
        transport_type=TransportType.HTTP_SSE
    )
    
    try:
        resource = await client.get_resource("file:///path/to/resource")
        print(f"Resource content: {resource}")
        
    except Exception as e:
        print(f"Error accessing resource: {e}")
    
    finally:
        await client.disconnect()


async def example_with_authentication():
    config = MCPConfig(
        server_url="https://api.example.com/mcp",
        transport_type=TransportType.HTTP_SSE,
        auth_type=AuthType.BEARER,
        auth_token="your-api-key-here"
    )
    
    client = MCPClient(config)
    
    if await client.connect():
        tools = client.list_tools()
        print(f"Authenticated. Found {len(tools)} tools")
        
        await client.disconnect()


async def example_stdio_transport():
    config = MCPConfig(
        transport_type=TransportType.STDIO,
        timeout=60
    )
    
    client = MCPClient(config)
    
    if await client.connect():
        print("Connected via stdio transport")
        
        tools = client.list_tools()
        for tool in tools:
            print(f"Tool: {tool.name}")
        
        await client.disconnect()


async def example_websocket_transport():
    config = MCPConfig(
        server_url="ws://localhost:8080/mcp",
        transport_type=TransportType.WEBSOCKET,
        auth_type=AuthType.API_KEY,
        auth_token="your-api-key"
    )
    
    client = MCPClient(config)
    
    if await client.connect():
        print("Connected via WebSocket")
        
        capabilities = client.get_capabilities()
        print(f"Server capabilities: {capabilities}")
        
        await client.disconnect()


async def example_error_handling_and_retry():
    config = MCPConfig(
        server_url="http://localhost:3000",
        transport_type=TransportType.HTTP_SSE,
        max_retries=5,
        retry_delay=2.0
    )
    
    client = MCPClient(config)
    
    try:
        if await client.connect():
            result = await client.call_tool("analyze", {"text": "Sample text"})
            print(f"Analysis result: {result}")
    except Exception as e:
        print(f"Operation failed after retries: {e}")
    finally:
        await client.disconnect()


async def example_prompt_usage():
    client = await create_mcp_client(
        server_url="http://localhost:3000"
    )
    
    try:
        prompt = await client.get_prompt(
            name="code_review",
            arguments={
                "language": "python",
                "file_path": "example.py"
            }
        )
        print(f"Generated prompt: {prompt}")
        
    except Exception as e:
        print(f"Error getting prompt: {e}")
    
    finally:
        await client.disconnect()


async def main():
    print("=== MCP Client Examples ===\n")
    
    print("1. Basic Usage")
    await example_basic_usage()
    
    print("\n2. Tool Invocation")
    await example_tool_invocation()
    
    print("\n3. Resource Access")
    await example_resource_access()
    
    print("\n4. Authentication")
    await example_with_authentication()
    
    print("\n5. STDIO Transport")
    await example_stdio_transport()
    
    print("\n6. WebSocket Transport")
    await example_websocket_transport()
    
    print("\n7. Error Handling and Retry")
    await example_error_handling_and_retry()
    
    print("\n8. Prompt Usage")
    await example_prompt_usage()


if __name__ == "__main__":
    asyncio.run(main())
