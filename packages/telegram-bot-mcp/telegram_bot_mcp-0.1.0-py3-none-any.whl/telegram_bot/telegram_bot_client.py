"""Telegram Bot client wrapper for managing bot operations."""

import logging
import os
from typing import Optional, Any, Union, cast

from telegram import Bot, Message, InputMediaPhoto
from telegram.constants import ParseMode
from telegram.error import TelegramError

# Configure logging
logger = logging.getLogger(__name__)


class TelegramBotClient:
    """
    Wrapper for Telegram Bot API operations.

    This client provides a simplified interface for common bot operations
    like publishing, editing, and searching messages in channels.
    """

    def __init__(self, bot_token: Optional[str] = None):
        """
        Initialize Telegram bot client.

        Args:
            bot_token: Telegram bot token. If not provided, reads from TELEGRAM_BOT_TOKEN env var.

        Raises:
            ValueError: If bot token is not provided and not found in environment.
        """
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
        if not self.bot_token:
            logger.error(
                "Bot token not provided and TELEGRAM_BOT_TOKEN environment variable not set"
            )
            raise ValueError(
                "Telegram bot token is required. "
                "Provide it as argument or set TELEGRAM_BOT_TOKEN environment variable."
            )

        logger.info("Initializing Telegram bot client")
        self.bot = Bot(token=self.bot_token)
        self._message_cache: dict[str, list[dict[str, Any]]] = {}
        logger.info("Telegram bot client initialized successfully")

    async def publish_message(
        self,
        channel_id: str,
        text: str,
        parse_mode: str = "Markdown",
        disable_web_page_preview: bool = False,
        disable_notification: bool = False,
    ) -> dict[str, Any]:
        """
        Publish a message to a Telegram channel.

        Args:
            channel_id: Channel username (e.g., '@mychannel') or chat ID
            text: Message text to publish
            parse_mode: Parse mode for text formatting ('Markdown', 'HTML', or None)
            disable_web_page_preview: Disable link previews
            disable_notification: Send message silently

        Returns:
            Dictionary with message details including message_id, date, and text

        Raises:
            TelegramError: If message publishing fails
        """
        try:
            logger.info(f"Publishing message to channel {channel_id}")
            # Convert parse_mode string to ParseMode constant
            pm = None
            if parse_mode:
                pm = ParseMode.MARKDOWN if parse_mode.lower() == "markdown" else ParseMode.HTML

            message = await self.bot.send_message(
                chat_id=channel_id,
                text=text,
                parse_mode=pm,
                disable_web_page_preview=disable_web_page_preview,
                disable_notification=disable_notification,
            )

            result = {
                "message_id": message.message_id,
                "chat_id": message.chat_id,
                "date": message.date.isoformat(),
                "text": message.text,
                "link": self._get_message_link(channel_id, message.message_id),
            }

            # Cache the message for search
            self._cache_message(channel_id, result)
            logger.info(
                f"Successfully published message {message.message_id} to channel {channel_id}"
            )

            return result

        except TelegramError as e:
            logger.error(f"Failed to publish message to channel {channel_id}: {e}", exc_info=True)
            raise TelegramError(f"Failed to publish message: {str(e)}") from e

    async def publish_photo(
        self,
        channel_id: str,
        photo: Union[str, bytes, Any],
        caption: Optional[str] = None,
        parse_mode: str = "Markdown",
        disable_notification: bool = False,
    ) -> dict[str, Any]:
        """
        Publish a photo to a Telegram channel.

        Args:
            channel_id: Channel username (e.g., '@mychannel') or chat ID
            photo: Photo to send. Can be:
                - File path (str) to local image file
                - URL (str) to remote image
                - File-like object or bytes
                - file_id of a photo that exists on Telegram servers
            caption: Optional caption text for the photo
            parse_mode: Parse mode for caption formatting ('Markdown', 'HTML', or None)
            disable_notification: Send message silently

        Returns:
            Dictionary with message details including message_id, date, caption, and photo info

        Raises:
            TelegramError: If photo publishing fails
        """
        try:
            logger.info(f"Publishing photo to channel {channel_id}")
            pm = None
            if parse_mode:
                pm = ParseMode.MARKDOWN if parse_mode.lower() == "markdown" else ParseMode.HTML

            message = await self.bot.send_photo(
                chat_id=channel_id,
                photo=photo,
                caption=caption,
                parse_mode=pm,
                disable_notification=disable_notification,
            )

            # Get the largest photo size
            photo_info = None
            if message.photo:
                largest_photo = max(message.photo, key=lambda p: p.file_size or 0)
                photo_info = {
                    "file_id": largest_photo.file_id,
                    "file_unique_id": largest_photo.file_unique_id,
                    "width": largest_photo.width,
                    "height": largest_photo.height,
                    "file_size": largest_photo.file_size,
                }

            result = {
                "message_id": message.message_id,
                "chat_id": message.chat_id,
                "date": message.date.isoformat(),
                "caption": message.caption,
                "photo": photo_info,
                "link": self._get_message_link(channel_id, message.message_id),
            }

            # Cache the message for search
            self._cache_message(channel_id, result)
            logger.info(
                f"Successfully published photo message {message.message_id} to channel {channel_id}"
            )

            return result

        except TelegramError as e:
            logger.error(f"Failed to publish photo to channel {channel_id}: {e}", exc_info=True)
            raise TelegramError(f"Failed to publish photo: {str(e)}") from e

    async def publish_photo_album(
        self,
        channel_id: str,
        photos: list[dict[str, Any]],
        disable_notification: bool = False,
    ) -> dict[str, Any]:
        """
        Publish multiple photos as an album (media group) to a Telegram channel.

        Args:
            channel_id: Channel username (e.g., '@mychannel') or chat ID
            photos: List of photo dictionaries, each containing:
                - photo: Photo to send (file path, URL, or file_id)
                - caption: Optional caption text for this photo
                - parse_mode: Optional parse mode ('Markdown', 'HTML', or None)
            disable_notification: Send message silently

        Returns:
            Dictionary with album details including message_ids, dates, and photo info

        Raises:
            TelegramError: If album publishing fails
            ValueError: If photos list is invalid (must contain 2-10 photos)
        """
        try:
            # Validate photos list
            if not photos or len(photos) < 2:
                raise ValueError("Album must contain at least 2 photos")
            if len(photos) > 10:
                raise ValueError("Album cannot contain more than 10 photos")

            logger.info(f"Publishing photo album with {len(photos)} photos to channel {channel_id}")

            # Build media group
            media_group = []
            for idx, photo_data in enumerate(photos):
                photo = photo_data.get("photo")
                if not photo:
                    raise ValueError(f"Photo at index {idx} is missing 'photo' field")

                caption = photo_data.get("caption")
                parse_mode_str = photo_data.get("parse_mode", "Markdown")

                # Convert parse_mode string to ParseMode constant
                pm = None
                if parse_mode_str:
                    pm = (
                        ParseMode.MARKDOWN
                        if parse_mode_str.lower() == "markdown"
                        else ParseMode.HTML
                    )

                # Create InputMediaPhoto object
                media_item = InputMediaPhoto(
                    media=photo,
                    caption=caption,
                    parse_mode=pm,
                )
                media_group.append(media_item)

            # Send media group
            messages = await self.bot.send_media_group(
                chat_id=channel_id,
                media=media_group,
                disable_notification=disable_notification,
            )

            # Process results
            album_messages = []
            for message in messages:
                # Get the largest photo size
                photo_info = None
                if message.photo:
                    largest_photo = max(message.photo, key=lambda p: p.file_size or 0)
                    photo_info = {
                        "file_id": largest_photo.file_id,
                        "file_unique_id": largest_photo.file_unique_id,
                        "width": largest_photo.width,
                        "height": largest_photo.height,
                        "file_size": largest_photo.file_size,
                    }

                msg_data = {
                    "message_id": message.message_id,
                    "chat_id": message.chat_id,
                    "date": message.date.isoformat(),
                    "caption": message.caption,
                    "photo": photo_info,
                    "link": self._get_message_link(channel_id, message.message_id),
                }
                album_messages.append(msg_data)

                # Cache each message
                self._cache_message(channel_id, msg_data)

            result = {
                "album_id": messages[0].media_group_id if messages else None,
                "message_count": len(messages),
                "messages": album_messages,
                "first_message_id": messages[0].message_id if messages else None,
                "chat_id": messages[0].chat_id if messages else None,
            }

            logger.info(
                f"Successfully published photo album with {len(messages)} photos to channel {channel_id}"
            )

            return result

        except ValueError as e:
            logger.error(f"Invalid photo album parameters: {e}")
            raise ValueError(str(e)) from e
        except TelegramError as e:
            logger.error(f"Failed to publish photo album to channel {channel_id}: {e}", exc_info=True)
            raise TelegramError(f"Failed to publish photo album: {str(e)}") from e

    async def edit_message(
        self,
        channel_id: str,
        message_id: int,
        new_text: str,
        parse_mode: str = "Markdown",
    ) -> dict[str, Any]:
        """
        Edit an existing message in a Telegram channel.

        Args:
            channel_id: Channel username (e.g., '@mychannel') or chat ID
            message_id: ID of the message to edit
            new_text: New message text
            parse_mode: Parse mode for text formatting ('Markdown', 'HTML', or None)

        Returns:
            Dictionary with updated message details

        Raises:
            TelegramError: If message editing fails
        """
        try:
            logger.info(f"Editing message {message_id} in channel {channel_id}")
            pm = None
            if parse_mode:
                pm = ParseMode.MARKDOWN if parse_mode.lower() == "markdown" else ParseMode.HTML

            message = await self.bot.edit_message_text(
                chat_id=channel_id,
                message_id=message_id,
                text=new_text,
                parse_mode=pm,
            )

            # When chat_id and message_id are provided, result is always a Message
            message = cast(Message, message)

            result = {
                "message_id": message.message_id,
                "chat_id": message.chat_id,
                "date": message.date.isoformat(),
                "edit_date": message.edit_date.isoformat() if message.edit_date else None,
                "text": message.text,
                "link": self._get_message_link(channel_id, message.message_id),
            }

            # Update cache
            self._update_cache(channel_id, result)
            logger.info(f"Successfully edited message {message_id} in channel {channel_id}")

            return result

        except TelegramError as e:
            logger.error(
                f"Failed to edit message {message_id} in channel {channel_id}: {e}", exc_info=True
            )
            raise TelegramError(f"Failed to edit message: {str(e)}") from e

    async def edit_message_caption(
        self,
        channel_id: str,
        message_id: int,
        new_caption: str,
        parse_mode: str = "Markdown",
    ) -> dict[str, Any]:
        """
        Edit the caption of a photo message in a Telegram channel.

        Note: This only works for messages with media (photos, videos, etc.).
        You cannot change the photo itself, only the caption text.

        Args:
            channel_id: Channel username (e.g., '@mychannel') or chat ID
            message_id: ID of the message to edit
            new_caption: New caption text
            parse_mode: Parse mode for caption formatting ('Markdown', 'HTML', or None)

        Returns:
            Dictionary with updated message details

        Raises:
            TelegramError: If caption editing fails
        """
        try:
            logger.info(f"Editing caption for message {message_id} in channel {channel_id}")
            pm = None
            if parse_mode:
                pm = ParseMode.MARKDOWN if parse_mode.lower() == "markdown" else ParseMode.HTML

            message = await self.bot.edit_message_caption(
                chat_id=channel_id,
                message_id=message_id,
                caption=new_caption,
                parse_mode=pm,
            )

            # When chat_id and message_id are provided, result is always a Message
            message = cast(Message, message)

            # Get the largest photo size if available
            photo_info = None
            if message.photo:
                largest_photo = max(message.photo, key=lambda p: p.file_size or 0)
                photo_info = {
                    "file_id": largest_photo.file_id,
                    "file_unique_id": largest_photo.file_unique_id,
                    "width": largest_photo.width,
                    "height": largest_photo.height,
                    "file_size": largest_photo.file_size,
                }

            result = {
                "message_id": message.message_id,
                "chat_id": message.chat_id,
                "date": message.date.isoformat(),
                "edit_date": message.edit_date.isoformat() if message.edit_date else None,
                "caption": message.caption,
                "photo": photo_info,
                "link": self._get_message_link(channel_id, message.message_id),
            }

            # Update cache
            self._update_cache(channel_id, result)
            logger.info(
                f"Successfully edited caption for message {message_id} in channel {channel_id}"
            )

            return result

        except TelegramError as e:
            logger.error(
                f"Failed to edit caption for message {message_id} in channel {channel_id}: {e}",
                exc_info=True,
            )
            raise TelegramError(f"Failed to edit message caption: {str(e)}") from e

    async def delete_message(
        self,
        channel_id: str,
        message_id: int,
    ) -> bool:
        """
        Delete a message from a Telegram channel.

        Args:
            channel_id: Channel username (e.g., '@mychannel') or chat ID
            message_id: ID of the message to delete

        Returns:
            True if message was deleted successfully

        Raises:
            TelegramError: If message deletion fails
        """
        try:
            logger.info(f"Deleting message {message_id} from channel {channel_id}")
            result = await self.bot.delete_message(
                chat_id=channel_id,
                message_id=message_id,
            )

            # Remove from cache
            self._remove_from_cache(channel_id, message_id)
            logger.info(f"Successfully deleted message {message_id} from channel {channel_id}")

            return result

        except TelegramError as e:
            logger.error(
                f"Failed to delete message {message_id} from channel {channel_id}: {e}",
                exc_info=True,
            )
            raise TelegramError(f"Failed to delete message: {str(e)}") from e

    async def get_channel_info(self, channel_id: str) -> dict[str, Any]:
        """
        Get information about a Telegram channel.

        Args:
            channel_id: Channel username (e.g., '@mychannel') or chat ID

        Returns:
            Dictionary with channel information

        Raises:
            TelegramError: If channel info retrieval fails
        """
        try:
            logger.info(f"Getting info for channel {channel_id}")
            chat = await self.bot.get_chat(chat_id=channel_id)

            result = {
                "id": chat.id,
                "title": chat.title,
                "username": chat.username,
                "type": chat.type,
                "description": chat.description,
                "invite_link": chat.invite_link,
                "member_count": await self.bot.get_chat_member_count(chat_id=channel_id),
            }
            logger.info(f"Successfully retrieved info for channel {channel_id}")

            return result

        except TelegramError as e:
            logger.error(f"Failed to get channel info for {channel_id}: {e}", exc_info=True)
            raise TelegramError(f"Failed to get channel info: {str(e)}") from e

    def search_messages(
        self,
        channel_id: str,
        query: Optional[str] = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Search messages in the local cache.

        Note: Telegram Bot API doesn't support message search directly.
        This searches through cached messages from publish/edit operations.

        Args:
            channel_id: Channel username or chat ID
            query: Search query (searches in message text). If None, returns all cached messages.
            limit: Maximum number of results to return

        Returns:
            List of matching messages, sorted by date (newest first)
        """
        logger.debug(f"Searching messages in channel {channel_id} with query: {query}")
        cached_messages = self._message_cache.get(channel_id, [])

        if query:
            # Case-insensitive search in message text
            query_lower = query.lower()
            results = [msg for msg in cached_messages if query_lower in msg.get("text", "").lower()]
        else:
            results = cached_messages

        # Sort by date (newest first) and limit
        results.sort(key=lambda x: x.get("date", ""), reverse=True)
        logger.debug(f"Found {len(results[:limit])} matching messages in channel {channel_id}")
        return results[:limit]

    def _get_message_link(self, channel_id: str, message_id: int) -> Optional[str]:
        """Generate a public link to the message if channel has username."""
        if channel_id.startswith("@"):
            username = channel_id[1:]  # Remove @ prefix
            return f"https://t.me/{username}/{message_id}"
        return None

    def _cache_message(self, channel_id: str, message_data: dict[str, Any]) -> None:
        """Add message to cache."""
        if channel_id not in self._message_cache:
            self._message_cache[channel_id] = []
        self._message_cache[channel_id].append(message_data)
        logger.debug(f"Cached message {message_data.get('message_id')} for channel {channel_id}")

    def _update_cache(self, channel_id: str, message_data: dict[str, Any]) -> None:
        """Update cached message."""
        if channel_id in self._message_cache:
            for i, msg in enumerate(self._message_cache[channel_id]):
                if msg.get("message_id") == message_data.get("message_id"):
                    self._message_cache[channel_id][i] = message_data
                    logger.debug(
                        f"Updated cached message {message_data.get('message_id')} for channel {channel_id}"
                    )
                    return
        # If not found in cache, add it
        self._cache_message(channel_id, message_data)

    def _remove_from_cache(self, channel_id: str, message_id: int) -> None:
        """Remove message from cache."""
        if channel_id in self._message_cache:
            self._message_cache[channel_id] = [
                msg
                for msg in self._message_cache[channel_id]
                if msg.get("message_id") != message_id
            ]
            logger.debug(f"Removed message {message_id} from cache for channel {channel_id}")

    async def get_message_info(self, channel_id: str, message_id: int) -> dict[str, Any]:
        """
        Get information about a specific message.

        This is useful for debugging or determining message type before editing.

        Args:
            channel_id: Channel username (e.g., '@mychannel') or chat ID
            message_id: ID of the message to inspect

        Returns:
            Dictionary with message information including type, content, etc.

        Raises:
            TelegramError: If message retrieval fails
        """
        try:
            logger.info(f"Getting info for message {message_id} in channel {channel_id}")
            # Use forward_message to get message info (then delete the forwarded copy)
            # Unfortunately, Telegram Bot API doesn't have a direct "get message" endpoint
            # So we need to check the cache or use other methods

            # Check cache first
            cached = self._message_cache.get(channel_id, [])
            for msg in cached:
                if msg.get("message_id") == message_id:
                    logger.info(
                        f"Successfully retrieved message {message_id} info from channel {channel_id} (from cache)"
                    )
                    return {
                        **msg,
                        "source": "cache",
                        "status": "success",
                    }

            # If not in cache, we can't get it with Bot API (limitation)
            logger.debug(f"Message {message_id} not found in cache for channel {channel_id}")
            return {
                "status": "not_found",
                "message": f"Message {message_id} not found in cache. The Telegram Bot API doesn't provide a way to fetch arbitrary messages. Only messages published/edited through this tool are cached.",
                "hint": "Try publishing or editing the message through this tool to add it to the cache.",
            }

        except TelegramError as e:
            logger.error(
                f"Failed to get message info for {message_id} in channel {channel_id}: {e}",
                exc_info=True,
            )
            raise TelegramError(f"Failed to get message info: {str(e)}") from e

    async def close(self) -> None:
        """Close bot session and cleanup resources."""
        # python-telegram-bot handles cleanup automatically
        pass
