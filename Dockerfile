# Use Alpine Linux for Raspberry Pi
FROM python:3.11-alpine

WORKDIR /app

# Install system dependencies
RUN apk add --no-cache gcc musl-dev libffi-dev openssl-dev

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Install the package in development mode
RUN pip install -e .

# Create directories for downloads and saved files
RUN mkdir -p downloads

# Run the bot using the installed package
CMD ["telegram-downloader-bot"] 