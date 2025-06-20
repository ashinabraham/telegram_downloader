# 📱 Telegram File Downloader Bot

A powerful Telegram bot built with Telethon that allows authorized users to download files from Telegram chats directly to their local system. Features interactive directory navigation, file renaming, parallel downloads with progress tracking, and secure user authentication.

## 🏗️ Project Structure

```
telegram_bot/
├── src/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py          # Configuration management
│   │   └── user_state.py      # User state management
│   ├── bot/
│   │   ├── __init__.py
│   │   └── client.py          # Telegram client management
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── path_utils.py      # Path and directory utilities
│   │   └── keyboard_utils.py  # Inline keyboard creation
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── command_handlers.py    # Bot commands (/start, /help, /status)
│   │   ├── callback_handlers.py   # Inline button callbacks
│   │   └── message_handlers.py    # Text message and file handling
│   └── downloads/
│       ├── __init__.py
│       └── download_manager.py    # Download queue and progress tracking
├── main.py                   # Main entry point
├── requirements.txt          # Python dependencies
├── Dockerfile               # Docker configuration
├── docker-compose.yml       # Docker Compose configuration
└── README.md               # This file
```

## ✨ Features

- **🔐 Secure Authentication**: Interactive login via phone number and Telegram verification code
- **📁 Smart Directory Navigation**: Full system directory tree navigation with inline buttons
- **🔄 Parallel Downloads**: Up to 5 simultaneous downloads with real-time progress tracking
- **📝 File Renaming**: Optional file renaming with intelligent extension handling
- **⚡ Progress Monitoring**: Real-time download progress with speed, ETA, and completion status
- **🛡️ User Authorization**: Environment-based user whitelist for security
- **📊 Status Commands**: `/status` command to monitor all downloads and their states
- **🐳 Docker Support**: Ready-to-deploy Docker containerization

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Telegram Bot Token
- Telegram API ID and API Hash
- Docker (optional)

### Environment Setup

1. Create a `.env` file in the project root:

```bash
API_ID=your_api_id
API_HASH=your_api_hash
BOT_TOKEN=your_bot_token
ALLOWED_USERS=user_id1,user_id2
```

### Running with Docker

```bash
# Build and run with Docker Compose
docker-compose up -d

# Or build and run manually
docker build -t telegram-downloader-bot .
docker run -d --name telegram-bot telegram-downloader-bot
```

### Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run the bot
python main.py
```

## 📖 Usage

1. **Start the bot** with `/start`
2. **Complete interactive login** with phone number and verification code
3. **Forward any file** from Telegram to the bot
4. **Navigate to desired directory** using inline buttons
5. **Optionally rename the file**
6. **Monitor download progress** in real-time

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `API_ID` | Telegram API ID | Yes |
| `API_HASH` | Telegram API Hash | Yes |
| `BOT_TOKEN` | Telegram Bot Token | Yes |
| `ALLOWED_USERS` | Comma-separated list of authorized user IDs | Yes |

### Download Settings

The bot includes optimized download settings:

- **Chunk Size**: 1MB chunks for faster downloads
- **Progress Updates**: Every 5 seconds to reduce overhead
- **Parallel Downloads**: Up to 5 simultaneous downloads
- **Rate Limiting**: 30-second cooldown between notifications

## 🛠️ Development

### Module Overview

#### Core Modules
- **`config.py`**: Centralized configuration management with validation
- **`user_state.py`**: User session and state management

#### Bot Modules
- **`client.py`**: Telegram client initialization and connection management

#### Utility Modules
- **`path_utils.py`**: Directory navigation, path encoding, and file operations
- **`keyboard_utils.py`**: Inline keyboard creation for various menus

#### Handler Modules
- **`command_handlers.py`**: Bot commands (`/start`, `/help`, `/status`)
- **`callback_handlers.py`**: Inline button callbacks and status management
- **`message_handlers.py`**: Text messages, file forwarding, and state transitions

#### Download Modules
- **`download_manager.py`**: Download queue, progress tracking, and notifications

### Adding New Features

1. **New Commands**: Add handlers to `src/handlers/command_handlers.py`
2. **New Callbacks**: Add handlers to `src/handlers/callback_handlers.py`
3. **New Message Types**: Add handlers to `src/handlers/message_handlers.py`
4. **New Utilities**: Add to appropriate module in `src/utils/`
5. **Configuration**: Add to `src/core/config.py`

## 🔒 Security Features

- User whitelist via environment variables
- Secure session management
- Permission-based directory access
- Rate-limited notifications
- Error logging and monitoring

## 📈 Performance

- Parallel download support (up to 5 concurrent)
- Optimized chunk sizes for faster downloads
- Memory-efficient file handling
- Connection retry logic with exponential backoff

## 🐛 Troubleshooting

### Common Issues

1. **Permission Errors**: Ensure the bot has write access to the target directory
2. **Login Issues**: Check API credentials and phone number format
3. **Rate Limiting**: The bot includes built-in rate limiting to prevent flood wait
4. **Session Issues**: Delete the session file to force re-login

### Logs

The bot provides detailed logging for debugging:

```bash
# View logs in Docker
docker-compose logs -f telegram-bot

# View logs locally
tail -f bot.log
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Check the `/help` command in the bot
- Review the logs for error messages
- Open an issue on GitHub

---

**Perfect for personal file management, backup solutions, or automated file processing workflows!** 🎯
