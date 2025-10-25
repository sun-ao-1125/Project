#!/usr/bin/env python3
import pytest
import uuid
from unittest.mock import Mock, patch, AsyncMock
from ai_navigator.mcp_client import (
    TransportType,
    AuthType,
    MCPConfig,
    Tool,
    Resource,
    Prompt,
    HTTPSSETransport,
    StreamableHTTPTransport,
    StdioTransport,
    WebSocketTransport,
    MCPClient,
    create_mcp_client
)


class TestMCPConfig:
    
    def test_default_config(self):
        config = MCPConfig()
        
        assert config.server_url is None
        assert config.transport_type == TransportType.HTTP_SSE
        assert config.auth_type == AuthType.NONE
        assert config.timeout == 30
        assert config.max_retries == 3
    
    def test_custom_config(self):
        config = MCPConfig(
            server_url="https://test.com",
            transport_type=TransportType.WEBSOCKET,
            auth_type=AuthType.BEARER,
            auth_token="test-token",
            timeout=60
        )
        
        assert config.server_url == "https://test.com"
        assert config.transport_type == TransportType.WEBSOCKET
        assert config.auth_type == AuthType.BEARER
        assert config.auth_token == "test-token"
        assert config.timeout == 60


class TestHTTPSSETransport:
    
    @pytest.mark.asyncio
    async def test_connect_success(self):
        config = MCPConfig(server_url="https://test.com")
        transport = HTTPSSETransport(config)
        
        with patch('httpx.AsyncClient'):
            result = await transport.connect()
            
            assert result is True
            assert transport.connected is True
    
    @pytest.mark.asyncio
    async def test_connect_failure(self):
        config = MCPConfig(server_url="https://test.com")
        transport = HTTPSSETransport(config)
        
        with patch('httpx.AsyncClient', side_effect=Exception("Connection error")):
            result = await transport.connect()
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_disconnect(self):
        config = MCPConfig(server_url="https://test.com")
        transport = HTTPSSETransport(config)
        transport.client = Mock()
        transport.client.aclose = AsyncMock()
        transport.connected = True
        
        await transport.disconnect()
        
        assert transport.connected is False
        assert transport.client is None
    
    @pytest.mark.asyncio
    async def test_send_request_success(self):
        config = MCPConfig(server_url="https://test.com")
        transport = HTTPSSETransport(config)
        transport.connected = True
        transport.client = Mock()
        
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json = Mock(return_value={"result": {"data": "test"}})
        transport.client.post = AsyncMock(return_value=mock_response)
        
        result = await transport.send_request("test_method", {"param": "value"})
        
        assert result == {"data": "test"}
    
    @pytest.mark.asyncio
    async def test_send_request_not_connected(self):
        config = MCPConfig(server_url="https://test.com")
        transport = HTTPSSETransport(config)
        
        with pytest.raises(ConnectionError, match="Not connected to server"):
            await transport.send_request("test", {})
    
    @pytest.mark.asyncio
    async def test_send_request_with_bearer_auth(self):
        config = MCPConfig(
            server_url="https://test.com",
            auth_type=AuthType.BEARER,
            auth_token="test-token"
        )
        transport = HTTPSSETransport(config)
        transport.connected = True
        transport.client = Mock()
        
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json = Mock(return_value={"result": {}})
        transport.client.post = AsyncMock(return_value=mock_response)
        
        await transport.send_request("test", {})
        
        call_args = transport.client.post.call_args
        headers = call_args[1]["headers"]
        assert headers["Authorization"] == "Bearer test-token"
    
    @pytest.mark.asyncio
    async def test_send_request_with_api_key_auth(self):
        config = MCPConfig(
            server_url="https://test.com",
            auth_type=AuthType.API_KEY,
            auth_token="api-key-value"
        )
        transport = HTTPSSETransport(config)
        transport.connected = True
        transport.client = Mock()
        
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json = Mock(return_value={"result": {}})
        transport.client.post = AsyncMock(return_value=mock_response)
        
        await transport.send_request("test", {})
        
        call_args = transport.client.post.call_args
        headers = call_args[1]["headers"]
        assert headers["X-API-Key"] == "api-key-value"
    
    @pytest.mark.asyncio
    async def test_send_request_server_error(self):
        config = MCPConfig(server_url="https://test.com")
        transport = HTTPSSETransport(config)
        transport.connected = True
        transport.client = Mock()
        
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json = Mock(return_value={"error": {"message": "Server error"}})
        transport.client.post = AsyncMock(return_value=mock_response)
        
        with pytest.raises(Exception, match="Server error"):
            await transport.send_request("test", {})
    
    def test_generate_request_id(self):
        config = MCPConfig()
        transport = HTTPSSETransport(config)
        
        request_id = transport._generate_request_id()
        
        assert isinstance(request_id, str)
        uuid.UUID(request_id)


class TestStreamableHTTPTransport:
    
    @pytest.mark.asyncio
    async def test_connect_success(self):
        config = MCPConfig(server_url="https://test.com")
        transport = StreamableHTTPTransport(config)
        
        with patch('httpx.AsyncClient'):
            result = await transport.connect()
            
            assert result is True
            assert transport.connected is True
    
    @pytest.mark.asyncio
    async def test_send_request_success(self):
        config = MCPConfig(server_url="https://test.com")
        transport = StreamableHTTPTransport(config)
        transport.connected = True
        transport.client = Mock()
        
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        
        async def mock_aiter_bytes():
            yield b'{"result": {"data": "test"}}'
        
        mock_response.aiter_bytes = mock_aiter_bytes
        
        mock_stream = AsyncMock()
        mock_stream.__aenter__.return_value = mock_response
        mock_stream.__aexit__.return_value = None
        transport.client.stream = Mock(return_value=mock_stream)
        
        result = await transport.send_request("test_method", {})
        
        assert result == {"data": "test"}


class TestMCPClient:
    
    @pytest.mark.asyncio
    async def test_connect_success(self):
        config = MCPConfig(server_url="https://test.com")
        client = MCPClient(config)
        
        mock_transport = Mock()
        mock_transport.connect = AsyncMock(return_value=True)
        mock_transport.send_request = AsyncMock(return_value={
            "serverInfo": {"name": "test-server"},
            "capabilities": {"tools": True}
        })
        
        with patch.object(client, '_create_transport', return_value=mock_transport):
            with patch.object(client, '_discover_capabilities', new_callable=AsyncMock):
                result = await client.connect()
                
                assert result is True
                assert client.connected is True
    
    @pytest.mark.asyncio
    async def test_connect_failure(self):
        config = MCPConfig(server_url="https://test.com")
        client = MCPClient(config)
        
        mock_transport = Mock()
        mock_transport.connect = AsyncMock(return_value=False)
        
        with patch.object(client, '_create_transport', return_value=mock_transport):
            with patch.object(client, '_handle_reconnect', new_callable=AsyncMock):
                result = await client.connect()
                
                assert result is False
    
    @pytest.mark.asyncio
    async def test_disconnect(self):
        config = MCPConfig()
        client = MCPClient(config)
        client.transport = Mock()
        client.transport.disconnect = AsyncMock()
        client.connected = True
        
        await client.disconnect()
        
        assert client.connected is False
    
    def test_create_transport_http_sse(self):
        config = MCPConfig(transport_type=TransportType.HTTP_SSE)
        client = MCPClient(config)
        
        transport = client._create_transport()
        
        assert isinstance(transport, HTTPSSETransport)
    
    def test_create_transport_http_stream(self):
        config = MCPConfig(transport_type=TransportType.HTTP_STREAM)
        client = MCPClient(config)
        
        transport = client._create_transport()
        
        assert isinstance(transport, StreamableHTTPTransport)
    
    def test_create_transport_stdio(self):
        config = MCPConfig(transport_type=TransportType.STDIO)
        client = MCPClient(config)
        
        transport = client._create_transport()
        
        assert isinstance(transport, StdioTransport)
    
    def test_create_transport_websocket(self):
        config = MCPConfig(transport_type=TransportType.WEBSOCKET)
        client = MCPClient(config)
        
        transport = client._create_transport()
        
        assert isinstance(transport, WebSocketTransport)
    
    @pytest.mark.asyncio
    async def test_call_tool_success(self):
        config = MCPConfig()
        client = MCPClient(config)
        client.connected = True
        client.transport = Mock()
        client.transport.send_request = AsyncMock(return_value={"content": "result"})
        client.tools = {"test_tool": Tool(name="test_tool", description="test", parameters={})}
        
        result = await client.call_tool("test_tool", {"arg": "value"})
        
        assert result == {"content": "result"}
    
    @pytest.mark.asyncio
    async def test_call_tool_not_connected(self):
        config = MCPConfig()
        client = MCPClient(config)
        
        with pytest.raises(ConnectionError, match="Not connected to MCP server"):
            await client.call_tool("test", {})
    
    @pytest.mark.asyncio
    async def test_call_tool_not_found(self):
        config = MCPConfig()
        client = MCPClient(config)
        client.connected = True
        
        with pytest.raises(ValueError, match="Tool 'unknown' not found"):
            await client.call_tool("unknown", {})
    
    @pytest.mark.asyncio
    async def test_get_resource_success(self):
        config = MCPConfig()
        client = MCPClient(config)
        client.connected = True
        client.transport = Mock()
        client.transport.send_request = AsyncMock(return_value={"data": "resource_data"})
        
        result = await client.get_resource("test://resource")
        
        assert result == {"data": "resource_data"}
    
    @pytest.mark.asyncio
    async def test_get_prompt_success(self):
        config = MCPConfig()
        client = MCPClient(config)
        client.connected = True
        client.transport = Mock()
        client.transport.send_request = AsyncMock(return_value={"prompt": "test_prompt"})
        client.prompts = {"test": Prompt(name="test", description="test")}
        
        result = await client.get_prompt("test", {"arg": "value"})
        
        assert result == {"prompt": "test_prompt"}
    
    def test_list_tools(self):
        config = MCPConfig()
        client = MCPClient(config)
        client.tools = {
            "tool1": Tool(name="tool1", description="", parameters={}),
            "tool2": Tool(name="tool2", description="", parameters={})
        }
        
        tools = client.list_tools()
        
        assert len(tools) == 2
    
    def test_is_connected(self):
        config = MCPConfig()
        client = MCPClient(config)
        
        assert client.is_connected() is False
        
        client.connected = True
        assert client.is_connected() is True


class TestCreateMCPClient:
    
    @pytest.mark.asyncio
    async def test_create_mcp_client(self):
        with patch('mcp_client.MCPClient') as mock_client_class:
            mock_instance = Mock()
            mock_instance.connect = AsyncMock()
            mock_client_class.return_value = mock_instance
            
            client = await create_mcp_client(
                server_url="https://test.com",
                transport_type=TransportType.HTTP_SSE
            )
            
            assert client == mock_instance
            mock_instance.connect.assert_called_once()
