# Quick Start Guide

Get WhatsApp MCP running in 5 minutes.

## Step 1: Start WhatsApp Server (1 min)

You need a WhatsApp server running. Using the provided Go server:

```bash
cd /path/to/whatsapp-go-server
docker-compose up -d
```

Verify it's running:
```bash
curl http://localhost:3000
```

## Step 2: Install WhatsApp MCP (2 min)

```bash
cd whatsapp-mcp

# Install dependencies
pip install -r requirements.txt

# Validate setup
python test_setup.py
```

## Step 3: Configure Claude Desktop (1 min)

### macOS
Edit: `~/Library/Application Support/Claude/claude_desktop_config.json`

### Windows
Edit: `%APPDATA%\Claude\claude_desktop_config.json`

### Linux
Edit: `~/.config/Claude/claude_desktop_config.json`

Add this configuration (replace `/absolute/path/to/whatsapp-mcp` with your actual path):

```json
{
  "mcpServers": {
    "whatsapp": {
      "command": "python",
      "args": ["/absolute/path/to/whatsapp-mcp/whatsapp_mcp.py"],
      "env": {
        "WHATSAPP_API_URL": "http://localhost:3000"
      }
    }
  }
}
```

**Important:** Use absolute paths! 

To get absolute path:
```bash
cd whatsapp-mcp
pwd
# Use this output in your config
```

## Step 4: Restart Claude Desktop (30 sec)

Completely quit and restart Claude Desktop application.

## Step 5: Login to WhatsApp (30 sec)

In Claude Desktop, say:
```
Login to WhatsApp via QR code
```

1. Open WhatsApp on your phone
2. Go to: Settings → Linked Devices → Link a Device
3. Scan the QR code shown in Claude's response or at http://localhost:3000

Done! 🎉

## Test It

Try these commands in Claude:

**Check connection:**
```
Show me my WhatsApp profile
```

**List chats:**
```
Show me my recent WhatsApp conversations
```

**Send a test message:**
```
Send "Hello from Claude!" to +1234567890 on WhatsApp
```

## Troubleshooting

### "Cannot connect to WhatsApp server"
```bash
# Check if server is running
docker-compose ps

# Restart server
docker-compose restart

# Check logs
docker-compose logs
```

### "Python command not found"
Use full Python path in config:
```bash
# Find Python path
which python3
# Use this in claude_desktop_config.json instead of "python"
```

### "Server not loading in Claude"
1. Check config file has valid JSON (use jsonlint.com)
2. Use absolute paths, not relative
3. Restart Claude Desktop completely
4. Check Claude Desktop logs:
   - macOS: `~/Library/Logs/Claude/`
   - Windows: `%APPDATA%\Claude\logs\`

### "QR code expired"
Just run the login command again - it generates a new QR code.

## Next Steps

- Read [README.md](README.md) for full documentation
- Explore all 30+ available tools
- Set up `.env` file for custom configuration
- Check out example use cases

## Environment Variables (Optional)

Create `.env` file for custom config:

```bash
cp .env.example .env
```

Edit `.env`:
```bash
WHATSAPP_API_URL=http://localhost:3000
WHATSAPP_AUTH_USER=your_username  # if server uses auth
WHATSAPP_AUTH_PASS=your_password  # if server uses auth
```

## Common Use Cases

### 1. Send message to contact
```
Send a WhatsApp message to +1234567890 saying "Meeting at 3pm"
```

### 2. Send image
```
Send this image to John: https://example.com/photo.jpg
with caption "Check this out!"
```

### 3. Create group
```
Create a WhatsApp group called "Project Team" with:
+1234567890
+9876543210
```

### 4. List recent chats
```
Show me my last 10 WhatsApp conversations
```

### 5. Get chat messages
```
Show me the last 20 messages from my chat with +1234567890
```

## Need Help?

1. Run validation: `python test_setup.py`
2. Check server logs: `docker-compose logs whatsapp_go`
3. Verify Claude config: Check JSON syntax
4. Read full docs: [README.md](README.md)
