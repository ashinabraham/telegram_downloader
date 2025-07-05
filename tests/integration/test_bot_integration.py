"""
Integration tests for the Telegram bot functionality.
"""

import pytest
import pytest_asyncio
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from telethon import TelegramClient
from telethon.tl.types import User, Document, DocumentAttributeFilename
import os

from src.core.config import Config
from src.core.user_state import UserState
from src.bot.client import client
from src.download_manager import DownloadManager
from src.utils.path_utils import PathManager


@pytest.mark.integration
class TestBotIntegration:
    """Integration tests for bot functionality."""

    @pytest_asyncio.fixture
    async def setup_bot_components(self):
        """Set up bot components for integration testing."""
        # Mock configuration
        with patch.dict(
            "os.environ",
            {
                "API_ID": "12345",
                "API_HASH": "test_hash",
                "BOT_TOKEN": "test_token",
                "ALLOWED_USERS": "123456,789012",
            },
        ):
            config = Config()
            user_state = UserState()
            download_manager = DownloadManager()
            path_manager = PathManager()

            yield {
                "config": config,
                "user_state": user_state,
                "download_manager": download_manager,
                "path_manager": path_manager,
            }

    @pytest.mark.asyncio
    async def test_user_login_flow(self, setup_bot_components):
        """Test complete user login flow."""
        components = setup_bot_components
        user_state = components["user_state"]
        config = components["config"]

        user_id = "123456"

        # Test user authorization
        assert user_state.is_authorized(user_id, config.allowed_users) is True

        # Test state transitions
        user_state.set_state(user_id, "awaiting_phone", chat_id=789012)
        assert user_state.get_state(user_id) == "awaiting_phone"
        assert user_state.get_chat_id(user_id) == 789012

        user_state.set_state(user_id, "awaiting_code", phone="+1234567890")
        assert user_state.get_state(user_id) == "awaiting_code"
        assert user_state.get_user_data(user_id, "phone") == "+1234567890"

        user_state.set_state(user_id, "logged_in")
        assert user_state.get_state(user_id) == "logged_in"
        assert user_state.is_logged_in(user_id) is True

    @pytest.mark.asyncio
    async def test_file_download_workflow(self, setup_bot_components, test_base_download_dir):
        """Test complete file download workflow."""
        components = setup_bot_components
        user_state = components["user_state"]
        download_manager = components["download_manager"]
        path_manager = components["path_manager"]

        user_id = "123456"

        # Set up user as logged in
        user_state.set_state(user_id, "logged_in", chat_id=789012)

        # Create mock file message
        file_message = Mock()
        file_message.media = Mock()
        file_message.media.document = Mock()
        file_message.media.document.size = 1024000  # 1MB
        file_message.media.document.attributes = [Mock(file_name="test_file.pdf")]

        # Test directory selection (use base dir)
        save_dir = test_base_download_dir
        assert path_manager.ensure_directory_exists(save_dir) is True

        # Test download
        save_path = path_manager.join_paths(save_dir, "test_file.pdf")
        task = await download_manager.queue_download(user_id, file_message, save_path)
        assert task.user_id == user_id
        assert task.save_path == save_path
        assert task.status == "queued"

    @pytest.mark.asyncio
    async def test_directory_navigation_workflow(self, setup_bot_components, test_base_download_dir):
        """Test directory navigation workflow."""
        components = setup_bot_components
        path_manager = components["path_manager"]

        # Test path encoding/decoding
        test_path = "/test/path/with/many/components"
        encoded = path_manager.encode_path(test_path)
        decoded = path_manager.decode_path(encoded)
        assert decoded == test_path

        # Test directory options (use base dir)
        os.makedirs(os.path.join(test_base_download_dir, "folder1"), exist_ok=True)
        os.makedirs(os.path.join(test_base_download_dir, "folder2"), exist_ok=True)
        options = await path_manager.get_directory_options(test_base_download_dir)
        assert len(options) >= 2  # Should have folder1 and folder2

    @pytest.mark.asyncio
    async def test_download_manager_operations(self, setup_bot_components, test_base_download_dir):
        """Test download manager operations."""
        components = setup_bot_components
        download_manager = components["download_manager"]

        user_id = "123456"

        # Create multiple download tasks
        file_messages = [Mock() for _ in range(3)]
        for i, file_message in enumerate(file_messages):
            file_message.media = Mock()
            file_message.media.document = Mock()
            file_message.media.document.size = 1024000

            task = await download_manager.queue_download(
                user_id, file_message, f"/test/path/file{i}.txt"
            )

            # Mark some as completed, some as failed
            if i == 0:
                task.status = "completed"
            elif i == 1:
                task.status = "failed"
                task.error = "Network error"

        # Test clearing completed downloads
        cleared_count = download_manager.clear_completed_downloads(user_id)
        assert cleared_count == 1

        # Test retrying failed downloads
        retry_count = download_manager.retry_failed_downloads(user_id)
        assert retry_count == 1

        # Verify remaining downloads
        downloads = download_manager.get_user_downloads(user_id)
        assert len(downloads) == 2  # One queued, one retried

    @pytest.mark.asyncio
    async def test_path_encoding_workflow(self, setup_bot_components):
        """Test path encoding workflow for long paths."""
        components = setup_bot_components
        path_manager = components["path_manager"]

        # Test multiple path encodings
        paths = [
            "/home/user/documents",
            "/home/user/downloads",
            "/var/log",
            "/home/user/documents",  # Duplicate
            "/tmp/test",
        ]

        encodings = []
        for path in paths:
            encoded = path_manager.encode_path(path)
            encodings.append(encoded)

        # Check that duplicates get same encoding
        assert encodings[0] == encodings[3]  # Both "/home/user/documents"

        # Check that different paths get different encodings
        assert encodings[0] != encodings[1]
        assert encodings[1] != encodings[2]

        # Test decoding
        for i, path in enumerate(paths):
            decoded = path_manager.decode_path(encodings[i])
            assert decoded == path

    @pytest.mark.asyncio
    async def test_user_state_persistence(self, setup_bot_components):
        """Test user state persistence across operations."""
        components = setup_bot_components
        user_state = components["user_state"]

        user_id = "123456"

        # Test state persistence
        user_state.set_state(user_id, "awaiting_phone", chat_id=789012)
        assert user_state.get_state(user_id) == "awaiting_phone"

        # Simulate some operations
        user_state.set_user_data(user_id, "temp_data", "test_value")
        assert user_state.get_user_data(user_id, "temp_data") == "test_value"

        # State should persist
        assert user_state.get_state(user_id) == "awaiting_phone"
        assert user_state.get_chat_id(user_id) == 789012

    @pytest.mark.asyncio
    async def test_error_handling_integration(self, setup_bot_components):
        """Test error handling in integration scenarios."""
        components = setup_bot_components
        user_state = components["user_state"]
        download_manager = components["download_manager"]

        user_id = "123456"

        # Test handling of invalid states
        user_state.set_state(user_id, "invalid_state")
        assert user_state.get_state(user_id) == "invalid_state"

        # Test handling of missing user data
        assert user_state.get_user_data(user_id, "nonexistent") is None
        assert (
            user_state.get_user_data(user_id, "nonexistent", default="default")
            == "default"
        )

        # Test handling of empty download queue
        downloads = download_manager.get_user_downloads(user_id)
        assert downloads == []

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, setup_bot_components):
        """Test concurrent operations."""
        components = setup_bot_components
        download_manager = components["download_manager"]

        user_id = "123456"

        # Create multiple concurrent downloads
        file_messages = [Mock() for _ in range(5)]
        for i, file_message in enumerate(file_messages):
            file_message.media = Mock()
            file_message.media.document = Mock()
            file_message.media.document.size = 1024000

            task = await download_manager.queue_download(
                f"user{i}", file_message, f"/test/path/file{i}.txt"
            )
            assert task.status == "queued"

        # Verify all downloads are queued
        for i in range(5):
            downloads = download_manager.get_user_downloads(f"user{i}")
            assert len(downloads) == 1
            assert downloads[0].status == "queued"

    @pytest.mark.asyncio
    async def test_filename_sanitization_workflow(self, setup_bot_components, test_base_download_dir):
        """Test filename sanitization for files with spaces, symbols, and colons."""
        components = setup_bot_components
        user_state = components["user_state"]
        download_manager = components["download_manager"]
        path_manager = components["path_manager"]

        user_id = "123456"

        # Set up user as logged in
        user_state.set_state(user_id, "logged_in", chat_id=789012)

        # Test various problematic filenames
        problematic_filenames = [
            "file with spaces.txt",
            "file:with:colons.pdf",
            "file/with/slashes.doc",
            "file\\with\\backslashes.xlsx",
            "file with symbols!@#$%^&*().zip",
            "file with unicode ñáéíóú.pdf",
            "file with multiple   spaces.txt",
            "file:with:multiple:colons:and:spaces.doc",
        ]

        for original_filename in problematic_filenames:
            # Create mock file message with problematic filename
            file_message = Mock()
            file_message.media = Mock()
            file_message.media.document = Mock()
            file_message.media.document.size = 1024000  # 1MB
            file_message.media.document.attributes = [Mock(file_name=original_filename)]

            # Store file message in user state (simulating file forward)
            user_state.set_user_data(user_id, "file_message", file_message)

            # Test that file_message can be retrieved
            retrieved_message = user_state.get_user_data(user_id, "file_message")
            assert retrieved_message == file_message

            # Test filename sanitization
            sanitized_filename = path_manager.sanitize_filename(original_filename)

            # Verify sanitization removes problematic characters
            assert "/" not in sanitized_filename
            assert "\\" not in sanitized_filename
            assert (
                sanitized_filename.strip() == sanitized_filename
            )  # No leading/trailing spaces

            # Test download with sanitized filename (use base dir)
            save_path = path_manager.join_paths(test_base_download_dir, sanitized_filename)
            task = await download_manager.queue_download(
                user_id, file_message, save_path
            )

            assert task.user_id == user_id
            assert task.save_path == save_path
            assert task.status == "queued"

            # Verify the path is valid (no problematic characters)
            assert "/" not in os.path.basename(save_path)
            assert "\\" not in os.path.basename(save_path)

            # Clear the download for next iteration
            download_manager.clear_completed_downloads(user_id)

        # Test user-provided filename with problematic characters
        user_provided_filename = "my file:with:colons and spaces!@#.txt"
        sanitized_user_filename = path_manager.sanitize_filename(user_provided_filename)

        # Verify user filename is also sanitized
        assert "/" not in sanitized_user_filename
        assert "\\" not in sanitized_user_filename
        assert sanitized_user_filename.strip() == sanitized_user_filename

        # Test that the sanitized filename can be used in a path (use base dir)
        test_save_path = path_manager.join_paths(test_base_download_dir, sanitized_user_filename)
        assert os.path.basename(test_save_path) == sanitized_user_filename
