# Development Guide

This guide explains how to use the development tools and pipeline scripts for the Telegram Bot project.

## Quick Start

### Using Makefile (Recommended)

The Makefile provides a comprehensive set of commands for development tasks:

```bash
# Show all available commands
make help

# Install dependencies
make install

# Run full pipeline (linting, testing, Docker)
make pipeline

# Run fast pipeline (essential checks only)
make fast-pipeline

# Format code
make format

# Run linting
make lint

# Run tests with coverage
make test-coverage
```

### Using Pipeline Script

The shell script provides an alternative with colored output:

```bash
# Run full pipeline
./scripts/pipeline.sh

# Run fast pipeline
./scripts/pipeline.sh --fast

# Skip Docker operations
./scripts/pipeline.sh --skip-docker

# Skip linting
./scripts/pipeline.sh --skip-linting
```

## Available Commands

### Setup & Installation

| Command | Description |
|---------|-------------|
| `make install` | Install project dependencies |
| `make install-dev` | Install development dependencies |
| `make dev-setup` | Setup development environment |

### Code Quality

| Command | Description |
|---------|-------------|
| `make lint` | Run flake8 linting |
| `make format` | Format code with black |
| `make format-check` | Check if code is formatted (CI) |

### Testing

| Command | Description |
|---------|-------------|
| `make test` | Run all tests |
| `make test-coverage` | Run tests with coverage report |
| `make test-fast` | Run only fast tests |
| `make test-unit` | Run only unit tests |
| `make test-integration` | Run only integration tests |

### Docker Operations

| Command | Description |
|---------|-------------|
| `make docker-build` | Build Docker image |
| `make docker-build-alpine` | Build Alpine Docker image |
| `make docker-test` | Run tests in Docker container |
| `make docker-clean` | Clean up Docker images |

### Pipeline Commands

| Command | Description |
|---------|-------------|
| `make pipeline` | Run full CI pipeline locally |
| `make fast-pipeline` | Run essential checks only |
| `make pre-commit` | Run pre-commit checks |

### Maintenance

| Command | Description |
|---------|-------------|
| `make clean` | Clean up generated files |
| `make clean-all` | Clean everything including Docker |

## Development Workflow

### Before Committing Code

1. **Format your code:**
   ```bash
   make format
   ```

2. **Run pre-commit checks:**
   ```bash
   make pre-commit
   ```

3. **Run full pipeline (optional):**
   ```bash
   make pipeline
   ```

### Quick Development

For quick iterations during development:

```bash
# Quick test (format check + lint + fast tests)
make quick-test

# Fast pipeline (install + lint + test)
make fast-pipeline
```

### CI/CD Simulation

To simulate the exact GitHub Actions pipeline locally:

```bash
# Full pipeline (matches CI exactly)
make pipeline

# Or using the script
./scripts/pipeline.sh
```

## Environment Variables

The following environment variables are automatically set for testing:

- `API_ID=1234`
- `API_HASH=dummy`
- `BOT_TOKEN=dummy`

## Troubleshooting

### Common Issues

1. **Python version not compatible:**
   - Ensure you have Python 3.11 or higher
   - Check with: `make check-python`

2. **Dependencies not installed:**
   - Run: `make install`
   - For development: `make install-dev`

3. **Docker not found:**
   - Docker operations will be skipped automatically
   - Install Docker if needed for full pipeline testing

4. **Linting fails:**
   - Run: `make format` to fix formatting issues
   - Check flake8 output for specific issues

### Getting Help

- Show all available commands: `make help`
- Show pipeline script help: `./scripts/pipeline.sh --help`

## Integration with IDE

### VS Code

Add these tasks to your `.vscode/tasks.json`:

```json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Format Code",
            "type": "shell",
            "command": "make",
            "args": ["format"],
            "group": "build"
        },
        {
            "label": "Run Tests",
            "type": "shell",
            "command": "make",
            "args": ["test"],
            "group": "test"
        },
        {
            "label": "Quick Test",
            "type": "shell",
            "command": "make",
            "args": ["quick-test"],
            "group": "test"
        }
    ]
}
```

### Pre-commit Hooks

You can set up pre-commit hooks to automatically run checks:

```bash
# Install pre-commit
pip install pre-commit

# Create .pre-commit-config.yaml
cat > .pre-commit-config.yaml << EOF
repos:
  - repo: local
    hooks:
      - id: format
        name: Format Code
        entry: make format
        language: system
        types: [python]
      - id: lint
        name: Lint Code
        entry: make lint
        language: system
        types: [python]
      - id: test
        name: Run Tests
        entry: make test-fast
        language: system
        types: [python]
EOF

# Install the hooks
pre-commit install
```

## Contributing

When contributing to this project:

1. Follow the existing code style (enforced by black and flake8)
2. Write tests for new features
3. Run the full pipeline before submitting PRs
4. Update documentation as needed

The pipeline ensures code quality and consistency across the project. 