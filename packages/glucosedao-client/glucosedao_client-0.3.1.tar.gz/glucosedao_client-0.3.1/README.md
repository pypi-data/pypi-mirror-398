# GluRPC Client - Reference Implementation

**Official reference client implementation** for [GluRPC](https://github.com/glucosedao/glurpc), the glucose prediction server. This package demonstrates best practices for integrating with GluRPC and provides both a Python SDK and a production-ready Gradio web interface for uploading CGM data and visualizing glucose predictions.

## Features

### 🎯 Reference Client Capabilities

- 🌐 **Full GluRPC API Coverage**: Complete Python SDK with sync and async support
- 🖥️ **Production-Ready Web Interface**: Beautiful Gradio UI with real-time updates
- 📊 **Advanced Visualization**: Interactive Plotly charts with confidence intervals
- 🔍 **Real-time Health Monitoring**: Live server metrics with historical graphs
- ⚡ **Smart Request Management**: Automatic request cancellation and client-side optimization
- 💾 **Format Conversion**: Upload raw CGM files, get unified format with data quality warnings
- 🎚️ **Interactive Exploration**: Slider-based navigation through prediction samples
- 🔐 **Secure Authentication**: API key support for protected servers
- 📥 **Export Capabilities**: Download unified CSV and interactive HTML plots
- 🧪 **Development Tools**: Built-in test server for local development
- 📈 **Performance Tracking**: Client-side request timing and server queue monitoring

## Installation

### Using uv (Recommended)

```bash
uv sync
```

### Using pip

```bash
pip install glucosedao-client
```

## Quick Start

### Quickest Start: Using uv Scripts

```bash
# Run client + server together (recommended for development)
uv run dev

# Run only the client (connect to existing server)
uv run client

# Run only the server
uv run server
```

### Option 1: Connect to Existing Server

If you have a GluRPC server running elsewhere:

```bash
# Start the client interface
glucosedao-client launch

# Or with custom host/port
glucosedao-client launch --host 0.0.0.0 --port 7860
```

Then open your browser and:
1. Enter the server URL (e.g., `http://your-server:8000`)
2. Enter API key if required
3. Upload your CGM data file
4. View predictions!

### Option 2: Launch with Local Test Server

For development or testing, start both client and server together:

```bash
# Start both client and server
glucosedao-client launch --with-server

# With custom ports
glucosedao-client launch --with-server --port 7860 --server-port 8001
```

### Option 3: Start Only the Server

If you want to run just the server:

```bash
glucosedao-client server --host 0.0.0.0 --port 8000
```

## CLI Commands

### `launch` - Start the Web Interface

```bash
glucosedao-client launch [OPTIONS]
```

Options:
- `--share`: Create a public Gradio share link
- `--host HOST`: Hostname to bind to (default: 127.0.0.1)
- `--port PORT`: Port to bind to (default: 7860)
- `--with-server`: Start GluRPC server locally for testing
- `--server-host HOST`: GluRPC server host when using --with-server (default: 127.0.0.1)
- `--server-port PORT`: GluRPC server port when using --with-server (default: 8000)

Examples:

```bash
# Basic launch
glucosedao-client launch

# Launch with local test server
glucosedao-client launch --with-server

# Create public share link
glucosedao-client launch --share

# Custom configuration
glucosedao-client launch --host 0.0.0.0 --port 8080 --with-server --server-port 8001
```

### `server` - Start Only the Server

```bash
glucosedao-client server [OPTIONS]
```

Options:
- `--host HOST`: Host to bind to (default: 0.0.0.0)
- `--port PORT`: Port to bind to (default: 8000)

Example:

```bash
glucosedao-client server --host 0.0.0.0 --port 8000
```

### `check` - Health Check

```bash
glucosedao-client check [OPTIONS]
```

Options:
- `--url URL`: Server URL to check (default: http://localhost:8000)

Example:

```bash
glucosedao-client check --url http://your-server:8000
```

## Python API

You can also use the client programmatically:

```python
from glucosedao_client import GluRPCClient, GluRPCConfig

# Initialize client
config = GluRPCConfig(
    base_url="http://localhost:8000",
    api_key="your-api-key"  # Optional
)
client = GluRPCClient(config)

# Convert raw CGM file to unified format
convert_response = client.convert_to_unified("path/to/dexcom.csv")

if not convert_response.error:
    # Process the data
    process_response = client.process_unified(convert_response.csv_content)
    
    if not process_response.error:
        # Generate plot for a specific sample
        png_bytes = client.draw_plot(
            handle=process_response.handle,
            index=0
        )
        
        # Save plot
        with open("prediction.png", "wb") as f:
            f.write(png_bytes)

# Check server health
health = client.health()
print(f"Server status: {health.status}")
print(f"Models initialized: {health.models_initialized}")
print(f"Total requests: {health.total_requests_processed}")

# Clean up
client.close()
```

### Async API

For async applications:

```python
from glucosedao_client import AsyncGluRPCClient, GluRPCConfig

async def main():
    config = GluRPCConfig(base_url="http://localhost:8000")
    
    async with AsyncGluRPCClient(config) as client:
        # Convert file
        convert_response = await client.convert_to_unified("data.csv")
        
        # Process data
        process_response = await client.process_unified(
            convert_response.csv_content
        )
        
        # Get plot
        png_bytes = await client.draw_plot(
            process_response.handle,
            index=0
        )
```

## Using the Web Interface

1. **Configure Server**: Enter the GluRPC server URL and API key (if required)
2. **Check Health**: Click "Check Server Health" to verify connectivity
3. **Upload Data**: Upload a CGM data file (Dexcom, LibreView, etc.)
4. **View Predictions**: The app will automatically process and show predictions
5. **Explore Samples**: Use the slider to view predictions for different time windows

## Supported Data Formats

The client supports any CGM data format that GluRPC server supports:
- Dexcom
- LibreView (Freestyle Libre)
- Nightscout exports
- And more...

The server handles all format conversion automatically.

## Configuration

### Environment Variables

You can set default configuration using environment variables:

```bash
export GLURPC_URL="http://localhost:8000"
export GLURPC_API_KEY="your-api-key"
```

### Logging

Logs are saved to `logs/app_<timestamp>.log` with both console and file output. The client uses Python's standard logging library with DEBUG level for files and INFO level for console output.

## Development

### Setting up Development Environment

```bash
# Clone the repository
git clone https://github.com/glucosedao/glucosedao_client.git
cd glucosedao_client

# Install dependencies with uv
uv sync

# Run in development mode
uv run python -m glucosedao_client.app
```

### Running Tests

```bash
# Install test dependencies
uv add --dev pytest pytest-asyncio httpx

# Run tests
uv run pytest
```

## Architecture

This reference implementation demonstrates proper client architecture:

### Core Components

- **`client.py`**: Complete HTTP client for GluRPC API
  - Sync (`GluRPCClient`) and async (`AsyncGluRPCClient`) implementations
  - Type-safe response models with Pydantic
  - Connection pooling and timeout management
  - Error handling and retry logic

- **`app.py`**: Production-ready Gradio web interface (1000+ LOC)
  - Real-time server health monitoring with live graphs
  - Automatic request cancellation for smooth slider interaction
  - Data quality warnings from server validation
  - Format conversion and unified CSV export
  - Interactive Plotly visualizations
  - Client-side performance tracking

- **`server.py`**: Development server utilities
  - Local test server management
  - Process lifecycle handling

- **`cli.py`**: Typer-based CLI
  - Multiple launch modes (client-only, with-server, server-only)
  - Health check utilities
  - Flexible configuration options

### Client-Server Interaction

The reference implementation demonstrates:

1. **Efficient API Usage**: 
   - File upload → Convert to unified format
   - Process unified data → Get handle + warnings
   - Draw plots on demand with caching

2. **Request Management**:
   - Client-side request ID tracking
   - Automatic cancellation of stale requests
   - Server-side concurrent request handling

3. **Real-time Monitoring**:
   - Health polling with 1-second updates
   - Historical metrics visualization
   - Queue size and processing time tracking

4. **User Experience**:
   - Automatic plot generation on file upload
   - Smooth slider interaction with debouncing
   - Clear status messages and error handling
   - Download options for data and plots

## Troubleshooting

### Server Not Responding

```bash
# Check if server is running
glucosedao-client check --url http://your-server:8000

# Try starting a local test server
glucosedao-client launch --with-server
```

### API Key Errors

Make sure you're providing the correct API key in the web interface or:

```python
config = GluRPCConfig(
    base_url="http://localhost:8000",
    api_key="your-api-key"
)
```

### Port Already in Use

If the default port is in use:

```bash
# Use a different port
glucosedao-client launch --port 8080
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

Apache 2.0 - See LICENSE file for details.

## Links

- [GluRPC Server](https://github.com/glucosedao/glucosedao)
- [Documentation](https://github.com/glucosedao/glucosedao_client)
- [Issue Tracker](https://github.com/glucosedao/glucosedao_client/issues)

## Why This is a Reference Implementation

This client serves as the **official example** of how to properly integrate with GluRPC:

✅ **Complete API Coverage**: Shows how to use all GluRPC endpoints  
✅ **Best Practices**: Demonstrates proper error handling, caching, and request management  
✅ **Type Safety**: Uses Pydantic models for all API interactions  
✅ **Production Ready**: Includes monitoring, logging, and performance tracking  
✅ **Async Support**: Shows both sync and async usage patterns  
✅ **User Experience**: Implements smart features like request cancellation and live updates  

Use this client as a template when building your own GluRPC integrations!

## Technology Stack

- **[Gradio 4.x](https://gradio.app/)** - Interactive web interface with real-time updates
- **[httpx](https://www.python-httpx.org/)** - Modern async HTTP client
- **[Typer](https://typer.tiangolo.com/)** - CLI framework with type hints
- **[Plotly](https://plotly.com/python/)** - Interactive scientific visualization
- **[Pydantic 2](https://docs.pydantic.dev/)** - Data validation and settings management
- **[cgm-format](https://github.com/glucosedao/cgm-format)** - CGM data format handling
