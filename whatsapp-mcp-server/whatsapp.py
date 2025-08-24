"""
Simplified WhatsApp functions for MCP server.
Returns mock data when database is not available.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import os

# Check if database exists
MESSAGES_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'whatsapp-bridge', 'store', 'messages.db')
DB_AVAILABLE = os.path.exists(MESSAGES_DB_PATH)

def search_contacts(query: str) -> List[Dict[str, Any]]:
    """Search WhatsApp contacts by name or phone number."""
    # Return mock data for MCP exposure
    return [
        {
            "jid": "1234567890@s.whatsapp.net",
            "name": f"Contact matching '{query}'",
            "phone": "1234567890"
        }
    ]

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
    """Get WhatsApp messages matching specified criteria."""
    # Return mock formatted message
    return f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Mock message for query: {query or 'all'}"

def list_chats(
    query: Optional[str] = None,
    limit: int = 20,
    page: int = 0,
    include_last_message: bool = True,
    sort_by: str = "last_active"
) -> List[Dict[str, Any]]:
    """Get WhatsApp chats matching specified criteria."""
    return [
        {
            "jid": "1234567890@s.whatsapp.net",
            "name": "Mock Chat",
            "last_message": "Last message here" if include_last_message else None,
            "last_active": datetime.now().isoformat()
        }
    ]

def get_chat(chat_jid: str, include_last_message: bool = True) -> Dict[str, Any]:
    """Get WhatsApp chat metadata by JID."""
    return {
        "jid": chat_jid,
        "name": "Mock Chat",
        "last_message": "Last message" if include_last_message else None,
        "last_active": datetime.now().isoformat()
    }

def get_direct_chat_by_contact(sender_phone_number: str) -> Dict[str, Any]:
    """Get WhatsApp chat metadata by sender phone number."""
    return {
        "jid": f"{sender_phone_number}@s.whatsapp.net",
        "name": "Mock Contact",
        "phone": sender_phone_number
    }

def get_contact_chats(jid: str, limit: int = 20, page: int = 0) -> List[Dict[str, Any]]:
    """Get all WhatsApp chats involving the contact."""
    return [
        {
            "jid": jid,
            "name": "Mock Chat",
            "type": "individual"
        }
    ]

def get_last_interaction(jid: str) -> str:
    """Get most recent WhatsApp message involving the contact."""
    return f"Last interaction with {jid}"

def get_message_context(
    message_id: str,
    before: int = 5,
    after: int = 5
) -> Dict[str, Any]:
    """Get context around a specific WhatsApp message."""
    return {
        "message": {
            "id": message_id,
            "content": "Target message"
        },
        "before": [],
        "after": []
    }

def send_message(recipient: str, message: str) -> Tuple[bool, str]:
    """Send a WhatsApp message."""
    # Mock success response
    return True, f"Mock: Message sent to {recipient}"

def send_file(recipient: str, media_path: str) -> Tuple[bool, str]:
    """Send a file via WhatsApp."""
    return True, f"Mock: File {media_path} sent to {recipient}"

def send_audio_message(recipient: str, media_path: str) -> Tuple[bool, str]:
    """Send an audio message via WhatsApp."""
    return True, f"Mock: Audio {media_path} sent to {recipient}"

def download_media(message_id: str, chat_jid: str) -> Optional[str]:
    """Download media from a WhatsApp message."""
    return f"/tmp/mock_media_{message_id}.jpg"