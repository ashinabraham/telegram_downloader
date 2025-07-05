"""
Download service module for handling file downloads and business logic.
"""

import os
import asyncio
import logging
from typing import Optional, Tuple

from ..core.config import get_config
from ..core.user_state import user_state
from ..download_manager.manager import download_manager
from ..utils.path_utils import path_manager

logger = logging.getLogger(__name__)

# Get configuration
config = get_config()


class DownloadService:
    """Service layer for handling download operations."""

    @staticmethod
    async def validate_user_permission(user_id: str) -> bool:
        """Validate if user has permission to download files."""
        allowed_users = config.allowed_users
        if not allowed_users:
            return True
        return str(user_id) in allowed_users

    @staticmethod
    async def validate_file_message(file_message) -> Tuple[bool, str]:
        """Validate if the message contains a downloadable file."""
        try:
            if not file_message or not file_message.media:
                return False, "No media found in message"

            # Check if it's a document
            if hasattr(file_message.media, "document") and file_message.media.document:
                return True, ""

            # Check if it's a photo
            if hasattr(file_message.media, "photo") and file_message.media.photo:
                return True, ""

            # Check if it's a video
            if hasattr(file_message.media, "video") and file_message.media.video:
                return True, ""

            # Check if it's an audio file
            if hasattr(file_message.media, "audio") and file_message.media.audio:
                return True, ""

            # Check if it's a voice message
            if hasattr(file_message.media, "voice") and file_message.media.voice:
                return True, ""

            return False, "Unsupported media type"

        except Exception as e:
            logger.error(f"Error validating file message: {e}")
            return False, f"Error validating message: {str(e)}"

    @staticmethod
    async def get_file_info(file_message) -> Tuple[str, int, str]:
        """Extract file information from message."""
        try:
            filename = "unknown_file"
            file_size = 0
            file_type = "unknown"

            if hasattr(file_message.media, "document") and file_message.media.document:
                document = file_message.media.document
                filename = (
                    document.attributes[0].file_name
                    if document.attributes
                    else "document"
                )
                file_size = document.size
                file_type = "document"
            elif hasattr(file_message.media, "photo") and file_message.media.photo:
                photo = file_message.media.photo
                filename = f"photo_{photo.id}.jpg"
                file_size = photo.sizes[-1].size if photo.sizes else 0
                file_type = "photo"
            elif hasattr(file_message.media, "video") and file_message.media.video:
                video = file_message.media.video
                filename = (
                    video.attributes[0].file_name
                    if video.attributes
                    else f"video_{video.id}.mp4"
                )
                file_size = video.size
                file_type = "video"
            elif hasattr(file_message.media, "audio") and file_message.media.audio:
                audio = file_message.media.audio
                filename = (
                    audio.attributes[0].file_name
                    if audio.attributes
                    else f"audio_{audio.id}.mp3"
                )
                file_size = audio.size
                file_type = "audio"
            elif hasattr(file_message.media, "voice") and file_message.media.voice:
                voice = file_message.media.voice
                filename = f"voice_{voice.id}.ogg"
                file_size = voice.size
                file_type = "voice"

            return filename, file_size, file_type

        except Exception as e:
            logger.error(f"Error getting file info: {e}")
            return "unknown_file", 0, "unknown"

    @staticmethod
    async def generate_save_path(user_id: str, filename: str) -> str:
        """Generate a safe file path for saving the downloaded file."""
        try:
            # Sanitize filename using path_manager
            safe_filename = path_manager.sanitize_filename(filename)

            # Create user-specific directory
            user_dir = os.path.join(config.base_download_dir, str(user_id))

            # Ensure directory exists using async operation
            await asyncio.to_thread(path_manager.ensure_directory_exists, user_dir)

            # Generate unique filename if file already exists
            base_name, ext = os.path.splitext(safe_filename)
            counter = 1
            final_filename = safe_filename

            while await asyncio.to_thread(
                os.path.exists, os.path.join(user_dir, final_filename)
            ):
                final_filename = f"{base_name}_{counter}{ext}"
                counter += 1

            return os.path.join(user_dir, final_filename)

        except Exception as e:
            logger.error(f"Error generating save path: {e}")
            # Fallback to simple path
            return os.path.join(config.base_download_dir, str(user_id), safe_filename)

    @staticmethod
    async def check_disk_space(file_size: int) -> bool:
        """Check if there's enough disk space for the file."""
        try:
            import shutil

            total, used, free = await asyncio.to_thread(
                shutil.disk_usage, config.base_download_dir
            )

            # Require at least 2x the file size as free space for safety
            required_space = file_size * 2
            return free >= required_space

        except Exception as e:
            logger.error(f"Error checking disk space: {e}")
            return True  # Assume OK if we can't check

    @staticmethod
    async def start_download(user_id: str, file_message) -> Tuple[bool, str]:
        """Start a download for the given user and file message."""
        try:
            # Validate user permission
            if not await DownloadService.validate_user_permission(user_id):
                return False, "You are not authorized to download files."

            # Validate file message
            is_valid, error_msg = await DownloadService.validate_file_message(
                file_message
            )
            if not is_valid:
                return False, error_msg

            # Get file information
            filename, file_size, file_type = await DownloadService.get_file_info(
                file_message
            )

            # Check disk space
            if not await DownloadService.check_disk_space(file_size):
                return (
                    False,
                    f"Insufficient disk space. File size: {file_size / (1024*1024):.1f} MB",
                )

            # Generate save path
            save_path = await DownloadService.generate_save_path(user_id, filename)

            # Queue the download
            task = await download_manager.queue_download(
                user_id, file_message, save_path
            )

            logger.info(
                f"Download queued for user {user_id}: {filename} -> {save_path}"
            )
            return True, f"Download started for {filename}"

        except Exception as e:
            logger.error(f"Error starting download: {e}")
            return False, f"Failed to start download: {str(e)}"

    @staticmethod
    async def get_download_status(user_id: str) -> dict:
        """Get download status for a user."""
        try:
            downloads = download_manager.get_user_downloads(user_id)

            status = {
                "total": len(downloads),
                "queued": 0,
                "downloading": 0,
                "completed": 0,
                "failed": 0,
                "downloads": [],
            }

            for task in downloads:
                status[task.status] += 1

                download_info = {
                    "filename": os.path.basename(task.save_path),
                    "status": task.status,
                    "progress": 0,
                    "size": task.total_bytes,
                    "downloaded": task.downloaded_bytes,
                    "error": task.error,
                }

                # Calculate progress percentage
                if task.total_bytes > 0:
                    download_info["progress"] = (
                        task.downloaded_bytes / task.total_bytes
                    ) * 100

                status["downloads"].append(download_info)

            return status

        except Exception as e:
            logger.error(f"Error getting download status: {e}")
            return {"error": str(e)}

    @staticmethod
    async def clear_completed_downloads(user_id: str) -> int:
        """Clear completed downloads for a user."""
        try:
            return download_manager.clear_completed_downloads(user_id)
        except Exception as e:
            logger.error(f"Error clearing completed downloads: {e}")
            return 0

    @staticmethod
    async def retry_failed_downloads(user_id: str) -> int:
        """Retry failed downloads for a user."""
        try:
            return download_manager.retry_failed_downloads(user_id)
        except Exception as e:
            logger.error(f"Error retrying failed downloads: {e}")
            return 0


# Global download service instance
download_service = DownloadService()
