# WhatsApp MCP Deployment Guide

## Smithery Deployment

Deploy this MCP server to Smithery.ai for cloud-hosted WhatsApp integration.

### Prerequisites
- Smithery.ai account
- WhatsApp account for authentication

### Configuration

The `smithery.yaml` file is pre-configured:
```yaml
version: 1
runtime: container
startCommand:
  type: stdio
build:
  dockerfile: "Dockerfile"
  dockerBuildPath: "."
```

### Deployment Steps

1. **Deploy to Smithery**
   ```bash
   smithery deploy
   ```

2. **Authenticate WhatsApp**
   - Use the `get_whatsapp_status` tool to get QR code
   - Scan with WhatsApp mobile app
   - Connection established

### Available Tools (15 total)

**Authentication (3)**
- `get_whatsapp_status` - Connection status and QR code
- `get_whatsapp_qr` - Get QR code for authentication  
- `wait_for_whatsapp_connection` - Wait for connection

**Messaging (4)**
- `send_message` - Send text messages
- `send_file` - Send images/videos/documents
- `send_audio_message` - Send audio messages
- `download_media` - Download received media

**Contacts & Chats (8)**
- `search_contacts` - Search contacts by name/phone
- `list_messages` - Get messages with filters
- `list_chats` - List all chats
- `get_chat` - Get chat metadata
- `get_direct_chat_by_contact` - Get chat by phone number
- `get_contact_chats` - Get all chats with contact
- `get_last_interaction` - Get last message with contact
- `get_message_context` - Get message context

## Local Development

### Run with Mock Bridge (Testing)
```bash
python mock_bridge.py  # Start mock bridge
python whatsapp-mcp-server/main.py  # Start MCP server
```

### Run with Real WhatsApp Bridge
```bash
cd whatsapp-bridge
go build
./whatsapp-client  # Start WhatsApp bridge
cd ..
python whatsapp-mcp-server/main.py  # Start MCP server
```

## Architecture

```
┌─────────────┐     HTTP API      ┌──────────────┐
│ MCP Server  │ ◄──────────────► │ WhatsApp     │
│  (Python)   │                   │ Bridge (Go)  │
└─────────────┘                   └──────────────┘
      ▲                                  ▲
      │                                  │
      ▼                                  ▼
┌─────────────┐                   ┌──────────────┐
│   Claude    │                   │  WhatsApp    │
│   Desktop   │                   │   Web API    │
└─────────────┘                   └──────────────┘
```

## Security Notes

- Never commit WhatsApp session data
- Keep authentication tokens secure
- Use environment variables for sensitive config
- Session data persists in `/app/store` directory