"""
Message handlers module for the Telegram File Downloader Bot.
Handles text messages, file forwarding, and user state transitions.
"""

import logging
from telethon import events
from telethon.errors import SessionPasswordNeededError

from ..core.config import config
from ..core.user_state import user_state
from ..bot.client import client
from ..utils.path_utils import path_manager
from ..utils.keyboard_utils import create_directory_keyboard
from ..downloads.download_manager import download_manager

logger = logging.getLogger(__name__)


@client.on(events.NewMessage())
async def message_handler(event):
    """Handle all incoming messages based on user state."""
    user_id = str(event.sender_id)
    chat_id = event.chat_id

    if not user_state.is_authorized(user_id, config.allowed_users):
        return

    # Update chat_id in user state
    user_state.set_chat_id(user_id, chat_id)

    state = user_state.get_state(user_id)
    logger.info(f"User {user_id} sent message in state: {state}")

    # Handle users who haven't started the bot
    if state is None:
        await event.respond("Please use /start to begin using the bot.")
        return

    if state == "awaiting_phone":
        await handle_phone_input(event, user_id)

    elif state == "awaiting_code":
        await handle_code_input(event, user_id)

    elif state == "awaiting_2fa":
        await handle_2fa_input(event, user_id)

    elif state == "awaiting_filename":
        await handle_filename_input(event, user_id)

    elif state == "awaiting_folder_name":
        await handle_folder_name_input(event, user_id)

    elif state == "logged_in":
        await handle_logged_in_message(event, user_id)

    else:
        logger.warning(f"User {user_id} in unknown state: {state}")
        await event.respond("Please use /start to begin using the bot.")


async def handle_phone_input(event, user_id: str):
    """Handle phone number input during login."""
    phone = event.raw_text.strip()
    logger.info(f"User {user_id} provided phone number: {phone}")

    user_state.set_state(user_id, "awaiting_code", phone=phone)

    try:
        await client.send_code_request(phone)
        logger.info(f"Code request sent to {phone}")
        await event.respond(
            "A code has been sent to your Telegram. Please enter the code:"
        )
    except Exception as e:
        logger.error(f"Failed to send code to {phone}: {e}")
        error_msg = f"❌ **Login Error!**\n\nFailed to send verification code to {phone}.\n\n**Error:** {str(e)}\n\nPlease try again with a valid phone number."
        await download_manager.send_notification(user_id, error_msg)
        user_state.set_state(user_id, "awaiting_phone")
        await event.respond(
            f"Failed to send code: {e}. Please enter your phone number again:"
        )


async def handle_code_input(event, user_id: str):
    """Handle verification code input during login."""
    code = event.raw_text.strip()
    phone = user_state.get_user_data(user_id, "phone")
    logger.info(f"User {user_id} provided code for {phone}")

    try:
        await client.sign_in(phone, code)
        logger.info(f"User {user_id} successfully signed in")
        user_state.set_state(user_id, "logged_in")
        await event.respond(
            "Login successful! Forward me a file and I will download it for you."
        )
    except SessionPasswordNeededError:
        logger.info(f"User {user_id} needs 2FA password")
        user_state.set_state(user_id, "awaiting_2fa", phone=phone, code=code)
        await event.respond(
            "Two-step verification is enabled. Please enter your password:"
        )
    except Exception as e:
        logger.error(f"Login failed for user {user_id}: {e}")
        error_msg = f"❌ **Login Error!**\n\nFailed to verify code for {phone}.\n\n**Error:** {str(e)}\n\nPlease try again with the correct code."
        await download_manager.send_notification(user_id, error_msg)
        user_state.set_state(user_id, "awaiting_phone")
        await event.respond(f"Login failed: {e}. Please enter your phone number again:")


async def handle_2fa_input(event, user_id: str):
    """Handle two-factor authentication password input."""
    password = event.raw_text.strip()
    phone = user_state.get_user_data(user_id, "phone")
    code = user_state.get_user_data(user_id, "code")
    logger.info(f"User {user_id} provided 2FA password")

    try:
        await client.sign_in(phone, code, password=password)
        logger.info(f"User {user_id} successfully signed in with 2FA")
        user_state.set_state(user_id, "logged_in")
        await event.respond(
            "Login successful! Forward me a file and I will download it for you."
        )
    except Exception as e:
        logger.error(f"2FA failed for user {user_id}: {e}")
        error_msg = f"❌ **2FA Error!**\n\nFailed to verify 2FA password.\n\n**Error:** {str(e)}\n\nPlease try again with the correct password."
        await download_manager.send_notification(user_id, error_msg)
        user_state.set_state(user_id, "awaiting_phone")
        await event.respond(f"2FA failed: {e}. Please enter your phone number again:")


async def handle_filename_input(event, user_id: str):
    """Handle filename input for file renaming."""
    new_filename = event.raw_text.strip()
    if not new_filename:
        await event.respond(
            "Please provide a valid filename or click 'Skip' to use the original name."
        )
        return

    # Download the file with new filename
    from .callback_handlers import download_file

    await download_file(event, user_id, new_filename)


async def handle_folder_name_input(event, user_id: str):
    """Handle folder name input for creating new folders."""
    folder_name = event.raw_text.strip()
    if not folder_name:
        await event.respond(
            "Please provide a valid folder name or click 'Cancel' to go back."
        )
        return

    # Sanitize folder name
    safe_folder_name = path_manager.sanitize_filename(folder_name)
    if not safe_folder_name:
        await event.respond(
            "Invalid folder name. Please use only letters, numbers, and spaces."
        )
        return

    # Get the path where folder should be created
    create_path = user_state.get_user_data(user_id, "create_folder_path")
    new_folder_path = path_manager.join_paths(create_path, safe_folder_name)

    try:
        # Create the folder
        if path_manager.ensure_directory_exists(new_folder_path):
            logger.info(f"User {user_id} created folder: {new_folder_path}")

            # Navigate to the newly created folder
            buttons = await create_directory_keyboard(new_folder_path)

            await event.respond(
                f"✅ Folder '{safe_folder_name}' created successfully!\n\n"
                f"Current location: {new_folder_path}",
                buttons=buttons,
            )

            # Reset user state
            user_state.set_state(user_id, "logged_in")

        else:
            raise PermissionError("Failed to create folder")

    except PermissionError:
        error_msg = f"❌ **Permission Error!**\n\nCannot create folder: {safe_folder_name}\n\n**Error:** Permission denied\n\nPlease choose a different location or check permissions."
        await download_manager.send_notification(user_id, error_msg)
        await event.respond(
            f"❌ Permission denied: Cannot create folder {safe_folder_name}"
        )
        user_state.set_state(user_id, "logged_in")
    except Exception as e:
        logger.error(f"Error creating folder: {e}")
        await event.respond(f"❌ Error creating folder: {e}")
        user_state.set_state(user_id, "logged_in")


async def handle_logged_in_message(event, user_id: str):
    """Handle messages when user is logged in."""
    # Check if message contains a file
    if event.message.media:
        logger.info(f"User {user_id} forwarded a file")
        user_state.set_user_data(user_id, "file_message", event.message)
        user_state.set_state(user_id, "selecting_directory")

        # Show directory selection
        buttons = await create_directory_keyboard()
        await event.respond("Select directory to save the file:", buttons=buttons)
    else:
        # Only respond to text messages that are commands or specific requests
        message_text = event.raw_text.strip().lower() if event.raw_text else ""

        # Ignore empty messages or non-command messages to prevent spam
        if not message_text or message_text in ["/start", "/help", "/status"]:
            # These commands are handled by their specific handlers
            return
        else:
            # Only respond to actual requests, not random messages
            logger.info(
                f"User {user_id} sent message while logged in: {event.raw_text[:50]}..."
            )
            # Don't respond to every message to prevent flood wait
            return
