"""Gradio frontend for GluRPC glucose prediction client."""
import base64
import io
import os
import tempfile
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List
from collections import deque
from datetime import datetime

import gradio as gr
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from glucosedao_client.client import GluRPCClient, GluRPCConfig

# Setup standard logging
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
logname = f"app_{timestamp}.log"
LOG_FILE = Path("logs") / logname
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

# Configure logger
logger = logging.getLogger("glurpc.app")
logger.setLevel(logging.DEBUG)

# File handler
file_handler = logging.FileHandler(LOG_FILE)
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Load API key from environment
DEFAULT_API_KEY = os.getenv("GLURPC_API_KEY", "")

# Global state
client: Optional[GluRPCClient] = None
current_handle: Optional[str] = None
current_warnings: Optional[Dict[str, Any]] = None
current_unified_csv: Optional[str] = None
current_total_samples: Optional[int] = None

# Request cancellation tracking
pending_request_id: Optional[int] = None
request_counter: int = 0

# Client-side stats tracking
client_request_times: list[float] = []
MAX_REQUEST_TIMES = 100  # Keep last 100 request times

# Health metrics history for graphing
MAX_HEALTH_HISTORY = 60  # Keep 60 seconds of history (1 sample per second)
health_history: deque = deque(maxlen=MAX_HEALTH_HISTORY)
health_timestamps: deque = deque(maxlen=MAX_HEALTH_HISTORY)
health_polling_enabled: bool = True  # Control health polling


def initialize_client(server_url: str, api_key: Optional[str] = None) -> GluRPCClient:
    """Initialize the GluRPC client with configuration.
    
    Args:
        server_url: Base URL of the GluRPC server
        api_key: Optional API key for authentication
        
    Returns:
        Initialized GluRPCClient
    """
    config = GluRPCConfig(
        base_url=server_url,
        api_key=api_key if api_key else None
    )
    return GluRPCClient(config)


def format_warnings_for_display(warnings: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Format warning information for Gradio display.
    
    Args:
        warnings: Warning dictionary from server response
        
    Returns:
        Formatted warning information
    """
    if not warnings:
        return {
            'has_warnings': False,
            'warning_messages': [],
            'warning_count': 0
        }
    
    has_warnings = warnings.get('has_warnings', False)
    
    if not has_warnings:
        return {
            'has_warnings': False,
            'warning_messages': [],
            'warning_count': 0
        }
    
    # Extract warning messages from the server response
    warning_messages = []
    
    # The server returns warnings in a specific format
    # Check various possible keys
    if 'warning_messages' in warnings:
        warning_messages = warnings['warning_messages']
    elif 'messages' in warnings:
        warning_messages = warnings['messages']
    
    # Filter out time_duplicates warnings (irrelevant)
    filtered_messages = [msg for msg in warning_messages if 'TIME_DUPLICATES' not in msg.upper()]
    
    return {
        'has_warnings': len(filtered_messages) > 0,
        'warning_messages': filtered_messages,
        'warning_count': len(filtered_messages)
    }


def create_warning_display(warning_info: Dict[str, Any]) -> Dict[str, Any]:
    """Create HTML for warning display.
    
    Args:
        warning_info: Warning information dictionary
        
    Returns:
        Gradio update dictionary with HTML content
    """
    if not warning_info or not warning_info.get('has_warnings', False):
        # Green light - all good
        status_html = """
        <div style="padding: 15px; border-radius: 8px; background-color: #d4edda; border: 2px solid #28a745; margin: 10px 0;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <div style="width: 30px; height: 30px; border-radius: 50%; background-color: #28a745; box-shadow: 0 0 10px #28a745;"></div>
                <div style="flex: 1;">
                    <h3 style="margin: 0; color: #155724;">✅ Data Quality: GOOD</h3>
                    <p style="margin: 5px 0 0 0; color: #155724;">No quality issues detected. Data is ready for inference.</p>
                </div>
            </div>
        </div>
        """
        return gr.update(value=status_html, visible=True)
    else:
        # Red light - warnings present
        warning_messages = warning_info.get('warning_messages', [])
        warning_list_html = "".join([f"<li>{msg}</li>" for msg in warning_messages])
        
        status_html = f"""
        <div style="padding: 15px; border-radius: 8px; background-color: #f8d7da; border: 2px solid #dc3545; margin: 10px 0;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <div style="width: 30px; height: 30px; border-radius: 50%; background-color: #dc3545; box-shadow: 0 0 10px #dc3545;"></div>
                <div style="flex: 1;">
                    <h3 style="margin: 0; color: #721c24;">⚠️ Data Quality: WARNINGS DETECTED</h3>
                    <p style="margin: 5px 0; color: #721c24;"><strong>{warning_info.get('warning_count', 0)} warning(s) found:</strong></p>
                    <ul style="margin: 5px 0 0 20px; color: #721c24;">
                        {warning_list_html}
                    </ul>
                </div>
            </div>
        </div>
        """
        return gr.update(value=status_html, visible=True)


def process_and_prepare(
    file: Optional[tempfile._TemporaryFileWrapper],
    server_url: str,
    api_key: str
) -> Tuple[gr.Slider, gr.Markdown, Dict[str, Any], str, gr.DownloadButton, int]:
    """Process uploaded file and prepare for prediction.
    
    Args:
        file: Uploaded file (can be None if user clears selection)
        server_url: GluRPC server URL
        api_key: API key for authentication
        
    Returns:
        Tuple of (slider update, markdown update, warning info, status message, download button update, total_samples)
    """
    global client, current_handle, current_warnings, current_unified_csv, current_total_samples
    
    # Handle file deselection (user pressed X to clear)
    if file is None:
        logger.info("File selection cleared by user")
        # Reset global state
        current_handle = None
        current_warnings = None
        current_unified_csv = None
        current_total_samples = None
        
        return (
            gr.update(visible=False),  # Hide slider
            gr.update(visible=False),  # Hide sample count
            {},  # Empty warning info
            "📁 Please upload a file to begin",
            gr.update(visible=False),  # Hide CSV download button
            1  # Default total_samples
        )
    
    logger.info(f"Processing file: {file.name}")
    start_time = time.time()
    
    # Debug API key handling
    api_key_debug = f"{api_key[:16]}..." if api_key and len(api_key) > 8 else "(empty)" if not api_key else api_key
    logger.debug(f"API key received: {api_key_debug}")
    
    try:
        # Initialize client if needed
        if client is None or client.config.base_url != server_url:
            client = initialize_client(server_url, api_key if api_key else None)
            logger.info(f"Initialized client for server: {server_url}, api_key: {api_key_debug}")
        
        logger.info("Converting file to unified format...")
        
        # Step 1: Convert to unified format
        convert_start = time.time()
        convert_response = client.convert_to_unified(file.name)
        convert_duration = time.time() - convert_start
        
        if convert_response.error:
            raise RuntimeError(f"Conversion failed: {convert_response.error}")
        
        if not convert_response.csv_content:
            raise RuntimeError("No CSV content returned from conversion")
        
        # Store the unified CSV for later saving
        current_unified_csv = convert_response.csv_content
        
        logger.info(f"Converted to unified format in {convert_duration:.3f}s, size={len(convert_response.csv_content)} bytes")
        
        # Step 2: Process unified CSV
        logger.info("Processing unified CSV...")
        process_start = time.time()
        process_response = client.process_unified(convert_response.csv_content)
        process_duration = time.time() - process_start
        
        # Log the complete response structure
        logger.debug(f"Process Response: handle={process_response.handle}, total_samples={process_response.total_samples}, warnings={process_response.warnings}")
        
        if process_response.error:
            raise RuntimeError(f"Processing failed: {process_response.error}")
        
        if not process_response.handle:
            raise RuntimeError("No handle returned from processing")
        
        current_handle = process_response.handle
        current_warnings = process_response.warnings
        
        # Handle case where total_samples is None
        if process_response.total_samples is None:
            logger.warning("total_samples is None, using default value of 1")
            max_index = 0
            total_samples = 1
        else:
            max_index = process_response.total_samples - 1
            total_samples = process_response.total_samples
        
        # Store total_samples globally for index conversion
        current_total_samples = total_samples
        
        logger.info(f"Processed data in {process_duration:.3f}s, handle={current_handle[:8]}, total_samples={total_samples}")
        
        # Format warnings
        warning_info = format_warnings_for_display(process_response.warnings)
        
        if warning_info['has_warnings']:
            logger.warning(f"Data quality warnings: {warning_info['warning_messages']}")
        
        total_duration = time.time() - start_time
        logger.info(f"Total processing time: {total_duration:.3f}s")
        
        return (
            gr.update(
                minimum=0,
                maximum=max_index,
                value=max_index,
                step=1,
                label="Select Sample Index",
                visible=True
            ),
            gr.update(
                value=f"Total number of test samples: {total_samples}",
                visible=True
            ),
            warning_info,
            "✅ File processed successfully",
            gr.update(visible=True),  # Enable save button
            total_samples  # Return total_samples for state
        )
        
    except Exception as e:
        duration = time.time() - start_time
        
        # Provide helpful error message for 403 errors
        error_message = str(e)
        if "403" in error_message or "Forbidden" in error_message:
            logger.error(f"Authentication failed after {duration:.3f}s: {e}", exc_info=True)
            error_message = "Authentication failed (403 Forbidden). Please check your API key."
        else:
            logger.error(f"Processing failed after {duration:.3f}s: {e}", exc_info=True)
        
        warning_info = {
            'has_warnings': True,
            'warning_messages': [f"Error during processing: {error_message}"],
            'warning_count': 1
        }
        
        return (
            gr.update(visible=False),
            gr.update(visible=False),
            warning_info,
            f"❌ Error: {error_message}",
            gr.update(visible=False),  # Keep save button hidden on error
            1  # Return default total_samples on error
        )


def predict_glucose(ind: int, total_samples: int) -> Tuple[Optional[go.Figure], str]:
    """Generate prediction plot for a specific sample index.
    
    Args:
        ind: Sample index from slider (0 = first, total_samples-1 = last)
        total_samples: Total number of samples in the dataset
        
    Returns:
        Tuple of (Plotly Figure object or None, status message)
    """
    global client, current_handle, pending_request_id, request_counter, client_request_times
    
    # Assign unique ID to this request
    request_counter += 1
    my_request_id = request_counter
    old_request_id = pending_request_id
    pending_request_id = my_request_id
    
    # Convert positive slider index to negative server index
    # Slider: 0 (first) ... N-1 (last)
    # Server: -(N-1) (first) ... 0 (last)
    # Formula: server_index = slider_index - total_samples + 1
    server_index = ind - total_samples + 1
    
    logger.info(f"Slider event: request_id={my_request_id}, cancelled_request_id={old_request_id}, index={ind}, server_index={server_index}, total_samples={total_samples}")
    request_start = time.time()
    
    try:
        if client is None:
            logger.error("Client not initialized")
            return None, "❌ Client not initialized. Please process a file first."
        
        if current_handle is None:
            logger.error("No data loaded")
            return None, "❌ No data loaded. Please upload and process a file first."
        
        # Capture the handle we're requesting for - to detect if file changed
        request_handle = current_handle
        
        # Note: The server now tracks concurrent requests and will cancel previous incomplete
        # requests for the same (handle, index) pair automatically. We just need to avoid
        # making the request if a newer one is already pending on the client side.
        
        # Check if this request is still the latest before making network call
        if my_request_id != pending_request_id:
            elapsed = time.time() - request_start
            logger.info(f"Request cancelled before network call: request_id={my_request_id}, cancelled_after={elapsed:.3f}s")
            return None, f"⏭️ Skipped (newer request pending)"
        
        # Check if the file was changed/unloaded
        if request_handle != current_handle:
            elapsed = time.time() - request_start
            logger.info(f"Request cancelled - file changed: request_id={my_request_id}, old_handle={request_handle[:8] if request_handle else 'None'}, new_handle={current_handle[:8] if current_handle else 'None'}")
            return None, f"⏭️ Skipped (file changed)"
        
        logger.debug(f"Requesting plot: request_id={my_request_id}, handle={request_handle[:8]}, server_index={server_index}")
        
        # Get plot from server using negative index
        # Server automatically cancels previous incomplete requests for same (handle, index)
        plot_start = time.time()
        plot_data = client.draw_plot(request_handle, server_index, force_calculate=False)
        network_duration = time.time() - plot_start
        
        # Check again if this request is still the latest after network call
        if my_request_id != pending_request_id:
            elapsed = time.time() - request_start
            logger.info(f"Request cancelled after network call: request_id={my_request_id}, cancelled_after={elapsed:.3f}s")
            return None, f"⏭️ Skipped (newer request completed)"
        
        # Check again if the file was changed/unloaded after network call
        if request_handle != current_handle:
            elapsed = time.time() - request_start
            logger.info(f"Request discarded - file changed during network call: request_id={my_request_id}, request_handle={request_handle[:8]}, current_handle={current_handle[:8] if current_handle else 'None'}")
            return None, f"⏭️ Discarded (file changed)"
        
        # Convert the JSON dictionary to a proper Plotly Figure object
        fig = go.Figure(plot_data)
        
        # Update layout to ensure full width and responsive sizing
        fig.update_layout(
            autosize=True,
            width=None,
            height=600,
            margin=dict(l=50, r=50, t=80, b=80)
        )
        
        total_duration = time.time() - request_start
        
        # Track request time for stats
        client_request_times.append(total_duration * 1000)  # Convert to ms
        if len(client_request_times) > MAX_REQUEST_TIMES:
            client_request_times.pop(0)
        
        logger.info(f"Plot delivered: request_id={my_request_id}, slider_index={ind}, server_index={server_index}, network_time={network_duration:.3f}s, total_time={total_duration:.3f}s")
        
        return fig, f"✅ Generated plot for sample {ind}"
        
    except RuntimeError as e:
        if "Request cancelled" in str(e):
            duration = time.time() - request_start
            logger.info(f"Plot request cancelled by server: request_id={my_request_id}, duration={duration:.3f}s")
            return None, f"⏭️ Request cancelled (newer request processing)"
        duration = time.time() - request_start
        logger.error(f"Plot generation failed: request_id={my_request_id}, duration={duration:.3f}s, slider_index={ind}, server_index={server_index}, error={e}", exc_info=True)
        return None, f"❌ Error: {str(e)}"
    except Exception as e:
        duration = time.time() - request_start
        logger.error(f"Plot generation failed: request_id={my_request_id}, duration={duration:.3f}s, slider_index={ind}, server_index={server_index}, error={e}", exc_info=True)
        return None, f"❌ Error: {str(e)}"


def save_unified_csv() -> str:
    """Save the current unified CSV to a temporary file for download.
    
    Returns:
        File path for Gradio to download
    """
    global current_unified_csv
    
    logger.info("Saving unified CSV")
    
    try:
        if current_unified_csv is None:
            logger.error("No unified CSV data available")
            # Return a temporary empty file with error message
            temp_file = tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.txt',
                prefix='error_',
                delete=False
            )
            temp_file.write("No unified CSV data available. Please upload and process a file first.")
            temp_file.flush()
            temp_file.close()
            return temp_file.name
        
        # Create a descriptive filename with timestamp
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create a temporary file
        temp_file = tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.csv',
            prefix=f'unified_glucose_data_{timestamp_str}_',
            delete=False
        )
        
        temp_file.write(current_unified_csv)
        temp_file.flush()
        temp_file.close()
        
        logger.info(f"Saved unified CSV: path={temp_file.name}, size={len(current_unified_csv)} bytes")
        
        return temp_file.name
        
    except Exception as e:
        logger.error(f"Save CSV failed: {e}", exc_info=True)
        # Return a temporary file with error message
        temp_file = tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.txt',
            prefix='error_',
            delete=False
        )
        temp_file.write(f"Error: {str(e)}")
        temp_file.flush()
        temp_file.close()
        return temp_file.name


def save_plot_html(plot_fig: Optional[go.Figure]) -> str:
    """Save the current plot as HTML file for download.
    
    Args:
        plot_fig: Plotly Figure object of the current plot
        
    Returns:
        File path for Gradio to download
    """
    logger.info("Saving plot HTML")
    
    try:
        if plot_fig is None:
            logger.error("No plot data available")
            # Return a temporary empty file with error message
            temp_file = tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.txt',
                prefix='error_',
                delete=False
            )
            temp_file.write("No plot available. Please upload and process a file first.")
            temp_file.flush()
            temp_file.close()
            return temp_file.name
        
        # Create a descriptive filename with timestamp
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create a temporary HTML file
        temp_file = tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.html',
            prefix=f'glucose_plot_{timestamp_str}_',
            delete=False
        )
        
        # Use Plotly's built-in method to save as HTML
        plot_fig.write_html(temp_file.name)
        temp_file.close()
        
        # Get file size
        file_size = Path(temp_file.name).stat().st_size
        logger.info(f"Saved plot HTML: path={temp_file.name}, size={file_size} bytes")
        
        return temp_file.name
        
    except Exception as e:
        logger.error(f"Save plot failed: {e}", exc_info=True)
        # Return a temporary file with error message
        temp_file = tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.txt',
            prefix='error_',
            delete=False
        )
        temp_file.write(f"Error: {str(e)}")
        temp_file.flush()
        temp_file.close()
        return temp_file.name


def check_server_health(server_url: str) -> Tuple[str, go.Figure, go.Figure]:
    """Check if server is healthy and return status with separate metrics graphs.
    
    Args:
        server_url: GluRPC server URL
        
    Returns:
        Tuple of (HTML formatted static metrics, Request times figure, Queues/Other figure)
    """
    global health_history, health_timestamps
    
    logger.debug(f"Health check for server: {server_url}")
    
    try:
        temp_client = initialize_client(server_url, None)
        health = temp_client.health()
        temp_client.close()
        
        # Store health data for graphing
        current_time = time.time()
        health_history.append(health)
        health_timestamps.append(current_time)
        
        # Status lamps
        if health.status == "ok":
            status_lamp = "🟢"
            status_text = "OK"
            status_color = "#28a745"
        elif health.status == "degraded":
            status_lamp = "🟡"
            status_text = "DEGRADED"
            status_color = "#ffc107"
        else:
            status_lamp = "🔴"
            status_text = "ERROR"
            status_color = "#dc3545"
        
        models_lamp = "🟢" if health.models_initialized else "🔴"
        models_text = "LOADED" if health.models_initialized else "UNLOADED"
        
        device_lamp = "🟢" if "cuda" in health.device.lower() or "gpu" in health.device.lower() else "🔵"
        device_text = "GPU" if "cuda" in health.device.lower() or "gpu" in health.device.lower() else "CPU"
        
        load_colors = {
            "idle": "#28a745",
            "lightly loaded": "#5bc0de",
            "heavily loaded": "#ffc107",
            "overloaded": "#ff851b",
            "full": "#dc3545"
        }
        load_color = load_colors.get(health.load_status, "#6c757d")
        
        # Horizontal counters layout - 2x5 symmetric grid (added min/max from graph)
        static_html = f"""
        <div style="padding: 12px; border-radius: 8px; background-color: #f8f9fa; border: 2px solid {status_color}; margin: 10px 0;">
            <!-- Status Lamps Row -->
            <div style="display: flex; gap: 20px; align-items: center; margin-bottom: 12px; flex-wrap: wrap;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 20px;">{status_lamp}</span>
                    <span style="font-weight: bold; color: {status_color};">{status_text}</span>
                </div>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 20px;">{models_lamp}</span>
                    <span style="font-weight: bold;">{models_text}</span>
                </div>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 20px;">{device_lamp}</span>
                    <span style="font-weight: bold;">{device_text}</span>
                </div>
                <div style="padding: 4px 12px; border-radius: 15px; background-color: {load_color}; color: white; font-weight: bold; font-size: 12px;">
                    {health.load_status.upper()}
                </div>
            </div>
            
            <!-- Counters Grid - 2x5 -->
            <div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px;">
                <div style="padding: 8px; background-color: white; border-radius: 4px; border-left: 3px solid #007bff;">
                    <div style="font-size: 10px; color: #6c757d; margin-bottom: 3px;">HTTP REQ</div>
                    <div style="font-size: 20px; font-weight: bold; color: #007bff;">{health.total_http_requests}</div>
                </div>
                
                <div style="padding: 8px; background-color: white; border-radius: 4px; border-left: 3px solid #dc3545;">
                    <div style="font-size: 10px; color: #6c757d; margin-bottom: 3px;">HTTP ERR</div>
                    <div style="font-size: 20px; font-weight: bold; color: #dc3545;">{health.total_http_errors}</div>
                </div>
                
                <div style="padding: 8px; background-color: white; border-radius: 4px; border-left: 3px solid #28a745;">
                    <div style="font-size: 10px; color: #6c757d; margin-bottom: 3px;">CALC RUNS</div>
                    <div style="font-size: 20px; font-weight: bold; color: #28a745;">{health.total_calc_runs}</div>
                </div>
                
                <div style="padding: 8px; background-color: white; border-radius: 4px; border-left: 3px solid #ffc107;">
                    <div style="font-size: 10px; color: #6c757d; margin-bottom: 3px;">CALC ERR</div>
                    <div style="font-size: 20px; font-weight: bold; color: #ffc107;">{health.total_calc_errors}</div>
                </div>
                
                <div style="padding: 8px; background-color: white; border-radius: 4px; border-left: 3px solid #6610f2;">
                    <div style="font-size: 10px; color: #6c757d; margin-bottom: 3px;">INF ERR</div>
                    <div style="font-size: 20px; font-weight: bold; color: #6610f2;">{health.total_inference_errors}</div>
                </div>
                
                <div style="padding: 8px; background-color: white; border-radius: 4px; border-left: 3px solid #17a2b8;">
                    <div style="font-size: 10px; color: #6c757d; margin-bottom: 3px;">CACHE</div>
                    <div style="font-size: 20px; font-weight: bold; color: #17a2b8;">{health.cache_size}</div>
                </div>
                
                <div style="padding: 8px; background-color: white; border-radius: 4px; border-left: 3px solid #20c997;">
                    <div style="font-size: 10px; color: #6c757d; margin-bottom: 3px;">PRIO AVAIL</div>
                    <div style="font-size: 20px; font-weight: bold; color: #20c997;">{health.available_priority_models}</div>
                </div>
                
                <div style="padding: 8px; background-color: white; border-radius: 4px; border-left: 3px solid #e83e8c;">
                    <div style="font-size: 10px; color: #6c757d; margin-bottom: 3px;">GEN AVAIL</div>
                    <div style="font-size: 20px; font-weight: bold; color: #e83e8c;">{health.available_general_models}</div>
                </div>
                
                <div style="padding: 8px; background-color: white; border-radius: 4px; border-left: 3px solid #17a2b8;">
                    <div style="font-size: 10px; color: #6c757d; margin-bottom: 3px;">MIN REQ</div>
                    <div style="font-size: 20px; font-weight: bold; color: #17a2b8;">{health.min_request_time_ms:.1f}ms</div>
                </div>
                
                <div style="padding: 8px; background-color: white; border-radius: 4px; border-left: 3px solid #dc3545;">
                    <div style="font-size: 10px; color: #6c757d; margin-bottom: 3px;">MAX REQ</div>
                    <div style="font-size: 20px; font-weight: bold; color: #dc3545;">{health.max_request_time_ms/1000:.2f}s</div>
                </div>
            </div>
        </div>
        """
        
        # Create separate graphs
        request_times_fig, queues_fig = create_health_metrics_graphs()
        
        return static_html, request_times_fig, queues_fig
        
    except Exception as e:
        error_html = f"""
        <div style="padding: 15px; border-radius: 8px; background-color: #f8d7da; border: 2px solid #dc3545; margin: 10px 0;">
            <h3 style="margin: 0; color: #721c24;">❌ Server Unavailable</h3>
            <p style="margin: 10px 0 0 0; color: #721c24;">Error: {str(e)}</p>
        </div>
        """
        empty_fig = go.Figure()
        empty_fig.update_layout(title="No data")
        return error_html, empty_fig, empty_fig


def create_health_metrics_graphs() -> Tuple[go.Figure, go.Figure]:
    """Create separate graphs for request times and queues/other metrics.
    
    Returns:
        Tuple of (Request times figure, Queues/Other figure)
    """
    global health_history, health_timestamps, client_request_times
    
    if len(health_history) == 0:
        empty_fig1 = go.Figure()
        empty_fig1.update_layout(title="Waiting...")
        empty_fig2 = go.Figure()
        empty_fig2.update_layout(title="Waiting...")
        return empty_fig1, empty_fig2
    
    # Convert timestamps to relative seconds
    if len(health_timestamps) > 0:
        base_time = health_timestamps[0]
        relative_times = [t - base_time for t in health_timestamps]
    else:
        relative_times = []
    
    # Extract server metrics
    avg_request_times = [h.avg_request_time_ms for h in health_history]
    median_request_times = [h.median_request_time_ms for h in health_history]
    
    # Figure 1: Request Times (Server only - clean ms scale)
    fig1 = go.Figure()
    
    fig1.add_trace(go.Scatter(
        x=relative_times, y=avg_request_times, name="Avg", 
        mode='lines', line=dict(color='#007bff', width=2)
    ))
    
    fig1.add_trace(go.Scatter(
        x=relative_times, y=median_request_times, name="Median",
        mode='lines', line=dict(color='#28a745', width=2)
    ))
    
    fig1.update_layout(
        height=220,
        xaxis_title="Time (s)",
        yaxis_title="Request Time (ms)",
        margin=dict(l=50, r=20, t=5, b=40),
        hovermode='x unified',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            font=dict(size=9)
        )
    )
    
    # Figure 2: Queues + Client Avg + Model Fulfillment
    avg_fulfillment_times = [h.avg_fulfillment_time_ms for h in health_history]
    inference_queue_sizes = [h.inference_queue_size for h in health_history]
    calc_queue_sizes = [h.calc_queue_size for h in health_history]
    
    fig2 = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Primary Y-axis: Queues
    fig2.add_trace(go.Scatter(
        x=relative_times, y=inference_queue_sizes, name="Inf Q",
        mode='lines+markers', line=dict(color='#20c997', width=2),
        marker=dict(size=4)
    ), secondary_y=False)
    
    fig2.add_trace(go.Scatter(
        x=relative_times, y=calc_queue_sizes, name="Calc Q",
        mode='lines+markers', line=dict(color='#e83e8c', width=2),
        marker=dict(size=4)
    ), secondary_y=False)
    
    # Secondary Y-axis: Times (ms) - Client and Model Fulfillment
    fig2.add_trace(go.Scatter(
        x=relative_times, y=avg_fulfillment_times, name="Model Acq",
        mode='lines', line=dict(color='#fd7e14', width=2, dash='dash')
    ), secondary_y=True)
    
    # Add client-side request times
    if len(client_request_times) > 0:
        client_avg = sum(client_request_times) / len(client_request_times)
        client_avgs = [client_avg] * len(relative_times)
        
        fig2.add_trace(go.Scatter(
            x=relative_times, y=client_avgs, name="Client Avg",
            mode='lines', line=dict(color='#6610f2', width=2, dash='dashdot')
        ), secondary_y=True)
    
    fig2.update_xaxes(title_text="Time (s)")
    fig2.update_yaxes(title_text="Queue Size", secondary_y=False)
    fig2.update_yaxes(title_text="Time (ms)", secondary_y=True)
    
    fig2.update_layout(
        height=220,
        margin=dict(l=50, r=60, t=5, b=40),
        hovermode='x unified',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            font=dict(size=9)
        )
    )
    
    return fig1, fig2


def poll_health(server_url: str) -> Tuple[str, go.Figure, go.Figure]:
    """Poll server health for continuous updates.
    
    This function is called by Gradio's timer mechanism to update health metrics.
    
    Args:
        server_url: GluRPC server URL
        
    Returns:
        Tuple of (HTML formatted static metrics, Request times figure, Queues/Other figure)
    """
    global health_polling_enabled
    
    if not health_polling_enabled:
        empty_fig = go.Figure()
        return "", empty_fig, empty_fig
    
    return check_server_health(server_url)


def create_gradio_app(default_server_url: str = "http://localhost:8000") -> gr.Blocks:
    """Create and configure the Gradio application.
    
    Args:
        default_server_url: Default GluRPC server URL to use
        
    Returns:
        Configured Gradio Blocks app
    """
    logger.info(f"Creating Gradio app with default_server_url={default_server_url}")
    
    with gr.Blocks(title="GluRPC Client - Glucose Prediction") as app:
        gr.Markdown("# 🩸 Glucose Prediction Tool (GluRPC Client)")
        gr.Markdown("Upload a CGM data file to get glucose predictions from the GluRPC server")
        
        with gr.Accordion("⚙️ Server Configuration", open=False):
            with gr.Row():
                server_url_input = gr.Textbox(
                    value=default_server_url,
                    label="GluRPC Server URL",
                    placeholder=default_server_url
                )
                api_key_input = gr.Textbox(
                    value=DEFAULT_API_KEY,
                    label="API Key (optional)",
                    placeholder="Enter API key if required",
                    type="password"
                )
            
            health_button = gr.Button("🔄 Manual Health Check")
        
        # Server health tracker - three columns: counters, request times, queues/other
        with gr.Accordion("📊 Server Health Monitor", open=True):
            gr.Markdown("*Updates every second automatically*")
            with gr.Row(equal_height=True):
                # Left 1/3: Counters
                with gr.Column(scale=1):
                    health_status = gr.HTML(label="Status & Counters", visible=True)
                # Middle 1/3: Request Times
                with gr.Column(scale=1):
                    health_graph_requests = gr.Plot(label="", visible=True, show_label=False)
                # Right 1/3: Queues + Other
                with gr.Column(scale=1):
                    health_graph_queues = gr.Plot(label="", visible=True, show_label=False)
        
        file_input = gr.File(label="📁 Upload CGM Data File (CSV)")
        
        status_message = gr.Markdown(visible=True)
        
        # Warning display
        warning_display = gr.HTML(
            label="Data Quality Status",
            visible=False
        )
        
        # Download button for unified CSV at top
        download_csv_btn = gr.DownloadButton(
            "💾 Download Unified CSV",
            visible=False,
            variant="secondary",
            size="sm"
        )
        
        with gr.Row():
            index_slider = gr.Slider(
                minimum=0,
                maximum=100,
                value=10,
                step=1,
                label="Select Sample Index",
                visible=False
            )
        
        sample_count = gr.Markdown(visible=False)
        
        plot_output = gr.Plot(label="📊 Glucose Prediction Plot")
        
        # Download plot button directly under the plot
        download_plot_btn = gr.DownloadButton(
            "📊 Download Plot (HTML)",
            visible=True,
            interactive=False,
            variant="secondary",
            size="sm"
        )
        
        plot_status = gr.Markdown(visible=True)
        
        # Store warning info in state
        warning_state = gr.State(value={})
        # Store total samples in state for index conversion
        total_samples_state = gr.State(value=1)
        # Store server URL in state - initialized with default_server_url
        # This ensures the value is available immediately when app.load() runs
        server_url_state = gr.State(value=default_server_url)
        # Store API key in state - initialized with DEFAULT_API_KEY from environment
        # This ensures the value is available immediately and not empty string from uninitialized textbox
        api_key_state = gr.State(value=DEFAULT_API_KEY)
        
        # Sync textbox changes to state
        server_url_input.change(
            fn=lambda url: url,
            inputs=[server_url_input],
            outputs=[server_url_state],
            queue=False
        )
        
        # Sync API key textbox changes to state
        api_key_input.change(
            fn=lambda key: key,
            inputs=[api_key_input],
            outputs=[api_key_state],
            queue=False
        )
        
        # Initialize server health on load - use state which has immediate value
        app.load(
            fn=check_server_health,
            inputs=[server_url_state],
            outputs=[health_status, health_graph_requests, health_graph_queues]
        )
        
        # Set up health polling timer - every 1 second
        health_timer = gr.Timer(value=1.0, active=True)
        health_timer.tick(
            fn=poll_health,
            inputs=[server_url_state],
            outputs=[health_status, health_graph_requests, health_graph_queues]
        )
        
        # Manual health button click
        health_button.click(
            fn=check_server_health,
            inputs=[server_url_state],
            outputs=[health_status, health_graph_requests, health_graph_queues]
        )
        
        # File upload event - use state variables to ensure correct values
        upload_event = file_input.change(
            fn=process_and_prepare,
            inputs=[file_input, server_url_state, api_key_state],
            outputs=[index_slider, sample_count, warning_state, status_message, download_csv_btn, total_samples_state],
            queue=True
        )
        
        # Display warnings after processing
        upload_event.then(
            fn=create_warning_display,
            inputs=[warning_state],
            outputs=warning_display,
            queue=True
        )
        
        # Automatically generate plot after upload completes
        plot_event = upload_event.then(
            fn=predict_glucose,
            inputs=[index_slider, total_samples_state],
            outputs=[plot_output, plot_status],
            queue=True
        )
        
        # Enable download plot button after first plot is generated
        plot_event.then(
            fn=lambda: gr.update(interactive=True),
            inputs=[],
            outputs=[download_plot_btn],
            queue=False
        )
        
        # Allow manual update when slider changes
        # Use release event instead of change to avoid triggering on initialization
        slider_event = index_slider.release(
            fn=predict_glucose,
            inputs=[index_slider, total_samples_state],
            outputs=[plot_output, plot_status],
            queue=True
        )
        
        # Download CSV button
        download_csv_btn.click(
            fn=save_unified_csv,
            inputs=[],
            outputs=[download_csv_btn],
            queue=False
        )
        
        # Download plot button
        download_plot_btn.click(
            fn=save_plot_html,
            inputs=[plot_output],
            outputs=[download_plot_btn],
            queue=False
        )
        
        gr.Markdown("""
        ---
        ### 📖 Instructions
        1. Configure the GluRPC server URL and API key (if required)
        2. The server health monitor updates automatically every second
        3. Upload a CGM data file (Dexcom, LibreView, etc.)
        4. The file will be automatically processed and the latest prediction shown
        5. Use the slider to view predictions for different samples
        6. Click "Download Unified CSV" to save the converted data in unified format
        7. Click "Download Plot (HTML)" to save the current prediction plot as an interactive HTML file
        
        ### ℹ️ About
        This is a client application for GluRPC, a glucose prediction service.
        All inference and processing happens on the server side.
        
        ### 🎯 New Features
        - **Automatic request cancellation**: When you move the slider, previous incomplete plot requests are cancelled on the server
        - **Real-time health monitoring**: Server metrics update every second with historical graphs
        - **Improved error handling**: Better handling of server errors and disconnections
        """)
    
    return app


def launch_app(
    share: bool = False,
    server_name: str = "127.0.0.1",
    server_port: int = 7860,
    default_server_url: str = "http://localhost:8000"
):
    """Launch the Gradio application.
    
    Args:
        share: Whether to create a public share link
        server_name: Server hostname
        server_port: Server port
        default_server_url: Default GluRPC server URL to use
    """
    logger.info(f"Launching Gradio app with default_server_url={default_server_url}")
    logger.info(f"Server name: {server_name}")
    logger.info(f"Server port: {server_port}")
    logger.info(f"Share: {share}")
    
    app = create_gradio_app(default_server_url=default_server_url)
    app.launch(
        share=share,
        server_name=server_name,
        server_port=server_port
    )


if __name__ == "__main__":
    launch_app(share=False)
