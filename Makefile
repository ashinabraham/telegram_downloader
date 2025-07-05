# Makefile for Telegram Bot Project
# Usage: make <target>

.PHONY: help install install-dev install-package build-package version lint format test test-coverage test-fast clean docker-build docker-test pipeline fast-pipeline

# Default target
help:
	@echo "🚀 Telegram Bot Development Commands"
	@echo "====================================="
	@echo ""
	@echo "📦 Setup & Installation:"
	@echo "  install          - Install project dependencies"
	@echo "  install-dev      - Install development dependencies"
	@echo "  install-package  - Install the package in development mode"
	@echo "  build-package    - Build the package distribution"
	@echo "  version          - Show version information"
	@echo ""
	@echo "🔍 Code Quality:"
	@echo "  lint             - Run flake8 linting"
	@echo "  format           - Format code with black"
	@echo "  format-check     - Check if code is formatted (CI)"
	@echo ""
	@echo "🧪 Testing:"
	@echo "  test             - Run all tests"
	@echo "  test-coverage    - Run tests with coverage report"
	@echo "  test-fast        - Run only fast tests"
	@echo "  test-unit        - Run only unit tests"
	@echo "  test-integration - Run only integration tests"
	@echo ""
	@echo "🐳 Docker:"
	@echo "  docker-build     - Build Docker image"
	@echo "  docker-test      - Run tests in Docker container"
	@echo "  docker-clean     - Clean up Docker images"
	@echo ""
	@echo "🚀 Pipeline:"
	@echo "  pipeline         - Run full CI pipeline locally"
	@echo "  fast-pipeline    - Run essential checks only"
	@echo ""
	@echo "🧹 Maintenance:"
	@echo "  clean            - Clean up generated files"
	@echo "  clean-pycache    - Clean all Python cache files"
	@echo "  clean-all        - Clean everything including Docker"

# Python and pip commands
PYTHON := python3
PIP := pip3

# Directories
SRC_DIR := src
TEST_DIR := tests
COVERAGE_DIR := htmlcov
DIST_DIR := dist
BUILD_DIR := build

# Environment variables for testing
export API_ID := 1234
export API_HASH := dummy
export BOT_TOKEN := dummy

# =============================================================================
# Setup & Installation
# =============================================================================

install:
	@echo "📦 Installing project dependencies..."
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo "✅ Dependencies installed successfully!"

install-dev:
	@echo "📦 Installing development dependencies..."
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PIP) install black flake8 mypy pytest pytest-asyncio pytest-cov
	@echo "✅ Development dependencies installed successfully!"

install-package:
	@echo "📦 Installing package in development mode..."
	$(PIP) install -e .
	@echo "✅ Package installed successfully!"

build-package:
	@echo "📦 Building package distribution..."
	$(PYTHON) -m build
	@echo "✅ Package distribution built successfully!"
	@echo "📁 Distribution files created in $(DIST_DIR)/"

version:
	@echo "📋 Version Information:"
	@$(PYTHON) -c "import sys; sys.path.insert(0, 'src'); import version; print(f'Version: {version.__version__}'); print(f'Author: {version.__author__}'); print(f'Description: {version.__description__}')"

# =============================================================================
# Code Quality
# =============================================================================

lint:
	@echo "🔍 Running flake8 linting..."
	$(PYTHON) -m flake8 $(SRC_DIR)/ --max-line-length=120 --ignore=E501,W503
	@echo "✅ Linting passed!"

format:
	@echo "🎨 Formatting code with black..."
	$(PYTHON) -m black $(SRC_DIR)/ $(TEST_DIR)/ main.py run_tests.py
	@echo "✅ Code formatted successfully!"

format-check:
	@echo "🎨 Checking code formatting..."
	$(PYTHON) -m black --check $(SRC_DIR)/ $(TEST_DIR)/ main.py run_tests.py
	@echo "✅ Code formatting check passed!"

# =============================================================================
# Testing
# =============================================================================

test:
	@echo "🧪 Running all tests..."
	$(PYTHON) -m pytest $(TEST_DIR)/ -v
	@echo "✅ All tests passed!"

test-coverage:
	@echo "🧪 Running tests with coverage..."
	$(PYTHON) -m pytest $(TEST_DIR)/ -v --cov=$(SRC_DIR) --cov-report=term-missing --cov-report=html
	@echo "✅ Tests with coverage completed!"
	@echo "📊 Coverage report generated in $(COVERAGE_DIR)/"

test-fast:
	@echo "⚡ Running fast tests only..."
	$(PYTHON) -m pytest $(TEST_DIR)/ -v -m "not slow"
	@echo "✅ Fast tests completed!"

test-unit:
	@echo "🧪 Running unit tests..."
	$(PYTHON) -m pytest $(TEST_DIR)/unit/ -v
	@echo "✅ Unit tests completed!"

test-integration:
	@echo "🧪 Running integration tests..."
	$(PYTHON) -m pytest $(TEST_DIR)/integration/ -v
	@echo "✅ Integration tests completed!"

# =============================================================================
# Docker Operations
# =============================================================================

docker-build:
	@echo "🐳 Building Docker image..."
	docker build -t telegram-downloader .
	@echo "✅ Docker image built successfully!"



docker-test:
	@echo "🧪 Running tests in Docker container..."
	docker run --rm \
		-e API_ID=1234 \
		-e API_HASH=dummy \
		-e BOT_TOKEN=dummy \
		telegram-downloader $(PYTHON) -m pytest $(TEST_DIR)/ -v --cov=$(SRC_DIR) --cov-report=term-missing
	@echo "✅ Docker tests completed!"

docker-clean:
	@echo "🧹 Cleaning up Docker images..."
	-docker rmi telegram-downloader 2>/dev/null || true
	@echo "✅ Docker cleanup completed!"

# =============================================================================
# Pipeline Commands
# =============================================================================

pipeline: install format-check lint test-coverage docker-build
	@echo ""
	@echo "🎉 Full pipeline completed successfully!"
	@echo "✅ Your code is ready to push to GitHub!"

fast-pipeline: install lint test
	@echo ""
	@echo "⚡ Fast pipeline completed successfully!"
	@echo "✅ Essential checks passed!"

# =============================================================================
# Maintenance
# =============================================================================

clean:
	@echo "🧹 Cleaning up generated files..."
	-rm -rf $(COVERAGE_DIR)/
	-rm -f .coverage
	-rm -f coverage.xml
	-rm -rf .pytest_cache/
	-rm -rf __pycache__/
	-rm -rf $(DIST_DIR)/
	-rm -rf $(BUILD_DIR)/
	-rm -rf *.egg-info/
	-find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	-find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ Cleanup completed!"

clean-pycache:
	@echo "🧹 Cleaning all Python cache files..."
	-find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	-find . -type f -name "*.pyc" -delete 2>/dev/null || true
	-find . -type f -name "*.pyo" -delete 2>/dev/null || true
	-find . -type f -name "*.pyd" -delete 2>/dev/null || true
	@echo "✅ Python cache cleanup completed!"

clean-all: clean docker-clean
	@echo "🧹 Full cleanup completed!"

# =============================================================================
# Development Helpers
# =============================================================================

check-python:
	@echo "🐍 Checking Python version..."
	@$(PYTHON) --version
	@echo "✅ Python version check completed!"

check-deps:
	@echo "📋 Checking installed dependencies..."
	$(PIP) list
	@echo "✅ Dependencies check completed!"

run-bot:
	@echo "🤖 Starting the Telegram bot..."
	$(PYTHON) main.py

# =============================================================================
# CI/CD Helpers
# =============================================================================

ci-setup:
	@echo "🔧 Setting up CI environment..."
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo "✅ CI setup completed!"

ci-test:
	@echo "🧪 Running CI tests..."
	$(PYTHON) -m pytest $(TEST_DIR)/ -v --cov=$(SRC_DIR) --cov-report=xml
	@echo "✅ CI tests completed!"

# =============================================================================
# Quick Development Workflow
# =============================================================================

dev-setup: install-dev format
	@echo "🚀 Development environment ready!"

quick-test: format-check lint test-fast
	@echo "⚡ Quick test completed!"

pre-commit: format lint test-fast
	@echo "✅ Pre-commit checks passed!" 