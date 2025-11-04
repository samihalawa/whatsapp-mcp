# Changelog

All notable changes to WhatsApp MCP Server will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-01-XX

### Added

#### Authentication & Connection
- QR code login support (`whatsapp_login_qr`)
- Phone verification code login (`whatsapp_login_code`)
- Session logout functionality (`whatsapp_logout`)
- Automatic reconnection (`whatsapp_reconnect`)

#### Messaging Tools (10 tools)
- Text message sending with reply support
- Image message sending (file/URL/base64)
- Video message sending with captions
- Audio/voice note sending
- Document file sharing
- Location sharing with coordinates
- Contact card sharing
- Interactive poll creation
- Presence status control
- Chat-specific typing indicators

#### Message Management (5 tools)
- Message deletion (for self)
- Message revocation (delete for everyone)
- Emoji reactions
- Message editing
- Read receipt marking

#### Chat Management (2 tools)
- Chat listing with pagination
- Message history retrieval

#### Group Management (6 tools)
- Group creation
- Group joining via invite links
- Group information retrieval
- Participant management (add/remove/promote/demote)
- Group settings updates
- Group photo management

#### Account Management (6 tools)
- User information lookup
- Profile retrieval
- Profile updates (name/status)
- Avatar management
- Privacy settings control
- Business profile viewing

### Features
- Production-ready error handling
- Comprehensive input validation with Pydantic v2
- Support for JSON and Markdown response formats
- Automatic response truncation (25,000 character limit)
- Pagination support for list operations
- Base64, file path, and URL support for media
- Environment variable configuration
- Basic authentication support
- Detailed tool documentation
- Type hints throughout

### Documentation
- Comprehensive README with examples
- Quick start guide
- Environment variable template
- Claude Desktop configuration examples
- Validation test script
- MIT License
- Changelog

### Developer Experience
- MCP best practices compliance
- Async/await for all I/O operations
- Shared utility functions
- Consistent error messaging
- Character limit enforcement
- Response format flexibility

## [Unreleased]

### Planned Features
- Incoming message webhooks
- Status/Stories support
- Sticker sending
- Reaction removal
- Message forwarding
- Chat archiving
- Broadcast list support
- Multiple account support
- Rate limiting built-in
- Automated tests
- Performance metrics
- Health check endpoint

---

For upgrade instructions and breaking changes, see [README.md](README.md).
