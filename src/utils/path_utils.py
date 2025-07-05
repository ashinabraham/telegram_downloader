"""
Path utilities module for the Telegram File Downloader Bot.
Handles directory navigation, path encoding, and file operations.
"""

import os
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)


class PathManager:
    """Path management class for directory navigation and path encoding."""

    def __init__(self):
        # Path encoding system to avoid callback data size limits
        self.path_encodings = {}
        self.path_counter = 0
        # Get the base download directory from environment variable directly
        self.base_download_dir = os.getenv("ROOT_DOWNLOAD_PATH", "/app/downloads")

    def _is_path_within_bounds(self, path: str) -> bool:
        """Check if a path is within the allowed base download directory."""
        try:
            # Resolve both paths to absolute paths
            abs_path = os.path.abspath(path)
            abs_base = os.path.abspath(self.base_download_dir)
            
            # Check if the path is within the base directory
            return abs_path == abs_base or abs_path.startswith(abs_base + os.sep)
        except Exception as e:
            logger.error(f"Error checking path bounds: {e}")
            return False

    def encode_path(self, path: str) -> str:
        """Encode a path to a short identifier."""
        if path not in self.path_encodings:
            self.path_encodings[path] = str(self.path_counter)
            self.path_counter += 1
        return self.path_encodings[path]

    def decode_path(self, encoded: str) -> str:
        """Decode a short identifier back to a path."""
        for path, code in self.path_encodings.items():
            if code == encoded:
                return path
        return self.base_download_dir

    async def get_directory_options(
        self, current_path: str = ""
    ) -> List[Tuple[str, str]]:
        """Get directory options for the current path."""
        # Ensure current_path is within bounds
        if not self._is_path_within_bounds(current_path):
            current_path = self.base_download_dir
            
        full_path = current_path if current_path else self.base_download_dir
        if not os.path.exists(full_path):
            return []

        items = []
        try:
            for item in os.listdir(full_path):
                item_path = os.path.join(full_path, item)
                if os.path.isdir(item_path):
                    # Skip hidden directories and system directories for safety
                    if not item.startswith(".") and item not in [
                        "System",
                        "Library",
                        "Applications",
                        "bin",
                        "sbin",
                        "dev",
                        "proc",
                        "sys",
                    ]:
                        items.append((item, "dir"))
        except (PermissionError, OSError) as e:
            logger.warning(f"Permission denied or error accessing {full_path}: {e}")
        except Exception as e:
            logger.error(f"Error listing directory {full_path}: {e}")

        return items

    def sanitize_filename(self, filename: str) -> str:
        """Sanitize a filename to be safe for filesystem operations."""
        # Replace problematic characters
        safe_filename = filename.replace("/", "_").replace("\\", "_").strip()
        return safe_filename

    def get_file_extension(self, filename: str) -> str:
        """Get the file extension from a filename."""
        return os.path.splitext(filename)[1]

    def join_paths(self, *paths) -> str:
        """Join multiple path components safely."""
        joined_path = os.path.join(*paths)
        # Ensure the joined path is within bounds
        if not self._is_path_within_bounds(joined_path):
            logger.warning(f"Path {joined_path} is outside allowed bounds, using base directory")
            return self.base_download_dir
        return joined_path

    def is_directory_writable(self, directory: str) -> bool:
        """Check if a directory is writable."""
        try:
            # Ensure directory is within bounds
            if not self._is_path_within_bounds(directory):
                return False
            return os.access(directory, os.W_OK)
        except (OSError, PermissionError):
            return False

    def ensure_directory_exists(self, directory: str) -> bool:
        """Ensure a directory exists, create if necessary."""
        try:
            # Ensure directory is within bounds
            if not self._is_path_within_bounds(directory):
                logger.error(f"Cannot create directory {directory} - outside allowed bounds")
                return False
            os.makedirs(directory, exist_ok=True)
            return True
        except (OSError, PermissionError) as e:
            logger.error(f"Failed to create directory {directory}: {e}")
            return False

    def get_parent_directory(self, path: str) -> str:
        """Get the parent directory of a path."""
        parent = os.path.dirname(path)
        # Handle root path and cases where parent is the same as path
        if not parent or parent == path or parent == "/":
            return self.base_download_dir
        # Ensure parent is within bounds
        if not self._is_path_within_bounds(parent):
            return self.base_download_dir
        return parent

    def is_safe_directory(self, path: str) -> bool:
        """Check if a directory is safe to access (within bounds and not a system directory)."""
        # First check if path is within bounds
        if not self._is_path_within_bounds(path):
            return False
            
        # List of potentially dangerous directories
        dangerous_dirs = {
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
        }

        normalized_path = os.path.normpath(path)
        return normalized_path not in dangerous_dirs and not normalized_path.startswith(
            "/dev/"
        )


# Global path manager instance
path_manager = PathManager()
