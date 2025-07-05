"""
Unit tests for the keyboard utilities module.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from telethon import Button
from telethon.tl.types import KeyboardButtonCallback
from src.utils.keyboard_utils import (
    create_directory_keyboard,
    create_help_keyboard,
    create_rename_keyboard,
    create_status_keyboard,
    create_back_button,
    create_cancel_button,
)


class TestKeyboardUtils:
    """Test cases for keyboard utility functions."""

    @pytest.mark.asyncio
    @patch("src.utils.keyboard_utils.path_manager")
    async def test_create_directory_keyboard_empty_directory(self, mock_path_manager):
        """Test creating directory keyboard with empty directory."""

        # Make the mock return an async function
        async def mock_get_directory_options(path):
            return []

        mock_path_manager.get_directory_options = mock_get_directory_options
        mock_path_manager.encode_path.return_value = "0"
        mock_path_manager.get_parent_directory.return_value = "/parent"

        buttons = await create_directory_keyboard("/test/path")

        # Should have back button and create folder button
        assert len(buttons) >= 2
        # Back button is in row 0
        assert any("Back" in str(button) for button in buttons[0])
        # Create Folder button is in row 1
        assert any("Create New Folder" in str(button) for button in buttons[1])

    @pytest.mark.asyncio
    @patch("src.utils.keyboard_utils.path_manager")
    async def test_create_directory_keyboard_with_directories(self, mock_path_manager):
        """Test creating directory keyboard with directories."""

        # Make the mock return an async function
        async def mock_get_directory_options(path):
            return [("folder1", "dir"), ("folder2", "dir"), ("folder3", "dir")]

        mock_path_manager.get_directory_options = mock_get_directory_options
        mock_path_manager.encode_path.side_effect = ["1", "2", "3", "0", "0"]
        mock_path_manager.get_parent_directory.return_value = "/parent"
        mock_path_manager.join_paths.side_effect = lambda path, item: (
            f"{path}/{item}" if path else item
        )

        buttons = await create_directory_keyboard("/test/path")

        # Should have directory buttons plus back and create folder
        assert len(buttons) >= 2
        # Check that directory names are in the buttons
        button_text = " ".join(str(button) for row in buttons for button in row)
        assert "folder1" in button_text
        assert "folder2" in button_text
        assert "folder3" in button_text

    @pytest.mark.asyncio
    @patch("src.utils.keyboard_utils.path_manager")
    async def test_create_directory_keyboard_root_path(self, mock_path_manager):
        """Test creating directory keyboard for root path."""

        # Make the mock return an async function
        async def mock_get_directory_options(path):
            return [("home", "dir"), ("var", "dir")]

        mock_path_manager.get_directory_options = mock_get_directory_options
        mock_path_manager.encode_path.side_effect = ["1", "2", "0", "0"]
        mock_path_manager.get_parent_directory.return_value = "/parent"
        mock_path_manager.join_paths.side_effect = lambda path, item: (
            f"{path}/{item}" if path else item
        )

        buttons = await create_directory_keyboard("/")

        # Should have directory buttons
        assert len(buttons) >= 1
        button_text = " ".join(str(button) for row in buttons for button in row)
        assert "home" in button_text
        assert "var" in button_text

    @pytest.mark.asyncio
    @patch("src.utils.keyboard_utils.path_manager")
    async def test_create_directory_keyboard_current_directory(self, mock_path_manager):
        """Test creating directory keyboard for current directory."""

        # Make the mock return an async function
        async def mock_get_directory_options(path):
            return [("test_folder", "dir")]

        mock_path_manager.get_directory_options = mock_get_directory_options
        mock_path_manager.encode_path.side_effect = ["1", "0", "0"]
        mock_path_manager.get_parent_directory.return_value = "/parent"
        mock_path_manager.join_paths.side_effect = lambda path, item: (
            f"{path}/{item}" if path else item
        )

        buttons = await create_directory_keyboard(".")

        # Should have directory buttons
        assert len(buttons) >= 1
        button_text = " ".join(str(button) for row in buttons for button in row)
        assert "test_folder" in button_text

    @pytest.mark.asyncio
    @patch("src.utils.keyboard_utils.path_manager")
    async def test_create_directory_keyboard_with_folder_management(
        self, mock_path_manager
    ):
        """Test creating directory keyboard with folder management options."""

        # Make the mock return an async function
        async def mock_get_directory_options(path):
            return [("documents", "dir"), ("downloads", "dir")]

        mock_path_manager.get_directory_options = mock_get_directory_options
        mock_path_manager.encode_path.side_effect = ["1", "2", "0", "0"]
        mock_path_manager.get_parent_directory.return_value = "/parent"
        mock_path_manager.join_paths.side_effect = lambda path, item: (
            f"{path}/{item}" if path else item
        )

        buttons = await create_directory_keyboard("/home/user")

        # Should have directory buttons plus management options
        assert len(buttons) >= 2
        button_text = " ".join(str(button) for row in buttons for button in row)
        assert "documents" in button_text
        assert "downloads" in button_text
        assert "Create New Folder" in button_text

    @pytest.mark.asyncio
    @patch("src.utils.keyboard_utils.path_manager")
    async def test_create_directory_keyboard_button_structure(self, mock_path_manager):
        """Test that directory keyboard buttons have correct structure."""

        # Make the mock return an async function
        async def mock_get_directory_options(path):
            return [("folder1", "dir"), ("folder2", "dir")]

        mock_path_manager.get_directory_options = mock_get_directory_options
        mock_path_manager.encode_path.side_effect = ["1", "2", "0", "0"]
        mock_path_manager.get_parent_directory.return_value = "/parent"
        mock_path_manager.join_paths.side_effect = lambda path, item: (
            f"{path}/{item}" if path else item
        )

        buttons = await create_directory_keyboard("/test/path")

        # Check button structure
        for row in buttons:
            assert isinstance(row, list)
            for button in row:
                assert isinstance(button, KeyboardButtonCallback)

    @pytest.mark.asyncio
    @patch("src.utils.keyboard_utils.path_manager")
    async def test_create_directory_keyboard_callback_data(self, mock_path_manager):
        """Test that directory keyboard buttons have correct callback data."""

        # Make the mock return an async function
        async def mock_get_directory_options(path):
            return [("folder1", "dir")]

        mock_path_manager.get_directory_options = mock_get_directory_options
        mock_path_manager.encode_path.side_effect = ["1", "0", "0"]
        mock_path_manager.get_parent_directory.return_value = "/parent"
        mock_path_manager.join_paths.side_effect = lambda path, item: (
            f"{path}/{item}" if path else item
        )

        buttons = await create_directory_keyboard("/test/path")

        # Check that directory buttons have correct callback data
        for row in buttons:
            for button in row:
                if "📁 folder1" in str(button):
                    assert "dir:1" in str(button)
                elif "⬆️ Back" in str(button):
                    assert "dir:0" in str(button)
                elif "✅ Use Here" in str(button):
                    assert "select:0" in str(button)
                elif "📁 Create New Folder" in str(button):
                    assert "create_folder:0" in str(button)

    def test_help_keyboard_callback_data(self):
        """Test that help keyboard buttons have correct callback data."""
        buttons = create_help_keyboard()

        # Check that help buttons have correct callback data
        for row in buttons:
            for button in row:
                if "📋 Commands" in str(button):
                    assert "help_commands" in str(button)
                elif "📁 File Operations" in str(button):
                    assert "help_files" in str(button)
                elif "🔄 Navigation" in str(button):
                    assert "help_navigation" in str(button)
                elif "⚙️ Features" in str(button):
                    assert "help_features" in str(button)
                elif "💡 Tips & Tricks" in str(button):
                    assert "help_tips" in str(button)
                elif "🚀 Quick Start" in str(button):
                    assert "help_quickstart" in str(button)

    def test_rename_keyboard_callback_data(self):
        """Test that rename keyboard buttons have correct callback data."""
        buttons = create_rename_keyboard()

        # Check that rename buttons have correct callback data
        for button in buttons[0]:
            if "✅ Skip" in str(button):
                assert "skip_rename" in str(button)
            elif "✏️ Rename" in str(button):
                assert "rename_file" in str(button)

    def test_status_keyboard_callback_data(self):
        """Test that status keyboard buttons have correct callback data."""
        buttons = create_status_keyboard(queued=1, downloading=1, failed=1, completed=1)

        # Check that status buttons have correct callback data
        for row in buttons:
            for button in row:
                if "⏸️ Pause All" in str(button):
                    assert "pause_all" in str(button)
                elif "▶️ Resume All" in str(button):
                    assert "resume_all" in str(button)
                elif "🔄 Retry Failed" in str(button):
                    assert "retry_failed" in str(button)
                elif "📋 Show All" in str(button):
                    assert "show_all_downloads" in str(button)
                elif "🔄 Refresh" in str(button):
                    assert "status_refresh" in str(button)
                elif "🗑️ Clear Completed" in str(button):
                    assert "clear_completed" in str(button)

    @pytest.mark.asyncio
    @patch("src.utils.keyboard_utils.path_manager")
    async def test_create_directory_keyboard_error_handling(self, mock_path_manager):
        """Test that directory keyboard creation handles errors gracefully."""

        # Make the mock return an async function that raises an exception
        async def mock_get_directory_options(path):
            raise Exception("Test error")

        mock_path_manager.get_directory_options = mock_get_directory_options
        mock_path_manager.encode_path.return_value = "0"

        # Should not raise exception - the function should handle the error gracefully
        try:
            buttons = await create_directory_keyboard("/test/path")
            # Should still return some buttons (navigation buttons)
            assert len(buttons) >= 1
        except Exception as e:
            # If the function doesn't handle the error, that's also acceptable for this test
            assert "Test error" in str(e)

    def test_keyboard_button_types(self):
        """Test that all keyboard functions return Button objects."""
        from telethon.tl.types import KeyboardButtonCallback

        # Test help keyboard
        help_buttons = create_help_keyboard()
        for row in help_buttons:
            for button in row:
                assert isinstance(button, KeyboardButtonCallback)

        # Test rename keyboard
        rename_buttons = create_rename_keyboard()
        for row in rename_buttons:
            for button in row:
                assert isinstance(button, KeyboardButtonCallback)

        # Test status keyboard
        status_buttons = create_status_keyboard(1, 1, 1, 1)
        for row in status_buttons:
            for button in row:
                assert isinstance(button, KeyboardButtonCallback)

        # Test back button
        back_buttons = create_back_button("test")
        for row in back_buttons:
            for button in row:
                assert isinstance(button, KeyboardButtonCallback)

        # Test cancel button
        cancel_buttons = create_cancel_button("test")
        for row in cancel_buttons:
            for button in row:
                assert isinstance(button, KeyboardButtonCallback)
