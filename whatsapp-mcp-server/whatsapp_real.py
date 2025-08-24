"""
WhatsApp functions for MCP server with real bridge communication.
"""

import sqlite3
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, List, Tuple, Dict, Any
import os.path
import requests
import json
import time
import base64
from pathlib import Path

# Configuration
MESSAGES_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'whatsapp-bridge', 'store', 'messages.db')
WHATSAPP_API_BASE_URL = os.getenv("WHATSAPP_API_URL", "http://localhost:8080/api")
MEDIA_DOWNLOAD_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'whatsapp-bridge', 'store', 'media')

# Ensure media directory exists
Path(MEDIA_DOWNLOAD_PATH).mkdir(parents=True, exist_ok=True)

@dataclass
class Message:
    timestamp: datetime
    sender: str
    content: str
    is_from_me: bool
    chat_jid: str
    id: str
    chat_name: Optional[str] = None
    media_type: Optional[str] = None

@dataclass
class Chat:
    jid: str
    name: Optional[str]
    last_message_time: Optional[datetime]
    last_message: Optional[str] = None
    last_sender: Optional[str] = None
    last_is_from_me: Optional[bool] = None

    @property
    def is_group(self) -> bool:
        """Determine if chat is a group based on JID pattern."""
        return self.jid.endswith("@g.us")

@dataclass
class Contact:
    phone_number: str
    name: Optional[str]
    jid: str

def check_bridge_connection() -> bool:
    """Check if the WhatsApp bridge is running and accessible."""
    try:
        response = requests.get(f"{WHATSAPP_API_BASE_URL}/qr", timeout=2)
        return response.status_code == 200
    except:
        return False

def get_qr_code() -> Dict[str, Any]:
    """Get the current QR code status from the WhatsApp bridge."""
    try:
        response = requests.get(f"{WHATSAPP_API_BASE_URL}/qr", timeout=5)
        if response.status_code == 200:
            return response.json()
        return {
            "status": "error",
            "message": f"Bridge returned status {response.status_code}"
        }
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "message": f"Failed to connect to WhatsApp bridge: {str(e)}"
        }

def trigger_reauth() -> Dict[str, Any]:
    """Trigger re-authentication with WhatsApp."""
    try:
        response = requests.post(f"{WHATSAPP_API_BASE_URL}/reauth", timeout=5)
        if response.status_code == 200:
            return response.json()
        return {
            "success": False,
            "message": f"Bridge returned status {response.status_code}"
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "message": f"Failed to trigger re-authentication: {str(e)}"
        }

def wait_for_connection(timeout: int = 180) -> bool:
    """Wait for WhatsApp to be connected."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        status = get_qr_code()
        if status.get("status") == "connected":
            return True
        time.sleep(2)
    return False

def get_db_connection():
    """Get a connection to the messages database."""
    if not os.path.exists(MESSAGES_DB_PATH):
        raise FileNotFoundError(f"Database not found at {MESSAGES_DB_PATH}. Is the WhatsApp bridge running?")
    return sqlite3.connect(MESSAGES_DB_PATH)

def search_contacts(query: str) -> List[Dict[str, Any]]:
    """Search WhatsApp contacts by name or phone number."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Search for chats that match the query
        cursor.execute("""
            SELECT DISTINCT jid, name
            FROM chats
            WHERE (name LIKE ? OR jid LIKE ?)
            AND jid LIKE '%@s.whatsapp.net'
            ORDER BY name
            LIMIT 20
        """, (f"%{query}%", f"%{query}%"))
        
        contacts = []
        for row in cursor.fetchall():
            jid, name = row
            # Extract phone number from JID
            phone = jid.split('@')[0] if '@' in jid else jid
            
            contacts.append({
                "jid": jid,
                "name": name or phone,
                "phone": phone
            })
        
        conn.close()
        return contacts
        
    except Exception as e:
        print(f"Error searching contacts: {e}")
        return []

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
    """Get messages matching the specified criteria with optional context."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build query
        query_parts = ["SELECT messages.timestamp, messages.sender, chats.name, messages.content, messages.is_from_me, chats.jid, messages.id, messages.media_type"]
        query_parts.append("FROM messages")
        query_parts.append("JOIN chats ON messages.chat_jid = chats.jid")
        
        where_clauses = []
        params = []
        
        if after:
            after_dt = datetime.fromisoformat(after)
            where_clauses.append("messages.timestamp > ?")
            params.append(after_dt)
        
        if before:
            before_dt = datetime.fromisoformat(before)
            where_clauses.append("messages.timestamp < ?")
            params.append(before_dt)
        
        if sender_phone_number:
            where_clauses.append("messages.sender = ?")
            params.append(sender_phone_number)
        
        if chat_jid:
            where_clauses.append("messages.chat_jid = ?")
            params.append(chat_jid)
        
        if query:
            where_clauses.append("LOWER(messages.content) LIKE LOWER(?)")
            params.append(f"%{query}%")
        
        if where_clauses:
            query_parts.append("WHERE " + " AND ".join(where_clauses))
        
        query_parts.append("ORDER BY messages.timestamp DESC")
        query_parts.append("LIMIT ? OFFSET ?")
        params.extend([limit, page * limit])
        
        cursor.execute(" ".join(query_parts), tuple(params))
        messages = cursor.fetchall()
        
        # Format messages
        output = []
        for msg in messages:
            timestamp = datetime.fromisoformat(msg[0])
            sender = msg[1]
            chat_name = msg[2]
            content = msg[3]
            is_from_me = msg[4]
            chat_jid = msg[5]
            msg_id = msg[6]
            media_type = msg[7]
            
            # Format message
            msg_str = f"[{timestamp:%Y-%m-%d %H:%M:%S}]"
            if chat_name:
                msg_str += f" Chat: {chat_name}"
            
            sender_display = "Me" if is_from_me else sender
            msg_str += f" From: {sender_display}"
            
            if media_type:
                msg_str += f" [{media_type} - ID: {msg_id} - Chat: {chat_jid}]"
            
            msg_str += f": {content}"
            output.append(msg_str)
        
        conn.close()
        return "\n".join(output) if output else "No messages found"
        
    except Exception as e:
        return f"Error retrieving messages: {e}"

def list_chats(
    query: Optional[str] = None,
    limit: int = 20,
    page: int = 0,
    include_last_message: bool = True,
    sort_by: str = "last_active"
) -> List[Dict[str, Any]]:
    """Get WhatsApp chats matching specified criteria."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build query
        query_parts = ["SELECT chats.jid, chats.name, chats.last_message_time"]
        
        if include_last_message:
            query_parts[0] += ", messages.content, messages.sender, messages.is_from_me"
            query_parts.append("FROM chats")
            query_parts.append("LEFT JOIN messages ON messages.chat_jid = chats.jid")
            query_parts.append("AND messages.timestamp = (SELECT MAX(timestamp) FROM messages WHERE chat_jid = chats.jid)")
        else:
            query_parts.append("FROM chats")
        
        params = []
        if query:
            query_parts.append("WHERE (chats.name LIKE ? OR chats.jid LIKE ?)")
            params.extend([f"%{query}%", f"%{query}%"])
        
        # Sorting
        if sort_by == "name":
            query_parts.append("ORDER BY chats.name")
        else:  # last_active
            query_parts.append("ORDER BY chats.last_message_time DESC")
        
        query_parts.append("LIMIT ? OFFSET ?")
        params.extend([limit, page * limit])
        
        cursor.execute(" ".join(query_parts), tuple(params))
        
        chats = []
        for row in cursor.fetchall():
            chat = {
                "jid": row[0],
                "name": row[1],
                "last_active": row[2]
            }
            
            if include_last_message and len(row) > 3:
                chat["last_message"] = row[3]
                chat["last_sender"] = row[4]
                chat["last_is_from_me"] = row[5]
            
            chats.append(chat)
        
        conn.close()
        return chats
        
    except Exception as e:
        print(f"Error listing chats: {e}")
        return []

def send_message(recipient: str, message: str) -> Tuple[bool, str]:
    """Send a WhatsApp message."""
    try:
        # Check connection first
        if not check_bridge_connection():
            return False, "WhatsApp bridge is not running. Please ensure the bridge is started."
        
        # Check WhatsApp connection status
        status = get_qr_code()
        if status.get("status") != "connected":
            return False, f"WhatsApp is not connected. Status: {status.get('message', 'Unknown')}"
        
        # Send message
        url = f"{WHATSAPP_API_BASE_URL}/send"
        payload = {
            "recipient": recipient,
            "message": message,
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            return result.get("success", False), result.get("message", "Unknown response")
        else:
            return False, f"Error: HTTP {response.status_code} - {response.text}"
            
    except requests.exceptions.RequestException as e:
        return False, f"Failed to send message: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"

def send_file(recipient: str, media_path: str) -> Tuple[bool, str]:
    """Send a file via WhatsApp."""
    try:
        # Validate file exists
        if not os.path.exists(media_path):
            return False, f"File not found: {media_path}"
        
        # Check connection
        if not check_bridge_connection():
            return False, "WhatsApp bridge is not running"
        
        status = get_qr_code()
        if status.get("status") != "connected":
            return False, f"WhatsApp is not connected. Status: {status.get('message', 'Unknown')}"
        
        # Send file
        url = f"{WHATSAPP_API_BASE_URL}/send"
        payload = {
            "recipient": recipient,
            "media_path": media_path
        }
        
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            return result.get("success", False), result.get("message", "Unknown response")
        else:
            return False, f"Error: HTTP {response.status_code} - {response.text}"
            
    except Exception as e:
        return False, f"Failed to send file: {str(e)}"

def send_audio_message(recipient: str, media_path: str) -> Tuple[bool, str]:
    """Send an audio message via WhatsApp."""
    # For now, use the same implementation as send_file
    # The Go bridge handles the distinction based on file type
    return send_file(recipient, media_path)

def download_media(message_id: str, chat_jid: str) -> Optional[str]:
    """Download media from a WhatsApp message."""
    try:
        url = f"{WHATSAPP_API_BASE_URL}/download"
        payload = {
            "message_id": message_id,
            "chat_jid": chat_jid
        }
        
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                return result.get("path")
        
        return None
        
    except Exception as e:
        print(f"Failed to download media: {str(e)}")
        return None

# Additional helper functions

def get_chat(chat_jid: str, include_last_message: bool = True) -> Dict[str, Any]:
    """Get WhatsApp chat metadata by JID."""
    chats = list_chats(query=chat_jid, limit=1, include_last_message=include_last_message)
    if chats:
        return chats[0]
    return {"error": f"Chat {chat_jid} not found"}

def get_direct_chat_by_contact(sender_phone_number: str) -> Dict[str, Any]:
    """Get WhatsApp chat metadata by sender phone number."""
    jid = f"{sender_phone_number}@s.whatsapp.net"
    return get_chat(jid)

def get_contact_chats(jid: str, limit: int = 20, page: int = 0) -> List[Dict[str, Any]]:
    """Get all WhatsApp chats involving the contact."""
    return list_chats(query=jid, limit=limit, page=page)

def get_last_interaction(jid: str) -> str:
    """Get most recent WhatsApp message involving the contact."""
    messages = list_messages(chat_jid=jid, limit=1)
    return messages if messages else "No interactions found"

def get_message_context(
    message_id: str,
    before: int = 5,
    after: int = 5
) -> Dict[str, Any]:
    """Get context around a specific WhatsApp message."""
    # This would require additional implementation in the Go bridge
    # For now, return a placeholder
    return {
        "message": {"id": message_id, "content": "Message context not yet implemented"},
        "before": [],
        "after": []
    }