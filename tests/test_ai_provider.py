#!/usr/bin/env python3
import pytest
import json
import os
from unittest.mock import Mock, patch, AsyncMock
from map_navigator.ai_provider import (
    ClaudeProvider,
    OpenAICompatibleProvider,
    create_ai_provider
)


class TestClaudeProvider:
    
    @pytest.mark.asyncio
    async def test_parse_navigation_request_success(self):
        provider = ClaudeProvider(api_key="test-key")
        
        mock_message = Mock()
        mock_message.content = [Mock(text='{"start": "北京", "end": "上海"}')]
        
        with patch.object(provider.client.messages, 'create', return_value=mock_message):
            result = await provider.parse_navigation_request("从北京到上海")
            
            assert result == {"start": "北京", "end": "上海"}
    
    @pytest.mark.asyncio
    async def test_parse_navigation_request_with_embedded_json(self):
        provider = ClaudeProvider(api_key="test-key")
        
        mock_message = Mock()
        mock_message.content = [Mock(text='Here is the result: {"start": "广州", "end": "深圳"} done')]
        
        with patch.object(provider.client.messages, 'create', return_value=mock_message):
            result = await provider.parse_navigation_request("从广州到深圳")
            
            assert result == {"start": "广州", "end": "深圳"}
    
    def test_parse_json_response_valid_json(self):
        provider = ClaudeProvider(api_key="test-key")
        result = provider._parse_json_response('{"start": "A", "end": "B"}')
        assert result == {"start": "A", "end": "B"}
    
    def test_parse_json_response_invalid_json_raises_error(self):
        provider = ClaudeProvider(api_key="test-key")
        with pytest.raises(ValueError, match="Failed to parse AI response"):
            provider._parse_json_response("not a json string")
    
    def test_parse_json_response_extracts_json_from_text(self):
        provider = ClaudeProvider(api_key="test-key")
        result = provider._parse_json_response('Some text {"key": "value"} more text')
        assert result == {"key": "value"}


class TestOpenAICompatibleProvider:
    
    @pytest.mark.asyncio
    async def test_parse_navigation_request_success(self):
        provider = OpenAICompatibleProvider(
            api_key="test-key",
            base_url="https://api.test.com/v1",
            model="gpt-3.5-turbo"
        )
        
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.aread = AsyncMock(return_value=json.dumps({
            "choices": [{"message": {"content": '{"start": "杭州", "end": "南京"}'}}]
        }).encode('utf-8'))
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            result = await provider.parse_navigation_request("从杭州到南京")
            
            assert result == {"start": "杭州", "end": "南京"}
    
    @pytest.mark.asyncio
    async def test_parse_navigation_request_http_error(self):
        provider = OpenAICompatibleProvider(
            api_key="test-key",
            base_url="https://api.test.com/v1",
            model="gpt-3.5-turbo"
        )
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=Exception("HTTP Error")
            )
            
            with pytest.raises(Exception, match="HTTP Error"):
                await provider.parse_navigation_request("test")
    
    def test_parse_json_response_valid_json(self):
        provider = OpenAICompatibleProvider(
            api_key="test-key",
            base_url="https://api.test.com",
            model="test-model"
        )
        result = provider._parse_json_response('{"start": "C", "end": "D"}')
        assert result == {"start": "C", "end": "D"}
    
    def test_parse_json_response_invalid_json_raises_error(self):
        provider = OpenAICompatibleProvider(
            api_key="test-key",
            base_url="https://api.test.com",
            model="test-model"
        )
        with pytest.raises(ValueError, match="Failed to parse AI response"):
            provider._parse_json_response("invalid json")
    
    def test_base_url_rstrip_slash(self):
        provider = OpenAICompatibleProvider(
            api_key="test-key",
            base_url="https://api.test.com/v1/",
            model="test-model"
        )
        assert provider.base_url == "https://api.test.com/v1"


class TestCreateAIProvider:
    
    def test_create_anthropic_provider_success(self):
        with patch.dict(os.environ, {"AI_PROVIDER": "anthropic", "ANTHROPIC_API_KEY": "test-key"}):
            provider = create_ai_provider()
            assert isinstance(provider, ClaudeProvider)
    
    def test_create_anthropic_provider_missing_key(self):
        with patch.dict(os.environ, {"AI_PROVIDER": "anthropic"}, clear=True):
            with pytest.raises(ValueError, match="ANTHROPIC_API_KEY environment variable not set"):
                create_ai_provider()
    
    def test_create_openai_provider_success(self):
        with patch.dict(os.environ, {
            "AI_PROVIDER": "openai",
            "OPENAI_API_KEY": "test-key",
            "OPENAI_BASE_URL": "https://api.test.com",
            "OPENAI_MODEL": "gpt-4"
        }):
            provider = create_ai_provider()
            assert isinstance(provider, OpenAICompatibleProvider)
            assert provider.model == "gpt-4"
    
    def test_create_openai_provider_missing_api_key(self):
        with patch.dict(os.environ, {
            "AI_PROVIDER": "openai",
            "OPENAI_BASE_URL": "https://api.test.com"
        }, clear=True):
            with pytest.raises(ValueError, match="OPENAI_API_KEY environment variable not set"):
                create_ai_provider()
    
    def test_create_openai_provider_missing_base_url(self):
        with patch.dict(os.environ, {
            "AI_PROVIDER": "openai",
            "OPENAI_API_KEY": "test-key"
        }, clear=True):
            with pytest.raises(ValueError, match="OPENAI_BASE_URL environment variable not set"):
                create_ai_provider()
    
    def test_create_provider_default_to_anthropic(self):
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}, clear=True):
            provider = create_ai_provider()
            assert isinstance(provider, ClaudeProvider)
    
    def test_create_provider_unsupported_type(self):
        with patch.dict(os.environ, {"AI_PROVIDER": "unsupported"}, clear=True):
            with pytest.raises(ValueError, match="Unsupported AI provider: unsupported"):
                create_ai_provider()
