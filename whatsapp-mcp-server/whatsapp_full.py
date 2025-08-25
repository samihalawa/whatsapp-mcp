"""
WhatsApp bridge HTTP client implementation.
"""

import requests
import time
from typing import List, Dict, Any, Optional, Tuple

BRIDGE_URL = "http://localhost:8080"

def _check_response(response):
    """Raise exception if response is not successful."""
    if response.status_code != 200:
        raise Exception(f"Bridge error: {response.status_code} - {response.text}")
    return response.json()

def get_whatsapp_status() -> Dict[str, Any]:
    """Get WhatsApp connection status."""
    response = requests.get(f"{BRIDGE_URL}/api/status")
    data = _check_response(response)
    
    if not data.get("connected"):
        qr_response = requests.get(f"{BRIDGE_URL}/api/qr")
        if qr_response.status_code == 200:
            qr_data = qr_response.json()
            data["qr_code"] = qr_data.get("qr_string")
            data["qr_image"] = qr_data.get("qr_base64")
    
    return data

def get_whatsapp_qr() -> Dict[str, Any]:
    """Get WhatsApp QR code."""
    response = requests.get(f"{BRIDGE_URL}/api/qr")
    return _check_response(response)

def wait_for_whatsapp_connection(timeout: int = 60) -> Dict[str, Any]:
    """Wait for WhatsApp connection."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        response = requests.get(f"{BRIDGE_URL}/api/status")
        data = _check_response(response)
        if data.get("connected"):
            return {"success": True, "message": "Connected"}
        time.sleep(2)
    raise Exception("Connection timeout")

def search_contacts(query: str) -> List[Dict[str, Any]]:
    """Search contacts."""
    response = requests.get(f"{BRIDGE_URL}/api/contacts", params={"q": query})
    return _check_response(response)

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
    """List messages."""
    params = {
        "after": after,
        "before": before,
        "sender": sender_phone_number,
        "chat": chat_jid,
        "q": query,
        "limit": limit,
        "page": page
    }
    params = {k: v for k, v in params.items() if v is not None}
    response = requests.get(f"{BRIDGE_URL}/api/messages", params=params)
    return _check_response(response)

def list_chats(
    query: Optional[str] = None,
    limit: int = 20,
    page: int = 0,
    include_last_message: bool = True,
    sort_by: str = "last_active"
) -> List[Dict[str, Any]]:
    """List chats."""
    params = {"q": query, "limit": limit, "page": page}
    params = {k: v for k, v in params.items() if v is not None}
    response = requests.get(f"{BRIDGE_URL}/api/chats", params=params)
    return _check_response(response)

def get_chat(chat_jid: str, include_last_message: bool = True) -> Dict[str, Any]:
    """Get chat details."""
    response = requests.get(f"{BRIDGE_URL}/api/chats/{chat_jid}")
    return _check_response(response)

def get_direct_chat_by_contact(sender_phone_number: str) -> Dict[str, Any]:
    """Get chat by phone number."""
    response = requests.get(f"{BRIDGE_URL}/api/chats/phone/{sender_phone_number}")
    return _check_response(response)

def get_contact_chats(jid: str, limit: int = 20, page: int = 0) -> List[Dict[str, Any]]:
    """Get contact's chats."""
    params = {"limit": limit, "page": page}
    response = requests.get(f"{BRIDGE_URL}/api/contacts/{jid}/chats", params=params)
    return _check_response(response)

def get_last_interaction(jid: str) -> str:
    """Get last interaction."""
    response = requests.get(f"{BRIDGE_URL}/api/contacts/{jid}/last")
    data = _check_response(response)
    return data.get("message", "")

def get_message_context(
    message_id: str,
    before: int = 5,
    after: int = 5
) -> Dict[str, Any]:
    """Get message context."""
    params = {"before": before, "after": after}
    response = requests.get(f"{BRIDGE_URL}/api/messages/{message_id}/context", params=params)
    return _check_response(response)

def send_message(recipient: str, message: str) -> Tuple[bool, str]:
    """Send message."""
    response = requests.post(f"{BRIDGE_URL}/api/send", json={
        "recipient": recipient,
        "message": message
    })
    if response.status_code != 200:
        return False, response.text
    return True, "Message sent"

def send_file(recipient: str, media_path: str) -> Tuple[bool, str]:
    """Send file."""
    with open(media_path, 'rb') as f:
        response = requests.post(
            f"{BRIDGE_URL}/api/send-media",
            data={"recipient": recipient},
            files={"media": f}
        )
    if response.status_code != 200:
        return False, response.text
    return True, "File sent"

def send_audio_message(recipient: str, media_path: str) -> Tuple[bool, str]:
    """Send audio."""
    with open(media_path, 'rb') as f:
        response = requests.post(
            f"{BRIDGE_URL}/api/send-audio",
            data={"recipient": recipient},
            files={"audio": f}
        )
    if response.status_code != 200:
        return False, response.text
    return True, "Audio sent"

def download_media(message_id: str, chat_jid: str) -> Optional[str]:
    """Download media."""
    response = requests.post(f"{BRIDGE_URL}/api/download-media", json={
        "message_id": message_id,
        "chat_jid": chat_jid
    })
    data = _check_response(response)
    return data.get("file_path")