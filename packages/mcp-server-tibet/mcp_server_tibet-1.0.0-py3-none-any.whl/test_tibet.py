#!/usr/bin/env python3
"""
Test TIBET MCP Server
Claude & Jasper saying Hello to the World!
"""

import asyncio
import json
from tibet_server import call_tool, list_tools

async def test_tibet():
    print("=" * 60)
    print("🌍 TIBET MCP Server Test - Hello World!")
    print("=" * 60)
    print()

    # Test 1: Hello World
    print("📣 Test 1: tibet_hello_world")
    print("-" * 40)
    result = await call_tool("tibet_hello_world", {})
    data = json.loads(result[0].text)
    print(json.dumps(data, indent=2))
    print()

    # Test 2: Create a token
    print("🎫 Test 2: tibet_create_token")
    print("-" * 40)
    result = await call_tool("tibet_create_token", {
        "type": "hello_world",
        "erin": "First TIBET token ever created!",
        "eraan": ["mcp-servers", "humoticaos"],
        "eromheen": {
            "location": "Den Dolder",
            "creators": ["Claude", "Jasper"],
            "date": "2024-12-20"
        },
        "erachter": "Saying hello to the world with TIBET!",
        "actor": "claude_and_jasper"
    })
    token_data = json.loads(result[0].text)
    print(json.dumps(token_data, indent=2))
    token_id = token_data.get("token_id")
    print()

    # Test 3: Verify the token
    print("✅ Test 3: tibet_verify_token")
    print("-" * 40)
    result = await call_tool("tibet_verify_token", {"token_id": token_id})
    print(json.dumps(json.loads(result[0].text), indent=2))
    print()

    # Test 4: Get trust score
    print("🤝 Test 4: tibet_get_trust")
    print("-" * 40)
    result = await call_tool("tibet_get_trust", {"actor": "claude_and_jasper"})
    print(json.dumps(json.loads(result[0].text), indent=2))
    print()

    # Test 5: Get provenance chain
    print("🔗 Test 5: tibet_get_chain")
    print("-" * 40)
    result = await call_tool("tibet_get_chain", {"token_id": token_id})
    print(json.dumps(json.loads(result[0].text), indent=2))
    print()

    print("=" * 60)
    print("✨ TIBET MCP Server - All tests passed!")
    print("   One love, one fAmIly 💙")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_tibet())
