from typing import List, Dict, Any, Optional
from mcp.server.fastmcp import FastMCP
from whatsapp_full import (
    search_contacts,
    list_messages,
    list_chats,
    get_chat,
    get_direct_chat_by_contact,
    get_contact_chats,
    get_last_interaction,
    get_message_context,
    send_message,
    send_file,
    send_audio_message,
    download_media,
    get_whatsapp_status,
    get_whatsapp_qr,
    wait_for_whatsapp_connection
)

mcp = FastMCP("whatsapp")

@mcp.tool()
def search_contacts_tool(query: str) -> List[Dict[str, Any]]:
    """Search WhatsApp contacts by name or phone number."""
    return search_contacts(query)

@mcp.tool()
def list_messages_tool(
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
) -> List[Dict[str, Any]]:
    """Get WhatsApp messages matching specified criteria."""
    return list_messages(
        after, before, sender_phone_number, chat_jid, query,
        limit, page, include_context, context_before, context_after
    )

@mcp.tool()
def list_chats_tool(
    query: Optional[str] = None,
    limit: int = 20,
    page: int = 0,
    include_last_message: bool = True,
    sort_by: str = "last_active"
) -> List[Dict[str, Any]]:
    """Get WhatsApp chats matching specified criteria."""
    return list_chats(query, limit, page, include_last_message, sort_by)

@mcp.tool()
def get_chat_tool(chat_jid: str, include_last_message: bool = True) -> Dict[str, Any]:
    """Get WhatsApp chat metadata by JID."""
    return get_chat(chat_jid, include_last_message)

@mcp.tool()
def get_direct_chat_by_contact_tool(sender_phone_number: str) -> Dict[str, Any]:
    """Get WhatsApp chat metadata by sender phone number."""
    return get_direct_chat_by_contact(sender_phone_number)

@mcp.tool()
def get_contact_chats_tool(jid: str, limit: int = 20, page: int = 0) -> List[Dict[str, Any]]:
    """Get all WhatsApp chats involving the contact."""
    return get_contact_chats(jid, limit, page)

@mcp.tool()
def get_last_interaction_tool(jid: str) -> str:
    """Get most recent WhatsApp message involving the contact."""
    return get_last_interaction(jid)

@mcp.tool()
def get_message_context_tool(
    message_id: str,
    before: int = 5,
    after: int = 5
) -> Dict[str, Any]:
    """Get context around a specific WhatsApp message."""
    return get_message_context(message_id, before, after)

@mcp.tool()
def send_message_tool(recipient: str, message: str) -> Dict[str, Any]:
    """Send a WhatsApp message to a person or group."""
    success, status_message = send_message(recipient, message)
    return {"success": success, "message": status_message}

@mcp.tool()
def send_file_tool(recipient: str, media_path: str) -> Dict[str, Any]:
    """Send a file via WhatsApp."""
    success, status_message = send_file(recipient, media_path)
    return {"success": success, "message": status_message}

@mcp.tool()
def send_audio_message_tool(recipient: str, media_path: str) -> Dict[str, Any]:
    """Send an audio message via WhatsApp."""
    success, status_message = send_audio_message(recipient, media_path)
    return {"success": success, "message": status_message}

@mcp.tool()
def download_media_tool(message_id: str, chat_jid: str) -> Dict[str, Any]:
    """Download media from a WhatsApp message."""
    file_path = download_media(message_id, chat_jid)
    if file_path:
        return {"success": True, "message": "Media downloaded", "file_path": file_path}
    return {"success": False, "message": "Failed to download media"}

@mcp.tool()
def get_whatsapp_status_tool() -> Dict[str, Any]:
    """Get WhatsApp connection status and QR code if not connected."""
    return get_whatsapp_status()

@mcp.tool()
def get_whatsapp_qr_tool() -> Dict[str, Any]:
    """Get WhatsApp QR code for authentication."""
    return get_whatsapp_qr()

@mcp.tool()
def wait_for_whatsapp_connection_tool(timeout: int = 60) -> Dict[str, Any]:
    """Wait for WhatsApp to be connected."""
    return wait_for_whatsapp_connection(timeout)

if __name__ == "__main__":
    mcp.run(transport='stdio')