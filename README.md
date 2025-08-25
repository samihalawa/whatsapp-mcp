# WhatsApp MCP Server

MCP server for WhatsApp Web integration via Claude.

## Local Testing

### Build and Run Container
```bash
docker build -t whatsapp-mcp .
docker run -it whatsapp-mcp
```

### Get QR Code
Call `get_whatsapp_qr_tool` via Claude or JSON-RPC:
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "get_whatsapp_qr_tool",
    "arguments": {}
  },
  "id": 1
}
```

### Available Tools
- `get_whatsapp_status_tool` - Connection status
- `get_whatsapp_qr_tool` - QR code for auth
- `wait_for_whatsapp_connection_tool` - Wait for connection
- `send_message_tool` - Send messages
- `list_chats_tool` - List chats
- Plus 10 more messaging tools

## Deployment
Deploy to Smithery.ai using `smithery.yaml`.