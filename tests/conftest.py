"""
Pytest configuration and shared fixtures for Telegram bot tests.
"""

import pytest
import os
import tempfile
import shutil
from unittest.mock import Mock, AsyncMock, patch
from telethon import TelegramClient
from telethon.tl.types import User, Document, DocumentAttributeFilename

# Add src to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    with patch.dict(os.environ, {
        'API_ID': '12345',
        'API_HASH': 'test_hash',
        'BOT_TOKEN': 'test_token',
        'ALLOWED_USERS': '123456,789012'
    }):
        from src.core.config import Config
        return Config()

@pytest.fixture
def mock_user_state():
    """Mock user state for testing."""
    from src.core.user_state import UserState
    return UserState()

@pytest.fixture
def mock_path_manager():
    """Mock path manager for testing."""
    from src.utils.path_utils import PathManager
    return PathManager()

@pytest.fixture
def mock_download_manager():
    """Mock download manager for testing."""
    from src.downloads.download_manager import DownloadManager
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
    document.file_reference = b'test_reference'
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
def sample_directory_structure(temp_dir):
    """Create a sample directory structure for testing."""
    # Create test directories
    os.makedirs(os.path.join(temp_dir, "folder1"), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, "folder2"), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, "folder1", "subfolder"), exist_ok=True)
    
    # Create test files
    with open(os.path.join(temp_dir, "test_file1.txt"), "w") as f:
        f.write("test content 1")
    
    with open(os.path.join(temp_dir, "folder1", "test_file2.txt"), "w") as f:
        f.write("test content 2")
    
    return temp_dir

@pytest.fixture
def test_env_vars():
    """Test environment variables."""
    return {
        'API_ID': '12345',
        'API_HASH': 'test_hash_123456789',
        'BOT_TOKEN': 'test_bot_token_123456789',
        'ALLOWED_USERS': '123456,789012,345678'
    }

@pytest.fixture
def mock_download_task():
    """Mock download task for testing."""
    from src.downloads.download_manager import DownloadTask
    
    task = DownloadTask(
        user_id="123456",
        file_message=Mock(),
        save_path="/test/path/file.pdf"
    )
    task.downloaded_bytes = 512000  # 50% of 1MB
    task.total_bytes = 1024000
    task.status = "downloading"
    task.start_time = 1640995200.0
    return task 