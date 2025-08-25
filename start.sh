#!/bin/sh
/app/whatsapp-bridge &
exec python -m whatsapp_mcp_server.main