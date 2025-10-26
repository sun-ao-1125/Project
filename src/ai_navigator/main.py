#!/usr/bin/env python3
"""
AI Map Navigator - Main Application
Coordinates between AI, MCP server, and browser control MCP server.
"""

import asyncio
import os
import json
import requests
import logging
from typing import Optional, Dict, Any
from ai_navigator.config import load_config
from ai_navigator.ai_provider import create_ai_provider
from ai_navigator.mcp_client import create_mcp_client, TransportType, AuthType, _sanitize_url
from ai_navigator.amap_mcp_client import create_amap_client
from ai_navigator.voice_recognizer import get_voice_input
from ai_navigator.constants import (
    DEFAULT_LOCATION,
    CITY_TRANSLATIONS,
    REGION_TRANSLATIONS,
    COUNTRY_TRANSLATIONS,
    CURRENT_LOCATION_KEYWORDS,
    GPS_PARAM_OPTIONS,
    get_step_label
)
from ai_navigator.ai_context import AIContext

load_config()

# 尝试导入SystemMCPManager，如果不存在则使用回退方案
try:
    from ai_navigator.system_mcp_manager import SystemMCPManager, TransportMethod
    SYSTEM_MCP_AVAILABLE = True
except ImportError:
    SYSTEM_MCP_AVAILABLE = False
    print("⚠️  SystemMCPManager not available, using fallback browser control")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Disable httpx INFO logging to prevent API keys in URLs from being logged
logging.getLogger("httpx").setLevel(logging.WARNING)


def _sanitize_url(url: str) -> str:
    """
    Sanitize URL by masking sensitive query parameters (keys, tokens, etc.).
    
    Args:
        url: The URL to sanitize
        
    Returns:
        Sanitized URL with masked sensitive parameters
    """
    if not url:
        return url
    
    try:
        from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
        
        parsed = urlparse(url)
        if not parsed.query:
            return url
        
        params = parse_qs(parsed.query, keep_blank_values=True)
        
        sensitive_params = ['key', 'api_key', 'apikey', 'token', 'access_token', 
                          'secret', 'password', 'auth', 'authorization', 'ak', 'sk']
        
        sanitized_params = {}
        for key, values in params.items():
            key_lower = key.lower()
            if any(sensitive in key_lower for sensitive in sensitive_params):
                sanitized_params[key] = ['***']
            else:
                sanitized_params[key] = values
        
        sanitized_query = urlencode(sanitized_params, doseq=True)
        sanitized = parsed._replace(query=sanitized_query)
        
        return urlunparse(sanitized)
    except Exception:
        return url

# 添加一个新函数用于通过IP获取当前位置
# 修改get_current_location_by_ip函数，确保返回中文地名
async def get_current_location_by_ip() -> dict:
    """
    通过IP获取用户的当前地理位置
    使用ipinfo.io提供的免费API，并将结果转换为中文显示
    
    Returns:
        包含位置信息的字典
    """
    try:
        # 调用ipinfo.io API获取IP位置信息
        response = requests.get('https://ipinfo.io/json')
        if response.status_code == 200:
            data = response.json()
            
            # 解析位置信息
            default_loc = f"{DEFAULT_LOCATION['latitude']},{DEFAULT_LOCATION['longitude']}"
            location_str = data.get('loc', default_loc)
            lat, lng = map(float, location_str.split(','))
            
            # 获取并翻译地名
            city = data.get('city', '未知城市')
            city_cn = CITY_TRANSLATIONS.get(city, city)
            
            region = data.get('region', '')
            region_cn = REGION_TRANSLATIONS.get(region, region)
            
            country = data.get('country', '')
            country_cn = COUNTRY_TRANSLATIONS.get(country, country)
            
            # 构建完整的位置名称（中文）
            location_name = f"{city_cn}"
            if region_cn and region_cn != city_cn:
                location_name = f"{region_cn}{location_name}"
            
            return {
                "name": location_name,
                "longitude": lng,
                "latitude": lat,
                "formatted_address": f"{country_cn}{region_cn}{city_cn}"
            }
        else:
            print("⚠️  无法获取IP位置信息，使用默认位置")
            return DEFAULT_LOCATION.copy()
    except Exception as e:
        print(f"⚠️  IP定位出错: {e}，使用默认位置")
        return DEFAULT_LOCATION.copy()

async def get_location_coordinates_ai_driven(
    location_name: str, 
    mcp_client, 
    ai_provider,
    is_current_location: bool = False
) -> dict:
    """
    AI-driven location coordinate lookup using MCP tools.
    The AI intelligently selects the best MCP tool and parses the response.
    
    Args:
        location_name: Name of the location to geocode
        mcp_client: MCP client instance
        ai_provider: AI provider for intelligent tool selection
        is_current_location: Whether this is the user's current location
        
    Returns:
        Dictionary with location coordinates
    """
    try:
        # Get available MCP tools
        tools = mcp_client.list_tools()
        
        # Prepare tool information for AI
        available_tools = []
        for tool in tools:
            tool_info = {
                "name": tool.name,
                "description": tool.description if hasattr(tool, 'description') else f"Tool: {tool.name}",
                "parameters": {}
            }
            if hasattr(tool, 'inputSchema'):
                tool_info["parameters"] = tool.inputSchema
            available_tools.append(tool_info)
        
        # Let AI select the most appropriate tool
        context = {
            "is_current_location": is_current_location,
            "location_type": "current" if is_current_location else "destination"
        }
        
        tool_decision = await ai_provider.select_mcp_tool(
            user_intent=f"Get coordinates for location: {location_name}",
            available_tools=available_tools,
            context=context
        )
        
        debug_mode = os.getenv("DEBUG", "").lower() == "true"
        if debug_mode:
            print(f"   AI selected tool: {tool_decision['tool_name']}")
            print(f"   Reasoning: {tool_decision['reasoning']}")
        
        # Call the selected tool with AI-generated arguments
        result = await mcp_client.call_tool(
            tool_decision["tool_name"],
            tool_decision["arguments"]
        )
        
        # Let AI parse the response
        parsed_data = await ai_provider.parse_mcp_response(
            raw_response=result,
            expected_info="Extract location name, longitude, latitude, and formatted address",
            context={"original_location_name": location_name}
        )
        
        return parsed_data
        
    except Exception as e:
        raise ValueError(f"Failed to get coordinates for '{location_name}': {str(e)}")


async def get_location_coordinates(location_name: str, mcp_client, ai_provider=None) -> dict:
    """
    Get coordinates for a location using MCP server.
    Uses AI-driven tool selection if ai_provider is provided, otherwise falls back to hardcoded logic.
    
    Args:
        location_name: Name of the location to geocode
        mcp_client: MCP client instance
        ai_provider: Optional AI provider for intelligent tool selection
        
    Returns:
        Dictionary with location coordinates
    """
    # Try AI-driven approach first if AI provider is available
    if ai_provider:
        try:
            return await get_location_coordinates_ai_driven(location_name, mcp_client, ai_provider)
        except Exception as e:
            print(f"   AI-driven lookup failed, falling back to hardcoded logic: {e}")
    
    # Fallback to hardcoded logic
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
    
    gps_params_options = GPS_PARAM_OPTIONS
    
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
    return DEFAULT_LOCATION.copy()


async def parse_navigation_request(user_input: str, ai_provider) -> Dict[str, Any]:
    """
    Use AI to parse user's navigation request and extract locations.
    """
    return await ai_provider.parse_navigation_request(user_input)

async def open_browser_navigation(start_coords: dict, end_coords: dict, ai_provider, mcp_manager=None):
    """
    Use AI provider to generate navigation URL and open in browser.
    Supports both MCP protocol and direct browser control as fallback.
    """
    result_dict = await ai_provider.generate_navigation_url(start_coords, end_coords)
    url = result_dict['url']
    
    if mcp_manager and SYSTEM_MCP_AVAILABLE:
        try:
            result = await mcp_manager.call_tool(
                server_name="browser",
                tool_name="open_map_navigation",
                arguments={
                    "start_lng": start_coords['longitude'],
                    "start_lat": start_coords['latitude'],
                    "end_lng": end_coords['longitude'],
                    "end_lat": end_coords['latitude'],
                    "start_name": start_coords['name'],
                    "end_name": end_coords.get('name', '终点'),
                    "mode": result_dict.get('mode', 'car'),
                    "policy": result_dict.get('policy', 1),
                    "callnative": result_dict.get('callnative', 1)
                }
            )
            
            if result.content and len(result.content) > 0:
                content = result.content[0]
                if hasattr(content, 'text'):
                    data = json.loads(content.text)
                    return {
                        "success": data.get("success", False),
                        "message": data.get("message", "Navigation opened"),
                        "url": data.get("url", url),
                        "mode": result_dict.get('mode', 'car'),
                        "policy": result_dict.get('policy', 1),
                        "callnative": result_dict.get('callnative', 1),
                        "description": result_dict.get('description', 'AI-generated navigation')
                    }
        
        except Exception as e:
            logger.error(f"Failed to open browser navigation via MCP: {e}")
            # Fall back to direct browser control
            pass
    
    # Fallback to direct browser control
    import webbrowser
    webbrowser.open(url)
    
    return {
        "success": True,
        "message": f"Navigation opened from {start_coords['name']} to {end_coords['name']}",
        "url": url,
        "mode": result_dict.get('mode', 'car'),
        "policy": result_dict.get('policy', 1),
        "callnative": result_dict.get('callnative', 1),
        "description": result_dict.get('description', 'AI-generated navigation')
    }


async def main():
    """Main application flow."""
    print("=== AI Map Navigator (MCP Architecture with Security) ===\n")
    
    ai_context = AIContext()
    
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
    
    # Initialize MCP Manager if available
    mcp_manager = None
    if SYSTEM_MCP_AVAILABLE:
        mcp_manager = SystemMCPManager(
            enable_security=True,
            enable_confirmation=False,
            audit_log_file="mcp_audit.log"
        )
        
        try:
            print("\n[0/5] Initializing MCP system...")
            browser_server_path = os.path.join(os.path.dirname(__file__), "mcp_browser_server.py")
            success = await mcp_manager.register_server(
                name="browser",
                server_path=browser_server_path,
                transport=TransportMethod.STDIO
            )
            
            if success:
                print("✓ Browser control MCP server registered")
            else:
                print("⚠️  Failed to register browser control MCP server, falling back to direct control")
                mcp_manager = None
        except Exception as e:
            print(f"⚠️  Failed to initialize browser MCP: {e}")
            print("   Falling back to direct browser control")
            mcp_manager = None
    
    # 添加语音输入选项
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
    
    ai_context.add_user_message(user_input)
    
    print(f"\n{get_step_label('CONNECT')} Connecting to geocoding service...")
    
    mcp_client = None
    amap_client = None
    use_mcp = True
    
    try:
        server_url = os.getenv("AMAP_MCP_SERVER_URL")
        if not server_url:
            print("⚠️  AMAP_MCP_SERVER_URL not set, falling back to Amap MCP client...")
            use_mcp = False
        else:
            print(f"   Using MCP server: {_sanitize_url(server_url)}")
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
        print(f"\n{get_step_label('PARSE')} Parsing request with AI...")
        try:
            ai_provider.set_context(
                ai_context.get_conversation_history(),
                ai_context.get_context_summary()
            )
            locations = await parse_navigation_request(user_input, ai_provider)
            print(f"✓ Parsed: {locations['start']} → {locations['end']}")
            ai_context.add_assistant_message(f"Parsed locations: {locations['start']} → {locations['end']}")
        except Exception as e:
            print(f"✗ Failed to parse request: {e}")
            return
        
        print(f"\n{get_step_label('START_COORDS')} 获取起点位置坐标...")
        try:
            start_location = locations['start']
            
            is_current_location = (start_location is None) or \
                                 (isinstance(start_location, str) and \
                                  any(keyword in start_location for keyword in CURRENT_LOCATION_KEYWORDS))
            
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
                    start_coords = await get_location_coordinates(start_location, mcp_client, ai_provider)
                else:
                    async with amap_client:
                        start_coords = await amap_client.geocode(start_location)
            
            print(f"✓ Start: {start_coords['name']} ({start_coords['longitude']}, {start_coords['latitude']})")
            ai_context.set_start_location(start_coords)
        except Exception as e:
            print(f"✗ Failed to get start coordinates: {e}")
            return
        
        print(f"\n{get_step_label('END_COORDS')} Getting coordinates for end location...")
        try:
            if use_mcp and mcp_client:
                end_coords = await get_location_coordinates(locations['end'], mcp_client, ai_provider)
            else:
                async with amap_client:
                    end_coords = await amap_client.geocode(locations['end'])
            print(f"✓ End: {end_coords['name']} ({end_coords['longitude']}, {end_coords['latitude']})")
            ai_context.set_end_location(end_coords)
        except Exception as e:
            print(f"✗ Failed to get end coordinates: {e}")
            return
        
        print(f"\n{get_step_label('OPEN_BROWSER')} Opening navigation in browser...")
        try:
            result = await open_browser_navigation(start_coords, end_coords, ai_provider, mcp_manager)
            print(f"✓ {result['message']}")
            print(f"   Mode: {result['mode']}, Policy: {result['policy']}, Native App: {'Yes' if result['callnative'] == 1 else 'No'}")
            print(f"   AI Decision: {result['description']}")
            if 'url' in result and result['url']:
                print(f"\nNavigation URL: {result['url']}")
        except Exception as e:
            print(f"✗ Failed to open navigation: {e}")
            return
        
        print("\n=== Navigation request completed successfully! ===")
    
    finally:
        if mcp_client:
            await mcp_client.disconnect()
        
        if mcp_manager:
            await mcp_manager.disconnect_all()


if __name__ == "__main__":
    asyncio.run(main())
