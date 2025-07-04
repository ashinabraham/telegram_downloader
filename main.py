"""
Main entry point for the Telegram File Downloader Bot.
Initializes all modules and starts the bot.
"""

import asyncio
import logging

# Import all modules to register handlers
from src.core.user_state import user_state
from src.bot.client import client, start_client, run_until_disconnected, stop_client
from src.handlers.command_handlers import start_handler, help_handler, status_handler
from src.handlers.callback_handlers import callback_handler
from src.handlers.message_handlers import message_handler

logger = logging.getLogger(__name__)


async def main():
    """Main function to start the bot."""
    logger.info("Starting Telegram File Downloader Bot...")

    try:
        # Start the Telegram client
        await start_client()
        logger.info("Bot connected successfully")
        print("Bot is running... Press Ctrl+C to stop.")

        # Run the bot until disconnected
        await run_until_disconnected()

    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
    except Exception as e:
        logger.error(f"Bot failed to start: {e}")
        raise
    finally:
        logger.info("Bot shutting down")
        await stop_client()


if __name__ == "__main__":
    logger.info("Initializing bot application")
    asyncio.run(main())
