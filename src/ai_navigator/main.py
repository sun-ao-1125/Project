#!/usr/bin/env python3
"""
AI Map Navigator - Main Application
Coordinates between AI, MCP server, and browser control MCP server.
"""

# 在导入部分添加requests库
import asyncio
import os
import json
import requests
from ai_navigator.ai_provider import create_ai_provider
from ai_navigator.mcp_client import create_mcp_client, TransportType, AuthType
from ai_navigator.amap_mcp_client import create_amap_client
# 导入新的语音识别模块
from ai_navigator.voice_recognizer import get_voice_input

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
            location_str = data.get('loc', '39.9042,116.4074')  # 默认北京坐标
            lat, lng = map(float, location_str.split(','))
            
            # 城市名称中英文映射
            city_translation = {
                'Guangzhou': '广州',
                'Beijing': '北京',
                'Shanghai': '上海',
                'Shenzhen': '深圳',
                'Hangzhou': '杭州',
                'Chengdu': '成都',
                'Wuhan': '武汉',
                'Xi\'an': '西安',
                'Chongqing': '重庆',
                'Nanjing': '南京'
            }
            
            # 省份名称中英文映射
            region_translation = {
                'Guangdong': '广东',
                'Beijing': '北京',
                'Shanghai': '上海',
                'Zhejiang': '浙江',
                'Sichuan': '四川',
                'Hubei': '湖北',
                'Shaanxi': '陕西',
                'Chongqing': '重庆',
                'Jiangsu': '江苏'
            }
            
            # 国家名称中英文映射
            country_translation = {
                'CN': '中国',
                'US': '美国',
                'JP': '日本',
                'KR': '韩国',
                'SG': '新加坡'
            }
            
            # 获取并翻译地名
            city = data.get('city', '未知城市')
            city_cn = city_translation.get(city, city)  # 如果在映射表中找到则翻译，否则保留原名称
            
            region = data.get('region', '')
            region_cn = region_translation.get(region, region)
            
            country = data.get('country', '')
            country_cn = country_translation.get(country, country)
            
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
            # API调用失败时返回默认位置（北京）
            print("⚠️  无法获取IP位置信息，使用默认位置")
            return {
                "name": "当前位置",
                "longitude": 116.4074,
                "latitude": 39.9042,
                "formatted_address": "中国北京市"
            }
    except Exception as e:
        print(f"⚠️  IP定位出错: {e}，使用默认位置")
        # 异常情况下返回默认位置
        return {
            "name": "当前位置",
            "longitude": 116.4074,
            "latitude": 39.9042,
            "formatted_address": "中国北京市"
        }

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
    import urllib.parse
    
    # 确保正确编码起点和终点名称
    sname = urllib.parse.quote(start_coords['name'])
    dname = urllib.parse.quote(end_coords['name'])
    
    # 构建符合高德地图API的URL，确保正确显示起点终点名称
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
        
        # 修改获取起点坐标的逻辑中的输出信息，使用中文替代英文
        print(f"\n[3/5] 获取起点位置坐标...")
        try:
            # 检查起点是否为None或表示当前位置的关键词
            start_location = locations['start']
            
            # 如果起点是None或者包含表示当前位置的关键词，使用IP定位
            is_current_location = (start_location is None) or \
                                 (isinstance(start_location, str) and \
                                  any(keyword in start_location for keyword in 
                                      ['当前位置', '我的位置', 'current location', 'Current Location']))
            
            if is_current_location:
                # 使用IP获取真实地理位置
                print("   获取您的实际位置...")
                start_coords = await get_current_location_by_ip()
                print(f"✓ 使用您的实际位置: {start_coords['name']} ({start_coords['longitude']}, {start_coords['latitude']})")
            else:
                # 原有逻辑，通过MCP客户端或Amap客户端获取坐标
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
        # Ensure proper cleanup
        if mcp_client:
            await mcp_client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())