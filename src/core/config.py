"""
Configuration module for the Telegram File Downloader Bot.
Handles environment variables, settings, and validation.
"""

import os
import logging
import pathlib
from dotenv import load_dotenv

logger = logging.getLogger("src.core.config")


class Config:
    """Configuration class for the bot."""

    def __init__(self):
        # Load environment variables
        load_dotenv()

        # Debug: Check if .env file exists and what's loaded
        env_path = pathlib.Path(".env")
        logger.info(f".env file exists: {env_path.exists()}")
        logger.info(f"Current working directory: {pathlib.Path.cwd()}")

        # Check what's actually loaded
        logger.info(f"API_ID from env: {repr(os.getenv('API_ID'))}")
        logger.info(f"API_HASH from env: {repr(os.getenv('API_HASH'))}")
        logger.info(f"BOT_TOKEN from env: {repr(os.getenv('BOT_TOKEN'))}")
        logger.info(f"ALLOWED_USERS from env: {repr(os.getenv('ALLOWED_USERS'))}")

        # Load configuration
        self.api_id = os.getenv("API_ID")
        self.api_hash = os.getenv("API_HASH")
        self.bot_token = os.getenv("BOT_TOKEN")

        # Parse allowed users, handling whitespace and empty values
        allowed_users_str = os.getenv("ALLOWED_USERS", "")
        if allowed_users_str.strip():
            self.allowed_users = {
                user.strip() for user in allowed_users_str.split(",") if user.strip()
            }
        else:
            self.allowed_users = set()

        # Bot settings
        self.session_name = "downloader_bot_session"
        self.root_download_path = os.getenv("ROOT_DOWNLOAD_PATH", "/app/downloads")
        self.base_download_dir = self.root_download_path

        # Download settings
        self.download_chunk_size = 8 * 1024 * 1024  # 8MB chunks (increased from 1MB)
        self.progress_update_interval = 5.0  # Update progress every 5 seconds
        self.max_concurrent_downloads = 3  # Reduced to avoid rate limiting
        self.notification_cooldown = (
            30  # Minimum seconds between notifications per user
        )

        # Connection settings
        self.connection_retries = 5
        self.retry_delay = 1
        self.timeout = 60  # Increased timeout for large files
        self.request_retries = 5
        self.flood_sleep_threshold = 60

        self._validate_config()
        self._log_config()

    def _validate_config(self):
        """Validate required configuration values."""
        if not self.api_id or not self.api_hash or not self.bot_token:
            logger.error("Missing required environment variables")
            raise ValueError(
                "API_ID, API_HASH, and BOT_TOKEN must be set in the environment variables."
            )

        # Convert API_ID to int
        try:
            self.api_id = int(self.api_id)
        except ValueError:
            raise ValueError("API_ID must be a valid integer.")

        logger.info(f"API_ID converted to int: {self.api_id}")

    def _log_config(self):
        """Log configuration details (without sensitive data)."""
        logger.info(
            f"Loaded environment variables - API_ID: {self.api_id}, API_HASH: {'*' * len(self.api_hash) if self.api_hash else 'None'}, BOT_TOKEN: {'*' * len(self.bot_token) if self.bot_token else 'None'}"
        )
        logger.info(f"Allowed users: {self.allowed_users}")
        logger.info("Configuration validation completed successfully")


# Global configuration instance - created lazily when needed
_config_instance = None


def get_config():
    """Get the global configuration instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance


# Create and export the global config instance
config = get_config()

# Export symbols
__all__ = ["Config", "config", "get_config"]
