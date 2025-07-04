"""
Main entry point for the Telegram File Downloader Bot.
Initializes all modules and starts the bot.
"""

import asyncio
import logging
import sys
import os

# Configure logging to display in console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

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

    # Debug: Log environment variables (without sensitive data)
    logger.info(
        f"Environment check - API_ID: {'SET' if os.getenv('API_ID') else 'NOT SET'}"
    )
    logger.info(
        f"Environment check - API_HASH: {'SET' if os.getenv('API_HASH') else 'NOT SET'}"
    )
    logger.info(
        f"Environment check - BOT_TOKEN: {'SET' if os.getenv('BOT_TOKEN') else 'NOT SET'}"
    )
    logger.info(
        f"Environment check - ALLOWED_USERS: {'SET' if os.getenv('ALLOWED_USERS') else 'NOT SET'}"
    )

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
