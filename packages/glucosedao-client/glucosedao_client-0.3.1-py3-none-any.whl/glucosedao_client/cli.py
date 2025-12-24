"""Command-line interface for GluRPC client."""
from typing import Optional
from urllib.parse import urlparse
import typer
from pathlib import Path

from glucosedao_client.app import launch_app
from glucosedao_client.server import start_server, stop_server, is_server_running


app = typer.Typer(
    name="glucosedao-client",
    help="GluRPC Client - Glucose prediction client application"
)


@app.command()
def launch(
    share: bool = typer.Option(
        False,
        "--share",
        help="Create a public Gradio share link"
    ),
    server_name: str = typer.Option(
        "127.0.0.1",
        "--host",
        help="Hostname to bind to"
    ),
    server_port: int = typer.Option(
        7860,
        "--port",
        help="Port to bind to"
    ),
    with_server: bool = typer.Option(
        False,
        "--with-server",
        help="Start GluRPC server locally for testing"
    ),
    server_host: str = typer.Option(
        "localhost",
        "--server-host",
        help="GluRPC server host (can include schema like https://example.com)"
    ),
    server_port_backend: int = typer.Option(
        None,
        "--server-port",
        help="GluRPC server port (defaults: 80 for http, 443 for https, 8000 for no schema)"
    )
):
    """Launch the Gradio web interface.
    
    Examples:
    
    # Launch client only (assumes server is running elsewhere)
    glucosedao-client launch
    
    # Launch client pointing to remote server
    glucosedao-client launch --server-host https://glurpc-rest.glucosedao.org
    
    # Launch client with custom port
    glucosedao-client launch --server-host https://example.com --server-port 8443
    
    # Launch client with local server for testing
    glucosedao-client launch --with-server
    
    # Launch with custom ports
    glucosedao-client launch --port 8080 --with-server --server-port 8001
    
    # Create public share link
    glucosedao-client launch --share
    """
    # Parse server URL
    parsed_host = urlparse(server_host)
    
    # Determine schema, host, and port
    if parsed_host.scheme:
        # Schema is present (http:// or https://)
        schema = parsed_host.scheme
        hostname = parsed_host.hostname or parsed_host.netloc
        
        # Determine default port based on schema
        if server_port_backend is None:
            if schema == "https":
                port = 443
            elif schema == "http":
                port = 80
            else:
                port = 8000
        else:
            port = server_port_backend
    else:
        # No schema present - treat as plain hostname/IP
        schema = "http"
        hostname = server_host
        port = server_port_backend if server_port_backend is not None else 8000
    
    # Build the server URL for Gradio app
    if (schema == "http" and port == 80) or (schema == "https" and port == 443):
        # Don't include port in URL if it's the default for the schema
        default_server_url = f"{schema}://{hostname}"
    else:
        default_server_url = f"{schema}://{hostname}:{port}"
    
    server_process = None
    
    try:
        if with_server:
            typer.echo("🚀 Starting GluRPC server for local testing...")
            # For local server, always use http and the specified hostname/port
            local_host = hostname if not parsed_host.scheme else "127.0.0.1"
            server_process = start_server(
                host=local_host,
                port=port,
                background=True,
                wait=True
            )
            
            if server_process is None and not is_server_running(f"http://{local_host}:{port}"):
                typer.echo("❌ Failed to start server", err=True)
                raise typer.Exit(1)
        
        typer.echo(f"🚀 Launching Gradio client on {server_name}:{server_port}...")
        typer.echo(f"   Default server URL: {default_server_url}")
        
        if with_server:
            typer.echo(f"   Local server running at {default_server_url}")
        
        launch_app(
            share=share,
            server_name=server_name,
            server_port=server_port,
            default_server_url=default_server_url
        )
        
    except KeyboardInterrupt:
        typer.echo("\n🛑 Shutting down...")
    finally:
        if server_process is not None:
            stop_server(server_process)


@app.command()
def server(
    host: str = typer.Option(
        "0.0.0.0",
        "--host",
        help="Host to bind to"
    ),
    port: int = typer.Option(
        8000,
        "--port",
        help="Port to bind to"
    )
):
    """Start only the GluRPC server (no client interface).
    
    This is useful for running the server separately.
    
    Example:
    
    glucosedao-client server --host 0.0.0.0 --port 8000
    """
    typer.echo(f"🚀 Starting GluRPC server on {host}:{port}...")
    
    try:
        start_server(
            host=host,
            port=port,
            background=False,
            wait=False
        )
    except KeyboardInterrupt:
        typer.echo("\n🛑 Server stopped")


@app.command()
def check(
    url: str = typer.Option(
        "http://localhost:8000",
        "--url",
        help="Server URL to check"
    )
):
    """Check if GluRPC server is running and healthy.
    
    Example:
    
    glucosedao-client check --url http://localhost:8000
    """
    typer.echo(f"🔍 Checking server at {url}...")
    
    if is_server_running(url):
        typer.echo(f"✅ Server is running and healthy at {url}")
    else:
        typer.echo(f"❌ Server is not responding at {url}")
        raise typer.Exit(1)


def main():
    """Main entry point for the CLI."""
    app()


def dev():
    """Shortcut to launch client with server on 0.0.0.0."""
    import sys
    sys.argv = ["glucosedao-client", "launch", "--with-server", "--host", "0.0.0.0"]
    app()


def client():
    """Shortcut to launch client only."""
    import sys
    sys.argv = ["glucosedao-client", "launch"]
    app()


def check_shortcut():
    """Shortcut to check server health."""
    import sys
    sys.argv = ["glucosedao-client", "check"]
    app()


if __name__ == "__main__":
    main()

