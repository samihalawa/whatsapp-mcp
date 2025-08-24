#!/usr/bin/env python3
"""
Test script for WhatsApp MCP server
"""

import json
import subprocess
import sys

def send_mcp_request(request):
    """Send a request to the MCP server via stdio"""
    process = subprocess.Popen(
        ['python', 'whatsapp-mcp-server/main.py'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Send request
    stdout, stderr = process.communicate(input=json.dumps(request) + '\n')
    
    if stderr:
        print(f"Error: {stderr}", file=sys.stderr)
    
    # Parse response
    for line in stdout.split('\n'):
        if line.strip():
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue
    return None

def test_mcp_server():
    """Test the MCP server functionality"""
    
    print("Testing WhatsApp MCP Server...")
    print("=" * 50)
    
    # Test 1: Initialize
    print("\n1. Testing Initialize...")
    init_request = {
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "protocolVersion": "1.0.0",
            "capabilities": {},
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        },
        "id": 1
    }
    
    response = send_mcp_request(init_request)
    if response:
        print(f"✓ Initialize successful: {response.get('result', {}).get('serverInfo', {}).get('name', 'Unknown')}")
    else:
        print("✗ Initialize failed")
    
    # Test 2: List Tools
    print("\n2. Testing List Tools...")
    list_tools_request = {
        "jsonrpc": "2.0",
        "method": "tools/list",
        "params": {},
        "id": 2
    }
    
    response = send_mcp_request(list_tools_request)
    if response and 'result' in response:
        tools = response['result'].get('tools', [])
        print(f"✓ Found {len(tools)} tools:")
        for tool in tools:
            print(f"  - {tool['name']}: {tool.get('description', 'No description')[:60]}...")
    else:
        print("✗ List tools failed")
    
    # Test 3: Call a tool (get_whatsapp_status)
    print("\n3. Testing get_whatsapp_status tool...")
    call_tool_request = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "get_whatsapp_status",
            "arguments": {}
        },
        "id": 3
    }
    
    response = send_mcp_request(call_tool_request)
    if response and 'result' in response:
        content = response['result'].get('content', [])
        if content:
            print(f"✓ Tool call successful: {json.dumps(content[0], indent=2)}")
    else:
        print("✗ Tool call failed")
    
    print("\n" + "=" * 50)
    print("Testing complete!")

if __name__ == "__main__":
    test_mcp_server()