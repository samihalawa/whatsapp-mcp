#!/usr/bin/env python3
"""
Proper MCP protocol test using the mcp package
"""

import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_mcp():
    """Test MCP server with proper protocol"""
    
    print("Testing WhatsApp MCP Server via MCP Protocol")
    print("=" * 50)
    
    # Create server parameters
    server_params = StdioServerParameters(
        command="python",
        args=["whatsapp-mcp-server/main.py"],
        env=None
    )
    
    # Connect to server
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize
            print("\n1. Initializing connection...")
            init_result = await session.initialize()
            
            # Get server info from initialization result
            if init_result:
                print(f"✓ Connected to: {init_result.server_info.name}")
                print(f"  Version: {init_result.server_info.version}")
            
            # List available tools
            print("\n2. Listing available tools...")
            tools_result = await session.call("tools/list", {})
            tools = tools_result.get('tools', [])
            
            print(f"✓ Found {len(tools)} tools:")
            for tool in tools[:5]:  # Show first 5
                print(f"  - {tool.name}")
                if tool.description:
                    print(f"    {tool.description[:60]}...")
            
            # Test get_whatsapp_status tool
            print("\n3. Testing get_whatsapp_status tool...")
            result = await session.call("tools/call", {
                "name": "get_whatsapp_status",
                "arguments": {}
            })
            
            if result and 'content' in result:
                content = result['content'][0]
                if 'text' in content:
                    data = json.loads(content['text'])
                    print(f"✓ Status retrieved:")
                    print(f"  Connected: {data.get('connected', False)}")
                    print(f"  Message: {data.get('message', 'No message')}")
            
            # Test search_contacts tool
            print("\n4. Testing search_contacts tool...")
            result = await session.call("tools/call", {
                "name": "search_contacts",
                "arguments": {"query": "test"}
            })
            
            if result and 'content' in result:
                content = result['content'][0]
                if 'text' in content:
                    contacts = json.loads(content['text'])
                    print(f"✓ Found {len(contacts)} contacts")
                    if contacts:
                        print(f"  First: {contacts[0].get('name', 'Unknown')}")
            
            # Test send_message tool (mock)
            print("\n5. Testing send_message tool...")
            result = await session.call("tools/call", {
                "name": "send_message",
                "arguments": {
                    "recipient": "1234567890",
                    "message": "Test message from MCP"
                }
            })
            
            if result and 'content' in result:
                content = result['content'][0]
                if 'text' in content:
                    response = json.loads(content['text'])
                    print(f"✓ Send result:")
                    print(f"  Success: {response.get('success', False)}")
                    print(f"  Message: {response.get('message', 'No message')}")
    
    print("\n" + "=" * 50)
    print("MCP protocol test complete!")

if __name__ == "__main__":
    asyncio.run(test_mcp())