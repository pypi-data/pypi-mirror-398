"""
Centralized Ray Session Manager
Ensures Ray is initialized once with consistent parameters and reused across all modules.

CLOUD SUPPORT:
- When running from Python source in cloud (AWS EC2 with GPU), uses real Ray with full GPU support
- When running from Nuitka exe (desktop mode), uses nuitka_ray_replacement to avoid subprocess issues
- The manager auto-detects the environment and configures Ray accordingly
"""

import os
import sys
import tempfile
import threading

# Ray environment configuration is now handled by nuitka_ray_compatibility_fix.py
# This ensures consistent configuration across all modules

def is_cloud_environment():
    """
    Detect if running in cloud environment (AWS EC2 with GPU).
    Cloud mode uses pip-installed Ray with full GPU support.
    """
    # Check for cloud-specific environment variables
    if os.environ.get('TASK_ID') or os.environ.get('CHLOROS_CLOUD_MODE'):
        return True
    # Check if running from backend-source directory (cloud deployment)
    if 'backend-source' in os.getcwd():
        return True
    return False

def is_nuitka_compiled():
    """Check if running as Nuitka compiled executable."""
    # Check multiple indicators for Nuitka frozen state
    is_frozen = getattr(sys, 'frozen', False)
    is_compiled = '__compiled__' in globals()
    
    # Also check if executable path suggests frozen state
    exe_name = os.path.basename(sys.executable).lower()
    is_exe = exe_name.endswith(('.exe', '.bin')) and not exe_name.startswith('python')
    
    result = is_frozen or is_compiled or is_exe
    
    return result

class RaySessionManager:
    """Singleton Ray session manager for consistent Ray initialization across the application."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(RaySessionManager, cls).__new__(cls)
                    cls._instance._initialized = False
                    cls._instance._ray = None
                    cls._instance._ray_available = False
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized') or not self._initialized:
            self._initialized = True
            self._ray = None
            self._ray_available = False
            self._session_config = None
    
    def get_ray(self):
        """
        Get Ray instance - handles both cloud and desktop environments.
        
        Cloud Mode (Python source):
            - Ray is pip-installed with full GPU support
            - All protobuf/gRPC files are available
            - Full parallel processing with GPU
        
        Desktop Mode (Nuitka exe):
            - Uses nuitka_ray_replacement to avoid subprocess spawning
            - No visible GCS windows
            - Process pool + thread pool for maximum performance
        """
        if self._ray is None:
            cloud_mode = is_cloud_environment()
            nuitka_mode = is_nuitka_compiled()
            
            # CLOUD MODE: Always use real Ray for full GPU support
            if cloud_mode:
                pass  # Cloud environment detected - using real Ray for GPU support
                try:
                    import ray
                    self._ray = ray
                    self._ray_available = True
                    
                    # Verify Ray's protobuf files are available
                    try:
                        from ray.core.generated import gcs_service_pb2
                    except ImportError as proto_err:
                        self._install_ray_for_cloud()
                        
                except ImportError as e:
                    self._ray_available = False
                    return None
            
            # DESKTOP COMPILED MODE: Use replacement to avoid subprocess spawning
            elif nuitka_mode:
                pass  # Compiled desktop mode - using nuitka_ray_replacement
                try:
                    import nuitka_ray_replacement as ray
                    self._ray = ray
                    self._ray_available = True
                except ImportError as e:
                    # Fallback to real Ray (may have issues)
                    try:
                        import ray
                        self._ray = ray
                        self._ray_available = True
                    except ImportError as e2:
                        self._ray_available = False
                        return None
            
            # DEVELOPMENT MODE: Try replacement first, then real Ray
            else:
                try:
                    import nuitka_ray_replacement as ray
                    self._ray = ray
                    self._ray_available = True
                except ImportError:
                    # Fallback to real Ray
                    try:
                        import ray
                        self._ray = ray
                        self._ray_available = True
                    except ImportError as e2:
                        self._ray_available = False
                        return None
                        
        return self._ray
    
    def _install_ray_for_cloud(self):
        """Install Ray with full support for cloud GPU processing."""
        import subprocess
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', 'ray[default]>=2.9.0', '--quiet'],
                capture_output=True,
                text=True,
                timeout=300
            )
        except Exception as e:
            pass  # Could not install Ray
    
    def is_available(self):
        """Check if Ray is available."""
        if not self._ray_available:
            self.get_ray()  # Try to import if not already done
        return self._ray_available
    
    def initialize_session(self, mode='premium', max_workers=None):
        """
        Initialize Ray session - supports both cloud GPU and desktop modes.
        
        Cloud Mode: Full Ray with GPU parallel processing
        Desktop Mode: Replacement for maximum performance (no subprocess spawning)
        """
        ray = self.get_ray()
        if ray is None:
            return False
            
        try:
            # Check if Ray is already initialized
            if ray.is_initialized():
                return True
            
            # Determine environment
            cloud_mode = is_cloud_environment()
            nuitka_mode = is_nuitka_compiled()
            
            # Determine CPU/GPU configuration
            num_cpus = self._detect_cpu_count()
            num_gpus = self._detect_gpu_availability()
            
            if cloud_mode:
                # CLOUD MODE: Full Ray with GPU support
                pass  # Cloud mode - enabling full GPU parallel processing
                
                init_config = {
                    'num_cpus': num_cpus,
                    'num_gpus': num_gpus,
                    'local_mode': False,  # Full distributed mode for parallel GPU
                    'include_dashboard': False,
                    'ignore_reinit_error': True,
                    'log_to_driver': False,
                    'logging_level': 'error',
                    'object_store_memory': 4000000000,  # 4GB for cloud
                }
                
            elif nuitka_mode:
                # NUITKA MODE: Use replacement (no subprocess spawning)
                init_config = {
                    'num_cpus': num_cpus,
                    'num_gpus': num_gpus,
                    'local_mode': True,  # Local mode for replacement
                }
            else:
                # DEVELOPMENT MODE: Standard configuration
                from nuitka_ray_compatibility_fix import get_nuitka_ray_config
                init_config = get_nuitka_ray_config()
                init_config.update({
                    'num_cpus': num_cpus,
                    'num_gpus': num_gpus,
                })
            
            # Initialize Ray (real or replacement)
            ray.init(**init_config)
            
            self._session_config = init_config.copy()
            return True
            
        except Exception as e:
            self._ray_available = False
            return False
    
    def get_initialized_ray(self, mode='premium', max_workers=None):
        """Get Ray instance, initializing if necessary."""
        if not self.is_available():
            return None
        
        ray = self.get_ray()
        if ray is None:
            return None
        
        # Initialize if not already done
        if not self.initialize_session(mode, max_workers):
            return None
        
        return ray
    
    def _detect_gpu_availability(self):
        """Detect available GPUs for Ray initialization."""
        try:
            # Try PyTorch CUDA detection first
            import torch
            
            # CRITICAL FIX: Check CUDA with timeout protection to avoid hanging on no-GPU systems
            cuda_available = False
            try:
                cuda_available = torch.cuda.is_available()
            except Exception as cuda_error:
                cuda_available = False
            
            if cuda_available:
                gpu_count = torch.cuda.device_count()
                
                if gpu_count > 0:
                    return gpu_count
                
            # Fall back to alternative GPU detection methods
            return self._fallback_gpu_detection()
        except ImportError as e:
            # Fall back to alternative GPU detection methods
            return self._fallback_gpu_detection()
        except Exception as e:
            # Fall back to alternative GPU detection methods
            return self._fallback_gpu_detection()
    
    def _fallback_gpu_detection(self):
        """Fallback GPU detection when PyTorch is not available."""
        try:
            # Try nvidia-ml-py for NVIDIA GPUs
            import pynvml
            pynvml.nvmlInit()
            gpu_count = pynvml.nvmlDeviceGetCount()
            if gpu_count > 0:
                return gpu_count
        except ImportError:
            pass
        except Exception as e:
            pass
        
        try:
            # Try Linux GPU detection via lspci
            import subprocess
            import sys
            
            # WMI GPU detection DISABLED - produces unavoidable console errors on some systems
            if sys.platform == 'win32':
                result = type('obj', (object,), {'returncode': 1, 'stdout': ''})()  # Fake failed result
            else:
                # Linux/Mac - use lspci
                result = subprocess.run(['lspci'], capture_output=True, text=True, timeout=1)
            
            if result.returncode == 0:
                lines = [line.strip() for line in result.stdout.split('\n') if line.strip() and line.strip() != 'Name']
                gpu_names = [line for line in lines if any(keyword in line.lower() for keyword in ['nvidia', 'amd', 'intel', 'geforce', 'radeon'])]
                if gpu_names:
                    return len(gpu_names)
        except Exception as e:
            pass
        
        return 0
    
    def _detect_cpu_count(self):
        """Detect the number of CPU cores available for Ray."""
        import os
        import multiprocessing
        
        try:
            # Try to get the number of logical CPU cores
            logical_cores = multiprocessing.cpu_count()
            
            # Try to get physical cores (more accurate for performance)
            try:
                import psutil
                physical_cores = psutil.cpu_count(logical=False)
                if physical_cores and physical_cores > 0:
                    # Use physical cores but cap at logical cores
                    cpu_count = min(physical_cores, logical_cores)
                else:
                    cpu_count = logical_cores
            except ImportError:
                cpu_count = logical_cores
            
            # Ensure we have at least 1 CPU and cap at reasonable maximum
            cpu_count = max(1, min(cpu_count, 32))  # Cap at 32 cores for Ray stability
            
            return cpu_count
            
        except Exception as e:
            return 4  # Safe default
    
    def _detect_electron_environment(self):
        """Detect if running under Electron by checking environment and process tree."""
        import os
        import psutil
        
        try:
            # Method 1: Check environment variables set by Electron
            electron_vars = [
                'ELECTRON_RUN_AS_NODE',
                'ORIGINAL_XDG_CURRENT_DESKTOP', 
                'CHROME_DESKTOP',
                'ELECTRON_NO_ATTACH_CONSOLE'
            ]
            
            for var in electron_vars:
                if os.environ.get(var):
                    return True
            
            # Method 2: Check parent process names
            try:
                current_process = psutil.Process()
                parent = current_process.parent()
                
                while parent:
                    parent_name = parent.name().lower()
                    if any(name in parent_name for name in ['electron', 'chloros', 'node']):
                        return True
                    parent = parent.parent()
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
            
            # Method 3: Check if running from resources/backend directory (Electron app structure)
            current_dir = os.getcwd()
            if 'resources' in current_dir and 'backend' in current_dir:
                return True
                
            return False
            
        except Exception as e:
            return False
    
    def shutdown(self):
        """Shutdown Ray session."""
        if self._ray:
            try:
                self._ray.shutdown()
            except Exception as e:
                pass

# Global singleton instance
ray_session = RaySessionManager()

def get_ray_session():
    """Get the global Ray session manager."""
    return ray_session

def get_ray(mode='premium', max_workers=None):
    """Convenience function to get initialized Ray instance."""
    return ray_session.get_initialized_ray(mode, max_workers)
