"""
Command handlers module for the Telegram File Downloader Bot.
Handles bot commands like /start, /help, and /status.
"""

import os
import time
import logging
from telethon import events, Button

from ..core.config import config
from ..core.user_state import user_state
from ..bot.client import client, is_logged_in
from ..utils.keyboard_utils import create_help_keyboard, create_status_keyboard
from ..downloads.download_manager import download_manager

logger = logging.getLogger(__name__)


@client.on(events.NewMessage(pattern="/start"))
async def start_handler(event):
    """Handle the /start command."""
    user_id = str(event.sender_id)
    chat_id = event.chat_id
    logger.info(f"Received /start command from user {user_id}")

    if not user_state.is_authorized(user_id, config.allowed_users):
        logger.warning(f"Unauthorized user {user_id} tried to access the bot")
        await event.respond("You are not allowed to use this bot.")
        return

    logger.info(f"Authorized user {user_id} started the bot")

    # Update chat_id in user state
    user_state.set_chat_id(user_id, chat_id)

    if not await is_logged_in():
        logger.info(f"User {user_id} needs to login")
        user_state.set_state(user_id, "awaiting_phone", chat_id=chat_id)
        await event.respond(
            "Please enter your phone number (with country code, e.g. +123456789):"
        )
    else:
        logger.info(f"User {user_id} is already logged in")
        user_state.set_state(user_id, "logged_in", chat_id=chat_id)
        await event.respond("Forward me a file and I will download it for you.")


@client.on(events.NewMessage(pattern="/help"))
async def help_handler(event):
    """Handle the /help command."""
    user_id = str(event.sender_id)
    logger.info(f"Received /help command from user {user_id}")

    if not user_state.is_authorized(user_id, config.allowed_users):
        logger.warning(f"Unauthorized user {user_id} tried to access help")
        await event.respond("You are not allowed to use this bot.")
        return

    help_text = """
🤖 **Telegram File Downloader Bot - Help Menu**

Choose a category below to learn more about specific features:
"""

    buttons = create_help_keyboard()
    await event.respond(help_text, buttons=buttons)


@client.on(events.NewMessage(pattern="/status"))
async def status_handler(event):
    """Handle the /status command to show download status."""
    user_id = str(event.sender_id)
    if not user_state.is_authorized(user_id, config.allowed_users):
        return

    user_downloads = download_manager.get_user_downloads(user_id)
    if not user_downloads:
        await event.respond(
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
📊 **Download Manager**

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
        filename = os.path.basename(task.save_path)
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

    # Create interactive buttons
    buttons = create_status_keyboard(queued, downloading, failed, completed)

    # Send status message
    await event.respond(status_text, buttons=buttons)
