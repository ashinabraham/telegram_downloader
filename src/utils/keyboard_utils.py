"""
Keyboard utilities module for the Telegram File Downloader Bot.
Handles inline keyboard creation for directory navigation and help menus.
"""

import logging
from telethon import Button

from ..utils.path_utils import path_manager

logger = logging.getLogger(__name__)


async def create_directory_keyboard(current_path: str = ""):
    """Create inline keyboard for directory selection."""
    items = await path_manager.get_directory_options(current_path)

    buttons = []
    for item, item_type in items:
        if item_type == "dir":
            new_path = (
                path_manager.join_paths(current_path, item) if current_path else item
            )
            encoded_path = path_manager.encode_path(new_path)
            buttons.append(
                [Button.inline("📁 {}".format(item), "dir:{}".format(encoded_path))]
            )

    # Add navigation buttons
    nav_buttons = []

    # Always show Back button if we can go up (even from current directory)
    if current_path:
        # We're in a subdirectory, go to parent
        parent_path = path_manager.get_parent_directory(current_path)
        encoded_parent = path_manager.encode_path(parent_path)
        nav_buttons.append(Button.inline("⬆️ Back", "dir:{}".format(encoded_parent)))
    else:
        # We're in current directory (.), go to parent directory
        # Use '..' as the parent path when we're in current directory
        encoded_parent = path_manager.encode_path("..")
        nav_buttons.append(Button.inline("⬆️ Back", "dir:{}".format(encoded_parent)))

    # Add "Go to Root" button for easier navigation
    if current_path != "/":
        nav_buttons.append(Button.inline("🏠 Root", "dir:/"))

    encoded_current = path_manager.encode_path(current_path)
    nav_buttons.append(
        Button.inline("✅ Use Here", "select:{}".format(encoded_current))
    )

    if nav_buttons:
        buttons.append(nav_buttons)

    # Add folder management buttons
    folder_buttons = []
    folder_buttons.append(
        Button.inline(
            "📁 Create New Folder", "create_folder:{}".format(encoded_current)
        )
    )
    if folder_buttons:
        buttons.append(folder_buttons)

    return buttons


def create_help_keyboard():
    """Create the main help menu keyboard."""
    buttons = [
        [Button.inline("📋 Commands", "help_commands")],
        [Button.inline("📁 File Operations", "help_files")],
        [Button.inline("🔄 Navigation", "help_navigation")],
        [Button.inline("⚙️ Features", "help_features")],
        [Button.inline("💡 Tips & Tricks", "help_tips")],
        [Button.inline("🚀 Quick Start", "help_quickstart")],
    ]
    return buttons


def create_rename_keyboard():
    """Create keyboard for file renaming options."""
    return [
        [
            Button.inline("✅ Skip", "skip_rename"),
            Button.inline("✏️ Rename", "rename_file"),
        ]
    ]


def create_status_keyboard(queued: int, downloading: int, failed: int, completed: int):
    """Create keyboard for status management."""
    buttons = []

    # Action buttons
    action_row = []
    if downloading > 0:
        action_row.append(Button.inline("⏸️ Pause All", "pause_all"))
    if queued > 0:
        action_row.append(Button.inline("▶️ Resume All", "resume_all"))
    if failed > 0:
        action_row.append(Button.inline("🔄 Retry Failed", "retry_failed"))
    if action_row:
        buttons.append(action_row)

    # Navigation buttons
    nav_row = []
    if completed > 0 or failed > 0:
        nav_row.append(Button.inline("📋 Show All", "show_all_downloads"))
    nav_row.append(Button.inline("🔄 Refresh", "status_refresh"))
    nav_row.append(Button.inline("🗑️ Clear Completed", "clear_completed"))
    if nav_row:
        buttons.append(nav_row)

    return buttons


def create_back_button(callback_data: str):
    """Create a back button with the specified callback data."""
    return [[Button.inline("⬅️ Back", callback_data)]]


def create_cancel_button(callback_data: str):
    """Create a cancel button with the specified callback data."""
    return [[Button.inline("❌ Cancel", callback_data)]]
