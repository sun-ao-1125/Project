#!/usr/bin/env python3
"""
AI Provider Abstraction Layer
Supports multiple AI providers: Anthropic Claude and OpenAI-compatible APIs
"""

import os
import json
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from anthropic import Anthropic
import httpx


class AIProvider(ABC):
    @abstractmethod
    async def parse_navigation_request(self, user_input: str) -> dict:
        """Parse user's navigation request and extract locations."""
        pass
    
    @abstractmethod
    async def select_mcp_tool(
        self,
        user_intent: str,
        available_tools: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Intelligently select the most appropriate MCP tool based on user intent.
        
        Args:
            user_intent: Description of what the user wants to accomplish
            available_tools: List of available MCP tools with their descriptions and parameters
            context: Optional additional context (e.g., user preferences, location, etc.)
        
        Returns:
            {
                "tool_name": str,  # Name of the selected tool
                "arguments": dict,  # Arguments to pass to the tool
                "reasoning": str   # Explanation of why this tool was chosen
            }
        """
        pass
    
    @abstractmethod
    async def parse_mcp_response(
        self,
        raw_response: Dict[str, Any],
        expected_info: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Parse and extract information from MCP tool response using AI understanding.
        
        Args:
            raw_response: The raw response from an MCP tool
            expected_info: Description of what information to extract
            context: Optional context about what the information will be used for
        
        Returns:
            Extracted and structured information as a dictionary
        """
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
    
    async def select_mcp_tool(
        self,
        user_intent: str,
        available_tools: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        tools_description = json.dumps(available_tools, indent=2, ensure_ascii=False)
        context_str = json.dumps(context, ensure_ascii=False) if context else "None"
        
        prompt = f"""You are an intelligent tool selector. Based on the user's intent and available MCP tools, select the most appropriate tool and generate the correct arguments.

User Intent: {user_intent}

Available Tools:
{tools_description}

Context: {context_str}

Analyze the intent and select the best tool. Return a JSON object with:
- tool_name: The name of the selected tool
- arguments: A dictionary of arguments for the tool
- reasoning: Brief explanation of why you chose this tool

Response format:
{{
  "tool_name": "selected_tool_name",
  "arguments": {{"param1": "value1"}},
  "reasoning": "explanation"
}}

Only return the JSON, no other text."""

        message = self.client.messages.create(
            model=self.model,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = message.content[0].text.strip()
        return self._parse_json_response(response_text)
    
    async def parse_mcp_response(
        self,
        raw_response: Dict[str, Any],
        expected_info: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        response_str = json.dumps(raw_response, indent=2, ensure_ascii=False)
        context_str = json.dumps(context, ensure_ascii=False) if context else "None"
        
        prompt = f"""You are an intelligent response parser. Extract the requested information from the MCP tool response.

MCP Tool Response:
{response_str}

Expected Information: {expected_info}

Context: {context_str}

Analyze the response and extract the requested information. Return a JSON object with the extracted data in a clean, structured format.

Example for location coordinates:
{{
  "name": "location name",
  "longitude": 116.123,
  "latitude": 39.456,
  "formatted_address": "full address"
}}

Only return the JSON, no other text."""

        message = self.client.messages.create(
            model=self.model,
            max_tokens=500,
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
    
    async def select_mcp_tool(
        self,
        user_intent: str,
        available_tools: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        tools_description = json.dumps(available_tools, indent=2, ensure_ascii=False)
        context_str = json.dumps(context, ensure_ascii=False) if context else "None"
        
        prompt = f"""You are an intelligent tool selector. Based on the user's intent and available MCP tools, select the most appropriate tool and generate the correct arguments.

User Intent: {user_intent}

Available Tools:
{tools_description}

Context: {context_str}

Analyze the intent and select the best tool. Return a JSON object with:
- tool_name: The name of the selected tool
- arguments: A dictionary of arguments for the tool
- reasoning: Brief explanation of why you chose this tool

Response format:
{{
  "tool_name": "selected_tool_name",
  "arguments": {{"param1": "value1"}},
  "reasoning": "explanation"
}}

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
            "max_tokens": 500,
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
    
    async def parse_mcp_response(
        self,
        raw_response: Dict[str, Any],
        expected_info: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        response_str = json.dumps(raw_response, indent=2, ensure_ascii=False)
        context_str = json.dumps(context, ensure_ascii=False) if context else "None"
        
        prompt = f"""You are an intelligent response parser. Extract the requested information from the MCP tool response.

MCP Tool Response:
{response_str}

Expected Information: {expected_info}

Context: {context_str}

Analyze the response and extract the requested information. Return a JSON object with the extracted data in a clean, structured format.

Example for location coordinates:
{{
  "name": "location name",
  "longitude": 116.123,
  "latitude": 39.456,
  "formatted_address": "full address"
}}

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
            "max_tokens": 500,
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
