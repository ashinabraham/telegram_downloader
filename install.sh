#!/bin/bash

# Installation script for Telegram File Downloader Bot
# This script installs the package in development mode

set -e

echo "🚀 Installing Telegram File Downloader Bot..."

# Check if Python 3.8+ is available
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Error: Python 3.8 or higher is required. Found: $python_version"
    exit 1
fi

echo "✅ Python version: $python_version"

# Upgrade pip
echo "📦 Upgrading pip..."
python3 -m pip install --upgrade pip

# Install dependencies
echo "📦 Installing dependencies..."
pip3 install -r requirements.txt

# Install the package in development mode
echo "📦 Installing package in development mode..."
pip3 install -e .

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p downloads

# Set permissions
echo "🔐 Setting permissions..."
chmod 755 downloads

echo ""
echo "🎉 Installation completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Copy .env.example to .env and configure your settings"
echo "2. Run the bot with: telegram-downloader-bot"
echo "3. Or run with: python3 src/main.py"
echo ""
echo "📚 For development:"
echo "- Run tests: make test"
echo "- Format code: make format"
echo "- Lint code: make lint"
echo ""
echo "🐳 For Docker:"
echo "- Build image: make docker-build"
echo "- Run container: docker run --env-file .env telegram-downloader" 