"""
Chloros Local SDK
=================

Main SDK module for local Chloros image processing.
Provides Python interface to the Chloros backend API running on localhost.

Requirements:
    - Chloros Desktop installed
    - Chloros backend running (auto-starts if enabled)
    - Active Chloros+ license

Copyright (c) 2025 MAPIR Inc. All rights reserved.
"""

import os
import sys
import time
import json
import subprocess
import platform
from pathlib import Path
from typing import Optional, List, Dict, Union, Callable

import requests

from .exceptions import (
    ChlorosBackendError,
    ChlorosConnectionError,
    ChlorosProcessingError,
    ChlorosConfigurationError,
    ChlorosLicenseError
)


class ChlorosLocal:
    """
    Chloros Local SDK - Python interface for Chloros image processing
    
    This class provides programmatic access to the Chloros backend API
    running on localhost. It enables automation, custom workflows, and
    integration with existing Python pipelines.
    
    Requirements:
        - Chloros Desktop installed locally
        - Active Chloros+ license (validated via GUI login)
        - Backend running or auto-start enabled
    
    Basic Usage:
        >>> from chloros_sdk import ChlorosLocal
        >>> 
        >>> # Initialize SDK (auto-starts backend)
        >>> chloros = ChlorosLocal()
        >>> 
        >>> # Create project and import images
        >>> chloros.create_project("MyProject", camera="Survey3N_RGN")
        >>> chloros.import_images("C:/DroneImages/Flight001")
        >>> 
        >>> # Configure processing settings
        >>> chloros.configure(
        ...     vignette_correction=True,
        ...     reflectance_calibration=True,
        ...     indices=["NDVI", "NDRE", "GNDVI"]
        ... )
        >>> 
        >>> # Process images
        >>> results = chloros.process(mode="parallel", wait=True)
    
    Advanced Usage:
        >>> # Custom progress monitoring
        >>> def progress_callback(progress, message):
        ...     print(f"Progress: {progress}% - {message}")
        >>> 
        >>> chloros.process(
        ...     mode="parallel",
        ...     progress_callback=progress_callback,
        ...     wait=True
        ... )
    
    Attributes:
        api_url (str): URL of local Chloros backend (default: http://localhost:5000)
        timeout (int): Request timeout in seconds
        backend_process: Backend process object if auto-started
    """
    
    # Default backend installation paths
    DEFAULT_BACKEND_PATHS = [
        r"C:\Program Files\MAPIR\Chloros\resources\backend\chloros-backend.exe",
        r"C:\Program Files\Chloros\resources\backend\chloros-backend.exe",
        r"C:\Program Files\Chloros\resources\backend\chloros-backend-safe.exe",
        r"C:\Program Files (x86)\MAPIR\Chloros\resources\backend\chloros-backend.exe",
        r"C:\Program Files (x86)\Chloros\resources\backend\chloros-backend.exe",
    ]
    
    def __init__(self,
                 api_url: str = "http://localhost:5000",
                 auto_start_backend: bool = True,
                 backend_exe: Optional[str] = None,
                 timeout: int = 30,
                 backend_startup_timeout: int = 60):
        """
        Initialize Chloros Local SDK
        
        Args:
            api_url: URL of local Chloros backend (default: http://localhost:5000)
            auto_start_backend: Automatically start backend if not running (default: True)
            backend_exe: Path to backend executable (auto-detected if None)
            timeout: Request timeout in seconds (default: 30)
            backend_startup_timeout: Timeout for backend startup in seconds (default: 60)
        
        Raises:
            ChlorosConnectionError: If backend not running and auto_start is False
            ChlorosBackendError: If backend fails to start
            ChlorosLicenseError: If no valid Chloros+ license found
        
        Example:
            >>> # Auto-start backend (default)
            >>> chloros = ChlorosLocal()
            >>> 
            >>> # Connect to existing backend
            >>> chloros = ChlorosLocal(auto_start_backend=False)
            >>> 
            >>> # Use custom backend path
            >>> chloros = ChlorosLocal(backend_exe="C:/Custom/chloros-backend.exe")
        """
        self.api_url = api_url
        self.timeout = timeout
        self.backend_startup_timeout = backend_startup_timeout
        self.backend_process: Optional[subprocess.Popen] = None
        self.backend_exe = backend_exe or self._find_backend_exe()
        
        # Check if backend is running
        if not self._is_backend_running():
            if auto_start_backend:
                self._start_backend()
            else:
                raise ChlorosConnectionError(
                    "Chloros backend not running. "
                    "Start Chloros Desktop or set auto_start_backend=True"
                )
        
        # Verify license (optional check - backend will enforce)
        self._check_license_status()
    
    def _find_backend_exe(self) -> str:
        """
        Auto-detect Chloros backend executable
        
        Returns:
            str: Path to backend executable
        
        Raises:
            ChlorosBackendError: If backend not found
        """
        for path in self.DEFAULT_BACKEND_PATHS:
            if os.path.exists(path):
                return path
        
        raise ChlorosBackendError(
            "Chloros backend not found. Please install Chloros Desktop first.\n"
            "Download from: https://www.mapir.camera/downloads"
        )
    
    def _is_backend_running(self) -> bool:
        """
        Check if Chloros backend is accessible
        
        Returns:
            bool: True if backend is running and responding
        """
        try:
            response = requests.get(
                f"{self.api_url}/",
                timeout=2
            )
            return response.ok
        except (requests.exceptions.RequestException, Exception):
            return False
    
    def _start_backend(self):
        """
        Auto-start Chloros backend
        
        Raises:
            ChlorosBackendError: If backend fails to start
        """
        if not self.backend_exe or not os.path.exists(self.backend_exe):
            raise ChlorosBackendError(
                f"Backend executable not found: {self.backend_exe}"
            )
        
        try:
            # Start backend process (hidden window on Windows)
            if platform.system() == 'Windows':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = 0  # SW_HIDE
                
                self.backend_process = subprocess.Popen(
                    [self.backend_exe],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    startupinfo=startupinfo
                )
            else:
                self.backend_process = subprocess.Popen(
                    [self.backend_exe],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            
            # Wait for backend to be ready
            start_time = time.time()
            while time.time() - start_time < self.backend_startup_timeout:
                if self._is_backend_running():
                    return
                time.sleep(1)
            
            # Timeout - backend failed to start
            if self.backend_process:
                self.backend_process.terminate()
            
            raise ChlorosBackendError(
                f"Backend started but not responding after {self.backend_startup_timeout} seconds"
            )
            
        except Exception as e:
            raise ChlorosBackendError(f"Failed to start backend: {str(e)}")
    
    def _check_license_status(self):
        """
        Check if valid Chloros+ license is cached
        
        Raises:
            ChlorosLicenseError: If no valid license found (warning only)
        """
        try:
            # This is a soft check - backend will enforce license requirements
            # Just warn user if we can't detect a license
            response = requests.get(
                f"{self.api_url}/api/get-config",
                timeout=self.timeout
            )
            
            if not response.ok:
                # Warning only - don't fail initialization
                import warnings
                warnings.warn(
                    "Could not verify Chloros+ license. "
                    "Ensure you've logged in via Chloros Desktop GUI.",
                    UserWarning
                )
        except Exception:
            # Silently continue - license check is optional
            pass
    
    def _request(self,
                 method: str,
                 endpoint: str,
                 json_data: Optional[Dict] = None,
                 timeout: Optional[int] = None) -> requests.Response:
        """
        Make HTTP request to Chloros API
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., '/api/new-project')
            json_data: JSON data for request body
            timeout: Request timeout (uses self.timeout if None)
        
        Returns:
            requests.Response: HTTP response object
        
        Raises:
            ChlorosConnectionError: If connection fails
        """
        timeout = timeout or self.timeout
        url = f"{self.api_url}{endpoint}"
        
        try:
            response = requests.request(
                method=method,
                url=url,
                json=json_data,
                timeout=timeout
            )
            return response
        except requests.exceptions.Timeout:
            raise ChlorosConnectionError(
                f"Request timeout after {timeout} seconds"
            )
        except requests.exceptions.ConnectionError:
            raise ChlorosConnectionError(
                "Could not connect to Chloros backend. "
                "Ensure Chloros Desktop is running."
            )
        except Exception as e:
            raise ChlorosConnectionError(f"Connection error: {str(e)}")
    
    # =========================================================================
    # PUBLIC API METHODS
    # =========================================================================
    
    def create_project(self,
                      project_name: str,
                      camera: Optional[str] = None) -> Dict:
        """
        Create a new Chloros project
        
        Args:
            project_name: Name for the project
            camera: Optional camera template (e.g., "Survey3N_RGN", "Survey3W_OCN")
        
        Returns:
            dict: Project creation response
        
        Raises:
            ChlorosProcessingError: If project creation fails
        
        Example:
            >>> chloros.create_project("DroneField_A", camera="Survey3N_RGN")
        """
        try:
            response = self._request(
                'POST',
                '/api/new-project',
                json_data={
                    'projectName': project_name,
                    'template': camera
                }
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            raise ChlorosProcessingError(
                f"Failed to create project: {e.response.text if hasattr(e, 'response') else str(e)}"
            )
    
    def import_images(self,
                     folder_path: Union[str, Path],
                     recursive: bool = False) -> Dict:
        """
        Import images from a folder
        
        Args:
            folder_path: Path to folder containing RAW/TIF/JPG images
            recursive: Search subfolders for images (default: False)
        
        Returns:
            dict: Import results with file count and file list
        
        Raises:
            ChlorosProcessingError: If import fails
            FileNotFoundError: If folder doesn't exist
        
        Example:
            >>> chloros.import_images("C:/DroneImages/Flight001")
            >>> chloros.import_images("C:/DroneImages", recursive=True)
        """
        folder_path = Path(folder_path)
        
        if not folder_path.exists():
            raise FileNotFoundError(f"Folder not found: {folder_path}")
        
        if not folder_path.is_dir():
            raise ValueError(f"Not a directory: {folder_path}")
        
        try:
            response = self._request(
                'POST',
                '/api/import-from-folder',
                json_data={
                    'folder_path': str(folder_path.absolute()),
                    'recursive': recursive
                },
                timeout=self.timeout * 3  # Import can take longer
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            raise ChlorosProcessingError(
                f"Failed to import images: {e.response.text if hasattr(e, 'response') else str(e)}"
            )
    
    def configure(self,
                 debayer: str = "High Quality (Faster)",
                 vignette_correction: bool = True,
                 reflectance_calibration: bool = True,
                 indices: Optional[List[str]] = None,
                 export_format: str = "TIFF (16-bit)",
                 ppk: bool = False,
                 custom_settings: Optional[Dict] = None) -> Dict:
        """
        Configure processing settings
        
        Args:
            debayer: Debayer method (default: "High Quality (Faster)")
            vignette_correction: Enable vignette correction (default: True)
            reflectance_calibration: Enable reflectance calibration (default: True)
            indices: List of vegetation indices to calculate (e.g., ["NDVI", "NDRE"])
            export_format: Output format:
                - "TIFF (16-bit)" (default, recommended)
                - "TIFF (32-bit, Percent)"
                - "PNG (8-bit)"
                - "JPG (8-bit)"
            ppk: Enable PPK corrections from .daq files (default: False)
            custom_settings: Custom settings dict for advanced configuration
        
        Returns:
            dict: Configuration response
        
        Raises:
            ChlorosConfigurationError: If configuration fails
        
        Example:
            >>> # Basic configuration
            >>> chloros.configure(
            ...     vignette_correction=True,
            ...     reflectance_calibration=True,
            ...     indices=["NDVI", "NDRE", "GNDVI"]
            ... )
            >>> 
            >>> # Advanced configuration
            >>> chloros.configure(
            ...     debayer="High Quality (Faster)",
            ...     export_format="TIFF (32-bit, Percent)",
            ...     ppk=True,
            ...     indices=["NDVI", "NDRE", "GNDVI", "OSAVI", "CIG"]
            ... )
        """
        # Build settings dict
        if custom_settings:
            settings = custom_settings
        else:
            settings = {
                "Project Settings": {
                    "Processing": {
                        "Debayer method": debayer,
                        "Vignette correction": vignette_correction,
                        "Reflectance calibration / white balance": reflectance_calibration,
                        "Apply PPK Corrections": ppk
                    },
                    "Export": {
                        "Calibrated image format": export_format
                    }
                }
            }
            
            if indices:
                settings["Project Settings"]["Index"] = {
                    "Add index": indices
                }
        
        try:
            response = self._request(
                'POST',
                '/api/update-project-config',
                json_data=settings
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            raise ChlorosConfigurationError(
                f"Failed to configure settings: {e.response.text if hasattr(e, 'response') else str(e)}"
            )
    
    def process(self,
               mode: str = "parallel",
               wait: bool = True,
               progress_callback: Optional[Callable[[int, str], None]] = None,
               poll_interval: float = 2.0) -> Dict:
        """
        Start processing the project
        
        Args:
            mode: Processing mode:
                - "parallel": Parallel processing (requires Chloros+, recommended)
                - "serial": Serial processing (one image at a time)
            wait: Wait for processing to complete (default: True)
            progress_callback: Optional callback function(progress: int, message: str)
                               Called periodically with progress updates
            poll_interval: Polling interval in seconds for progress checks (default: 2.0)
        
        Returns:
            dict: Processing results
        
        Raises:
            ChlorosProcessingError: If processing fails
            ChlorosLicenseError: If mode requires Chloros+ and not licensed
        
        Example:
            >>> # Simple processing
            >>> results = chloros.process()
            >>> 
            >>> # With progress monitoring
            >>> def show_progress(progress, message):
            ...     print(f"[{progress}%] {message}")
            >>> 
            >>> chloros.process(
            ...     mode="parallel",
            ...     progress_callback=show_progress,
            ...     wait=True
            ... )
            >>> 
            >>> # Fire-and-forget
            >>> chloros.process(wait=False)
        """
        # Set processing mode
        try:
            mode_response = self._request(
                'POST',
                '/api/set-processing-mode',
                json_data={'mode': mode}
            )
            mode_response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if e.response and e.response.status_code == 403:
                raise ChlorosLicenseError(
                    f"Mode '{mode}' requires Chloros+ license. "
                    "Upgrade at https://cloud.mapir.camera/pricing"
                )
            raise ChlorosProcessingError(f"Failed to set processing mode: {str(e)}")
        
        # Start processing
        try:
            process_response = self._request(
                'POST',
                '/api/process-project',
                timeout=10  # Quick response, actual processing is async
            )
            process_response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise ChlorosProcessingError(
                f"Failed to start processing: {e.response.text if hasattr(e, 'response') else str(e)}"
            )
        
        if not wait:
            return {"status": "started", "async": True}
        
        # Monitor progress
        if progress_callback:
            self._monitor_progress_polling(progress_callback, poll_interval)
        else:
            self._wait_for_completion(poll_interval)
        
        return {"status": "complete", "async": False}
    
    def _monitor_progress_polling(self,
                                  callback: Callable[[int, str], None],
                                  poll_interval: float = 2.0):
        """
        Monitor processing progress via polling
        
        Args:
            callback: Function to call with progress updates
            poll_interval: Polling interval in seconds
        """
        last_progress = -1
        max_wait = 3600  # 1 hour max
        elapsed = 0
        
        while elapsed < max_wait:
            time.sleep(poll_interval)
            elapsed += poll_interval
            
            try:
                # Check config for processing status
                response = self._request('GET', '/api/get-config', timeout=5)
                if response.ok:
                    config = response.json()
                    
                    # Extract progress info (simplified - adjust based on actual API)
                    # This is a placeholder - actual implementation depends on your API
                    processing_complete = config.get('processing_complete', False)
                    
                    if processing_complete:
                        callback(100, "Processing complete")
                        return
                    
                    # Estimate progress based on time (placeholder)
                    estimated_progress = min(int((elapsed / 900) * 100), 95)
                    
                    if estimated_progress != last_progress:
                        callback(estimated_progress, f"Processing... ({elapsed}s elapsed)")
                        last_progress = estimated_progress
            
            except Exception as e:
                # Continue polling even if status check fails
                pass
        
        raise ChlorosProcessingError("Processing timeout")
    
    def _wait_for_completion(self, poll_interval: float = 2.0):
        """
        Simple wait for completion without progress updates
        
        Args:
            poll_interval: Polling interval in seconds
        """
        max_wait = 3600  # 1 hour max
        elapsed = 0
        
        while elapsed < max_wait:
            time.sleep(poll_interval)
            elapsed += poll_interval
            
            try:
                response = self._request('GET', '/api/get-config', timeout=5)
                if response.ok:
                    config = response.json()
                    if config.get('processing_complete', False):
                        return
            except Exception:
                pass
        
        raise ChlorosProcessingError("Processing timeout")
    
    def get_config(self) -> Dict:
        """
        Get current project configuration
        
        Returns:
            dict: Current project configuration
        
        Raises:
            ChlorosConnectionError: If request fails
        
        Example:
            >>> config = chloros.get_config()
            >>> print(config['Project Settings'])
        """
        try:
            response = self._request('GET', '/api/get-config')
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            raise ChlorosConnectionError(
                f"Failed to get config: {e.response.text if hasattr(e, 'response') else str(e)}"
            )
    
    def get_status(self) -> Dict:
        """
        Get backend status
        
        Returns:
            dict: Backend status information
        
        Example:
            >>> status = chloros.get_status()
            >>> print(f"Backend version: {status.get('version')}")
        """
        try:
            response = self._request('GET', '/')
            return {
                'running': response.ok,
                'status_code': response.status_code,
                'url': self.api_url
            }
        except Exception as e:
            return {
                'running': False,
                'error': str(e),
                'url': self.api_url
            }
    
    def logout(self) -> Dict:
        """
        Logout and clear stored credentials
        
        This clears the cached session file (~/.chloros/user_session.json)
        to prevent auto-login on next backend start.
        
        Returns:
            dict: Logout response with success status
        
        Raises:
            ChlorosConnectionError: If logout request fails
        
        Example:
            >>> chloros = ChlorosLocal()
            >>> # ... do some work ...
            >>> chloros.logout()
            >>> print("Logged out - credentials cleared")
        """
        try:
            response = self._request(
                'POST',
                '/api/logout',
                json_data={}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            raise ChlorosConnectionError(
                f"Logout failed: {e.response.text if hasattr(e, 'response') else str(e)}"
            )
    
    def shutdown_backend(self):
        """
        Shutdown the backend (if started by SDK)
        
        Example:
            >>> chloros.shutdown_backend()
        """
        if self.backend_process:
            try:
                self.backend_process.terminate()
                self.backend_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.backend_process.kill()
            finally:
                self.backend_process = None
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup"""
        self.shutdown_backend()
    
    def __del__(self):
        """Destructor - cleanup"""
        if hasattr(self, 'backend_process'):
            self.shutdown_backend()


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def process_folder(folder_path: Union[str, Path],
                  project_name: Optional[str] = None,
                  camera: Optional[str] = None,
                  indices: Optional[List[str]] = None,
                  vignette_correction: bool = True,
                  reflectance_calibration: bool = True,
                  export_format: str = "TIFF (16-bit)",
                  mode: str = "parallel",
                  progress_callback: Optional[Callable[[int, str], None]] = None,
                  **kwargs) -> Dict:
    """
    Convenience function to process a folder in one call
    
    This function creates a project, imports images, configures settings,
    and processes images with minimal code.
    
    Args:
        folder_path: Path to folder containing images
        project_name: Project name (auto-generated from folder name if None)
        camera: Camera template (optional)
        indices: List of indices to calculate (default: ["NDVI"])
        vignette_correction: Enable vignette correction (default: True)
        reflectance_calibration: Enable reflectance calibration (default: True)
        export_format: Output format (default: "TIFF (16-bit)")
        mode: Processing mode (default: "parallel")
        progress_callback: Optional progress callback function
        **kwargs: Additional configuration options
    
    Returns:
        dict: Processing results
    
    Raises:
        ChlorosError: If any step fails
    
    Example:
        >>> from chloros_sdk import process_folder
        >>> 
        >>> # Simple one-liner
        >>> results = process_folder("C:/DroneImages/Flight001")
        >>> 
        >>> # With custom settings
        >>> results = process_folder(
        ...     "C:/DroneImages/Flight001",
        ...     project_name="Field_A_Survey",
        ...     camera="Survey3N_RGN",
        ...     indices=["NDVI", "NDRE", "GNDVI"],
        ...     mode="parallel"
        ... )
        >>> 
        >>> # With progress monitoring
        >>> def show_progress(progress, message):
        ...     print(f"[{progress}%] {message}")
        >>> 
        >>> results = process_folder(
        ...     "C:/DroneImages/Flight001",
        ...     progress_callback=show_progress
        ... )
    """
    folder_path = Path(folder_path)
    
    if not folder_path.exists():
        raise FileNotFoundError(f"Folder not found: {folder_path}")
    
    # Generate project name from folder if not provided
    if project_name is None:
        project_name = folder_path.name
    
    # Default indices if none provided
    if indices is None:
        indices = ["NDVI"]
    
    # Create SDK instance
    with ChlorosLocal() as chloros:
        # Create project
        chloros.create_project(project_name, camera=camera)
        
        # Import images
        chloros.import_images(folder_path)
        
        # Configure settings
        chloros.configure(
            vignette_correction=vignette_correction,
            reflectance_calibration=reflectance_calibration,
            indices=indices,
            export_format=export_format,
            **kwargs
        )
        
        # Process
        results = chloros.process(
            mode=mode,
            wait=True,
            progress_callback=progress_callback
        )
    
    return results






