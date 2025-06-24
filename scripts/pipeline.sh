#!/bin/bash

# Local Pipeline Script - Alternative to Makefile
# Provides colored output and better error handling

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
print_step() {
    echo -e "\n${BLUE}============================================================"
    echo -e "🔍 $1"
    echo -e "============================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to run command with error handling
run_command() {
    local cmd="$1"
    local description="$2"
    
    print_info "Running: $description"
    if eval "$cmd"; then
        print_success "$description completed successfully"
    else
        print_error "$description failed"
        return 1
    fi
}

# Main pipeline function
run_pipeline() {
    local skip_docker=false
    local skip_linting=false
    local skip_tests=false
    local fast_mode=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-docker)
                skip_docker=true
                shift
                ;;
            --skip-linting)
                skip_linting=true
                shift
                ;;
            --skip-tests)
                skip_tests=true
                shift
                ;;
            --fast)
                fast_mode=true
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    echo -e "${PURPLE}🚀 Local Pipeline - Testing Your Code Locally${NC}"
    echo -e "${PURPLE}============================================================${NC}"
    
    # Check Python version
    print_step "Checking Python Version"
    if command_exists python3; then
        python_version=$(python3 --version 2>&1)
        print_info "Found: $python_version"
        
        # Extract version numbers
        if [[ $python_version =~ Python\ ([0-9]+)\.([0-9]+) ]]; then
            major=${BASH_REMATCH[1]}
            minor=${BASH_REMATCH[2]}
            
            if [[ $major -eq 3 && $minor -ge 11 ]]; then
                print_success "Python version is compatible (3.11+)"
            else
                print_error "Python version $major.$minor is not supported. Need Python 3.11+"
                exit 1
            fi
        else
            print_warning "Could not determine Python version, continuing..."
        fi
    else
        print_error "Python 3 not found"
        exit 1
    fi
    
    # Install dependencies
    print_step "Installing Dependencies"
    run_command "pip3 install --upgrade pip" "Upgrading pip"
    run_command "pip3 install -r requirements.txt" "Installing project dependencies"
    
    # Run linting (unless skipped)
    if [[ "$skip_linting" == false && "$fast_mode" == false ]]; then
        print_step "Running Linting Checks"
        
        # Check if flake8 is available
        if ! command_exists flake8; then
            print_warning "flake8 not found, installing..."
            run_command "pip3 install flake8" "Installing flake8"
        fi
        
        run_command "python3 -m flake8 src/ --max-line-length=120 --ignore=E501,W503" "Flake8 linting"
        
        # Check if black is available
        if ! command_exists black; then
            print_warning "black not found, installing..."
            run_command "pip3 install black" "Installing black"
        fi
        
        run_command "python3 -m black --check src/ tests/ main.py run_tests.py" "Black formatting check"
    fi
    
    # Run tests (unless skipped)
    if [[ "$skip_tests" == false ]]; then
        print_step "Running Tests"
        
        # Set environment variables for testing
        export API_ID=1234
        export API_HASH=dummy
        export BOT_TOKEN=dummy
        
        if [[ "$fast_mode" == true ]]; then
            run_command "python3 -m pytest tests/ -v -m 'not slow'" "Fast tests"
        else
            run_command "python3 -m pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html" "Tests with coverage"
        fi
    fi
    
    # Docker operations (unless skipped)
    if [[ "$skip_docker" == false && "$fast_mode" == false ]]; then
        print_step "Docker Operations"
        
        if command_exists docker; then
            run_command "docker build -t telegram-downloader-test ." "Building Docker image"
            run_command "docker run --rm -e API_ID=1234 -e API_HASH=dummy -e BOT_TOKEN=dummy telegram-downloader-test python3 -m pytest tests/ -v --cov=src --cov-report=term-missing" "Running tests in Docker"
            run_command "docker rmi telegram-downloader-test" "Cleaning up Docker image"
        else
            print_warning "Docker not found, skipping Docker operations"
        fi
    fi
    
    # Final result
    echo -e "\n${PURPLE}============================================================"
    print_success "Pipeline completed successfully!"
    print_success "Your code is ready to push to GitHub!"
    echo -e "============================================================${NC}"
}

# Show help
show_help() {
    echo -e "${CYAN}Local Pipeline Script${NC}"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --skip-docker     Skip Docker-related operations"
    echo "  --skip-linting    Skip linting checks"
    echo "  --skip-tests      Skip test execution"
    echo "  --fast            Run only essential checks"
    echo "  --help, -h        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                    # Run full pipeline"
    echo "  $0 --fast            # Run essential checks only"
    echo "  $0 --skip-docker     # Skip Docker operations"
    echo "  $0 --skip-linting    # Skip linting"
}

# Run the pipeline
run_pipeline "$@" 