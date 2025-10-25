#!/usr/bin/env python3
"""
AI Map Navigator - Main Application
Coordinates between AI, MCP server, and browser control MCP server.
"""

import asyncio
import os
import json
from ai_provider import create_ai_provider
from mcp_client import create_mcp_client, TransportType, AuthType
from amap_mcp_client import create_amap_client
# 导入新的语音识别模块
from voice_recognizer import get_voice_input

async def get_location_coordinates(location_name: str, mcp_client) -> dict:
    """
    Get coordinates for a location using MCP server.
    
    Args:
        location_name: Name of the location to geocode
        mcp_client: MCP client instance
        
    Returns:
        Dictionary with location coordinates
    """
    try:
        # Try different geocoding tools based on what's available
        tools = mcp_client.list_tools()
        tool_names = [tool.name for tool in tools]
        
        # Try maps_geo first (Amap specific)
        if "maps_geo" in tool_names:
            result = await mcp_client.call_tool("maps_geo", {"address": location_name})
        # Try maps_text_search as fallback
        elif "maps_text_search" in tool_names:
            result = await mcp_client.call_tool("maps_text_search", {"keywords": location_name})
        # Try standard geocode
        elif "geocode" in tool_names:
            result = await mcp_client.call_tool("geocode", {"address": location_name})
        else:
            raise ValueError(f"No geocoding tool available. Available tools: {tool_names}")
        
        # Parse the result based on the actual MCP response format
        if result and "content" in result:
            content = result["content"]
            if isinstance(content, list) and len(content) > 0:
                # Extract text content and parse JSON
                text_content = content[0].get("text", "")
                if text_content:
                    data = json.loads(text_content)
                    
                    # Handle maps_geo response format
                    if "results" in data and len(data["results"]) > 0:
                        result_item = data["results"][0]
                        location_str = result_item.get("location", "")
                        if location_str:
                            lng, lat = location_str.split(",")
                            return {
                                "name": location_name,
                                "longitude": float(lng),
                                "latitude": float(lat),
                                "formatted_address": f"{result_item.get('province', '')}{result_item.get('city', '')}"
                            }
                    
                    # Handle maps_text_search response format
                    elif "pois" in data and len(data["pois"]) > 0:
                        poi = data["pois"][0]
                        location_str = poi.get("location", "")
                        if location_str:
                            lng, lat = location_str.split(",")
                            return {
                                "name": location_name,
                                "longitude": float(lng),
                                "latitude": float(lat),
                                "formatted_address": poi.get("address", location_name)
                            }
                    
                    # Handle standard geocode format
                    elif data.get("status") == "success" and data.get("location"):
                        loc = data["location"]
                        return {
                            "name": location_name,
                            "longitude": loc["longitude"],
                            "latitude": loc["latitude"],
                            "formatted_address": data.get("formatted_address", location_name)
                        }
        
        raise ValueError(f"Failed to geocode location '{location_name}': Invalid response format")
    except Exception as e:
        raise ValueError(f"Failed to geocode location '{location_name}': {str(e)}")

async def parse_navigation_request(user_input: str, ai_provider) -> dict:
    """
    Use AI to parse user's navigation request and extract locations.
    """
    return await ai_provider.parse_navigation_request(user_input)

async def open_browser_navigation(start_coords: dict, end_coords: dict):
    """
    Use browser control MCP server to open navigation.
    For now, we directly open the browser.
    """
    import webbrowser
    
    url = (
        f"https://uri.amap.com/navigation?"
        f"from={start_coords['longitude']},{start_coords['latitude']}&"
        f"to={end_coords['longitude']},{end_coords['latitude']}&"
        f"mode=car&policy=1&src=ai-navigator&coordinate=gaode&callnative=0"
    )
    
    webbrowser.open(url)
    
    return {
        "success": True,
        "message": f"Navigation opened from {start_coords['name']} to {end_coords['name']}",
        "url": url
    }

async def main():
    """Main application flow."""
    print("=== AI Map Navigator (MCP Architecture) ===\n")
    
    try:
        ai_provider = create_ai_provider()
        provider_type = os.getenv("AI_PROVIDER", "anthropic")
        print(f"Using AI provider: {provider_type}")
    except ValueError as e:
        print(f"Error: {e}")
        print("\nConfiguration guide:")
        print("- For Anthropic Claude:")
        print("  export AI_PROVIDER='anthropic'")
        print("  export ANTHROPIC_API_KEY='your-api-key'")
        print("- For OpenAI-compatible APIs (e.g., Qiniu):")
        print("  export AI_PROVIDER='openai'")
        print("  export OPENAI_API_KEY='your-api-key'")
        print("  export OPENAI_BASE_URL='https://api.example.com/v1'")
        print("  export OPENAI_MODEL='gpt-3.5-turbo'  # optional")
        print("- For MCP Server:")
        print("  # SSE endpoint (Server-Sent Events):")
        print("  export AMAP_MCP_SERVER_URL='https://mcp.amap.com/sse?key=your-amap-api-key'")
        print("  # Streamable HTTP endpoint:")
        print("  export AMAP_MCP_SERVER_URL='https://mcp.amap.com/stream?key=your-amap-api-key'")
        print("  # 或者自定义MCP服务器:")
        print("  export AMAP_MCP_SERVER_URL='http://localhost:3000'")
        return
    
    # 添加语音输入选项
    print("请选择输入方式:")
    print("1. 文本输入")
    print("2. 语音输入")
    input_type = input("请选择 (1/2): ").strip()
    
    user_input = None
    
    if input_type == "2":
        # 使用语音输入
        user_input = await get_voice_input()
    else:
        # 默认使用文本输入
        print("Enter your navigation request (e.g., '从北京到上海', '我要从广州去深圳'):")
        user_input = input("> ").strip()
    
    if not user_input:
        print("No input provided.")
        return
    
    print(f"\n[1/5] Connecting to geocoding service...")
    
    # Try generic MCP client first
    mcp_client = None
    amap_client = None
    use_mcp = True
    
    try:
        # Configure MCP client using user-provided URL
        server_url = os.getenv("AMAP_MCP_SERVER_URL")
        if not server_url:
            print("⚠️  AMAP_MCP_SERVER_URL not set, falling back to Amap MCP client...")
            use_mcp = False
        else:
            print(f"   Using MCP server: {server_url}")
            # Auto-detect transport type based on URL
            if "sse" in server_url.lower():
                transport_type = TransportType.HTTP_SSE
            elif "stream" in server_url.lower():
                transport_type = TransportType.HTTP_STREAM
            else:
                transport_type = TransportType.HTTP_SSE  # Default
            auth_type = AuthType.NONE
        
            mcp_client = await create_mcp_client(
                server_url=server_url,
                transport_type=transport_type,
                auth_token=None,
                auth_type=auth_type
            )
            
            if not mcp_client.is_connected():
                raise ConnectionError("MCP client not connected")
            
        # Check if geocoding tool is available (maps_geo for Amap)
        tools = mcp_client.list_tools()
        tool_names = [tool.name for tool in tools]
        geocoding_tools = ["geocode", "maps_geo", "maps_text_search"]
        available_geocoding_tools = [tool for tool in geocoding_tools if tool in tool_names]
        
        if not available_geocoding_tools:
            print(f"⚠️  MCP server connected but no geocoding tool found. Available tools: {tool_names}")
            print("   Falling back to Amap MCP client...")
            use_mcp = False
        else:
            print(f"✓ Connected to MCP server with geocoding tools: {available_geocoding_tools}")
    
    except Exception as e:
        print(f"⚠️  Failed to connect to MCP server: {e}")
        print("   Falling back to Amap MCP client...")
        use_mcp = False
    
    # Fallback to Amap MCP client if MCP server is not available
    if not use_mcp:
        amap_client = create_amap_client()
        print("✓ Using Amap MCP client (fallback mode)")
    
    try:
        print(f"\n[2/5] Parsing request with AI...")
        try:
            locations = await parse_navigation_request(user_input, ai_provider)
            print(f"✓ Parsed: {locations['start']} → {locations['end']}")
        except Exception as e:
            print(f"✗ Failed to parse request: {e}")
            return
        
        print(f"\n[3/5] Getting coordinates for start location...")
        try:
            if use_mcp and mcp_client:
                start_coords = await get_location_coordinates(locations['start'], mcp_client)
            else:
                async with amap_client:
                    start_coords = await amap_client.geocode(locations['start'])
            print(f"✓ Start: {start_coords['name']} ({start_coords['longitude']}, {start_coords['latitude']})")
        except Exception as e:
            print(f"✗ Failed to get start coordinates: {e}")
            return
        
        print(f"\n[4/5] Getting coordinates for end location...")
        try:
            if use_mcp and mcp_client:
                end_coords = await get_location_coordinates(locations['end'], mcp_client)
            else:
                async with amap_client:
                    end_coords = await amap_client.geocode(locations['end'])
            print(f"✓ End: {end_coords['name']} ({end_coords['longitude']}, {end_coords['latitude']})")
        except Exception as e:
            print(f"✗ Failed to get end coordinates: {e}")
            return
        
        print(f"\n[5/5] Opening navigation in browser...")
        try:
            result = await open_browser_navigation(start_coords, end_coords)
            print(f"✓ {result['message']}")
            print(f"\nNavigation URL: {result['url']}")
        except Exception as e:
            print(f"✗ Failed to open navigation: {e}")
            return
        
        print("\n=== Navigation request completed successfully! ===")
    
    finally:
        # Ensure proper cleanup
        if mcp_client:
            await mcp_client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())