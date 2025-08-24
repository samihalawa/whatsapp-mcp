"""
Full WhatsApp implementation that connects to the Go bridge.
"""

import os
import sqlite3
import requests
import json
import time
import base64
import io
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
import qrcode
from PIL import Image

# Bridge configuration
BRIDGE_URL = os.getenv("WHATSAPP_BRIDGE_URL", "http://localhost:8080")
DB_PATH = "/app/store/messages.db"
SESSION_DB_PATH = "/app/store/whatsapp_session.db"

def check_bridge_health() -> bool:
    """Check if WhatsApp bridge is running."""
    try:
        response = requests.get(f"{BRIDGE_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def get_connection_status() -> Dict[str, Any]:
    """Get WhatsApp connection status and QR code if not connected."""
    try:
        # Check bridge health first
        if not check_bridge_health():
            return {
                "connected": False,
                "bridge_running": False,
                "message": "WhatsApp bridge is not running. Please wait for it to start."
            }
        
        # Get connection status from bridge
        response = requests.get(f"{BRIDGE_URL}/api/status", timeout=5)
        data = response.json()
        
        if not data.get("connected", False):
            # Get QR code if not connected
            qr_response = requests.get(f"{BRIDGE_URL}/api/qr", timeout=5)
            if qr_response.status_code == 200:
                qr_data = qr_response.json()
                return {
                    "connected": False,
                    "bridge_running": True,
                    "qr_code": qr_data.get("qr_string"),
                    "qr_image": qr_data.get("qr_base64"),
                    "message": "Please scan the QR code with WhatsApp on your phone"
                }
        
        return {
            "connected": True,
            "bridge_running": True,
            "phone_number": data.get("phone_number"),
            "message": "WhatsApp is connected"
        }
    except Exception as e:
        return {
            "connected": False,
            "bridge_running": False,
            "error": str(e),
            "message": "Failed to get connection status"
        }

def get_qr_code() -> Dict[str, Any]:
    """Get WhatsApp QR code for authentication."""
    try:
        response = requests.get(f"{BRIDGE_URL}/api/qr", timeout=5)
        if response.status_code == 200:
            data = response.json()
            
            # Generate QR code image if we have the string
            qr_string = data.get("qr_string")
            if qr_string:
                # Create QR code image
                qr = qrcode.QRCode(version=1, box_size=10, border=5)
                qr.add_data(qr_string)
                qr.make(fit=True)
                
                # Convert to base64
                img = qr.make_image(fill_color="black", back_color="white")
                buffered = io.BytesIO()
                img.save(buffered, format="PNG")
                img_base64 = base64.b64encode(buffered.getvalue()).decode()
                
                return {
                    "success": True,
                    "qr_string": qr_string,
                    "qr_ascii": data.get("qr_ascii", qr_string),
                    "qr_image": f"data:image/png;base64,{img_base64}",
                    "message": "Scan this QR code with WhatsApp"
                }
        
        return {
            "success": False,
            "message": "No QR code available. WhatsApp might already be connected."
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to get QR code"
        }

def wait_for_connection(timeout: int = 60) -> Dict[str, Any]:
    """Wait for WhatsApp to be connected."""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        status = get_connection_status()
        if status.get("connected"):
            return {
                "success": True,
                "message": "WhatsApp is now connected",
                "phone_number": status.get("phone_number")
            }
        time.sleep(2)
    
    return {
        "success": False,
        "message": f"Timeout waiting for WhatsApp connection after {timeout} seconds"
    }

def search_contacts(query: str) -> List[Dict[str, Any]]:
    """Search WhatsApp contacts by name or phone number."""
    if not os.path.exists(DB_PATH):
        return []
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT sender_jid, sender_name, sender_phone_number
            FROM messages
            WHERE sender_name LIKE ? OR sender_phone_number LIKE ?
            LIMIT 20
        """, (f"%{query}%", f"%{query}%"))
        
        contacts = []
        for row in cursor.fetchall():
            contacts.append({
                "jid": row["sender_jid"],
                "name": row["sender_name"],
                "phone": row["sender_phone_number"]
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
    """Get WhatsApp messages matching specified criteria."""
    if not os.path.exists(DB_PATH):
        return "No messages found"
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Build query
        conditions = []
        params = []
        
        if after:
            conditions.append("timestamp > ?")
            params.append(after)
        
        if before:
            conditions.append("timestamp < ?")
            params.append(before)
        
        if sender_phone_number:
            conditions.append("sender_phone_number = ?")
            params.append(sender_phone_number)
        
        if chat_jid:
            conditions.append("chat_jid = ?")
            params.append(chat_jid)
        
        if query:
            conditions.append("message_text LIKE ?")
            params.append(f"%{query}%")
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        cursor.execute(f"""
            SELECT * FROM messages
            WHERE {where_clause}
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
        """, params + [limit, page * limit])
        
        messages = []
        for row in cursor.fetchall():
            timestamp = datetime.fromisoformat(row["timestamp"])
            formatted = f"[{timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {row['sender_name']}: {row['message_text']}"
            messages.append(formatted)
        
        conn.close()
        return "\n".join(messages) if messages else "No messages found"
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
    if not os.path.exists(DB_PATH):
        return []
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get unique chats
        cursor.execute("""
            SELECT chat_jid, chat_name, MAX(timestamp) as last_active, 
                   MAX(message_text) as last_message
            FROM messages
            WHERE chat_name LIKE ? OR chat_jid LIKE ?
            GROUP BY chat_jid
            ORDER BY last_active DESC
            LIMIT ? OFFSET ?
        """, (f"%{query}%" if query else "%", f"%{query}%" if query else "%", limit, page * limit))
        
        chats = []
        for row in cursor.fetchall():
            chat = {
                "jid": row["chat_jid"],
                "name": row["chat_name"],
                "last_active": row["last_active"]
            }
            if include_last_message:
                chat["last_message"] = row["last_message"]
            chats.append(chat)
        
        conn.close()
        return chats
    except Exception as e:
        print(f"Error listing chats: {e}")
        return []

def get_chat(chat_jid: str, include_last_message: bool = True) -> Dict[str, Any]:
    """Get WhatsApp chat metadata by JID."""
    if not os.path.exists(DB_PATH):
        return {"jid": chat_jid, "name": "Unknown"}
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT chat_jid, chat_name, MAX(timestamp) as last_active,
                   MAX(message_text) as last_message
            FROM messages
            WHERE chat_jid = ?
            GROUP BY chat_jid
        """, (chat_jid,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            chat = {
                "jid": row["chat_jid"],
                "name": row["chat_name"],
                "last_active": row["last_active"]
            }
            if include_last_message:
                chat["last_message"] = row["last_message"]
            return chat
        
        return {"jid": chat_jid, "name": "Unknown"}
    except Exception as e:
        return {"jid": chat_jid, "name": "Unknown", "error": str(e)}

def get_direct_chat_by_contact(sender_phone_number: str) -> Dict[str, Any]:
    """Get WhatsApp chat metadata by sender phone number."""
    jid = f"{sender_phone_number}@s.whatsapp.net"
    return get_chat(jid)

def get_contact_chats(jid: str, limit: int = 20, page: int = 0) -> List[Dict[str, Any]]:
    """Get all WhatsApp chats involving the contact."""
    if not os.path.exists(DB_PATH):
        return []
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT chat_jid, chat_name
            FROM messages
            WHERE sender_jid = ?
            LIMIT ? OFFSET ?
        """, (jid, limit, page * limit))
        
        chats = []
        for row in cursor.fetchall():
            chats.append({
                "jid": row["chat_jid"],
                "name": row["chat_name"],
                "type": "group" if "@g.us" in row["chat_jid"] else "individual"
            })
        
        conn.close()
        return chats
    except Exception as e:
        print(f"Error getting contact chats: {e}")
        return []

def get_last_interaction(jid: str) -> str:
    """Get most recent WhatsApp message involving the contact."""
    if not os.path.exists(DB_PATH):
        return "No interactions found"
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM messages
            WHERE sender_jid = ? OR chat_jid = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (jid, jid))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            timestamp = datetime.fromisoformat(row["timestamp"])
            return f"[{timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {row['sender_name']}: {row['message_text']}"
        
        return "No interactions found"
    except Exception as e:
        return f"Error: {e}"

def get_message_context(
    message_id: str,
    before: int = 5,
    after: int = 5
) -> Dict[str, Any]:
    """Get context around a specific WhatsApp message."""
    # This would require message IDs to be stored in the database
    # For now, return a placeholder
    return {
        "message": {"id": message_id, "content": "Message context not available"},
        "before": [],
        "after": []
    }

def send_message(recipient: str, message: str) -> Tuple[bool, str]:
    """Send a WhatsApp message."""
    try:
        # Check connection first
        status = get_connection_status()
        if not status.get("connected"):
            return False, "WhatsApp is not connected. Please scan the QR code first."
        
        # Send via bridge API
        response = requests.post(
            f"{BRIDGE_URL}/api/send",
            json={"recipient": recipient, "message": message},
            timeout=10
        )
        
        if response.status_code == 200:
            return True, f"Message sent to {recipient}"
        else:
            return False, f"Failed to send message: {response.text}"
    except Exception as e:
        return False, f"Error sending message: {e}"

def send_file(recipient: str, media_path: str) -> Tuple[bool, str]:
    """Send a file via WhatsApp."""
    try:
        # Check connection first
        status = get_connection_status()
        if not status.get("connected"):
            return False, "WhatsApp is not connected. Please scan the QR code first."
        
        # Send via bridge API
        with open(media_path, 'rb') as f:
            files = {'media': f}
            data = {'recipient': recipient}
            response = requests.post(
                f"{BRIDGE_URL}/api/send-media",
                data=data,
                files=files,
                timeout=30
            )
        
        if response.status_code == 200:
            return True, f"File sent to {recipient}"
        else:
            return False, f"Failed to send file: {response.text}"
    except Exception as e:
        return False, f"Error sending file: {e}"

def send_audio_message(recipient: str, media_path: str) -> Tuple[bool, str]:
    """Send an audio message via WhatsApp."""
    try:
        # Check connection first
        status = get_connection_status()
        if not status.get("connected"):
            return False, "WhatsApp is not connected. Please scan the QR code first."
        
        # Send via bridge API as audio
        with open(media_path, 'rb') as f:
            files = {'audio': f}
            data = {'recipient': recipient}
            response = requests.post(
                f"{BRIDGE_URL}/api/send-audio",
                data=data,
                files=files,
                timeout=30
            )
        
        if response.status_code == 200:
            return True, f"Audio message sent to {recipient}"
        else:
            return False, f"Failed to send audio: {response.text}"
    except Exception as e:
        return False, f"Error sending audio: {e}"

def download_media(message_id: str, chat_jid: str) -> Optional[str]:
    """Download media from a WhatsApp message."""
    try:
        response = requests.post(
            f"{BRIDGE_URL}/api/download-media",
            json={"message_id": message_id, "chat_jid": chat_jid},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("file_path")
        
        return None
    except Exception as e:
        print(f"Error downloading media: {e}")
        return None