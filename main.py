#!/usr/bin/env python3
"""
AI Map Navigator - Main Application
Coordinates between AI, Amap MCP server, and browser control MCP server.
"""

import asyncio
import os
from ai_provider import create_ai_provider
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

async def parse_navigation_request(user_input: str, ai_provider) -> dict:
    """
    Use AI to parse user's navigation request and extract locations.
    """
    return await ai_provider.parse_navigation_request(user_input)

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
    
    try:
        ai_provider = create_ai_provider()
        provider_type = os.getenv("AI_PROVIDER", "anthropic")
        print(f"Using AI provider: {provider_type}")
    except ValueError as e:
        print(f"Error: {e}")
        print("\nConfiguration guide:")
        print("- For Anthropic Claude:")
        print("  export AI_PROVIDER='anthropic'")
        print("  export ANTHROPIC_API_KEY='your-api-key'")
        print("- For OpenAI-compatible APIs (e.g., Qiniu):")
        print("  export AI_PROVIDER='openai'")
        print("  export OPENAI_API_KEY='your-api-key'")
        print("  export OPENAI_BASE_URL='https://api.example.com/v1'")
        print("  export OPENAI_MODEL='gpt-3.5-turbo'  # optional")
        return
    
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
            locations = await parse_navigation_request(user_input, ai_provider)
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
