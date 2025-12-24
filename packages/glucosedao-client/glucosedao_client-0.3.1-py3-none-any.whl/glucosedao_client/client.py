"""GluRPC Client Library for communicating with the glucose prediction server."""
import base64
import io
import logging
import time
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, Union
from dataclasses import dataclass

import httpx

# Configure logger
logger = logging.getLogger("glurpc.client")
logger.setLevel(logging.DEBUG)
#from glurpc import schemas

@dataclass
class GluRPCConfig:
    """Configuration for GluRPC client."""
    base_url: str = "http://localhost:8000"
    api_key: Optional[str] = None
    timeout: float = 120.0


@dataclass
class ConvertResponse:
    """Response from convert_to_unified endpoint."""
    csv_content: Optional[str] = None
    error: Optional[str] = None


@dataclass  
class ProcessResponse:
    """Response from process_unified endpoint."""
    handle: Optional[str] = None
    total_samples: Optional[int] = None
    warnings: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@dataclass
class QuickPlotResponse:
    """Response from quick_plot endpoint."""
    plot_data: Optional[Dict[str, Any]] = None
    warnings: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@dataclass
class HealthResponse:
    """Response from health endpoint."""
    status: str
    load_status: str
    cache_size: int
    models_initialized: bool
    available_priority_models: int
    available_general_models: int
    avg_fulfillment_time_ms: float
    vmem_usage_mb: float
    device: str
    total_http_requests: int
    total_http_errors: int
    avg_request_time_ms: float
    median_request_time_ms: float
    min_request_time_ms: float
    max_request_time_ms: float
    inference_requests_by_priority: Dict[str, int]
    total_inference_errors: int
    total_calc_runs: int
    total_calc_errors: int
    inference_queue_size: int
    inference_queue_capacity: int
    calc_queue_size: int
    calc_queue_capacity: int


class GluRPCClient:
    """Client for interacting with GluRPC server."""
    
    def __init__(self, config: Optional[GluRPCConfig] = None):
        """Initialize client with configuration.
        
        Args:
            config: GluRPC configuration. If None, uses defaults.
        """
        self.config = config or GluRPCConfig()
        self.client = httpx.Client(timeout=self.config.timeout)
        self._current_plot_request: Optional[httpx.Request] = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers including API key if configured."""
        headers = {}
        if self.config.api_key:
            headers["X-API-Key"] = self.config.api_key
        return headers
    
    def convert_to_unified(self, file_path: Union[str, Path]) -> ConvertResponse:
        """Convert a raw CGM file to unified format.
        
        Args:
            file_path: Path to the raw CGM file
            
        Returns:
            ConvertResponse with csv_content or error
        """
        file_path = Path(file_path)
        logger.info(f"Converting file to unified: file={file_path.name}")
        start_time = time.time()
        
        try:
            with open(file_path, "rb") as f:
                files = {"file": (file_path.name, f, "text/csv")}
                
                response = self.client.post(
                    f"{self.config.base_url}/convert_to_unified",
                    files=files
                )
            
            response.raise_for_status()
            data = response.json()
            
            duration = time.time() - start_time
            csv_length = len(data.get("csv_content", "")) if data.get("csv_content") else 0
            logger.info(f"Convert completed: duration={duration:.3f}s, csv_length={csv_length}")
            
            return ConvertResponse(
                csv_content=data.get("csv_content"),
                error=data.get("error")
            )
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Convert failed after {duration:.3f}s: {e}")
            raise
    
    def process_unified(
        self, 
        csv_content: str, 
        force_calculate: bool = False
    ) -> ProcessResponse:
        """Process unified CSV and cache for plotting.
        
        Args:
            csv_content: CSV content in unified format
            force_calculate: Force recalculation even if cached
            
        Returns:
            ProcessResponse with handle and metadata
        """
        logger.info(f"Processing unified CSV: force={force_calculate}, size={len(csv_content)} bytes")
        start_time = time.time()
        
        try:
            csv_base64 = base64.b64encode(csv_content.encode()).decode()
            
            response = self.client.post(
                f"{self.config.base_url}/process_unified",
                json={
                    "csv_base64": csv_base64,
                    "force_calculate": force_calculate
                },
                headers=self._get_headers()
            )
            
            response.raise_for_status()
            data = response.json()
            
            duration = time.time() - start_time
            logger.info(f"Process completed: duration={duration:.3f}s, handle={data.get('handle', 'N/A')[:8]}, total_samples={data.get('total_samples')}")
            
            return ProcessResponse(
                handle=data.get("handle"),
                total_samples=data.get("total_samples"),
                warnings=data.get("warnings"),
                error=data.get("error")
            )
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Process failed after {duration:.3f}s: {e}")
            raise
    
    def draw_plot(self, handle: str, index: int, force_calculate: bool = False) -> Dict[str, Any]:
        """Generate a plot for a specific sample.
        
        Args:
            handle: Cache handle from process_unified
            index: Sample index to plot
            force_calculate: Force recalculation even if cached
            
        Returns:
            Plotly figure as JSON dict
        """
        logger.debug(f"Requesting plot: handle={handle[:8]}, index={index}, force={force_calculate}")
        start_time = time.time()
        
        try:
            response = self.client.post(
                f"{self.config.base_url}/draw_a_plot",
                json={
                    "handle": handle, 
                    "index": index,
                    "force_calculate": force_calculate
                },
                headers=self._get_headers()
            )
            
            response.raise_for_status()
            duration = time.time() - start_time
            plot_data = response.json()
            logger.info(f"Plot received: index={index}, duration={duration:.3f}s")
            
            return plot_data
        except httpx.HTTPStatusError as e:
            duration = time.time() - start_time
            if e.response.status_code == 499:
                logger.info(f"Plot request cancelled by server: index={index}, duration={duration:.3f}s")
                raise RuntimeError("Request cancelled")
            logger.error(f"Plot request failed after {duration:.3f}s: index={index}, status={e.response.status_code}, error={e}")
            raise
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Plot request failed after {duration:.3f}s: index={index}, error={e}")
            raise
    
    def quick_plot(
        self, 
        csv_content: str, 
        force_calculate: bool = False
    ) -> QuickPlotResponse:
        """Process CSV and immediately get plot for last sample.
        
        Args:
            csv_content: CSV content in unified format
            force_calculate: Force recalculation even if cached
            
        Returns:
            QuickPlotResponse with plot and metadata
        """
        logger.info(f"Quick plot: force={force_calculate}")
        start_time = time.time()
        
        try:
            csv_base64 = base64.b64encode(csv_content.encode()).decode()
            
            response = self.client.post(
                f"{self.config.base_url}/quick_plot",
                json={
                    "csv_base64": csv_base64,
                    "force_calculate": force_calculate
                },
                headers=self._get_headers()
            )
            
            response.raise_for_status()
            data = response.json()
            
            duration = time.time() - start_time
            logger.info(f"Quick plot completed: duration={duration:.3f}s")
            
            return QuickPlotResponse(
                plot_data=data.get("plot_data"),
                warnings=data.get("warnings"),
                error=data.get("error")
            )
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Quick plot failed after {duration:.3f}s: {e}")
            raise
    
    def health(self) -> HealthResponse:
        """Check server health and status.
        
        Returns:
            HealthResponse with server metrics
        """
        logger.debug("Checking server health")
        
        try:
            response = self.client.get(
                f"{self.config.base_url}/health"
            )
            
            response.raise_for_status()
            data = response.json()
            
            logger.debug(f"Server health: status={data.get('status')}")
            
            return HealthResponse(**data)
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            raise
    
    def cache_management(
        self, 
        action: str, 
        handle: Optional[str] = None
    ) -> Dict[str, Any]:
        """Manage cache operations.
        
        Args:
            action: Action to perform (flush, info, delete, save, load)
            handle: Handle for delete/load/save operations
            
        Returns:
            Dictionary with operation results
        """
        logger.info(f"Cache management: action={action}, handle={handle[:8] if handle else 'N/A'}")
        
        try:
            params = {"action": action}
            if handle:
                params["handle"] = handle
            
            response = self.client.post(
                f"{self.config.base_url}/cache_management",
                params=params,
                headers=self._get_headers()
            )
            
            response.raise_for_status()
            result = response.json()
            logger.info(f"Cache management completed: action={action}")
            return result
        except Exception as e:
            logger.error(f"Cache management failed: action={action}, error={e}")
            raise
    
    def close(self):
        """Close the HTTP client."""
        self.client.close()


class AsyncGluRPCClient:
    """Async client for interacting with GluRPC server."""
    
    def __init__(self, config: Optional[GluRPCConfig] = None):
        """Initialize async client with configuration.
        
        Args:
            config: GluRPC configuration. If None, uses defaults.
        """
        self.config = config or GluRPCConfig()
        self.client = httpx.AsyncClient(timeout=self.config.timeout)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers including API key if configured."""
        headers = {}
        if self.config.api_key:
            headers["X-API-Key"] = self.config.api_key
        return headers
    
    async def convert_to_unified(self, file_path: Union[str, Path]) -> ConvertResponse:
        """Convert a raw CGM file to unified format.
        
        Args:
            file_path: Path to the raw CGM file
            
        Returns:
            ConvertResponse with csv_content or error
        """
        file_path = Path(file_path)
        
        with open(file_path, "rb") as f:
            files = {"file": (file_path.name, f, "text/csv")}
            
            response = await self.client.post(
                f"{self.config.base_url}/convert_to_unified",
                files=files
            )
        
        response.raise_for_status()
        data = response.json()
        
        return ConvertResponse(
            csv_content=data.get("csv_content"),
            error=data.get("error")
        )
    
    async def process_unified(
        self, 
        csv_content: str, 
        force_calculate: bool = False
    ) -> ProcessResponse:
        """Process unified CSV and cache for plotting.
        
        Args:
            csv_content: CSV content in unified format
            force_calculate: Force recalculation even if cached
            
        Returns:
            ProcessResponse with handle and metadata
        """
        csv_base64 = base64.b64encode(csv_content.encode()).decode()
        
        response = await self.client.post(
            f"{self.config.base_url}/process_unified",
            json={
                "csv_base64": csv_base64,
                "force_calculate": force_calculate
            },
            headers=self._get_headers()
        )
        
        response.raise_for_status()
        data = response.json()
        
        return ProcessResponse(
            handle=data.get("handle"),
            total_samples=data.get("total_samples"),
            warnings=data.get("warnings"),
            error=data.get("error")
        )
    
    async def draw_plot(self, handle: str, index: int, force_calculate: bool = False) -> Dict[str, Any]:
        """Generate a plot for a specific sample.
        
        Args:
            handle: Cache handle from process_unified
            index: Sample index to plot
            force_calculate: Force recalculation even if cached
            
        Returns:
            Plotly figure as JSON dict
        """
        response = await self.client.post(
            f"{self.config.base_url}/draw_a_plot",
            json={
                "handle": handle, 
                "index": index,
                "force_calculate": force_calculate
            },
            headers=self._get_headers()
        )
        
        response.raise_for_status()
        return response.json()
    
    async def quick_plot(
        self, 
        csv_content: str, 
        force_calculate: bool = False
    ) -> QuickPlotResponse:
        """Process CSV and immediately get plot for last sample.
        
        Args:
            csv_content: CSV content in unified format
            force_calculate: Force recalculation even if cached
            
        Returns:
            QuickPlotResponse with plot and metadata
        """
        csv_base64 = base64.b64encode(csv_content.encode()).decode()
        
        response = await self.client.post(
            f"{self.config.base_url}/quick_plot",
            json={
                "csv_base64": csv_base64,
                "force_calculate": force_calculate
            },
            headers=self._get_headers()
        )
        
        response.raise_for_status()
        data = response.json()
        
        return QuickPlotResponse(
            plot_data=data.get("plot_data"),
            warnings=data.get("warnings"),
            error=data.get("error")
        )
    
    async def health(self) -> HealthResponse:
        """Check server health and status.
        
        Returns:
            HealthResponse with server metrics
        """
        response = await self.client.get(
            f"{self.config.base_url}/health"
        )
        
        response.raise_for_status()
        data = response.json()
        
        return HealthResponse(**data)
    
    async def cache_management(
        self, 
        action: str, 
        handle: Optional[str] = None
    ) -> Dict[str, Any]:
        """Manage cache operations.
        
        Args:
            action: Action to perform (flush, info, delete, save, load)
            handle: Handle for delete/load/save operations
            
        Returns:
            Dictionary with operation results
        """
        params = {"action": action}
        if handle:
            params["handle"] = handle
        
        response = await self.client.post(
            f"{self.config.base_url}/cache_management",
            params=params,
            headers=self._get_headers()
        )
        
        response.raise_for_status()
        return response.json()
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

