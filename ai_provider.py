#!/usr/bin/env python3
"""
AI Provider Abstraction Layer
Supports multiple AI providers: Anthropic Claude and OpenAI-compatible APIs
"""

import os
import json
from abc import ABC, abstractmethod
from typing import Dict, Any
from anthropic import Anthropic
import httpx


class AIProvider(ABC):
    @abstractmethod
    async def parse_navigation_request(self, user_input: str) -> dict:
        """Parse user's navigation request and extract locations."""
        pass


class ClaudeProvider(AIProvider):
    def __init__(self, api_key: str):
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-3-5-sonnet-20241022"
    
    async def parse_navigation_request(self, user_input: str) -> dict:
        prompt = f"""Parse this navigation request and extract the start location (A) and end location (B).
Return a JSON object with 'start' and 'end' keys.

User request: {user_input}

Response format:
{{"start": "location A", "end": "location B"}}

Only return the JSON, no other text."""

        message = self.client.messages.create(
            model=self.model,
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = message.content[0].text.strip()
        return self._parse_json_response(response_text)
    
    def _parse_json_response(self, response_text: str) -> dict:
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            import re
            json_match = re.search(r'\{[^}]+\}', response_text)
            if json_match:
                return json.loads(json_match.group())
            raise ValueError("Failed to parse AI response")


class OpenAICompatibleProvider(AIProvider):
    def __init__(self, api_key: str, base_url: str, model: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.model = model
    
    async def parse_navigation_request(self, user_input: str) -> dict:
        prompt = f"""Parse this navigation request and extract the start location (A) and end location (B).
Return a JSON object with 'start' and 'end' keys.

User request: {user_input}

Response format:
{{"start": "location A", "end": "location B"}}

Only return the JSON, no other text."""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 200,
            "temperature": 0.7
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = await response.aread()
            data = json.loads(data.decode('utf-8'))
            
            response_text = data["choices"][0]["message"]["content"].strip()
            return self._parse_json_response(response_text)
    
    def _parse_json_response(self, response_text: str) -> dict:
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            import re
            json_match = re.search(r'\{[^}]+\}', response_text)
            if json_match:
                return json.loads(json_match.group())
            raise ValueError("Failed to parse AI response")


def create_ai_provider() -> AIProvider:
    """
    Factory function to create appropriate AI provider based on environment variables.
    
    Environment variables:
    - AI_PROVIDER: 'anthropic' or 'openai' (default: 'anthropic')
    - ANTHROPIC_API_KEY: API key for Claude (required if AI_PROVIDER='anthropic')
    - OPENAI_API_KEY: API key for OpenAI-compatible service (required if AI_PROVIDER='openai')
    - OPENAI_BASE_URL: Base URL for OpenAI-compatible API (required if AI_PROVIDER='openai')
    - OPENAI_MODEL: Model name to use (default: 'gpt-3.5-turbo')
    """
    provider_type = os.getenv("AI_PROVIDER", "anthropic").lower()
    
    if provider_type == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        return ClaudeProvider(api_key)
    
    elif provider_type == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL")
        model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        if not base_url:
            raise ValueError("OPENAI_BASE_URL environment variable not set")
        
        return OpenAICompatibleProvider(api_key, base_url, model)
    
    else:
        raise ValueError(f"Unsupported AI provider: {provider_type}. Use 'anthropic' or 'openai'")
