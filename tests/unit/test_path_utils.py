"""
Unit tests for path utilities module.
"""

import pytest
import os
import tempfile
from unittest.mock import patch, Mock
from src.utils.path_utils import PathManager


class TestPathManager:
    """Test cases for PathManager class."""

    def test_path_manager_initialization(self, test_base_download_dir):
        """Test PathManager initialization."""
        with patch.dict(os.environ, {"ROOT_DOWNLOAD_PATH": test_base_download_dir}):
            path_manager = PathManager()
            assert path_manager.base_download_dir == test_base_download_dir
            assert path_manager.path_encodings == {}
            assert path_manager.path_counter == 0

    def test_encode_path_new_path(self, test_base_download_dir):
        """Test encoding a new path."""
        with patch.dict(os.environ, {"ROOT_DOWNLOAD_PATH": test_base_download_dir}):
            path_manager = PathManager()
            encoded = path_manager.encode_path("/test/path")
            assert encoded == "0"
            assert "/test/path" in path_manager.path_encodings

    def test_encode_path_existing_path(self, test_base_download_dir):
        """Test encoding an existing path."""
        with patch.dict(os.environ, {"ROOT_DOWNLOAD_PATH": test_base_download_dir}):
            path_manager = PathManager()
            path_manager.encode_path("/test/path")
            encoded = path_manager.encode_path("/test/path")
            assert encoded == "0"
            assert len(path_manager.path_encodings) == 1

    def test_encode_path_multiple_paths(self, test_base_download_dir):
        """Test encoding multiple paths."""
        with patch.dict(os.environ, {"ROOT_DOWNLOAD_PATH": test_base_download_dir}):
            path_manager = PathManager()
            encoded1 = path_manager.encode_path("/test/path1")
            encoded2 = path_manager.encode_path("/test/path2")
            assert encoded1 == "0"
            assert encoded2 == "1"
            assert len(path_manager.path_encodings) == 2

    def test_decode_path_existing_encoded(self, test_base_download_dir):
        """Test decoding an existing encoded path."""
        with patch.dict(os.environ, {"ROOT_DOWNLOAD_PATH": test_base_download_dir}):
            path_manager = PathManager()
            original_path = "/test/path"
            encoded = path_manager.encode_path(original_path)
            decoded = path_manager.decode_path(encoded)
            assert decoded == original_path

    def test_decode_path_nonexistent_encoded(self, test_base_download_dir):
        """Test decoding a nonexistent encoded path."""
        with patch.dict(os.environ, {"ROOT_DOWNLOAD_PATH": test_base_download_dir}):
            path_manager = PathManager()
            decoded = path_manager.decode_path("nonexistent")
            assert decoded == test_base_download_dir

    def test_decode_path_empty_string(self, test_base_download_dir):
        """Test decoding an empty string."""
        with patch.dict(os.environ, {"ROOT_DOWNLOAD_PATH": test_base_download_dir}):
            path_manager = PathManager()
            decoded = path_manager.decode_path("")
            assert decoded == test_base_download_dir

    def test_sanitize_filename_safe(self, test_base_download_dir):
        """Test sanitizing a safe filename."""
        with patch.dict(os.environ, {"ROOT_DOWNLOAD_PATH": test_base_download_dir}):
            path_manager = PathManager()
            filename = "safe_filename.txt"
            sanitized = path_manager.sanitize_filename(filename)
            assert sanitized == filename

    def test_sanitize_filename_with_slashes(self, test_base_download_dir):
        """Test sanitizing filename with slashes."""
        with patch.dict(os.environ, {"ROOT_DOWNLOAD_PATH": test_base_download_dir}):
            path_manager = PathManager()
            filename = "file/with/slashes.txt"
            sanitized = path_manager.sanitize_filename(filename)
            assert sanitized == "file_with_slashes.txt"

    def test_sanitize_filename_with_backslashes(self, test_base_download_dir):
        """Test sanitizing filename with backslashes."""
        with patch.dict(os.environ, {"ROOT_DOWNLOAD_PATH": test_base_download_dir}):
            path_manager = PathManager()
            filename = "file\\with\\backslashes.txt"
            sanitized = path_manager.sanitize_filename(filename)
            assert sanitized == "file_with_backslashes.txt"

    def test_sanitize_filename_with_whitespace(self, test_base_download_dir):
        """Test sanitizing filename with whitespace."""
        with patch.dict(os.environ, {"ROOT_DOWNLOAD_PATH": test_base_download_dir}):
            path_manager = PathManager()
            filename = "  file with spaces.txt  "
            sanitized = path_manager.sanitize_filename(filename)
            assert sanitized == "file with spaces.txt"

    def test_get_file_extension_with_extension(self, test_base_download_dir):
        """Test getting file extension from filename with extension."""
        with patch.dict(os.environ, {"ROOT_DOWNLOAD_PATH": test_base_download_dir}):
            path_manager = PathManager()
            filename = "test_file.txt"
            extension = path_manager.get_file_extension(filename)
            assert extension == ".txt"

    def test_get_file_extension_without_extension(self, test_base_download_dir):
        """Test getting file extension from filename without extension."""
        with patch.dict(os.environ, {"ROOT_DOWNLOAD_PATH": test_base_download_dir}):
            path_manager = PathManager()
            filename = "test_file"
            extension = path_manager.get_file_extension(filename)
            assert extension == ""

    def test_get_file_extension_multiple_dots(self, test_base_download_dir):
        """Test getting file extension from filename with multiple dots."""
        with patch.dict(os.environ, {"ROOT_DOWNLOAD_PATH": test_base_download_dir}):
            path_manager = PathManager()
            filename = "test.file.txt"
            extension = path_manager.get_file_extension(filename)
            assert extension == ".txt"

    def test_join_paths_simple(self, test_base_download_dir):
        """Test joining simple paths within base directory."""
        with patch.dict(os.environ, {"ROOT_DOWNLOAD_PATH": test_base_download_dir}):
            path_manager = PathManager()
            joined = path_manager.join_paths(
                test_base_download_dir, "dir1", "dir2", "file.txt"
            )
            expected = os.path.join(test_base_download_dir, "dir1", "dir2", "file.txt")
            assert joined == expected

    def test_join_paths_empty_components(self, test_base_download_dir):
        """Test joining paths with empty components within base directory."""
        with patch.dict(os.environ, {"ROOT_DOWNLOAD_PATH": test_base_download_dir}):
            path_manager = PathManager()
            joined = path_manager.join_paths(
                test_base_download_dir, "dir1", "", "file.txt"
            )
            expected = os.path.join(test_base_download_dir, "dir1", "", "file.txt")
            assert joined == expected

    def test_join_paths_outside_bounds(self, test_base_download_dir):
        """Test joining paths that would be outside the base directory."""
        with patch.dict(os.environ, {"ROOT_DOWNLOAD_PATH": test_base_download_dir}):
            path_manager = PathManager()
            joined = path_manager.join_paths("dir1", "dir2", "file.txt")
            # Should return base directory when path is outside bounds
            assert joined == test_base_download_dir

    def test_is_directory_writable_existing_writable(self, test_base_download_dir):
        """Test checking if existing writable directory is writable."""
        with patch.dict(os.environ, {"ROOT_DOWNLOAD_PATH": test_base_download_dir}):
            path_manager = PathManager()
            is_writable = path_manager.is_directory_writable(test_base_download_dir)
            assert is_writable is True

    def test_is_directory_writable_nonexistent(self, test_base_download_dir):
        """Test checking if nonexistent directory is writable."""
        with patch.dict(os.environ, {"ROOT_DOWNLOAD_PATH": test_base_download_dir}):
            path_manager = PathManager()
            is_writable = path_manager.is_directory_writable("/nonexistent/path")
            assert is_writable is False

    def test_is_directory_writable_permission_error(self, test_base_download_dir):
        """Test checking if directory with permission error is writable."""
        with patch.dict(os.environ, {"ROOT_DOWNLOAD_PATH": test_base_download_dir}):
            path_manager = PathManager()
            with patch("os.access", side_effect=PermissionError):
                is_writable = path_manager.is_directory_writable("/test/path")
                assert is_writable is False

    def test_ensure_directory_exists_new_directory(self, test_base_download_dir):
        """Test creating a new directory within base directory."""
        with patch.dict(os.environ, {"ROOT_DOWNLOAD_PATH": test_base_download_dir}):
            path_manager = PathManager()
            new_dir = os.path.join(test_base_download_dir, "new_directory")
            result = path_manager.ensure_directory_exists(new_dir)
            assert result is True
            assert os.path.exists(new_dir)

    def test_ensure_directory_exists_existing_directory(self, test_base_download_dir):
        """Test ensuring an existing directory exists within base directory."""
        with patch.dict(os.environ, {"ROOT_DOWNLOAD_PATH": test_base_download_dir}):
            path_manager = PathManager()
            existing_dir = os.path.join(test_base_download_dir, "existing_directory")
            os.makedirs(existing_dir, exist_ok=True)
            result = path_manager.ensure_directory_exists(existing_dir)
            assert result is True

    def test_ensure_directory_exists_permission_error(self, test_base_download_dir):
        """Test ensuring directory exists with permission error."""
        with patch.dict(os.environ, {"ROOT_DOWNLOAD_PATH": test_base_download_dir}):
            path_manager = PathManager()
            with patch("os.makedirs", side_effect=PermissionError):
                result = path_manager.ensure_directory_exists("/test/path")
                assert result is False

    def test_ensure_directory_exists_outside_bounds(self, test_base_download_dir):
        """Test ensuring directory exists outside base directory."""
        with patch.dict(os.environ, {"ROOT_DOWNLOAD_PATH": test_base_download_dir}):
            path_manager = PathManager()
            result = path_manager.ensure_directory_exists("/outside/path")
            assert result is False

    def test_get_parent_directory_with_parent(self, test_base_download_dir):
        """Test getting parent directory of a path with parent within base directory."""
        with patch.dict(os.environ, {"ROOT_DOWNLOAD_PATH": test_base_download_dir}):
            path_manager = PathManager()
            parent = path_manager.get_parent_directory(
                os.path.join(test_base_download_dir, "test", "path", "file.txt")
            )
            expected = os.path.join(test_base_download_dir, "test", "path")
            assert parent == expected

    def test_get_parent_directory_root(self, test_base_download_dir):
        """Test getting parent directory of root path."""
        with patch.dict(os.environ, {"ROOT_DOWNLOAD_PATH": test_base_download_dir}):
            path_manager = PathManager()
            parent = path_manager.get_parent_directory("/")
            assert parent == test_base_download_dir

    def test_get_parent_directory_current(self, test_base_download_dir):
        """Test getting parent directory of current directory."""
        with patch.dict(os.environ, {"ROOT_DOWNLOAD_PATH": test_base_download_dir}):
            path_manager = PathManager()
            parent = path_manager.get_parent_directory(".")
            assert parent == test_base_download_dir

    def test_get_parent_directory_single_component(self, test_base_download_dir):
        """Test getting parent directory of single component path."""
        with patch.dict(os.environ, {"ROOT_DOWNLOAD_PATH": test_base_download_dir}):
            path_manager = PathManager()
            parent = path_manager.get_parent_directory("file.txt")
            assert parent == test_base_download_dir

    def test_get_parent_directory_outside_bounds(self, test_base_download_dir):
        """Test getting parent directory of path outside base directory."""
        with patch.dict(os.environ, {"ROOT_DOWNLOAD_PATH": test_base_download_dir}):
            path_manager = PathManager()
            parent = path_manager.get_parent_directory("/outside/path/file.txt")
            assert parent == test_base_download_dir

    def test_is_safe_directory_safe_paths(self, test_base_download_dir):
        """Test checking if safe directories are considered safe within base directory."""
        with patch.dict(os.environ, {"ROOT_DOWNLOAD_PATH": test_base_download_dir}):
            path_manager = PathManager()
            safe_paths = [
                test_base_download_dir,
                os.path.join(test_base_download_dir, "home", "user"),
                os.path.join(test_base_download_dir, "tmp", "test"),
                os.path.join(test_base_download_dir, "var", "log"),
            ]

            for path in safe_paths:
                assert path_manager.is_safe_directory(path) is True

    def test_is_safe_directory_dangerous_paths(self, test_base_download_dir):
        """Test checking if dangerous directories are considered unsafe."""
        with patch.dict(os.environ, {"ROOT_DOWNLOAD_PATH": test_base_download_dir}):
            path_manager = PathManager()
            dangerous_paths = [
                "/",
                "/bin",
                "/sbin",
                "/usr",
                "/etc",
                "/var",
                "/tmp",
                "/System",
                "/Library",
                "/Applications",
                "/dev",
                "/proc",
                "/sys",
            ]

            for path in dangerous_paths:
                assert path_manager.is_safe_directory(path) is False

    def test_is_safe_directory_outside_bounds(self, test_base_download_dir):
        """Test checking if directories outside base directory are considered unsafe."""
        with patch.dict(os.environ, {"ROOT_DOWNLOAD_PATH": test_base_download_dir}):
            path_manager = PathManager()
            outside_paths = [
                "/home/user",
                "/tmp/test",
                "/var/log",
                "/usr/local/bin",
                "/opt/applications",
            ]

            for path in outside_paths:
                assert path_manager.is_safe_directory(path) is False

    @pytest.mark.asyncio
    async def test_get_directory_options_success(self, test_base_download_dir):
        """Test getting directory options successfully."""
        with patch.dict(os.environ, {"ROOT_DOWNLOAD_PATH": test_base_download_dir}):
            path_manager = PathManager()
            # Create test directories
            os.makedirs(
                os.path.join(test_base_download_dir, "test_dir1"), exist_ok=True
            )
            os.makedirs(
                os.path.join(test_base_download_dir, "test_dir2"), exist_ok=True
            )

            options = await path_manager.get_directory_options(test_base_download_dir)
            assert len(options) >= 2
            assert any("test_dir1" in option[0] for option in options)
            assert any("test_dir2" in option[0] for option in options)

    @pytest.mark.asyncio
    async def test_get_directory_options_permission_error(self, test_base_download_dir):
        """Test getting directory options with permission error."""
        with patch.dict(os.environ, {"ROOT_DOWNLOAD_PATH": test_base_download_dir}):
            path_manager = PathManager()
            with patch("os.listdir", side_effect=PermissionError):
                options = await path_manager.get_directory_options(
                    test_base_download_dir
                )
                assert options == []

    @pytest.mark.asyncio
    async def test_get_directory_options_os_error(self, test_base_download_dir):
        """Test getting directory options with OS error."""
        with patch.dict(os.environ, {"ROOT_DOWNLOAD_PATH": test_base_download_dir}):
            path_manager = PathManager()
            with patch("os.listdir", side_effect=OSError):
                options = await path_manager.get_directory_options(
                    test_base_download_dir
                )
                assert options == []

    @pytest.mark.asyncio
    async def test_get_directory_options_general_exception(
        self, test_base_download_dir
    ):
        """Test getting directory options with general exception."""
        with patch.dict(os.environ, {"ROOT_DOWNLOAD_PATH": test_base_download_dir}):
            path_manager = PathManager()
            with patch("os.listdir", side_effect=Exception("Test exception")):
                options = await path_manager.get_directory_options(
                    test_base_download_dir
                )
                assert options == []

    @pytest.mark.asyncio
    async def test_get_directory_options_nonexistent_path(self, test_base_download_dir):
        """Test getting directory options for nonexistent path."""
        with patch.dict(os.environ, {"ROOT_DOWNLOAD_PATH": test_base_download_dir}):
            path_manager = PathManager()
            options = await path_manager.get_directory_options("/nonexistent/path")
            assert options == []

    @pytest.mark.asyncio
    async def test_get_directory_options_empty_path(self, test_base_download_dir):
        """Test getting directory options for empty path."""
        with patch.dict(os.environ, {"ROOT_DOWNLOAD_PATH": test_base_download_dir}):
            path_manager = PathManager()
            options = await path_manager.get_directory_options("")
            assert len(options) >= 0  # Should work with base directory

    def test_path_encoding_roundtrip(self, test_base_download_dir):
        """Test encoding and decoding a path maintains the original path."""
        with patch.dict(os.environ, {"ROOT_DOWNLOAD_PATH": test_base_download_dir}):
            path_manager = PathManager()
            original_path = "/test/path/with/many/components"
            encoded = path_manager.encode_path(original_path)
            decoded = path_manager.decode_path(encoded)
            assert decoded == original_path

    def test_multiple_path_encodings(self, test_base_download_dir):
        """Test multiple path encodings work correctly."""
        with patch.dict(os.environ, {"ROOT_DOWNLOAD_PATH": test_base_download_dir}):
            path_manager = PathManager()
            paths = [
                "/path1",
                "/path2",
                "/path3",
                "/path1",
            ]  # Note: path1 appears twice
            encodings = [path_manager.encode_path(path) for path in paths]
            decodings = [path_manager.decode_path(encoding) for encoding in encodings]

            assert decodings[0] == "/path1"
            assert decodings[1] == "/path2"
            assert decodings[2] == "/path3"
            assert decodings[3] == "/path1"  # Should decode to same path
            assert encodings[0] == encodings[3]  # Should have same encoding

    def test_sanitize_filename_edge_cases(self, test_base_download_dir):
        """Test sanitizing filenames with edge cases."""
        with patch.dict(os.environ, {"ROOT_DOWNLOAD_PATH": test_base_download_dir}):
            path_manager = PathManager()
            test_cases = [
                ("", ""),
                ("   ", ""),
                ("file.txt", "file.txt"),
                ("file/with/path.txt", "file_with_path.txt"),
                ("file\\with\\path.txt", "file_with_path.txt"),
                ("file:with:colons.txt", "file:with:colons.txt"),  # Colons are allowed
            ]

            for original, expected in test_cases:
                sanitized = path_manager.sanitize_filename(original)
                assert sanitized == expected

    def test_sanitize_filename_preserves_valid_characters(self, test_base_download_dir):
        """Test that sanitize_filename preserves valid characters."""
        with patch.dict(os.environ, {"ROOT_DOWNLOAD_PATH": test_base_download_dir}):
            path_manager = PathManager()
            filename = "file_with_letters_123_and_symbols!@#$%^&*().txt"
            sanitized = path_manager.sanitize_filename(filename)
            # Should preserve letters, numbers, and most symbols, but replace slashes
            assert "file_with_letters_123_and_symbols!@#$%^&*().txt" in sanitized
            assert "/" not in sanitized
            assert "\\" not in sanitized
