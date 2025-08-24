#!/bin/bash

echo "Starting WhatsApp MCP services..."

# Start supervisor to manage both services
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf