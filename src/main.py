"""
Main entry point for the Telegram File Downloader Bot.
This module can be used both as a script and as an entry point for the installable package.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Import version information first
from . import version

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],  # Only use stdout handler for Docker
)

logger = logging.getLogger(__name__)


def show_version():
    """Display version information."""
    print(f"Telegram File Downloader Bot v{version.__version__}")
    print(f"Author: {version.__author__}")
    print(f"Email: {version.__email__}")
    print(f"Description: {version.__description__}")
    print(f"URL: {version.__url__}")
    print(f"License: {version.__license__}")


async def main():
    """Main function to run the bot."""
    try:
        # Add the src directory to the Python path
        sys.path.insert(0, str(Path(__file__).parent))

        from bot.client import start_client, stop_client, run_until_disconnected
        from core.config import get_config

        # Get configuration (not used but required for initialization)
        get_config()
        logger.info(f"Starting Telegram File Downloader Bot v{version.__version__}...")

        # Start the client
        await start_client()

        # Run until disconnected
        await run_until_disconnected()

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise
    finally:
        # Stop the client
        try:
            await stop_client()
            logger.info("Bot stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping bot: {e}")


def run():
    """Entry point for console scripts."""
    # Check for version flag
    if len(sys.argv) > 1 and sys.argv[1] in ["--version", "-v"]:
        show_version()
        return

    try:
        print(f"Telegram File Downloader Bot v{version.__version__}")
        print(f"Author: {version.__author__}")
        print(f"License: {version.__license__}")
        print("-" * 50)
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Failed to run bot: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run()
