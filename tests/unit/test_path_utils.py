"""
Unit tests for the path utilities module.
"""

import pytest
import os
from unittest.mock import patch, mock_open
from src.utils.path_utils import PathManager


class TestPathManager:
    """Test cases for the PathManager class."""

    def test_path_manager_initialization(self):
        """Test PathManager initialization."""
        path_manager = PathManager()
        assert path_manager.path_encodings == {}
        assert path_manager.path_counter == 0

    def test_encode_path_new_path(self):
        """Test encoding a new path."""
        path_manager = PathManager()
        encoded = path_manager.encode_path("/test/path")
        
        assert encoded == "0"
        assert path_manager.path_encodings["/test/path"] == "0"
        assert path_manager.path_counter == 1

    def test_encode_path_existing_path(self):
        """Test encoding an existing path returns same code."""
        path_manager = PathManager()
        encoded1 = path_manager.encode_path("/test/path")
        encoded2 = path_manager.encode_path("/test/path")
        
        assert encoded1 == encoded2
        assert path_manager.path_counter == 1

    def test_encode_path_multiple_paths(self):
        """Test encoding multiple different paths."""
        path_manager = PathManager()
        encoded1 = path_manager.encode_path("/test/path1")
        encoded2 = path_manager.encode_path("/test/path2")
        encoded3 = path_manager.encode_path("/test/path3")
        
        assert encoded1 == "0"
        assert encoded2 == "1"
        assert encoded3 == "2"
        assert path_manager.path_counter == 3

    def test_decode_path_existing_encoded(self):
        """Test decoding an existing encoded path."""
        path_manager = PathManager()
        original_path = "/test/path"
        encoded = path_manager.encode_path(original_path)
        decoded = path_manager.decode_path(encoded)
        
        assert decoded == original_path

    def test_decode_path_nonexistent_encoded(self):
        """Test decoding a nonexistent encoded path."""
        path_manager = PathManager()
        decoded = path_manager.decode_path("nonexistent")
        
        assert decoded == "."

    def test_decode_path_empty_string(self):
        """Test decoding an empty string."""
        path_manager = PathManager()
        decoded = path_manager.decode_path("")
        
        assert decoded == "."

    def test_sanitize_filename_safe(self):
        """Test sanitizing a safe filename."""
        path_manager = PathManager()
        sanitized = path_manager.sanitize_filename("safe_filename.txt")
        
        assert sanitized == "safe_filename.txt"

    def test_sanitize_filename_with_slashes(self):
        """Test sanitizing filename with slashes."""
        path_manager = PathManager()
        sanitized = path_manager.sanitize_filename("file/with/slashes.txt")
        
        assert sanitized == "file_with_slashes.txt"

    def test_sanitize_filename_with_backslashes(self):
        """Test sanitizing filename with backslashes."""
        path_manager = PathManager()
        sanitized = path_manager.sanitize_filename("file\\with\\backslashes.txt")
        
        assert sanitized == "file_with_backslashes.txt"

    def test_sanitize_filename_with_whitespace(self):
        """Test sanitizing filename with whitespace."""
        path_manager = PathManager()
        sanitized = path_manager.sanitize_filename("  file with spaces.txt  ")
        
        assert sanitized == "file with spaces.txt"

    def test_get_file_extension_with_extension(self):
        """Test getting file extension from filename with extension."""
        path_manager = PathManager()
        extension = path_manager.get_file_extension("file.txt")
        
        assert extension == ".txt"

    def test_get_file_extension_without_extension(self):
        """Test getting file extension from filename without extension."""
        path_manager = PathManager()
        extension = path_manager.get_file_extension("file")
        
        assert extension == ""

    def test_get_file_extension_multiple_dots(self):
        """Test getting file extension from filename with multiple dots."""
        path_manager = PathManager()
        extension = path_manager.get_file_extension("file.backup.txt")
        
        assert extension == ".txt"

    def test_join_paths_simple(self):
        """Test joining simple paths."""
        path_manager = PathManager()
        joined = path_manager.join_paths("dir1", "dir2", "file.txt")
        
        assert joined == os.path.join("dir1", "dir2", "file.txt")

    def test_join_paths_empty_components(self):
        """Test joining paths with empty components."""
        path_manager = PathManager()
        joined = path_manager.join_paths("dir1", "", "file.txt")
        
        assert joined == os.path.join("dir1", "", "file.txt")

    def test_is_directory_writable_existing_writable(self, temp_dir):
        """Test checking if existing writable directory is writable."""
        path_manager = PathManager()
        is_writable = path_manager.is_directory_writable(temp_dir)
        
        assert is_writable is True

    def test_is_directory_writable_nonexistent(self):
        """Test checking if nonexistent directory is writable."""
        path_manager = PathManager()
        is_writable = path_manager.is_directory_writable("/nonexistent/path")
        
        assert is_writable is False

    @patch('os.access')
    def test_is_directory_writable_permission_error(self, mock_access):
        """Test checking directory writability with permission error."""
        mock_access.side_effect = PermissionError("Permission denied")
        path_manager = PathManager()
        is_writable = path_manager.is_directory_writable("/test/path")
        
        assert is_writable is False

    def test_ensure_directory_exists_new_directory(self, temp_dir):
        """Test creating a new directory."""
        path_manager = PathManager()
        new_dir = os.path.join(temp_dir, "new_directory")
        
        result = path_manager.ensure_directory_exists(new_dir)
        
        assert result is True
        assert os.path.exists(new_dir)

    def test_ensure_directory_exists_existing_directory(self, temp_dir):
        """Test ensuring an existing directory exists."""
        path_manager = PathManager()
        existing_dir = os.path.join(temp_dir, "existing_directory")
        os.makedirs(existing_dir, exist_ok=True)
        
        result = path_manager.ensure_directory_exists(existing_dir)
        
        assert result is True
        assert os.path.exists(existing_dir)

    @patch('os.makedirs')
    def test_ensure_directory_exists_permission_error(self, mock_makedirs):
        """Test creating directory with permission error."""
        mock_makedirs.side_effect = PermissionError("Permission denied")
        path_manager = PathManager()
        
        result = path_manager.ensure_directory_exists("/test/path")
        
        assert result is False

    def test_get_parent_directory_with_parent(self):
        """Test getting parent directory of a path with parent."""
        path_manager = PathManager()
        parent = path_manager.get_parent_directory("/test/path/file.txt")
        
        assert parent == "/test/path"

    def test_get_parent_directory_root(self):
        """Test getting parent directory of root path."""
        path_manager = PathManager()
        parent = path_manager.get_parent_directory("/")
        
        assert parent == "."

    def test_get_parent_directory_current(self):
        """Test getting parent directory of current directory."""
        path_manager = PathManager()
        parent = path_manager.get_parent_directory(".")
        
        assert parent == "."

    def test_get_parent_directory_single_component(self):
        """Test getting parent directory of single component path."""
        path_manager = PathManager()
        parent = path_manager.get_parent_directory("file.txt")
        
        assert parent == "."

    def test_is_safe_directory_safe_paths(self):
        """Test checking if safe directories are considered safe."""
        path_manager = PathManager()
        safe_paths = [
            "/home/user",
            "/tmp/test",
            "/var/log",
            "/usr/local/bin",
            "/opt/applications"
        ]
        
        for path in safe_paths:
            assert path_manager.is_safe_directory(path) is True

    def test_is_safe_directory_dangerous_paths(self):
        """Test checking if dangerous directories are considered unsafe."""
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
            "/dev/null",
            "/dev/random"
        ]
        
        for path in dangerous_paths:
            assert path_manager.is_safe_directory(path) is False

    @patch('os.path.isdir')
    @patch('os.path.exists')
    @patch('os.listdir')
    @pytest.mark.asyncio
    async def test_get_directory_options_success(self, mock_listdir, mock_exists, mock_isdir):
        """Test getting directory options successfully."""
        mock_exists.return_value = True
        mock_listdir.return_value = ["folder1", "folder2", "file.txt", ".hidden"]
        # Mock isdir to return True for folders, False for files
        mock_isdir.side_effect = lambda path: any(folder in path for folder in ["folder1", "folder2"])
        
        path_manager = PathManager()
        
        options = await path_manager.get_directory_options("/test/path")
        
        assert len(options) == 2
        assert ("folder1", "dir") in options
        assert ("folder2", "dir") in options
        assert ("file.txt", "dir") not in options  # Not a directory
        assert (".hidden", "dir") not in options  # Hidden directory

    @patch('os.listdir')
    @pytest.mark.asyncio
    async def test_get_directory_options_permission_error(self, mock_listdir):
        """Test getting directory options with permission error."""
        mock_listdir.side_effect = PermissionError("Permission denied")
        path_manager = PathManager()
        
        options = await path_manager.get_directory_options("/test/path")
        
        assert options == []

    @patch('os.listdir')
    @pytest.mark.asyncio
    async def test_get_directory_options_os_error(self, mock_listdir):
        """Test getting directory options with OSError."""
        mock_listdir.side_effect = OSError("OS error")
        path_manager = PathManager()
        
        options = await path_manager.get_directory_options("/test/path")
        
        assert options == []

    @patch('os.listdir')
    @pytest.mark.asyncio
    async def test_get_directory_options_general_exception(self, mock_listdir):
        """Test getting directory options with general Exception."""
        mock_listdir.side_effect = Exception("General error")
        path_manager = PathManager()
        
        options = await path_manager.get_directory_options("/test/path")
        
        assert options == []

    @pytest.mark.asyncio
    async def test_get_directory_options_nonexistent_path(self):
        """Test getting directory options for nonexistent path."""
        path_manager = PathManager()
        
        options = await path_manager.get_directory_options("/nonexistent/path")
        
        assert options == []

    @pytest.mark.asyncio
    async def test_get_directory_options_empty_path(self):
        """Test getting directory options for empty path."""
        path_manager = PathManager()
        
        options = await path_manager.get_directory_options("")
        
        # This should use current directory
        assert isinstance(options, list)

    def test_path_encoding_roundtrip(self):
        """Test that encoding and decoding a path works correctly."""
        path_manager = PathManager()
        original_path = "/very/long/path/with/many/components"
        
        encoded = path_manager.encode_path(original_path)
        decoded = path_manager.decode_path(encoded)
        
        assert decoded == original_path

    def test_multiple_path_encodings(self):
        """Test encoding multiple paths maintains consistency."""
        path_manager = PathManager()
        paths = [
            "/path1",
            "/path2",
            "/path3",
            "/path1",  # Duplicate
            "/path4"
        ]
        
        encodings = [path_manager.encode_path(path) for path in paths]
        
        # Check that duplicates get same encoding
        assert encodings[0] == encodings[3]  # Both "/path1"
        # Check that different paths get different encodings
        assert encodings[0] != encodings[1]
        assert encodings[1] != encodings[2]
        assert encodings[2] != encodings[4]

    def test_sanitize_filename_edge_cases(self):
        """Test sanitize_filename with edge cases and problematic characters."""
        path_manager = PathManager()
        
        # Test various problematic characters
        test_cases = [
            ("file with spaces.txt", "file with spaces.txt"),
            ("file:with:colons.pdf", "file:with:colons.pdf"),
            ("file/with/slashes.doc", "file_with_slashes.doc"),
            ("file\\with\\backslashes.xlsx", "file_with_backslashes.xlsx"),
            ("file with symbols!@#$%^&*().zip", "file with symbols!@#$%^&*().zip"),
            ("file with unicode ñáéíóú.pdf", "file with unicode ñáéíóú.pdf"),
            ("file with multiple   spaces.txt", "file with multiple   spaces.txt"),
            ("file:with:multiple:colons:and:spaces.doc", "file:with:multiple:colons:and:spaces.doc"),
            ("  leading_spaces.txt  ", "leading_spaces.txt"),
            ("file_with_tabs\tand\nnewlines.txt", "file_with_tabs\tand\nnewlines.txt"),
            ("file_with_mixed/slashes\\and:colons.txt", "file_with_mixed_slashes_and:colons.txt"),
            ("", ""),
            ("   ", ""),
            ("file.with.dots.txt", "file.with.dots.txt"),
            ("file-with-dashes.txt", "file-with-dashes.txt"),
            ("file_with_underscores.txt", "file_with_underscores.txt"),
            ("file with (parentheses).txt", "file with (parentheses).txt"),
            ("file with [brackets].txt", "file with [brackets].txt"),
            ("file with {braces}.txt", "file with {braces}.txt"),
            ("file with <angle> brackets.txt", "file with <angle> brackets.txt"),
            ("file with \"quotes\".txt", "file with \"quotes\".txt"),
            ("file with 'single' quotes.txt", "file with 'single' quotes.txt"),
            ("file with |pipe| symbols.txt", "file with |pipe| symbols.txt"),
            ("file with ?question? marks.txt", "file with ?question? marks.txt"),
            ("file with *wildcard* symbols.txt", "file with *wildcard* symbols.txt"),
        ]
        
        for original, expected in test_cases:
            result = path_manager.sanitize_filename(original)
            assert result == expected, f"Failed for '{original}': expected '{expected}', got '{result}'"
            
            # Additional checks for problematic characters
            if result:  # Only check non-empty results
                assert '/' not in result, f"Forward slashes not removed from '{original}'"
                assert '\\' not in result, f"Backslashes not removed from '{original}'"
                assert result.strip() == result, f"Leading/trailing spaces not removed from '{original}'"

    def test_sanitize_filename_preserves_valid_characters(self):
        """Test that sanitize_filename preserves valid characters while removing problematic ones."""
        path_manager = PathManager()
        
        # Test that valid characters are preserved
        valid_filename = "my_file-123 (copy).txt"
        sanitized = path_manager.sanitize_filename(valid_filename)
        
        # Should preserve most characters except slashes
        assert sanitized == valid_filename
        
        # Test with mixed valid and invalid characters
        mixed_filename = "my file/with\\mixed:chars.txt"
        sanitized = path_manager.sanitize_filename(mixed_filename)
        
        # Should remove slashes but preserve other characters
        assert sanitized == "my file_with_mixed:chars.txt"
        assert '/' not in sanitized
        assert '\\' not in sanitized
        assert ':' in sanitized  # Colons should be preserved
        assert ' ' in sanitized  # Spaces should be preserved 