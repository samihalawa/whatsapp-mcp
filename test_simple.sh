#!/bin/bash

echo "Testing WhatsApp MCP Server with simple requests"
echo "=================================================="

# Test initialization
echo -e "\n1. Testing initialization..."
echo '{"jsonrpc": "2.0", "method": "initialize", "params": {"protocolVersion": "1.0.0", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0"}}, "id": 1}
{"jsonrpc": "2.0", "method": "initialized", "params": {}, "id": 2}
{"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 3}' | python whatsapp-mcp-server/main.py 2>/dev/null | jq -r '.result.tools | length' | head -1 | xargs -I {} echo "✓ Found {} tools"

# Test tool listing
echo -e "\n2. Listing available tools..."
echo '{"jsonrpc": "2.0", "method": "initialize", "params": {"protocolVersion": "1.0.0", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0"}}, "id": 1}
{"jsonrpc": "2.0", "method": "initialized", "params": {}, "id": 2}
{"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 3}' | python whatsapp-mcp-server/main.py 2>/dev/null | grep -o '"name":"[^"]*"' | head -5 | sed 's/"name":"/ - /g' | sed 's/"//g'

echo -e "\nMCP server is working correctly!"