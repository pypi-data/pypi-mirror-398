# Development Guide

This guide is for developers who want to contribute to or modify the glucosedao-client project.

## Project Structure

```
glucosedao_client/
├── src/glucosedao_client/
│   ├── __init__.py         # Package exports
│   ├── client.py           # HTTP client for GluRPC API (sync & async)
│   ├── app.py              # Gradio web interface
│   ├── server.py           # Server management utilities
│   └── cli.py              # Command-line interface
├── pyproject.toml          # Project metadata and dependencies
├── README.md               # User documentation
├── DEVELOPMENT.md          # This file
├── example.py              # Example usage
└── test_setup.py           # Setup verification tests
```

## Setup Development Environment

### 1. Install uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Clone and Setup

```bash
cd /data/sources/glucosedao/glucosedao_client
uv sync
```

This will:
- Create a virtual environment
- Install all dependencies from pyproject.toml
- Install the package in editable mode

### 3. Verify Setup

```bash
uv run python test_setup.py
```

## Development Workflow

### Running the Client Locally

```bash
# Option 1: Run directly with Python
uv run python -m glucosedao_client.cli launch

# Option 2: Use the installed CLI
uv run glucosedao-client launch

# Option 3: With test server
uv run glucosedao-client launch --with-server
```

### Running Tests

```bash
# Run setup tests
uv run python test_setup.py

# Run example script (requires server)
uv run python example.py
```

### Code Style and Linting

We follow Python best practices:

- **Type hints**: All functions should have type hints (per user rules)
- **Docstrings**: Google-style docstrings for all public APIs
- **Logging**: Use Eliot for structured logging
- **No placeholders**: No placeholder paths or values in real code

Run linting:

```bash
# Check lints
uv run ruff check src/

# Format code
uv run ruff format src/
```

## Architecture Overview

### Client Library (`client.py`)

The client library provides both sync and async interfaces:

```python
# Synchronous
client = GluRPCClient(config)
response = client.process_unified(csv_content)

# Asynchronous
async with AsyncGluRPCClient(config) as client:
    response = await client.process_unified(csv_content)
```

Key design decisions:
- Uses `httpx` for HTTP (not requests) - supports both sync and async
- Uses `dataclasses` for response types
- Structured logging with Eliot
- No try-catch inside actions (per user rules)

### Gradio App (`app.py`)

The Gradio interface follows these principles:
- Clean separation of UI and business logic
- Global state management for current session
- Error handling with user-friendly messages
- Real-time server health monitoring

Key functions:
- `process_and_prepare()`: Handles file upload and processing
- `predict_glucose()`: Generates plot for a sample
- `create_warning_display()`: Formats quality warnings
- `check_server_health()`: Verifies server status

### Server Management (`server.py`)

Utilities for starting/stopping the GluRPC server locally:
- `is_server_running()`: Check if server is up
- `wait_for_server()`: Wait for server to be ready
- `start_server()`: Start server process
- `stop_server()`: Gracefully stop server

### CLI (`cli.py`)

Built with Typer, provides three main commands:
- `launch`: Start the Gradio interface (with optional server)
- `server`: Start only the server
- `check`: Health check

## Adding New Features

### Adding a New API Endpoint

1. **Update `client.py`**:

```python
def new_endpoint(self, param: str) -> ResponseType:
    """Description.
    
    Args:
        param: Parameter description
        
    Returns:
        Response description
    """
    with start_action(action_type="new_endpoint", param=param):
        response = self.client.post(
            f"{self.config.base_url}/new_endpoint",
            json={"param": param},
            headers=self._get_headers()
        )
        
        response.raise_for_status()
        return ResponseType(**response.json())
```

2. **Update async client** with same method

3. **Add to `__init__.py` exports** if needed

4. **Update `app.py`** if UI changes needed

5. **Update documentation**

### Adding a New CLI Command

1. **Update `cli.py`**:

```python
@app.command()
def new_command(
    arg: str = typer.Option(..., "--arg", help="Argument help")
):
    """Command description.
    
    Example:
    
    glucosedao-client new-command --arg value
    """
    # Implementation
```

2. **Update README** with new command documentation

## Testing

### Manual Testing Checklist

Before submitting changes, test:

- [ ] Client can connect to server
- [ ] File upload and conversion works
- [ ] Processing and plotting works
- [ ] Health check displays correctly
- [ ] Error messages are user-friendly
- [ ] CLI commands work as expected
- [ ] --with-server option works
- [ ] Server startup/shutdown is graceful

### Integration Testing

To test with a real server:

```bash
# Terminal 1: Start server
cd /data/sources/glucosedao/glucosedao
uv run python -m glurpc.app

# Terminal 2: Start client
cd /data/sources/glucosedao/glucosedao_client
uv run glucosedao-client launch
```

Upload a test file and verify:
1. File converts successfully
2. Processing completes
3. Warnings display if applicable
4. Plots generate correctly
5. Slider works for different samples

## Common Development Tasks

### Updating Dependencies

```bash
# Add new dependency
uv add package-name

# Update specific package
uv add package-name@latest

# Remove dependency
uv remove package-name

# Update lock file
uv lock
```

### Building Distribution

```bash
# Build wheel
uv build

# Check dist/
ls -lh dist/
```

### Installing Locally for Testing

```bash
# Install in editable mode
uv pip install -e .

# Now CLI is available system-wide
glucosedao-client --help
```

## Troubleshooting

### Import Errors

If you get import errors:
```bash
# Reinstall in editable mode
uv sync --force
```

### Server Won't Start

Check if port is in use:
```bash
lsof -i :8000
```

Use a different port:
```bash
glucosedao-client launch --with-server --server-port 8001
```

### Gradio Interface Issues

If Gradio interface doesn't work:
1. Check Gradio version: `uv pip list | grep gradio`
2. Should be < 6.0 (per pyproject.toml)
3. Reinstall if needed: `uv sync --force`

## Code Guidelines

### Following User Rules

This project follows specific user preferences:

1. **No nested try-catch**: Avoid try-catch inside Eliot actions
2. **No placeholders**: Never use paths like `/my/custom/path/` in code
3. **Real tests**: Integration tests use real data, not mocks
4. **No markdown files**: Don't create change summaries unless asked
5. **Type hints**: Always use type hints
6. **Typer for CLI**: Use typer library for CLI
7. **Eliot logging**: Use `with start_action(...)` pattern
8. **Pydantic 2**: Assume pydantic 2 by default
9. **No hardcoded versions**: Don't put version in `__init__.py`

### Example: Good Code Pattern

```python
from typing import Optional
from eliot import start_action
from glucosedao_client.client import GluRPCClient

def process_data(client: GluRPCClient, csv_path: str) -> Optional[str]:
    """Process data using client.
    
    Args:
        client: Initialized GluRPC client
        csv_path: Path to CSV file
        
    Returns:
        Handle if successful, None otherwise
    """
    with start_action(action_type="process_data", path=csv_path):
        # No try-catch inside action
        convert_resp = client.convert_to_unified(csv_path)
        
        if convert_resp.error:
            return None
        
        process_resp = client.process_unified(convert_resp.csv_content)
        
        if process_resp.error:
            return None
        
        return process_resp.handle
```

## Release Process

1. **Update version** in `pyproject.toml`
2. **Update CHANGELOG** (if exists)
3. **Test thoroughly**:
   ```bash
   uv run python test_setup.py
   uv run glucosedao-client launch --with-server
   ```
4. **Build distribution**:
   ```bash
   uv build
   ```
5. **Tag release**:
   ```bash
   git tag -a v0.1.0 -m "Release v0.1.0"
   git push --tags
   ```

## Getting Help

- Check README.md for user documentation
- Review code comments and docstrings
- Test with `test_setup.py` and `example.py`
- Check GluRPC server documentation

## Contributing

1. Create a feature branch
2. Make changes following code guidelines
3. Test thoroughly
4. Update documentation
5. Submit pull request

## Resources

- [httpx Documentation](https://www.python-httpx.org/)
- [Gradio Documentation](https://gradio.app/)
- [Typer Documentation](https://typer.tiangolo.com/)
- [Eliot Documentation](https://eliot.readthedocs.io/)
- [uv Documentation](https://github.com/astral-sh/uv)

