"""Main entry point for the Telegram Bot MCP Server."""

from telegram_bot.server import mcp


def main():
    """Run the Telegram Bot MCP Server."""
    mcp.run()


if __name__ == "__main__":
    main()
