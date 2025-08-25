#!/usr/bin/env python3
"""
Test MCP server with real WhatsApp bridge
"""

import sys
import json
import time
sys.path.insert(0, 'whatsapp-mcp-server')

# Test the connection status
print("Testing WhatsApp MCP with Real Bridge")
print("=" * 50)

# Import the functions
from whatsapp import get_connection_status, get_qr_code

try:
    # Test 1: Get connection status
    print("\n1. Testing get_connection_status()...")
    status = get_connection_status()
    print(f"   Result: {json.dumps(status, indent=2)}")
    
    # Test 2: Get QR code
    print("\n2. Testing get_qr_code()...")
    qr = get_qr_code()
    print(f"   Result: {json.dumps(qr, indent=2)[:200]}...")
    
    if qr.get('qr_string'):
        print("\n3. QR Code String (for scanning):")
        print("-" * 40)
        print(qr['qr_string'])
        print("-" * 40)
        print("\nScan this QR code with WhatsApp to connect!")
    
except Exception as e:
    print(f"\nError: {e}")
    print("\nThis error is expected since we removed all mock data.")
    print("The bridge needs to be running with proper QR endpoints.")

print("\n" + "=" * 50)
print("Test complete!")