#!/usr/bin/env python3
"""
Amap MCP Client
Client for connecting to Amap MCP Server for geocoding and map services.
"""

import os
import json
from typing import Optional, Dict, Any
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from anthropic import Anthropic

class AmapMCPClient:
    """Client for interacting with Amap MCP Server."""
    
    def __init__(self, server_script_path: Optional[str] = None, server_url: Optional[str] = None):
        """
        Initialize Amap MCP Client.
        
        Args:
            server_script_path: Path to the Amap MCP server script.
                               If None, will try to use environment variable or default location.
            server_url: URL of the Amap MCP server (HTTP mode).
                        If None, will try to use environment variable.
        """
        self.server_script_path = server_script_path or os.getenv(
            "AMAP_MCP_SERVER_PATH",
            "amap-mcp-server"
        )
        self.server_url = server_url or os.getenv("AMAP_MCP_SERVER_URL")
        self.session: Optional[ClientSession] = None
        self._api_key = os.getenv("AMAP_API_KEY", "")
        self.client = None
        
    async def connect(self):
        """Connect to the Amap MCP server."""
        if self.server_url:
            # 使用HTTP方式连接
            from ai_navigator.mcp_client import MCPConfig, TransportType, AuthType, HTTPSSETransport
            
            # SECURITY: Do not extract API keys from URLs - use AMAP_API_KEY environment variable
            if 'key=' in self.server_url:
                print("⚠️  WARNING: API key detected in URL. Use AMAP_API_KEY environment variable instead for security.")
            
            config = MCPConfig(
                server_url=self.server_url,
                transport_type=TransportType.HTTP_SSE,
                auth_type=AuthType.API_KEY if self._api_key else AuthType.NONE,
                auth_token=self._api_key,
                timeout=30
            )
            
            self.client = HTTPSSETransport(config)
            await self.client.connect()
        else:
            # 使用标准输入输出方式连接
            server_params = StdioServerParameters(
                command=self.server_script_path,
                args=[],
                env={
                    "AMAP_API_KEY": self._api_key
                } if self._api_key else None
            )
            
            stdio_transport = await stdio_client(server_params)
            self.stdio, self.write = stdio_transport
            self.session = ClientSession(self.stdio, self.write)
            await self.session.initialize()
        
        return self
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on the MCP server."""
        if self.client:
            # 使用HTTP客户端调用工具
            return await self.client.send_request("call_tool", {
                "tool": tool_name,
                "arguments": arguments
            })
        elif self.session:
            # 使用标准输入输出客户端调用工具
            return await self.session.call_tool(tool_name, arguments)
        else:
            raise RuntimeError("Not connected to Amap MCP server. Call connect() first.")
    
    async def disconnect(self):
        """Disconnect from the Amap MCP server."""
        if self.client:
            await self.client.disconnect()
            self.client = None
        elif self.session:
            await self.session.__aexit__(None, None, None)
            self.session = None

    async def geocode(self, address: str) -> Dict[str, Any]:
        """
        Geocode an address to coordinates using Amap MCP server.
        
        Args:
            address: Address or location name to geocode
            
        Returns:
            Dictionary with location information including longitude and latitude
        """
        try:
            result = await self.call_tool(
                "geocode",
                arguments={"address": address}
            )
            
            if isinstance(result, dict) and result.get("status") == "success" and result.get("location"):
                loc = result["location"]
                return {
                    "name": address,
                    "longitude": loc["longitude"],
                    "latitude": loc["latitude"],
                    "formatted_address": result.get("formatted_address", address)
                }
            
            raise ValueError(f"Failed to geocode address: {address}")
            
        except Exception as e:
            raise ValueError(f"Geocoding error: {str(e)}")
    
    async def reverse_geocode(self, longitude: float, latitude: float) -> Dict[str, Any]:
        """
        Reverse geocode coordinates to address using Amap MCP server.
        
        Args:
            longitude: Longitude coordinate
            latitude: Latitude coordinate
            
        Returns:
            Dictionary with address information
        """
        if not self.session:
            raise RuntimeError("Not connected to Amap MCP server. Call connect() first.")
        
        try:
            result = await self.session.call_tool(
                "reverse_geocode",
                arguments={
                    "longitude": longitude,
                    "latitude": latitude
                }
            )
            
            if result.content and len(result.content) > 0:
                content = result.content[0]
                if hasattr(content, 'text'):
                    data = json.loads(content.text)
                    return data
            
            raise ValueError("Failed to reverse geocode coordinates")
            
        except Exception as e:
            raise ValueError(f"Reverse geocoding error: {str(e)}")
    
    async def search_poi(self, keyword: str, city: Optional[str] = None) -> list:
        """
        Search for POI (Point of Interest) using Amap MCP server.
        
        Args:
            keyword: Search keyword
            city: Optional city name to narrow search
            
        Returns:
            List of POI results
        """
        if not self.session:
            raise RuntimeError("Not connected to Amap MCP server. Call connect() first.")
        
        try:
            args = {"keyword": keyword}
            if city:
                args["city"] = city
            
            result = await self.session.call_tool("search_poi", arguments=args)
            
            if result.content and len(result.content) > 0:
                content = result.content[0]
                if hasattr(content, 'text'):
                    data = json.loads(content.text)
                    return data.get("pois", [])
            
            return []
            
        except Exception as e:
            raise ValueError(f"POI search error: {str(e)}")
    
    async def get_current_location(self) -> Dict[str, Any]:
        """
        Get current location using Amap MCP server with fallback mechanisms.
        
        This method attempts to get the current location through the following steps:
        1. First tries the 'get_location' MCP tool (GPS-based location)
        2. Falls back to 'ip_location' MCP tool if get_location fails
        3. Returns default location (Beijing) if both methods fail
        
        Returns:
            Dictionary with current location information:
            - name (str): Location name or "北京市" as default
            - longitude (float): Longitude coordinate
            - latitude (float): Latitude coordinate
            - formatted_address (str): Formatted address string
            
        Note:
            This method never raises exceptions. If location detection fails,
            it silently returns Beijing coordinates (116.4074, 39.9042).
        """
        if not self.session:
            raise RuntimeError("Not connected to Amap MCP server. Call connect() first.")
        
        try:
            # 使用高德MCP的get_location工具获取当前位置
            result = await self.session.call_tool(
                "get_location",
                arguments={}
            )
            
            if result.content and len(result.content) > 0:
                content = result.content[0]
                if hasattr(content, 'text'):
                    data = json.loads(content.text)
                    
                    # 处理返回的位置信息
                    if data.get("status") == "success" and data.get("location"):
                        loc = data["location"]
                        return {
                            "name": data.get("name", "") or data.get("formatted_address", "") or "定位位置",  # 使用实际位置名称
                            "longitude": float(loc.get("longitude", 0)),
                            "latitude": float(loc.get("latitude", 0)),
                            "formatted_address": data.get("formatted_address", "未知位置")
                        }
            
            # 如果get_location失败，尝试使用IP定位作为备选
            try:
                result = await self.session.call_tool(
                    "ip_location",
                    arguments={}
                )
                
                if result.content and len(result.content) > 0:
                    content = result.content[0]
                    if hasattr(content, 'text'):
                        data = json.loads(content.text)
                        if data.get("status") == "success" and data.get("location"):
                            loc = data["location"]
                            return {
                                "name": data.get("name", "") or data.get("formatted_address", "") or "定位位置",  # 使用实际位置名称
                                "longitude": float(loc.get("longitude", 0)),
                                "latitude": float(loc.get("latitude", 0)),
                                "formatted_address": data.get("formatted_address", "未知位置")
                            }
            except Exception:
                # 如果IP定位也失败，不抛出异常，继续使用默认位置
                pass
            
            # 返回默认位置（北京）
            return {
                "name": "北京市",  # 使用更具体的默认名称
                "longitude": 116.4074,
                "latitude": 39.9042,
                "formatted_address": "中国北京市"
            }
            
        except Exception as e:
            print(f"⚠️  获取当前位置出错: {e}，使用默认位置")
            # 异常情况下返回默认位置
            return {
                "name": "北京市",  # 使用更具体的默认名称
                "longitude": 116.4074,
                "latitude": 39.9042,
                "formatted_address": "中国北京市"
            }


class MockAmapMCPClient:
    """Mock Amap MCP Client for testing without actual server."""
    
    def __init__(self, *args, **kwargs):
        """Initialize mock client."""
        self.connected = False
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
    
    async def connect(self):
        """Mock connect."""
        self.connected = True
        return self
    
    async def disconnect(self):
        """Mock disconnect."""
        self.connected = False
    
    async def geocode(self, address: str) -> Dict[str, Any]:
        """Mock geocode with predefined coordinates."""
        mock_coords = {
            "北京": {"lng": 116.397128, "lat": 39.916527},
            "上海": {"lng": 121.473701, "lat": 31.230416},
            "广州": {"lng": 113.264385, "lat": 23.129112},
            "深圳": {"lng": 114.057868, "lat": 22.543099},
            "杭州": {"lng": 120.155070, "lat": 30.274085},
            "成都": {"lng": 104.065735, "lat": 30.659462},
            "西安": {"lng": 108.940175, "lat": 34.341568},
            "重庆": {"lng": 106.551643, "lat": 29.563761},
            "南京": {"lng": 118.796623, "lat": 32.059344},
            "武汉": {"lng": 114.305539, "lat": 30.593102},
        }
        
        for city, coords in mock_coords.items():
            if city in address:
                return {
                    "name": city,
                    "longitude": coords["lng"],
                    "latitude": coords["lat"],
                    "formatted_address": f"{city}市"
                }
        
        return {
            "name": address,
            "longitude": 116.397128,
            "latitude": 39.916527,
            "formatted_address": address
        }
    
    async def reverse_geocode(self, longitude: float, latitude: float) -> Dict[str, Any]:
        """Mock reverse geocode."""
        return {
            "formatted_address": f"Location at ({longitude}, {latitude})",
            "province": "Unknown",
            "city": "Unknown"
        }
    
    async def search_poi(self, keyword: str, city: Optional[str] = None) -> list:
        """Mock POI search."""
        return [
            {
                "name": f"{keyword}示例地点",
                "address": f"{city or '某城市'}{keyword}附近",
                "location": {"longitude": 116.397128, "latitude": 39.916527}
            }
        ]


def create_amap_client(use_mock: bool = None) -> AmapMCPClient:
    """
    Create an Amap MCP client.
    
    Args:
        use_mock: If True, use mock client. If None, auto-detect based on environment.
        
    Returns:
        AmapMCPClient or MockAmapMCPClient instance
    """
    if use_mock is None:
        # 检查AMAP_MCP_SERVER_URL、AMAP_MCP_SERVER_PATH或AMAP_API_KEY环境变量
        use_mock = not bool(os.getenv("AMAP_MCP_SERVER_URL") or os.getenv("AMAP_MCP_SERVER_PATH") or os.getenv("AMAP_API_KEY"))
    
    if use_mock:
        print("Note: Using mock Amap MCP client. Set AMAP_MCP_SERVER_URL, AMAP_MCP_SERVER_PATH or AMAP_API_KEY to use real server.")
        return MockAmapMCPClient()
    else:
        # 创建客户端时传入server_url
        return AmapMCPClient(server_url=os.getenv("AMAP_MCP_SERVER_URL"))
