"""Main entry point for the Telegram Bot MCP Server when run as a module."""

from telegram_bot.server import mcp


def main() -> None:
    """Run the Telegram Bot MCP Server."""
    mcp.run()


if __name__ == "__main__":
    main()
