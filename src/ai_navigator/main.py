#!/usr/bin/env python3
"""
AI Map Navigator - Main Application
Coordinates between AI, MCP server, and browser control MCP server.
"""

import asyncio
import os
import json
from typing import Optional, Dict, Any
from ai_navigator.ai_provider import create_ai_provider
from ai_navigator.mcp_client import create_mcp_client, TransportType, AuthType
from ai_navigator.amap_mcp_client import create_amap_client
from ai_navigator.voice_recognizer import get_voice_input


async def get_location_coordinates(location_name: str, mcp_client) -> Dict[str, Any]:
    """
    Get coordinates for a location using MCP server.
    
    Args:
        location_name: Name of the location to geocode
        mcp_client: MCP client instance
        
    Returns:
        Dictionary with location coordinates
    """
    try:
        tools = mcp_client.list_tools()
        tool_names = [tool.name for tool in tools]
        
        if "maps_geo" in tool_names:
            result = await mcp_client.call_tool("maps_geo", {"address": location_name})
        elif "maps_text_search" in tool_names:
            result = await mcp_client.call_tool("maps_text_search", {"keywords": location_name})
        elif "geocode" in tool_names:
            result = await mcp_client.call_tool("geocode", {"address": location_name})
        else:
            raise ValueError(f"No geocoding tool available. Available tools: {tool_names}")
        
        if result and "content" in result:
            content = result["content"]
            if isinstance(content, list) and len(content) > 0:
                text_content = content[0].get("text", "")
                if text_content:
                    data = json.loads(text_content)
                    
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


async def parse_coordinates_from_gps_response(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Parse coordinates from GPS response data.
    
    Args:
        data: GPS response data
        
    Returns:
        Dictionary with coordinates or None if parsing fails
    """
    if not isinstance(data, dict):
        return None
    
    if "results" in data and isinstance(data["results"], list) and len(data["results"]) > 0:
        first_result = data["results"][0]
        if "location" in first_result:
            location = first_result["location"]
            if isinstance(location, str) and "," in location:
                lng_lat = location.split(",")
                if len(lng_lat) == 2:
                    try:
                        return {
                            "longitude": float(lng_lat[0]),
                            "latitude": float(lng_lat[1]),
                            "name": f"{first_result.get('province', '')}{first_result.get('city', '')}{first_result.get('district', '')}".strip() or "当前GPS位置"
                        }
                    except ValueError:
                        pass
    
    if "longitude" in data and "latitude" in data:
        try:
            return {
                "longitude": float(data["longitude"]),
                "latitude": float(data["latitude"]),
                "name": "当前GPS位置"
            }
        except ValueError:
            pass
    
    if "location" in data:
        location = data["location"]
        if isinstance(location, str) and "," in location:
            lng_lat = location.split(",")
            if len(lng_lat) == 2:
                try:
                    return {
                        "longitude": float(lng_lat[0]),
                        "latitude": float(lng_lat[1]),
                        "name": "当前GPS位置"
                    }
                except ValueError:
                    pass
    
    return None


async def get_gps_location(mcp_client, tool_names: list) -> Optional[Dict[str, Any]]:
    """
    Get current location using GPS-based positioning (maps_geo tool).
    
    Args:
        mcp_client: MCP client instance
        tool_names: List of available tool names
        
    Returns:
        Dictionary with coordinates or None if GPS positioning fails
    """
    if "maps_geo" not in tool_names:
        return None
    
    debug_mode = os.getenv("DEBUG", "").lower() == "true"
    
    gps_params_options = [
        {"address": "current_location"},
        {"address": ""},
        {"get_current_location": True}
    ]
    
    for params in gps_params_options:
        if debug_mode:
            print(f"   尝试GPS参数: {params}")
        
        try:
            result = await mcp_client.call_tool("maps_geo", params)
            
            if result.get("isError") is not True and "content" in result:
                content = result["content"]
                if isinstance(content, list) and len(content) > 0:
                    text_content = content[0].get("text", "")
                    
                    if text_content and not text_content.startswith("API 调用失败"):
                        try:
                            data = json.loads(text_content)
                            coords = await parse_coordinates_from_gps_response(data)
                            if coords:
                                if debug_mode:
                                    print(f"   GPS定位成功: {coords}")
                                return coords
                        except json.JSONDecodeError:
                            if debug_mode:
                                print(f"   无法解析GPS返回的JSON数据")
        except Exception as e:
            if debug_mode:
                print(f"   GPS尝试失败: {str(e)}")
    
    return None


async def get_ip_location(mcp_client, tool_names: list) -> Optional[Dict[str, Any]]:
    """
    Get current location using IP-based positioning.
    
    Args:
        mcp_client: MCP client instance
        tool_names: List of available tool names
        
    Returns:
        Dictionary with coordinates or None if IP positioning fails
    """
    if "maps_ip_location" not in tool_names:
        return None
    
    debug_mode = os.getenv("DEBUG", "").lower() == "true"
    
    try:
        result = await mcp_client.call_tool("maps_ip_location", {})
        
        if debug_mode:
            print(f"   IP定位返回结果")
        
        if result.get("isError") is not True and "content" in result:
            content = result["content"]
            if isinstance(content, list) and len(content) > 0:
                text_content = content[0].get("text", "")
                
                if text_content:
                    try:
                        data = json.loads(text_content)
                        
                        if all(not data.get(key) for key in ['province', 'city', 'adcode', 'rectangle']):
                            if debug_mode:
                                print("   警告: IP定位返回空的位置信息")
                            return None
                        
                        rectangle = data.get("rectangle", "")
                        if rectangle and ";" in rectangle:
                            coords = rectangle.split(";")
                            if len(coords) >= 2:
                                lng_lat = coords[0].split(",")
                                if len(lng_lat) == 2:
                                    try:
                                        return {
                                            "longitude": float(lng_lat[0]),
                                            "latitude": float(lng_lat[1]),
                                            "name": f"{data.get('city', '')}{data.get('district', '')}".strip() or "当前位置"
                                        }
                                    except ValueError:
                                        pass
                    except json.JSONDecodeError:
                        if debug_mode:
                            print(f"   无法解析IP定位返回的JSON数据")
    except Exception as e:
        if debug_mode:
            print(f"   IP定位失败: {str(e)}")
    
    return None


async def get_current_location_coordinates(mcp_client, tool_names: list, amap_client) -> Dict[str, Any]:
    """
    Get current location coordinates using available positioning methods.
    Tries GPS first, then IP-based location, then falls back to default.
    
    Args:
        mcp_client: MCP client instance
        tool_names: List of available tool names
        amap_client: Amap MCP client for fallback
        
    Returns:
        Dictionary with current location coordinates
    """
    print("   获取您的实际位置...")
    
    coords = await get_gps_location(mcp_client, tool_names)
    if coords:
        print(f"   ✓ GPS定位成功")
        return coords
    
    print("   GPS定位失败，尝试IP定位...")
    coords = await get_ip_location(mcp_client, tool_names)
    if coords:
        print(f"   ✓ IP定位成功")
        return coords
    
    print("   ⚠️  定位失败，使用默认位置（北京）")
    return {
        "longitude": 116.4074,
        "latitude": 39.9042,
        "name": "北京市"
    }


async def parse_navigation_request(user_input: str, ai_provider) -> Dict[str, Any]:
    """
    Use AI to parse user's navigation request and extract locations.
    """
    return await ai_provider.parse_navigation_request(user_input)


async def open_browser_navigation(start_coords: Dict[str, Any], end_coords: Dict[str, Any]):
    """
    Open navigation in browser using Amap navigation URL.
    """
    import webbrowser
    import urllib.parse
    
    sname = urllib.parse.quote(start_coords['name'])
    dname = urllib.parse.quote(end_coords['name'])
    
    url = (
        f"https://uri.amap.com/navigation?"
        f"from={start_coords['longitude']},{start_coords['latitude']},{sname}&"
        f"to={end_coords['longitude']},{end_coords['latitude']},{dname}&"
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
        print("  export OPENAI_MODEL='gpt-3.5-turbo'")
        print("- For MCP Server:")
        print("  export AMAP_MCP_SERVER_URL='https://mcp.amap.com/sse'")
        print("  export AMAP_API_KEY='your-amap-api-key'")
        return
    
    print("请选择输入方式:")
    print("1. 文本输入")
    print("2. 语音输入")
    input_type = input("请选择 (1/2): ").strip()
    
    user_input = None
    
    if input_type == "2":
        user_input = await get_voice_input()
    else:
        print("Enter your navigation request (e.g., '从北京到上海', '我要从广州去深圳'):")
        user_input = input("> ").strip()
    
    if not user_input:
        print("No input provided.")
        return
    
    print(f"\n[1/5] Connecting to geocoding service...")
    
    mcp_client = None
    amap_client = None
    use_mcp = True
    
    try:
        server_url = os.getenv("AMAP_MCP_SERVER_URL")
        if not server_url:
            print("⚠️  AMAP_MCP_SERVER_URL not set, falling back to Amap MCP client...")
            use_mcp = False
        else:
            print(f"   Using MCP server: {server_url}")
            if "sse" in server_url.lower():
                transport_type = TransportType.HTTP_SSE
            elif "stream" in server_url.lower():
                transport_type = TransportType.HTTP_STREAM
            else:
                transport_type = TransportType.HTTP_SSE
            auth_type = AuthType.NONE
        
            mcp_client = await create_mcp_client(
                server_url=server_url,
                transport_type=transport_type,
                auth_token=None,
                auth_type=auth_type
            )
            
            if not mcp_client.is_connected():
                raise ConnectionError("MCP client not connected")
            
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
        
        print(f"\n[3/5] 获取起点位置坐标...")
        try:
            start_location = locations['start']
            
            is_current_location = (start_location is None) or \
                                 (isinstance(start_location, str) and \
                                  any(keyword in start_location for keyword in 
                                      ['当前位置', '我的位置', 'current location', 'Current Location']))
            
            if amap_client is None:
                amap_client = create_amap_client()
            
            if is_current_location:
                if use_mcp and mcp_client:
                    start_coords = await get_current_location_coordinates(mcp_client, tool_names, amap_client)
                else:
                    async with amap_client:
                        start_coords = await amap_client.get_current_location()
            else:
                if use_mcp and mcp_client:
                    start_coords = await get_location_coordinates(start_location, mcp_client)
                else:
                    async with amap_client:
                        start_coords = await amap_client.geocode(start_location)
            
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
        if mcp_client:
            await mcp_client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
