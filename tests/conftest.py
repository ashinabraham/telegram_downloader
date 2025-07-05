"""
Pytest configuration and shared fixtures for Telegram bot tests.
"""

import pytest
import os
import tempfile
import shutil
import importlib
from unittest.mock import Mock, AsyncMock, patch
from telethon import TelegramClient
from telethon.tl.types import User, Document, DocumentAttributeFilename

# Add src to path for imports
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def test_base_download_dir(temp_dir):
    """Create a test-specific base download directory."""
    # Create a subdirectory within temp_dir to use as base download dir
    base_dir = os.path.join(temp_dir, "downloads")
    os.makedirs(base_dir, exist_ok=True)
    return base_dir


@pytest.fixture(autouse=True)
def patch_path_manager_env(test_base_download_dir):
    # Patch env and reload path_utils before each test
    with patch.dict(os.environ, {"ROOT_DOWNLOAD_PATH": test_base_download_dir}):
        import src.utils.path_utils

        importlib.reload(src.utils.path_utils)
        yield


@pytest.fixture
def mock_config(test_base_download_dir):
    """Mock configuration for testing with test-specific base download directory."""
    with patch.dict(
        os.environ,
        {
            "API_ID": "12345",
            "API_HASH": "test_hash",
            "BOT_TOKEN": "test_token",
            "ALLOWED_USERS": "123456,789012",
            "ROOT_DOWNLOAD_PATH": test_base_download_dir,
        },
    ):
        from src.core.config import Config

        return Config()


@pytest.fixture
def mock_user_state():
    """Mock user state for testing."""
    from src.core.user_state import UserState

    return UserState()


@pytest.fixture
def mock_path_manager(test_base_download_dir):
    """Mock path manager for testing with test-specific base directory."""
    with patch.dict(os.environ, {"ROOT_DOWNLOAD_PATH": test_base_download_dir}):
        from src.utils.path_utils import PathManager

        return PathManager()


@pytest.fixture
def mock_download_manager():
    """Mock download manager for testing."""
    from src.download_manager.manager import DownloadManager

    return DownloadManager()


@pytest.fixture
def mock_telegram_client():
    """Mock Telegram client for testing."""
    client = Mock(spec=TelegramClient)
    client.send_message = AsyncMock()
    client.send_code_request = AsyncMock()
    client.sign_in = AsyncMock()
    client.get_me = AsyncMock()
    client.download_media = AsyncMock()
    return client


@pytest.fixture
def mock_user():
    """Mock Telegram user."""
    user = Mock(spec=User)
    user.id = 123456
    user.username = "test_user"
    user.first_name = "Test"
    user.last_name = "User"
    return user


@pytest.fixture
def mock_document():
    """Mock Telegram document."""
    document = Mock(spec=Document)
    document.id = 123456789
    document.access_hash = 987654321
    document.file_reference = b"test_reference"
    document.date = 1640995200  # 2022-01-01
    document.mime_type = "application/pdf"
    document.size = 1024000  # 1MB
    document.dc_id = 2
    document.attributes = [DocumentAttributeFilename(file_name="test_file.pdf")]
    return document


@pytest.fixture
def mock_file_message():
    """Mock file message for testing."""
    message = Mock()
    message.media = Mock()
    message.media.document = Mock()
    message.media.document.size = 1024000
    message.media.document.attributes = [Mock(file_name="test_file.pdf")]
    return message


@pytest.fixture
def mock_event():
    """Mock Telegram event for testing."""
    event = Mock()
    event.sender_id = 123456
    event.chat_id = 123456
    event.raw_text = "test message"
    event.respond = AsyncMock()
    event.edit = AsyncMock()
    event.answer = AsyncMock()
    event.data = b"test_callback"
    event.message = Mock()
    event.message.media = None
    return event


@pytest.fixture
def sample_directory_structure(test_base_download_dir):
    """Create a sample directory structure for testing within the base download directory."""
    # Create test directories within the base download directory
    os.makedirs(os.path.join(test_base_download_dir, "folder1"), exist_ok=True)
    os.makedirs(os.path.join(test_base_download_dir, "folder2"), exist_ok=True)
    os.makedirs(
        os.path.join(test_base_download_dir, "folder1", "subfolder"), exist_ok=True
    )

    # Create test files
    with open(os.path.join(test_base_download_dir, "test_file1.txt"), "w") as f:
        f.write("test content 1")

    with open(
        os.path.join(test_base_download_dir, "folder1", "test_file2.txt"), "w"
    ) as f:
        f.write("test content 2")

    return test_base_download_dir


@pytest.fixture
def test_env_vars(test_base_download_dir):
    """Test environment variables with test-specific base download directory."""
    return {
        "API_ID": "12345",
        "API_HASH": "test_hash_123456789",
        "BOT_TOKEN": "test_bot_token_123456789",
        "ALLOWED_USERS": "123456,789012,345678",
        "ROOT_DOWNLOAD_PATH": test_base_download_dir,
    }


@pytest.fixture
def mock_download_task(test_base_download_dir):
    """Mock download task for testing with test-specific base directory."""
    from src.download_manager.manager import DownloadTask

    task = DownloadTask(
        user_id="123456",
        file_message=Mock(),
        save_path=os.path.join(test_base_download_dir, "file.pdf"),
    )
    task.downloaded_bytes = 512000  # 50% of 1MB
    task.total_bytes = 1024000
    task.status = "downloading"
    task.start_time = 1640995200.0
    return task


@pytest.fixture
def setup_bot_components(test_base_download_dir):
    """Set up all bot components for integration testing."""
    with patch.dict(
        os.environ,
        {
            "API_ID": "12345",
            "API_HASH": "test_hash",
            "BOT_TOKEN": "test_token",
            "ALLOWED_USERS": "123456,789012",
            "ROOT_DOWNLOAD_PATH": test_base_download_dir,
        },
    ):
        from src.core.config import Config
        from src.core.user_state import UserState
        from src.download_manager.manager import DownloadManager
        from src.utils.path_utils import PathManager

        config = Config()
        user_state = UserState()
        download_manager = DownloadManager()
        path_manager = PathManager()

        return {
            "config": config,
            "user_state": user_state,
            "download_manager": download_manager,
            "path_manager": path_manager,
        }
