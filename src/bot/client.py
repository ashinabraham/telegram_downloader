"""
Telegram client module for the File Downloader Bot.
Handles client initialization and connection management.
"""

import logging
from telethon import TelegramClient

from ..core.config import get_config
from ..core.user_state import UserState

logger = logging.getLogger(__name__)

# Get configuration
config = get_config()

# Initialize user state
user_state = UserState()

# Initialize Telegram client with explicit type casting
api_id: int = config.api_id  # type: ignore
api_hash: str = config.api_hash  # type: ignore
bot_token: str = config.bot_token  # type: ignore

# Initialize client with optimized settings for downloads
client: TelegramClient = TelegramClient(
    "bot_session",
    api_id,
    api_hash,
    # Optimized connection settings for downloads
    connection_retries=config.max_retries,
    retry_delay=1,
    timeout=int(config.async_io_timeout),
    request_retries=config.max_retries,
    # Download optimizations
    flood_sleep_threshold=60,
)
logger.info("Telethon client initialized with optimized settings")


async def is_logged_in() -> bool:
    """Check if the client is logged in."""
    try:
        me = await client.get_me()
        username = getattr(me, "username", "Unknown")
        user_id = getattr(me, "id", "Unknown")
        logger.info(f"User logged in: {username} ({user_id})")
        return True
    except Exception as e:
        logger.warning(f"Not logged in: {e}")
        return False


async def start_client() -> None:
    """Start the Telegram client."""
    logger.info("Starting Telegram client...")
    try:
        await client.start(bot_token=bot_token)  # type: ignore
        logger.info("Telegram client connected successfully")
    except Exception as e:
        logger.error(f"Failed to start Telegram client: {e}")
        raise


async def stop_client() -> None:
    """Stop the Telegram client."""
    logger.info("Stopping Telegram client...")
    try:
        await client.disconnect()  # type: ignore
        logger.info("Telegram client disconnected successfully")
    except Exception as e:
        logger.error(f"Error stopping Telegram client: {e}")


async def run_until_disconnected() -> None:
    """Run the client until disconnected."""
    try:
        await client.run_until_disconnected()  # type: ignore
    except Exception as e:
        logger.error(f"Client disconnected with error: {e}")
        raise
