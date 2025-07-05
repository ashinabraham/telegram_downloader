"""
Version information for the Telegram File Downloader Bot.
"""

__version__ = "3.1.0-dev"
__author__ = "Ashin Abraham"
__email__ = "ashineabraham@gmail.com"
__description__ = "A Telegram bot for downloading files with progress tracking and directory navigation"
__url__ = "https://github.com/ashinabraham/telegram_downloader"
__license__ = "MIT"

# Version tuple for comparison
VERSION = (3, 1, 0)


def get_version():
    """Get the version string."""
    return __version__


def get_version_tuple():
    """Get the version as a tuple."""
    return VERSION


def is_development():
    """Check if this is a development version."""
    return "dev" in __version__ or "alpha" in __version__ or "beta" in __version__
