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
from telethon.errors import MessageNotModifiedError

from ..core.config import get_config
from ..core.user_state import UserState

logger = logging.getLogger(__name__)

# Get configuration
config = get_config()

# Import the global user state instance
from ..core.user_state import user_state


class DownloadTask:
    """Represents a download task with progress tracking."""

    def __init__(
        self, user_id: str, file_message, save_path: str, progress_message=None
    ):
        self.user_id = user_id
        self.file_message = file_message
        self.save_path = save_path
        self.progress_message = progress_message
        self.start_time = time.time()
        self.downloaded_bytes = 0
        self.total_bytes = 0
        self.status = "queued"  # queued, downloading, completed, failed
        self.error: Optional[str] = None
        self.last_progress_update: float = 0.0
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

    async def update_progress_message(
        self, task: DownloadTask, progress_text: str
    ) -> None:
        """Update the progress message in Telegram with throttling and better error handling."""
        try:
            current_time = time.time()
            # Only update if enough time has passed since last update
            if (
                current_time - task.last_progress_update
                >= config.progress_update_interval
            ):
                if task.progress_message:
                    await task.progress_message.edit(progress_text)
                    task.last_progress_update = current_time
        except MessageNotModifiedError:
            # Message content is the same, ignore this error
            pass
        except Exception as e:
            error_msg = str(e)
            if "wait of" in error_msg and "seconds is required" in error_msg:
                # Rate limit error - extract wait time and log it
                logger.warning(
                    f"Rate limit hit for progress updates. Error: {error_msg}"
                )
                # Don't update last_progress_update to prevent immediate retry
            else:
                logger.error(f"Failed to update progress message: {e}")

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
        """Download file with optimized progress tracking."""
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

            # Create progress message
            progress_text = f"📥 Starting download...\nFile: {os.path.basename(task.save_path)}\nSize: {task.total_bytes / (1024 * 1024):.1f} MB"
            from ..bot.client import client

            task.progress_message = await client.send_message(chat_id, progress_text)

            # Optimized progress callback with throttling
            def progress_callback(received_bytes, total_bytes):
                with task.progress_lock:
                    task.downloaded_bytes = received_bytes
                    task.total_bytes = total_bytes

                    # Calculate progress
                    if total_bytes > 0:
                        progress_percent = (received_bytes / total_bytes) * 100
                        elapsed_time = time.time() - task.start_time
                        speed = received_bytes / elapsed_time if elapsed_time > 0 else 0

                        # Only update progress message periodically to reduce overhead
                        current_time = time.time()
                        if (
                            current_time - task.last_progress_update
                            >= config.progress_update_interval
                        ):
                            progress_text = (
                                f"📥 Downloading...\n"
                                f"File: {os.path.basename(task.save_path)}\n"
                                f"Progress: {progress_percent:.1f}%\n"
                                f"Speed: {speed / (1024 * 1024):.1f} MB/s\n"
                                f"Downloaded: {received_bytes / (1024 * 1024):.1f} MB / {total_bytes / (1024 * 1024):.1f} MB\n"
                                f"ETA: {((total_bytes - received_bytes) / speed / 60):.1f} min"
                                if speed > 0
                                else "Calculating..."
                            )

                            # Update progress message (non-blocking)
                            asyncio.create_task(
                                self.update_progress_message(task, progress_text)
                            )

            # Download with optimized settings
            downloaded_file = await client.download_media(
                task.file_message.media,
                task.save_path,
                progress_callback=progress_callback,
            )

            if downloaded_file:
                task.status = "completed"
                total_time = time.time() - task.start_time
                avg_speed = task.total_bytes / total_time if total_time > 0 else 0

                completion_text = (
                    f"✅ Download completed!\n"
                    f"File: {os.path.basename(task.save_path)}\n"
                    f"Path: {downloaded_file}\n"
                    f"Time: {total_time:.1f}s\n"
                    f"Avg Speed: {avg_speed / (1024 * 1024):.1f} MB/s"
                )
                await self.update_progress_message(task, completion_text)

                # Send completion notification to user
                try:
                    chat_id = user_state.get_chat_id(task.user_id)
                    if chat_id:
                        notification_text = (
                            f"🎉 **Download Complete!**\n\n"
                            f"📁 **File:** {os.path.basename(task.save_path)}\n"
                            f"📂 **Location:** {downloaded_file}\n"
                            f"⏱️ **Time:** {total_time:.1f} seconds\n"
                            f"🚀 **Avg Speed:** {avg_speed / (1024 * 1024):.1f} MB/s\n"
                            f"📊 **Size:** {task.total_bytes / (1024 * 1024):.1f} MB"
                        )
                        await self.send_notification(task.user_id, notification_text)
                except Exception as e:
                    logger.error(f"Failed to send completion notification: {e}")

                logger.info(
                    f"Download completed: {downloaded_file} in {total_time:.1f}s"
                )
            else:
                task.status = "failed"
                task.error = "Download failed"
                await self.update_progress_message(
                    task, f"❌ Download failed: {os.path.basename(task.save_path)}"
                )

                # Send failure notification to user
                try:
                    chat_id = user_state.get_chat_id(task.user_id)
                    if chat_id:
                        notification_text = (
                            f"❌ **Download Failed!**\n\n"
                            f"📁 **File:** {os.path.basename(task.save_path)}\n"
                            f"🔍 **Error:** Download failed\n\n"
                            f"Use /status to retry failed downloads."
                        )
                        await self.send_notification(task.user_id, notification_text)
                except Exception as e:
                    logger.error(f"Failed to send failure notification: {e}")

                logger.error("Download failed")

        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            error_text = f"❌ Download error: {os.path.basename(task.save_path)}\nError: {str(e)}"
            await self.update_progress_message(task, error_text)

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
            except Exception as notify_e:
                logger.error(f"Failed to send error notification: {notify_e}")

            logger.error(f"Download error: {e}")

    async def queue_download(
        self, user_id: str, file_message, save_path: str
    ) -> DownloadTask:
        """Add download to queue and start if possible with optimized concurrency."""
        logger.info(f"Queueing download for user {user_id} to path: {save_path}")
        logger.info(f"User state chat_id for {user_id}: {user_state.get_chat_id(user_id)}")
        
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
