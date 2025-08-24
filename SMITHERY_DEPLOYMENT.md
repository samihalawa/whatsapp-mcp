# WhatsApp MCP Smithery Deployment

This WhatsApp MCP can be deployed to Smithery with both the Go WhatsApp bridge and Python MCP server running together in a single container.

## How It Works

The Docker container runs both services:

1. **WhatsApp Bridge** (Go) - Connects to WhatsApp Web API, handles authentication, and maintains the message database
2. **MCP Server** (Python) - Provides the Model Context Protocol interface for Claude

Both services run in the same container and communicate via the shared SQLite database.

## Architecture

```
Docker Container
├── whatsapp-bridge (Go binary)
│   ├── Connects to WhatsApp Web
│   ├── Handles QR authentication
│   └── Writes to SQLite database
│
├── whatsapp-mcp-server (Python)
│   ├── MCP protocol implementation
│   ├── Reads from SQLite database
│   └── Sends messages via bridge API
│
└── store/
    ├── messages.db (SQLite database)
    ├── whatsapp.db (Session data)
    └── media/ (Downloaded media files)
```

## Deployment Steps

### 1. Deploy to Smithery

```bash
# From the whatsapp-mcp directory
smithery publish
```

### 2. Configure in Smithery

When configuring the MCP server in Smithery, you can customize:

- `dbPath`: Path to messages database (default: `./store/messages.db`)
- `mediaPath`: Path for downloaded media (default: `./store/media`)
- `sessionPath`: Path to WhatsApp session (default: `./store/whatsapp.db`)
- `logLevel`: Logging verbosity (default: `info`)
- `qrTimeout`: QR code timeout in seconds (default: 60)

### 3. Authentication

The first time the container starts, you'll need to authenticate with WhatsApp:

1. Check the container logs for the QR code
2. Open WhatsApp on your phone
3. Go to Settings > Linked Devices > Link a Device
4. Scan the QR code

The session will persist in the container's volume, so you won't need to re-authenticate unless the session expires (approximately every 20 days).

## Container Features

- **Multi-stage build**: Optimized size with separate Go build stage
- **Health checks**: Monitors both services are running
- **Signal handling**: Graceful shutdown of both services
- **Non-root user**: Runs as `whatsapp` user for security
- **FFmpeg included**: For audio message conversion
- **Persistent storage**: Session and messages are preserved

## Local Testing

To test the container locally:

```bash
# Build the container
docker build -t whatsapp-mcp .

# Run with volume for persistence
docker run -it -v whatsapp-data:/app/store whatsapp-mcp

# View logs to see QR code
docker logs <container-id>
```

## Troubleshooting

### QR Code Not Visible
Check the container logs:
```bash
docker logs <container-id>
```

### Session Issues
If the session is corrupted, you may need to clear the volume and re-authenticate:
```bash
docker volume rm whatsapp-data
```

### Both Services Not Starting
The health check verifies both services are running. If it fails, check:
1. Go bridge started successfully
2. Python MCP server started successfully
3. No port conflicts or permission issues

## Security Notes

- The container runs as a non-root user (`whatsapp`)
- All data is stored locally in the container
- Messages are only accessed when Claude uses the MCP tools
- Session data should be treated as sensitive

## Environment Variables

The container respects these environment variables:

- `DB_PATH`: Override database path
- `MEDIA_PATH`: Override media storage path
- `SESSION_PATH`: Override session storage path
- `LOG_LEVEL`: Set logging level (debug, info, warn, error)
- `QR_TIMEOUT`: QR code display timeout