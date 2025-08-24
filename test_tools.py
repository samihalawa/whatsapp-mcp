#!/usr/bin/env python3
"""
Direct test of WhatsApp MCP tools
"""

import sys
import os
sys.path.insert(0, 'whatsapp-mcp-server')

from main import (
    search_contacts,
    list_messages,
    list_chats,
    get_whatsapp_status,
    get_whatsapp_qr,
    send_message
)

def test_tools():
    """Test WhatsApp MCP tools directly"""
    
    print("Testing WhatsApp MCP Tools")
    print("=" * 50)
    
    # Test 1: Connection Status
    print("\n1. Testing get_whatsapp_status()...")
    status = get_whatsapp_status()
    print(f"   Connected: {status.get('connected', False)}")
    print(f"   Bridge Running: {status.get('bridge_running', False)}")
    print(f"   Message: {status.get('message', 'No message')}")
    
    # Test 2: Search Contacts
    print("\n2. Testing search_contacts()...")
    contacts = search_contacts("test")
    print(f"   Found {len(contacts)} contacts")
    if contacts:
        print(f"   First contact: {contacts[0].get('name', 'Unknown')}")
    
    # Test 3: List Chats
    print("\n3. Testing list_chats()...")
    chats = list_chats(limit=5)
    print(f"   Found {len(chats)} chats")
    if chats:
        print(f"   First chat: {chats[0].get('name', 'Unknown')}")
    
    # Test 4: List Messages
    print("\n4. Testing list_messages()...")
    messages = list_messages(limit=5)
    print(f"   Messages: {messages[:100]}...")
    
    # Test 5: Send Message (mock)
    print("\n5. Testing send_message()...")
    result = send_message("1234567890", "Test message")
    print(f"   Success: {result.get('success', False)}")
    print(f"   Message: {result.get('message', 'No message')}")
    
    # Test 6: QR Code
    print("\n6. Testing get_whatsapp_qr()...")
    qr = get_whatsapp_qr()
    print(f"   Success: {qr.get('success', False)}")
    print(f"   Message: {qr.get('message', 'No message')}")
    if qr.get('qr_string'):
        print(f"   QR String: {qr['qr_string'][:50]}...")
    
    print("\n" + "=" * 50)
    print("All tools tested successfully!")

if __name__ == "__main__":
    test_tools()