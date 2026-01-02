"""Telegram Bot MCP Server.

This module provides a FastMCP server for interacting with Telegram channels:
- Publishing messages to channels
- Publishing photos with captions
- Editing existing messages
- Editing photo captions
- Searching messages (from cache)
- Deleting messages
- Getting channel information
"""

import logging
from typing import Any, Optional

from mcp.server.fastmcp import FastMCP
from telegram.error import TelegramError

from telegram_bot.telegram_bot_client import TelegramBotClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global client instance for reuse across tool calls
_client: Optional[TelegramBotClient] = None


def _get_client() -> TelegramBotClient:
    """Get or create the global Telegram bot client."""
    global _client
    if _client is None:
        logger.info("Initializing Telegram bot client")
        _client = TelegramBotClient()
    return _client


# Create FastMCP server instance
mcp = FastMCP("telegram-bot-mcp")


@mcp.prompt()
def telegram_bot_instructions() -> str:
    """Comprehensive instructions for using the Telegram Bot MCP server.

    This prompt provides AI assistants with detailed guidance on how to effectively
    use the Telegram Bot MCP server tools to interact with Telegram channels.
    """
    return """# Telegram Bot MCP Server Instructions

This MCP server enables AI assistants to publish, edit, search, and manage messages in Telegram channels.

## Quick Reference

| Task | Message Type | Tool to Use |
|------|-------------|-------------|
| Publish a text message | Text | `publish_message` |
| Publish a photo | Photo | `publish_photo` |
| Publish multiple photos (album) | Photo Album | `publish_photo_album` |
| Edit a text-only message | Text | `edit_message` |
| Edit a photo's caption | Photo | `edit_message_caption` |
| Delete any message | Any | `delete_message` |
| Search cached messages | Any | `search_messages` |
| Get channel info | - | `get_channel_info` |

## Critical Rules

### Message Type and Editing
**IMPORTANT:** You CANNOT use `edit_message` on photo messages or `edit_message_caption` on text messages!

- **Text messages**: Use `edit_message` (will fail on photo messages)
- **Photo messages**: Use `edit_message_caption` (will fail on text-only messages)
- You cannot change a text message to a photo or vice versa
- The bot can only edit messages it sent itself

### Channel ID Format
- **Public channels**: Use `@channelname` format (e.g., `@mynews`)
- **Private channels**: Use numeric chat ID (e.g., `-1001234567890`)
- To get the chat ID:
  1. Add the bot to the channel
  2. Send a test message
  3. Check: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`

### Bot Permissions Required
The bot must be a channel administrator with these permissions:
- Post messages
- Edit messages of others
- Delete messages of others

## Tool Usage Patterns

### Publishing Messages
```
Use publish_message for:
- Announcements and updates
- Formatted text with Markdown or HTML
- Messages with links (can disable preview)

Use publish_photo for:
- Single images with captions
- Visual content announcements
- Photos from local files, URLs, or Telegram file_id

Use publish_photo_album for:
- Multiple photos (2-10) in a single message
- Photo galleries and collections
- Each photo can have its own caption
- Users can swipe through the album
- Photos from local files, URLs, or Telegram file_ids
```

### Editing Messages
```
Before editing, determine message type:
- If it's text only → use edit_message
- If it has a photo → use edit_message_caption

Common error: "Message can't be edited"
Reasons:
1. Wrong tool for message type (most common)
2. Bot didn't send the original message
3. Message is older than 48 hours
```

### Search Limitations
**CRITICAL LIMITATION:** The `search_messages` tool only searches messages cached in the current session.

- ❌ Cannot search historical messages from before server started
- ❌ Cache is cleared when server restarts
- ❌ Cannot fetch arbitrary messages by ID
- ✅ Can still edit/delete messages from previous sessions if you know the message_id
- ✅ All messages published/edited in current session are automatically cached

## Error Handling

### Common Errors and Solutions

1. **"Chat not found"**
   - Verify bot is added to channel as admin
   - Check channel ID format (@username or numeric ID)

2. **"Not enough rights to send messages"**
   - Bot needs admin permissions with "Post messages" enabled

3. **"Message can't be edited"**
   - Check if you're using the correct edit tool for the message type
   - Verify bot sent the original message
   - Check if message is within 48-hour edit window

4. **"Message is not modified"**
   - New content is identical to current content

## Rate Limits

Telegram enforces rate limits on bot API calls. If publishing many messages:
- Add delays between messages
- Monitor for rate limit errors
- Consider using `disable_notification: true` for bulk updates

## Best Practices

1. **Always verify channel permissions** before attempting operations
2. **Store message_id values** from publish operations for later editing/deletion
3. **Use appropriate parse_mode** (Markdown/HTML) for formatted content
4. **Check message type** before choosing edit tool
5. **Handle errors gracefully** - API errors include helpful hints
6. **Use get_channel_info** to verify bot access before operations

## Example Workflows

### Publishing an Announcement
1. Use `get_channel_info` to verify access
2. Use `publish_message` with formatted text
3. Store returned `message_id` for potential edits
4. If editing needed, use `edit_message` with stored `message_id`

### Publishing Photo Update
1. Use `publish_photo` with image path/URL
2. Store returned `message_id`
3. If caption needs updating, use `edit_message_caption`

### Publishing Photo Album
1. Prepare list of 2-10 photos with optional captions
2. Use `publish_photo_album` with the photos list
3. Store returned `first_message_id` and `album_id`
4. All photos are posted as a single swipeable album
5. Each photo's caption can be edited separately using `edit_message_caption` with its message_id

### Managing Content
1. Use `search_messages` to find recent messages (current session only)
2. Use `delete_message` with message_id to remove outdated content
3. Use appropriate edit tool to update existing messages
"""


@mcp.resource("server://info")
def get_server_info() -> str:
    """Get server version and capability information.

    This resource provides metadata about the Telegram Bot MCP server,
    including version, capabilities, and configuration details.
    """
    return """# Telegram Bot MCP Server Information

**Server Name:** telegram-bot-mcp
**Version:** 0.1.0
**Protocol:** Model Context Protocol (MCP)
**Framework:** FastMCP

## Capabilities

### Supported Operations
- ✅ Publish text messages to channels
- ✅ Publish photos with captions to channels
- ✅ Publish photo albums (2-10 photos in one message)
- ✅ Edit text messages
- ✅ Edit photo captions
- ✅ Delete messages
- ✅ Search messages (session cache only)
- ✅ Get channel information

### Message Formats
- Markdown formatting
- HTML formatting
- Plain text

### Supported Content Types
- Text messages
- Photo messages with captions
- Links with optional preview control

## Requirements

### Bot Permissions
The Telegram bot must be a channel administrator with:
- Post messages
- Edit messages of others
- Delete messages of others

### Environment Configuration
- `TELEGRAM_BOT_TOKEN`: Required Telegram bot API token

## Technical Details

### Dependencies
- python-telegram-bot >= 21.0
- fastmcp >= 0.1.0
- Python >= 3.10

### Limitations
- Message search only works for messages in current session cache
- Cannot retrieve historical messages through Bot API
- Cannot change message type (text to photo or vice versa)
- Bot can only edit its own messages

### API Rate Limits
Subject to Telegram Bot API rate limits. Consider delays for bulk operations.

## Support
For issues and feature requests, visit the project repository.
"""


@mcp.tool()
async def publish_message(
    channel_id: str,
    text: str,
    parse_mode: str = "Markdown",
    disable_web_page_preview: bool = False,
    disable_notification: bool = False,
) -> dict[str, Any]:
    """Publish a message to a Telegram channel.

    Use this tool to post new messages to a Telegram channel where the bot is an admin.
    The bot must have permission to post messages in the channel.

    Args:
        channel_id: Channel username (e.g., '@mychannel') or numeric chat ID (e.g., '-1001234567890').
            Use '@' prefix for public channels with username.
        text: The message text to publish. Supports Markdown or HTML formatting based on parse_mode.
        parse_mode: Text formatting mode. Options: 'Markdown', 'HTML', or 'None' for plain text.
            Default is 'Markdown'.
        disable_web_page_preview: If True, disables link preview for URLs in the message.
            Default is False.
        disable_notification: If True, sends the message silently (no notification to users).
            Default is False.

    Returns:
        A dictionary containing message_id, chat_id, date, text, and link.
    """
    try:
        client = _get_client()
        result = await client.publish_message(
            channel_id=channel_id,
            text=text,
            parse_mode=parse_mode,
            disable_web_page_preview=disable_web_page_preview,
            disable_notification=disable_notification,
        )
        return result
    except TelegramError as e:
        return {
            "error": str(e),
            "status": "failed",
            "message": f"Failed to publish message to channel {channel_id}",
        }
    except Exception as e:
        return {
            "error": str(e),
            "status": "failed",
            "message": "Unexpected error occurred while publishing message",
        }


@mcp.tool()
async def publish_photo(
    channel_id: str,
    photo: str,
    caption: Optional[str] = None,
    parse_mode: str = "Markdown",
    disable_notification: bool = False,
) -> dict[str, Any]:
    """Publish a photo to a Telegram channel with an optional caption.

    Use this tool to post photos to a Telegram channel where the bot is an admin.
    The photo can include a text caption with formatting. The bot must have
    permission to post messages in the channel.

    Args:
        channel_id: Channel username (e.g., '@mychannel') or numeric chat ID.
        photo: Photo to send. Can be:
            - File path to a local image file (e.g., '/path/to/image.jpg')
            - URL to a remote image (e.g., 'https://example.com/image.png')
            - Telegram file_id of a photo that exists on Telegram servers
        caption: Optional text caption for the photo. Supports Markdown or HTML
            formatting based on parse_mode. Maximum 1024 characters.
        parse_mode: Caption formatting mode. Options: 'Markdown', 'HTML', or 'None' for plain text.
            Default is 'Markdown'.
        disable_notification: If True, sends the photo silently (no notification to users).
            Default is False.

    Returns:
        A dictionary containing message_id, chat_id, date, caption, photo info, and link.
    """
    try:
        client = _get_client()
        result = await client.publish_photo(
            channel_id=channel_id,
            photo=photo,
            caption=caption,
            parse_mode=parse_mode,
            disable_notification=disable_notification,
        )
        return result
    except TelegramError as e:
        return {
            "error": str(e),
            "status": "failed",
            "message": f"Failed to publish photo to channel {channel_id}",
        }
    except Exception as e:
        return {
            "error": str(e),
            "status": "failed",
            "message": "Unexpected error occurred while publishing photo",
        }


@mcp.tool()
async def publish_photo_album(
    channel_id: str,
    photos: list[dict[str, Any]],
    disable_notification: bool = False,
) -> dict[str, Any]:
    """Publish multiple photos as an album (media group) to a Telegram channel.

    Use this tool to post 2-10 photos in a single message as an album/gallery.
    Users can swipe through the photos. Each photo can have its own caption.
    The bot must have permission to post messages in the channel.

    Args:
        channel_id: Channel username (e.g., '@mychannel') or numeric chat ID.
        photos: List of photo objects (2-10 items). Each photo object must contain:
            - photo (required): Photo to send. Can be:
                - File path to a local image file (e.g., '/path/to/image.jpg')
                - URL to a remote image (e.g., 'https://example.com/image.png')
                - Telegram file_id of a photo that exists on Telegram servers
            - caption (optional): Text caption for this specific photo. Maximum 1024 characters.
            - parse_mode (optional): Caption formatting mode ('Markdown', 'HTML', or 'None').
                Default is 'Markdown' if not specified.
        disable_notification: If True, sends the album silently (no notification to users).
            Default is False.

    Returns:
        A dictionary containing:
        - album_id: Unique identifier for the media group
        - message_count: Number of photos in the album
        - messages: List of message details for each photo (message_id, caption, photo info, link)
        - first_message_id: ID of the first message in the album
        - chat_id: Channel chat ID

    Example:
        photos = [
            {
                "photo": "https://example.com/photo1.jpg",
                "caption": "First photo caption",
                "parse_mode": "Markdown"
            },
            {
                "photo": "/path/to/photo2.jpg",
                "caption": "Second photo caption"
            },
            {
                "photo": "AgACAgIAAxkBAAIC...",  # Telegram file_id
                "caption": "Third photo"
            }
        ]
    """
    try:
        client = _get_client()
        result = await client.publish_photo_album(
            channel_id=channel_id,
            photos=photos,
            disable_notification=disable_notification,
        )
        return result
    except ValueError as e:
        return {
            "error": str(e),
            "status": "failed",
            "message": f"Invalid photo album parameters: {str(e)}",
        }
    except TelegramError as e:
        return {
            "error": str(e),
            "status": "failed",
            "message": f"Failed to publish photo album to channel {channel_id}",
        }
    except Exception as e:
        return {
            "error": str(e),
            "status": "failed",
            "message": "Unexpected error occurred while publishing photo album",
        }


@mcp.tool()
async def edit_message(
    channel_id: str,
    message_id: int,
    new_text: str,
    parse_mode: str = "Markdown",
) -> dict[str, Any]:
    """Edit an existing TEXT message in a Telegram channel.

    Use this tool to modify the content of a previously published TEXT message.
    IMPORTANT: This only works for text messages. If the message contains a photo,
    use edit_message_caption instead.

    The bot must be the original sender of the message and have edit permissions.

    Args:
        channel_id: Channel username (e.g., '@mychannel') or numeric chat ID.
            Must be the same channel where the original message was sent.
        message_id: The unique identifier of the message to edit.
            This is returned when you publish a message.
        new_text: The new text to replace the existing message content.
            Supports formatting based on parse_mode.
        parse_mode: Text formatting mode. Options: 'Markdown', 'HTML', or 'None'.
            Default is 'Markdown'.

    Returns:
        A dictionary containing message_id, chat_id, date, edit_date, text, and link.
    """
    try:
        client = _get_client()
        result = await client.edit_message(
            channel_id=channel_id,
            message_id=message_id,
            new_text=new_text,
            parse_mode=parse_mode,
        )
        return result
    except TelegramError as e:
        error_msg = str(e)
        hint = ""

        # Provide helpful hints based on common errors
        if (
            "message can't be edited" in error_msg.lower()
            or "message to edit not found" in error_msg.lower()
        ):
            hint = " NOTE: If this is a photo message, use edit_message_caption instead. Also, the bot can only edit messages it sent itself."
        elif "message is not modified" in error_msg.lower():
            hint = " The new text is identical to the current text."

        return {
            "error": error_msg,
            "status": "failed",
            "message": f"Failed to edit message {message_id} in channel {channel_id}.{hint}",
            "telegram_error": error_msg,
        }
    except Exception as e:
        return {
            "error": str(e),
            "status": "failed",
            "message": "Unexpected error occurred while editing message",
        }


@mcp.tool()
async def edit_message_caption(
    channel_id: str,
    message_id: int,
    new_caption: str,
    parse_mode: str = "Markdown",
) -> dict[str, Any]:
    """Edit the caption of an existing photo message in a Telegram channel.

    Use this tool to modify the caption text of a previously published photo message.
    This only works for messages that contain media (photos, videos, etc.).
    You cannot change the photo itself, only the caption text.
    The bot must be the original sender of the message and have edit permissions.

    Args:
        channel_id: Channel username (e.g., '@mychannel') or numeric chat ID.
            Must be the same channel where the original message was sent.
        message_id: The unique identifier of the photo message to edit.
            This is returned when you publish a photo.
        new_caption: The new caption text to replace the existing caption.
            Supports formatting based on parse_mode. Maximum 1024 characters.
        parse_mode: Caption formatting mode. Options: 'Markdown', 'HTML', or 'None'.
            Default is 'Markdown'.

    Returns:
        A dictionary containing message_id, chat_id, date, edit_date, caption, photo info, and link.
    """
    try:
        client = _get_client()
        result = await client.edit_message_caption(
            channel_id=channel_id,
            message_id=message_id,
            new_caption=new_caption,
            parse_mode=parse_mode,
        )
        return result
    except TelegramError as e:
        error_msg = str(e)
        hint = ""

        # Provide helpful hints based on common errors
        if (
            "message can't be edited" in error_msg.lower()
            or "message to edit not found" in error_msg.lower()
        ):
            hint = " NOTE: If this is a text-only message (no photo), use edit_message instead. Also, the bot can only edit messages it sent itself."
        elif "message is not modified" in error_msg.lower():
            hint = " The new caption is identical to the current caption."
        elif "message has no caption" in error_msg.lower():
            hint = " This message doesn't have a caption to edit."

        return {
            "error": error_msg,
            "status": "failed",
            "message": f"Failed to edit caption of message {message_id} in channel {channel_id}.{hint}",
            "telegram_error": error_msg,
        }
    except Exception as e:
        return {
            "error": str(e),
            "status": "failed",
            "message": "Unexpected error occurred while editing message caption",
        }


@mcp.tool()
async def delete_message(
    channel_id: str,
    message_id: int,
) -> dict[str, Any]:
    """Delete a message from a Telegram channel.

    Use this tool to permanently remove a message from a channel.
    The bot must have delete message permissions in the channel.

    Args:
        channel_id: Channel username (e.g., '@mychannel') or numeric chat ID.
        message_id: The unique identifier of the message to delete.

    Returns:
        A dictionary containing success status, message_id, and operation status.
    """
    try:
        client = _get_client()
        success = await client.delete_message(
            channel_id=channel_id,
            message_id=message_id,
        )
        return {
            "success": success,
            "message_id": message_id,
            "status": "deleted" if success else "failed",
        }
    except TelegramError as e:
        return {
            "error": str(e),
            "status": "failed",
            "message": f"Failed to delete message {message_id} from channel {channel_id}",
        }
    except Exception as e:
        return {
            "error": str(e),
            "status": "failed",
            "message": "Unexpected error occurred while deleting message",
        }


@mcp.tool()
def search_messages(
    channel_id: str,
    query: Optional[str] = None,
    limit: int = 10,
) -> dict[str, Any]:
    """Search for messages in a Telegram channel (from local cache ONLY).

    ⚠️ CRITICAL LIMITATIONS - READ CAREFULLY:

    1. **Session-Only Cache**: This tool ONLY searches messages cached in the CURRENT SERVER SESSION.
       - Messages published/edited BEFORE the server started are NOT available
       - Cache is CLEARED when the server restarts
       - This is a Telegram Bot API limitation, not a bug

    2. **Cannot Retrieve Historical Messages**: The Telegram Bot API does not provide
       methods to fetch arbitrary messages or search message history.

    3. **What IS Cached**:
       ✅ Messages published via publish_message in current session
       ✅ Messages edited via edit_message in current session
       ✅ Photos published via publish_photo in current session
       ✅ Photo captions edited via edit_message_caption in current session

    4. **What is NOT Cached**:
       ❌ Messages sent before server started
       ❌ Messages sent by other bots or users
       ❌ Messages sent when server was offline

    5. **You CAN Still**:
       ✅ Edit messages from previous sessions if you have the message_id
       ✅ Delete messages from previous sessions if you have the message_id
       ✅ The message_id is returned when publishing messages - store it if needed later!

    Args:
        channel_id: Channel username (e.g., '@mychannel') or numeric chat ID to search in.
        query: Search query string. Performs case-insensitive search in message text/caption.
            If None or empty, returns all cached messages for the channel.
        limit: Maximum number of results to return. Default is 10.
            Results are sorted by date (newest first).

    Returns:
        A dictionary containing:
        - messages: List of matching messages (may be empty if nothing cached)
        - count: Number of messages found
        - query: The search query used
        - channel_id: The channel searched
        - status: Operation status

    Note: If you need to work with older messages, you must keep track of message_id
    values returned when publishing. There is no way to retrieve message_id for
    historical messages through the Telegram Bot API.
    """
    try:
        logger.info(f"Searching messages in channel {channel_id} with query: {query}")
        client = _get_client()
        messages = client.search_messages(
            channel_id=channel_id,
            query=query,
            limit=limit,
        )
        logger.info(f"Found {len(messages)} messages matching query in cache")
        return {
            "messages": messages,
            "count": len(messages),
            "query": query,
            "channel_id": channel_id,
            "status": "success",
        }
    except Exception as e:
        logger.error(f"Error searching messages: {e}", exc_info=True)
        return {
            "error": str(e),
            "status": "failed",
            "message": "Unexpected error occurred while searching messages",
            "messages": [],
            "count": 0,
        }


@mcp.tool()
async def get_channel_info(channel_id: str) -> dict[str, Any]:
    """Get detailed information about a Telegram channel.

    Use this tool to retrieve metadata and statistics about a channel
    where the bot is a member or admin.

    Args:
        channel_id: Channel username (e.g., '@mychannel') or numeric chat ID.

    Returns:
        A dictionary containing id, title, username, type, description, invite_link, and member_count.
    """
    try:
        client = _get_client()
        info = await client.get_channel_info(channel_id=channel_id)
        return {
            **info,
            "status": "success",
        }
    except TelegramError as e:
        return {
            "error": str(e),
            "status": "failed",
            "message": f"Failed to get info for channel {channel_id}",
        }
    except Exception as e:
        return {
            "error": str(e),
            "status": "failed",
            "message": "Unexpected error occurred while getting channel info",
        }
