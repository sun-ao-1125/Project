"""
Integration tests for AI+MCP architecture.
Tests the end-to-end flow of AI-driven tool selection and response parsing.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from ai_navigator.ai_provider import ClaudeProvider, OpenAICompatibleProvider
from ai_navigator.main import get_location_coordinates_ai_driven


class TestAIMCPIntegration:
    """Integration tests for AI+MCP flow"""
    
    @pytest.mark.asyncio
    async def test_ai_driven_location_lookup_full_flow(self):
        """Test complete AI-driven location lookup flow"""
        
        # Mock MCP client
        mock_mcp_client = Mock()
        mock_tool = Mock()
        mock_tool.name = "maps_geo"
        mock_tool.description = "Geocode an address to get coordinates"
        mock_tool.inputSchema = {"address": "string"}
        mock_mcp_client.list_tools.return_value = [mock_tool]
        
        mock_mcp_client.call_tool = AsyncMock(return_value={
            "content": [{
                "text": '{"results": [{"location": "116.397,39.916", "province": "北京", "city": "北京市"}]}'
            }]
        })
        
        # Mock AI provider
        mock_ai = Mock()
        mock_ai.select_mcp_tool = AsyncMock(return_value={
            "tool_name": "maps_geo",
            "arguments": {"address": "北京"},
            "reasoning": "Use geocode tool for address lookup"
        })
        
        mock_ai.parse_mcp_response = AsyncMock(return_value={
            "name": "北京",
            "longitude": 116.397,
            "latitude": 39.916,
            "formatted_address": "北京北京市"
        })
        
        # Execute
        result = await get_location_coordinates_ai_driven(
            location_name="北京",
            mcp_client=mock_mcp_client,
            ai_provider=mock_ai
        )
        
        # Verify
        assert result["name"] == "北京"
        assert result["longitude"] == 116.397
        assert result["latitude"] == 39.916
        assert "formatted_address" in result
        
        # Verify AI was called
        mock_ai.select_mcp_tool.assert_called_once()
        mock_ai.parse_mcp_response.assert_called_once()
        
        # Verify MCP tool was called with AI-selected parameters
        mock_mcp_client.call_tool.assert_called_once_with("maps_geo", {"address": "北京"})
    
    @pytest.mark.asyncio
    async def test_ai_tool_selection_with_context(self):
        """Test AI tool selection uses context for better decisions"""
        
        # Mock MCP client with multiple tools
        mock_mcp_client = Mock()
        mock_tools = [
            Mock(name="maps_geo", description="Geocode address", inputSchema={}),
            Mock(name="maps_text_search", description="Search POI", inputSchema={}),
            Mock(name="get_current_location", description="Get current GPS", inputSchema={})
        ]
        mock_mcp_client.list_tools.return_value = mock_tools
        mock_mcp_client.call_tool = AsyncMock(return_value={"content": [{"text": "{}"}]})
        
        # Mock AI provider
        mock_ai = Mock()
        mock_ai.select_mcp_tool = AsyncMock(return_value={
            "tool_name": "get_current_location",
            "arguments": {},
            "reasoning": "User wants current location, use GPS tool"
        })
        mock_ai.parse_mcp_response = AsyncMock(return_value={
            "name": "当前位置",
            "longitude": 116.0,
            "latitude": 40.0,
            "formatted_address": "北京市"
        })
        
        # Execute with context indicating current location
        result = await get_location_coordinates_ai_driven(
            location_name="当前位置",
            mcp_client=mock_mcp_client,
            ai_provider=mock_ai,
            is_current_location=True
        )
        
        # Verify AI received context
        call_args = mock_ai.select_mcp_tool.call_args
        assert call_args[1]["context"]["is_current_location"] is True
        
        # Verify result
        assert result["name"] == "当前位置"
    
    @pytest.mark.asyncio
    async def test_ai_response_parsing_handles_various_formats(self):
        """Test AI can parse different MCP response formats"""
        
        mock_mcp_client = Mock()
        mock_tool = Mock(name="test_tool", description="Test", inputSchema={})
        mock_mcp_client.list_tools.return_value = [mock_tool]
        
        # Test different response formats
        test_cases = [
            {
                "raw_response": {
                    "content": [{"text": '{"results": [{"location": "120.0,30.0"}]}'}]
                },
                "expected": {"longitude": 120.0, "latitude": 30.0}
            },
            {
                "raw_response": {
                    "content": [{"text": '{"pois": [{"location": "121.0,31.0"}]}'}]
                },
                "expected": {"longitude": 121.0, "latitude": 31.0}
            }
        ]
        
        for test_case in test_cases:
            mock_mcp_client.call_tool = AsyncMock(return_value=test_case["raw_response"])
            
            mock_ai = Mock()
            mock_ai.select_mcp_tool = AsyncMock(return_value={
                "tool_name": "test_tool",
                "arguments": {},
                "reasoning": "test"
            })
            mock_ai.parse_mcp_response = AsyncMock(return_value=test_case["expected"])
            
            result = await get_location_coordinates_ai_driven(
                "test_location",
                mock_mcp_client,
                mock_ai
            )
            
            assert result["longitude"] == test_case["expected"]["longitude"]
            assert result["latitude"] == test_case["expected"]["latitude"]
    
    @pytest.mark.asyncio
    async def test_error_handling_in_ai_driven_flow(self):
        """Test error handling in AI-driven flow"""
        
        mock_mcp_client = Mock()
        mock_mcp_client.list_tools.return_value = []
        
        mock_ai = Mock()
        mock_ai.select_mcp_tool = AsyncMock(side_effect=Exception("AI selection failed"))
        
        with pytest.raises(ValueError, match="Failed to get coordinates"):
            await get_location_coordinates_ai_driven(
                "test_location",
                mock_mcp_client,
                mock_ai
            )
    
    @pytest.mark.asyncio
    async def test_ai_reasoning_is_logged(self, capsys):
        """Test that AI reasoning is displayed to user"""
        
        mock_mcp_client = Mock()
        mock_tool = Mock(name="test_tool", description="Test", inputSchema={})
        mock_mcp_client.list_tools.return_value = [mock_tool]
        mock_mcp_client.call_tool = AsyncMock(return_value={"content": [{"text": "{}"}]})
        
        mock_ai = Mock()
        reasoning = "Chose test_tool because it's the best match"
        mock_ai.select_mcp_tool = AsyncMock(return_value={
            "tool_name": "test_tool",
            "arguments": {},
            "reasoning": reasoning
        })
        mock_ai.parse_mcp_response = AsyncMock(return_value={
            "name": "test",
            "longitude": 0.0,
            "latitude": 0.0
        })
        
        await get_location_coordinates_ai_driven(
            "test",
            mock_mcp_client,
            mock_ai
        )
        
        captured = capsys.readouterr()
        assert "AI selected tool: test_tool" in captured.out
        assert reasoning in captured.out


class TestAIProviderMethods:
    """Test AI provider methods for tool selection and response parsing"""
    
    @pytest.mark.asyncio
    async def test_select_mcp_tool_claude(self):
        """Test Claude provider's select_mcp_tool method"""
        
        # Skip if no API key
        import os
        if not os.getenv("ANTHROPIC_API_KEY"):
            pytest.skip("ANTHROPIC_API_KEY not set")
        
        provider = ClaudeProvider(os.getenv("ANTHROPIC_API_KEY"))
        
        available_tools = [
            {
                "name": "geocode",
                "description": "Convert address to coordinates",
                "parameters": {"address": "string"}
            }
        ]
        
        result = await provider.select_mcp_tool(
            user_intent="Get coordinates for Beijing",
            available_tools=available_tools
        )
        
        assert "tool_name" in result
        assert "arguments" in result
        assert "reasoning" in result
        assert result["tool_name"] == "geocode"
    
    @pytest.mark.asyncio
    async def test_parse_mcp_response_claude(self):
        """Test Claude provider's parse_mcp_response method"""
        
        # Skip if no API key
        import os
        if not os.getenv("ANTHROPIC_API_KEY"):
            pytest.skip("ANTHROPIC_API_KEY not set")
        
        provider = ClaudeProvider(os.getenv("ANTHROPIC_API_KEY"))
        
        raw_response = {
            "content": [{
                "text": '{"results": [{"location": "116.397,39.916", "province": "北京", "city": "北京市"}]}'
            }]
        }
        
        result = await provider.parse_mcp_response(
            raw_response=raw_response,
            expected_info="Extract longitude, latitude, and formatted address"
        )
        
        assert "longitude" in result or "latitude" in result
