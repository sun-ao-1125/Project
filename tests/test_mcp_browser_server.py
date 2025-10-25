#!/usr/bin/env python3
import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from map_navigator.mcp_browser_server import handle_list_tools, handle_call_tool


class TestHandleListTools:
    
    @pytest.mark.asyncio
    async def test_list_tools_returns_two_tools(self):
        tools = await handle_list_tools()
        
        assert len(tools) == 2
        assert tools[0].name == "open_url"
        assert tools[1].name == "open_map_navigation"
    
    @pytest.mark.asyncio
    async def test_list_tools_open_url_schema(self):
        tools = await handle_list_tools()
        open_url_tool = tools[0]
        
        assert open_url_tool.name == "open_url"
        assert open_url_tool.description == "Open a URL in the default web browser"
        assert "url" in open_url_tool.inputSchema["properties"]
        assert "url" in open_url_tool.inputSchema["required"]
    
    @pytest.mark.asyncio
    async def test_list_tools_open_map_navigation_schema(self):
        tools = await handle_list_tools()
        nav_tool = tools[1]
        
        assert nav_tool.name == "open_map_navigation"
        assert "start_lng" in nav_tool.inputSchema["properties"]
        assert "start_lat" in nav_tool.inputSchema["properties"]
        assert "end_lng" in nav_tool.inputSchema["properties"]
        assert "end_lat" in nav_tool.inputSchema["properties"]
        assert len(nav_tool.inputSchema["required"]) == 4


class TestHandleCallTool:
    
    @pytest.mark.asyncio
    async def test_open_url_success(self):
        with patch('webbrowser.open') as mock_open:
            result = await handle_call_tool("open_url", {"url": "https://example.com"})
            
            assert len(result) == 1
            assert result[0].type == "text"
            data = json.loads(result[0].text)
            assert data["success"] is True
            assert "https://example.com" in data["message"]
            mock_open.assert_called_once_with("https://example.com")
    
    @pytest.mark.asyncio
    async def test_open_url_missing_url(self):
        result = await handle_call_tool("open_url", {})
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "error" in data
        assert data["error"] == "URL is required"
    
    @pytest.mark.asyncio
    async def test_open_url_exception(self):
        with patch('webbrowser.open', side_effect=Exception("Browser error")):
            result = await handle_call_tool("open_url", {"url": "invalid"})
            
            assert len(result) == 1
            data = json.loads(result[0].text)
            assert data["success"] is False
            assert "Browser error" in data["error"]
    
    @pytest.mark.asyncio
    async def test_open_map_navigation_success(self):
        with patch('webbrowser.open') as mock_open:
            arguments = {
                "start_lng": 116.397128,
                "start_lat": 39.916527,
                "end_lng": 121.473701,
                "end_lat": 31.230416,
                "start_name": "北京",
                "end_name": "上海"
            }
            
            result = await handle_call_tool("open_map_navigation", arguments)
            
            assert len(result) == 1
            data = json.loads(result[0].text)
            assert data["success"] is True
            assert "北京" in data["message"]
            assert "上海" in data["message"]
            assert "url" in data
            mock_open.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_open_map_navigation_default_names(self):
        with patch('webbrowser.open') as mock_open:
            arguments = {
                "start_lng": 116.397128,
                "start_lat": 39.916527,
                "end_lng": 121.473701,
                "end_lat": 31.230416
            }
            
            result = await handle_call_tool("open_map_navigation", arguments)
            
            assert len(result) == 1
            data = json.loads(result[0].text)
            assert data["success"] is True
            assert "起点" in data["message"]
            assert "终点" in data["message"]
    
    @pytest.mark.asyncio
    async def test_open_map_navigation_exception(self):
        with patch('webbrowser.open', side_effect=Exception("Navigation error")):
            arguments = {
                "start_lng": 0,
                "start_lat": 0,
                "end_lng": 0,
                "end_lat": 0
            }
            
            result = await handle_call_tool("open_map_navigation", arguments)
            
            assert len(result) == 1
            data = json.loads(result[0].text)
            assert data["success"] is False
            assert "Navigation error" in data["error"]
    
    @pytest.mark.asyncio
    async def test_unknown_tool(self):
        result = await handle_call_tool("unknown_tool", {})
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "error" in data
        assert "Unknown tool" in data["error"]
    
    @pytest.mark.asyncio
    async def test_open_map_navigation_url_encoding(self):
        with patch('webbrowser.open') as mock_open:
            arguments = {
                "start_lng": 116.397128,
                "start_lat": 39.916527,
                "end_lng": 121.473701,
                "end_lat": 31.230416,
                "start_name": "天安门广场",
                "end_name": "东方明珠"
            }
            
            result = await handle_call_tool("open_map_navigation", arguments)
            
            data = json.loads(result[0].text)
            assert data["success"] is True
            called_url = mock_open.call_args[0][0]
            assert "天安门广场" not in called_url
            assert "东方明珠" not in called_url
            assert "%E5%" in called_url or "sname=" in called_url
