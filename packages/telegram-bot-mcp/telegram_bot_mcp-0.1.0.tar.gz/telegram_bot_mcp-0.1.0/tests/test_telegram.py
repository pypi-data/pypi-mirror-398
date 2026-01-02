"""Tests for Telegram tools."""

import os
import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime

from telegram_bot import server
from telegram_bot.telegram_bot_client import TelegramBotClient

# Access the tool functions directly (new MCP version)
publish_message = server.publish_message
publish_photo = server.publish_photo
publish_photo_album = server.publish_photo_album
edit_message = server.edit_message
edit_message_caption = server.edit_message_caption
delete_message = server.delete_message
search_messages = server.search_messages
get_channel_info = server.get_channel_info


@pytest.fixture
def mock_bot_token():
    """Set up mock bot token."""
    original = os.environ.get("TELEGRAM_BOT_TOKEN")
    os.environ["TELEGRAM_BOT_TOKEN"] = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
    yield
    if original:
        os.environ["TELEGRAM_BOT_TOKEN"] = original
    else:
        del os.environ["TELEGRAM_BOT_TOKEN"]


@pytest.fixture
def mock_telegram_message():
    """Create a mock Telegram message object."""
    message = Mock()
    message.message_id = 12345
    message.chat_id = -1001234567890
    message.date = datetime(2024, 1, 15, 10, 30, 0)
    message.edit_date = None
    message.text = "Test message"
    return message


@pytest.fixture
def mock_telegram_photo_message():
    """Create a mock Telegram photo message object."""
    photo_size = Mock()
    photo_size.file_id = "AgACAgIAAxkBAAMCY1234567890"
    photo_size.file_unique_id = "AQADAgATxxx"
    photo_size.width = 1280
    photo_size.height = 720
    photo_size.file_size = 102400

    message = Mock()
    message.message_id = 12345
    message.chat_id = -1001234567890
    message.date = datetime(2024, 1, 15, 10, 30, 0)
    message.edit_date = None
    message.caption = "Test photo caption"
    message.photo = [photo_size]
    return message


@pytest.fixture
def mock_telegram_album_messages():
    """Create a list of mock Telegram photo messages for an album."""
    messages = []
    media_group_id = "12345678901234567"

    for i in range(3):
        photo_size = Mock()
        photo_size.file_id = f"AgACAgIAAxkBAAMCY123456789{i}"
        photo_size.file_unique_id = f"AQADAgATxx{i}"
        photo_size.width = 1280
        photo_size.height = 720
        photo_size.file_size = 102400 + (i * 1000)

        message = Mock()
        message.message_id = 12345 + i
        message.chat_id = -1001234567890
        message.date = datetime(2024, 1, 15, 10, 30, i)
        message.edit_date = None
        message.caption = f"Photo {i+1}" if i == 0 else None
        message.photo = [photo_size]
        message.media_group_id = media_group_id
        messages.append(message)

    return messages


class TestTelegramClient:
    """Tests for TelegramBotClient."""

    def test_client_init_with_token(self):
        """Test client initialization with explicit token."""
        client = TelegramBotClient(bot_token="test_token")
        assert client.bot_token == "test_token"
        assert client.bot is not None

    def test_client_init_from_env(self, mock_bot_token):
        """Test client initialization from environment variable."""
        client = TelegramBotClient()
        assert client.bot_token is not None
        assert client.bot is not None

    def test_client_init_no_token(self):
        """Test client initialization fails without token."""
        # Temporarily remove env var
        original = os.environ.get("TELEGRAM_BOT_TOKEN")
        if "TELEGRAM_BOT_TOKEN" in os.environ:
            del os.environ["TELEGRAM_BOT_TOKEN"]

        with pytest.raises(ValueError, match="Telegram bot token is required"):
            TelegramBotClient()

        # Restore env var
        if original:
            os.environ["TELEGRAM_BOT_TOKEN"] = original

    @pytest.mark.asyncio
    async def test_publish_message(self, mock_bot_token, mock_telegram_message):
        """Test publishing a message."""
        with patch("telegram_bot.telegram_bot_client.Bot") as MockBot:
            mock_bot_instance = MockBot.return_value
            mock_bot_instance.send_message = AsyncMock(return_value=mock_telegram_message)

            client = TelegramBotClient()
            result = await client.publish_message(
                channel_id="@testchannel",
                text="Test message",
            )

            assert result["message_id"] == 12345
            assert result["chat_id"] == -1001234567890
            assert result["text"] == "Test message"
            assert "link" in result
            mock_bot_instance.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_edit_message(self, mock_bot_token, mock_telegram_message):
        """Test editing a message."""
        mock_telegram_message.edit_date = datetime(2024, 1, 15, 11, 0, 0)
        mock_telegram_message.text = "Updated message"

        with patch("telegram_bot.telegram_bot_client.Bot") as MockBot:
            mock_bot_instance = MockBot.return_value
            mock_bot_instance.edit_message_text = AsyncMock(return_value=mock_telegram_message)

            client = TelegramBotClient()
            result = await client.edit_message(
                channel_id="@testchannel",
                message_id=12345,
                new_text="Updated message",
            )

            assert result["message_id"] == 12345
            assert result["text"] == "Updated message"
            assert result["edit_date"] is not None
            mock_bot_instance.edit_message_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_message(self, mock_bot_token):
        """Test deleting a message."""
        with patch("telegram_bot.telegram_bot_client.Bot") as MockBot:
            mock_bot_instance = MockBot.return_value
            mock_bot_instance.delete_message = AsyncMock(return_value=True)

            client = TelegramBotClient()
            result = await client.delete_message(
                channel_id="@testchannel",
                message_id=12345,
            )

            assert result is True
            mock_bot_instance.delete_message.assert_called_once()

    def test_search_messages_with_query(self, mock_bot_token):
        """Test searching messages with a query."""
        client = TelegramBotClient()

        # Manually populate cache
        client._message_cache["@testchannel"] = [
            {"message_id": 1, "text": "Hello world", "date": "2024-01-15T10:00:00"},
            {"message_id": 2, "text": "Goodbye world", "date": "2024-01-15T11:00:00"},
            {"message_id": 3, "text": "Test message", "date": "2024-01-15T12:00:00"},
        ]

        results = client.search_messages(
            channel_id="@testchannel",
            query="world",
            limit=10,
        )

        assert len(results) == 2
        assert all("world" in msg["text"].lower() for msg in results)
        # Should be sorted by date (newest first)
        assert results[0]["message_id"] == 2

    def test_search_messages_no_query(self, mock_bot_token):
        """Test searching messages without a query (get all)."""
        client = TelegramBotClient()

        client._message_cache["@testchannel"] = [
            {"message_id": 1, "text": "Message 1", "date": "2024-01-15T10:00:00"},
            {"message_id": 2, "text": "Message 2", "date": "2024-01-15T11:00:00"},
        ]

        results = client.search_messages(
            channel_id="@testchannel",
            query=None,
            limit=10,
        )

        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_get_channel_info(self, mock_bot_token):
        """Test getting channel information."""
        mock_chat = Mock()
        mock_chat.id = -1001234567890
        mock_chat.title = "Test Channel"
        mock_chat.username = "testchannel"
        mock_chat.type = "channel"
        mock_chat.description = "A test channel"
        mock_chat.invite_link = "https://t.me/testchannel"

        with patch("telegram_bot.telegram_bot_client.Bot") as MockBot:
            mock_bot_instance = MockBot.return_value
            mock_bot_instance.get_chat = AsyncMock(return_value=mock_chat)
            mock_bot_instance.get_chat_member_count = AsyncMock(return_value=1234)

            client = TelegramBotClient()
            result = await client.get_channel_info(channel_id="@testchannel")

            assert result["id"] == -1001234567890
            assert result["title"] == "Test Channel"
            assert result["username"] == "testchannel"
            assert result["member_count"] == 1234

    @pytest.mark.asyncio
    async def test_get_message_info_from_cache(self, mock_bot_token):
        """Test getting message info from cache."""
        client = TelegramBotClient()

        # Manually populate cache
        test_message = {
            "message_id": 12345,
            "chat_id": -1001234567890,
            "text": "Test message",
            "date": "2024-01-15T10:30:00",
        }
        client._message_cache["@testchannel"] = [test_message]

        result = await client.get_message_info(
            channel_id="@testchannel",
            message_id=12345,
        )

        assert result["status"] == "success"
        assert result["source"] == "cache"
        assert result["message_id"] == 12345
        assert result["text"] == "Test message"

    @pytest.mark.asyncio
    async def test_get_message_info_not_found(self, mock_bot_token):
        """Test getting message info when not in cache."""
        client = TelegramBotClient()

        result = await client.get_message_info(
            channel_id="@testchannel",
            message_id=99999,
        )

        assert result["status"] == "not_found"
        assert "not found in cache" in result["message"]
        assert "hint" in result

    def test_get_message_link_with_username(self, mock_bot_token):
        """Test generating message link for channel with username."""
        client = TelegramBotClient()
        link = client._get_message_link("@testchannel", 12345)
        assert link == "https://t.me/testchannel/12345"

    def test_get_message_link_without_username(self, mock_bot_token):
        """Test generating message link for channel without username."""
        client = TelegramBotClient()
        link = client._get_message_link("-1001234567890", 12345)
        assert link is None

    @pytest.mark.asyncio
    async def test_publish_photo(self, mock_bot_token, mock_telegram_photo_message):
        """Test publishing a photo."""
        with patch("telegram_bot.telegram_bot_client.Bot") as MockBot:
            mock_bot_instance = MockBot.return_value
            mock_bot_instance.send_photo = AsyncMock(return_value=mock_telegram_photo_message)

            client = TelegramBotClient()
            result = await client.publish_photo(
                channel_id="@testchannel",
                photo="/path/to/image.jpg",
                caption="Test photo caption",
            )

            assert result["message_id"] == 12345
            assert result["chat_id"] == -1001234567890
            assert result["caption"] == "Test photo caption"
            assert "photo" in result
            assert result["photo"]["file_id"] == "AgACAgIAAxkBAAMCY1234567890"
            assert result["photo"]["width"] == 1280
            assert result["photo"]["height"] == 720
            assert "link" in result
            mock_bot_instance.send_photo.assert_called_once()

    @pytest.mark.asyncio
    async def test_edit_message_caption(self, mock_bot_token, mock_telegram_photo_message):
        """Test editing a photo message caption."""
        mock_telegram_photo_message.edit_date = datetime(2024, 1, 15, 11, 0, 0)
        mock_telegram_photo_message.caption = "Updated caption"

        with patch("telegram_bot.telegram_bot_client.Bot") as MockBot:
            mock_bot_instance = MockBot.return_value
            mock_bot_instance.edit_message_caption = AsyncMock(
                return_value=mock_telegram_photo_message
            )

            client = TelegramBotClient()
            result = await client.edit_message_caption(
                channel_id="@testchannel",
                message_id=12345,
                new_caption="Updated caption",
            )

            assert result["message_id"] == 12345
            assert result["caption"] == "Updated caption"
            assert result["edit_date"] is not None
            assert "photo" in result
            assert result["photo"]["file_id"] == "AgACAgIAAxkBAAMCY1234567890"
            mock_bot_instance.edit_message_caption.assert_called_once()

    @pytest.mark.asyncio
    async def test_publish_photo_album(self, mock_bot_token, mock_telegram_album_messages):
        """Test publishing a photo album."""
        with patch("telegram_bot.telegram_bot_client.Bot") as MockBot:
            mock_bot_instance = MockBot.return_value
            mock_bot_instance.send_media_group = AsyncMock(
                return_value=mock_telegram_album_messages
            )

            client = TelegramBotClient()
            photos = [
                {"photo": "/path/to/photo1.jpg", "caption": "Photo 1"},
                {"photo": "/path/to/photo2.jpg"},
                {"photo": "/path/to/photo3.jpg"},
            ]
            result = await client.publish_photo_album(
                channel_id="@testchannel",
                photos=photos,
            )

            assert result["album_id"] == "12345678901234567"
            assert result["message_count"] == 3
            assert result["first_message_id"] == 12345
            assert len(result["messages"]) == 3
            assert result["messages"][0]["caption"] == "Photo 1"
            mock_bot_instance.send_media_group.assert_called_once()

    @pytest.mark.asyncio
    async def test_publish_photo_album_validation(self, mock_bot_token):
        """Test photo album validation errors."""
        client = TelegramBotClient()

        # Test with too few photos
        with pytest.raises(ValueError, match="at least 2 photos"):
            await client.publish_photo_album(
                channel_id="@testchannel",
                photos=[{"photo": "/path/to/photo1.jpg"}],
            )

        # Test with too many photos
        with pytest.raises(ValueError, match="cannot contain more than 10"):
            photos = [{"photo": f"/path/to/photo{i}.jpg"} for i in range(11)]
            await client.publish_photo_album(
                channel_id="@testchannel",
                photos=photos,
            )

        # Test with missing photo field
        with pytest.raises(ValueError, match="missing 'photo' field"):
            await client.publish_photo_album(
                channel_id="@testchannel",
                photos=[{"photo": "/path/to/photo1.jpg"}, {"caption": "No photo"}],
            )


class TestTelegramTools:
    """Tests for Telegram tool functions."""

    @pytest.mark.asyncio
    async def test_publish_message_tool(self, mock_bot_token, mock_telegram_message):
        """Test publish_message tool function."""
        with patch("telegram_bot.server._get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.publish_message = AsyncMock(
                return_value={
                    "message_id": 12345,
                    "chat_id": -1001234567890,
                    "date": "2024-01-15T10:30:00",
                    "text": "Test message",
                    "link": "https://t.me/testchannel/12345",
                }
            )
            mock_get_client.return_value = mock_client

            result = await publish_message(
                channel_id="@testchannel",
                text="Test message",
            )

            assert result["message_id"] == 12345
            assert "error" not in result

    @pytest.mark.asyncio
    async def test_edit_message_tool(self, mock_bot_token):
        """Test edit_message tool function."""
        with patch("telegram_bot.server._get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.edit_message = AsyncMock(
                return_value={
                    "message_id": 12345,
                    "text": "Updated message",
                    "edit_date": "2024-01-15T11:00:00",
                }
            )
            mock_get_client.return_value = mock_client

            result = await edit_message(
                channel_id="@testchannel",
                message_id=12345,
                new_text="Updated message",
            )

            assert result["message_id"] == 12345
            assert "error" not in result

    @pytest.mark.asyncio
    async def test_delete_message_tool(self, mock_bot_token):
        """Test delete_message tool function."""
        with patch("telegram_bot.server._get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.delete_message = AsyncMock(return_value=True)
            mock_get_client.return_value = mock_client

            result = await delete_message(
                channel_id="@testchannel",
                message_id=12345,
            )

            assert result["success"] is True
            assert result["status"] == "deleted"

    def test_search_messages_tool(self, mock_bot_token):
        """Test search_messages tool function."""
        with patch("telegram_bot.server._get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.search_messages = Mock(
                return_value=[
                    {"message_id": 1, "text": "Test 1"},
                    {"message_id": 2, "text": "Test 2"},
                ]
            )
            mock_get_client.return_value = mock_client

            result = search_messages(
                channel_id="@testchannel",
                query="test",
            )

            assert result["count"] == 2
            assert len(result["messages"]) == 2
            assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_get_channel_info_tool(self, mock_bot_token):
        """Test get_channel_info tool function."""
        with patch("telegram_bot.server._get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.get_channel_info = AsyncMock(
                return_value={
                    "id": -1001234567890,
                    "title": "Test Channel",
                    "username": "testchannel",
                    "member_count": 1234,
                }
            )
            mock_get_client.return_value = mock_client

            result = await get_channel_info(channel_id="@testchannel")

            assert result["id"] == -1001234567890
            assert result["title"] == "Test Channel"
            assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_publish_photo_tool(self, mock_bot_token):
        """Test publish_photo tool function."""
        with patch("telegram_bot.server._get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.publish_photo = AsyncMock(
                return_value={
                    "message_id": 12345,
                    "chat_id": -1001234567890,
                    "date": "2024-01-15T10:30:00",
                    "caption": "Test photo caption",
                    "photo": {
                        "file_id": "AgACAgIAAxkBAAMCY1234567890",
                        "width": 1280,
                        "height": 720,
                        "file_size": 102400,
                    },
                    "link": "https://t.me/testchannel/12345",
                }
            )
            mock_get_client.return_value = mock_client

            result = await publish_photo(
                channel_id="@testchannel",
                photo="/path/to/image.jpg",
                caption="Test photo caption",
            )

            assert result["message_id"] == 12345
            assert result["caption"] == "Test photo caption"
            assert "photo" in result
            assert result["photo"]["file_id"] == "AgACAgIAAxkBAAMCY1234567890"
            assert "error" not in result

    @pytest.mark.asyncio
    async def test_edit_message_caption_tool(self, mock_bot_token):
        """Test edit_message_caption tool function."""
        with patch("telegram_bot.server._get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.edit_message_caption = AsyncMock(
                return_value={
                    "message_id": 12345,
                    "caption": "Updated caption",
                    "edit_date": "2024-01-15T11:00:00",
                    "photo": {
                        "file_id": "AgACAgIAAxkBAAMCY1234567890",
                        "width": 1280,
                        "height": 720,
                        "file_size": 102400,
                    },
                }
            )
            mock_get_client.return_value = mock_client

            result = await edit_message_caption(
                channel_id="@testchannel",
                message_id=12345,
                new_caption="Updated caption",
            )

            assert result["message_id"] == 12345
            assert result["caption"] == "Updated caption"
            assert result["edit_date"] == "2024-01-15T11:00:00"
            assert "photo" in result
            assert "error" not in result

    @pytest.mark.asyncio
    async def test_publish_photo_album_tool(self, mock_bot_token):
        """Test publish_photo_album tool function."""
        with patch("telegram_bot.server._get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.publish_photo_album = AsyncMock(
                return_value={
                    "album_id": "12345678901234567",
                    "message_count": 3,
                    "first_message_id": 12345,
                    "messages": [
                        {
                            "message_id": 12345,
                            "caption": "Photo 1",
                            "photo": {"file_id": "AgACAgIAAxkBAAMCY1234567890"},
                        },
                        {
                            "message_id": 12346,
                            "caption": None,
                            "photo": {"file_id": "AgACAgIAAxkBAAMCY1234567891"},
                        },
                        {
                            "message_id": 12347,
                            "caption": None,
                            "photo": {"file_id": "AgACAgIAAxkBAAMCY1234567892"},
                        },
                    ],
                }
            )
            mock_get_client.return_value = mock_client

            photos = [
                {"photo": "/path/to/photo1.jpg", "caption": "Photo 1"},
                {"photo": "/path/to/photo2.jpg"},
                {"photo": "/path/to/photo3.jpg"},
            ]
            result = await publish_photo_album(
                channel_id="@testchannel",
                photos=photos,
            )

            assert result["album_id"] == "12345678901234567"
            assert result["message_count"] == 3
            assert result["first_message_id"] == 12345
            assert len(result["messages"]) == 3
            assert "error" not in result
