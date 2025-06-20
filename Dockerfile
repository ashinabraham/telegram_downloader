# Use Alpine Linux for Raspberry Pi
FROM python:3.11-alpine

WORKDIR /app

# Install system dependencies
RUN apk add --no-cache gcc musl-dev libffi-dev openssl-dev

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create directories
RUN mkdir -p saved_files downloads

# Create user
RUN adduser -D botuser && chown -R botuser:botuser /app
USER botuser

# Run the bot
CMD ["python", "downloader_bot.py"] 