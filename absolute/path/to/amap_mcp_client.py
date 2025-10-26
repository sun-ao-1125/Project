#!/usr/bin/env python3
"""
Amap MCP Client
Client for connecting to Amap MCP Server for geocoding and map services.
"""

import os
import json
import requests
from typing import Optional, Dict, Any
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class AmapMCPClient:
    """Client for interacting with Amap MCP Server."""
    
    def __init__(self, server_script_path: Optional[str] = None):
        """
        Initialize Amap MCP Client.
        
        Args:
            server_script_path: Path to the Amap MCP server script.
                               If None, will try to use environment variable or default location.
        """
        self.server_script_path = server_script_path or os.getenv(
            "AMAP_MCP_SERVER_PATH",
            "amap-mcp-server"
        )
        self.session: Optional[ClientSession] = None
        self._api_key = os.getenv("AMAP_API_KEY", "")
    
    # ... 现有代码保持不变 ...
    
    async def get_current_location(self) -> Dict[str, Any]:
        """
        获取当前位置信息
        
        优先使用高德地图IP定位API，如果有API密钥
        否则使用MCP服务器的定位工具
        
        Returns:
            包含位置信息的字典，包括名称、经纬度和地址
        """
        # 如果有API密钥，优先使用高德地图IP定位API
        if self._api_key:
            try:
                url = "https://restapi.amap.com/v3/ip"
                params = {
                    "key": self._api_key,
                }
                
                # 使用同步请求，因为这是在异步函数中的一次性调用
                # 对于更复杂的场景，可以考虑使用aiohttp等异步HTTP客户端
                response = requests.get(url, params=params, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "1":
                        # 提取位置信息
                        country = data.get("country", "中国")
                        province = data.get("province", "")
                        city = data.get("city", "")
                        district = data.get("district", "")
                        
                        # 构建位置名称
                        location_name = "当前位置"
                        if district:
                            location_name = district
                        elif city:
                            location_name = city
                        elif province:
                            location_name = province
                        
                        # 使用获取到的位置名称进行地理编码获取精确坐标
                        try:
                            # 先尝试完整地址
                            full_address = f"{province}{city}{district}"
                            if full_address.strip():
                                location_coords = await self.geocode(full_address)
                                return {
                                    "name": location_name,
                                    "longitude": location_coords["longitude"],
                                    "latitude": location_coords["latitude"],
                                    "formatted_address": full_address,
                                    "source": "amap_ip"
                                }
                        except Exception:
                            # 如果地理编码失败，返回基于IP的基本信息
                            return {
                                "name": location_name,
                                "longitude": 116.4074,  # 默认北京坐标
                                "latitude": 39.9042,
                                "formatted_address": full_address,
                                "source": "amap_ip_fallback"
                            }
            except Exception as e:
                print(f"高德IP定位API调用失败: {e}")
        
        # 如果没有API密钥或IP定位失败，尝试使用MCP服务器的定位工具
        if self.session:
            try:
                result = await self.session.call_tool("get_location")
                
                if result.content and len(result.content) > 0:
                    content = result.content[0]
                    if hasattr(content, 'text'):
                        data = json.loads(content.text)
                        if data.get("success") and "location" in data:
                            return data["location"]
            except Exception as e:
                print(f"MCP服务器定位工具调用失败: {e}")
        
        # 如果以上方法都失败，尝试使用关键词进行地理编码
        try:
            for keyword in ["当前位置", "我的位置", "当前定位"]:
                try:
                    location_coords = await self.geocode(keyword)
                    location_coords["source"] = "amap_keyword"
                    return location_coords
                except Exception:
                    continue
        except Exception:
            pass
        
        # 所有方法都失败，返回默认位置
        return {
            "name": "当前位置",
            "longitude": 116.4074,
            "latitude": 39.9042,
            "formatted_address": "中国北京市",
            "source": "default"
        }

class MockAmapMCPClient:
    """Mock Amap MCP Client for testing without actual server."""
    
    # ... 现有代码保持不变 ...
    
    async def get_current_location(self) -> Dict[str, Any]:
        """
        Mock implementation of get_current_location.
        Returns a mock location (Beijing by default).
        """
        # 模拟定位功能，返回默认位置（北京）
        # 这里可以根据测试需求修改返回值
        return {
            "name": "当前位置",
            "longitude": 116.397128,
            "latitude": 39.916527,
            "formatted_address": "中国北京市",
            "source": "mock"
        }

# ... 其余代码保持不变 ...