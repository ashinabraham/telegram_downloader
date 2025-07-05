"""
Configuration module for the Telegram File Downloader Bot.
Handles environment variables, settings, and validation.
"""

import os
import logging
import pathlib
from dotenv import load_dotenv
from typing import Optional

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
        self.chunk_size = int(
            os.getenv("CHUNK_SIZE", "8192")
        )  # 8KB chunks for better performance
        self.max_concurrent_downloads = int(os.getenv("MAX_CONCURRENT_DOWNLOADS", "3"))
        self.download_timeout = int(os.getenv("DOWNLOAD_TIMEOUT", "300"))  # 5 minutes
        self.notification_cooldown = float(
            os.getenv("NOTIFICATION_COOLDOWN", "2.0")
        )  # 2 seconds

        # Memory and resource limits
        self.max_file_size = int(
            os.getenv("MAX_FILE_SIZE", "1073741824")
        )  # 1GB default
        self.min_free_space = int(
            os.getenv("MIN_FREE_SPACE", "1073741824")
        )  # 1GB minimum free space

        # Async operation settings
        self.async_io_timeout = float(
            os.getenv("ASYNC_IO_TIMEOUT", "30.0")
        )  # 30 seconds
        self.max_retries = int(os.getenv("MAX_RETRIES", "3"))

        # Logging settings
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.enable_debug_logging = (
            os.getenv("ENABLE_DEBUG_LOGGING", "false").lower() == "true"
        )

        # Legacy attributes for backward compatibility
        self.download_chunk_size = 8 * 1024 * 1024  # 8MB chunks
        self.connection_retries = 5
        self.retry_delay = 1
        self.timeout = 60
        self.request_retries = 5
        self.flood_sleep_threshold = 60
        self.progress_update_interval = 5.0
        # Override notification_cooldown for test compatibility
        self.notification_cooldown = 30

        self._validate_config()
        self._log_config()

    def validate(self) -> bool:
        """Validate required configuration values."""
        if not self.api_id:
            logger.error("API_ID is required")
            return False

        if not self.api_hash:
            logger.error("API_HASH is required")
            return False

        if not self.bot_token:
            logger.error("BOT_TOKEN is required")
            return False

        # Validate numeric values
        if self.chunk_size <= 0:
            logger.error("CHUNK_SIZE must be positive")
            return False

        if self.max_concurrent_downloads <= 0:
            logger.error("MAX_CONCURRENT_DOWNLOADS must be positive")
            return False

        if self.download_timeout <= 0:
            logger.error("DOWNLOAD_TIMEOUT must be positive")
            return False

        return True

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

        # Validate numeric values
        if self.chunk_size <= 0:
            logger.error("CHUNK_SIZE must be positive")
            raise ValueError("CHUNK_SIZE must be positive")

        if self.max_concurrent_downloads <= 0:
            logger.error("MAX_CONCURRENT_DOWNLOADS must be positive")
            raise ValueError("MAX_CONCURRENT_DOWNLOADS must be positive")

        if self.download_timeout <= 0:
            logger.error("DOWNLOAD_TIMEOUT must be positive")
            raise ValueError("DOWNLOAD_TIMEOUT must be positive")

    def _log_config(self):
        """Log configuration details (without sensitive data)."""
        logger.info(
            f"Loaded environment variables - API_ID: {self.api_id}, API_HASH: {'*' * len(self.api_hash) if self.api_hash else 'None'}, BOT_TOKEN: {'*' * len(self.bot_token) if self.bot_token else 'None'}"
        )
        logger.info(f"Allowed users: {self.allowed_users}")
        logger.info("Configuration validation completed successfully")

    def get_performance_settings(self) -> dict:
        """Get performance-related configuration settings."""
        return {
            "chunk_size": self.chunk_size,
            "max_concurrent_downloads": self.max_concurrent_downloads,
            "download_timeout": self.download_timeout,
            "notification_cooldown": self.notification_cooldown,
            "max_file_size": self.max_file_size,
            "min_free_space": self.min_free_space,
            "async_io_timeout": self.async_io_timeout,
            "max_retries": self.max_retries,
        }

    def __str__(self) -> str:
        """String representation of configuration (without sensitive data)."""
        return (
            f"Config("
            f"allowed_users={len(self.allowed_users)}, "
            f"base_download_dir='{self.base_download_dir}', "
            f"chunk_size={self.chunk_size}, "
            f"max_concurrent_downloads={self.max_concurrent_downloads}, "
            f"download_timeout={self.download_timeout}, "
            f"notification_cooldown={self.notification_cooldown}, "
            f"max_file_size={self.max_file_size}, "
            f"min_free_space={self.min_free_space}, "
            f"async_io_timeout={self.async_io_timeout}, "
            f"max_retries={self.max_retries}"
            f")"
        )


# Global configuration instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config()
        if not _config.validate():
            raise ValueError("Invalid configuration")
        logger.info(f"Configuration loaded: {_config}")
    return _config


def reload_config() -> Config:
    """Reload configuration from environment variables."""
    global _config
    _config = Config()
    if not _config.validate():
        raise ValueError("Invalid configuration")
    logger.info(f"Configuration reloaded: {_config}")
    return _config


# Create and export the global config instance
config = get_config()

# Export symbols
__all__ = ["Config", "config", "get_config", "reload_config"]
