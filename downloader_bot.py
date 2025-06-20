import os
import asyncio
import logging
import pathlib
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from telethon import TelegramClient, events, Button
from telethon.errors import SessionPasswordNeededError, MessageNotModifiedError
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Debug: Check if .env file exists and what's loaded
env_path = pathlib.Path('.env')
logger.info(f".env file exists: {env_path.exists()}")
logger.info(f"Current working directory: {pathlib.Path.cwd()}")

# Check what's actually loaded
logger.info(f"API_ID from env: {repr(os.getenv('API_ID'))}")
logger.info(f"API_HASH from env: {repr(os.getenv('API_HASH'))}")
logger.info(f"BOT_TOKEN from env: {repr(os.getenv('BOT_TOKEN'))}")
logger.info(f"ALLOWED_USERS from env: {repr(os.getenv('ALLOWED_USERS'))}")

API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')
ALLOWED_USERS = set(os.getenv('ALLOWED_USERS', '').split(','))

logger.info(f"Loaded environment variables - API_ID: {API_ID}, API_HASH: {'*' * len(API_HASH) if API_HASH else 'None'}, BOT_TOKEN: {'*' * len(BOT_TOKEN) if BOT_TOKEN else 'None'}")
logger.info(f"Allowed users: {ALLOWED_USERS}")

# Validate required environment variables
if not API_ID or not API_HASH or not BOT_TOKEN:
    logger.error("Missing required environment variables")
    raise ValueError('API_ID, API_HASH, and BOT_TOKEN must be set in the environment variables.')

API_ID = int(API_ID)
logger.info(f"API_ID converted to int: {API_ID}")

# Path to save session
SESSION_NAME = 'downloader_bot_session'

# Initialize Telethon client with optimized settings
client = TelegramClient(
    SESSION_NAME, 
    API_ID, 
    API_HASH,
    connection_retries=5,
    retry_delay=1,
    timeout=30,
    request_retries=5,
    flood_sleep_threshold=60
)
logger.info("Telethon client initialized with optimized settings")

# Base directory for downloads - start from current directory
BASE_DOWNLOAD_DIR = '.'

# Track user login state
user_states = {}
# Possible states: None, 'awaiting_phone', 'awaiting_code', 'logged_in', 'selecting_directory', 'awaiting_filename'

# Path encoding system to avoid callback data size limits
path_encodings = {}
path_counter = 0

def encode_path(path):
    """Encode a path to a short identifier"""
    global path_counter
    if path not in path_encodings:
        path_encodings[path] = str(path_counter)
        path_counter += 1
    return path_encodings[path]

def decode_path(encoded):
    """Decode a short identifier back to a path"""
    for path, code in path_encodings.items():
        if code == encoded:
            return path
    return '.'

async def get_directory_options(current_path=''):
    """Get directory options for the current path"""
    full_path = current_path if current_path else '.'
    if not os.path.exists(full_path):
        return []
    
    items = []
    try:
        for item in os.listdir(full_path):
            item_path = os.path.join(full_path, item)
            if os.path.isdir(item_path):
                # Skip hidden directories and system directories for safety
                if not item.startswith('.') and item not in ['System', 'Library', 'Applications', 'bin', 'sbin', 'dev', 'proc', 'sys']:
                    items.append((item, 'dir'))
    except (PermissionError, OSError) as e:
        logger.warning(f"Permission denied or error accessing {full_path}: {e}")
    except Exception as e:
        logger.error(f"Error listing directory {full_path}: {e}")
    
    return items

async def create_directory_keyboard(current_path=''):
    """Create inline keyboard for directory selection"""
    items = await get_directory_options(current_path)
    
    buttons = []
    for item, item_type in items:
        if item_type == 'dir':
            new_path = os.path.join(current_path, item) if current_path else item
            encoded_path = encode_path(new_path)
            buttons.append([Button.inline(f"📁 {item}", f"dir:{encoded_path}")])
    
    # Add navigation buttons
    nav_buttons = []
    
    # Always show Back button if we can go up (even from current directory)
    if current_path:
        # We're in a subdirectory, go to parent
        parent_path = os.path.dirname(current_path) if os.path.dirname(current_path) else '.'
        encoded_parent = encode_path(parent_path)
        nav_buttons.append(Button.inline("⬆️ Back", f"dir:{encoded_parent}"))
    else:
        # We're in current directory (.), go to parent directory
        # Use '..' as the parent path when we're in current directory
        encoded_parent = encode_path('..')
        nav_buttons.append(Button.inline("⬆️ Back", f"dir:{encoded_parent}"))
    
    # Add "Go to Root" button for easier navigation
    if current_path != '/':
        nav_buttons.append(Button.inline("🏠 Root", f"dir:/"))
    
    encoded_current = encode_path(current_path)
    nav_buttons.append(Button.inline("✅ Use Here", f"select:{encoded_current}"))
    
    if nav_buttons:
        buttons.append(nav_buttons)
    
    # Add folder management buttons
    folder_buttons = []
    folder_buttons.append(Button.inline("📁 Create New Folder", f"create_folder:{encoded_current}"))
    if folder_buttons:
        buttons.append(folder_buttons)
    
    return buttons

async def is_logged_in():
    try:
        me = await client.get_me()
        username = getattr(me, 'username', 'Unknown')
        user_id = getattr(me, 'id', 'Unknown')
        logger.info(f"User logged in: {username} ({user_id})")
        return True
    except Exception as e:
        logger.warning(f"Not logged in: {e}")
        return False

@client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    user_id = str(event.sender_id)
    chat_id = event.chat_id
    logger.info(f"Received /start command from user {user_id}")
    
    if user_id not in ALLOWED_USERS:
        logger.warning(f"Unauthorized user {user_id} tried to access the bot")
        await event.respond('You are not allowed to use this bot.')
        return

    logger.info(f"Authorized user {user_id} started the bot")
    
    if not await is_logged_in():
        logger.info(f"User {user_id} needs to login")
        user_states[user_id] = {'state': 'awaiting_phone', 'chat_id': chat_id}
        await event.respond('Please enter your phone number (with country code, e.g. +123456789):')
    else:
        logger.info(f"User {user_id} is already logged in")
        user_states[user_id] = {'state': 'logged_in', 'chat_id': chat_id}
        await event.respond('Forward me a file and I will download it for you.')

@client.on(events.NewMessage(pattern='/help'))
async def help_handler(event):
    user_id = str(event.sender_id)
    logger.info(f"Received /help command from user {user_id}")
    
    if user_id not in ALLOWED_USERS:
        logger.warning(f"Unauthorized user {user_id} tried to access help")
        await event.respond('You are not allowed to use this bot.')
        return

    help_text = """
🤖 **Telegram File Downloader Bot - Help Menu**

Choose a category below to learn more about specific features:
"""
    
    buttons = [
        [Button.inline("📋 Commands", "help_commands")],
        [Button.inline("📁 File Operations", "help_files")],
        [Button.inline("🔄 Navigation", "help_navigation")],
        [Button.inline("⚙️ Features", "help_features")],
        [Button.inline("💡 Tips & Tricks", "help_tips")],
        [Button.inline("🚀 Quick Start", "help_quickstart")]
    ]
    
    await event.respond(help_text, buttons=buttons)

@client.on(events.CallbackQuery())
async def callback_handler(event):
    """Handle button callbacks for directory selection and help"""
    user_id = str(event.sender_id)
    if user_id not in ALLOWED_USERS:
        return
    
    data = event.data.decode()
    logger.info(f"User {user_id} clicked button: {data}")
    
    try:
        if data.startswith('dir:'):
            # Directory navigation
            encoded_path = data[4:]  # Remove 'dir:' prefix
            path = decode_path(encoded_path)
            buttons = await create_directory_keyboard(path)
            await event.edit(
                f"Select directory to save file:\nCurrent: {path}",
                buttons=buttons
            )
        
        elif data.startswith('select:'):
            # Directory selected
            encoded_path = data[7:]  # Remove 'select:' prefix
            path = decode_path(encoded_path)
            user_states[user_id]['selected_dir'] = path
            user_states[user_id]['state'] = 'awaiting_filename'
            
            display_path = path if path else '.'
            await event.edit(
                f"Directory selected: {display_path}\n\n"
                "Do you want to rename the file?",
                buttons=[
                    [Button.inline("✅ Skip", "skip_rename")],
                    [Button.inline("✏️ Rename", "rename_file")]
                ]
            )
        
        elif data == 'skip_rename':
            # Skip renaming, use original filename
            logger.info(f"User {user_id} chose to skip renaming")
            await download_file(event, user_id)
        
        elif data == 'rename_file':
            # User wants to rename, ask for new filename
            logger.info(f"User {user_id} chose to rename file")
            user_states[user_id]['state'] = 'awaiting_filename'
            await event.edit(
                "Please enter the new filename (including extension):"
            )
        
        elif data.startswith('create_folder:'):
            # Create new folder
            encoded_path = data[14:]  # Remove 'create_folder:' prefix
            path = decode_path(encoded_path)
            user_states[user_id]['state'] = 'awaiting_folder_name'
            user_states[user_id]['create_folder_path'] = path
            
            display_path = path if path else '.'
            await event.edit(
                f"Creating new folder in: {display_path}\n\n"
                "Please enter the name for the new folder:",
                buttons=[[Button.inline("⬅️ Cancel", f"dir:{encoded_path}")]]
            )
        
        # Help section callbacks
        elif data == 'help_commands':
            help_text = """
📋 **Available Commands:**

• `/start` - Start the bot and begin file download process
• `/help` - Show this help menu with all available commands
• `/status` - Check the status of your current downloads

Each command serves a specific purpose in the file download workflow.
"""
            buttons = [[Button.inline("⬅️ Back to Help", "help_back")]]
            await event.edit(help_text, buttons=buttons)
        
        elif data == 'help_files':
            help_text = """
📁 **File Operations:**

• **Forward any file** (up to 2GB) to the bot
• **Navigate directories** using interactive inline buttons
• **Rename files** before downloading (optional)
• **Download to any directory** on your system
• **Support for all file types**: documents, photos, videos, audio, voice messages

The bot handles files of any type and size up to 2GB.
"""
            buttons = [[Button.inline("⬅️ Back to Help", "help_back")]]
            await event.edit(help_text, buttons=buttons)
        
        elif data == 'help_navigation':
            help_text = """
🔄 **Directory Navigation:**

• **⬆️ Back** - Go to parent directory
• **🏠 Root** - Go to system root directory
• **✅ Use Here** - Select current directory for download
• **📁 Folder names** - Click to navigate into directories

You can navigate up to parent directories indefinitely and access any directory on your system.
"""
            buttons = [[Button.inline("⬅️ Back to Help", "help_back")]]
            await event.edit(help_text, buttons=buttons)
        
        elif data == 'help_features':
            help_text = """
⚙️ **Bot Features:**

• **Parallel downloads** - Multiple files download simultaneously
• **Real-time progress** - Live updates with percentage, speed, and ETA
• **Progress tracking** - Monitor download status and queue
• **Session management** - Automatic login and session persistence
• **User authentication** - Secure access control
• **File type support** - All Telegram file types supported
• **Directory navigation** - Full system directory access
"""
            buttons = [[Button.inline("⬅️ Back to Help", "help_back")]]
            await event.edit(help_text, buttons=buttons)
        
        elif data == 'help_tips':
            help_text = """
💡 **Tips & Tricks:**

• **Navigate freely** - You can go up parent directories indefinitely
• **Original names** - Files keep original names unless you rename them
• **Progress monitoring** - Use /status to check download queue
• **Speed optimization** - Bot uses optimized download settings
• **Session persistence** - Login once, use multiple times
• **Safe navigation** - System directories are filtered for safety
"""
            buttons = [[Button.inline("⬅️ Back to Help", "help_back")]]
            await event.edit(help_text, buttons=buttons)
        
        elif data == 'help_quickstart':
            help_text = """
🚀 **Quick Start Guide:**

1. **Start the bot** - Send `/start`
2. **Forward a file** - Send any file up to 2GB
3. **Choose directory** - Navigate to where you want to save
4. **Select location** - Click "✅ Use Here"
5. **Rename (optional)** - Choose to rename or skip
6. **Download** - File downloads with progress updates

That's it! Your file will be downloaded to the selected location.
"""
            buttons = [[Button.inline("⬅️ Back to Help", "help_back")]]
            await event.edit(help_text, buttons=buttons)
        
        elif data == 'help_back':
            # Return to main help menu
            help_text = """
🤖 **Telegram File Downloader Bot - Help Menu**

Choose a category below to learn more about specific features:
"""
            buttons = [
                [Button.inline("📋 Commands", "help_commands")],
                [Button.inline("📁 File Operations", "help_files")],
                [Button.inline("🔄 Navigation", "help_navigation")],
                [Button.inline("⚙️ Features", "help_features")],
                [Button.inline("💡 Tips & Tricks", "help_tips")],
                [Button.inline("🚀 Quick Start", "help_quickstart")]
            ]
            await event.edit(help_text, buttons=buttons)
        
        # Status manager callbacks
        elif data == 'status_refresh':
            # Refresh status display
            user_downloads = download_queue.get(user_id, [])
            if not user_downloads:
                await event.edit(
                    "📊 **Download Manager**\n\n"
                    "No downloads in queue.\n"
                    "Forward a file to start downloading!",
                    buttons=[[Button.inline("🔄 Refresh", "status_refresh")]]
                )
                return
            
            # Count downloads by status
            queued = sum(1 for task in user_downloads if task.status == "queued")
            downloading = sum(1 for task in user_downloads if task.status == "downloading")
            completed = sum(1 for task in user_downloads if task.status == "completed")
            failed = sum(1 for task in user_downloads if task.status == "failed")
            
            # Calculate total progress
            total_downloaded = sum(task.downloaded_bytes for task in user_downloads if task.status == "downloading")
            total_size = sum(task.total_bytes for task in user_downloads if task.status == "downloading")
            overall_progress = (total_downloaded / total_size * 100) if total_size > 0 else 0
            
            status_text = f"""
📊 **Download Manager** (Refreshed)

📈 **Overall Progress:** {overall_progress:.1f}%
📦 **Queue Status:**
• ⏳ Queued: {queued}
• 📥 Downloading: {downloading}
• ✅ Completed: {completed}
• ❌ Failed: {failed}

📋 **Active Downloads:**
"""
            
            # Show active downloads (downloading and queued)
            active_downloads = [task for task in user_downloads if task.status in ["queued", "downloading"]]
            for i, task in enumerate(active_downloads[:5], 1):  # Show max 5 active downloads
                filename = os.path.basename(task.save_path)
                if task.status == "queued":
                    status_text += f"{i}. ⏳ **{filename}** - Waiting in queue\n"
                elif task.status == "downloading":
                    progress = (task.downloaded_bytes / task.total_bytes * 100) if task.total_bytes > 0 else 0
                    downloaded_mb = task.downloaded_bytes / (1024*1024)
                    total_mb = task.total_bytes / (1024*1024)
                    elapsed_time = time.time() - task.start_time
                    speed = task.downloaded_bytes / elapsed_time if elapsed_time > 0 else 0
                    speed_mb = speed / (1024*1024)
                    eta_seconds = (task.total_bytes - task.downloaded_bytes) / speed if speed > 0 else 0
                    eta_minutes = eta_seconds / 60
                    
                    status_text += f"{i}. 📥 **{filename}**\n"
                    status_text += f"   Progress: {progress:.1f}%\n"
                    status_text += f"   Speed: {speed_mb:.1f} MB/s\n"
                    status_text += f"   Downloaded: {downloaded_mb:.1f} MB / {total_mb:.1f} MB\n"
                    status_text += f"   ETA: {eta_minutes:.1f} min\n\n"
            
            if len(active_downloads) > 5:
                status_text += f"... and {len(active_downloads) - 5} more downloads\n"
            
            # Create interactive buttons
            buttons = []
            action_row = []
            if downloading > 0:
                action_row.append(Button.inline("⏸️ Pause All", "pause_all"))
            if queued > 0:
                action_row.append(Button.inline("▶️ Resume All", "resume_all"))
            if failed > 0:
                action_row.append(Button.inline("🔄 Retry Failed", "retry_failed"))
            if action_row:
                buttons.append(action_row)
            
            nav_row = []
            if completed > 0 or failed > 0:
                nav_row.append(Button.inline("📋 Show All", "show_all_downloads"))
            nav_row.append(Button.inline("🔄 Refresh", "status_refresh"))
            nav_row.append(Button.inline("🗑️ Clear Completed", "clear_completed"))
            if nav_row:
                buttons.append(nav_row)
            
            await event.edit(status_text, buttons=buttons)
        
        elif data == 'show_all_downloads':
            # Show all downloads including completed and failed
            user_downloads = download_queue.get(user_id, [])
            if not user_downloads:
                await event.edit("No downloads found.")
                return
            
            status_text = "📋 **All Downloads:**\n\n"
            
            for i, task in enumerate(user_downloads, 1):
                filename = os.path.basename(task.save_path)
                if task.status == "queued":
                    status_text += f"{i}. ⏳ **{filename}** - Waiting in queue\n"
                elif task.status == "downloading":
                    progress = (task.downloaded_bytes / task.total_bytes * 100) if task.total_bytes > 0 else 0
                    downloaded_mb = task.downloaded_bytes / (1024*1024)
                    total_mb = task.total_bytes / (1024*1024)
                    elapsed_time = time.time() - task.start_time
                    speed = task.downloaded_bytes / elapsed_time if elapsed_time > 0 else 0
                    speed_mb = speed / (1024*1024)
                    eta_seconds = (task.total_bytes - task.downloaded_bytes) / speed if speed > 0 else 0
                    eta_minutes = eta_seconds / 60
                    
                    status_text += f"{i}. 📥 **{filename}**\n"
                    status_text += f"   Progress: {progress:.1f}%\n"
                    status_text += f"   Speed: {speed_mb:.1f} MB/s\n"
                    status_text += f"   Downloaded: {downloaded_mb:.1f} MB / {total_mb:.1f} MB\n"
                    status_text += f"   ETA: {eta_minutes:.1f} min\n\n"
                elif task.status == "completed":
                    status_text += f"{i}. ✅ **{filename}** - Completed\n"
                elif task.status == "failed":
                    error_msg = task.error if task.error else "Unknown error"
                    status_text += f"{i}. ❌ **{filename}** - Failed: {error_msg}\n"
            
            buttons = [[Button.inline("⬅️ Back to Status", "status_refresh")]]
            await event.edit(status_text, buttons=buttons)
        
        elif data == 'clear_completed':
            # Remove completed downloads from queue
            user_downloads = download_queue.get(user_id, [])
            if user_downloads:
                # Keep only non-completed downloads
                download_queue[user_id] = [task for task in user_downloads if task.status != "completed"]
                await event.answer("✅ Completed downloads cleared!")
                # Refresh the status display
                await event.edit(
                    "📊 **Download Manager**\n\n"
                    "✅ Completed downloads have been cleared from the queue.",
                    buttons=[[Button.inline("🔄 Refresh", "status_refresh")]]
                )
            else:
                await event.answer("No downloads to clear.")
        
        elif data == 'pause_all':
            # Pause all downloading tasks (this would require implementing pause functionality)
            await event.answer("⏸️ Pause functionality coming soon!")
        
        elif data == 'resume_all':
            # Resume all paused tasks (this would require implementing resume functionality)
            await event.answer("▶️ Resume functionality coming soon!")
        
        elif data == 'retry_failed':
            # Retry all failed downloads
            user_downloads = download_queue.get(user_id, [])
            failed_tasks = [task for task in user_downloads if task.status == "failed"]
            
            if not failed_tasks:
                await event.answer("No failed downloads to retry.")
                return
            
            retry_count = 0
            for task in failed_tasks:
                # Reset task status and restart download
                task.status = "queued"
                task.downloaded_bytes = 0
                task.error = None
                task.start_time = time.time()
                retry_count += 1
                # Restart the download
                asyncio.create_task(download_with_progress(task))
            
            await event.answer(f"🔄 Retrying {retry_count} failed downloads...")
            # Refresh the status display
            await event.edit(
                f"📊 **Download Manager**\n\n"
                f"🔄 Retrying {retry_count} failed downloads...",
                buttons=[[Button.inline("🔄 Refresh", "status_refresh")]]
            )
    
    except MessageNotModifiedError:
        # Message content is the same, ignore this error
        pass
    except Exception as e:
        logger.error(f"Error in callback handler: {e}")
        error_msg = f"❌ **Bot Error!**\n\nAn error occurred while processing your request.\n\n**Error:** {str(e)}\n\nPlease try again or use /start to restart."
        await send_notification(user_id, error_msg)
        await event.answer("An error occurred. Please try again.")

@client.on(events.NewMessage())
async def message_handler(event):
    user_id = str(event.sender_id)
    chat_id = event.chat_id
    if user_id not in ALLOWED_USERS:
        return
    
    # Update chat_id in user state
    if user_id in user_states:
        user_states[user_id]['chat_id'] = chat_id
    
    state = user_states.get(user_id, {}).get('state')
    logger.info(f"User {user_id} sent message in state: {state}")
    
    # Handle users who haven't started the bot
    if state is None:
        await event.respond("Please use /start to begin using the bot.")
        return
    
    if state == 'awaiting_phone':
        phone = event.raw_text.strip()
        logger.info(f"User {user_id} provided phone number: {phone}")
        user_states[user_id] = {'state': 'awaiting_code', 'phone': phone, 'chat_id': chat_id}
        try:
            await client.send_code_request(phone)
            logger.info(f"Code request sent to {phone}")
            await event.respond('A code has been sent to your Telegram. Please enter the code:')
        except Exception as e:
            logger.error(f"Failed to send code to {phone}: {e}")
            error_msg = f"❌ **Login Error!**\n\nFailed to send verification code to {phone}.\n\n**Error:** {str(e)}\n\nPlease try again with a valid phone number."
            await send_notification(user_id, error_msg)
            user_states[user_id] = {'state': 'awaiting_phone', 'chat_id': chat_id}
            await event.respond(f'Failed to send code: {e}. Please enter your phone number again:')
    
    elif state == 'awaiting_code':
        code = event.raw_text.strip()
        phone = user_states[user_id]['phone']
        logger.info(f"User {user_id} provided code for {phone}")
        try:
            await client.sign_in(phone, code)
            logger.info(f"User {user_id} successfully signed in")
            user_states[user_id] = {'state': 'logged_in', 'chat_id': chat_id}
            await event.respond('Login successful! Forward me a file and I will download it for you.')
        except SessionPasswordNeededError:
            logger.info(f"User {user_id} needs 2FA password")
            user_states[user_id] = {'state': 'awaiting_2fa', 'phone': phone, 'code': code, 'chat_id': chat_id}
            await event.respond('Two-step verification is enabled. Please enter your password:')
        except Exception as e:
            logger.error(f"Login failed for user {user_id}: {e}")
            error_msg = f"❌ **Login Error!**\n\nFailed to verify code for {phone}.\n\n**Error:** {str(e)}\n\nPlease try again with the correct code."
            await send_notification(user_id, error_msg)
            user_states[user_id] = {'state': 'awaiting_phone', 'chat_id': chat_id}
            await event.respond(f'Login failed: {e}. Please enter your phone number again:')
    
    elif state == 'awaiting_2fa':
        password = event.raw_text.strip()
        phone = user_states[user_id]['phone']
        code = user_states[user_id]['code']
        logger.info(f"User {user_id} provided 2FA password")
        try:
            await client.sign_in(phone, code, password=password)
            logger.info(f"User {user_id} successfully signed in with 2FA")
            user_states[user_id] = {'state': 'logged_in', 'chat_id': chat_id}
            await event.respond('Login successful! Forward me a file and I will download it for you.')
        except Exception as e:
            logger.error(f"2FA failed for user {user_id}: {e}")
            error_msg = f"❌ **2FA Error!**\n\nFailed to verify 2FA password.\n\n**Error:** {str(e)}\n\nPlease try again with the correct password."
            await send_notification(user_id, error_msg)
            user_states[user_id] = {'state': 'awaiting_phone', 'chat_id': chat_id}
            await event.respond(f'2FA failed: {e}. Please enter your phone number again:')
    
    elif state == 'awaiting_filename':
        # User provided new filename
        new_filename = event.raw_text.strip()
        if not new_filename:
            await event.respond("Please provide a valid filename or click 'Skip' to use the original name.")
            return
        
        # Download the file
        await download_file(event, user_id, new_filename)
    
    elif state == 'awaiting_folder_name':
        # User provided new folder name
        folder_name = event.raw_text.strip()
        if not folder_name:
            await event.respond("Please provide a valid folder name or click 'Cancel' to go back.")
            return
        
        # Sanitize folder name
        safe_folder_name = folder_name.replace('/', '_').replace('\\', '_').strip()
        if not safe_folder_name:
            await event.respond("Invalid folder name. Please use only letters, numbers, and spaces.")
            return
        
        # Get the path where folder should be created
        create_path = user_states[user_id]['create_folder_path']
        new_folder_path = os.path.join(create_path, safe_folder_name)
        
        try:
            # Create the folder
            os.makedirs(new_folder_path, exist_ok=True)
            logger.info(f"User {user_id} created folder: {new_folder_path}")
            
            # Navigate to the newly created folder
            encoded_new_path = encode_path(new_folder_path)
            buttons = await create_directory_keyboard(new_folder_path)
            
            await event.respond(
                f"✅ Folder '{safe_folder_name}' created successfully!\n\n"
                f"Current location: {new_folder_path}",
                buttons=buttons
            )
            
            # Reset user state
            user_states[user_id] = {'state': 'logged_in', 'chat_id': chat_id}
            
        except PermissionError:
            error_msg = f"❌ **Permission Error!**\n\nCannot create folder: {safe_folder_name}\n\n**Error:** Permission denied\n\nPlease choose a different location or check permissions."
            await send_notification(user_id, error_msg)
            await event.respond(f"❌ Permission denied: Cannot create folder {safe_folder_name}")
            user_states[user_id] = {'state': 'logged_in', 'chat_id': chat_id}
        except Exception as e:
            logger.error(f"Error creating folder: {e}")
            await event.respond(f"❌ Error creating folder: {e}")
            user_states[user_id] = {'state': 'logged_in', 'chat_id': chat_id}
    
    elif state == 'logged_in':
        # Check if message contains a file
        if event.message.media:
            logger.info(f"User {user_id} forwarded a file")
            user_states[user_id]['file_message'] = event.message
            user_states[user_id]['state'] = 'selecting_directory'
            
            # Show directory selection
            buttons = await create_directory_keyboard()
            await event.respond(
                "Select directory to save the file:",
                buttons=buttons
            )
        else:
            # Only respond to text messages that are commands or specific requests
            message_text = event.raw_text.strip().lower() if event.raw_text else ""
            
            # Ignore empty messages or non-command messages to prevent spam
            if not message_text or message_text in ['/start', '/help', '/status']:
                # These commands are handled by their specific handlers
                return
            else:
                # Only respond to actual requests, not random messages
                logger.info(f"User {user_id} sent message while logged in: {event.raw_text[:50]}...")
                # Don't respond to every message to prevent flood wait
                return
    
    else:
        logger.warning(f"User {user_id} in unknown state: {state}")
        await event.respond("Please use /start to begin using the bot.")

# Download management
download_queue = {}
download_progress = {}
download_executor = ThreadPoolExecutor(max_workers=5)  # Increased from 3 to 5 parallel downloads

# Rate limiting for notifications
notification_cooldowns = {}  # Track last notification time per user
NOTIFICATION_COOLDOWN = 30  # Minimum seconds between notifications per user

# Download optimization settings
DOWNLOAD_CHUNK_SIZE = 1024 * 1024  # 1MB chunks (increased from default 256KB)
PROGRESS_UPDATE_INTERVAL = 5.0  # Update progress every 5 seconds (increased from 1 second)
MAX_CONCURRENT_DOWNLOADS = 5

class DownloadTask:
    def __init__(self, user_id, file_message, save_path, progress_message=None):
        self.user_id = user_id
        self.file_message = file_message
        self.save_path = save_path
        self.progress_message = progress_message
        self.start_time = time.time()
        self.downloaded_bytes = 0
        self.total_bytes = 0
        self.status = "queued"  # queued, downloading, completed, failed
        self.error = None
        self.last_progress_update = 0
        self.progress_lock = threading.Lock()

async def update_progress_message(task, progress_text):
    """Update the progress message in Telegram with throttling and better error handling"""
    try:
        current_time = time.time()
        # Only update if enough time has passed since last update
        if current_time - task.last_progress_update >= PROGRESS_UPDATE_INTERVAL:
            if task.progress_message:
                await task.progress_message.edit(progress_text)
                task.last_progress_update = current_time
    except MessageNotModifiedError:
        # Message content is the same, ignore this error
        pass
    except Exception as e:
        error_msg = str(e)
        if "wait of" in error_msg and "seconds is required" in error_msg:
            # Rate limit error - extract wait time and log it
            logger.warning(f"Rate limit hit for progress updates. Error: {error_msg}")
            # Don't update last_progress_update to prevent immediate retry
        else:
            logger.error(f"Failed to update progress message: {e}")

async def send_rate_limited_notification(user_id, message):
    """Send a notification to user with rate limiting to prevent flood wait"""
    try:
        current_time = time.time()
        last_notification = notification_cooldowns.get(user_id, 0)
        
        # Check if enough time has passed since last notification
        if current_time - last_notification < NOTIFICATION_COOLDOWN:
            logger.info(f"Rate limiting notification for user {user_id}")
            return
        
        chat_id = user_states.get(user_id, {}).get('chat_id')
        if chat_id:
            await client.send_message(chat_id, message)
            notification_cooldowns[user_id] = current_time
            logger.info(f"Sent notification to user {user_id}")
    except Exception as e:
        logger.error(f"Failed to send notification to user {user_id}: {e}")

async def send_notification(user_id, message, is_management_command=False):
    """Send a notification to user with optional rate limiting"""
    try:
        # Skip rate limiting for management commands
        if is_management_command:
            chat_id = user_states.get(user_id, {}).get('chat_id')
            if chat_id:
                await client.send_message(chat_id, message)
                logger.info(f"Sent management notification to user {user_id}")
        else:
            # Use rate limiting for regular notifications
            await send_rate_limited_notification(user_id, message)
    except Exception as e:
        logger.error(f"Failed to send notification to user {user_id}: {e}")

async def download_with_progress(task):
    """Download file with optimized progress tracking"""
    try:
        task.status = "downloading"
        
        # Get file size
        if hasattr(task.file_message.media, 'document') and task.file_message.media.document:
            task.total_bytes = task.file_message.media.document.size
        else:
            task.total_bytes = 0
        
        # Get chat_id from user_states
        chat_id = user_states.get(task.user_id, {}).get('chat_id')
        if not chat_id:
            logger.error(f"No chat_id found for user {task.user_id}")
            return
        
        # Create progress message
        progress_text = f"📥 Starting download...\nFile: {os.path.basename(task.save_path)}\nSize: {task.total_bytes / (1024*1024):.1f} MB"
        task.progress_message = await client.send_message(chat_id, progress_text)
        
        # Optimized progress callback with throttling
        def progress_callback(received_bytes, total_bytes):
            with task.progress_lock:
                task.downloaded_bytes = received_bytes
                task.total_bytes = total_bytes
                
                # Calculate progress
                if total_bytes > 0:
                    progress_percent = (received_bytes / total_bytes) * 100
                    elapsed_time = time.time() - task.start_time
                    speed = received_bytes / elapsed_time if elapsed_time > 0 else 0
                    
                    # Only update progress message periodically to reduce overhead
                    current_time = time.time()
                    if current_time - task.last_progress_update >= PROGRESS_UPDATE_INTERVAL:
                        progress_text = (
                            f"📥 Downloading...\n"
                            f"File: {os.path.basename(task.save_path)}\n"
                            f"Progress: {progress_percent:.1f}%\n"
                            f"Speed: {speed / (1024*1024):.1f} MB/s\n"
                            f"Downloaded: {received_bytes / (1024*1024):.1f} MB / {total_bytes / (1024*1024):.1f} MB\n"
                            f"ETA: {((total_bytes - received_bytes) / speed / 60):.1f} min" if speed > 0 else "Calculating..."
                        )
                        
                        # Update progress message (non-blocking)
                        asyncio.create_task(update_progress_message(task, progress_text))
        
        # Download with optimized settings
        downloaded_file = await client.download_media(
            task.file_message.media, 
            task.save_path,
            progress_callback=progress_callback
        )
        
        if downloaded_file:
            task.status = "completed"
            total_time = time.time() - task.start_time
            avg_speed = task.total_bytes / total_time if total_time > 0 else 0
            
            completion_text = (
                f"✅ Download completed!\n"
                f"File: {os.path.basename(task.save_path)}\n"
                f"Path: {downloaded_file}\n"
                f"Time: {total_time:.1f}s\n"
                f"Avg Speed: {avg_speed / (1024*1024):.1f} MB/s"
            )
            await update_progress_message(task, completion_text)
            
            # Send completion notification to user
            try:
                chat_id = user_states.get(task.user_id, {}).get('chat_id')
                if chat_id:
                    notification_text = (
                        f"🎉 **Download Complete!**\n\n"
                        f"📁 **File:** {os.path.basename(task.save_path)}\n"
                        f"📂 **Location:** {downloaded_file}\n"
                        f"⏱️ **Time:** {total_time:.1f} seconds\n"
                        f"🚀 **Avg Speed:** {avg_speed / (1024*1024):.1f} MB/s\n"
                        f"📊 **Size:** {task.total_bytes / (1024*1024):.1f} MB"
                    )
                    await send_notification(task.user_id, notification_text)
            except Exception as e:
                logger.error(f"Failed to send completion notification: {e}")
            
            logger.info(f"Download completed: {downloaded_file} in {total_time:.1f}s")
        else:
            task.status = "failed"
            task.error = "Download failed"
            await update_progress_message(task, f"❌ Download failed: {os.path.basename(task.save_path)}")
            
            # Send failure notification to user
            try:
                chat_id = user_states.get(task.user_id, {}).get('chat_id')
                if chat_id:
                    notification_text = (
                        f"❌ **Download Failed!**\n\n"
                        f"📁 **File:** {os.path.basename(task.save_path)}\n"
                        f"🔍 **Error:** Download failed\n\n"
                        f"Use /status to retry failed downloads."
                    )
                    await send_notification(task.user_id, notification_text)
            except Exception as e:
                logger.error(f"Failed to send failure notification: {e}")
            
            logger.error("Download failed")
            
    except Exception as e:
        task.status = "failed"
        task.error = str(e)
        error_text = f"❌ Download error: {os.path.basename(task.save_path)}\nError: {str(e)}"
        await update_progress_message(task, error_text)
        
        # Send error notification to user
        try:
            chat_id = user_states.get(task.user_id, {}).get('chat_id')
            if chat_id:
                notification_text = (
                    f"❌ **Download Error!**\n\n"
                    f"📁 **File:** {os.path.basename(task.save_path)}\n"
                    f"🔍 **Error:** {str(e)}\n\n"
                    f"Use /status to retry failed downloads."
                )
                await send_notification(task.user_id, notification_text)
        except Exception as notify_e:
            logger.error(f"Failed to send error notification: {notify_e}")
        
        logger.error(f"Download error: {e}")

async def queue_download(user_id, file_message, save_path):
    """Add download to queue and start if possible with optimized concurrency"""
    task = DownloadTask(user_id, file_message, save_path)
    download_queue[user_id] = download_queue.get(user_id, []) + [task]
    
    # Start download in background with optimized executor
    asyncio.create_task(download_with_progress(task))
    
    return task

async def download_file(event, user_id, filename=None):
    """Queue file for download instead of downloading immediately"""
    try:
        file_message = user_states[user_id]['file_message']
        selected_dir = user_states[user_id]['selected_dir']
        chat_id = user_states[user_id].get('chat_id', event.chat_id)  # Fallback to event chat_id
        
        # Determine save path - use full system path
        save_dir = selected_dir if selected_dir else '.'
        
        # Check if directory exists and is writable
        if not os.path.exists(save_dir):
            try:
                os.makedirs(save_dir, exist_ok=True)
            except PermissionError:
                error_msg = f"❌ **Permission Error!**\n\nCannot create directory: {save_dir}\n\n**Error:** Permission denied\n\nPlease choose a different location or check permissions."
                await send_notification(user_id, error_msg)
                await event.respond(f"❌ Permission denied: Cannot create directory {save_dir}")
                user_states[user_id] = {'state': 'logged_in', 'chat_id': chat_id}
                return
        elif not os.access(save_dir, os.W_OK):
            error_msg = f"❌ **Permission Error!**\n\nCannot write to directory: {save_dir}\n\n**Error:** Directory is read-only\n\nPlease choose a different location."
            await send_notification(user_id, error_msg)
            await event.respond(f"❌ Permission denied: Cannot write to directory {save_dir}")
            user_states[user_id] = {'state': 'logged_in', 'chat_id': chat_id}
            return
        
        # Get original filename and extension
        original_filename = None
        original_extension = None
        
        if hasattr(file_message.media, 'document') and file_message.media.document:
            original_filename = file_message.media.document.attributes[0].file_name
            if original_filename:
                original_extension = os.path.splitext(original_filename)[1]
        
        # Handle filename logic
        if not filename:
            # Use original filename
            if original_filename:
                final_filename = original_filename
            else:
                final_filename = f"file_{int(asyncio.get_event_loop().time())}"
        else:
            # User provided a new filename
            user_filename = filename.strip()
            
            # Check if user included an extension
            user_name, user_ext = os.path.splitext(user_filename)
            
            if user_ext:
                # User provided extension, use it as-is
                final_filename = user_filename
                logger.info(f"User provided extension: {user_ext}, using: {final_filename}")
            else:
                # User provided only name, use original extension
                if original_extension:
                    final_filename = f"{user_name}{original_extension}"
                    logger.info(f"Using original extension {original_extension}, final filename: {final_filename}")
                else:
                    # No original extension, use as-is
                    final_filename = user_filename
                    logger.info(f"No original extension found, using as-is: {final_filename}")
        
        save_path = os.path.join(save_dir, final_filename)
        
        logger.info(f"Queuing download to: {save_path}")
        await event.respond(f"📥 Queuing download to: {save_path}")
        
        # Queue the download
        task = await queue_download(user_id, file_message, save_path)
        
        # Reset user state but preserve chat_id
        user_states[user_id] = {'state': 'logged_in', 'chat_id': chat_id}
        
    except PermissionError as e:
        logger.error(f"Permission error queuing download: {e}")
        error_msg = f"❌ **Permission Error!**\n\nCannot write to the selected directory.\n\n**Error:** {str(e)}\n\nPlease choose a different location."
        await send_notification(user_id, error_msg)
        await event.respond(f"❌ Permission denied: Cannot write to the selected directory. Please choose a different location.")
        user_states[user_id] = {'state': 'logged_in', 'chat_id': event.chat_id}
    except Exception as e:
        logger.error(f"Error queuing download: {e}")
        error_msg = f"❌ **Download Error!**\n\nFailed to queue download.\n\n**Error:** {str(e)}\n\nPlease try again or contact support."
        await send_notification(user_id, error_msg)
        await event.respond(f"❌ Error queuing download: {e}")
        user_states[user_id] = {'state': 'logged_in', 'chat_id': event.chat_id}

# Add command to show download status
@client.on(events.NewMessage(pattern='/status'))
async def status_handler(event):
    """Show interactive download status for the user"""
    user_id = str(event.sender_id)
    if user_id not in ALLOWED_USERS:
        return
    
    user_downloads = download_queue.get(user_id, [])
    if not user_downloads:
        await event.respond(
            "📊 **Download Manager**\n\n"
            "No downloads in queue.\n"
            "Forward a file to start downloading!",
            buttons=[[Button.inline("🔄 Refresh", "status_refresh")]]
        )
        return
    
    # Count downloads by status
    queued = sum(1 for task in user_downloads if task.status == "queued")
    downloading = sum(1 for task in user_downloads if task.status == "downloading")
    completed = sum(1 for task in user_downloads if task.status == "completed")
    failed = sum(1 for task in user_downloads if task.status == "failed")
    
    # Calculate total progress
    total_downloaded = sum(task.downloaded_bytes for task in user_downloads if task.status == "downloading")
    total_size = sum(task.total_bytes for task in user_downloads if task.status == "downloading")
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
    active_downloads = [task for task in user_downloads if task.status in ["queued", "downloading"]]
    for i, task in enumerate(active_downloads[:5], 1):  # Show max 5 active downloads
        filename = os.path.basename(task.save_path)
        if task.status == "queued":
            status_text += f"{i}. ⏳ **{filename}** - Waiting in queue\n"
        elif task.status == "downloading":
            progress = (task.downloaded_bytes / task.total_bytes * 100) if task.total_bytes > 0 else 0
            downloaded_mb = task.downloaded_bytes / (1024*1024)
            total_mb = task.total_bytes / (1024*1024)
            elapsed_time = time.time() - task.start_time
            speed = task.downloaded_bytes / elapsed_time if elapsed_time > 0 else 0
            speed_mb = speed / (1024*1024)
            eta_seconds = (task.total_bytes - task.downloaded_bytes) / speed if speed > 0 else 0
            eta_minutes = eta_seconds / 60
            
            status_text += f"{i}. 📥 **{filename}**\n"
            status_text += f"   Progress: {progress:.1f}%\n"
            status_text += f"   Speed: {speed_mb:.1f} MB/s\n"
            status_text += f"   Downloaded: {downloaded_mb:.1f} MB / {total_mb:.1f} MB\n"
            status_text += f"   ETA: {eta_minutes:.1f} min\n\n"
    
    if len(active_downloads) > 5:
        status_text += f"... and {len(active_downloads) - 5} more downloads\n"
    
    # Create interactive buttons
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
    nav_row.append(Button.inline("🔄 Manual Refresh", "status_refresh"))
    nav_row.append(Button.inline("🗑️ Clear Completed", "clear_completed"))
    if nav_row:
        buttons.append(nav_row)
    
    # Send status message
    status_message = await event.respond(status_text, buttons=buttons)

async def main():
    logger.info("Starting bot...")
    try:
        await client.start(bot_token=BOT_TOKEN)
        logger.info("Bot connected successfully")
        print('Bot is running...')
        await client.run_until_disconnected()
    except Exception as e:
        logger.error(f"Bot failed to start: {e}")
        raise
    finally:
        logger.info("Bot shutting down")

if __name__ == '__main__':
    logger.info("Initializing bot application")
    asyncio.run(main()) 