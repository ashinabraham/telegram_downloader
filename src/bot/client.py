"""
Telegram client module for the Telegram File Downloader Bot.
Handles Telethon client initialization and connection management.
"""

import logging
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

from ..core.config import config

logger = logging.getLogger(__name__)

# Initialize Telethon client with optimized settings
client = TelegramClient(
    config.session_name, 
    config.api_id, 
    config.api_hash,
    connection_retries=config.connection_retries,
    retry_delay=config.retry_delay,
    timeout=config.timeout,
    request_retries=config.request_retries,
    flood_sleep_threshold=config.flood_sleep_threshold
)
logger.info("Telethon client initialized with optimized settings")

async def is_logged_in() -> bool:
    """Check if the client is logged in."""
    try:
        me = await client.get_me()
        username = getattr(me, 'username', 'Unknown')
        user_id = getattr(me, 'id', 'Unknown')
        logger.info(f"User logged in: {username} ({user_id})")
        return True
    except Exception as e:
        logger.warning(f"Not logged in: {e}")
        return False

async def start_client() -> None:
    """Start the Telegram client."""
    logger.info("Starting Telegram client...")
    try:
        await client.start(bot_token=config.bot_token)
        logger.info("Telegram client connected successfully")
    except Exception as e:
        logger.error(f"Failed to start Telegram client: {e}")
        raise

async def stop_client() -> None:
    """Stop the Telegram client."""
    logger.info("Stopping Telegram client...")
    try:
        await client.disconnect()
        logger.info("Telegram client disconnected successfully")
    except Exception as e:
        logger.error(f"Error stopping Telegram client: {e}")

async def run_until_disconnected() -> None:
    """Run the client until disconnected."""
    try:
        await client.run_until_disconnected()
    except Exception as e:
        logger.error(f"Client disconnected with error: {e}")
        raise 