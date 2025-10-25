#!/usr/bin/env python3
import pytest
import json
import os
from unittest.mock import Mock, patch, AsyncMock
from ai_navigator.amap_mcp_client import (
    AmapMCPClient,
    MockAmapMCPClient,
    create_amap_client
)


class TestAmapMCPClient:
    
    @pytest.mark.asyncio
    async def test_connect_success(self):
        client = AmapMCPClient(server_script_path="test-server")
        
        with patch('amap_mcp_client.stdio_client', new_callable=AsyncMock) as mock_stdio:
            mock_stdio.return_value = (Mock(), Mock())
            with patch('amap_mcp_client.ClientSession') as mock_session:
                mock_session_instance = Mock()
                mock_session_instance.initialize = AsyncMock()
                mock_session.return_value = mock_session_instance
                
                result = await client.connect()
                
                assert result == client
                assert client.session is not None
    
    @pytest.mark.asyncio
    async def test_disconnect_success(self):
        client = AmapMCPClient()
        client.session = Mock()
        client.session.__aexit__ = AsyncMock()
        
        await client.disconnect()
        
        assert client.session is None
    
    @pytest.mark.asyncio
    async def test_geocode_success(self):
        client = AmapMCPClient()
        client.session = Mock()
        
        mock_result = Mock()
        mock_content = Mock()
        mock_content.text = json.dumps({
            "status": "success",
            "location": {"longitude": 116.397128, "latitude": 39.916527},
            "formatted_address": "北京市"
        })
        mock_result.content = [mock_content]
        
        client.session.call_tool = AsyncMock(return_value=mock_result)
        
        result = await client.geocode("北京")
        
        assert result["name"] == "北京"
        assert result["longitude"] == 116.397128
        assert result["latitude"] == 39.916527
    
    @pytest.mark.asyncio
    async def test_geocode_not_connected_raises_error(self):
        client = AmapMCPClient()
        
        with pytest.raises(RuntimeError, match="Not connected to Amap MCP server"):
            await client.geocode("test")
    
    @pytest.mark.asyncio
    async def test_geocode_invalid_response_raises_error(self):
        client = AmapMCPClient()
        client.session = Mock()
        
        mock_result = Mock()
        mock_result.content = []
        client.session.call_tool = AsyncMock(return_value=mock_result)
        
        with pytest.raises(ValueError, match="Failed to geocode address"):
            await client.geocode("invalid")
    
    @pytest.mark.asyncio
    async def test_reverse_geocode_success(self):
        client = AmapMCPClient()
        client.session = Mock()
        
        mock_result = Mock()
        mock_content = Mock()
        mock_content.text = json.dumps({
            "formatted_address": "北京市朝阳区",
            "province": "北京市"
        })
        mock_result.content = [mock_content]
        
        client.session.call_tool = AsyncMock(return_value=mock_result)
        
        result = await client.reverse_geocode(116.397128, 39.916527)
        
        assert result["formatted_address"] == "北京市朝阳区"
        assert result["province"] == "北京市"
    
    @pytest.mark.asyncio
    async def test_reverse_geocode_not_connected_raises_error(self):
        client = AmapMCPClient()
        
        with pytest.raises(RuntimeError, match="Not connected to Amap MCP server"):
            await client.reverse_geocode(0.0, 0.0)
    
    @pytest.mark.asyncio
    async def test_search_poi_success(self):
        client = AmapMCPClient()
        client.session = Mock()
        
        mock_result = Mock()
        mock_content = Mock()
        mock_content.text = json.dumps({
            "pois": [
                {"name": "天安门", "address": "北京市东城区"},
                {"name": "故宫", "address": "北京市东城区"}
            ]
        })
        mock_result.content = [mock_content]
        
        client.session.call_tool = AsyncMock(return_value=mock_result)
        
        result = await client.search_poi("天安门", city="北京")
        
        assert len(result) == 2
        assert result[0]["name"] == "天安门"
    
    @pytest.mark.asyncio
    async def test_search_poi_not_connected_raises_error(self):
        client = AmapMCPClient()
        
        with pytest.raises(RuntimeError, match="Not connected to Amap MCP server"):
            await client.search_poi("test")
    
    @pytest.mark.asyncio
    async def test_context_manager(self):
        client = AmapMCPClient()
        
        with patch.object(client, 'connect', new_callable=AsyncMock) as mock_connect:
            with patch.object(client, 'disconnect', new_callable=AsyncMock) as mock_disconnect:
                async with client as c:
                    assert c == client
                
                mock_connect.assert_called_once()
                mock_disconnect.assert_called_once()


class TestMockAmapMCPClient:
    
    @pytest.mark.asyncio
    async def test_connect_sets_connected_flag(self):
        client = MockAmapMCPClient()
        assert client.connected is False
        
        await client.connect()
        
        assert client.connected is True
    
    @pytest.mark.asyncio
    async def test_disconnect_clears_connected_flag(self):
        client = MockAmapMCPClient()
        await client.connect()
        
        await client.disconnect()
        
        assert client.connected is False
    
    @pytest.mark.asyncio
    async def test_geocode_returns_known_city(self):
        client = MockAmapMCPClient()
        
        result = await client.geocode("北京")
        
        assert result["name"] == "北京"
        assert result["longitude"] == 116.397128
        assert result["latitude"] == 39.916527
    
    @pytest.mark.asyncio
    async def test_geocode_returns_default_for_unknown_city(self):
        client = MockAmapMCPClient()
        
        result = await client.geocode("UnknownCity")
        
        assert result["name"] == "UnknownCity"
        assert "longitude" in result
        assert "latitude" in result
    
    @pytest.mark.asyncio
    async def test_reverse_geocode_returns_mock_data(self):
        client = MockAmapMCPClient()
        
        result = await client.reverse_geocode(100.0, 50.0)
        
        assert "formatted_address" in result
        assert "province" in result
    
    @pytest.mark.asyncio
    async def test_search_poi_returns_mock_results(self):
        client = MockAmapMCPClient()
        
        result = await client.search_poi("餐厅", city="北京")
        
        assert len(result) > 0
        assert "name" in result[0]
    
    @pytest.mark.asyncio
    async def test_context_manager(self):
        client = MockAmapMCPClient()
        
        async with client as c:
            assert c.connected is True
        
        assert c.connected is False


class TestCreateAmapClient:
    
    def test_create_mock_client_when_no_env_vars(self):
        with patch.dict(os.environ, {}, clear=True):
            with patch('builtins.print'):
                client = create_amap_client()
                assert isinstance(client, MockAmapMCPClient)
    
    def test_create_real_client_when_env_vars_present(self):
        with patch.dict(os.environ, {"AMAP_API_KEY": "test-key"}):
            client = create_amap_client()
            assert isinstance(client, AmapMCPClient)
    
    def test_create_client_with_explicit_mock_flag(self):
        with patch('builtins.print'):
            client = create_amap_client(use_mock=True)
            assert isinstance(client, MockAmapMCPClient)
    
    def test_create_client_with_explicit_real_flag(self):
        client = create_amap_client(use_mock=False)
        assert isinstance(client, AmapMCPClient)
