"""
Instance Protection Module
Prevents multiple instances and detects containerized/virtualized environments
"""

import os
import sys
import socket
import tempfile
import atexit
import time
import threading
import subprocess
import re
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import hashlib
import uuid


class InstanceProtection:
    """
    Protects against multiple instances and detects containerized environments
    """
    
    def __init__(self, lock_port: int = 5000, app_name: str = 'chloros-backend'):
        self.lock_port = lock_port
        self.app_name = app_name
        self.lock_file = None
        self.lock_handle = None
        
        try:
            self.instance_id = self._generate_instance_id()
        except Exception as e:
            raise
        
        try:
            self.is_containerized = self._detect_containerized()
        except Exception as e:
            self.is_containerized = False
        
        try:
            self.is_virtual_machine = self._detect_virtual_machine()
        except Exception as e:
            self.is_virtual_machine = False
        
        # SECURITY: Check if cloud mode is enabled (allows multiple instances)
        self.cloud_mode = self._check_cloud_mode()
        self.allow_multiple_instances = self.cloud_mode
        
        if self.cloud_mode:
            pass
            # print(f"[INSTANCE-PROTECTION] Γÿü∩╕Å Cloud mode ENABLED - multiple instances allowed")
        else:
            # Instance ID generated silently (privacy)
            pass
    
    def _check_cloud_mode(self) -> bool:
        """
        Check if cloud mode is enabled (allows multiple instances)
        
        Cloud mode can be enabled via:
        1. Environment variable: CHLOROS_CLOUD_MODE=1
        2. Environment variable: CHLOROS_ALLOW_MULTIPLE_INSTANCES=1
        3. Server-side subscription level (checked later during login)
        
        Returns: True if cloud mode enabled, False otherwise
        """
        # Check environment variables
        cloud_mode_env = os.environ.get('CHLOROS_CLOUD_MODE', '').lower() in ('1', 'true', 'yes')
        allow_multiple_env = os.environ.get('CHLOROS_ALLOW_MULTIPLE_INSTANCES', '').lower() in ('1', 'true', 'yes')
        
        if cloud_mode_env or allow_multiple_env:
            # print("[INSTANCE-PROTECTION] Γÿü∩╕Å Cloud mode enabled via environment variable")
            return True
        
        return False
    
    def _generate_instance_id(self) -> str:
        """Generate unique instance ID for this process"""
        pid = os.getpid()
        timestamp = time.time()
        random = uuid.uuid4().hex
        combined = f"{pid}:{timestamp}:{random}"
        return hashlib.sha256(combined.encode()).hexdigest()[:32]
    
    def _detect_containerized(self) -> bool:
        """
        Detect if running in container (Docker, Kubernetes, etc.)
        
        Returns: True if containerized, False otherwise
        """
        # Check for Docker
        if Path('/.dockerenv').exists():
            # print("[INSTANCE-PROTECTION] ≡ƒÉ│ Docker container detected (.dockerenv)")
            return True
        
        # Check cgroup for container indicators
        try:
            cgroup_path = Path('/proc/self/cgroup')
            if cgroup_path.exists():
                with open(cgroup_path, 'r') as f:
                    cgroup_content = f.read()
                    if 'docker' in cgroup_content.lower() or \
                       'kubepods' in cgroup_content.lower() or \
                       'containerd' in cgroup_content.lower():
                        # print(f"[INSTANCE-PROTECTION] ≡ƒÉ│ Container detected in cgroup")
                        return True
        except Exception:
            pass
        
        # Check for container environment variables
        container_vars = ['KUBERNETES_SERVICE_HOST', 'CONTAINER_ID', 'HOSTNAME']
        for var in container_vars:
            if os.environ.get(var):
                # print(f"[INSTANCE-PROTECTION] ≡ƒÉ│ Container environment variable detected: {var}")
                return True
        
        # Check if PID 1 is not typical init (container indicator)
        try:
            if sys.platform != 'win32':
                init_cmd = Path('/proc/1/cmdline')
                if init_cmd.exists():
                    with open(init_cmd, 'rb') as f:
                        cmdline = f.read().decode('utf-8', errors='ignore')
                        # Typical container init processes
                        if any(x in cmdline.lower() for x in ['docker', 'containerd', 'runc', 'pause']):
                            # print(f"[INSTANCE-PROTECTION] ≡ƒÉ│ Container init detected: {cmdline[:50]}")
                            return True
        except Exception:
            pass
        
        return False
    
    def _detect_virtual_machine(self) -> bool:
        """
        Detect if running in virtual machine
        
        Returns: True if VM, False otherwise
        """
        vm_indicators = [
            'vmware', 'virtualbox', 'qemu', 'kvm', 'xen',
            'hyper-v', 'parallels', 'vbox', 'virtual', 'bochs'
        ]
        
        # Check system info (Windows)
        if sys.platform == 'win32':
            try:
                # CRITICAL FIX: Use shorter timeout (2s) to avoid hanging on slow systems
                output = subprocess.check_output(
                    'systeminfo',
                    shell=True,
                    stderr=subprocess.DEVNULL,
                    timeout=2  # REDUCED from 5 to 2 seconds
                ).decode('utf-8', errors='ignore').lower()
                
                for indicator in vm_indicators:
                    if indicator in output:
                        # print(f"[INSTANCE-PROTECTION] ≡ƒÆ╗ VM detected in systeminfo: {indicator}")
                        return True
            except subprocess.TimeoutExpired:
                # Timeout - assume not VM to avoid blocking startup
                print(f"[INSTANCE-PROTECTION] ⚠️ VM detection timed out - assuming no VM")
                pass
            except Exception:
                pass
            
            # Check WMI for VM indicators - DISABLED due to unavoidable console errors on some systems
            # WMI detection skipped (systeminfo check above is sufficient for VM detection)
            pass
        
        # Check /sys/class/dmi/id (Linux)
        if sys.platform != 'win32':
            dmi_paths = [
                '/sys/class/dmi/id/product_name',
                '/sys/class/dmi/id/sys_vendor',
                '/sys/class/dmi/id/board_vendor'
            ]
            
            for dmi_path in dmi_paths:
                try:
                    if Path(dmi_path).exists():
                        with open(dmi_path, 'r') as f:
                            content = f.read().lower()
                            for indicator in vm_indicators:
                                if indicator in content:
                                    # print(f"[INSTANCE-PROTECTION] ≡ƒÆ╗ VM detected in DMI: {indicator}")
                                    return True
                except Exception:
                    pass
        
        # Check for VM-specific processes
        try:
            if sys.platform == 'win32':
                # CRITICAL FIX: Use shorter timeout (2s) to avoid hanging
                output = subprocess.check_output(
                    'tasklist',
                    shell=True,
                    stderr=subprocess.DEVNULL,
                    timeout=2  # REDUCED from 5 to 2 seconds
                ).decode('utf-8', errors='ignore').lower()
            else:
                output = subprocess.check_output(
                    'ps aux',
                    shell=True,
                    stderr=subprocess.DEVNULL,
                    timeout=2  # REDUCED from 5 to 2 seconds
                ).decode('utf-8', errors='ignore').lower()
            
            vm_processes = ['vmware', 'vbox', 'qemu', 'xen', 'kvm']
            for proc in vm_processes:
                if proc in output:
                    # print(f"[INSTANCE-PROTECTION] ≡ƒÆ╗ VM process detected: {proc}")
                    return True
        except subprocess.TimeoutExpired:
            # Timeout - assume no VM processes to avoid blocking startup
            print(f"[INSTANCE-PROTECTION] ⚠️ VM process detection timed out - assuming no VM")
            pass
        except Exception:
            pass
        
        return False
    
    def acquire_instance_lock(self) -> Tuple[bool, Optional[str]]:
        """
        Acquire exclusive lock to prevent multiple instances
        
        Returns: (success, error_message)
        """
        # SECURITY: Skip locking in cloud mode (allows multiple instances)
        if self.cloud_mode:
            # print("[INSTANCE-PROTECTION] Γÿü∩╕Å Cloud mode: Skipping instance lock (multiple instances allowed)")
            return True, None
        
        # Method 1: Port-based locking (most reliable)
        if not self._check_port_available():
            return False, f"Port {self.lock_port} is already in use - another instance may be running"
        
        # Method 2: File-based locking
        lock_file_path = self._get_lock_file_path()
        
        try:
            # Try to create and lock the file
            if sys.platform == 'win32':
                # Windows: Use msvcrt for file locking
                try:
                    import msvcrt
                    self.lock_file = open(lock_file_path, 'w')
                    try:
                        msvcrt.locking(self.lock_file.fileno(), msvcrt.LK_NBLCK, 1)
                        self.lock_handle = self.lock_file
                    except IOError:
                        self.lock_file.close()
                        return False, "Another instance is running (file lock failed)"
                except ImportError:
                    # Fallback: Just check if file exists and is recent
                    if lock_file_path.exists():
                        # Check if process is still alive
                        try:
                            with open(lock_file_path, 'r') as f:
                                pid = int(f.read().strip())
                            # Check if process exists
                            if sys.platform == 'win32':
                                # CRITICAL FIX: Use very short timeout (1s) to avoid hanging
                                result = subprocess.run(
                                    ['tasklist', '/FI', f'PID eq {pid}'],
                                    capture_output=True,
                                    timeout=1  # REDUCED from 2 to 1 second
                                )
                                if 'INFO: No tasks' not in result.stdout.decode('utf-8', errors='ignore'):
                                    return False, f"Another instance is running (PID {pid})"
                        except Exception:
                            pass
                    
                    # Create lock file
                    self.lock_file = open(lock_file_path, 'w')
                    self.lock_file.write(str(os.getpid()))
                    self.lock_file.flush()
                    self.lock_handle = self.lock_file
            else:
                # Unix/Linux: Use fcntl for file locking
                import fcntl
                self.lock_file = open(lock_file_path, 'w')
                try:
                    fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    self.lock_file.write(str(os.getpid()))
                    self.lock_file.flush()
                    self.lock_handle = self.lock_file
                except IOError:
                    self.lock_file.close()
                    return False, "Another instance is running (file lock failed)"
            
            # Register cleanup on exit
            atexit.register(self.release_instance_lock)
            
            # print(f"[INSTANCE-PROTECTION] Γ£à Instance lock acquired (PID: {os.getpid()})")
            return True, None
            
        except Exception as e:
            return False, f"Failed to acquire instance lock: {str(e)}"
    
    def _check_port_available(self) -> bool:
        """Check if lock port is available"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', self.lock_port))
            sock.close()
            return result != 0  # Port is available if connection fails
        except Exception:
            return True  # Assume available if check fails
    
    def _get_lock_file_path(self) -> Path:
        """Get path to lock file"""
        if sys.platform == 'win32':
            lock_dir = Path(os.environ.get('TEMP', tempfile.gettempdir()))
        else:
            lock_dir = Path('/tmp')
        
        return lock_dir / f'{self.app_name}.lock'
    
    def release_instance_lock(self):
        """Release instance lock"""
        try:
            if self.lock_file:
                self.lock_file.close()
            
            lock_file_path = self._get_lock_file_path()
            if lock_file_path.exists():
                lock_file_path.unlink(missing_ok=True)
            
            # print("[INSTANCE-PROTECTION] ≡ƒöô Instance lock released")
        except Exception as e:
            print(f"[INSTANCE-PROTECTION] ΓÜá∩╕Å Error releasing lock: {e}")
    
    def detect_concurrent_instances(self) -> Tuple[bool, int, list]:
        """
        Detect if multiple Chloros BACKEND processes are running
        
        Returns: (has_concurrent, count, pids)
        
        Note: We only count separate backend_server.py processes, NOT Electron helper processes
        from the same GUI instance, as Electron naturally spawns multiple child processes.
        """
        # SECURITY: In cloud mode, still detect but don't treat as violation
        # This allows monitoring without blocking
        
        try:
            import psutil
        except ImportError:
            # Fallback method without psutil
            return self._detect_concurrent_fallback()
        
        current_pid = os.getpid()
        backend_processes = []
        
        # Get current process info to find parent if we're in Electron
        try:
            current_proc = psutil.Process(current_pid)
            current_parent = current_proc.parent()
            current_parent_pid = current_parent.pid if current_parent else None
        except Exception:
            current_parent_pid = None
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'exe', 'ppid']):
            try:
                proc_info = proc.info
                pid = proc_info['pid']
                
                # Skip current process
                if pid == current_pid:
                    continue
                
                # Skip parent process (if running under Electron)
                if current_parent_pid and pid == current_parent_pid:
                    continue
                
                name = (proc_info.get('name') or '').lower()
                cmdline_list = proc_info.get('cmdline') or []
                cmdline = ' '.join(cmdline_list).lower() if cmdline_list else ''
                exe = (proc_info.get('exe') or '').lower()
                
                # Only detect actual backend_server.py processes or standalone Python processes
                # running Chloros backend - NOT Electron helper processes
                is_backend = (
                    'backend_server' in cmdline or
                    ('python' in name and 'chloros' in cmdline and 'backend' in cmdline) or
                    ('chloros.exe' in name and 'type=' not in cmdline)  # Main Chloros.exe only, not helpers
                )
                
                # Additional check: If it's an Electron process, make sure it's a main process
                # not a helper/renderer/gpu process (which have --type= in cmdline)
                if 'electron' in name or 'chloros.exe' in name:
                    # Skip Electron helper processes (renderer, gpu, utility, etc.)
                    if '--type=' in cmdline or 'type=' in cmdline:
                        continue
                    # Skip if it's a child of current parent (same Electron instance)
                    if current_parent_pid:
                        try:
                            proc_obj = psutil.Process(pid)
                            proc_parent = proc_obj.parent()
                            if proc_parent and proc_parent.pid == current_parent_pid:
                                continue
                        except Exception:
                            pass
                
                if is_backend:
                    backend_processes.append(pid)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        has_concurrent = len(backend_processes) > 0
        
        if has_concurrent and self.cloud_mode:
            pass
            # print(f"[INSTANCE-PROTECTION] Γÿü∩╕Å Cloud mode: {len(backend_processes)} concurrent backend instances detected (allowed)")
        
        return has_concurrent, len(backend_processes), backend_processes
    
    def _detect_concurrent_fallback(self) -> Tuple[bool, int, list]:
        """Fallback concurrent detection without psutil"""
        if sys.platform == 'win32':
            try:
                # CRITICAL FIX: Use very short timeout (1s) to avoid hanging
                output = subprocess.check_output(
                    'tasklist /FI "IMAGENAME eq Chloros.exe" /FO CSV /NH',
                    shell=True,
                    stderr=subprocess.DEVNULL,
                    timeout=1  # REDUCED from 2 to 1 second
                ).decode('utf-8', errors='ignore')
                
                pids = []
                for line in output.split('\n'):
                    match = re.search(r'"Chloros.exe","(\d+)"', line)
                    if match:
                        pid = int(match.group(1))
                        if pid != os.getpid():
                            pids.append(pid)
                
                return len(pids) > 0, len(pids), pids
            except subprocess.TimeoutExpired:
                # Timeout - return no concurrent instances to avoid blocking startup
                print(f"[INSTANCE-PROTECTION] ⚠️ Concurrent detection timed out (Windows)")
                return False, 0, []
            except Exception:
                pass
        else:
            try:
                # CRITICAL FIX: Use very short timeout (1s) to avoid hanging
                output = subprocess.check_output(
                    ['ps', 'aux'],
                    stderr=subprocess.DEVNULL,
                    timeout=1  # REDUCED from 2 to 1 second
                ).decode('utf-8', errors='ignore')
                
                pids = []
                for line in output.split('\n'):
                    if 'chloros' in line.lower() or 'backend_server' in line.lower():
                        parts = line.split()
                        if len(parts) > 1:
                            try:
                                pid = int(parts[1])
                                if pid != os.getpid():
                                    pids.append(pid)
                            except ValueError:
                                pass
                
                return len(pids) > 0, len(pids), pids
            except subprocess.TimeoutExpired:
                # Timeout - return no concurrent instances to avoid blocking startup
                print(f"[INSTANCE-PROTECTION] ⚠️ Concurrent detection timed out (Unix)")
                return False, 0, []
            except Exception:
                pass
        
        return False, 0, []
    
    def get_environment_info(self) -> Dict[str, Any]:
        """Get information about the execution environment"""
        return {
            'instance_id': self.instance_id,
            'pid': os.getpid(),
            'is_containerized': self.is_containerized,
            'is_virtual_machine': self.is_virtual_machine,
            'cloud_mode': self.cloud_mode,
            'allow_multiple_instances': self.allow_multiple_instances,
            'platform': sys.platform,
            'hostname': socket.gethostname(),
            'container_id': os.environ.get('HOSTNAME') if self.is_containerized else None
        }
    
    def set_cloud_mode(self, enabled: bool, reason: str = ""):
        """
        Enable/disable cloud mode programmatically
        
        This can be called after checking subscription level from server
        
        Args:
            enabled: True to enable cloud mode (allow multiple instances)
            reason: Reason for enabling (e.g., "enterprise subscription", "cloud deployment")
        """
        self.cloud_mode = enabled
        self.allow_multiple_instances = enabled
        
        if enabled:
            print(f"[INSTANCE-PROTECTION] Γÿü∩╕Å Cloud mode ENABLED: {reason}")
        else:
            print(f"[INSTANCE-PROTECTION] ≡ƒöÉ Cloud mode DISABLED: {reason}")


# Global instance
_instance_protection: Optional[InstanceProtection] = None


def get_instance_protection(lock_port: int = 5000, app_name: str = 'chloros-backend') -> InstanceProtection:
    """Get or create global instance protection"""
    global _instance_protection
    if _instance_protection is None:
        try:
            _instance_protection = InstanceProtection(lock_port=lock_port, app_name=app_name)
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise
    return _instance_protection

