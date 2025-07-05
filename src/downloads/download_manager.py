"""
Download manager module for the Telegram File Downloader Bot.
Handles file downloads, progress tracking, and queue management.
"""

import os
import asyncio
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional

from ..core.config import get_config
from ..core.user_state import user_state

logger = logging.getLogger(__name__)


# Get configuration
config = get_config()


class DownloadTask:
    """Represents a download task with progress tracking."""

    def __init__(
        self, user_id: str, file_message, save_path: str
    ):
        self.user_id = user_id
        self.file_message = file_message
        self.save_path = save_path
        self.start_time = time.time()
        self.downloaded_bytes = 0
        self.total_bytes = 0
        self.status = "queued"  # queued, downloading, completed, failed
        self.error: Optional[str] = None
        self.progress_lock = threading.Lock()


class DownloadManager:
    """Manages download queue and progress tracking."""

    def __init__(self):
        self.download_queue: Dict[str, List[DownloadTask]] = {}
        self.download_progress: Dict[str, dict] = {}
        self.download_executor = ThreadPoolExecutor(
            max_workers=config.max_concurrent_downloads
        )

        # Rate limiting for notifications
        self.notification_cooldowns: Dict[str, float] = {}

    async def send_rate_limited_notification(self, user_id: str, message: str) -> None:
        """Send a notification to user with rate limiting to prevent flood wait."""
        try:
            current_time = time.time()
            last_notification = self.notification_cooldowns.get(user_id, 0)

            # Check if enough time has passed since last notification
            if current_time - last_notification < config.notification_cooldown:
                logger.info(f"Rate limiting notification for user {user_id}")
                return

            chat_id = user_state.get_chat_id(user_id)
            if chat_id:
                from ..bot.client import client

                await client.send_message(chat_id, message)
                self.notification_cooldowns[user_id] = current_time
                logger.info(f"Sent notification to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send notification to user {user_id}: {e}")

    async def send_notification(
        self, user_id: str, message: str, is_management_command: bool = False
    ) -> None:
        """Send a notification to user with optional rate limiting."""
        try:
            # Skip rate limiting for management commands
            if is_management_command:
                chat_id = user_state.get_chat_id(user_id)
                if chat_id:
                    from ..bot.client import client

                    await client.send_message(chat_id, message)
                    logger.info(f"Sent management notification to user {user_id}")
            else:
                # Use rate limiting for regular notifications
                await self.send_rate_limited_notification(user_id, message)
        except Exception as e:
            logger.error(f"Failed to send notification to user {user_id}: {e}")

    async def download_with_progress(self, task: DownloadTask) -> None:
        """Download file with simple notification and .part extension handling."""
        try:
            task.status = "downloading"

            # Get file size
            if (
                hasattr(task.file_message.media, "document")
                and task.file_message.media.document
            ):
                task.total_bytes = task.file_message.media.document.size
            else:
                task.total_bytes = 0

            # Get chat_id from user_states
            chat_id = user_state.get_chat_id(task.user_id)
            logger.info(f"Download task for user {task.user_id}, chat_id: {chat_id}")
            if not chat_id:
                logger.error(f"No chat_id found for user {task.user_id}")
                # Try to get chat_id from the file message
                try:
                    chat_id = task.file_message.chat_id
                    logger.info(f"Using chat_id from file message: {chat_id}")
                except Exception as e:
                    logger.error(f"Could not get chat_id from file message: {e}")
                    return

            # Send simple downloading notification
            filename = os.path.basename(task.save_path)
            file_size_mb = task.total_bytes / (1024 * 1024) if task.total_bytes > 0 else 0

            notification_text = f"📥 **Download Started!**\n\n📁 **File:** {filename}\n📊 **Size:** {file_size_mb:.1f} MB\n\nUse `/status` to check download progress."

            from ..bot.client import client
            await client.send_message(chat_id, notification_text)

            # Download to .part file
            part_path = task.save_path + ".part"

            # Simple progress callback that only updates internal state
            def progress_callback(received_bytes, total_bytes):
                with task.progress_lock:
                    task.downloaded_bytes = received_bytes
                    task.total_bytes = total_bytes

            # Download with optimized settings
            downloaded_file = await client.download_media(
                task.file_message.media,
                part_path,
                progress_callback=progress_callback,
            )

            if downloaded_file:
                # Rename .part file to final filename
                try:
                    os.rename(part_path, task.save_path)
                    final_path = task.save_path
                except Exception as e:
                    logger.error(f"Failed to rename .part file: {e}")
                    final_path = part_path
                task.status = "completed"
                total_time = time.time() - task.start_time
                avg_speed = task.total_bytes / total_time if total_time > 0 else 0

                # Send completion notification to user
                try:
                    chat_id = user_state.get_chat_id(task.user_id)
                    if chat_id:
                        notification_text = (
                            f"🎉 **Download Complete!**\n\n"
                            f"📁 **File:** {filename}\n"
                            f"📂 **Location:** {final_path}\n"
                            f"⏱️ **Time:** {total_time:.1f} seconds\n"
                            f"🚀 **Avg Speed:** {avg_speed / (1024 * 1024):.1f} MB/s\n"
                            f"📊 **Size:** {file_size_mb:.1f} MB"
                        )
                        await self.send_notification(task.user_id, notification_text)
                except Exception as e:
                    logger.error(f"Failed to send completion notification: {e}")

                logger.info(
                    f"Download completed: {final_path} in {total_time:.1f}s"
                )
            else:
                task.status = "failed"
                task.error = "Download failed"

                # Send failure notification to user
                try:
                    chat_id = user_state.get_chat_id(task.user_id)
                    if chat_id:
                        notification_text = (
                            f"❌ **Download Failed!**\n\n"
                            f"📁 **File:** {filename}\n"
                            f"🔍 **Error:** Download failed\n\n"
                            f"Use /status to retry failed downloads."
                        )
                        await self.send_notification(task.user_id, notification_text)
                except Exception as e:
                    logger.error(f"Failed to send failure notification: {e}")

        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            logger.error(f"Download failed for {task.save_path}: {e}")

            # Send error notification to user
            try:
                chat_id = user_state.get_chat_id(task.user_id)
                if chat_id:
                    notification_text = (
                        f"❌ **Download Error!**\n\n"
                        f"📁 **File:** {os.path.basename(task.save_path)}\n"
                        f"🔍 **Error:** {str(e)}\n\n"
                        f"Use /status to retry failed downloads."
                    )
                    await self.send_notification(task.user_id, notification_text)
            except Exception as notification_error:
                logger.error(f"Failed to send error notification: {notification_error}")

    async def queue_download(
        self, user_id: str, file_message, save_path: str
    ) -> DownloadTask:
        """Add download to queue and start if possible with optimized concurrency."""
        logger.info(f"Queueing download for user {user_id} to path: {save_path}")
        logger.info(
            f"User state chat_id for {user_id}: {user_state.get_chat_id(user_id)}"
        )

        task = DownloadTask(user_id, file_message, save_path)
        self.download_queue[user_id] = self.download_queue.get(user_id, []) + [task]

        # Start download in background with optimized executor
        asyncio.create_task(self.download_with_progress(task))

        return task

    def get_user_downloads(self, user_id: str) -> List[DownloadTask]:
        """Get all downloads for a user."""
        return self.download_queue.get(user_id, [])

    def clear_completed_downloads(self, user_id: str) -> int:
        """Remove completed downloads from queue and return count of cleared downloads."""
        user_downloads = self.download_queue.get(user_id, [])
        if user_downloads:
            # Keep only non-completed downloads
            original_count = len(user_downloads)
            self.download_queue[user_id] = [
                task for task in user_downloads if task.status != "completed"
            ]
            cleared_count = original_count - len(self.download_queue[user_id])
            return cleared_count
        return 0

    def retry_failed_downloads(self, user_id: str) -> int:
        """Retry all failed downloads for a user and return count of retried downloads."""
        user_downloads = self.download_queue.get(user_id, [])
        failed_tasks = [task for task in user_downloads if task.status == "failed"]

        retry_count = 0
        for task in failed_tasks:
            # Reset task status and restart download
            task.status = "queued"
            task.downloaded_bytes = 0
            task.error = None
            task.start_time = time.time()
            retry_count += 1
            # Restart the download
            asyncio.create_task(self.download_with_progress(task))

        return retry_count


# Global download manager instance
download_manager = DownloadManager()
