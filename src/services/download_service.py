"""
Download service module for the Telegram File Downloader Bot.
Handles download business logic, queue management, and progress tracking.
"""

import os
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Any
from pathlib import Path

from ..core.config import get_config
from ..download_manager.manager import DownloadManager, DownloadTask
from ..utils.path_utils import path_manager

logger = logging.getLogger(__name__)

# Get configuration
config = get_config()


class DownloadService:
    """Service layer for download operations and business logic."""

    def __init__(self):
        self.download_manager = DownloadManager()
        self.download_executor = ThreadPoolExecutor(
            max_workers=config.max_concurrent_downloads
        )

    async def queue_download(
        self, user_id: str, file_message, save_path: str
    ) -> DownloadTask:
        """Queue a file for download with business logic validation."""
        logger.info(
            f"Service: Queueing download for user {user_id} to path: {save_path}"
        )

        # Validate save path
        if not self._validate_save_path(save_path):
            raise ValueError(f"Invalid save path: {save_path}")

        # Create download task
        task = await self.download_manager.queue_download(
            user_id, file_message, save_path
        )

        logger.info(f"Service: Download queued successfully for user {user_id}")
        return task

    def get_user_downloads(self, user_id: str) -> List[DownloadTask]:
        """Get all downloads for a user with business logic."""
        downloads = self.download_manager.get_user_downloads(user_id)

        # Filter out any invalid downloads
        valid_downloads = [d for d in downloads if self._validate_download_task(d)]

        return valid_downloads

    def clear_completed_downloads(self, user_id: str) -> int:
        """Clear completed downloads with business logic."""
        cleared_count = self.download_manager.clear_completed_downloads(user_id)

        if cleared_count > 0:
            logger.info(
                f"Service: Cleared {cleared_count} completed downloads for user {user_id}"
            )

        return cleared_count

    def retry_failed_downloads(self, user_id: str) -> int:
        """Retry failed downloads with business logic."""
        retry_count = self.download_manager.retry_failed_downloads(user_id)

        if retry_count > 0:
            logger.info(
                f"Service: Retrying {retry_count} failed downloads for user {user_id}"
            )

        return retry_count

    async def send_notification(
        self, user_id: str, message: str, is_management_command: bool = False
    ) -> None:
        """Send notification with business logic."""
        await self.download_manager.send_notification(
            user_id, message, is_management_command
        )

    def _validate_save_path(self, save_path: str) -> bool:
        """Validate save path with business rules."""
        try:
            # Check if path is within the allowed base download directory
            if not path_manager._is_path_within_bounds(save_path):
                logger.error(f"Save path {save_path} is outside allowed bounds")
                return False

            # Check if path is absolute or relative
            path = Path(save_path)

            # Ensure directory exists or can be created
            parent_dir = path.parent
            if not parent_dir.exists():
                # Try to create directory
                try:
                    parent_dir.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    logger.error(f"Failed to create directory {parent_dir}: {e}")
                    return False

            # Check if directory is writable
            if not os.access(parent_dir, os.W_OK):
                logger.error(f"Directory {parent_dir} is not writable")
                return False

            return True
        except Exception as e:
            logger.error(f"Error validating save path {save_path}: {e}")
            return False

    def _validate_download_task(self, task: DownloadTask) -> bool:
        """Validate download task with business rules."""
        try:
            # Check if task has required attributes
            if not hasattr(task, "user_id") or not hasattr(task, "save_path"):
                return False

            # Check if save path is valid
            if not self._validate_save_path(task.save_path):
                return False

            return True
        except Exception as e:
            logger.error(f"Error validating download task: {e}")
            return False

    def get_download_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get download statistics with business logic."""
        downloads = self.get_user_downloads(user_id)

        stats: Dict[str, Any] = {
            "total": len(downloads),
            "queued": 0,
            "downloading": 0,
            "completed": 0,
            "failed": 0,
            "total_size": 0,
            "downloaded_size": 0,
            "average_speed": 0.0,
        }

        total_speed = 0.0
        speed_count = 0

        for task in downloads:
            stats[task.status] += 1
            stats["total_size"] += task.total_bytes
            stats["downloaded_size"] += task.downloaded_bytes

            # Calculate speed for downloading tasks
            if task.status == "downloading" and task.start_time:
                elapsed_time = time.time() - task.start_time
                if elapsed_time > 0:
                    speed = task.downloaded_bytes / elapsed_time
                    total_speed += speed
                    speed_count += 1

        if speed_count > 0:
            stats["average_speed"] = total_speed / speed_count

        return stats


# Global download service instance
download_service = DownloadService()
