#!/bin/bash

# Start the WhatsApp bridge in the background
echo "Starting WhatsApp bridge..."
./whatsapp-bridge &
BRIDGE_PID=$!

# Wait a bit for the bridge to initialize
sleep 2

# Check if bridge is running
if ! kill -0 $BRIDGE_PID 2>/dev/null; then
    echo "WhatsApp bridge failed to start"
    exit 1
fi

echo "WhatsApp bridge started with PID $BRIDGE_PID"

# Function to handle shutdown
cleanup() {
    echo "Shutting down..."
    kill $BRIDGE_PID 2>/dev/null
    wait $BRIDGE_PID
    exit 0
}

# Trap signals to ensure clean shutdown
trap cleanup SIGTERM SIGINT

# Start the MCP server (this will be the main process)
echo "Starting MCP server..."
cd /app/whatsapp-mcp-server
exec python main.py