"""Server management utilities for local testing."""
import subprocess
import time
import sys
import logging
from pathlib import Path
from typing import Optional
import httpx

# Configure logger
logger = logging.getLogger("glurpc.server")
logger.setLevel(logging.DEBUG)


def is_server_running(base_url: str = "http://localhost:8000", timeout: float = 2.0) -> bool:
    """Check if GluRPC server is running.
    
    Args:
        base_url: Base URL of the server
        timeout: Request timeout in seconds
        
    Returns:
        True if server is responding, False otherwise
    """
    try:
        response = httpx.get(f"{base_url}/health", timeout=timeout)
        return response.status_code == 200
    except Exception:
        return False


def wait_for_server(
    base_url: str = "http://localhost:8000",
    max_wait: float = 60.0,
    check_interval: float = 1.0
) -> bool:
    """Wait for server to become available.
    
    Args:
        base_url: Base URL of the server
        max_wait: Maximum time to wait in seconds
        check_interval: Time between checks in seconds
        
    Returns:
        True if server became available, False if timeout
    """
    logger.info(f"Waiting for server at {base_url}")
    elapsed = 0.0
    while elapsed < max_wait:
        if is_server_running(base_url):
            logger.info(f"Server is available at {base_url}")
            return True
        
        time.sleep(check_interval)
        elapsed += check_interval
        logger.debug(f"Waiting for server... ({elapsed:.1f}s/{max_wait}s)")
    
    logger.error(f"Server did not become available within {max_wait}s")
    return False


def start_server(
    host: str = "0.0.0.0",
    port: int = 8000,
    background: bool = True,
    wait: bool = True
) -> Optional[subprocess.Popen]:
    """Start the GluRPC server locally.
    
    Args:
        host: Host to bind to
        port: Port to bind to
        background: If True, run server in background and return process handle
        wait: If True, wait for server to be ready before returning
        
    Returns:
        Process handle if background=True, None otherwise
    """
    base_url = f"http://{host}:{port}"
    logger.info(f"Starting server at {base_url}")
    
    # Check if already running
    if is_server_running(base_url):
        logger.info(f"Server already running at {base_url}")
        return None
    
    # Start server process
    if background:
        process = subprocess.Popen(
            [
                sys.executable, "-m", "uvicorn",
                "glurpc.app:app",
                "--host", host,
                "--port", str(port)
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if wait:
            if wait_for_server(base_url, max_wait=60.0):
                logger.info("Server started successfully")
            else:
                logger.error("Server failed to start")
                process.terminate()
                return None
        
        return process
    else:
        # Run in foreground (blocking)
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "glurpc.app:app",
            "--host", host,
            "--port", str(port)
        ])
        return None


def stop_server(process: subprocess.Popen, timeout: float = 10.0):
    """Stop a running server process gracefully.
    
    Args:
        process: Process handle returned by start_server
        timeout: Time to wait for graceful shutdown before killing
    """
    logger.info("Stopping server")
    
    process.terminate()
    
    try:
        process.wait(timeout=timeout)
        logger.info("Server stopped gracefully")
    except subprocess.TimeoutExpired:
        logger.warning("Server did not stop gracefully, forcing kill")
        process.kill()
        process.wait()
        logger.info("Server stopped forcefully")

