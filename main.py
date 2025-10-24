#!/usr/bin/env python3
"""
AI Map Navigator - Main Application
Coordinates between AI, Amap MCP server, and browser control MCP server.
"""

import asyncio
import os
import json
from anthropic import Anthropic
from amap_mcp_client import create_amap_client

async def get_location_coordinates(location_name: str, amap_client) -> dict:
    """
    Get coordinates for a location using Amap MCP server.
    
    Args:
        location_name: Name of the location to geocode
        amap_client: Amap MCP client instance
        
    Returns:
        Dictionary with location coordinates
    """
    try:
        result = await amap_client.geocode(location_name)
        return result
    except Exception as e:
        raise ValueError(f"Failed to geocode location '{location_name}': {str(e)}")

async def parse_navigation_request(user_input: str, client: Anthropic) -> dict:
    """
    Use AI to parse user's navigation request and extract locations.
    """
    prompt = f"""Parse this navigation request and extract the start location (A) and end location (B).
Return a JSON object with 'start' and 'end' keys.

User request: {user_input}

Response format:
{{"start": "location A", "end": "location B"}}

Only return the JSON, no other text."""

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}]
    )
    
    response_text = message.content[0].text.strip()
    
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        import re
        json_match = re.search(r'\{[^}]+\}', response_text)
        if json_match:
            return json.loads(json_match.group())
        raise ValueError("Failed to parse AI response")

async def open_browser_navigation(start_coords: dict, end_coords: dict):
    """
    Use browser control MCP server to open navigation.
    For now, we directly open the browser.
    """
    import webbrowser
    
    url = (
        f"https://uri.amap.com/navigation?"
        f"from={start_coords['longitude']},{start_coords['latitude']}&"
        f"to={end_coords['longitude']},{end_coords['latitude']}&"
        f"mode=car&policy=1&src=ai-navigator&coordinate=gaode&callnative=0"
    )
    
    webbrowser.open(url)
    
    return {
        "success": True,
        "message": f"Navigation opened from {start_coords['name']} to {end_coords['name']}",
        "url": url
    }

async def main():
    """Main application flow."""
    print("=== AI Map Navigator (MCP Architecture) ===\n")
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        print("Please set it with: export ANTHROPIC_API_KEY='your-api-key'")
        return
    
    client = Anthropic(api_key=api_key)
    
    print("Enter your navigation request (e.g., '从北京到上海', '我要从广州去深圳'):")
    user_input = input("> ").strip()
    
    if not user_input:
        print("No input provided.")
        return
    
    print(f"\n[1/5] Connecting to Amap MCP server...")
    amap_client = create_amap_client()
    
    async with amap_client:
        print("✓ Connected to Amap MCP server")
        
        print(f"\n[2/5] Parsing request with AI...")
        try:
            locations = await parse_navigation_request(user_input, client)
            print(f"✓ Parsed: {locations['start']} → {locations['end']}")
        except Exception as e:
            print(f"✗ Failed to parse request: {e}")
            return
        
        print(f"\n[3/5] Getting coordinates for start location via MCP...")
        try:
            start_coords = await get_location_coordinates(locations['start'], amap_client)
            print(f"✓ Start: {start_coords['name']} ({start_coords['longitude']}, {start_coords['latitude']})")
        except Exception as e:
            print(f"✗ Failed to get start coordinates: {e}")
            return
        
        print(f"\n[4/5] Getting coordinates for end location via MCP...")
        try:
            end_coords = await get_location_coordinates(locations['end'], amap_client)
            print(f"✓ End: {end_coords['name']} ({end_coords['longitude']}, {end_coords['latitude']})")
        except Exception as e:
            print(f"✗ Failed to get end coordinates: {e}")
            return
        
        print(f"\n[5/5] Opening navigation in browser...")
        try:
            result = await open_browser_navigation(start_coords, end_coords)
            print(f"✓ {result['message']}")
            print(f"\nNavigation URL: {result['url']}")
        except Exception as e:
            print(f"✗ Failed to open navigation: {e}")
            return
        
        print("\n=== Navigation request completed successfully! ===")

if __name__ == "__main__":
    asyncio.run(main())
