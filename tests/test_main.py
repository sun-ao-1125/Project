#!/usr/bin/env python3
import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from map_navigator.main import (
    get_location_coordinates,
    parse_navigation_request,
    open_browser_navigation,
    main
)


class TestGetLocationCoordinates:
    
    @pytest.mark.asyncio
    async def test_get_location_coordinates_with_maps_geo(self):
        mock_client = Mock()
        mock_tool = Mock()
        mock_tool.name = "maps_geo"
        mock_client.list_tools = Mock(return_value=[mock_tool])
        
        mock_result = {
            "content": [{
                "text": json.dumps({
                    "results": [{
                        "location": "116.397128,39.916527",
                        "province": "北京市",
                        "city": "北京市"
                    }]
                })
            }]
        }
        mock_client.call_tool = AsyncMock(return_value=mock_result)
        
        result = await get_location_coordinates("北京", mock_client)
        
        assert result["name"] == "北京"
        assert result["longitude"] == 116.397128
        assert result["latitude"] == 39.916527
    
    @pytest.mark.asyncio
    async def test_get_location_coordinates_with_maps_text_search(self):
        mock_client = Mock()
        mock_tool = Mock()
        mock_tool.name = "maps_text_search"
        mock_client.list_tools = Mock(return_value=[mock_tool])
        
        mock_result = {
            "content": [{
                "text": json.dumps({
                    "pois": [{
                        "location": "121.473701,31.230416",
                        "address": "上海市"
                    }]
                })
            }]
        }
        mock_client.call_tool = AsyncMock(return_value=mock_result)
        
        result = await get_location_coordinates("上海", mock_client)
        
        assert result["name"] == "上海"
        assert result["longitude"] == 121.473701
        assert result["latitude"] == 31.230416
    
    @pytest.mark.asyncio
    async def test_get_location_coordinates_with_geocode(self):
        mock_client = Mock()
        mock_tool = Mock()
        mock_tool.name = "geocode"
        mock_client.list_tools = Mock(return_value=[mock_tool])
        
        mock_result = {
            "content": [{
                "text": json.dumps({
                    "status": "success",
                    "location": {"longitude": 113.264385, "latitude": 23.129112},
                    "formatted_address": "广州市"
                })
            }]
        }
        mock_client.call_tool = AsyncMock(return_value=mock_result)
        
        result = await get_location_coordinates("广州", mock_client)
        
        assert result["name"] == "广州"
        assert result["longitude"] == 113.264385
        assert result["latitude"] == 23.129112
    
    @pytest.mark.asyncio
    async def test_get_location_coordinates_no_tool_available(self):
        mock_client = Mock()
        mock_client.list_tools = Mock(return_value=[])
        
        with pytest.raises(ValueError, match="No geocoding tool available"):
            await get_location_coordinates("test", mock_client)
    
    @pytest.mark.asyncio
    async def test_get_location_coordinates_invalid_response(self):
        mock_client = Mock()
        mock_tool = Mock()
        mock_tool.name = "geocode"
        mock_client.list_tools = Mock(return_value=[mock_tool])
        
        mock_result = {"content": []}
        mock_client.call_tool = AsyncMock(return_value=mock_result)
        
        with pytest.raises(ValueError, match="Failed to geocode location"):
            await get_location_coordinates("invalid", mock_client)
    
    @pytest.mark.asyncio
    async def test_get_location_coordinates_exception(self):
        mock_client = Mock()
        mock_tool = Mock()
        mock_tool.name = "geocode"
        mock_client.list_tools = Mock(return_value=[mock_tool])
        mock_client.call_tool = AsyncMock(side_effect=Exception("API error"))
        
        with pytest.raises(ValueError, match="Failed to geocode location 'test': API error"):
            await get_location_coordinates("test", mock_client)


class TestParseNavigationRequest:
    
    @pytest.mark.asyncio
    async def test_parse_navigation_request_success(self):
        mock_provider = Mock()
        mock_provider.parse_navigation_request = AsyncMock(
            return_value={"start": "北京", "end": "上海"}
        )
        
        result = await parse_navigation_request("从北京到上海", mock_provider)
        
        assert result == {"start": "北京", "end": "上海"}
    
    @pytest.mark.asyncio
    async def test_parse_navigation_request_error(self):
        mock_provider = Mock()
        mock_provider.parse_navigation_request = AsyncMock(
            side_effect=Exception("Parse error")
        )
        
        with pytest.raises(Exception, match="Parse error"):
            await parse_navigation_request("invalid", mock_provider)


class TestOpenBrowserNavigation:
    
    @pytest.mark.asyncio
    async def test_open_browser_navigation_success(self):
        start_coords = {
            "name": "北京",
            "longitude": 116.397128,
            "latitude": 39.916527
        }
        end_coords = {
            "name": "上海",
            "longitude": 121.473701,
            "latitude": 31.230416
        }
        
        with patch('webbrowser.open') as mock_open:
            result = await open_browser_navigation(start_coords, end_coords)
            
            assert result["success"] is True
            assert "北京" in result["message"]
            assert "上海" in result["message"]
            assert "url" in result
            mock_open.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_open_browser_navigation_url_format(self):
        start_coords = {
            "name": "起点",
            "longitude": 100.0,
            "latitude": 50.0
        }
        end_coords = {
            "name": "终点",
            "longitude": 110.0,
            "latitude": 60.0
        }
        
        with patch('webbrowser.open') as mock_open:
            result = await open_browser_navigation(start_coords, end_coords)
            
            url = mock_open.call_args[0][0]
            assert "100.0" in url
            assert "50.0" in url
            assert "110.0" in url
            assert "60.0" in url
            assert "amap.com" in url


class TestMain:
    
    @pytest.mark.asyncio
    async def test_main_missing_api_key(self):
        with patch('map_navigator.main.create_ai_provider', side_effect=ValueError("API key missing")):
            with patch('builtins.print'):
                await main()
    
    @pytest.mark.asyncio
    async def test_main_text_input_success(self):
        mock_ai_provider = Mock()
        mock_ai_provider.parse_navigation_request = AsyncMock(
            return_value={"start": "北京", "end": "上海"}
        )
        
        mock_mcp_client = Mock()
        mock_tool = Mock()
        mock_tool.name = "geocode"
        mock_mcp_client.list_tools = Mock(return_value=[mock_tool])
        mock_mcp_client.is_connected = Mock(return_value=True)
        
        mock_result = {
            "content": [{
                "text": json.dumps({
                    "status": "success",
                    "location": {"longitude": 116.397128, "latitude": 39.916527},
                    "formatted_address": "北京市"
                })
            }]
        }
        mock_mcp_client.call_tool = AsyncMock(return_value=mock_result)
        mock_mcp_client.disconnect = AsyncMock()
        
        with patch('map_navigator.main.create_ai_provider', return_value=mock_ai_provider):
            with patch('map_navigator.main.create_mcp_client', new_callable=AsyncMock, return_value=mock_mcp_client):
                with patch('builtins.input', side_effect=["1", "从北京到上海"]):
                    with patch('builtins.print'):
                        with patch('webbrowser.open'):
                            with patch.dict('os.environ', {"AMAP_MCP_SERVER_URL": "https://test.com"}):
                                await main()
    
    @pytest.mark.asyncio
    async def test_main_voice_input_selected(self):
        mock_ai_provider = Mock()
        
        with patch('map_navigator.main.create_ai_provider', return_value=mock_ai_provider):
            with patch('map_navigator.main.get_voice_input', new_callable=AsyncMock, return_value=None):
                with patch('builtins.input', return_value="2"):
                    with patch('builtins.print'):
                        await main()
    
    @pytest.mark.asyncio
    async def test_main_empty_input(self):
        mock_ai_provider = Mock()
        
        with patch('map_navigator.main.create_ai_provider', return_value=mock_ai_provider):
            with patch('builtins.input', side_effect=["1", ""]):
                with patch('builtins.print'):
                    await main()
    
    @pytest.mark.asyncio
    async def test_main_parse_request_failure(self):
        mock_ai_provider = Mock()
        mock_ai_provider.parse_navigation_request = AsyncMock(
            side_effect=Exception("Parse error")
        )
        
        mock_amap_client = Mock()
        mock_amap_client.__aenter__ = AsyncMock(return_value=mock_amap_client)
        mock_amap_client.__aexit__ = AsyncMock()
        
        with patch('map_navigator.main.create_ai_provider', return_value=mock_ai_provider):
            with patch('map_navigator.main.create_amap_client', return_value=mock_amap_client):
                with patch('builtins.input', side_effect=["1", "invalid input"]):
                    with patch('builtins.print'):
                        with patch.dict('os.environ', {}, clear=True):
                            await main()
    
    @pytest.mark.asyncio
    async def test_main_fallback_to_amap_client(self):
        mock_ai_provider = Mock()
        mock_ai_provider.parse_navigation_request = AsyncMock(
            return_value={"start": "北京", "end": "上海"}
        )
        
        mock_amap_client = Mock()
        mock_amap_client.__aenter__ = AsyncMock(return_value=mock_amap_client)
        mock_amap_client.__aexit__ = AsyncMock()
        mock_amap_client.geocode = AsyncMock(return_value={
            "name": "北京",
            "longitude": 116.397128,
            "latitude": 39.916527
        })
        
        with patch('map_navigator.main.create_ai_provider', return_value=mock_ai_provider):
            with patch('map_navigator.main.create_amap_client', return_value=mock_amap_client):
                with patch('builtins.input', side_effect=["1", "从北京到上海"]):
                    with patch('builtins.print'):
                        with patch('webbrowser.open'):
                            with patch.dict('os.environ', {}, clear=True):
                                await main()
