"""
WhatsApp MCP Server for Smithery.ai
Implements HTTP streamable MCP with QR code authentication support
"""

from typing import List, Dict, Any, Optional
from mcp.server.fastmcp import FastMCP
import whatsapp_real as whatsapp
import base64
import json

# Initialize FastMCP server
mcp = FastMCP("whatsapp")

# Authentication Management Tools

@mcp.tool()
def get_whatsapp_status() -> Dict[str, Any]:
    """Get the current WhatsApp connection status and QR code if needed.
    
    Returns:
        A dictionary containing:
        - status: 'connected', 'pending', 'expired', or 'disconnected'
        - qr_code: The QR code text (if status is 'pending')
        - qr_image: Base64 encoded QR code image (if status is 'pending')
        - message: Human-readable status message
        - instructions: Step-by-step instructions for authentication (if needed)
    """
    result = whatsapp.get_qr_code()
    
    # Add user-friendly instructions based on status
    if result.get("status") == "pending" and result.get("qr_code"):
        result["instructions"] = [
            "1. Open WhatsApp on your phone",
            "2. Go to Settings > Linked Devices",
            "3. Tap 'Link a Device'",
            "4. Scan the QR code below:",
            f"QR Code: {result.get('qr_code', 'Not available')}"
        ]
        
        # If we have a QR image, format it for display
        if result.get("qr_image"):
            result["qr_display"] = f"data:image/png;base64,{result['qr_image']}"
    
    elif result.get("status") == "connected":
        result["instructions"] = ["WhatsApp is connected and ready to use!"]
    
    elif result.get("status") == "expired":
        result["instructions"] = [
            "The QR code has expired.",
            "Use the 'trigger_whatsapp_reauth' tool to generate a new QR code."
        ]
    
    elif result.get("status") == "disconnected":
        result["instructions"] = [
            "WhatsApp is not connected.",
            "Use the 'trigger_whatsapp_reauth' tool to start authentication."
        ]
    
    return result

@mcp.tool()
def trigger_whatsapp_reauth() -> Dict[str, Any]:
    """Trigger WhatsApp re-authentication to generate a new QR code.
    
    Use this when:
    - The QR code has expired
    - You need to re-authenticate with WhatsApp
    - The connection has been lost
    
    Returns:
        A dictionary with success status and next steps
    """
    result = whatsapp.trigger_reauth()
    
    if result.get("success"):
        result["next_steps"] = [
            "Authentication process started!",
            "Use the 'get_whatsapp_status' tool to get the QR code",
            "Follow the instructions to scan it with your phone"
        ]
    else:
        result["next_steps"] = [
            "Failed to trigger re-authentication.",
            f"Error: {result.get('message', 'Unknown error')}",
            "Please check if the WhatsApp bridge is running."
        ]
    
    return result

@mcp.tool()
def wait_for_whatsapp_connection(timeout: int = 180) -> Dict[str, Any]:
    """Wait for WhatsApp to connect after QR code scanning.
    
    Args:
        timeout: Maximum time to wait in seconds (default 180)
    
    Returns:
        A dictionary indicating whether connection was successful
    """
    connected = whatsapp.wait_for_connection(timeout)
    
    if connected:
        return {
            "success": True,
            "message": "WhatsApp successfully connected!",
            "status": "ready"
        }
    else:
        return {
            "success": False,
            "message": f"Connection timeout after {timeout} seconds",
            "status": "timeout",
            "next_steps": [
                "Use 'get_whatsapp_status' to check current status",
                "If QR expired, use 'trigger_whatsapp_reauth' to generate new one"
            ]
        }
    
# Contact Management Tools

@mcp.tool()
def search_contacts(query: str) -> List[Dict[str, Any]]:
    """Search WhatsApp contacts by name or phone number.
    
    Args:
        query: Search term to match against contact names or phone numbers
    """
    contacts = whatsapp.search_contacts(query)
    return contacts

# Message Tools

@mcp.tool()
def list_messages(
    after: Optional[str] = None,
    before: Optional[str] = None,
    sender_phone_number: Optional[str] = None,
    chat_jid: Optional[str] = None,
    query: Optional[str] = None,
    limit: int = 20,
    page: int = 0,
    include_context: bool = True,
    context_before: int = 1,
    context_after: int = 1
) -> str:
    """Get WhatsApp messages matching specified criteria with optional context.
    
    Args:
        after: Optional ISO-8601 formatted string to only return messages after this date
        before: Optional ISO-8601 formatted string to only return messages before this date
        sender_phone_number: Optional phone number to filter messages by sender
        chat_jid: Optional chat JID to filter messages by chat
        query: Optional search term to filter messages by content
        limit: Maximum number of messages to return (default 20)
        page: Page number for pagination (default 0)
        include_context: Whether to include messages before and after matches (default True)
        context_before: Number of messages to include before each match (default 1)
        context_after: Number of messages to include after each match (default 1)
    """
    messages = whatsapp.list_messages(
        after=after,
        before=before,
        sender_phone_number=sender_phone_number,
        chat_jid=chat_jid,
        query=query,
        limit=limit,
        page=page,
        include_context=include_context,
        context_before=context_before,
        context_after=context_after
    )
    return messages

# Chat Management Tools

@mcp.tool()
def list_chats(
    query: Optional[str] = None,
    limit: int = 20,
    page: int = 0,
    include_last_message: bool = True,
    sort_by: str = "last_active"
) -> List[Dict[str, Any]]:
    """Get WhatsApp chats matching specified criteria.
    
    Args:
        query: Optional search term to filter chats by name or JID
        limit: Maximum number of chats to return (default 20)
        page: Page number for pagination (default 0)
        include_last_message: Whether to include the last message in each chat (default True)
        sort_by: Field to sort results by, either "last_active" or "name" (default "last_active")
    """
    chats = whatsapp.list_chats(
        query=query,
        limit=limit,
        page=page,
        include_last_message=include_last_message,
        sort_by=sort_by
    )
    return chats

@mcp.tool()
def get_chat(chat_jid: str, include_last_message: bool = True) -> Dict[str, Any]:
    """Get WhatsApp chat metadata by JID.
    
    Args:
        chat_jid: The JID of the chat to retrieve
        include_last_message: Whether to include the last message (default True)
    """
    chat = whatsapp.get_chat(chat_jid, include_last_message)
    return chat

@mcp.tool()
def get_direct_chat_by_contact(sender_phone_number: str) -> Dict[str, Any]:
    """Get WhatsApp chat metadata by sender phone number.
    
    Args:
        sender_phone_number: The phone number to search for
    """
    chat = whatsapp.get_direct_chat_by_contact(sender_phone_number)
    return chat

@mcp.tool()
def get_contact_chats(jid: str, limit: int = 20, page: int = 0) -> List[Dict[str, Any]]:
    """Get all WhatsApp chats involving the contact.
    
    Args:
        jid: The contact's JID to search for
        limit: Maximum number of chats to return (default 20)
        page: Page number for pagination (default 0)
    """
    chats = whatsapp.get_contact_chats(jid, limit, page)
    return chats

@mcp.tool()
def get_last_interaction(jid: str) -> str:
    """Get most recent WhatsApp message involving the contact.
    
    Args:
        jid: The JID of the contact to search for
    """
    message = whatsapp.get_last_interaction(jid)
    return message

@mcp.tool()
def get_message_context(
    message_id: str,
    before: int = 5,
    after: int = 5
) -> Dict[str, Any]:
    """Get context around a specific WhatsApp message.
    
    Args:
        message_id: The ID of the message to get context for
        before: Number of messages to include before the target message (default 5)
        after: Number of messages to include after the target message (default 5)
    """
    context = whatsapp.get_message_context(message_id, before, after)
    return context

# Messaging Tools

@mcp.tool()
def send_message(
    recipient: str,
    message: str
) -> Dict[str, Any]:
    """Send a WhatsApp message to a person or group.
    
    IMPORTANT: Ensure WhatsApp is connected before sending messages.
    Use 'get_whatsapp_status' to check connection status first.
    
    Args:
        recipient: The recipient - either a phone number with country code but no + or other symbols,
                 or a JID (e.g., "123456789@s.whatsapp.net" or a group JID like "123456789@g.us")
        message: The message text to send
    
    Returns:
        A dictionary containing success status and a status message
    """
    if not recipient:
        return {
            "success": False,
            "message": "Recipient must be provided"
        }
    
    success, status_message = whatsapp.send_message(recipient, message)
    
    # Add helpful information if sending failed due to connection
    if not success and "not connected" in status_message.lower():
        return {
            "success": False,
            "message": status_message,
            "help": "Use 'get_whatsapp_status' to check connection and get QR code if needed"
        }
    
    return {
        "success": success,
        "message": status_message
    }

@mcp.tool()
def send_file(recipient: str, media_path: str) -> Dict[str, Any]:
    """Send a file (image, video, document) via WhatsApp.
    
    Args:
        recipient: The recipient - either a phone number with country code but no + or other symbols,
                 or a JID (e.g., "123456789@s.whatsapp.net" or a group JID like "123456789@g.us")
        media_path: The absolute path to the media file to send
    
    Returns:
        A dictionary containing success status and a status message
    """
    success, status_message = whatsapp.send_file(recipient, media_path)
    
    if not success and "not connected" in status_message.lower():
        return {
            "success": False,
            "message": status_message,
            "help": "Use 'get_whatsapp_status' to check connection and get QR code if needed"
        }
    
    return {
        "success": success,
        "message": status_message
    }

@mcp.tool()
def send_audio_message(recipient: str, media_path: str) -> Dict[str, Any]:
    """Send an audio file as a WhatsApp voice message.
    
    Note: For best results, audio should be in .ogg Opus format.
    If FFmpeg is installed, other formats will be automatically converted.
    
    Args:
        recipient: The recipient - either a phone number with country code but no + or other symbols,
                 or a JID (e.g., "123456789@s.whatsapp.net" or a group JID like "123456789@g.us")
        media_path: The absolute path to the audio file to send
    
    Returns:
        A dictionary containing success status and a status message
    """
    success, status_message = whatsapp.send_audio_message(recipient, media_path)
    
    if not success and "not connected" in status_message.lower():
        return {
            "success": False,
            "message": status_message,
            "help": "Use 'get_whatsapp_status' to check connection and get QR code if needed"
        }
    
    return {
        "success": success,
        "message": status_message
    }

@mcp.tool()
def download_media(message_id: str, chat_jid: str) -> Dict[str, Any]:
    """Download media from a WhatsApp message and get the local file path.
    
    Args:
        message_id: The ID of the message containing the media
        chat_jid: The JID of the chat containing the message
    
    Returns:
        A dictionary containing success status, a status message, and the file path if successful
    """
    file_path = whatsapp.download_media(message_id, chat_jid)
    
    if file_path:
        return {
            "success": True,
            "message": "Media downloaded successfully",
            "file_path": file_path
        }
    else:
        return {
            "success": False,
            "message": "Failed to download media. Check if the message exists and contains media."
        }

# Server initialization
if __name__ == "__main__":
    # For Smithery deployment, we'll use HTTP transport
    # The stdio transport is still available for local testing
    import sys
    
    transport = 'stdio'  # Default for local testing
    
    # Check if we're running in Smithery environment
    if 'SMITHERY_ENV' in sys.environ or '--http' in sys.argv:
        transport = 'http'
        print("Starting WhatsApp MCP server with HTTP transport for Smithery")
    else:
        print("Starting WhatsApp MCP server with stdio transport")
    
    mcp.run(transport=transport)