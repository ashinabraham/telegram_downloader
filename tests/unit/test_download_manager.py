"""
Unit tests for the download manager module.
"""

import pytest
import time
from unittest.mock import Mock, AsyncMock, patch
from src.downloads.download_manager import DownloadTask, DownloadManager


class TestDownloadTask:
    """Test cases for the DownloadTask class."""

    def test_download_task_initialization(self):
        """Test DownloadTask initialization."""
        file_message = Mock()
        task = DownloadTask("123456", file_message, "/test/path/file.txt")
        
        assert task.user_id == "123456"
        assert task.file_message == file_message
        assert task.save_path == "/test/path/file.txt"
        assert task.progress_message is None
        assert task.start_time > 0
        assert task.downloaded_bytes == 0
        assert task.total_bytes == 0
        assert task.status == "queued"
        assert task.error is None
        assert task.last_progress_update == 0

    def test_download_task_with_progress_message(self):
        """Test DownloadTask initialization with progress message."""
        file_message = Mock()
        progress_message = Mock()
        task = DownloadTask("123456", file_message, "/test/path/file.txt", progress_message)
        
        assert task.progress_message == progress_message

    def test_download_task_thread_safety(self):
        """Test that DownloadTask has thread safety with progress_lock."""
        file_message = Mock()
        task = DownloadTask("123456", file_message, "/test/path/file.txt")
        
        assert hasattr(task, 'progress_lock')
        assert task.progress_lock is not None


class TestDownloadManager:
    """Test cases for the DownloadManager class."""

    def test_download_manager_initialization(self):
        """Test DownloadManager initialization."""
        manager = DownloadManager()
        
        assert manager.download_queue == {}
        assert manager.download_progress == {}
        assert manager.notification_cooldowns == {}
        assert manager.download_executor is not None

    @pytest.mark.asyncio
    async def test_queue_download_new_user(self):
        """Test queuing download for a new user."""
        manager = DownloadManager()
        file_message = Mock()
        
        task = await manager.queue_download("123456", file_message, "/test/path/file.txt")
        
        assert task.user_id == "123456"
        assert task.file_message == file_message
        assert task.save_path == "/test/path/file.txt"
        assert task.status == "queued"
        assert "123456" in manager.download_queue
        assert len(manager.download_queue["123456"]) == 1

    @pytest.mark.asyncio
    async def test_queue_download_existing_user(self):
        """Test queuing download for an existing user."""
        manager = DownloadManager()
        file_message1 = Mock()
        file_message2 = Mock()
        
        task1 = await manager.queue_download("123456", file_message1, "/test/path/file1.txt")
        task2 = await manager.queue_download("123456", file_message2, "/test/path/file2.txt")
        
        assert len(manager.download_queue["123456"]) == 2
        assert task1 in manager.download_queue["123456"]
        assert task2 in manager.download_queue["123456"]

    @pytest.mark.asyncio
    async def test_get_user_downloads_existing_user(self):
        """Test getting downloads for an existing user."""
        manager = DownloadManager()
        file_message = Mock()
        
        await manager.queue_download("123456", file_message, "/test/path/file.txt")
        downloads = manager.get_user_downloads("123456")
        
        assert len(downloads) == 1
        assert downloads[0].user_id == "123456"

    def test_get_user_downloads_nonexistent_user(self):
        """Test getting downloads for a nonexistent user."""
        manager = DownloadManager()
        downloads = manager.get_user_downloads("nonexistent")
        
        assert downloads == []

    @pytest.mark.asyncio
    async def test_clear_completed_downloads_with_completed(self):
        """Test clearing completed downloads."""
        manager = DownloadManager()
        file_message1 = Mock()
        file_message2 = Mock()
        
        task1 = await manager.queue_download("123456", file_message1, "/test/path/file1.txt")
        task2 = await manager.queue_download("123456", file_message2, "/test/path/file2.txt")
        
        # Mark one task as completed
        task1.status = "completed"
        
        cleared_count = manager.clear_completed_downloads("123456")
        
        assert cleared_count == 1
        assert len(manager.download_queue["123456"]) == 1
        assert task2 in manager.download_queue["123456"]

    @pytest.mark.asyncio
    async def test_clear_completed_downloads_no_completed(self):
        """Test clearing completed downloads when none exist."""
        manager = DownloadManager()
        file_message = Mock()
        
        await manager.queue_download("123456", file_message, "/test/path/file.txt")
        cleared_count = manager.clear_completed_downloads("123456")
        
        assert cleared_count == 0
        assert len(manager.download_queue["123456"]) == 1

    def test_clear_completed_downloads_nonexistent_user(self):
        """Test clearing completed downloads for nonexistent user."""
        manager = DownloadManager()
        cleared_count = manager.clear_completed_downloads("nonexistent")
        
        assert cleared_count == 0

    @pytest.mark.asyncio
    async def test_retry_failed_downloads_with_failed(self):
        """Test retrying failed downloads."""
        manager = DownloadManager()
        file_message1 = Mock()
        file_message2 = Mock()
        
        task1 = await manager.queue_download("123456", file_message1, "/test/path/file1.txt")
        task2 = await manager.queue_download("123456", file_message2, "/test/path/file2.txt")
        
        # Mark tasks as failed
        task1.status = "failed"
        task2.status = "failed"
        task1.error = "Network error"
        task2.error = "Permission error"
        
        retry_count = manager.retry_failed_downloads("123456")
        
        assert retry_count == 2
        assert task1.status == "queued"
        assert task2.status == "queued"
        assert task1.error is None
        assert task2.error is None

    @pytest.mark.asyncio
    async def test_retry_failed_downloads_no_failed(self):
        """Test retrying failed downloads when none exist."""
        manager = DownloadManager()
        file_message = Mock()
        
        await manager.queue_download("123456", file_message, "/test/path/file.txt")
        retry_count = manager.retry_failed_downloads("123456")
        
        assert retry_count == 0

    def test_retry_failed_downloads_nonexistent_user(self):
        """Test retrying failed downloads for nonexistent user."""
        manager = DownloadManager()
        retry_count = manager.retry_failed_downloads("nonexistent")
        
        assert retry_count == 0

    @pytest.mark.asyncio
    @patch('src.bot.client.client')
    async def test_send_notification_management_command(self, mock_client):
        """Test sending notification for management command."""
        manager = DownloadManager()
        mock_client.send_message = AsyncMock()
        
        # Set up user state with chat_id - use the one from download_manager
        from src.downloads.download_manager import user_state
        user_state.set_chat_id("123456", 123456789)
        
        await manager.send_notification("123456", "Test message", is_management_command=True)
        
        mock_client.send_message.assert_called_once()

    @pytest.mark.asyncio
    @patch('src.bot.client.client')
    async def test_send_notification_rate_limited(self, mock_client):
        """Test that notifications are rate limited."""
        manager = DownloadManager()
        mock_client.send_message = AsyncMock()
        
        # Set up user state with chat_id - use the one from download_manager
        from src.downloads.download_manager import user_state
        user_state.set_chat_id("123456", 123456789)
        
        # Set up rate limiting
        manager.notification_cooldowns["123456"] = time.time()
        
        await manager.send_notification("123456", "Test message", is_management_command=False)
        
        # Should not call send_message due to rate limiting
        mock_client.send_message.assert_not_called()

    @pytest.mark.asyncio
    @patch('src.bot.client.client')
    async def test_send_notification_no_chat_id(self, mock_client):
        """Test sending notification when no chat_id is available."""
        manager = DownloadManager()
        mock_client.send_message = AsyncMock()
        
        # Clear user state to ensure no chat_id is set
        from src.downloads.download_manager import user_state
        user_state.clear_user_state("123456")
        
        await manager.send_notification("123456", "Test message", is_management_command=True)
        
        # Should not call send_message when no chat_id
        mock_client.send_message.assert_not_called()

    @pytest.mark.asyncio
    @patch('src.bot.client.client')
    async def test_send_notification_exception_handling(self, mock_client):
        """Test exception handling in send_notification."""
        manager = DownloadManager()
        mock_client.send_message.side_effect = Exception("Network error")
        
        # Set up user state with chat_id - use the one from download_manager
        from src.downloads.download_manager import user_state
        user_state.set_chat_id("123456", 123456789)
        
        # Should not raise exception
        await manager.send_notification("123456", "Test message", is_management_command=True)

    @pytest.mark.asyncio
    @patch('src.bot.client.client')
    async def test_update_progress_message_success(self, mock_client):
        """Test successful progress message update."""
        manager = DownloadManager()
        task = DownloadTask("123456", Mock(), "/test/path/file.txt")
        task.progress_message = Mock()
        task.progress_message.edit = AsyncMock()
        
        await manager.update_progress_message(task, "Progress: 50%")
        
        task.progress_message.edit.assert_called_once_with("Progress: 50%")

    @pytest.mark.asyncio
    @patch('src.bot.client.client')
    async def test_update_progress_message_message_not_modified(self, mock_client):
        """Test progress message update with MessageNotModifiedError."""
        from telethon.errors import MessageNotModifiedError
        
        manager = DownloadManager()
        task = DownloadTask("123456", Mock(), "/test/path/file.txt")
        task.progress_message = Mock()
        task.progress_message.edit = AsyncMock(side_effect=MessageNotModifiedError(request=Mock()))
        
        # Should not raise exception
        await manager.update_progress_message(task, "Progress: 50%")

    @pytest.mark.asyncio
    @patch('src.bot.client.client')
    async def test_update_progress_message_rate_limit(self, mock_client):
        """Test progress message update with rate limit error."""
        manager = DownloadManager()
        task = DownloadTask("123456", Mock(), "/test/path/file.txt")
        task.progress_message = Mock()
        task.progress_message.edit = AsyncMock(side_effect=Exception("wait of 30 seconds is required"))
        
        # Should not raise exception
        await manager.update_progress_message(task, "Progress: 50%")

    @pytest.mark.asyncio
    @patch('src.bot.client.client')
    async def test_update_progress_message_no_progress_message(self, mock_client):
        """Test progress message update when no progress message exists."""
        manager = DownloadManager()
        task = DownloadTask("123456", Mock(), "/test/path/file.txt")
        task.progress_message = None
        
        # Should not raise exception
        await manager.update_progress_message(task, "Progress: 50%")

    @pytest.mark.asyncio
    @patch('src.bot.client.client')
    async def test_update_progress_message_throttling(self, mock_client):
        """Test that progress message updates are throttled."""
        manager = DownloadManager()
        task = DownloadTask("123456", Mock(), "/test/path/file.txt")
        task.progress_message = Mock()
        task.progress_message.edit = AsyncMock()
        task.last_progress_update = time.time()
        
        await manager.update_progress_message(task, "Progress: 50%")
        
        # Should not call edit due to throttling
        task.progress_message.edit.assert_not_called()

    @pytest.mark.asyncio
    @patch('src.bot.client.client')
    async def test_download_with_progress_success(self, mock_client):
        """Test successful download with progress."""
        manager = DownloadManager()
        file_message = Mock()
        file_message.media.document.size = 1024000
        
        task = DownloadTask("123456", file_message, "/test/path/file.txt")
        mock_client.send_message = AsyncMock(return_value=Mock())
        mock_client.download_media = AsyncMock(return_value="/test/path/file.txt")
        
        # Set up user state with chat_id - use the one from download_manager
        from src.downloads.download_manager import user_state
        user_state.set_chat_id("123456", 123456789)
        
        await manager.download_with_progress(task)
        
        assert task.status == "completed"
        assert task.total_bytes == 1024000

    @pytest.mark.asyncio
    @patch('src.bot.client.client')
    async def test_download_with_progress_failure(self, mock_client):
        """Test download failure."""
        manager = DownloadManager()
        file_message = Mock()
        file_message.media.document.size = 1024000
        
        task = DownloadTask("123456", file_message, "/test/path/file.txt")
        mock_client.send_message = AsyncMock(return_value=Mock())
        mock_client.download_media = AsyncMock(return_value=None)
        
        # Set up user state with chat_id - use the one from download_manager
        from src.downloads.download_manager import user_state
        user_state.set_chat_id("123456", 123456789)
        
        await manager.download_with_progress(task)
        
        assert task.status == "failed"
        assert task.error == "Download failed"

    @pytest.mark.asyncio
    @patch('src.bot.client.client')
    async def test_download_with_progress_exception(self, mock_client):
        """Test download with exception."""
        manager = DownloadManager()
        file_message = Mock()
        file_message.media.document.size = 1024000
        
        task = DownloadTask("123456", file_message, "/test/path/file.txt")
        mock_client.send_message = AsyncMock(return_value=Mock())
        mock_client.download_media = AsyncMock(side_effect=Exception("Network error"))
        
        # Set up user state with chat_id - use the one from download_manager
        from src.downloads.download_manager import user_state
        user_state.set_chat_id("123456", 123456789)
        
        await manager.download_with_progress(task)
        
        assert task.status == "failed"
        assert task.error == "Network error"

    @pytest.mark.asyncio
    @patch('src.bot.client.client')
    async def test_download_with_progress_no_chat_id(self, mock_client):
        """Test download when no chat_id is available."""
        manager = DownloadManager()
        file_message = Mock()
        file_message.media.document.size = 1024000
        
        task = DownloadTask("123456", file_message, "/test/path/file.txt")
        
        await manager.download_with_progress(task)
        
        # Should handle gracefully without chat_id
        assert task.status == "failed"

    @pytest.mark.asyncio
    async def test_download_manager_concurrent_downloads(self):
        """Test that download manager supports concurrent downloads."""
        manager = DownloadManager()
        
        # Should be able to queue multiple downloads
        file_messages = [Mock() for _ in range(5)]
        
        for i, file_message in enumerate(file_messages):
            task = await manager.queue_download(f"user{i}", file_message, f"/test/path/file{i}.txt")
            assert task.status == "queued"

    def test_download_task_progress_tracking(self):
        """Test that download task properly tracks progress."""
        task = DownloadTask("123456", Mock(), "/test/path/file.txt")
        
        # Simulate progress updates
        task.downloaded_bytes = 512000
        task.total_bytes = 1024000
        
        progress_percent = (task.downloaded_bytes / task.total_bytes) * 100
        assert progress_percent == 50.0

    def test_download_task_status_transitions(self):
        """Test download task status transitions."""
        task = DownloadTask("123456", Mock(), "/test/path/file.txt")
        
        assert task.status == "queued"
        
        task.status = "downloading"
        assert task.status == "downloading"
        
        task.status = "completed"
        assert task.status == "completed"
        
        task.status = "failed"
        assert task.status == "failed" 