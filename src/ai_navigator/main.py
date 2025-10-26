#!/usr/bin/env python3
"""
AI Map Navigator - Main Application
Coordinates between AI, MCP server, and browser control MCP server.
"""

import asyncio
import os
import json
import requests
from ai_navigator.ai_provider import create_ai_provider
from ai_navigator.mcp_client import create_mcp_client, TransportType, AuthType
from ai_navigator.amap_mcp_client import create_amap_client
from ai_navigator.voice_recognizer import get_voice_input

# 删除所有JavaScript风格的注释(//开头的行)
# 删除任何中文标点符号
"""
AI Map Navigator - Main Application
Coordinates between AI, MCP server, and browser control MCP server.
"""

# 移除requests导入，因为不再需要
import asyncio
import os
import json
import requests  # 添加requests模块导入
from ai_navigator.ai_provider import create_ai_provider
from ai_navigator.mcp_client import create_mcp_client, TransportType, AuthType
from ai_navigator.amap_mcp_client import create_amap_client
# 导入新的语音识别模块
from ai_navigator.voice_recognizer import get_voice_input

# 在文件开头添加requests模块的导入，因为get_current_location_by_ip函数仍然使用它
# 这行应该被删除，因为已经在上面导入了requests
# import requests

# 或者，如果不再需要这个函数，可以删除它
# 移除get_current_location_by_ip函数，因为我们使用AmapMCPClient的方法
# async def get_current_location_by_ip() -> dict:
#     ...

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
        
        # 修改第336行到第430行左右的代码
        
        # 修改获取起点坐标的逻辑
        print(f"\n[3/5] 获取起点位置坐标...")
        try:
            # 检查起点是否为None或表示当前位置的关键词
            start_location = locations['start']
            
            # 如果起点是None或者包含表示当前位置的关键词，使用高德MCP获取当前位置
            is_current_location = (start_location is None) or \
                                 (isinstance(start_location, str) and \
                                  any(keyword in start_location for keyword in 
                                      ['当前位置', '我的位置', 'current location', 'Current Location']))
            
            # 确保amap_client已初始化，无论是否使用MCP
            if amap_client is None:
                amap_client = create_amap_client()
            
            if is_current_location:
                # 使用高德MCP客户端获取当前位置
                print("   获取您的实际位置...")
                if use_mcp and mcp_client:
                    try:
                        # 优先尝试GPS定位，使用maps_geo工具
                        if "maps_geo" in tool_names:
                            print("   优先尝试通过maps_geo工具获取GPS位置...")
                            # 尝试不同的参数组合来获取当前位置
                            gps_params_options = [
                                {"address": "current_location"},  # 尝试使用特殊关键词
                                {"address": ""},  # 尝试空地址
                                {"get_current_location": True}  # 尝试特定的GPS参数
                            ]
                            
                            gps_success = False
                            for params in gps_params_options:
                                print(f"   尝试参数: {params}")
                                try:  # 这是外部try，需要正确闭合
                                    result = await mcp_client.call_tool("maps_geo", params)
                                    
                                    # 添加调试日志
                                    print(f"   maps_geo工具返回结果: {result}")
                                    print(f"   完整响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
                                    
                                    # 检查结果有效性
                                    if result.get("isError") is not True and "content" in result:
                                        content = result["content"]
                                        if isinstance(content, list) and len(content) > 0:
                                            text_content = content[0].get("text", "")
                                            print(f"   响应文本内容: {text_content}")
                                            
                                            if text_content and not text_content.startswith("API 调用失败"):
                                                try:
                                                    data = json.loads(text_content)
                                                    print(f"   解析后的JSON数据: {data}")
                                                    
                                                    # 尝试从GPS数据中提取坐标
                                                    if isinstance(data, dict):
                                                        # 处理results格式的数据（这是maps_geo实际返回的格式）
                                                        if "results" in data and isinstance(data["results"], list) and len(data["results"]) > 0:
                                                            first_result = data["results"][0]
                                                            if "location" in first_result:
                                                                location = first_result["location"]
                                                                if isinstance(location, str) and "," in location:
                                                                    lng_lat = location.split(",")
                                                                    if len(lng_lat) == 2:
                                                                        start_coords = {
                                                                            "lng": float(lng_lat[0]),
                                                                            "lat": float(lng_lat[1]),
                                                                            "name": f"{first_result.get('province', '')}{first_result.get('city', '')}{first_result.get('district', '')}" or "当前GPS位置"
                                                                        }
                                                                        print(f"   GPS定位成功: {start_coords}")
                                                                        # 确保返回的坐标格式与后续处理一致
                                                                        # 添加longitude和latitude字段，因为后续代码可能依赖这些字段
                                                                        start_coords['longitude'] = start_coords['lng']
                                                                        start_coords['latitude'] = start_coords['lat']
                                                                        # 不再直接return，而是将坐标赋值给外部变量并跳出循环
                                                                        gps_coords = start_coords
                                                                        break
                                                    
                                                    # 尝试不同的坐标字段格式
                                                    if "longitude" in data and "latitude" in data:
                                                        start_coords = {
                                                            "lng": float(data["longitude"]),
                                                            "lat": float(data["latitude"]),
                                                            "name": "当前GPS位置"
                                                        }
                                                        print(f"   GPS定位成功: {start_coords}")
                                                        gps_coords = start_coords
                                                        break
                                                    elif "lng" in data and "lat" in data:
                                                        start_coords = {
                                                            "lng": float(data["lng"]),
                                                            "lat": float(data["lat"]),
                                                            "name": "当前GPS位置"
                                                        }
                                                        print(f"   GPS定位成功: {start_coords}")
                                                        gps_coords = start_coords
                                                        break
                                                    elif "location" in data:
                                                        # 检查location是否包含经纬度
                                                        location = data["location"]
                                                        if isinstance(location, str) and "," in location:
                                                            lng_lat = location.split(",")
                                                            if len(lng_lat) == 2:
                                                                start_coords = {
                                                                    "lng": float(lng_lat[0]),
                                                                    "lat": float(lng_lat[1]),
                                                                    "name": "当前GPS位置"
                                                                }
                                                                print(f"   GPS定位成功: {start_coords}")
                                                                gps_coords = start_coords
                                                                break
                                                except json.JSONDecodeError:
                                                    print(f"   无法解析GPS定位返回的JSON数据")
                                except Exception as e:  # 这是对应的except块
                                    print(f"   尝试参数时出错: {str(e)}")
                            
                            # 修复GPS定位逻辑，确保GPS定位成功后继续执行
                            # 检查是否GPS定位成功
                            if 'gps_coords' in locals():
                                print("   GPS定位成功，使用GPS坐标继续")
                                start_coords = gps_coords
                                # 移除return语句，让程序继续执行后续流程
                            else:
                                print("   所有GPS定位参数尝试均失败，继续尝试IP定位")
                                # 修复GPS定位逻辑和坐标解析错误
                                # GPS定位失败，继续尝试IP定位
                                if "maps_ip_location" in tool_names:
                                    print("   尝试通过IP定位获取当前位置...")
                                    # 使用空参数调用maps_ip_location工具
                                    result = await mcp_client.call_tool("maps_ip_location", {})
                                    
                                    # 添加调试日志
                                    print(f"   maps_ip_location工具返回结果: {result}")
                                    print(f"   完整响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
                                    
                                    # 检查结果有效性
                                    if result.get("isError") is not True and "content" in result:
                                        content = result["content"]
                                        if isinstance(content, list) and len(content) > 0:
                                            text_content = content[0].get("text", "")
                                            print(f"   响应文本内容: {text_content}")
                                            
                                            if text_content:
                                                try:
                                                    data = json.loads(text_content)
                                                    print(f"   解析后的JSON数据: {data}")
                                                    print(f"   响应中的所有字段: {list(data.keys())}")
                                                    
                                                    # 检查数据是否为空
                                                    if all(not data.get(key) for key in ['province', 'city', 'adcode', 'rectangle']):
                                                        print("   警告: 所有位置字段均为空，IP定位可能受限或失败")
                                                        print("   可能的原因: 1. IP地址无法定位 2. 网络环境特殊 3. API限制")
                                                        raise Exception("IP定位服务返回空的位置信息")
                                                    
                                                    # 尝试提取有效坐标（如果rectangle有值）
                                                    rectangle = data.get("rectangle", "")
                                                    # 第425行修复
                                                    if rectangle and ";" in rectangle:
                                                        # 修复缩进，确保coords赋值语句在if块内
                                                        coords = rectangle.split(";")  # 正确写法
                                                        if len(coords) >= 2:
                                                            lng_lat = coords[0].split(",")
                                                            if len(lng_lat) == 2:
                                                                try:
                                                                    start_coords = {
                                                                        "lng": float(lng_lat[0]),
                                                                        "lat": float(lng_lat[1]),
                                                                        "name": f"{data.get('city', '')}{data.get('district', '')}" or "当前位置"
                                                                    }
                                                                    print(f"   IP定位成功: {start_coords}")
                                                                    return start_coords
                                                                except ValueError:
                                                                    pass
                                                    
                                                    # 如果无法从rectangle获取坐标，尝试其他方式
                                                    raise Exception("无法从IP定位结果中提取有效坐标")
                                                except json.JSONDecodeError:
                                                    raise Exception(f"获取位置失败: 无法解析返回的JSON数据: {text_content}")
                                    else:
                                        raise Exception("获取位置失败: IP定位工具返回无效结果")
                                else:
                                    raise Exception("获取位置失败: 系统中没有可用的maps_ip_location工具")
                        else:
                            print("   未发现可用的maps_geo工具，继续尝试IP定位")
                            # maps_geo工具不可用时，尝试IP定位
                            if "maps_ip_location" in tool_names:
                                # 这里也实现完整的IP定位逻辑
                                pass  # 可以复制上面的IP定位代码或提取为函数
                                result = await mcp_client.call_tool("maps_ip_location", {})
                                
                                # 添加调试日志
                                print(f"   maps_ip_location工具返回结果: {result}")
                                print(f"   完整响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
                                
                                # 检查结果有效性
                                if result.get("isError") is not True and "content" in result:
                                    content = result["content"]
                                    if isinstance(content, list) and len(content) > 0:
                                        text_content = content[0].get("text", "")
                                        print(f"   响应文本内容: {text_content}")
                                        
                                        if text_content:
                                            try:
                                                data = json.loads(text_content)
                                                print(f"   解析后的JSON数据: {data}")
                                                print(f"   响应中的所有字段: {list(data.keys())}")
                                                
                                                # 检查数据是否为空
                                                if all(not data.get(key) for key in ['province', 'city', 'adcode', 'rectangle']):
                                                    print("   警告: 所有位置字段均为空，IP定位可能受限或失败")
                                                    print("   可能的原因: 1. IP地址无法定位 2. 网络环境特殊 3. API限制")
                                                    # 由于IP定位失败，抛出异常而不是继续尝试
                                                    raise Exception("IP定位服务返回空的位置信息")
                                                
                                                # 尝试提取有效坐标（如果rectangle有值）
                                                rectangle = data.get("rectangle", "")
                                                if rectangle and ";" in rectangle:
                                                    # 修复这里的语法错误 - 移除多余的.split()
                                                    coords = rectangle.split(";").split()
                                                    if len(coords) >= 2:
                                                        lng_lat = coords[0].split(",")
                                                        if len(lng_lat) == 2:
                                                            try:
                                                                start_coords = {
                                                                    "lng": float(lng_lat[0]),
                                                                    "lat": float(lng_lat[1]),
                                                                    "name": f"{data.get('city', '')}{data.get('district', '')}" or "当前位置"
                                                                }
                                                                print(f"   IP定位成功: {start_coords}")
                                                                return start_coords
                                                            except ValueError:
                                                                pass
                                                
                                                # 如果无法从rectangle获取坐标，尝试其他方式
                                                raise Exception("无法从IP定位结果中提取有效坐标")
                                            except json.JSONDecodeError:
                                                raise Exception(f"获取位置失败: 无法解析返回的JSON数据: {text_content}")
                                    else:
                                        raise Exception("获取位置失败: IP定位工具返回无效结果")
                                else:
                                    raise Exception("获取位置失败: 系统中没有可用的maps_ip_location工具")
                    except Exception as e:
                        # 重新抛出异常
                        if not str(e).startswith("获取位置失败:"):
                            raise Exception(f"获取位置失败: {str(e)}")
                        raise
                else:
                    raise Exception("获取位置失败: 无法使用MCP客户端")
            else:
                # 原有逻辑，通过MCP客户端或Amap客户端获取坐标
                if use_mcp and mcp_client:
                    start_coords = await get_location_coordinates(start_location, mcp_client)
                else:
                    async with amap_client:
                        start_coords = await amap_client.geocode(start_location)
            # 确保无论通过哪种方式获取的坐标，都打印起点信息
            print(f"✓ Start: {start_coords['name']} ({start_coords.get('longitude', start_coords.get('lng'))}, {start_coords.get('latitude', start_coords.get('lat'))})")
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