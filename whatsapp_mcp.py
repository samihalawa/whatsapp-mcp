#!/usr/bin/env python3
"""
WhatsApp MCP Server

Production-ready MCP server for WhatsApp integration via whatsmeow library.
Provides comprehensive WhatsApp functionality including messaging, group management,
account operations, and chat management.

Requires a running WhatsApp Go server instance (based on whatsmeow).
"""

from typing import Optional, List, Dict, Any, Literal
from enum import Enum
import httpx
import json
import base64
from pathlib import Path
from pydantic import BaseModel, Field, field_validator, ConfigDict
from mcp.server.fastmcp import FastMCP

# Initialize the MCP server
mcp = FastMCP("whatsapp_mcp")

# Constants
CHARACTER_LIMIT = 25000
DEFAULT_TIMEOUT = 30.0

# Environment variables with defaults
import os
WHATSAPP_API_URL = os.getenv("WHATSAPP_API_URL", "http://localhost:3000")
WHATSAPP_AUTH_USER = os.getenv("WHATSAPP_AUTH_USER", "")
WHATSAPP_AUTH_PASS = os.getenv("WHATSAPP_AUTH_PASS", "")


# ============================================================================
# ENUMS
# ============================================================================

class ResponseFormat(str, Enum):
    """Output format for tool responses."""
    MARKDOWN = "markdown"
    JSON = "json"


class PresenceType(str, Enum):
    """WhatsApp presence types."""
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"


class ChatPresenceType(str, Enum):
    """WhatsApp chat presence types."""
    COMPOSING = "composing"
    PAUSED = "paused"


class PrivacySetting(str, Enum):
    """WhatsApp privacy settings."""
    ALL = "all"
    CONTACTS = "contacts"
    CONTACT_BLACKLIST = "contact_blacklist"
    NONE = "none"


# ============================================================================
# PYDANTIC INPUT MODELS
# ============================================================================

class LoginInput(BaseModel):
    """Input for WhatsApp login via QR code."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra='forbid')
    
    device_name: Optional[str] = Field(
        default="WhatsApp MCP",
        description="Device name to display in WhatsApp (e.g., 'My Bot', 'AI Assistant')",
        max_length=100
    )


class LoginWithCodeInput(BaseModel):
    """Input for WhatsApp login via phone code."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra='forbid')
    
    phone_number: str = Field(
        ...,
        description="Phone number with country code (e.g., '+1234567890', '+447700900123')",
        pattern=r'^\+\d{10,15}$'
    )


class SendMessageInput(BaseModel):
    """Input for sending text messages."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra='forbid')
    
    recipient: str = Field(
        ...,
        description="Recipient WhatsApp ID (e.g., '1234567890@s.whatsapp.net' for individual, '1234567890@g.us' for group)",
        min_length=5,
        max_length=100
    )
    message: str = Field(
        ...,
        description="Text message to send",
        min_length=1,
        max_length=4096
    )
    quoted_message_id: Optional[str] = Field(
        default=None,
        description="Message ID to reply to (optional)"
    )


class SendImageInput(BaseModel):
    """Input for sending image messages."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra='forbid')
    
    recipient: str = Field(..., description="Recipient WhatsApp ID", min_length=5, max_length=100)
    image_path: Optional[str] = Field(default=None, description="Local file path to image")
    image_url: Optional[str] = Field(default=None, description="URL to image file")
    image_base64: Optional[str] = Field(default=None, description="Base64 encoded image data")
    caption: Optional[str] = Field(default=None, description="Image caption", max_length=1024)
    quoted_message_id: Optional[str] = Field(default=None, description="Message ID to reply to")
    
    @field_validator('image_path', 'image_url', 'image_base64')
    @classmethod
    def check_one_source(cls, v, info):
        """Ensure exactly one image source is provided."""
        sources = [info.data.get('image_path'), info.data.get('image_url'), info.data.get('image_base64')]
        if sum(bool(s) for s in sources) != 1:
            raise ValueError("Provide exactly one of: image_path, image_url, or image_base64")
        return v


class SendVideoInput(BaseModel):
    """Input for sending video messages."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra='forbid')
    
    recipient: str = Field(..., description="Recipient WhatsApp ID", min_length=5, max_length=100)
    video_path: Optional[str] = Field(default=None, description="Local file path to video")
    video_url: Optional[str] = Field(default=None, description="URL to video file")
    video_base64: Optional[str] = Field(default=None, description="Base64 encoded video data")
    caption: Optional[str] = Field(default=None, description="Video caption", max_length=1024)
    quoted_message_id: Optional[str] = Field(default=None, description="Message ID to reply to")


class SendAudioInput(BaseModel):
    """Input for sending audio messages."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra='forbid')
    
    recipient: str = Field(..., description="Recipient WhatsApp ID", min_length=5, max_length=100)
    audio_path: Optional[str] = Field(default=None, description="Local file path to audio")
    audio_url: Optional[str] = Field(default=None, description="URL to audio file")
    audio_base64: Optional[str] = Field(default=None, description="Base64 encoded audio data")
    is_voice_note: bool = Field(default=False, description="Send as voice note (PTT)")


class SendFileInput(BaseModel):
    """Input for sending document files."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra='forbid')
    
    recipient: str = Field(..., description="Recipient WhatsApp ID", min_length=5, max_length=100)
    file_path: Optional[str] = Field(default=None, description="Local file path")
    file_url: Optional[str] = Field(default=None, description="URL to file")
    file_base64: Optional[str] = Field(default=None, description="Base64 encoded file data")
    filename: Optional[str] = Field(default=None, description="Custom filename", max_length=255)
    caption: Optional[str] = Field(default=None, description="File caption", max_length=1024)


class SendLocationInput(BaseModel):
    """Input for sending location messages."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra='forbid')
    
    recipient: str = Field(..., description="Recipient WhatsApp ID", min_length=5, max_length=100)
    latitude: float = Field(..., description="Latitude coordinate", ge=-90.0, le=90.0)
    longitude: float = Field(..., description="Longitude coordinate", ge=-180.0, le=180.0)
    name: Optional[str] = Field(default=None, description="Location name", max_length=200)
    address: Optional[str] = Field(default=None, description="Location address", max_length=500)


class SendContactInput(BaseModel):
    """Input for sending contact cards."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra='forbid')
    
    recipient: str = Field(..., description="Recipient WhatsApp ID", min_length=5, max_length=100)
    contact_name: str = Field(..., description="Contact display name", min_length=1, max_length=100)
    contact_phone: str = Field(
        ...,
        description="Contact phone number with country code",
        pattern=r'^\+?\d{10,15}$'
    )


class SendPollInput(BaseModel):
    """Input for sending poll messages."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra='forbid')
    
    recipient: str = Field(..., description="Recipient WhatsApp ID", min_length=5, max_length=100)
    question: str = Field(..., description="Poll question", min_length=1, max_length=255)
    options: List[str] = Field(
        ...,
        description="Poll options (2-12 choices)",
        min_length=2,
        max_length=12
    )
    selectable_count: int = Field(
        default=1,
        description="Number of options users can select (1 for single choice)",
        ge=1,
        le=12
    )


class SendPresenceInput(BaseModel):
    """Input for setting user presence."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra='forbid')
    
    presence: PresenceType = Field(..., description="Presence status to set")


class SendChatPresenceInput(BaseModel):
    """Input for setting chat-specific presence (typing indicator)."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra='forbid')
    
    recipient: str = Field(..., description="Chat WhatsApp ID", min_length=5, max_length=100)
    presence: ChatPresenceType = Field(..., description="Chat presence type")


class MessageActionInput(BaseModel):
    """Input for message actions (delete, revoke, read)."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra='forbid')
    
    recipient: str = Field(..., description="Chat WhatsApp ID", min_length=5, max_length=100)
    message_id: str = Field(..., description="Message ID to act on", min_length=1, max_length=100)


class ReactMessageInput(BaseModel):
    """Input for reacting to messages."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra='forbid')
    
    recipient: str = Field(..., description="Chat WhatsApp ID", min_length=5, max_length=100)
    message_id: str = Field(..., description="Message ID to react to", min_length=1, max_length=100)
    emoji: str = Field(..., description="Emoji reaction (e.g., '👍', '❤️', '' to remove)", max_length=10)


class UpdateMessageInput(BaseModel):
    """Input for updating (editing) messages."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra='forbid')
    
    recipient: str = Field(..., description="Chat WhatsApp ID", min_length=5, max_length=100)
    message_id: str = Field(..., description="Message ID to edit", min_length=1, max_length=100)
    new_text: str = Field(..., description="New message text", min_length=1, max_length=4096)


class ListChatsInput(BaseModel):
    """Input for listing chats."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra='forbid')
    
    limit: int = Field(default=50, description="Maximum chats to return", ge=1, le=200)
    offset: int = Field(default=0, description="Pagination offset", ge=0)
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )


class GetChatMessagesInput(BaseModel):
    """Input for getting chat messages."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra='forbid')
    
    chat_id: str = Field(..., description="Chat WhatsApp ID", min_length=5, max_length=100)
    limit: int = Field(default=50, description="Maximum messages to return", ge=1, le=200)
    offset: int = Field(default=0, description="Pagination offset", ge=0)
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )


class CreateGroupInput(BaseModel):
    """Input for creating WhatsApp groups."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra='forbid')
    
    name: str = Field(..., description="Group name", min_length=1, max_length=100)
    participants: List[str] = Field(
        ...,
        description="List of participant phone numbers/JIDs (e.g., ['1234567890@s.whatsapp.net'])",
        min_length=1,
        max_length=256
    )


class JoinGroupInput(BaseModel):
    """Input for joining groups via invite link."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra='forbid')
    
    invite_link: str = Field(
        ...,
        description="WhatsApp group invite link (e.g., 'https://chat.whatsapp.com/XXXX')",
        pattern=r'^https://chat\.whatsapp\.com/[\w-]+'
    )


class GroupInfoInput(BaseModel):
    """Input for getting group information."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra='forbid')
    
    group_id: str = Field(..., description="Group JID (e.g., '1234567890@g.us')", min_length=5, max_length=100)
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )


class ManageParticipantsInput(BaseModel):
    """Input for managing group participants."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra='forbid')
    
    group_id: str = Field(..., description="Group JID", min_length=5, max_length=100)
    participants: List[str] = Field(
        ...,
        description="Participant JIDs to add/remove",
        min_length=1,
        max_length=100
    )
    action: Literal["add", "remove", "promote", "demote"] = Field(
        ...,
        description="Action: 'add' (add members), 'remove' (kick), 'promote' (make admin), 'demote' (remove admin)"
    )


class UpdateGroupInput(BaseModel):
    """Input for updating group settings."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra='forbid')
    
    group_id: str = Field(..., description="Group JID", min_length=5, max_length=100)
    name: Optional[str] = Field(default=None, description="New group name", max_length=100)
    description: Optional[str] = Field(default=None, description="New group description", max_length=512)
    locked: Optional[bool] = Field(default=None, description="Lock group settings (only admins can edit)")
    announce: Optional[bool] = Field(default=None, description="Only admins can send messages")


class SetGroupPhotoInput(BaseModel):
    """Input for setting group photo."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra='forbid')
    
    group_id: str = Field(..., description="Group JID", min_length=5, max_length=100)
    image_path: Optional[str] = Field(default=None, description="Local image path")
    image_url: Optional[str] = Field(default=None, description="Image URL")
    image_base64: Optional[str] = Field(default=None, description="Base64 encoded image")


class GetUserInfoInput(BaseModel):
    """Input for getting user information."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra='forbid')
    
    phone_numbers: List[str] = Field(
        ...,
        description="Phone numbers to check (e.g., ['1234567890', '+447700900123'])",
        min_length=1,
        max_length=50
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )


class UpdateProfileInput(BaseModel):
    """Input for updating user profile."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra='forbid')
    
    push_name: Optional[str] = Field(default=None, description="Display name", max_length=100)
    status: Optional[str] = Field(default=None, description="Status message", max_length=139)


class SetAvatarInput(BaseModel):
    """Input for setting profile avatar."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra='forbid')
    
    image_path: Optional[str] = Field(default=None, description="Local image path")
    image_url: Optional[str] = Field(default=None, description="Image URL")
    image_base64: Optional[str] = Field(default=None, description="Base64 encoded image")


class UpdatePrivacyInput(BaseModel):
    """Input for updating privacy settings."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra='forbid')
    
    setting_type: Literal["last_seen", "online", "profile_picture", "status", "read_receipts", "groups"] = Field(
        ...,
        description="Privacy setting to update"
    )
    value: PrivacySetting = Field(..., description="Privacy value")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _get_auth() -> Optional[tuple]:
    """Get basic auth credentials if configured."""
    if WHATSAPP_AUTH_USER and WHATSAPP_AUTH_PASS:
        return (WHATSAPP_AUTH_USER, WHATSAPP_AUTH_PASS)
    return None


async def _make_api_request(
    endpoint: str,
    method: str = "GET",
    json_data: Optional[Dict[str, Any]] = None,
    files: Optional[Dict[str, Any]] = None,
    timeout: float = DEFAULT_TIMEOUT
) -> Dict[str, Any]:
    """
    Make HTTP request to WhatsApp API.
    
    Args:
        endpoint: API endpoint (e.g., '/send/text')
        method: HTTP method
        json_data: JSON payload
        files: File upload data
        timeout: Request timeout in seconds
    
    Returns:
        API response as dictionary
        
    Raises:
        Exception with formatted error message
    """
    url = f"{WHATSAPP_API_URL}{endpoint}"
    auth = _get_auth()
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method,
                url,
                json=json_data,
                files=files,
                auth=auth,
                timeout=timeout
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        return _handle_http_error(e)
    except httpx.TimeoutException:
        raise Exception(f"Request timed out after {timeout} seconds. The WhatsApp server may be slow or unresponsive.")
    except httpx.ConnectError:
        raise Exception(
            f"Could not connect to WhatsApp server at {WHATSAPP_API_URL}. "
            "Ensure the server is running and the URL is correct. "
            "Set WHATSAPP_API_URL environment variable if needed."
        )
    except Exception as e:
        raise Exception(f"Unexpected error: {type(e).__name__}: {str(e)}")


def _handle_http_error(e: httpx.HTTPStatusError) -> Dict[str, Any]:
    """Format HTTP errors with actionable messages."""
    status = e.response.status_code
    
    if status == 400:
        error_msg = "Invalid request parameters. Check that all required fields are provided correctly."
    elif status == 401:
        error_msg = "Authentication failed. Verify WHATSAPP_AUTH_USER and WHATSAPP_AUTH_PASS are set correctly."
    elif status == 403:
        error_msg = "Access forbidden. You may not have permission for this operation."
    elif status == 404:
        error_msg = "Resource not found. The chat, group, or message may not exist."
    elif status == 429:
        error_msg = "Rate limit exceeded. Wait a moment before retrying."
    elif status == 500:
        error_msg = "WhatsApp server error. The server may be experiencing issues."
    else:
        error_msg = f"Request failed with status {status}"
    
    try:
        error_detail = e.response.json()
        if isinstance(error_detail, dict):
            if "error" in error_detail:
                error_msg = f"{error_msg}: {error_detail['error']}"
            elif "message" in error_detail:
                error_msg = f"{error_msg}: {error_detail['message']}"
    except:
        pass
    
    raise Exception(error_msg)


def _format_response(data: Any, format_type: ResponseFormat = ResponseFormat.JSON) -> str:
    """
    Format response data as JSON or Markdown.
    
    Args:
        data: Response data to format
        format_type: Output format
        
    Returns:
        Formatted string
    """
    if format_type == ResponseFormat.JSON:
        result = json.dumps(data, indent=2, ensure_ascii=False)
    else:
        # Markdown formatting
        if isinstance(data, dict):
            result = _dict_to_markdown(data)
        elif isinstance(data, list):
            result = _list_to_markdown(data)
        else:
            result = str(data)
    
    # Enforce character limit
    if len(result) > CHARACTER_LIMIT:
        truncated = result[:CHARACTER_LIMIT]
        result = f"{truncated}\n\n[Response truncated at {CHARACTER_LIMIT} characters. Use filters or pagination to get more specific results.]"
    
    return result


def _dict_to_markdown(data: Dict[str, Any], level: int = 0) -> str:
    """Convert dictionary to readable markdown format."""
    lines = []
    indent = "  " * level
    
    for key, value in data.items():
        if isinstance(value, dict):
            lines.append(f"{indent}**{key}:**")
            lines.append(_dict_to_markdown(value, level + 1))
        elif isinstance(value, list):
            lines.append(f"{indent}**{key}:**")
            if value and isinstance(value[0], dict):
                for i, item in enumerate(value):
                    lines.append(f"{indent}  {i+1}.")
                    lines.append(_dict_to_markdown(item, level + 2))
            else:
                for item in value:
                    lines.append(f"{indent}  - {item}")
        else:
            lines.append(f"{indent}**{key}:** {value}")
    
    return "\n".join(lines)


def _list_to_markdown(data: List[Any]) -> str:
    """Convert list to readable markdown format."""
    if not data:
        return "No items found."
    
    if isinstance(data[0], dict):
        lines = []
        for i, item in enumerate(data):
            lines.append(f"\n### Item {i+1}")
            lines.append(_dict_to_markdown(item, 0))
        return "\n".join(lines)
    else:
        return "\n".join([f"- {item}" for item in data])


def _read_file_as_base64(file_path: str) -> str:
    """Read file and encode as base64."""
    try:
        with open(file_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    except FileNotFoundError:
        raise Exception(f"File not found: {file_path}. Provide a valid file path.")
    except Exception as e:
        raise Exception(f"Error reading file: {str(e)}")


async def _download_file_as_base64(url: str) -> str:
    """Download file from URL and encode as base64."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=60.0)
            response.raise_for_status()
            return base64.b64encode(response.content).decode('utf-8')
    except Exception as e:
        raise Exception(f"Error downloading file from URL: {str(e)}")




# ============================================================================
# AUTHENTICATION TOOLS
# ============================================================================

@mcp.tool(
    name="whatsapp_login_qr",
    annotations={
        "title": "Login to WhatsApp via QR Code",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def whatsapp_login_qr(params: LoginInput) -> str:
    """
    Initiate WhatsApp login via QR code scanning.
    
    This tool generates a QR code that needs to be scanned with the WhatsApp mobile app
    to link the device. The QR code will be displayed in the server's web interface or
    returned as a data URL.
    
    Args:
        params (LoginInput): Login parameters containing:
            - device_name (Optional[str]): Device name shown in WhatsApp (default: "WhatsApp MCP")
    
    Returns:
        str: JSON response with QR code data and login instructions
    
    Examples:
        - Use when: User wants to connect WhatsApp account for the first time
        - Use when: Previous session expired and re-authentication is needed
        - Don't use when: Already logged in (use whatsapp_reconnect instead)
        - Don't use when: Want to login via phone code (use whatsapp_login_code instead)
    
    Error Handling:
        - Returns error if server is unreachable
        - Returns error if already logged in (must logout first)
        - Provides QR code expiration time and renewal instructions
    """
    try:
        response = await _make_api_request(
            "/app/login",
            method="POST",
            json_data={"device_name": params.device_name}
        )
        return json.dumps(response, indent=2)
    except Exception as e:
        return f"Error initiating login: {str(e)}"


@mcp.tool(
    name="whatsapp_login_code",
    annotations={
        "title": "Login to WhatsApp via Phone Code",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def whatsapp_login_code(params: LoginWithCodeInput) -> str:
    """
    Initiate WhatsApp login via SMS/call verification code.
    
    This tool initiates login by sending a verification code to the specified phone number.
    The code will be received via SMS or phone call and must be provided in a follow-up request.
    
    Args:
        params (LoginWithCodeInput): Login parameters containing:
            - phone_number (str): Phone number with country code (e.g., '+1234567890')
    
    Returns:
        str: JSON response with next steps for code verification
    
    Examples:
        - Use when: User prefers code-based authentication over QR scanning
        - Use when: Automated bot setup without manual QR scanning
        - Don't use when: Already logged in
    
    Error Handling:
        - Returns error if phone number format is invalid
        - Returns error if number is not registered with WhatsApp
        - Provides instructions for code entry
    """
    try:
        response = await _make_api_request(
            "/app/login-with-code",
            method="POST",
            json_data={"phone": params.phone_number}
        )
        return json.dumps(response, indent=2)
    except Exception as e:
        return f"Error initiating code login: {str(e)}"


@mcp.tool(
    name="whatsapp_logout",
    annotations={
        "title": "Logout from WhatsApp",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def whatsapp_logout() -> str:
    """
    Logout from WhatsApp and disconnect the current session.
    
    This tool terminates the WhatsApp session and removes device pairing. After logout,
    a new QR code scan or phone verification is required to reconnect.
    
    WARNING: This is a destructive operation that will:
    - Disconnect all active WhatsApp connections
    - Remove device pairing from WhatsApp servers
    - Require re-authentication to use WhatsApp again
    
    Returns:
        str: Confirmation message of successful logout
    
    Examples:
        - Use when: Need to switch WhatsApp accounts
        - Use when: Decommissioning the bot/integration
        - Use when: Security requires session termination
        - Don't use when: Temporary disconnection needed (use whatsapp_reconnect instead)
    
    Error Handling:
        - Returns success even if already logged out
        - Provides next steps for re-authentication
    """
    try:
        response = await _make_api_request("/app/logout", method="POST")
        return json.dumps(response, indent=2)
    except Exception as e:
        return f"Error during logout: {str(e)}"


@mcp.tool(
    name="whatsapp_reconnect",
    annotations={
        "title": "Reconnect to WhatsApp",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def whatsapp_reconnect() -> str:
    """
    Reconnect to WhatsApp servers without re-authentication.
    
    This tool attempts to reconnect to WhatsApp using existing credentials.
    Use this when the connection was temporarily lost but the device is still paired.
    
    Returns:
        str: Status of reconnection attempt
    
    Examples:
        - Use when: Connection dropped due to network issues
        - Use when: Server was restarted but credentials still valid
        - Use when: "Disconnected" status shown but still paired
        - Don't use when: Never logged in (use whatsapp_login_qr instead)
        - Don't use when: Explicitly logged out (requires re-authentication)
    
    Error Handling:
        - Returns error if not previously authenticated
        - Returns error if device pairing was removed
        - Suggests re-authentication if reconnection fails
    """
    try:
        response = await _make_api_request("/app/reconnect", method="POST")
        return json.dumps(response, indent=2)
    except Exception as e:
        return f"Error during reconnect: {str(e)}"


# ============================================================================
# MESSAGING TOOLS
# ============================================================================

@mcp.tool(
    name="whatsapp_send_message",
    annotations={
        "title": "Send Text Message",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def whatsapp_send_message(params: SendMessageInput) -> str:
    """
    Send a text message to a WhatsApp contact or group.
    
    This tool sends plain text messages with optional reply functionality.
    Supports Unicode characters, emojis, and formatting (bold, italic).
    
    Args:
        params (SendMessageInput): Message parameters containing:
            - recipient (str): WhatsApp JID (e.g., '1234567890@s.whatsapp.net' for user, '1234567890@g.us' for group)
            - message (str): Text message content (1-4096 characters)
            - quoted_message_id (Optional[str]): Message ID to reply to
    
    Returns:
        str: JSON response with message ID and delivery status
    
    Examples:
        - Use when: Sending text messages to contacts
        - Use when: Replying to specific messages (provide quoted_message_id)
        - Use when: Sending to groups (use group JID with @g.us)
        - Don't use for: Images, videos, or files (use specific media tools)
        - Don't use for: Bulk messaging (send one at a time)
    
    Error Handling:
        - Returns error if recipient JID format invalid
        - Returns error if message too long (>4096 characters)
        - Returns error if quoted message not found
        - Provides message ID for tracking delivery
    """
    try:
        payload = {
            "recipient": params.recipient,
            "message": params.message
        }
        if params.quoted_message_id:
            payload["quoted_message_id"] = params.quoted_message_id
        
        response = await _make_api_request("/send/message", method="POST", json_data=payload)
        return json.dumps(response, indent=2)
    except Exception as e:
        return f"Error sending message: {str(e)}"


@mcp.tool(
    name="whatsapp_send_image",
    annotations={
        "title": "Send Image Message",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def whatsapp_send_image(params: SendImageInput) -> str:
    """
    Send an image message to a WhatsApp contact or group.
    
    Supports multiple image sources: local file, URL, or base64 encoded data.
    Automatically handles image compression and format conversion.
    
    Args:
        params (SendImageInput): Image parameters containing:
            - recipient (str): WhatsApp JID
            - image_path (Optional[str]): Local file path (e.g., '/path/to/image.jpg')
            - image_url (Optional[str]): Image URL (e.g., 'https://example.com/image.png')
            - image_base64 (Optional[str]): Base64 encoded image data
            - caption (Optional[str]): Image caption (max 1024 characters)
            - quoted_message_id (Optional[str]): Message ID to reply to
    
    Returns:
        str: JSON response with message ID
    
    Examples:
        - Use when: Sending photos, screenshots, or graphics
        - Use when: Sharing images with captions
        - Provide exactly one of: image_path, image_url, or image_base64
        - Supported formats: JPG, PNG, GIF, WebP
    
    Error Handling:
        - Returns error if no image source provided
        - Returns error if multiple sources provided
        - Returns error if file not found or URL unreachable
        - Returns error if image format not supported
    """
    try:
        # Prepare image data
        image_data = None
        if params.image_path:
            image_data = _read_file_as_base64(params.image_path)
        elif params.image_url:
            image_data = await _download_file_as_base64(params.image_url)
        elif params.image_base64:
            image_data = params.image_base64
        
        payload = {
            "recipient": params.recipient,
            "image": image_data,
            "caption": params.caption or ""
        }
        if params.quoted_message_id:
            payload["quoted_message_id"] = params.quoted_message_id
        
        response = await _make_api_request("/send/image", method="POST", json_data=payload)
        return json.dumps(response, indent=2)
    except Exception as e:
        return f"Error sending image: {str(e)}"



@mcp.tool(
    name="whatsapp_send_video",
    annotations={
        "title": "Send Video Message",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def whatsapp_send_video(params: SendVideoInput) -> str:
    """Send video message with optional caption."""
    try:
        video_data = None
        if params.video_path:
            video_data = _read_file_as_base64(params.video_path)
        elif params.video_url:
            video_data = await _download_file_as_base64(params.video_url)
        elif params.video_base64:
            video_data = params.video_base64
        
        payload = {
            "recipient": params.recipient,
            "video": video_data,
            "caption": params.caption or ""
        }
        if params.quoted_message_id:
            payload["quoted_message_id"] = params.quoted_message_id
        
        response = await _make_api_request("/send/video", method="POST", json_data=payload)
        return json.dumps(response, indent=2)
    except Exception as e:
        return f"Error sending video: {str(e)}"


@mcp.tool(
    name="whatsapp_send_audio",
    annotations={
        "title": "Send Audio Message",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def whatsapp_send_audio(params: SendAudioInput) -> str:
    """Send audio file or voice note (PTT)."""
    try:
        audio_data = None
        if params.audio_path:
            audio_data = _read_file_as_base64(params.audio_path)
        elif params.audio_url:
            audio_data = await _download_file_as_base64(params.audio_url)
        elif params.audio_base64:
            audio_data = params.audio_base64
        
        payload = {
            "recipient": params.recipient,
            "audio": audio_data,
            "ptt": params.is_voice_note
        }
        
        response = await _make_api_request("/send/audio", method="POST", json_data=payload)
        return json.dumps(response, indent=2)
    except Exception as e:
        return f"Error sending audio: {str(e)}"


@mcp.tool(
    name="whatsapp_send_file",
    annotations={
        "title": "Send Document File",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def whatsapp_send_file(params: SendFileInput) -> str:
    """Send document file with optional custom filename and caption."""
    try:
        file_data = None
        if params.file_path:
            file_data = _read_file_as_base64(params.file_path)
            if not params.filename:
                params.filename = Path(params.file_path).name
        elif params.file_url:
            file_data = await _download_file_as_base64(params.file_url)
        elif params.file_base64:
            file_data = params.file_base64
        
        payload = {
            "recipient": params.recipient,
            "file": file_data,
            "filename": params.filename or "document",
            "caption": params.caption or ""
        }
        
        response = await _make_api_request("/send/file", method="POST", json_data=payload)
        return json.dumps(response, indent=2)
    except Exception as e:
        return f"Error sending file: {str(e)}"


@mcp.tool(
    name="whatsapp_send_location",
    annotations={
        "title": "Send Location Message",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def whatsapp_send_location(params: SendLocationInput) -> str:
    """Send geographic location with coordinates, name, and address."""
    try:
        payload = {
            "recipient": params.recipient,
            "latitude": params.latitude,
            "longitude": params.longitude,
            "name": params.name or "",
            "address": params.address or ""
        }
        
        response = await _make_api_request("/send/location", method="POST", json_data=payload)
        return json.dumps(response, indent=2)
    except Exception as e:
        return f"Error sending location: {str(e)}"


@mcp.tool(
    name="whatsapp_send_contact",
    annotations={
        "title": "Send Contact Card",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def whatsapp_send_contact(params: SendContactInput) -> str:
    """Send contact card with name and phone number."""
    try:
        payload = {
            "recipient": params.recipient,
            "contact_name": params.contact_name,
            "contact_phone": params.contact_phone
        }
        
        response = await _make_api_request("/send/contact", method="POST", json_data=payload)
        return json.dumps(response, indent=2)
    except Exception as e:
        return f"Error sending contact: {str(e)}"


@mcp.tool(
    name="whatsapp_send_poll",
    annotations={
        "title": "Send Poll Message",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def whatsapp_send_poll(params: SendPollInput) -> str:
    """Send poll with question and multiple choice options."""
    try:
        payload = {
            "recipient": params.recipient,
            "question": params.question,
            "options": params.options,
            "selectable_count": params.selectable_count
        }
        
        response = await _make_api_request("/send/poll", method="POST", json_data=payload)
        return json.dumps(response, indent=2)
    except Exception as e:
        return f"Error sending poll: {str(e)}"


@mcp.tool(
    name="whatsapp_set_presence",
    annotations={
        "title": "Set User Presence Status",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def whatsapp_set_presence(params: SendPresenceInput) -> str:
    """Set global presence status (available/unavailable)."""
    try:
        payload = {"presence": params.presence.value}
        response = await _make_api_request("/send/presence", method="POST", json_data=payload)
        return json.dumps(response, indent=2)
    except Exception as e:
        return f"Error setting presence: {str(e)}"


@mcp.tool(
    name="whatsapp_set_chat_presence",
    annotations={
        "title": "Set Chat Typing Indicator",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def whatsapp_set_chat_presence(params: SendChatPresenceInput) -> str:
    """Set chat-specific presence (composing/paused typing indicator)."""
    try:
        payload = {
            "recipient": params.recipient,
            "presence": params.presence.value
        }
        response = await _make_api_request("/send/chat-presence", method="POST", json_data=payload)
        return json.dumps(response, indent=2)
    except Exception as e:
        return f"Error setting chat presence: {str(e)}"


# ============================================================================
# MESSAGE MANAGEMENT TOOLS
# ============================================================================

@mcp.tool(
    name="whatsapp_delete_message",
    annotations={
        "title": "Delete Message (For Me)",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def whatsapp_delete_message(params: MessageActionInput) -> str:
    """Delete message from your device only (not from recipient's device)."""
    try:
        payload = {
            "recipient": params.recipient,
            "message_id": params.message_id
        }
        response = await _make_api_request("/message/delete", method="POST", json_data=payload)
        return json.dumps(response, indent=2)
    except Exception as e:
        return f"Error deleting message: {str(e)}"


@mcp.tool(
    name="whatsapp_revoke_message",
    annotations={
        "title": "Revoke Message (Delete for Everyone)",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def whatsapp_revoke_message(params: MessageActionInput) -> str:
    """Revoke message for all participants (delete for everyone)."""
    try:
        payload = {
            "recipient": params.recipient,
            "message_id": params.message_id
        }
        response = await _make_api_request("/message/revoke", method="POST", json_data=payload)
        return json.dumps(response, indent=2)
    except Exception as e:
        return f"Error revoking message: {str(e)}"


@mcp.tool(
    name="whatsapp_react_message",
    annotations={
        "title": "React to Message",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def whatsapp_react_message(params: ReactMessageInput) -> str:
    """Add emoji reaction to a message (or remove by sending empty emoji)."""
    try:
        payload = {
            "recipient": params.recipient,
            "message_id": params.message_id,
            "emoji": params.emoji
        }
        response = await _make_api_request("/message/react", method="POST", json_data=payload)
        return json.dumps(response, indent=2)
    except Exception as e:
        return f"Error reacting to message: {str(e)}"


@mcp.tool(
    name="whatsapp_update_message",
    annotations={
        "title": "Edit Message",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def whatsapp_update_message(params: UpdateMessageInput) -> str:
    """Edit a previously sent message with new text."""
    try:
        payload = {
            "recipient": params.recipient,
            "message_id": params.message_id,
            "new_text": params.new_text
        }
        response = await _make_api_request("/message/update", method="POST", json_data=payload)
        return json.dumps(response, indent=2)
    except Exception as e:
        return f"Error updating message: {str(e)}"


@mcp.tool(
    name="whatsapp_mark_read",
    annotations={
        "title": "Mark Message as Read",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def whatsapp_mark_read(params: MessageActionInput) -> str:
    """Mark message as read (send read receipt)."""
    try:
        payload = {
            "recipient": params.recipient,
            "message_id": params.message_id
        }
        response = await _make_api_request("/message/read", method="POST", json_data=payload)
        return json.dumps(response, indent=2)
    except Exception as e:
        return f"Error marking message as read: {str(e)}"



# ============================================================================
# CHAT MANAGEMENT TOOLS
# ============================================================================

@mcp.tool(
    name="whatsapp_list_chats",
    annotations={
        "title": "List All Chats",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def whatsapp_list_chats(params: ListChatsInput) -> str:
    """
    List all WhatsApp chats (individual and group conversations).
    
    Returns a paginated list of all active chats with basic information including
    chat name, JID, last message preview, and unread count.
    
    Args:
        params (ListChatsInput): Parameters containing:
            - limit (int): Maximum chats to return (1-200, default: 50)
            - offset (int): Pagination offset (default: 0)
            - response_format (ResponseFormat): 'markdown' or 'json'
    
    Returns:
        str: Formatted list of chats with pagination info
    
    Examples:
        - Use when: Browsing available conversations
        - Use when: Finding a specific chat to interact with
        - Use when: Monitoring active conversations
        - Increase limit for more results per page
        - Use offset for pagination through large chat lists
    
    Error Handling:
        - Returns empty list if no chats found
        - Handles pagination automatically
        - Truncates if exceeds character limit
    """
    try:
        response = await _make_api_request(
            f"/chat/list?limit={params.limit}&offset={params.offset}",
            method="GET"
        )
        return _format_response(response, params.response_format)
    except Exception as e:
        return f"Error listing chats: {str(e)}"


@mcp.tool(
    name="whatsapp_get_messages",
    annotations={
        "title": "Get Chat Messages",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def whatsapp_get_messages(params: GetChatMessagesInput) -> str:
    """
    Retrieve messages from a specific chat conversation.
    
    Returns message history including text content, media indicators, sender info,
    timestamps, and message metadata. Supports pagination for long conversations.
    
    Args:
        params (GetChatMessagesInput): Parameters containing:
            - chat_id (str): Chat WhatsApp JID (e.g., '1234567890@s.whatsapp.net')
            - limit (int): Maximum messages to return (1-200, default: 50)
            - offset (int): Pagination offset (default: 0)
            - response_format (ResponseFormat): 'markdown' or 'json'
    
    Returns:
        str: Formatted message history with pagination info
    
    Examples:
        - Use when: Reading conversation history
        - Use when: Finding specific messages in a chat
        - Use when: Analyzing chat content
        - Set higher limit to retrieve more messages
        - Use offset to paginate through conversation history
    
    Error Handling:
        - Returns error if chat_id not found
        - Returns empty list if no messages in chat
        - Handles media message references appropriately
    """
    try:
        response = await _make_api_request(
            f"/chat/messages/{params.chat_id}?limit={params.limit}&offset={params.offset}",
            method="GET"
        )
        return _format_response(response, params.response_format)
    except Exception as e:
        return f"Error getting messages: {str(e)}"


# ============================================================================
# GROUP MANAGEMENT TOOLS
# ============================================================================

@mcp.tool(
    name="whatsapp_create_group",
    annotations={
        "title": "Create WhatsApp Group",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def whatsapp_create_group(params: CreateGroupInput) -> str:
    """
    Create a new WhatsApp group with specified name and participants.
    
    Creates a group where you are the admin, and adds the specified participants.
    You can manage group settings and participants after creation.
    
    Args:
        params (CreateGroupInput): Group creation parameters:
            - name (str): Group name (1-100 characters)
            - participants (List[str]): Participant JIDs (at least 1 required)
    
    Returns:
        str: JSON response with group JID and creation details
    
    Examples:
        - Use when: Creating new group conversations
        - Participants must be in format '1234567890@s.whatsapp.net'
        - You become the group admin automatically
        - Can add up to 256 participants initially
    
    Error Handling:
        - Returns error if participant format invalid
        - Returns error if participant not on WhatsApp
        - Provides group JID for future operations
    """
    try:
        payload = {
            "name": params.name,
            "participants": params.participants
        }
        response = await _make_api_request("/group/create", method="POST", json_data=payload)
        return json.dumps(response, indent=2)
    except Exception as e:
        return f"Error creating group: {str(e)}"


@mcp.tool(
    name="whatsapp_join_group",
    annotations={
        "title": "Join Group via Invite Link",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def whatsapp_join_group(params: JoinGroupInput) -> str:
    """
    Join a WhatsApp group using an invite link.
    
    Args:
        params (JoinGroupInput): Parameters containing:
            - invite_link (str): Group invite URL (e.g., 'https://chat.whatsapp.com/XXXXX')
    
    Returns:
        str: Confirmation of group join with group details
    
    Examples:
        - Use when: Joining groups via shared invite links
        - Link must start with 'https://chat.whatsapp.com/'
        - May fail if group is full or invite expired
    
    Error Handling:
        - Returns error if link invalid or expired
        - Returns error if group is full
        - Returns error if already a member
    """
    try:
        payload = {"invite_link": params.invite_link}
        response = await _make_api_request("/group/join", method="POST", json_data=payload)
        return json.dumps(response, indent=2)
    except Exception as e:
        return f"Error joining group: {str(e)}"


@mcp.tool(
    name="whatsapp_get_group_info",
    annotations={
        "title": "Get Group Information",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def whatsapp_get_group_info(params: GroupInfoInput) -> str:
    """
    Retrieve detailed information about a WhatsApp group.
    
    Returns group metadata including name, description, participant list,
    admin list, creation date, and group settings.
    
    Args:
        params (GroupInfoInput): Parameters containing:
            - group_id (str): Group JID (e.g., '1234567890@g.us')
            - response_format (ResponseFormat): 'markdown' or 'json'
    
    Returns:
        str: Formatted group information
    
    Examples:
        - Use when: Checking group details before sending
        - Use when: Verifying group membership
        - Use when: Listing group participants
        - Shows admin status for each participant
    
    Error Handling:
        - Returns error if group not found
        - Returns error if not a group member
        - Includes participant count and admin list
    """
    try:
        response = await _make_api_request(f"/group/info/{params.group_id}", method="GET")
        return _format_response(response, params.response_format)
    except Exception as e:
        return f"Error getting group info: {str(e)}"


@mcp.tool(
    name="whatsapp_manage_participants",
    annotations={
        "title": "Manage Group Participants",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def whatsapp_manage_participants(params: ManageParticipantsInput) -> str:
    """
    Add, remove, promote, or demote group participants.
    
    Admin-only operation for managing group membership and permissions.
    
    Args:
        params (ManageParticipantsInput): Parameters containing:
            - group_id (str): Group JID
            - participants (List[str]): Participant JIDs to manage
            - action (Literal): 'add', 'remove', 'promote', or 'demote'
    
    Returns:
        str: Result of participant management operation
    
    Examples:
        - action='add': Add new members to group
        - action='remove': Remove/kick members from group
        - action='promote': Make members group admins
        - action='demote': Remove admin privileges
        - Requires admin permissions
    
    Error Handling:
        - Returns error if not group admin
        - Returns error if participant not found
        - Returns partial success for batch operations
    """
    try:
        payload = {
            "group_id": params.group_id,
            "participants": params.participants,
            "action": params.action
        }
        response = await _make_api_request("/group/participants", method="POST", json_data=payload)
        return json.dumps(response, indent=2)
    except Exception as e:
        return f"Error managing participants: {str(e)}"


@mcp.tool(
    name="whatsapp_update_group",
    annotations={
        "title": "Update Group Settings",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def whatsapp_update_group(params: UpdateGroupInput) -> str:
    """
    Update group name, description, and settings.
    
    Admin-only operation for modifying group metadata and permissions.
    
    Args:
        params (UpdateGroupInput): Parameters containing:
            - group_id (str): Group JID
            - name (Optional[str]): New group name
            - description (Optional[str]): New group description
            - locked (Optional[bool]): Lock settings (only admins can edit info)
            - announce (Optional[bool]): Announcement mode (only admins can send)
    
    Returns:
        str: Confirmation of group updates
    
    Examples:
        - Provide only fields to update (others remain unchanged)
        - locked=True: Only admins can edit group info
        - announce=True: Only admins can send messages
        - Requires admin permissions
    
    Error Handling:
        - Returns error if not group admin
        - Returns error if group not found
        - Validates name/description length limits
    """
    try:
        payload = {"group_id": params.group_id}
        if params.name:
            payload["name"] = params.name
        if params.description:
            payload["description"] = params.description
        if params.locked is not None:
            payload["locked"] = params.locked
        if params.announce is not None:
            payload["announce"] = params.announce
        
        response = await _make_api_request("/group/update", method="POST", json_data=payload)
        return json.dumps(response, indent=2)
    except Exception as e:
        return f"Error updating group: {str(e)}"


@mcp.tool(
    name="whatsapp_set_group_photo",
    annotations={
        "title": "Set Group Profile Photo",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def whatsapp_set_group_photo(params: SetGroupPhotoInput) -> str:
    """
    Set or update group profile photo.
    
    Admin-only operation for changing group avatar.
    
    Args:
        params (SetGroupPhotoInput): Parameters containing:
            - group_id (str): Group JID
            - image_path, image_url, or image_base64: Photo source (one required)
    
    Returns:
        str: Confirmation of photo update
    
    Error Handling:
        - Returns error if not group admin
        - Returns error if image format unsupported
        - Automatically crops/resizes image
    """
    try:
        image_data = None
        if params.image_path:
            image_data = _read_file_as_base64(params.image_path)
        elif params.image_url:
            image_data = await _download_file_as_base64(params.image_url)
        elif params.image_base64:
            image_data = params.image_base64
        
        payload = {
            "group_id": params.group_id,
            "image": image_data
        }
        response = await _make_api_request("/group/photo", method="POST", json_data=payload)
        return json.dumps(response, indent=2)
    except Exception as e:
        return f"Error setting group photo: {str(e)}"



# ============================================================================
# ACCOUNT MANAGEMENT TOOLS
# ============================================================================

@mcp.tool(
    name="whatsapp_get_user_info",
    annotations={
        "title": "Get User Information",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def whatsapp_get_user_info(params: GetUserInfoInput) -> str:
    """
    Check if phone numbers are registered on WhatsApp and get user details.
    
    Validates phone numbers and returns WhatsApp registration status, JID,
    and available profile information.
    
    Args:
        params (GetUserInfoInput): Parameters containing:
            - phone_numbers (List[str]): Phone numbers to check (with/without +)
            - response_format (ResponseFormat): 'markdown' or 'json'
    
    Returns:
        str: User information for each phone number
    
    Examples:
        - Use when: Verifying contacts before sending
        - Use when: Checking WhatsApp registration status
        - Use when: Getting proper JID format for contacts
        - Supports batch lookup of multiple numbers
    
    Error Handling:
        - Returns status for each number individually
        - Indicates if number not registered on WhatsApp
        - Provides proper JID format for registered users
    """
    try:
        payload = {"phone_numbers": params.phone_numbers}
        response = await _make_api_request("/user/info", method="POST", json_data=payload)
        return _format_response(response, params.response_format)
    except Exception as e:
        return f"Error getting user info: {str(e)}"


@mcp.tool(
    name="whatsapp_get_my_profile",
    annotations={
        "title": "Get My Profile Information",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def whatsapp_get_my_profile() -> str:
    """
    Retrieve your own WhatsApp profile information.
    
    Returns current profile details including JID, push name (display name),
    status message, and profile photo URL.
    
    Returns:
        str: JSON with your profile information
    
    Examples:
        - Use when: Checking current profile settings
        - Use when: Verifying account information
        - Use when: Getting your own WhatsApp JID
    
    Error Handling:
        - Returns error if not logged in
        - Includes all available profile fields
    """
    try:
        response = await _make_api_request("/account/profile", method="GET")
        return json.dumps(response, indent=2)
    except Exception as e:
        return f"Error getting profile: {str(e)}"


@mcp.tool(
    name="whatsapp_update_profile",
    annotations={
        "title": "Update Profile Information",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def whatsapp_update_profile(params: UpdateProfileInput) -> str:
    """
    Update your WhatsApp display name or status message.
    
    Args:
        params (UpdateProfileInput): Parameters containing:
            - push_name (Optional[str]): New display name (max 100 chars)
            - status (Optional[str]): New status message (max 139 chars)
    
    Returns:
        str: Confirmation of profile update
    
    Examples:
        - Provide only fields to update
        - push_name is your display name shown to contacts
        - status is your status/about message
    
    Error Handling:
        - Returns error if not logged in
        - Validates length limits
        - Changes visible to all contacts
    """
    try:
        payload = {}
        if params.push_name:
            payload["push_name"] = params.push_name
        if params.status:
            payload["status"] = params.status
        
        response = await _make_api_request("/account/update", method="POST", json_data=payload)
        return json.dumps(response, indent=2)
    except Exception as e:
        return f"Error updating profile: {str(e)}"


@mcp.tool(
    name="whatsapp_set_avatar",
    annotations={
        "title": "Set Profile Avatar",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def whatsapp_set_avatar(params: SetAvatarInput) -> str:
    """
    Set or update your WhatsApp profile photo.
    
    Args:
        params (SetAvatarInput): Parameters containing:
            - image_path, image_url, or image_base64: Photo source (one required)
    
    Returns:
        str: Confirmation of avatar update
    
    Examples:
        - Provide exactly one image source
        - Image is automatically cropped to square
        - Visible to all contacts based on privacy settings
    
    Error Handling:
        - Returns error if image format unsupported
        - Returns error if not logged in
        - Automatically resizes image
    """
    try:
        image_data = None
        if params.image_path:
            image_data = _read_file_as_base64(params.image_path)
        elif params.image_url:
            image_data = await _download_file_as_base64(params.image_url)
        elif params.image_base64:
            image_data = params.image_base64
        
        payload = {"image": image_data}
        response = await _make_api_request("/account/avatar", method="POST", json_data=payload)
        return json.dumps(response, indent=2)
    except Exception as e:
        return f"Error setting avatar: {str(e)}"


@mcp.tool(
    name="whatsapp_update_privacy",
    annotations={
        "title": "Update Privacy Settings",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def whatsapp_update_privacy(params: UpdatePrivacyInput) -> str:
    """
    Update WhatsApp privacy settings for various features.
    
    Control who can see your information and interact with you.
    
    Args:
        params (UpdatePrivacyInput): Parameters containing:
            - setting_type: 'last_seen', 'online', 'profile_picture', 'status', 'read_receipts', or 'groups'
            - value: 'all', 'contacts', 'contact_blacklist', or 'none'
    
    Returns:
        str: Confirmation of privacy setting update
    
    Examples:
        - setting_type='last_seen', value='contacts': Only contacts see last seen
        - setting_type='profile_picture', value='all': Everyone can see photo
        - setting_type='groups', value='contacts': Only contacts can add to groups
        - setting_type='read_receipts', value='none': Disable read receipts
    
    Error Handling:
        - Returns error if invalid combination
        - Returns error if not logged in
        - Changes apply immediately
    """
    try:
        payload = {
            "setting_type": params.setting_type,
            "value": params.value.value
        }
        response = await _make_api_request("/account/privacy", method="POST", json_data=payload)
        return json.dumps(response, indent=2)
    except Exception as e:
        return f"Error updating privacy: {str(e)}"


@mcp.tool(
    name="whatsapp_get_business_profile",
    annotations={
        "title": "Get Business Profile",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def whatsapp_get_business_profile(jid: str) -> str:
    """
    Get business profile information for a WhatsApp Business account.
    
    Args:
        jid (str): WhatsApp JID of the business account
    
    Returns:
        str: Business profile including description, category, website, hours
    
    Examples:
        - Use when: Checking business account details
        - Only works for WhatsApp Business accounts
        - Regular accounts return error
    
    Error Handling:
        - Returns error if not a business account
        - Returns error if JID not found
    """
    try:
        response = await _make_api_request(f"/account/business/{jid}", method="GET")
        return json.dumps(response, indent=2)
    except Exception as e:
        return f"Error getting business profile: {str(e)}"


# ============================================================================
# SERVER ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import sys
    
    # Print configuration on startup
    print("WhatsApp MCP Server", file=sys.stderr)
    print(f"API URL: {WHATSAPP_API_URL}", file=sys.stderr)
    print(f"Auth configured: {'Yes' if WHATSAPP_AUTH_USER else 'No'}", file=sys.stderr)
    print("", file=sys.stderr)
    
    # Run the MCP server
    mcp.run()
