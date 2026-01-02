"""Telegram Bot MCP Server - Model Context Protocol server for Telegram Bot operations.

This package provides an MCP server that enables AI assistants to publish, edit,
search, and manage messages in Telegram channels.
"""

from telegram_bot.telegram_bot_client import TelegramBotClient
from telegram_bot.server import mcp

__version__ = "0.1.0"

__all__ = [
    "TelegramBotClient",
    "mcp",
]
