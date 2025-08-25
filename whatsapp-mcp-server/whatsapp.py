"""
WhatsApp functions for MCP server.
Requires real WhatsApp bridge to be running.
"""

from typing import List, Dict, Any, Optional, Tuple

# Try to import the full implementation
try:
    from whatsapp_full import (
        check_bridge_health,
        get_connection_status as full_get_connection_status,
        get_qr_code as full_get_qr_code,
        wait_for_connection as full_wait_for_connection,
        search_contacts as full_search_contacts,
        list_messages as full_list_messages,
        list_chats as full_list_chats,
        get_chat as full_get_chat,
        get_direct_chat_by_contact as full_get_direct_chat_by_contact,
        get_contact_chats as full_get_contact_chats,
        get_last_interaction as full_get_last_interaction,
        get_message_context as full_get_message_context,
        send_message as full_send_message,
        send_file as full_send_file,
        send_audio_message as full_send_audio_message,
        download_media as full_download_media
    )
    FULL_IMPL_AVAILABLE = True
except ImportError:
    FULL_IMPL_AVAILABLE = False
    check_bridge_health = lambda: False

def get_connection_status() -> Dict[str, Any]:
    """Get WhatsApp connection status and QR code if not connected."""
    if not FULL_IMPL_AVAILABLE:
        raise Exception("WhatsApp bridge implementation not available")
    return full_get_connection_status()

def get_qr_code() -> Dict[str, Any]:
    """Get WhatsApp QR code for authentication."""
    if not FULL_IMPL_AVAILABLE:
        raise Exception("WhatsApp bridge implementation not available")
    return full_get_qr_code()

def wait_for_connection(timeout: int = 60) -> Dict[str, Any]:
    """Wait for WhatsApp to be connected."""
    if not FULL_IMPL_AVAILABLE:
        raise Exception("WhatsApp bridge implementation not available")
    return full_wait_for_connection(timeout)

def search_contacts(query: str) -> List[Dict[str, Any]]:
    """Search WhatsApp contacts by name or phone number."""
    if not FULL_IMPL_AVAILABLE:
        raise Exception("WhatsApp bridge implementation not available")
    return full_search_contacts(query)

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
    if not FULL_IMPL_AVAILABLE:
        raise Exception("WhatsApp bridge implementation not available")
    return full_list_messages(
        after, before, sender_phone_number, chat_jid, query,
        limit, page, include_context, context_before, context_after
    )

def list_chats(
    query: Optional[str] = None,
    limit: int = 20,
    page: int = 0,
    include_last_message: bool = True,
    sort_by: str = "last_active"
) -> List[Dict[str, Any]]:
    """Get WhatsApp chats matching specified criteria."""
    if not FULL_IMPL_AVAILABLE:
        raise Exception("WhatsApp bridge implementation not available")
    return full_list_chats(query, limit, page, include_last_message, sort_by)

def get_chat(chat_jid: str, include_last_message: bool = True) -> Dict[str, Any]:
    """Get WhatsApp chat metadata by JID."""
    if not FULL_IMPL_AVAILABLE:
        raise Exception("WhatsApp bridge implementation not available")
    return full_get_chat(chat_jid, include_last_message)

def get_direct_chat_by_contact(sender_phone_number: str) -> Dict[str, Any]:
    """Get WhatsApp chat metadata by sender phone number."""
    if not FULL_IMPL_AVAILABLE:
        raise Exception("WhatsApp bridge implementation not available")
    return full_get_direct_chat_by_contact(sender_phone_number)

def get_contact_chats(jid: str, limit: int = 20, page: int = 0) -> List[Dict[str, Any]]:
    """Get all WhatsApp chats involving the contact."""
    if not FULL_IMPL_AVAILABLE:
        raise Exception("WhatsApp bridge implementation not available")
    return full_get_contact_chats(jid, limit, page)

def get_last_interaction(jid: str) -> str:
    """Get most recent WhatsApp message involving the contact."""
    if not FULL_IMPL_AVAILABLE:
        raise Exception("WhatsApp bridge implementation not available")
    return full_get_last_interaction(jid)

def get_message_context(
    message_id: str,
    before: int = 5,
    after: int = 5
) -> Dict[str, Any]:
    """Get context around a specific WhatsApp message."""
    if not FULL_IMPL_AVAILABLE:
        raise Exception("WhatsApp bridge implementation not available")
    return full_get_message_context(message_id, before, after)

def send_message(recipient: str, message: str) -> Tuple[bool, str]:
    """Send a WhatsApp message."""
    if not FULL_IMPL_AVAILABLE:
        raise Exception("WhatsApp bridge implementation not available")
    return full_send_message(recipient, message)

def send_file(recipient: str, media_path: str) -> Tuple[bool, str]:
    """Send a file via WhatsApp."""
    if not FULL_IMPL_AVAILABLE:
        raise Exception("WhatsApp bridge implementation not available")
    return full_send_file(recipient, media_path)

def send_audio_message(recipient: str, media_path: str) -> Tuple[bool, str]:
    """Send an audio message via WhatsApp."""
    if not FULL_IMPL_AVAILABLE:
        raise Exception("WhatsApp bridge implementation not available")
    return full_send_audio_message(recipient, media_path)

def download_media(message_id: str, chat_jid: str) -> Optional[str]:
    """Download media from a WhatsApp message."""
    if not FULL_IMPL_AVAILABLE:
        raise Exception("WhatsApp bridge implementation not available")
    return full_download_media(message_id, chat_jid)