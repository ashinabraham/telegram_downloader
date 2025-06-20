"""
Telegram client module for the File Downloader Bot.
Handles client initialization and connection management.
"""

import asyncio
import logging
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

from ..core.config import get_config
from ..core.user_state import UserState

logger = logging.getLogger(__name__)

# Get configuration
config = get_config()

# Initialize user state
user_state = UserState()

# Initialize Telegram client
client = TelegramClient(
    config.session_name,
    config.api_id,
    config.api_hash
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