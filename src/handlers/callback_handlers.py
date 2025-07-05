"""
Callback handlers for the Telegram File Downloader Bot.
Handles button callbacks and interactive elements.
"""

import logging
import time
from pathlib import Path
from typing import Optional
from telethon import events, Button
from telethon.errors import MessageNotModifiedError

from ..core.user_state import user_state
from ..core.config import config
from ..bot.client import client
from ..utils.path_utils import PathManager
from ..utils.keyboard_utils import (
    create_directory_keyboard,
    create_help_keyboard,
    create_rename_keyboard,
    create_status_keyboard,
    create_back_button,
)
from ..services.download_service import DownloadService

logger = logging.getLogger(__name__)

# Initialize services
path_manager = PathManager()
download_service = DownloadService()


@client.on(events.CallbackQuery())
async def callback_handler(event):
    """Handle button callbacks for directory selection and help."""
    user_id = str(event.sender_id)
    if not user_state.is_authorized(user_id, config.allowed_users):
        return

    data = event.data.decode()
    logger.info(f"User {user_id} clicked button: {data}")

    try:
        if data.startswith("dir:"):
            # Directory navigation
            encoded_path = data[4:]  # Remove 'dir:' prefix
            path = path_manager.decode_path(encoded_path)
            buttons = await create_directory_keyboard(path)
            await event.edit(
                f"Select directory to save file:\nCurrent: {path}", buttons=buttons
            )

        elif data.startswith("select:"):
            # Directory selected
            encoded_path = data[7:]  # Remove 'select:' prefix
            path = path_manager.decode_path(encoded_path)
            user_state.set_user_data(user_id, "selected_dir", path)
            user_state.set_state(user_id, "awaiting_filename")

            display_path = path if path else "."
            await event.edit(
                f"Directory selected: {display_path}\n\n"
                "Do you want to rename the file?",
                buttons=create_rename_keyboard(),
            )

        elif data == "skip_rename":
            # Skip renaming, use original filename
            logger.info(f"User {user_id} chose to skip renaming")
            await download_file(event, user_id)

        elif data == "rename_file":
            # User wants to rename, ask for new filename
            logger.info(f"User {user_id} chose to rename file")
            user_state.set_state(user_id, "awaiting_filename")
            await event.edit("Please enter the new filename (including extension):")

        elif data.startswith("create_folder:"):
            # Create new folder
            encoded_path = data[14:]  # Remove 'create_folder:' prefix
            path = path_manager.decode_path(encoded_path)
            user_state.set_state(user_id, "awaiting_folder_name")
            user_state.set_user_data(user_id, "create_folder_path", path)

            display_path = path if path else "."
            await event.edit(
                f"Creating new folder in: {display_path}\n\n"
                "Please enter the name for the new folder:",
                buttons=[[Button.inline("⬅️ Cancel", f"dir:{encoded_path}")]],
            )

        # Help section callbacks
        elif data == "help_commands":
            help_text = """
📋 **Available Commands:**

• `/start` - Start the bot and begin file download process
• `/help` - Show this help menu with all available commands
• `/status` - Check the status of your current downloads

Each command serves a specific purpose in the file download workflow.
"""
            buttons = create_back_button("help_back")
            await event.edit(help_text, buttons=buttons)

        elif data == "help_files":
            help_text = """
📁 **File Operations:**

• **Forward any file** (up to 2GB) to the bot
• **Navigate directories** using interactive inline buttons
• **Rename files** before downloading (optional)
• **Download to any directory** on your system
• **Support for all file types**: documents, photos, videos, audio, voice messages

The bot handles files of any type and size up to 2GB.
"""
            buttons = create_back_button("help_back")
            await event.edit(help_text, buttons=buttons)

        elif data == "help_navigation":
            help_text = """
🔄 **Directory Navigation:**

• **⬆️ Back** - Go to parent directory
• **🏠 Root** - Go to system root directory
• **✅ Use Here** - Select current directory for download
• **📁 Folder names** - Click to navigate into directories

You can navigate up to parent directories indefinitely and access any directory on your system.
"""
            buttons = create_back_button("help_back")
            await event.edit(help_text, buttons=buttons)

        elif data == "help_features":
            help_text = """
⚙️ **Bot Features:**

• **Parallel downloads** - Multiple files download simultaneously
• **Real-time progress** - Live updates with percentage, speed, and ETA
• **Progress tracking** - Monitor download status and queue
• **Session management** - Automatic login and session persistence
• **User authentication** - Secure access control
• **File type support** - All Telegram file types supported
• **Directory navigation** - Full system directory access
"""
            buttons = create_back_button("help_back")
            await event.edit(help_text, buttons=buttons)

        elif data == "help_tips":
            help_text = """
💡 **Tips & Tricks:**

• **Navigate freely** - You can go up parent directories indefinitely
• **Original names** - Files keep original names unless you rename them
• **Progress monitoring** - Use /status to check download queue
• **Speed optimization** - Bot uses optimized download settings
• **Session persistence** - Login once, use multiple times
• **Safe navigation** - System directories are filtered for safety
"""
            buttons = create_back_button("help_back")
            await event.edit(help_text, buttons=buttons)

        elif data == "help_quickstart":
            help_text = """
🚀 **Quick Start Guide:**

1. **Start the bot** - Send `/start`
2. **Forward a file** - Send any file up to 2GB
3. **Choose directory** - Navigate to where you want to save
4. **Select location** - Click "✅ Use Here"
5. **Rename (optional)** - Choose to rename or skip
6. **Download** - File downloads with progress updates

That's it! Your file will be downloaded to the selected location.
"""
            buttons = create_back_button("help_back")
            await event.edit(help_text, buttons=buttons)

        elif data == "help_back":
            # Return to main help menu
            help_text = """
🤖 **Telegram File Downloader Bot - Help Menu**

Choose a category below to learn more about specific features:
"""
            buttons = create_help_keyboard()
            await event.edit(help_text, buttons=buttons)

        # Status manager callbacks
        elif data == "status_refresh":
            await handle_status_refresh(event, user_id)

        elif data == "show_all_downloads":
            await handle_show_all_downloads(event, user_id)

        elif data == "clear_completed":
            await handle_clear_completed(event, user_id)

        elif data == "pause_all":
            await event.answer("⏸️ Pause functionality coming soon!")

        elif data == "resume_all":
            await event.answer("▶️ Resume functionality coming soon!")

        elif data == "retry_failed":
            await handle_retry_failed(event, user_id)

    except MessageNotModifiedError:
        # Message content is the same, ignore this error
        pass
    except Exception as e:
        logger.error(f"Error in callback handler: {e}")
        error_msg = f"❌ **Bot Error!**\n\nAn error occurred while processing your request.\n\n**Error:** {str(e)}\n\nPlease try again or use /start to restart."
        await download_service.send_notification(user_id, error_msg)
        await event.answer("An error occurred. Please try again.")


async def handle_status_refresh(event, user_id: str):
    """Handle status refresh callback."""
    user_downloads = download_service.get_user_downloads(user_id)
    if not user_downloads:
        await event.edit(
            "📊 **Download Manager**\n\n"
            "No downloads in queue.\n"
            "Forward a file to start downloading!",
            buttons=[[Button.inline("🔄 Refresh", "status_refresh")]],
        )
        return

    # Count downloads by status
    queued = sum(1 for task in user_downloads if task.status == "queued")
    downloading = sum(1 for task in user_downloads if task.status == "downloading")
    completed = sum(1 for task in user_downloads if task.status == "completed")
    failed = sum(1 for task in user_downloads if task.status == "failed")

    # Calculate total progress
    total_downloaded = sum(
        task.downloaded_bytes for task in user_downloads if task.status == "downloading"
    )
    total_size = sum(
        task.total_bytes for task in user_downloads if task.status == "downloading"
    )
    overall_progress = (total_downloaded / total_size * 100) if total_size > 0 else 0

    status_text = f"""
📊 **Download Manager** (Refreshed)

📈 **Overall Progress:** {overall_progress:.1f}%
📦 **Queue Status:**
• ⏳ Queued: {queued}
• 📥 Downloading: {downloading}
• ✅ Completed: {completed}
• ❌ Failed: {failed}

📋 **Active Downloads:**
"""

    # Show active downloads (downloading and queued)
    active_downloads = [
        task for task in user_downloads if task.status in ["queued", "downloading"]
    ]
    for i, task in enumerate(active_downloads[:5], 1):  # Show max 5 active downloads
        filename = Path(task.save_path).name
        if task.status == "queued":
            status_text += f"{i}. ⏳ **{filename}** - Waiting in queue\n"
        elif task.status == "downloading":
            progress = (
                (task.downloaded_bytes / task.total_bytes * 100)
                if task.total_bytes > 0
                else 0
            )
            downloaded_mb = task.downloaded_bytes / (1024 * 1024)
            total_mb = task.total_bytes / (1024 * 1024)
            elapsed_time = time.time() - task.start_time
            speed = task.downloaded_bytes / elapsed_time if elapsed_time > 0 else 0
            speed_mb = speed / (1024 * 1024)
            eta_seconds = (
                (task.total_bytes - task.downloaded_bytes) / speed if speed > 0 else 0
            )
            eta_minutes = eta_seconds / 60

            status_text += f"{i}. 📥 **{filename}**\n"
            status_text += f"   Progress: {progress:.1f}%\n"
            status_text += f"   Speed: {speed_mb:.1f} MB/s\n"
            status_text += (
                f"   Downloaded: {downloaded_mb:.1f} MB / {total_mb:.1f} MB\n"
            )
            status_text += f"   ETA: {eta_minutes:.1f} min\n\n"

    if len(active_downloads) > 5:
        status_text += f"... and {len(active_downloads) - 5} more downloads\n"

    buttons = create_status_keyboard(queued, downloading, failed, completed)
    await event.edit(status_text, buttons=buttons)


async def handle_show_all_downloads(event, user_id: str):
    """Handle show all downloads callback."""
    user_downloads = download_service.get_user_downloads(user_id)
    if not user_downloads:
        await event.edit("No downloads found.")
        return

    status_text = "📋 **All Downloads:**\n\n"

    for i, task in enumerate(user_downloads, 1):
        filename = Path(task.save_path).name
        if task.status == "queued":
            status_text += f"{i}. ⏳ **{filename}** - Waiting in queue\n"
        elif task.status == "downloading":
            progress = (
                (task.downloaded_bytes / task.total_bytes * 100)
                if task.total_bytes > 0
                else 0
            )
            downloaded_mb = task.downloaded_bytes / (1024 * 1024)
            total_mb = task.total_bytes / (1024 * 1024)
            elapsed_time = time.time() - task.start_time
            speed = task.downloaded_bytes / elapsed_time if elapsed_time > 0 else 0
            speed_mb = speed / (1024 * 1024)
            eta_seconds = (
                (task.total_bytes - task.downloaded_bytes) / speed if speed > 0 else 0
            )
            eta_minutes = eta_seconds / 60

            status_text += f"{i}. 📥 **{filename}**\n"
            status_text += f"   Progress: {progress:.1f}%\n"
            status_text += f"   Speed: {speed_mb:.1f} MB/s\n"
            status_text += (
                f"   Downloaded: {downloaded_mb:.1f} MB / {total_mb:.1f} MB\n"
            )
            status_text += f"   ETA: {eta_minutes:.1f} min\n\n"
        elif task.status == "completed":
            status_text += f"{i}. ✅ **{filename}** - Completed\n"
        elif task.status == "failed":
            error_msg = task.error if task.error else "Unknown error"
            status_text += f"{i}. ❌ **{filename}** - Failed: {error_msg}\n"

    buttons = create_back_button("status_refresh")
    await event.edit(status_text, buttons=buttons)


async def handle_clear_completed(event, user_id: str):
    """Handle clear completed downloads callback."""
    cleared_count = download_service.clear_completed_downloads(user_id)
    if cleared_count > 0:
        await event.answer(f"✅ {cleared_count} completed downloads cleared!")
        await event.edit(
            f"📊 **Download Manager**\n\n"
            f"✅ {cleared_count} completed downloads have been cleared from the queue.",
            buttons=[[Button.inline("🔄 Refresh", "status_refresh")]],
        )
    else:
        await event.answer("No downloads to clear.")


async def handle_retry_failed(event, user_id: str):
    """Handle retry failed downloads callback."""
    retry_count = download_service.retry_failed_downloads(user_id)

    if retry_count > 0:
        await event.answer(f"🔄 Retrying {retry_count} failed downloads...")
        await event.edit(
            f"📊 **Download Manager**\n\n"
            f"🔄 Retrying {retry_count} failed downloads...",
            buttons=[[Button.inline("🔄 Refresh", "status_refresh")]],
        )
    else:
        await event.answer("No failed downloads to retry.")


async def download_file(event, user_id: str, filename: Optional[str] = None):
    """Queue file for download instead of downloading immediately."""
    try:
        file_message = user_state.get_user_data(user_id, "file_message")
        if not file_message:
            error_msg = "❌ **Error!**\n\nNo file message found. Please try sending the file again."
            await download_service.send_notification(user_id, error_msg)
            await event.respond("❌ Error: No file message found")
            user_state.set_state(user_id, "logged_in", chat_id=event.chat_id)
            return

        selected_dir = user_state.get_user_data(user_id, "selected_dir", ".")
        chat_id = user_state.get_chat_id(user_id) or event.chat_id

        # Determine save path - use full system path
        save_dir = selected_dir if selected_dir else "."

        # Check if directory exists and is writable
        if not path_manager.ensure_directory_exists(save_dir):
            error_msg = f"❌ **Permission Error!**\n\nCannot create directory: {save_dir}\n\n**Error:** Permission denied\n\nPlease choose a different location or check permissions."
            await download_service.send_notification(user_id, error_msg)
            await event.respond(
                f"❌ Permission denied: Cannot create directory {save_dir}"
            )
            user_state.set_state(user_id, "logged_in", chat_id=chat_id)
            return
        elif not path_manager.is_directory_writable(save_dir):
            error_msg = f"❌ **Permission Error!**\n\nCannot write to directory: {save_dir}\n\n**Error:** Directory is read-only\n\nPlease choose a different location."
            await download_service.send_notification(user_id, error_msg)
            await event.respond(
                f"❌ Permission denied: Cannot write to directory {save_dir}"
            )
            user_state.set_state(user_id, "logged_in", chat_id=chat_id)
            return

        # Get original filename and extension
        original_filename = None
        original_extension = None

        if hasattr(file_message.media, "document") and file_message.media.document:
            original_filename = file_message.media.document.attributes[0].file_name
            if original_filename:
                original_extension = path_manager.get_file_extension(original_filename)

        # Handle filename logic
        if not filename:
            # Use original filename
            if original_filename:
                final_filename = original_filename
            else:
                final_filename = f"file_{int(time.time())}"
        else:
            # User provided a new filename
            user_filename = filename.strip()

            # Check if user included an extension
            user_ext = Path(user_filename).suffix
            user_name = Path(user_filename).stem

            if user_ext:
                # User provided extension, use it as-is
                final_filename = user_filename
                logger.info(
                    f"User provided extension: {user_ext}, using: {final_filename}"
                )
            else:
                # User provided only name, use original extension
                if original_extension:
                    final_filename = f"{user_name}{original_extension}"
                    logger.info(
                        f"Using original extension {original_extension}, final filename: {final_filename}"
                    )
                else:
                    # No original extension, use as-is
                    final_filename = user_filename
                    logger.info(
                        f"No original extension found, using as-is: {final_filename}"
                    )

        # Sanitize the final filename to remove problematic characters
        final_filename = path_manager.sanitize_filename(final_filename)

        save_path = path_manager.join_paths(save_dir, final_filename)

        logger.info(f"Queuing download to: {save_path}")
        await event.respond(f"📥 Queuing download to: {save_path}")

        # Queue the download
        await download_service.queue_download(user_id, file_message, save_path)

        # Reset user state but preserve chat_id
        user_state.set_state(user_id, "logged_in", chat_id=chat_id)

    except PermissionError as e:
        logger.error(f"Permission error queuing download: {e}")
        error_msg = f"❌ **Permission Error!**\n\nCannot write to the selected directory.\n\n**Error:** {str(e)}\n\nPlease choose a different location."
        await download_service.send_notification(user_id, error_msg)
        await event.respond(
            "❌ Permission denied: Cannot write to the selected directory. Please choose a different location."
        )
        user_state.set_state(user_id, "logged_in", chat_id=event.chat_id)
    except Exception as e:
        logger.error(f"Error queuing download: {e}")
        error_msg = f"❌ **Download Error!**\n\nFailed to queue download.\n\n**Error:** {str(e)}\n\nPlease try again or contact support."
        await download_service.send_notification(user_id, error_msg)
        await event.respond(f"❌ Error queuing download: {e}")
        user_state.set_state(user_id, "logged_in", chat_id=event.chat_id)
