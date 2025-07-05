"""
Message handlers for the Telegram File Downloader Bot.
Handles incoming messages and media files.
"""

import logging
from telethon import events

from ..services.download_service import download_service
from ..core.user_state import user_state

logger = logging.getLogger(__name__)


@events.register(events.NewMessage(pattern=r"/start"))
async def start_command(event):
    """Handle /start command."""
    try:
        user_id = str(event.sender_id)
        chat_id = event.chat_id

        # Store user's chat_id for notifications
        user_state.set_chat_id(user_id, chat_id)

        welcome_message = (
            "🤖 **Welcome to the Telegram File Downloader Bot!**\n\n"
            "📥 **How to use:**\n"
            "• Send me any file, photo, video, or audio message\n"
            "• I'll download it to your personal folder\n"
            "• Use `/status` to check download progress\n"
            "• Use `/clear` to remove completed downloads\n"
            "• Use `/retry` to retry failed downloads\n\n"
            "🚀 **Ready to download!**"
        )

        await event.respond(welcome_message)
        logger.info(f"User {user_id} started the bot")

    except Exception as e:
        logger.error(f"Error in start command: {e}")
        await event.respond("❌ An error occurred. Please try again.")


@events.register(events.NewMessage(pattern=r"/help"))
async def help_command(event):
    """Handle /help command."""
    try:
        help_message = (
            "📚 **Bot Commands:**\n\n"
            "📥 **Download:**\n"
            "• Send any file, photo, video, or audio\n"
            "• Files are saved to your personal folder\n\n"
            "📊 **Status & Management:**\n"
            "• `/status` - Check download progress\n"
            "• `/clear` - Remove completed downloads\n"
            "• `/retry` - Retry failed downloads\n"
            "• `/help` - Show this help message\n\n"
            "⚙️ **Settings:**\n"
            "• Files are organized by user ID\n"
            "• Automatic filename sanitization\n"
            "• Progress tracking and notifications\n"
        )

        await event.respond(help_message)

    except Exception as e:
        logger.error(f"Error in help command: {e}")
        await event.respond("❌ An error occurred. Please try again.")


@events.register(events.NewMessage(pattern=r"/status"))
async def status_command(event):
    """Handle /status command."""
    try:
        user_id = str(event.sender_id)

        # Get download status
        status = await download_service.get_download_status(user_id)

        if "error" in status:
            await event.respond(f"❌ Error getting status: {status['error']}")
            return

        if status["total"] == 0:
            await event.respond("📭 No downloads found.")
            return

        # Build status message
        status_message = "📊 **Download Status for " + user_id + ":**\n\n"
        status_message += "📈 **Summary:**\n"
        status_message += "• Total: " + str(status['total']) + "\n"
        status_message += "• Queued: " + str(status['queued']) + "\n"
        status_message += "• Downloading: " + str(status['downloading']) + "\n"
        status_message += "• Completed: " + str(status['completed']) + "\n"
        status_message += "• Failed: " + str(status['failed']) + "\n\n"

        if status["downloads"]:
            status_message += "📁 **Downloads:**\n"
            for download in status["downloads"][:5]:  # Show first 5 downloads
                filename = download["filename"]
                status_emoji = {
                    "queued": "⏳",
                    "downloading": "📥",
                    "completed": "✅",
                    "failed": "❌",
                }.get(download["status"], "❓")

                progress = download["progress"]
                size_mb = (
                    download["size"] / (1024 * 1024) if download["size"] > 0 else 0
                )

                status_message += (
                    status_emoji + " **" + filename + "**\n"
                    "   Status: " + str(download["status"]) + "\n"
                    "   Size: {:.1f} MB\n".format(size_mb)
                )

                if download["status"] == "downloading":
                    status_message += f"   Progress: {progress:.1f}%\n"
                elif download["status"] == "failed" and download["error"]:
                    status_message += f"   Error: {download['error']}\n"

                status_message += "\n"

            if len(status["downloads"]) > 5:
                status_message += (
                    f"... and {len(status['downloads']) - 5} more downloads\n"
                )

        await event.respond(status_message)

    except Exception as e:
        logger.error(f"Error in status command: {e}")
        await event.respond("❌ An error occurred while getting status.")


@events.register(events.NewMessage(pattern=r"/clear"))
async def clear_command(event):
    """Handle /clear command."""
    try:
        user_id = str(event.sender_id)

        # Clear completed downloads
        cleared_count = await download_service.clear_completed_downloads(user_id)

        if cleared_count > 0:
            await event.respond(f"🧹 Cleared {cleared_count} completed downloads.")
        else:
            await event.respond("📭 No completed downloads to clear.")

    except Exception as e:
        logger.error(f"Error in clear command: {e}")
        await event.respond("❌ An error occurred while clearing downloads.")


@events.register(events.NewMessage(pattern=r"/retry"))
async def retry_command(event):
    """Handle /retry command."""
    try:
        user_id = str(event.sender_id)

        # Retry failed downloads
        retry_count = await download_service.retry_failed_downloads(user_id)

        if retry_count > 0:
            await event.respond(f"🔄 Retrying {retry_count} failed downloads.")
        else:
            await event.respond("📭 No failed downloads to retry.")

    except Exception as e:
        logger.error(f"Error in retry command: {e}")
        await event.respond("❌ An error occurred while retrying downloads.")


@events.register(events.NewMessage)
async def handle_media_message(event):
    """Handle media messages (files, photos, videos, etc.)."""
    try:
        user_id = str(event.sender_id)
        chat_id = event.chat_id

        # Store user's chat_id for notifications
        user_state.set_chat_id(user_id, chat_id)

        # Check if message contains media
        if not event.media:
            return  # Not a media message, ignore

        # Start download
        success, message = await download_service.start_download(user_id, event.message)

        if success:
            await event.respond(f"✅ {message}")
        else:
            await event.respond(f"❌ {message}")

    except Exception as e:
        logger.error(f"Error handling media message: {e}")
        await event.respond("❌ An error occurred while processing your file.")
