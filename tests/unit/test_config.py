"""
Unit tests for the configuration module.
"""

import pytest
import os
from unittest.mock import patch, MagicMock
from src.core.config import Config


class TestConfig:
    """Test cases for Config class."""

    def test_config_initialization_success(self, test_env_vars, test_base_download_dir):
        """Test successful configuration initialization."""
        test_env_vars["ROOT_DOWNLOAD_PATH"] = test_base_download_dir
        with patch.dict(os.environ, test_env_vars):
            config = Config()

            assert config.api_id == 12345
            assert config.api_hash == "test_hash_123456789"
            assert config.bot_token == "test_bot_token_123456789"
            assert config.allowed_users == {"123456", "789012", "345678"}
            assert config.session_name == "downloader_bot_session"
            assert config.base_download_dir == test_base_download_dir
            assert config.download_chunk_size == 8 * 1024 * 1024  # 8MB
            assert config.progress_update_interval == 5.0
            assert config.max_concurrent_downloads == 3
            assert config.notification_cooldown == 30
            assert config.connection_retries == 5
            assert config.retry_delay == 1
            assert config.timeout == 60
            assert config.request_retries == 5
            assert config.flood_sleep_threshold == 60

    def test_config_invalid_api_id(self, test_env_vars, test_base_download_dir):
        """Test configuration with invalid API_ID."""
        test_env_vars["API_ID"] = "invalid"
        test_env_vars["ROOT_DOWNLOAD_PATH"] = test_base_download_dir
        with patch.dict(os.environ, test_env_vars):
            with pytest.raises(ValueError, match="API_ID must be a valid integer"):
                Config()

    def test_config_empty_allowed_users(self, test_env_vars, test_base_download_dir):
        """Test configuration with empty allowed users."""
        test_env_vars["ALLOWED_USERS"] = ""
        test_env_vars["ROOT_DOWNLOAD_PATH"] = test_base_download_dir
        with patch.dict(os.environ, test_env_vars):
            config = Config()
            assert config.allowed_users == set()

    def test_config_single_allowed_user(self, test_env_vars, test_base_download_dir):
        """Test configuration with single allowed user."""
        test_env_vars["ALLOWED_USERS"] = "123456"
        test_env_vars["ROOT_DOWNLOAD_PATH"] = test_base_download_dir
        with patch.dict(os.environ, test_env_vars):
            config = Config()
            assert config.allowed_users == {"123456"}

    def test_config_connection_settings(self, test_env_vars, test_base_download_dir):
        """Test connection settings are properly set."""
        test_env_vars["ROOT_DOWNLOAD_PATH"] = test_base_download_dir
        with patch.dict(os.environ, test_env_vars):
            config = Config()

            assert config.connection_retries == 5
            assert config.retry_delay == 1
            assert config.timeout == 60
            assert config.request_retries == 5
            assert config.flood_sleep_threshold == 60

    def test_config_download_settings(self, test_env_vars, test_base_download_dir):
        """Test download settings are properly set."""
        test_env_vars["ROOT_DOWNLOAD_PATH"] = test_base_download_dir
        with patch.dict(os.environ, test_env_vars):
            config = Config()

            assert config.download_chunk_size == 8 * 1024 * 1024  # 8MB
            assert config.progress_update_interval == 5.0
            assert config.max_concurrent_downloads == 3
            assert config.notification_cooldown == 30

    def test_load_dotenv_called(self, test_env_vars, test_base_download_dir):
        """Test that load_dotenv is called during initialization."""
        test_env_vars["ROOT_DOWNLOAD_PATH"] = test_base_download_dir
        with patch.dict(os.environ, test_env_vars):
            with patch("src.core.config.load_dotenv") as mock_load_dotenv:
                Config()
                mock_load_dotenv.assert_called_once()

    def test_config_allowed_users_whitespace_handling(self, test_env_vars, test_base_download_dir):
        """Test that whitespace in allowed users is handled correctly."""
        test_env_vars["ALLOWED_USERS"] = " 123456 , 789012 , 345678 "
        test_env_vars["ROOT_DOWNLOAD_PATH"] = test_base_download_dir
        with patch.dict(os.environ, test_env_vars):
            config = Config()
            assert config.allowed_users == {"123456", "789012", "345678"}

    def test_config_zero_api_id(self, test_env_vars, test_base_download_dir):
        """Test configuration with zero API_ID."""
        test_env_vars["API_ID"] = "0"
        test_env_vars["ROOT_DOWNLOAD_PATH"] = test_base_download_dir
        with patch.dict(os.environ, test_env_vars):
            config = Config()
            assert config.api_id == 0

    def test_config_negative_api_id(self, test_env_vars, test_base_download_dir):
        """Test configuration with negative API_ID."""
        test_env_vars["API_ID"] = "-12345"
        test_env_vars["ROOT_DOWNLOAD_PATH"] = test_base_download_dir
        with patch.dict(os.environ, test_env_vars):
            config = Config()
            assert config.api_id == -12345


@pytest.fixture
def test_env_vars():
    """Fixture providing test environment variables."""
    return {
        "API_ID": "12345",
        "API_HASH": "test_hash_123456789",
        "BOT_TOKEN": "test_bot_token_123456789",
        "ALLOWED_USERS": "123456,789012,345678",
    }

@pytest.fixture
def test_base_download_dir(temp_dir):
    """Fixture providing test base download directory."""
    base_dir = os.path.join(temp_dir, "downloads")
    os.makedirs(base_dir, exist_ok=True)
    return base_dir
