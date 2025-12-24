#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chloros CLI - Command Line Interface for Chloros Image Processing
Version: 1.0.2
Platform: Windows (Phase 1)

This CLI wrapper provides command-line access to the Chloros image processing backend.
It spawns the backend server and communicates via HTTP REST API.

Usage:
    chloros-cli process "C:\path\to\images" [options]
    chloros-cli --help

Requirements:
    - Chloros backend (backend_server.py or chloros-backend-safe.exe)
    - Python 3.8+ with requests package
    - Chloros+ license for parallel mode
"""

# Version constant
__version__ = "1.0.2"

import argparse
import json
import os
import pathlib
import subprocess
import sys
import time
import signal
from typing import Optional, Dict, Any, List

# Fix UTF-8 encoding for Windows console before any output
if sys.platform == 'win32':
    try:
        import io
        import ctypes
        import ctypes.wintypes as wintypes
        kernel32 = ctypes.windll.kernel32
        # Set console code page to UTF-8
        kernel32.SetConsoleOutputCP(65001)
        kernel32.SetConsoleCP(65001)
        # Reconfigure stdout/stderr for UTF-8
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
        if hasattr(sys.stderr, 'buffer'):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    except Exception:
        pass  # Silently fail if we can't set UTF-8

# Languages that require special font support (CJK, RTL, etc.)
SPECIAL_FONT_LANGUAGES = {'ja', 'ko', 'zh', 'zh-TW', 'hi', 'th', 'ar'}

def console_supports_unicode() -> bool:
    """
    Check if the current console can display international characters.
    Returns True for Windows Terminal, modern terminals, non-Windows, etc.
    Returns False for legacy cmd.exe/conhost.exe.
    """
    # Non-Windows platforms generally support Unicode
    if sys.platform != 'win32':
        return True
    
    # Windows Terminal sets this env var
    if os.environ.get('WT_SESSION'):
        return True
    
    # ConEmu/Cmder
    if os.environ.get('ConEmuPID'):
        return True
    
    # VS Code integrated terminal (VSCODE_PID is set)
    if os.environ.get('VSCODE_PID'):
        return True
    
    # Cursor's terminal (CURSOR_AGENT is set)
    if os.environ.get('CURSOR_AGENT'):
        return True
    
    # TERM_PROGRAM check as fallback
    term_program = os.environ.get('TERM_PROGRAM', '').lower()
    if term_program in ('vscode', 'cursor', 'iterm.app', 'apple_terminal'):
        return True
    
    # Default: assume legacy console that can't display CJK
    return False

def get_display_language_name(lang_code: str) -> str:
    """
    Get the language name to display, using English for languages
    that can't display in legacy consoles.
    """
    from cli_i18n import LANGUAGES
    
    lang_info = LANGUAGES.get(lang_code, LANGUAGES.get('en'))
    
    # If console supports Unicode or language doesn't need special fonts, use native name
    if console_supports_unicode() or lang_code not in SPECIAL_FONT_LANGUAGES:
        return lang_info['nativeName']
    
    # Legacy console + special font language: use English name
    return lang_info['name']

def get_cli_title() -> str:
    """
    Get CLI title, falling back to English for legacy consoles with CJK languages.
    """
    lang_code = i18n.get_language()
    
    # If console supports Unicode or language doesn't need special fonts, use translated
    if console_supports_unicode() or lang_code not in SPECIAL_FONT_LANGUAGES:
        return i18n.t('cli_title')
    
    # Legacy console + special font language: use English
    return 'MAPIR CHLOROS+ Command Line Interface'

def t(key: str, **kwargs) -> str:
    """
    Translate text, falling back to English for legacy consoles with CJK languages.
    This wraps i18n.t() but returns English when the console can't display the language.
    """
    lang_code = i18n.get_language()
    
    # If console supports Unicode or language doesn't need special fonts, use translated
    if console_supports_unicode() or lang_code not in SPECIAL_FONT_LANGUAGES:
        return i18n.t(key, **kwargs)
    
    # Legacy console + special font language: use English
    # Temporarily switch to English to get the translation
    from cli_i18n import TRANSLATIONS
    english_text = TRANSLATIONS.get('en', {}).get(key, key)
    if kwargs:
        try:
            english_text = english_text.format(**kwargs)
        except (KeyError, ValueError):
            pass
    return english_text

try:
    import requests
except ImportError:
    print("ERROR: 'requests' package is required. Install with: pip install requests")
    sys.exit(1)

# Import our beautiful styling module
try:
    from cli_styles import (
        print_header, print_success, print_error, print_warning, print_info,
        print_progress_bar, print_step, Spinner, Box, print_banner, print_divider,
        ANSIColors, Icons
    )
    USE_FANCY_STYLES = True
    
    # Progress bar drawing characters
    PROGRESS_BAR_FILLED = '█'
    PROGRESS_BAR_EMPTY = '░'
    PROGRESS_BAR_PARTIAL = ['▏', '▎', '▍', '▌', '▋', '▊', '▉']
except ImportError:
    # Fallback if cli_styles module not available
    USE_FANCY_STYLES = False
    PROGRESS_BAR_FILLED = '#'
    PROGRESS_BAR_EMPTY = '-'
    PROGRESS_BAR_PARTIAL = []
    
    # Fallback Icons class with ASCII characters
    class Icons:
        SUCCESS = '[OK]'
        ERROR = '[X]'
        WARNING = '[!]'
        INFO = '[i]'
        ARROW = '->'
        BULLET = '*'
    
    # Basic fallback styling
    class ANSIColors:
        RESET = '\033[0m'
        BOLD = '\033[1m'
        RED = '\033[91m'
        GREEN = '\033[92m'
        YELLOW = '\033[93m'
        BLUE = '\033[94m'
        CYAN = '\033[96m'
        
        @staticmethod
        def supports_color():
            return hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()

# Import i18n for multi-language support
try:
    from cli_i18n import get_i18n, LANGUAGES
    i18n = get_i18n()
    USE_I18N = True
except ImportError:
    USE_I18N = False
    # Fallback translation function
    class DummyI18n:
        def t(self, key, **kwargs):
            return key
        def get_language(self):
            return 'en'
        def set_language(self, code):
            return False
        def get_language_name(self, code=None):
            return 'English'
        def list_languages(self):
            return []
    i18n = DummyI18n()
    LANGUAGES = {}


class ChlorosCLI:
    """Main CLI class for Chloros image processing"""
    
    def __init__(self, backend_exe: Optional[str] = None, port: int = 5000, verbose: bool = False):
        """
        Initialize Chloros CLI
        
        Args:
            backend_exe: Path to backend executable (auto-detected if None)
            port: Port for backend API (default: 5000)
            verbose: Enable verbose output
        """
        self.port = port
        self.api_url = f'http://localhost:{port}'
        self.backend_process: Optional[subprocess.Popen] = None
        self.verbose = verbose
        self.suppress_verbose_output = False  # Can be set later for clean output
        self.use_colors = ANSIColors.supports_color()
        
        # Auto-detect backend executable
        if backend_exe is None:
            backend_exe = self._find_backend_exe()
        
        if backend_exe and not os.path.exists(backend_exe):
            self._print_error(f"Backend executable not found: {backend_exe}")
            sys.exit(1)
        
        self.backend_exe = backend_exe
        
        # Setup signal handlers for clean shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _find_backend_exe(self) -> Optional[str]:
        """Auto-detect backend executable location"""
        # Get the directory where the CLI executable/script is located
        cli_dir = os.path.dirname(os.path.abspath(__file__))
        
        possible_paths = [
            # Installed version: CLI is in resources/cli, backend is in resources/backend
            os.path.join(cli_dir, '..', 'backend', 'chloros-backend-safe.exe'),
            os.path.join(cli_dir, '..', 'backend', 'chloros-backend.exe'),
            # In same directory as CLI (development)
            os.path.join(cli_dir, 'chloros-backend-safe.exe'),
            os.path.join(cli_dir, 'backend_server.py'),
            # In current working directory
            'chloros-backend-safe.exe',
            'backend_server.py',
            # In common installation directories
            r'C:\Program Files\MAPIR\Chloros\resources\backend\chloros-backend-safe.exe',
            r'C:\Program Files\MAPIR\Chloros\resources\backend\chloros-backend.exe',
            r'C:\Program Files\Chloros\resources\backend\chloros-backend-safe.exe',
            r'C:\Program Files\Chloros\resources\backend\chloros-backend.exe',
            r'C:\Program Files (x86)\Chloros\resources\backend\chloros-backend-safe.exe',
        ]
        
        for path in possible_paths:
            # Normalize the path (resolve ..)
            normalized_path = os.path.normpath(path)
            if os.path.exists(normalized_path):
                # Suppress verbose message - will be set later
                # self._print_verbose(i18n.t('found_backend', path=normalized_path))
                return normalized_path
        
        self._print_warning(i18n.t('could_not_detect_backend'))
        return None
    
    def _signal_handler(self, signum, frame):
        """Handle Ctrl+C and termination signals"""
        self._print_info(f"\n\n{i18n.t('interrupted')}")
        self.stop_backend()
        sys.exit(0)
    
    def _get_device_limit_for_plan(self, plan_id: int) -> int:
        """
        Get device limit for a given plan ID
        
        Args:
            plan_id: Plan ID (0=Iron/Chloros, 1=Copper, 2=Bronze, 3=Silver, 4=Gold, 86=MAPIR)
            
        Returns:
            Device limit for the plan
        """
        device_limits = {
            0: 1,    # Iron/Chloros (Free): 1 device
            1: 2,    # Copper: 2 devices
            2: 2,    # Bronze: 2 devices
            3: 5,    # Silver: 5 devices
            4: 10,   # Gold: 10 devices
            86: 999  # MAPIR: unlimited
        }
        return device_limits.get(plan_id, 1)  # Default to 1 if unknown
    
    def _get_plan_tier_name(self, plan_id: int) -> str:
        """
        Get plan tier name for a given plan ID
        
        Args:
            plan_id: Plan ID (matches MAPIR API: 0=Iron/Chloros, 1=Copper, 2=Bronze, 3=Silver, 4=Gold, 86=MAPIR)
            
        Returns:
            Plan tier name (e.g., "Copper", "Bronze", "Silver", etc.)
        """
        tier_names = {
            0: "Iron",
            1: "Copper",
            2: "Bronze",
            3: "Silver",
            4: "Gold",
            86: "MAPIR"
        }
        return tier_names.get(plan_id, "")
    
    def _print_verbose(self, message: str):
        """Print verbose message (unless suppressed for clean output)"""
        if self.verbose and not self.suppress_verbose_output:
            if self.use_colors:
                print(f"{ANSIColors.DIM}[VERBOSE] {message}{ANSIColors.RESET}")
            else:
                print(f"[VERBOSE] {message}")
    
    def _print_info(self, message: str):
        """Print info message"""
        if USE_FANCY_STYLES:
            print_info(message)
        elif self.use_colors:
            print(f"{ANSIColors.CHLOROS_GREEN}ℹ {message}{ANSIColors.RESET}")
        else:
            print(f"[INFO] {message}")
    
    def _print_success(self, message: str):
        """Print success message"""
        if USE_FANCY_STYLES:
            print_success(message)
        elif self.use_colors:
            print(f"{ANSIColors.GREEN}{Icons.SUCCESS} {message}{ANSIColors.RESET}")
        else:
            print(f"[SUCCESS] {message}")
    
    def _print_warning(self, message: str):
        """Print warning message"""
        if USE_FANCY_STYLES:
            print_warning(message)
        elif self.use_colors:
            print(f"{ANSIColors.YELLOW}⚠ {message}{ANSIColors.RESET}")
        else:
            print(f"[WARNING] {message}")
    
    def _print_error(self, message: str):
        """Print error message"""
        if USE_FANCY_STYLES:
            print_error(message)
        elif self.use_colors:
            print(f"{ANSIColors.RED}{Icons.ERROR} {message}{ANSIColors.RESET}", file=sys.stderr)
        else:
            print(f"[ERROR] {message}", file=sys.stderr)
    
    def _print_progress(self, percent: float, message: str = ""):
        """Print progress bar"""
        if USE_FANCY_STYLES:
            print_progress_bar(percent, message, width=50)
        else:
            bar_width = 40
            filled = int(bar_width * percent / 100)
            bar = '█' * filled + '░' * (bar_width - filled)
            
            if self.use_colors:
                print(f"\r{ANSIColors.CYAN}Progress:{ANSIColors.RESET} [{bar}] {percent:5.1f}% {message}", end='', flush=True)
            else:
                print(f"\rProgress: [{bar}] {percent:5.1f}% {message}", end='', flush=True)
    
    def _check_license_cache(self) -> bool:
        """
        Check if there's a valid license cache from GUI login
        
        Returns:
            True if valid license cache exists, False otherwise
        """
        try:
            # Import license cache
            from pathlib import Path
            import os
            
            # Determine cache file location
            if sys.platform == 'win32':
                cache_dir = Path(os.environ.get('APPDATA', Path.home())) / 'Chloros' / 'cache'
            elif sys.platform == 'darwin':
                cache_dir = Path.home() / 'Library' / 'Application Support' / 'Chloros' / 'cache'
            else:
                cache_dir = Path.home() / '.chloros' / 'cache'
            
            cache_file = cache_dir / 'license_cache.enc'
            
            # Check if cache file exists and is not empty
            if cache_file.exists() and cache_file.stat().st_size > 0:
                self._print_verbose(f"Found license cache at: {cache_file}")
                return True
            else:
                self._print_verbose(f"No license cache found at: {cache_file}")
                return False
        except Exception as e:
            self._print_verbose(f"Error checking license cache: {e}")
            return False
    
    def _prompt_for_login(self) -> bool:
        """
        Prompt user for username and password to login
        
        Returns:
            True if login successful, False otherwise
        """
        try:
            import getpass
            
            print()
            self._print_warning(i18n.t('no_cached_license'))
            self._print_info(i18n.t('cli_requires_license'))
            print()
            
            # Prompt for email
            try:
                email = input("Email: ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                self._print_error(i18n.t('login_cancelled'))
                return False
            
            if not email:
                self._print_error(i18n.t('email_empty'))
                return False
            
            # Prompt for password
            try:
                password = getpass.getpass("Password: ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                self._print_error(i18n.t('login_cancelled'))
                return False
            
            if not password:
                self._print_error(i18n.t('password_empty'))
                return False
            
            print()
            
            # Now login - but we need the backend running first
            # So we'll return the credentials and let the caller handle it
            self.pending_login_email = email
            self.pending_login_password = password
            return True
            
        except Exception as e:
            self._print_error(f"Failed to prompt for login: {e}")
            return False
    
    def _stream_output(self, pipe, prefix):
        """Stream output from a pipe to console (suppressed in clean mode)"""
        try:
            if self.suppress_verbose_output:
                # Silently consume output to prevent pipe blocking
                for line in iter(pipe.readline, b''):
                    pass
            else:
                # Normal verbose output
                for line in iter(pipe.readline, b''):
                    if line:
                        decoded = line.decode('utf-8', errors='replace').rstrip()
                        if decoded:
                            print(f"{prefix}: {decoded}", flush=True)
        except Exception:
            pass
    
    def _kill_backend_process(self) -> bool:
        """
        Surgically kill only the backend_server.py process, not other Python processes
        
        Returns:
            True if successfully killed, False otherwise
        """
        try:
            if os.name == 'nt':  # Windows
                # Try psutil first (most reliable)
                try:
                    import psutil
                    killed_any = False
                    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                        try:
                            if proc.info['name'] and 'python' in proc.info['name'].lower():
                                cmdline = proc.info['cmdline']
                                if cmdline and any('backend_server.py' in str(arg) for arg in cmdline):
                                    self._print_verbose(f"Killing backend process PID {proc.info['pid']}")
                                    proc.kill()
                                    killed_any = True
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                    if killed_any:
                        return True
                except ImportError:
                    self._print_verbose("psutil not available, using netstat method")
                
                # Fallback: Find PID using port and kill it
                try:
                    # Find process listening on our port
                    result = subprocess.run(
                        f'netstat -ano | findstr :{self.port} | findstr LISTENING',
                        shell=True, capture_output=True, text=True, timeout=5
                    )
                    if result.stdout:
                        # Extract PID from last column
                        for line in result.stdout.strip().split('\n'):
                            parts = line.split()
                            if len(parts) >= 5:
                                pid = parts[-1]
                                self._print_verbose(f"Killing process on port {self.port}, PID {pid}")
                                subprocess.run(['taskkill', '/F', '/PID', pid], 
                                             capture_output=True, check=False)
                                return True
                except Exception as e:
                    self._print_verbose(f"Netstat method failed: {e}")
                
                return False
            else:  # Unix-like
                # Use pkill with exact match for backend_server.py
                result = subprocess.run(['pkill', '-9', '-f', 'backend_server.py'], 
                                      capture_output=True, check=False)
                return result.returncode == 0
        except Exception as e:
            self._print_verbose(f"Error killing backend process: {e}")
            return False
    
    def _is_backend_stale(self) -> bool:
        """
        Check if existing backend is stale and should be restarted
        
        Returns:
            True if backend is stale (has a project loaded), False if fresh
        """
        try:
            # Simple stale check - does backend have files loaded?
            status_response = requests.get(f'{self.api_url}/api/status', timeout=2)
            if status_response.ok:
                status = status_response.json()
                # Backend returns 'image_count', not 'files_count'
                status_data = status.get('status', status)  # Unwrap if nested
                files_count = status_data.get('image_count', status_data.get('files_count', 0))
                
                if files_count > 0:
                    self._print_verbose(f"Backend has {files_count} files loaded - considered stale")
                    return True
                
                self._print_verbose("Backend is clean (no files loaded)")
                return False
            else:
                # Can't get status - assume stale to be safe
                self._print_verbose("Cannot get backend status - considering stale")
                return True
                
        except Exception as e:
            # Error checking - assume stale
            self._print_verbose(f"Error checking backend: {e} - considering stale")
            return True
    
    def start_backend(self, skip_license_check: bool = False, for_login: bool = False, force_fresh: bool = False) -> bool:
        """
        Start the Chloros backend server
        
        Args:
            skip_license_check: If True, skip license check (for login command)
            for_login: If True, tell backend to skip auth checks (for login endpoint)
            force_fresh: If True, kill existing backend and start fresh (for processing)
            
        Returns:
            True if backend started successfully, False otherwise
        """
        if self.backend_exe is None:
            self._print_error(i18n.t('backend_not_found'))
            return False
        
        self._print_verbose(f"start_backend called with force_fresh={force_fresh}")
        
        # Check if backend is already running
        backend_exists = self._is_backend_running()
        self._print_verbose(f"Backend exists: {backend_exists}")
        
        # Check if backend is stale and auto-restart if needed
        if not force_fresh and backend_exists:
            is_stale = self._is_backend_stale()
            if is_stale:
                print("⚠ Existing backend has cached data - restarting automatically...", flush=True)
                force_fresh = True
        
        # If force_fresh requested (via flag or stale detection), stop existing backend
        if force_fresh and backend_exists:
            self._print_warning("Restarting backend with fresh instance...")
            
            # Try graceful shutdown first
            try:
                response = requests.post(f'{self.api_url}/api/shutdown', timeout=3)
                self._print_verbose(f"Shutdown request sent: {response.status_code if response else 'no response'}")
            except Exception as e:
                self._print_verbose(f"Shutdown request failed: {e}")
            
            # Wait for backend to shut down gracefully
            import time
            max_wait = 5  # Wait up to 5 seconds for graceful shutdown
            waited = 0
            while waited < max_wait and self._is_backend_running():
                time.sleep(1)
                waited += 1
                self._print_verbose(f"Waiting for graceful shutdown... ({waited}s)")
            
            # If still running, surgically kill only the backend process
            if self._is_backend_running():
                self._print_verbose("Backend did not shut down gracefully, force killing backend process...")
                if self._kill_backend_process():
                    self._print_verbose("Backend process terminated")
                    time.sleep(2)  # Wait for port release
                else:
                    self._print_warning("Could not kill backend process - will try to start anyway")
                    time.sleep(1)
            else:
                self._print_verbose("Backend shut down successfully")
                time.sleep(1)  # Extra wait for port release
        
        # Check if backend is already running (and we're not forcing fresh)
        if not force_fresh and self._is_backend_running():
            self._print_success(i18n.t('backend_already_running'))
            self._print_verbose(f"Backend already responding at {self.api_url}")
            self._print_info(i18n.t('using_existing_backend'))
            
            # Check license status if not skipping check
            if not skip_license_check:
                self._check_license_status()
            
            return True
        
        # Check if port is in use but not responding to our API
        if self._check_port_in_use():
            self._print_warning(f"Port {self.port} is in use but not responding to Chloros API")
            self._print_info(i18n.t('will_attempt_start'))
        
        # Check for license cache before starting backend (unless explicitly skipped)
        if not skip_license_check:
            if not self._check_license_cache():
                # No license cache found - prompt for login
                if not self._prompt_for_login():
                    return False
                
                # Start backend first so we can login
                self._print_info(i18n.t('starting_for_auth'))
                skip_license_check = True  # Skip check for this recursive call
                if not self.start_backend(skip_license_check=True, for_login=True):
                    return False
                
                # Now login with the credentials
                if hasattr(self, 'pending_login_email') and hasattr(self, 'pending_login_password'):
                    if not self.login(self.pending_login_email, self.pending_login_password):
                        self.stop_backend()
                        return False
                    # Clear pending credentials
                    delattr(self, 'pending_login_email')
                    delattr(self, 'pending_login_password')
                    
                    # License now cached - backend can be restarted if needed
                    return True
        
        self._print_info(i18n.t('starting_backend'))
        self._print_verbose(i18n.t('verbose_backend', path=self.backend_exe))
        self._print_verbose(i18n.t('verbose_port', port=self.port))
        
        # Prepare environment for backend
        env = os.environ.copy()
        
        # If starting for login, skip authentication checks in backend
        if for_login:
            env['CHLOROS_SKIP_AUTH'] = '1'
            self._print_verbose("Backend will skip authentication for login")
        
        # Start backend process
        try:
            # Set working directory to the backend's directory
            # This is critical for the backend to find its dependencies
            backend_dir = os.path.dirname(os.path.abspath(self.backend_exe))
            self._print_verbose(f"Backend working directory: {backend_dir}")
            
            # Check if backend executable exists
            if not os.path.exists(self.backend_exe):
                self._print_error(f"Backend executable not found: {self.backend_exe}")
                return False
            
            if self.backend_exe.endswith('.py'):
                # Run Python script
                cmd = [sys.executable, self.backend_exe]
                self._print_verbose(f"Starting backend: {' '.join(cmd)}")
                self.backend_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=backend_dir,
                    env=env,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
                )
            else:
                # Run compiled executable
                cmd = [self.backend_exe]
                self._print_verbose(f"Starting backend: {' '.join(cmd)}")
                # For .exe files, always capture output so we can display errors
                # Even in verbose mode, we need to capture to show errors if it crashes
                self.backend_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=backend_dir,
                    env=env,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
                )
            
            # Start output streaming threads in verbose mode
            if self.verbose:
                import threading
                stdout_thread = threading.Thread(
                    target=self._stream_output,
                    args=(self.backend_process.stdout, "[BACKEND]"),
                    daemon=True
                )
                stderr_thread = threading.Thread(
                    target=self._stream_output,
                    args=(self.backend_process.stderr, "[BACKEND-ERR]"),
                    daemon=True
                )
                stdout_thread.start()
                stderr_thread.start()
            
            # Wait for backend to be ready
            return self._wait_for_backend(for_login=for_login)
            
        except Exception as e:
            self._print_error(f"Failed to start backend: {e}")
            return False
    
    def _is_backend_running(self) -> bool:
        """Check if backend is already running"""
        try:
            response = requests.get(f'{self.api_url}/api/get-config', timeout=2)
            # Accept any HTTP response (200, 404, etc.) as proof backend is alive
            # The endpoint returns 404 when no project is loaded, which is fine
            return response.status_code in [200, 404, 500]
        except requests.exceptions.RequestException:
            return False
        except Exception:
            return False
    
    def _check_port_in_use(self) -> bool:
        """Check if the port is in use by something"""
        import socket
        try:
            # Try to connect to the port
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', self.port))
            sock.close()
            return result == 0  # Port is in use if connection succeeds
        except Exception:
            return False
    
    def _wait_for_backend(self, timeout: int = 60, for_login: bool = False) -> bool:
        """
        Wait for backend to be ready
        
        Args:
            timeout: Maximum wait time in seconds
            
        Returns:
            True if backend is ready, False if timeout
        """
        self._print_info(i18n.t('waiting_backend'))
        
        start_time = time.time()
        last_dot_time = start_time
        
        while time.time() - start_time < timeout:
            # Print dots every second
            if time.time() - last_dot_time >= 1:
                print(".", end='', flush=True)
                last_dot_time = time.time()
            
            # Check if backend is ready
            try:
                response = requests.get(f'{self.api_url}/api/get-config', timeout=2)
                # Accept any HTTP response as proof backend is alive
                # 200 = config available, 404 = no project loaded (still alive), 500 = error but responding
                if response.status_code in [200, 404, 500]:
                    print()  # New line after dots
                    self._print_success(i18n.t('backend_ready'))
                    
                    # Check license status (skip for login command as it will show after login)
                    if not for_login:
                        self._check_license_status()
                    
                    return True
            except requests.exceptions.RequestException:
                pass
            
            # Check if backend process died
            if self.backend_process and self.backend_process.poll() is not None:
                print()  # New line after dots
                exit_code = self.backend_process.poll()
                self._print_error(i18n.t('backend_terminated'))
                self._print_verbose(f"Backend exit code: {exit_code}")
                
                # Try to capture any remaining output (if not in verbose mode with threads)
                if not self.verbose and self.backend_process.stderr and self.backend_process.stdout:
                    try:
                        # Give threads a moment to finish if they exist
                        time.sleep(0.5)
                        stderr_output = self.backend_process.stderr.read().decode('utf-8', errors='replace')
                        stdout_output = self.backend_process.stdout.read().decode('utf-8', errors='replace')
                        if stdout_output.strip():
                            print("\nBackend stdout:")
                            print(stdout_output)
                        if stderr_output.strip():
                            print("\nBackend stderr:")
                            print(stderr_output)
                    except Exception as e:
                        self._print_verbose(f"Could not read backend output: {e}")
                
                # Check for common issues
                if self._check_port_in_use():
                    print()
                    self._print_error(f"Port {self.port} is already in use")
                    self._print_info(i18n.t('gui_may_be_running'))
                    self._print_info(i18n.t('close_gui_and_retry'))
                    self._print_info(i18n.t('or_use_existing'))
                    print()
                else:
                    self._print_error(i18n.t('backend_license_fail'))
                    self._print_info(i18n.t('cli_requires_license'))
                    self._print_info(i18n.t('activate_license'))
                return False
            
            time.sleep(0.5)
        
        print()  # New line after dots
        self._print_error(i18n.t('backend_failed_start', timeout=timeout))
        return False
    
    def _check_license_status(self):
        """Check and display license status"""
        try:
            # Try to get session info (includes license)
            response = requests.get(f'{self.api_url}/api/get-session-info', timeout=5)
            if response.ok:
                session_info = response.json()
                plan_id = session_info.get('plan_id', 0)
                plan_name = session_info.get('plan_name', 'Unknown')
                
                # Show license info in a nice box if fancy styles available
                if USE_FANCY_STYLES and plan_id > 0:
                    tier_name = self._get_plan_tier_name(plan_id)
                    device_limit = self._get_device_limit_for_plan(plan_id)
                    device_limit_str = "Unlimited" if device_limit >= 999 else str(device_limit)
                    # Use tier_name if plan_name is Unknown, otherwise show both
                    if plan_name == "Unknown" and tier_name:
                        plan_display = tier_name
                    else:
                        plan_display = f"{plan_name}" + (f" ({tier_name})" if tier_name and tier_name != plan_name else "")
                    license_info = f"{i18n.t('license_info', plan=plan_display)}\n{i18n.t('device_limit')}: {device_limit_str}\n{i18n.t('license_status')}"
                    print(Box.create(license_info, width=60, style='single', color=ANSIColors.CHLOROS_GREEN))
                elif self.verbose:
                    tier_name = self._get_plan_tier_name(plan_id)
                    device_limit = self._get_device_limit_for_plan(plan_id)
                    device_limit_str = "Unlimited" if device_limit >= 999 else str(device_limit)
                    # Use tier_name if plan_name is Unknown, otherwise show both
                    if plan_name == "Unknown" and tier_name:
                        plan_display = tier_name
                    else:
                        plan_display = f"{plan_name}" + (f" ({tier_name})" if tier_name and tier_name != plan_name else "")
                    self._print_info(f"{i18n.t('license_info', plan=plan_display)} (ID: {plan_id}), {i18n.t('device_limit')}: {device_limit_str}")
                
                # Warn if using free plan (shouldn't be possible, but check anyway)
                if plan_id == 0:
                    self._print_warning(i18n.t('using_free_plan'))
                    self._print_warning(i18n.t('cli_requires_plus'))
                    self._print_info(i18n.t('upgrade_url'))
        except:
            # If we can't check license, just continue
            # Backend will enforce license requirements
            pass
    
    def login(self, email: str, password: str) -> bool:
        """
        Authenticate with Chloros cloud account
        
        Args:
            email: User email address
            password: User password
            
        Returns:
            True if login successful, False otherwise
        """
        if USE_I18N:
            self._print_info(i18n.t('authenticating'))
        else:
            self._print_info(f"Authenticating with {email}...")
        
        try:
            self._print_verbose(f"Sending login request to {self.api_url}/api/login")
            
            response = requests.post(
                f'{self.api_url}/api/login',
                json={
                    'email': email,
                    'password': password
                },
                timeout=15
            )
            
            self._print_verbose(f"Login response status: {response.status_code}")
            if self.verbose and response.status_code != 200:
                self._print_verbose(f"Response body: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                if self.verbose:
                    self._print_verbose(f"Login response data: {json.dumps(data, indent=2)}")
                
                if data.get('success'):
                    # Plan data is nested in 'user' object
                    user_data = data.get('user', {})
                    plan_id = user_data.get('plan_id', 0)
                    
                    # Derive plan name from plan_id
                    tier_name = self._get_plan_tier_name(plan_id)
                    plan_name = tier_name if tier_name else f"Plan {plan_id}"
                    
                    self._print_success(i18n.t('login_success') if USE_I18N else "Login successful!")
                    
                    # Show license info
                    if USE_FANCY_STYLES and plan_id > 0:
                        device_limit = self._get_device_limit_for_plan(plan_id)
                        device_limit_str = i18n.t('unlimited') if device_limit >= 999 else str(device_limit)
                        cli_enabled = plan_id in [2, 3, 4, 86]
                        license_info = f"{i18n.t('account')}: {email}\nPlan: Chloros+ ({plan_name})\n{i18n.t('device_limit')}: {device_limit_str}\n{i18n.t('cli_access')}: {Icons.SUCCESS + ' ' + i18n.t('enabled') if cli_enabled else Icons.ERROR + ' ' + i18n.t('disabled')}"
                        print()
                        print(Box.create(license_info, width=60, style='single', color=ANSIColors.GREEN))
                        print()
                    else:
                        device_limit = self._get_device_limit_for_plan(plan_id)
                        device_limit_str = "Unlimited" if device_limit >= 999 else str(device_limit)
                        self._print_info(f"Plan: Chloros+ ({plan_name}), Device Limit: {device_limit_str}")
                    
                    # Warn if not Chloros+ plan (Bronze, Silver, Gold)
                    if plan_id not in [2, 3, 4, 86]:
                        self._print_warning(i18n.t('cli_requires_plus_full'))
                        self._print_info(i18n.t('plan_no_cli_access'))
                        self._print_info(i18n.t('upgrade_url'))
                        return False
                    
                    return True
                else:
                    error_msg = data.get('message', 'Unknown error')
                    self._print_error(f"Login failed: {error_msg}")
                    return False
            
            elif response.status_code == 401:
                # SMART RETRY 1: Try appending $$ to password
                # PowerShell strips $$ from double-quoted strings entirely
                # e.g., "mapir2025$$" becomes "mapir2025"
                self._print_verbose(f"Login failed, trying with $$ appended to password...")
                
                try:
                    retry_password = password + '$$'
                    retry_response = requests.post(
                        f'{self.api_url}/api/login',
                        json={
                            'email': email,
                            'password': retry_password
                        },
                        timeout=15
                    )
                    
                    if retry_response.status_code == 200:
                        retry_data = retry_response.json()
                        if retry_data.get('success'):
                            print()
                            self._print_warning("⚠ Login succeeded with corrected password!")
                            print()
                            self._print_info("PowerShell stripped $$ from your password (double quotes expand $$ to nothing).")
                            self._print_info("To avoid this, use SINGLE QUOTES for passwords with $:")
                            print()
                            print(f"  {Icons.SUCCESS} Correct:   chloros-cli login {email} 'your_password$$'")
                            print(f"  {Icons.ERROR} Incorrect: chloros-cli login {email} \"your_password$$\"")
                            print()
                            
                            # Continue with successful login
                            user_data = retry_data.get('user', {})
                            plan_id = user_data.get('plan_id', 0)
                            tier_name = self._get_plan_tier_name(plan_id)
                            plan_name = tier_name if tier_name else f"Plan {plan_id}"
                            
                            if USE_FANCY_STYLES and plan_id > 0:
                                device_limit = self._get_device_limit_for_plan(plan_id)
                                device_limit_str = "Unlimited" if device_limit >= 999 else str(device_limit)
                                cli_enabled = plan_id in [2, 3, 4, 86]
                                license_info = f"Account: {email}\nPlan: Chloros+ ({plan_name})\nDevice Limit: {device_limit_str}\nCLI Access: {Icons.SUCCESS + ' Enabled' if cli_enabled else Icons.ERROR + ' Disabled'}"
                                print(Box.create(license_info, width=60, style='single', color=ANSIColors.GREEN))
                                print()
                            else:
                                device_limit = self._get_device_limit_for_plan(plan_id)
                                device_limit_str = "Unlimited" if device_limit >= 999 else str(device_limit)
                                self._print_info(f"Plan: Chloros+ ({plan_name}), {i18n.t('device_limit')}: {device_limit_str}")
                            
                            if plan_id not in [2, 3, 4, 86]:
                                self._print_warning(i18n.t('cli_requires_plus_full'))
                                self._print_info(i18n.t('plan_no_cli_access'))
                                self._print_info(i18n.t('upgrade_url'))
                                return False
                            
                            return True
                except:
                    pass  # If retry fails, try next strategy
                
                # SMART RETRY 2: Detect if PowerShell duplicated the password
                # PowerShell's $$ variable can expand to the last token, causing duplication
                if len(password) > 4 and len(password) % 2 == 0:
                    half_len = len(password) // 2
                    first_half = password[:half_len]
                    second_half = password[half_len:]
                    
                    # Check if password appears to be duplicated (with possible $$ at the end)
                    if first_half == second_half or (second_half.startswith(first_half) and second_half.endswith('$$')):
                        self._print_verbose(f"Detected possible PowerShell $$ expansion (password appears duplicated)")
                        self._print_verbose(f"Retrying with deduplicated password...")
                        
                        # Try with just the first half (the original password)
                        retry_password = first_half
                        
                        try:
                            retry_response = requests.post(
                                f'{self.api_url}/api/login',
                                json={
                                    'email': email,
                                    'password': retry_password
                                },
                                timeout=15
                            )
                            
                            if retry_response.status_code == 200:
                                retry_data = retry_response.json()
                                if retry_data.get('success'):
                                    print()
                                    self._print_warning("⚠ Login succeeded with corrected password!")
                                    print()
                                    self._print_info("PowerShell's $$ variable expanded your password.")
                                    self._print_info("To avoid this, use SINGLE QUOTES for passwords with $:")
                                    print()
                                    print(f"  {Icons.SUCCESS} Correct:   chloros-cli login {email} 'your_password$$'")
                                    print(f"  {Icons.ERROR} Incorrect: chloros-cli login {email} \"your_password$$\"")
                                    print()
                                    
                                    # Continue with successful login
                                    user_data = retry_data.get('user', {})
                                    plan_id = user_data.get('plan_id', 0)
                                    tier_name = self._get_plan_tier_name(plan_id)
                                    plan_name = tier_name if tier_name else f"Plan {plan_id}"
                                    
                                    if USE_FANCY_STYLES and plan_id > 0:
                                        device_limit = self._get_device_limit_for_plan(plan_id)
                                        device_limit_str = "Unlimited" if device_limit >= 999 else str(device_limit)
                                        cli_enabled = plan_id in [2, 3, 4, 86]
                                        license_info = f"Account: {email}\nPlan: Chloros+ ({plan_name})\nDevice Limit: {device_limit_str}\nCLI Access: {Icons.SUCCESS + ' Enabled' if cli_enabled else Icons.ERROR + ' Disabled'}"
                                        print(Box.create(license_info, width=60, style='single', color=ANSIColors.GREEN))
                                        print()
                                    else:
                                        device_limit = self._get_device_limit_for_plan(plan_id)
                                        device_limit_str = "Unlimited" if device_limit >= 999 else str(device_limit)
                                        self._print_info(f"Plan: Chloros+ ({plan_name}), {i18n.t('device_limit')}: {device_limit_str}")
                                    
                                    if plan_id not in [2, 3, 4, 86]:
                                        self._print_warning(i18n.t('cli_requires_plus_full'))
                                        self._print_info(i18n.t('plan_no_cli_access'))
                                        self._print_info(i18n.t('upgrade_url'))
                                        return False
                                    
                                    return True
                        except:
                            pass  # If retry fails, fall through to normal error
                
                # Normal invalid credentials error
                self._print_error(i18n.t('invalid_credentials'))
                return False
            else:
                self._print_error(f"Login failed: HTTP {response.status_code}")
                return False
                
        except requests.exceptions.ConnectionError:
            self._print_error(i18n.t('cannot_connect_backend'))
            self._print_info(i18n.t('backend_required'))
            return False
        except requests.exceptions.Timeout:
            self._print_error(i18n.t('login_timeout'))
            return False
        except Exception as e:
            self._print_error(f"Login error: {e}")
            if self.verbose:
                import traceback
                traceback.print_exc()
            return False
    
    def logout(self) -> bool:
        """
        Logout and clear stored credentials
        
        Returns:
            True if logout successful, False otherwise
        """
        self._print_info(i18n.t('logging_out'))
        
        try:
            # Try to get current user email for proper cache clearing
            email = None
            try:
                session_response = requests.get(
                    f'{self.api_url}/api/get-session-info',
                    timeout=2
                )
                if session_response.status_code == 200:
                    session_data = session_response.json()
                    email = session_data.get('email')
            except:
                pass  # Continue with logout even if we can't get email
            
            # Send logout request with email if available
            response = requests.post(
                f'{self.api_url}/api/logout',
                json={'email': email} if email else {},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self._print_success(i18n.t('logged_out'))
                    self._print_info(i18n.t('credentials_cleared'))
                    return True
                else:
                    self._print_warning(i18n.t('logout_warnings'))
                    return True
            else:
                self._print_error(f"Logout failed: HTTP {response.status_code}")
                return False
                
        except requests.exceptions.ConnectionError:
            self._print_error("Cannot connect to backend server")
            return False
        except Exception as e:
            self._print_error(f"Logout error: {e}")
            if self.verbose:
                import traceback
                traceback.print_exc()
            return False
    
    def get_license_status(self) -> bool:
        """
        Get and display current license status
        
        Returns:
            True if license is valid, False otherwise
        """
        self._print_info(i18n.t('checking_license'))
        
        try:
            response = requests.get(
                f'{self.api_url}/api/license-status',
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('authenticated'):
                    email = data.get('email', 'Unknown')
                    plan_id = data.get('plan_id', 0)
                    expires = data.get('expires')
                    cli_enabled = plan_id in [2, 3, 4, 86]  # Bronze, Silver, Gold, MAPIR
                    
                    # Display license info
                    tier_name = self._get_plan_tier_name(plan_id)
                    device_limit = self._get_device_limit_for_plan(plan_id)
                    device_limit_str = "Unlimited" if device_limit >= 999 else str(device_limit)
                    plan_display = f"Chloros+ ({tier_name})" if tier_name else f"Plan {plan_id}"
                    
                    if USE_FANCY_STYLES:
                        status_info = f"{i18n.t('license_status')}\n"
                        status_info += f"{i18n.t('account')}: {email}\n"
                        status_info += f"Plan: {plan_display}\n"
                        status_info += f"{i18n.t('device_limit')}: {device_limit_str}\n"
                        if expires:
                            status_info += f"{i18n.t('expires')}: {expires}\n"
                        else:
                            status_info += f"{i18n.t('expires')}: {i18n.t('unlimited')}\n"
                        status_info += f"{i18n.t('cli_access')}: {Icons.SUCCESS + ' ' + i18n.t('enabled') if cli_enabled else Icons.ERROR + ' ' + i18n.t('disabled')}"
                        
                        print()
                        print(Box.create(status_info, width=60, style='double', 
                                       color=ANSIColors.GREEN if cli_enabled else ANSIColors.YELLOW))
                        print()
                    else:
                        print()
                        print(f"{Icons.SUCCESS} License Active")
                        print(f"  Account: {email}")
                        print(f"  Plan: {plan_display}")
                        print(f"  Device Limit: {device_limit_str}")
                        if expires:
                            print(f"  Expires: {expires}")
                        else:
                            print(f"  Expires: Unlimited")
                        print(f"  CLI Access: {Icons.SUCCESS + ' Enabled' if cli_enabled else Icons.ERROR + ' Disabled'}")
                        print()
                    
                    if not cli_enabled:
                        self._print_warning(i18n.t('cli_requires_plus'))
                        self._print_info(i18n.t('upgrade_url'))
                        return False
                    
                    return True
                else:
                    # Not authenticated
                    print()
                    print(i18n.t('not_authenticated'))
                    print()
                    self._print_info(i18n.t('need_login'))
                    self._print_info(i18n.t('run_login_command'))
                    self._print_info(i18n.t('or_activate_gui'))
                    print()
                    return False
                    
            elif response.status_code == 404:
                self._print_error(i18n.t('license_endpoint_unavailable'))
                self._print_info(i18n.t('backend_needs_update'))
                return False
            else:
                self._print_error(f"Failed to get license status: HTTP {response.status_code}")
                return False
                
        except requests.exceptions.ConnectionError:
            self._print_error(i18n.t('cannot_connect_backend'))
            self._print_info(i18n.t('backend_needs_running'))
            return False
        except Exception as e:
            self._print_error(f"Error checking license: {e}")
            if self.verbose:
                import traceback
                traceback.print_exc()
            return False
    
    def set_project_folder(self, folder: str) -> bool:
        """
        Set the default project folder location
        
        Args:
            folder: Path to the new project folder
            
        Returns:
            True if successful, False otherwise
        """
        try:
            folder_path = pathlib.Path(folder).resolve()
            
            # Create folder if it doesn't exist
            if not folder_path.exists():
                folder_path.mkdir(parents=True)
                self._print_verbose(f"Created folder: {folder_path}")
            
            if not folder_path.is_dir():
                self._print_error(f"Path is not a directory: {folder}")
                return False
            
            # Write to config file
            config_dir = pathlib.Path.home() / '.chloros'
            config_dir.mkdir(exist_ok=True)
            config_file = config_dir / 'working_directory.txt'
            
            config_file.write_text(str(folder_path))
            
            self._print_success(f"Project folder set to: {folder_path}")
            self._print_info(i18n.t('used_by_cli_and_gui'))
            return True
            
        except Exception as e:
            self._print_error(f"Failed to set project folder: {e}")
            return False
    
    def get_project_folder(self) -> bool:
        """
        Show the current default project folder location
        
        Returns:
            True if successful, False otherwise
        """
        try:
            config_dir = pathlib.Path.home() / '.chloros'
            config_file = config_dir / 'working_directory.txt'
            
            if config_file.exists():
                folder_path = config_file.read_text().strip()
                self._print_info(f"Current project folder: {folder_path}")
                
                if not pathlib.Path(folder_path).exists():
                    self._print_warning(i18n.t('folder_does_not_exist'))
                    return False
            else:
                default_path = pathlib.Path.home() / 'Chloros Projects'
                self._print_info(f"Project folder (default): {default_path}")
                if not default_path.exists():
                    self._print_info(i18n.t('will_create_when_needed'))
            
            return True
            
        except Exception as e:
            self._print_error(f"Failed to get project folder: {e}")
            return False
    
    def reset_project_folder(self) -> bool:
        """
        Reset project folder to default location
        
        Returns:
            True if successful, False otherwise
        """
        try:
            config_dir = pathlib.Path.home() / '.chloros'
            config_file = config_dir / 'working_directory.txt'
            
            if config_file.exists():
                config_file.unlink()
                self._print_success(i18n.t('project_folder_reset'))
            else:
                self._print_info(i18n.t('already_at_default'))
            
            default_path = pathlib.Path.home() / 'Chloros Projects'
            self._print_info(f"Default location: {default_path}")
            
            return True
            
        except Exception as e:
            self._print_error(f"Failed to reset project folder: {e}")
            return False
    
    def get_export_status(self) -> bool:
        """
        Get and display Thread 4 export progress
        
        Returns:
            True if successful, False otherwise
        """
        try:
            response = requests.get(
                f'{self.api_url}/api/get-thread-4-progress',
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success'):
                    percent = data.get('percent', 0)
                    phase = data.get('phase', 'Unknown')
                    time_remaining = data.get('timeRemaining', '')
                    is_active = data.get('isActive', False)
                    
                    # Print the export progress
                    if percent == 0 and not is_active:
                        print("Export Status: Not Started")
                    elif percent >= 100:
                        print("Export Status: 100% - Complete")
                    else:
                        status_msg = f"Export Status: {percent}%"
                        if time_remaining:
                            status_msg += f" ({time_remaining})"
                        print(status_msg)
                    
                    return True
                else:
                    error_msg = data.get('error', 'Unknown error')
                    self._print_error(f"Failed to get export status: {error_msg}")
                    return False
                    
            elif response.status_code == 404:
                self._print_error(i18n.t('export_endpoint_unavailable'))
                self._print_info(i18n.t('backend_needs_update'))
                return False
            else:
                self._print_error(f"Failed to get export status: HTTP {response.status_code}")
                return False
                
        except requests.exceptions.ConnectionError:
            self._print_error(i18n.t('cannot_connect_backend'))
            self._print_info(i18n.t('backend_needs_running'))
            return False
        except Exception as e:
            self._print_error(f"Error checking export status: {e}")
            if self.verbose:
                import traceback
                traceback.print_exc()
            return False
    
    def stop_backend(self):
        """Stop the backend server"""
        if self.backend_process:
            self._print_verbose(i18n.t('verbose_stopping'))
            
            # CRITICAL: Call shutdown API first to trigger proper cleanup (debayer cache, etc.)
            try:
                self._print_verbose("Calling shutdown API for proper cleanup...")
                response = requests.post(f'{self.api_url}/api/shutdown', timeout=3)
                if response.status_code == 200:
                    self._print_verbose("Shutdown API called successfully, waiting for cleanup...")
                    # Give backend time to clean up (debayer cache removal, etc.)
                    import time
                    time.sleep(1.5)
            except Exception as e:
                self._print_verbose(f"Shutdown API call failed (non-critical): {e}")
            
            # Now terminate the process if it's still running
            try:
                if self.backend_process.poll() is None:  # Still running
                    self.backend_process.terminate()
                    self.backend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._print_warning(i18n.t('verbose_force_shutdown'))
                self.backend_process.kill()
            except Exception as e:
                self._print_warning(i18n.t('verbose_error_stopping', error=e))
            
            self.backend_process = None
    
    def process_images(
        self,
        input_folder: str,
        output_folder: Optional[str] = None,
        project_name: Optional[str] = None,
        **settings
    ) -> bool:
        """
        Process images in a folder
        
        Args:
            input_folder: Path to folder containing source images (RAW/JPG files)
            output_folder: Project folder path. If not specified, uses global project path + auto-generated name
            **settings: Processing settings (see _build_config for options)
            
        Returns:
            True if processing succeeded, False otherwise
            
        Note:
            Input files stay in their original location.
            Project folder contains project.json and output subfolders (e.g., Survey3N_RGN/).
        """
        # Validate input folder
        input_path = pathlib.Path(input_folder).resolve()
        if not input_path.exists():
            self._print_error(i18n.t('input_not_exist', path=input_folder))
            return False
        
        if not input_path.is_dir():
            self._print_error(i18n.t('input_not_folder', path=input_folder))
            return False
        
        # Determine project folder location
        if output_folder is None:
            # Use global project path + project name
            # Generate project name if not provided
            if project_name is None:
                import datetime
                # Use only timestamp so folders sort chronologically
                project_name = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            else:
                # Sanitize the provided project name
                import re
                project_name = re.sub(r'[<>:"/\\|?*]', '_', project_name)
            
            # Get global project path
            try:
                response = requests.get(f'{self.api_url}/api/get-working-directory', timeout=5)
                if response.ok:
                    global_project_path = response.json().get('path')
                    project_folder = str(pathlib.Path(global_project_path) / project_name)
                else:
                    # Fallback to default
                    default_path = pathlib.Path.home() / 'Chloros Projects'
                    project_folder = str(default_path / project_name)
            except:
                # Fallback to default
                default_path = pathlib.Path.home() / 'Chloros Projects'
                project_folder = str(default_path / project_name)
            
            self._print_verbose(f"Project name: {project_name}")
            self._print_verbose(f"Project folder: {project_folder}")
        else:
            # Use specified output folder as project folder
            project_folder = str(pathlib.Path(output_folder).resolve())
            # Extract project name from output folder path
            project_name = pathlib.Path(project_folder).name
            self._print_verbose(f"Using specified project folder: {project_folder}")
            self._print_verbose(f"Project name: {project_name}")
        
        # Show workflow steps if fancy styles available
        if USE_FANCY_STYLES:
            print_banner(i18n.t('processing_workflow'))
        
        # Step 1: Create project and import images
        if USE_FANCY_STYLES:
            print_step(1, 3, f"Creating project and importing from: {input_folder}")
        else:
            self._print_info(f"Creating project from: {input_folder}")
        
        try:
            self._print_verbose(f"Input folder: {input_path.absolute()}")
            self._print_verbose(f"Project folder: {project_folder}")
            
            # First create/load the project folder
            self._print_verbose(f"Calling /api/load-project with path: {project_folder}")
            response = requests.post(
                f'{self.api_url}/api/load-project',
                json={'project_path': project_folder},
                timeout=30
            )
            
            if not response.ok:
                self._print_error(f"Failed to create project: {response.text}")
                return False
            
            # Log the actual project path that was loaded
            project_info = response.json().get('project_info', {})
            actual_path = project_info.get('path', 'unknown')
            self._print_verbose(f"Backend loaded project at: {actual_path}")
            
            # Now import images from the input folder into the project
            self._print_verbose(f"Importing images from: {input_path.absolute()}")
            self._print_verbose(f"Calling /api/import-from-folder")
            response = requests.post(
                f'{self.api_url}/api/import-from-folder',
                json={'folder_path': str(input_path.absolute()), 'recursive': False},
                timeout=60
            )
            
            self._print_verbose(f"Import response status: {response.status_code}")
            
            if self.verbose:
                self._print_verbose(f"Response: {response.text[:500]}")
            
            if not response.ok:
                print(f"  {Icons.ERROR} Import failed: {response.text[:200]}", flush=True)
                self._print_error(i18n.t('failed_load_project', error=response.text))
                return False
            
            result = response.json()
            self._print_verbose(f"Import API returned: {str(result)[:200]}")
            
            # Backend returns 'files' not 'images'
            files = result.get('files', [])
            image_count = len(files)
            self._print_verbose(f"Backend returned {image_count} files")
            
            if image_count == 0:
                self._print_warning(i18n.t('no_images_found'))
                return False
            
            self._print_success(i18n.t('found_images', count=image_count))
            
            # IMMEDIATELY verify files are still loaded in backend
            import time
            time.sleep(0.5)  # Brief pause to let backend settle
            status_check = requests.get(f'{self.api_url}/api/status', timeout=5)
            if status_check.ok:
                status = status_check.json()
                # Backend returns 'image_count', not 'files_count'
                status_data = status.get('status', status)  # Unwrap if nested
                backend_files = status_data.get('image_count', status_data.get('files_count', 0))
                self._print_verbose(f"Backend status: {backend_files} files loaded")
                
                if backend_files == 0:
                    print(f"\n⚠ Backend is in a stale state - restarting automatically...", flush=True)
                    
                    # Kill and restart backend
                    self._kill_backend_process()
                    time.sleep(1)
                    
                    # Start fresh backend
                    if not self.start_backend(force_fresh=True):
                        self._print_error("Failed to restart backend")
                        return False
                    
                    self._print_verbose("Backend restarted, retrying import")
                    
                    # Retry: Create/load the project folder
                    response = requests.post(
                        f'{self.api_url}/api/load-project',
                        json={'project_path': project_folder},
                        timeout=30
                    )
                    
                    if not response.ok:
                        self._print_error(f"Failed to create project after restart: {response.text}")
                        return False
                    
                    # Retry: Import images
                    self._print_verbose("Retrying /api/import-from-folder")
                    response = requests.post(
                        f'{self.api_url}/api/import-from-folder',
                        json={'folder_path': str(input_path.absolute()), 'recursive': False},
                        timeout=60
                    )
                    
                    self._print_verbose(f"Retry import API response: {response.status_code}")
                    
                    if not response.ok:
                        self._print_error(f"Failed to import images after restart: {response.text}")
                        return False
                    
                    result = response.json()
                    self._print_verbose(f"Retry import returned: {str(result)[:200]}")
                    files = result.get('files', [])
                    image_count = len(files)
                    self._print_verbose(f"Retry reported {image_count} files in response")
                    
                    if image_count == 0:
                        self._print_error("Still no images after restart - check input folder")
                        return False
                    
                    # Verify again
                    time.sleep(0.5)
                    status_check2 = requests.get(f'{self.api_url}/api/status', timeout=5)
                    if status_check2.ok:
                        status2 = status_check2.json()
                        status_data2 = status2.get('status', status2)
                        backend_files2 = status_data2.get('image_count', status_data2.get('files_count', 0))
                        print(f"  {Icons.SUCCESS} Backend restarted: {backend_files2} files loaded", flush=True)
                        
                        if backend_files2 == 0:
                            self._print_error("Files still disappearing after restart - backend issue")
                            return False
                    
                elif backend_files != image_count:
                    print(f"  ⚠ Warning: File count mismatch (imported {image_count}, backend has {backend_files})")
            else:
                print(f"  ⚠ Could not verify backend status", flush=True)
            
        except requests.exceptions.RequestException as e:
            self._print_error(i18n.t('failed_connect_backend', error=e))
            return False
        except Exception as e:
            self._print_error(i18n.t('unexpected_error_loading', error=e))
            return False
        
        # Step 2: Update configuration if settings provided
        config = self._build_config(settings)
        # Only apply config if there are actual settings (not just empty dict)
        has_custom_settings = bool(config.get("Project Settings"))
        
        if has_custom_settings:
            if USE_FANCY_STYLES:
                print_step(2, 3, i18n.t('applying_settings'))
            else:
                self._print_info(i18n.t('applying_settings_msg'))
            
            # Note: The /api/set-config endpoint expects path/value format
            # For now, we'll apply settings by updating the project config directly
            # TODO: Implement proper config update endpoint or iterate through settings
            try:
                response = requests.post(
                    f'{self.api_url}/api/update-project-config',
                    json=config,
                    timeout=10
                )
                
                if response.ok:
                    self._print_verbose(i18n.t('config_updated'))
                else:
                    # Only warn if it's a real error (not just endpoint not found)
                    if response.status_code != 404:
                        self._print_verbose(f"Config update returned {response.status_code}, continuing...")
                    
            except requests.exceptions.RequestException:
                # If endpoint doesn't exist, that's okay - settings will use defaults
                self._print_verbose("Using default settings")
        else:
            # No custom settings - skip this step silently
            if USE_FANCY_STYLES:
                print_step(2, 3, "Applying custom settings")
            elif self.verbose:
                self._print_verbose("No custom settings specified, using defaults")
        
        # Step 3: Set processing mode and start processing (combined)
        if USE_FANCY_STYLES:
            print_step(3, 3, "Processing")
        else:
            self._print_info("Starting processing")
        
        processing_mode = settings.get('processing_mode', 'serial')
        if processing_mode == 'parallel':
            self._print_verbose(i18n.t('enabling_parallel'))
            try:
                response = requests.post(
                    f'{self.api_url}/api/set-processing-mode',
                    json={'mode': 'premium'},
                    timeout=10
                )
                
                if response.status_code == 403:
                    # Subscription check failed
                    error_data = response.json()
                    error_msg = error_data.get('message', 'Premium mode requires Chloros+ subscription')
                    self._print_error(error_msg)
                    self._print_info(i18n.t('please_login_command'))
                    self._print_info(i18n.t('upgrade_url'))
                    return False
                elif not response.ok:
                    self._print_warning(i18n.t('parallel_failed'))
                    if self.verbose:
                        self._print_verbose(f"Response: {response.text}")
                    processing_mode = 'serial'
                else:
                    self._print_verbose(i18n.t('parallel_enabled'))
            except Exception as e:
                self._print_warning(i18n.t('failed_update_config', error=e))
                processing_mode = 'serial'
        
        # Continue with Step 3: Start processing (already printed above)
        self._print_verbose(i18n.t('starting_processing', mode=processing_mode))
        
        # Verify files are STILL loaded right before processing
        self._print_verbose("Verifying files before processing")
        try:
            pre_process_check = requests.get(f'{self.api_url}/api/status', timeout=5)
            if pre_process_check.ok:
                status = pre_process_check.json()
                status_data = status.get('status', status)
                files_before = status_data.get('image_count', status_data.get('files_count', 0))
                self._print_verbose(f"Files ready: {files_before}")
                
                if files_before == 0:
                    print(f"\n⚠ ERROR: No files loaded before processing!")
                    print(f"  Backend lost the files between import and process.")
                    print(f"  Try running with --restart flag.")
                    return False
        except Exception as e:
            print(f"  ⚠ Could not verify files: {e}", flush=True)
        
        # Start processing in a background thread since it's synchronous
        import threading
        processing_error = [None]  # Use list to allow modification in thread
        processing_complete = [False]
        
        def start_processing():
            try:
                self._print_verbose(f"[PROCESS-REQ] Calling POST {self.api_url}/api/process-project")
                import time
                request_start = time.time()
                
                # Backend should return immediately (async processing)
                response = requests.post(
                    f'{self.api_url}/api/process-project',
                    timeout=30  # 30 second timeout (should respond in <1s)
                )
                
                request_duration = time.time() - request_start
                self._print_verbose(f"[PROCESS-REQ] Response received in {request_duration:.2f}s")
                self._print_verbose(f"[PROCESS-REQ] Response status: {response.status_code}")
                self._print_verbose(f"[PROCESS-REQ] Response body: {response.text[:200]}")
                
                if not response.ok:
                    processing_error[0] = f"HTTP {response.status_code}: {response.text}"
                    self._print_verbose(f"[PROCESS-REQ] ❌ Error: {processing_error[0]}")
                else:
                    processing_complete[0] = True
                    self._print_verbose(f"[PROCESS-REQ] ✅ Processing completed successfully")
                    
            except requests.exceptions.Timeout as e:
                processing_error[0] = f"Process request timed out after 10s"
                self._print_verbose(f"[PROCESS-REQ] ❌ Timeout: {e}")
                print(f"  {Icons.ERROR} Process request TIMEOUT (10s)", flush=True)
                print(f"  {Icons.ERROR} Backend is not responding to process requests", flush=True)
                print(f"  {Icons.ERROR} This usually means the backend is stuck or crashed", flush=True)
            except Exception as e:
                processing_error[0] = str(e)
                self._print_verbose(f"[PROCESS-REQ] ❌ Exception: {e}")
                print(f"  {Icons.ERROR} Process request exception: {e}", flush=True)
                if self.verbose:
                    import traceback
                    traceback.print_exc()
        
        # Start processing in background thread
        self._print_verbose("Starting background processing thread")
        processing_thread = threading.Thread(target=start_processing, daemon=True)
        processing_thread.start()
        
        # Give it a moment to start and verify it's actually processing
        import time
        self._print_verbose("Waiting for backend to start processing")
        
        # Wait up to 15 seconds for the process request to complete
        max_wait = 15
        wait_start = time.time()
        while processing_thread.is_alive() and time.time() - wait_start < max_wait:
            time.sleep(0.5)
            if processing_complete[0]:
                break
            if processing_error[0]:
                break
        
        elapsed = time.time() - wait_start
        self._print_verbose(f"Waited {elapsed:.1f}s for process request")
        
        # If there was an error, stop immediately
        if processing_error[0]:
            print(f"\n{Icons.ERROR} Cannot proceed: {processing_error[0]}", flush=True)
            print(f"  The backend is not responding to process requests.", flush=True)
            print(f"  Possible causes:", flush=True)
            print(f"    1. Backend is stuck or crashed", flush=True)
            print(f"    2. Backend process needs to be restarted", flush=True)
            print(f"    3. Try: Stop-Process -Name python -Force", flush=True)
            return False
        
        # Check if thread is still running (request hanging)
        if processing_thread.is_alive() and not processing_complete[0]:
            print(f"  ⚠ Process request still pending after {elapsed:.1f}s", flush=True)
            print(f"  ⚠ Continuing to monitor, but backend may be stuck", flush=True)
        
        # Check if processing actually started
        try:
            status_check = requests.get(f'{self.api_url}/api/status', timeout=5)
            if status_check.ok:
                status = status_check.json()
                status_data = status.get('status', status)
                is_processing = status.get('is_processing', status_data.get('is_processing', False))
                files_count = status_data.get('image_count', status_data.get('files_count', 0))
                
                self._print_verbose(f"Backend status: processing={is_processing}, files={files_count}")
                
                if not is_processing:
                    self._print_verbose(f"WARNING: Backend not processing yet (files={files_count})")
                    self._print_verbose("This may indicate processing hasn't started or backend is stuck")
                else:
                    # Show confirmation that processing started (verbose only)
                    self._print_verbose(f"Processing started ({files_count} images)")
        except Exception as e:
            self._print_verbose(f"Could not check backend status: {e}")
        
        self._print_verbose("Processing thread started, beginning progress monitoring...")
        
        # Print a blank line before progress bars
        print()
        
        # Monitor progress while thread is running
        self._print_verbose("Connecting to SSE endpoint for progress updates...")
        success = self._monitor_progress()
        
        self._print_verbose(f"Progress monitoring ended with success={success}")
        
        # Wait for processing thread to complete
        self._print_verbose("Waiting for processing thread to complete...")
        processing_thread.join(timeout=10)  # Wait up to 10 more seconds
        
        # Check for errors
        if processing_error[0]:
            self._print_error(i18n.t('failed_start_processing', error=processing_error[0]))
            return False
        
        if success:
            print()  # New line after progress bar
            if USE_FANCY_STYLES:
                print_divider()
            self._print_success(i18n.t('processing_complete'))
            self._print_info(f"Output: {project_folder}")
            if USE_FANCY_STYLES:
                print_divider()
            return True
        else:
            return False
    
    def _draw_progress_bars(self, thread_states: dict) -> None:
        """
        Draw modern progress bars for all 4 threads
        
        Args:
            thread_states: Dict with thread_id as key and {name, percent} as value
        """
        if not USE_FANCY_STYLES:
            return
        
        BAR_WIDTH = 40
        
        # Move cursor up 4 lines (to overwrite previous bars)
        if hasattr(self, '_progress_bars_drawn'):
            print('\033[4A', end='', flush=True)  # ANSI escape: move cursor up 4 lines
        self._progress_bars_drawn = True
        
        # Draw each thread's progress bar
        for thread_id in [1, 2, 3, 4]:
            state = thread_states.get(thread_id, {'name': f'Thread {thread_id}', 'percent': 0})
            name = state['name']
            percent = state['percent']
            
            # Calculate filled and empty portions
            filled_blocks = int(BAR_WIDTH * percent / 100)
            empty_blocks = BAR_WIDTH - filled_blocks
            
            # Choose color based on completion
            if percent >= 100:
                color = ANSIColors.CHLOROS_GREEN
            elif percent > 0:
                color = ANSIColors.BRIGHT_WHITE
            else:
                color = ANSIColors.DIM
            
            # Build the bar
            bar_filled = PROGRESS_BAR_FILLED * filled_blocks
            bar_empty = PROGRESS_BAR_EMPTY * empty_blocks
            
            # Format the line
            percent_str = f"{int(percent):3d}%"
            line = f"  {name:12s} │{color}{bar_filled}{ANSIColors.DIM}{bar_empty}{ANSIColors.RESET}│ {color}{percent_str}{ANSIColors.RESET}"
            
            # Clear the entire line first, then print the new content
            print(f"\033[2K{line}", flush=True)  # \033[2K clears the entire line
    
    def _build_config(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert CLI settings to Chloros configuration format
        
        Args:
            settings: Dictionary of settings from CLI arguments
            
        Returns:
            Chloros configuration dictionary
        """
        config = {"Project Settings": {}}
        
        # Target Detection settings
        target_detection = {}
        
        if 'min_target_size' in settings and settings['min_target_size'] is not None:
            target_detection["Minimum calibration sample area (px)"] = settings['min_target_size']
        
        if 'target_clustering' in settings and settings['target_clustering'] is not None:
            target_detection["Minimum Target Clustering (0-100)"] = settings['target_clustering']
        
        if target_detection:
            config["Project Settings"]["Target Detection"] = target_detection
        
        # Processing settings
        processing = {}
        
        if 'debayer_method' in settings:
            processing["Debayer method"] = settings['debayer_method']
        
        if 'vignette_correction' in settings:
            processing["Vignette correction"] = settings['vignette_correction']
        
        if 'reflectance_calibration' in settings:
            processing["Reflectance calibration / white balance"] = settings['reflectance_calibration']
        
        if 'ppk_corrections' in settings:
            processing["Apply PPK corrections"] = settings['ppk_corrections']
        
        if 'exposure_pin_1' in settings and settings['exposure_pin_1']:
            processing["Exposure Pin 1"] = settings['exposure_pin_1']
        
        if 'exposure_pin_2' in settings and settings['exposure_pin_2']:
            processing["Exposure Pin 2"] = settings['exposure_pin_2']
        
        if 'recal_interval' in settings and settings['recal_interval'] is not None:
            processing["Minimum recalibration interval"] = settings['recal_interval']
        
        if 'timezone_offset' in settings and settings['timezone_offset'] is not None:
            processing["Light sensor timezone offset"] = settings['timezone_offset']
        
        if processing:
            config["Project Settings"]["Processing"] = processing
        
        # Export settings
        if 'export_format' in settings:
            config["Project Settings"]["Export"] = {
                "Calibrated image format": settings['export_format']
            }
        
        # Index settings
        if 'indices' in settings and settings['indices']:
            # Get available indices from backend
            try:
                response = requests.get(f'{self.api_url}/api/get-config', timeout=5)
                if response.ok:
                    current_config = response.json()
                    available_indices = current_config.get('Project Settings', {}).get('Index', {}).get('Add index', [])
                    
                    # Enable requested indices
                    enabled_indices = []
                    for idx in available_indices:
                        if isinstance(idx, dict):
                            idx_copy = idx.copy()
                            idx_copy['enabled'] = idx_copy.get('name', '').upper() in [i.upper() for i in settings['indices']]
                            enabled_indices.append(idx_copy)
                    
                    if enabled_indices:
                        config["Project Settings"]["Index"] = {
                            "Add index": enabled_indices
                        }
            except:
                # If we can't get current config, just log warning
                self._print_warning(i18n.t('could_not_configure_indices'))
        
        return config
    
    def _monitor_progress(self) -> bool:
        """
        Monitor processing progress via Server-Sent Events (SSE)
        
        Returns:
            True if processing completed successfully, False on error
        """
        import signal
        import sys
        import time
        
        # Flag to handle graceful shutdown
        interrupted = [False]
        
        def signal_handler(sig, frame):
            """Handle Ctrl+C gracefully"""
            interrupted[0] = True
            print("\n\n⚠ Interrupted by user (Ctrl+C)", flush=True)
            print("  Stopping monitoring...", flush=True)
        
        # Register signal handler for Ctrl+C
        signal.signal(signal.SIGINT, signal_handler)
        
        try:
            # Connect to SSE endpoint (long timeout for processing)
            response = requests.get(f'{self.api_url}/api/events', stream=True, timeout=3600)
            
            # Track last event time to detect dead connections
            last_event_time = time.time()
            no_event_timeout = 60  # 60 seconds with no events = backend is dead
            
            if not response.ok:
                self._print_error(i18n.t('failed_connect_backend', error=response.status_code))
                return False
            
            # Only show SSE connection in verbose mode
            self._print_verbose("Connected to backend SSE stream")
            
            # Process events
            last_percent = 0.0
            event_type = None  # Initialize event_type
            processing_complete = [False]  # Track if processing completed successfully
            
            # Thread 4 (export) progress tracking
            thread_4_percent = 0
            thread_4_last_print_time = 0
            thread_4_ever_active = False  # Track if Thread 4 has ever been active
            
            # Track which threads have started (for non-verbose mode feedback)
            threads_started = {1: False, 2: False, 3: False, 4: False}
            
            # Track last printed percentage for each thread (for 10% interval printing)
            thread_last_printed_percent = {1: -10, 2: -10, 3: -10, 4: -10}
            
            # Track thread states for progress bar display
            thread_states = {
                1: {'name': 'Detecting', 'percent': 0},
                2: {'name': 'Analyzing', 'percent': 0},
                3: {'name': 'Processing', 'percent': 0},
                4: {'name': 'Exporting', 'percent': 0}
            }
            
            # Track heartbeat for non-verbose mode
            last_heartbeat_print = time.time()
            heartbeat_count = 0
            lines_received = 0  # Track total lines received for debugging
            
            # Print immediately to show we're in the loop
            if not self.verbose:
                print("  Receiving events from backend...", flush=True)
                sys.stdout.flush()
            
            for line in response.iter_lines(decode_unicode=False):
                # Check if user interrupted with Ctrl+C
                if interrupted[0]:
                    print("  Monitoring stopped by user.", flush=True)
                    return False
                
                lines_received += 1
                
                # Show activity indicator in non-verbose mode (every 50 lines)
                if not self.verbose and lines_received % 50 == 1:
                    print(".", end="", flush=True)
                    sys.stdout.flush()
                
                # Check for timeout (no events received for too long)
                current_time = time.time()
                if current_time - last_event_time > no_event_timeout:
                    self._print_error(f"\n⚠ Backend connection lost (no events for 60s)")
                    self._print_error(f"  Lines received: {lines_received}")
                    self._print_error("The backend may have crashed. Please check the logs.")
                    return False
                
                if not line:
                    continue
                
                # Update last event time
                last_event_time = current_time
                
                try:
                    line = line.decode('utf-8', errors='replace')
                except Exception as e:
                    self._print_verbose(f"[SSE] Decode error: {e}")
                    continue
                
                self._print_verbose(f"[SSE] Received: {line[:100]}")  # Show first 100 chars
                
                # Parse SSE format: "data: {json containing type field}\n\n"
                if line.startswith('data:'):
                    try:
                        event_data = json.loads(line.split(':', 1)[1].strip())
                        event_type = event_data.get('type', 'unknown')
                        
                        self._print_verbose(f"[SSE] Event type: {event_type}")
                        
                        # Handle different event types
                        if event_type == 'progress':
                            data_obj = event_data.get('data', event_data)  # Try data field first, fallback to root
                            percent = data_obj.get('percent', 0)
                            message = data_obj.get('message', '')
                            
                            self._print_verbose(f"[PROGRESS] {percent}% - {message}")
                            
                            # Only update if progress changed significantly (reduces flicker)
                            if abs(percent - last_percent) >= 0.1 or message:
                                self._print_progress(percent, message)
                                last_percent = percent
                        
                        elif event_type == 'processing-progress':
                            # Extract thread progress from parallel processing events
                            data_obj = event_data.get('data', {})
                            processing_type = data_obj.get('type', 'unknown')
                            
                            # Handle serial mode completion
                            if processing_type == 'serial':
                                percent = data_obj.get('percentComplete', 0)
                                phase_name = data_obj.get('phaseName', 'Processing')
                                
                                self._print_verbose(f"[SERIAL] {phase_name}: {percent}%")
                                
                                # Check if serial processing is complete
                                if percent >= 100:
                                    self._print_verbose("[SSE] Serial processing complete (100%)")
                                    processing_complete[0] = True
                                    print()  # New line after progress bar
                                    return True
                            
                            # Handle parallel mode progress
                            elif processing_type == 'parallel':
                                thread_progress = data_obj.get('threadProgress', [])
                                
                                # Thread descriptions
                                thread_names = {
                                    1: "Detecting",
                                    2: "Analyzing", 
                                    3: "Processing",
                                    4: "Exporting"
                                }
                                
                                # Update thread states and draw progress bars
                                for thread in thread_progress:
                                    thread_id = thread.get('id')
                                    thread_name = thread_names.get(thread_id, f"Thread {thread_id}")
                                    new_percent = thread.get('percentComplete', 0)
                                    
                                    # Update thread state
                                    thread_states[thread_id]['percent'] = new_percent
                                    
                                    # Track if threads have started
                                    if not threads_started[thread_id] and new_percent > 0:
                                        threads_started[thread_id] = True
                                        self._print_verbose(f"[{thread_name}] Started")
                                    
                                    # Track Thread 4 completion for final message
                                    if thread_id == 4:
                                        if new_percent > 0:
                                            thread_4_ever_active = True
                                        thread_4_percent = new_percent
                                        
                                        # CRITICAL: If Thread-4 reaches 100%, processing is complete
                                        if thread_4_percent >= 100:
                                            self._print_verbose("[SSE] Thread-4 export reached 100%, marking complete")
                                            processing_complete[0] = True
                                            # Draw final state
                                            self._draw_progress_bars(thread_states)
                                            sys.stdout.flush()
                                            return True
                                    
                                    # Verbose logging for completion
                                    if new_percent >= 100:
                                        self._print_verbose(f"[{thread_name}] Completed")
                                
                                # Draw the progress bars (update display)
                                self._draw_progress_bars(thread_states)
                        
                        elif event_type == 'processing-complete':
                            self._print_verbose("[SSE] Processing complete event received")
                            processing_complete[0] = True  # Mark as completed
                            # Print completion if not already printed by Thread-4
                            if not thread_4_ever_active:
                                print(f"\n{Icons.SUCCESS} Processing complete!")
                                sys.stdout.flush()
                            return True
                        
                        elif event_type == 'error' or event_type == 'processing-error':
                            self._print_verbose(f"[SSE] Error event: {event_data}")
                            data_obj = event_data.get('data', {})
                            error_msg = data_obj.get('error', data_obj.get('message', 'Unknown error'))
                            
                            # Ignore [Errno 22] errors if processing already completed
                            if processing_complete[0] and ("[Errno 22]" in error_msg or "Invalid argument" in error_msg):
                                self._print_verbose(f"[SSE] Ignoring post-completion error: {error_msg}")
                                continue
                            
                            print()  # New line after progress bar
                            self._print_error(i18n.t('processing_error', error=error_msg))
                            return False
                        
                        elif event_type == 'thread-start':
                            data_obj = event_data.get('data', {})
                            thread_name = data_obj.get('thread_name', 'Thread')
                            self._print_verbose(i18n.t('thread_started', name=thread_name))
                        
                        elif event_type == 'thread-complete':
                            data_obj = event_data.get('data', {})
                            thread_name = data_obj.get('thread_name', 'Thread')
                            self._print_verbose(i18n.t('thread_completed', name=thread_name))
                        
                        elif event_type == 'heartbeat' or event_type == 'connected' or event_type == 'backend-ready' or event_type == 'backend-status':
                            # Show heartbeat indicator in non-verbose mode (every 3 heartbeats = ~6 seconds)
                            if event_type == 'heartbeat':
                                heartbeat_count += 1
                            
                            if not self.verbose and heartbeat_count > 0 and heartbeat_count % 3 == 0:
                                current_time = time.time()
                                if current_time - last_heartbeat_print >= 5:  # At least 5 seconds between prints
                                    print(".", end="", flush=True)
                                    sys.stdout.flush()
                                    last_heartbeat_print = current_time
                        
                    except json.JSONDecodeError as e:
                        self._print_verbose(f"[SSE] JSON decode error: {e} - Line: {line[:100]}")
                        continue
                    except Exception as e:
                        self._print_verbose(f"[SSE] Error processing event: {e}")
                        continue
            
            # If we exit the loop without seeing processing-complete, something went wrong
            print()  # New line after progress bar
            self._print_error(i18n.t('event_stream_ended'))
            return False
            
        except requests.exceptions.Timeout:
            print()  # New line after progress bar
            self._print_error(i18n.t('processing_timeout'))
            return False
        except requests.exceptions.RequestException as e:
            print()  # New line after progress bar
            # Ignore "Invalid argument" errors after processing completes - connection closing
            if "[Errno 22]" in str(e) and processing_complete[0]:
                self._print_verbose(f"[SSE] Connection closed after completion: {e}")
                return True
            self._print_error(i18n.t('connection_error', error=e))
            return False
        except OSError as e:
            # Handle OS errors like [Errno 22] Invalid argument when connection closes
            if "[Errno 22]" in str(e) or "Invalid argument" in str(e):
                self._print_verbose(f"[SSE] OS error (likely connection closing): {e}")
                # If processing completed, treat this as success
                if processing_complete[0]:
                    return True
            print()  # New line after progress bar
            self._print_error(i18n.t('connection_error', error=e))
            return False
        except KeyboardInterrupt:
            print()  # New line after progress bar
            self._print_warning(f"\n{i18n.t('processing_interrupted')}")
            # Try to stop processing
            try:
                requests.post(f'{self.api_url}/api/interrupt-project', timeout=5)
            except:
                pass
            return False


class CapitalizedHelpFormatter(argparse.RawDescriptionHelpFormatter):
    """Custom formatter that capitalizes section headers and widens argument column"""
    def __init__(self, prog, indent_increment=2, max_help_position=35, width=None):
        super().__init__(prog, indent_increment, max_help_position, width)
    
    def add_usage(self, usage, actions, groups, prefix=None):
        if prefix is None:
            prefix = 'Usage: '
        return super().add_usage(usage, actions, groups, prefix)
    
    def start_section(self, heading):
        if heading:
            # Capitalize standard argparse section headers
            if heading == 'positional arguments':
                heading = 'Positional Arguments'
            elif heading == 'options':
                heading = 'Options'
            elif heading == 'optional arguments':
                heading = 'Optional Arguments'
        return super().start_section(heading)


def main():
    """Main entry point for CLI"""
    
    # Handle --banner flag early (before argparse validation)
    if '--banner' in sys.argv:
        if USE_FANCY_STYLES:
            print_header(get_cli_title(), version=__version__)
        sys.exit(0)
    
    # Print beautiful header if fancy styles available
    if USE_FANCY_STYLES:
        print_header(get_cli_title(), version=__version__)
    
    parser = argparse.ArgumentParser(
        prog='chloros-cli',
        description=get_cli_title(),
        formatter_class=CapitalizedHelpFormatter,
        epilog=f'''
{t('target_detection_header')}
  --min-target-size PIXELS
      {t('arg_min_target_size')}
  
  --target-clustering 0-100
      {t('arg_target_clustering')}

{t('processing_options_header')}
  --vignette / --no-vignette
      {t('arg_vignette')}
  
  --reflectance / --no-reflectance
      {t('arg_reflectance')}
  
  --ppk
      {t('arg_ppk')}
  
  --exposure-pin-1 CAMERA_MODEL
      {t('arg_exposure_pin_1')}
  
  --exposure-pin-2 CAMERA_MODEL
      {t('arg_exposure_pin_2')}
  
  --recal-interval SECONDS
      {t('arg_recal_interval')}
  
  --timezone-offset HOURS
      {t('arg_timezone_offset')}

{t('export_options_header')}
  --format {{TIFF (16-bit)|TIFF (32-bit, Percent)|PNG (8-bit)|JPG (8-bit)}}
      {t('arg_format')}

{t('examples_header')}
  {t('example_1')}
  chloros-cli process "C:/images/survey_001"
  
  {t('example_2')}
  chloros-cli process "C:/images/survey_001" \\
    --vignette \\
    --reflectance
  
  {t('example_4')}
  chloros-cli process "C:/input" -o "C:/output"
  
  Check export progress during processing:
  chloros-cli export-status
  
  Login with your Chloros+ account:
  chloros-cli login user@example.com 'password123'
  
  Check license status:
  chloros-cli status
  
  Logout and clear credentials:
  chloros-cli logout
  
  {t('example_5')}
  chloros-cli language es
  
  {t('example_6')}
  chloros-cli language --list

{t('more_info')}
        '''
    )
    
    # Global options
    parser.add_argument('--backend-exe', help=i18n.t('arg_backend_exe'))
    parser.add_argument('--port', type=int, default=5000, help=i18n.t('arg_port'))
    parser.add_argument('-v', '--verbose', action='store_true', help=i18n.t('arg_verbose'))
    parser.add_argument('--restart', action='store_true', help='Force restart backend (kills existing backend_server.py processes)')
    parser.add_argument('--version', action='version', version=f'Chloros CLI {__version__}')
    parser.add_argument('--banner', action='store_true', help=argparse.SUPPRESS)  # Hidden flag to show header only
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', required=True, help='Available commands')
    
    # Process command
    process_parser = subparsers.add_parser(
        'process',
        help=i18n.t('cmd_process'),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    process_parser.add_argument(
        'input',
        help=i18n.t('arg_input')
    )
    
    process_parser.add_argument(
        '-o', '--output',
        help=i18n.t('arg_output')
    )
    
    process_parser.add_argument(
        '-n', '--project-name',
        metavar='NAME',
        help='Name for the project (default: auto-generated with timestamp)'
    )
    
    # Target Detection settings
    process_parser.add_argument(
        '--min-target-size',
        type=int,
        metavar='PIXELS',
        help=i18n.t('arg_min_target_size')
    )
    
    process_parser.add_argument(
        '--target-clustering',
        type=int,
        metavar='0-100',
        help=i18n.t('arg_target_clustering')
    )
    
    # Processing settings
    # Note: Debayer is always "High Quality (Faster)" (Edge-Aware algorithm)
    # This is the only method currently implemented and used by the backend
    
    process_parser.add_argument(
        '--vignette',
        action='store_true',
        default=True,
        help=i18n.t('arg_vignette')
    )
    
    process_parser.add_argument(
        '--no-vignette',
        action='store_false',
        dest='vignette',
        help=i18n.t('arg_no_vignette')
    )
    
    process_parser.add_argument(
        '--reflectance',
        action='store_true',
        default=True,
        help=i18n.t('arg_reflectance')
    )
    
    process_parser.add_argument(
        '--no-reflectance',
        action='store_false',
        dest='reflectance',
        help=i18n.t('arg_no_reflectance')
    )
    
    process_parser.add_argument(
        '--ppk',
        action='store_true',
        help=i18n.t('arg_ppk')
    )
    
    process_parser.add_argument(
        '--exposure-pin-1',
        metavar='CAMERA_MODEL',
        help=i18n.t('arg_exposure_pin_1')
    )
    
    process_parser.add_argument(
        '--exposure-pin-2',
        metavar='CAMERA_MODEL',
        help=i18n.t('arg_exposure_pin_2')
    )
    
    process_parser.add_argument(
        '--recal-interval',
        type=int,
        metavar='SECONDS',
        help=i18n.t('arg_recal_interval')
    )
    
    process_parser.add_argument(
        '--timezone-offset',
        type=int,
        metavar='HOURS',
        help=i18n.t('arg_timezone_offset')
    )
    
    process_parser.add_argument(
        '--format',
        choices=['TIFF (16-bit)', 'TIFF (32-bit, Percent)', 'PNG (8-bit)', 'JPG (8-bit)'],
        default='TIFF (16-bit)',
        help=i18n.t('arg_format')
    )
    
    process_parser.add_argument(
        '--indices',
        nargs='*',
        metavar='INDEX',
        help=i18n.t('arg_indices')
    )
    
    # Language command
    language_parser = subparsers.add_parser(
        'language',
        help=i18n.t('cmd_language'),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    language_parser.add_argument(
        'lang_code',
        nargs='?',
        help=i18n.t('cmd_set_language')
    )
    
    language_parser.add_argument(
        '--list',
        action='store_true',
        help=i18n.t('cmd_list_languages')
    )
    
    # Login command
    login_parser = subparsers.add_parser(
        'login',
        help='Authenticate with Chloros cloud account',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    login_parser.add_argument(
        'email',
        help='Your Chloros account email'
    )
    
    login_parser.add_argument(
        'password',
        help='Your Chloros account password (use SINGLE quotes for passwords with $: \'password$$\')'
    )
    
    # Logout command
    logout_parser = subparsers.add_parser(
        'logout',
        help='Logout and clear stored credentials'
    )
    
    # Status command  
    status_parser = subparsers.add_parser(
        'status',
        help='Show current license and authentication status'
    )
    
    # Export status command
    export_status_parser = subparsers.add_parser(
        'export-status',
        help='Check Thread 4 export progress (can be called during processing)'
    )
    
    # Project folder commands
    set_folder_parser = subparsers.add_parser(
        'set-project-folder',
        help='Set the default project folder location (shared with GUI)',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    set_folder_parser.add_argument(
        'folder',
        help='Path to the new project folder'
    )
    
    get_folder_parser = subparsers.add_parser(
        'get-project-folder',
        help='Show the current default project folder location'
    )
    
    reset_folder_parser = subparsers.add_parser(
        'reset-project-folder',
        help='Reset to default project folder'
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # CRITICAL FIX: Force verbose mode internally for 'process' command
    # (Verbose mode uses a different SSE handling that prevents hangs)
    # But suppress verbose output for clean display
    suppress_verbose_output = False
    if args.command == 'process' and not args.verbose:
        args.verbose = True  # Enable internally for SSE stability
        suppress_verbose_output = True  # But suppress verbose prints
    
    # Create CLI instance
    cli = ChlorosCLI(
        backend_exe=args.backend_exe,
        port=args.port,
        verbose=args.verbose
    )
    
    # Apply output suppression for clean display
    if suppress_verbose_output:
        cli.suppress_verbose_output = True
    
    try:
        # Handle commands that don't need backend startup
        # Project folder commands
        if args.command == 'set-project-folder':
            success = cli.set_project_folder(args.folder)
            sys.exit(0 if success else 1)
        
        elif args.command == 'get-project-folder':
            success = cli.get_project_folder()
            sys.exit(0 if success else 1)
        
        elif args.command == 'reset-project-folder':
            success = cli.reset_project_folder()
            sys.exit(0 if success else 1)
        
        # Language command
        elif args.command == 'language':
            if args.list:
                # List all languages
                print(f"\n{i18n.t('available_languages')}\n")
                print(f"{'Code':<10} {'Language':<30} {'Native Name':<30} {'Current':<10}")
                print("-" * 80)
                for lang_info in i18n.list_languages():
                    current = Icons.SUCCESS if lang_info['current'] else ""
                    print(f"{lang_info['code']:<10} {lang_info['name']:<30} {lang_info['nativeName']:<30} {current:<10}")
                print()
                sys.exit(0)
            elif args.lang_code:
                # Set language
                if i18n.set_language(args.lang_code):
                    # Use display name that works in current console
                    lang_name = get_display_language_name(args.lang_code)
                    print(f"{Icons.SUCCESS} Language set to: {lang_name}")
                    print(f"  Language preference saved")
                    sys.exit(0)
                else:
                    print(f"{Icons.ERROR} {i18n.t('invalid_language', code=args.lang_code)}")
                    print(f"\n{i18n.t('available_languages')}:")
                    for code in sorted(LANGUAGES.keys()):
                        print(f"  {code:<6} - {LANGUAGES[code]['name']} ({LANGUAGES[code]['nativeName']})")
                    sys.exit(1)
            else:
                # Show current language
                lang_code = i18n.get_language()
                lang_name = get_display_language_name(lang_code)
                print(f"Current language: {lang_name} [{lang_code}]")
                sys.exit(0)
        
        # Authentication and status commands (need backend to be running)
        if args.command in ['login', 'logout', 'status', 'export-status']:
            # Start backend for authentication (skip license check for login command)
            skip_check = (args.command == 'login')
            for_login = (args.command == 'login')
            if not cli.start_backend(skip_license_check=skip_check, for_login=for_login):
                sys.exit(1)
            
            # Execute authentication command
            if args.command == 'login':
                success = cli.login(args.email, args.password)
                sys.exit(0 if success else 1)
            
            elif args.command == 'logout':
                success = cli.logout()
                sys.exit(0 if success else 1)
            
            elif args.command == 'status':
                success = cli.get_license_status()
                sys.exit(0 if success else 1)
            
            elif args.command == 'export-status':
                success = cli.get_export_status()
                sys.exit(0 if success else 1)
        
        # For other commands, start backend
        # Use --restart flag to force fresh backend
        force_fresh = args.restart if hasattr(args, 'restart') else False
        
        # For process command, check if backend is stale
        # start_backend will automatically handle stale backends
        if not cli.start_backend(force_fresh=force_fresh):
            sys.exit(1)
        
        # Execute command
        if args.command == 'process':
            # Build settings from arguments
            settings = {
                # Target Detection
                'min_target_size': args.min_target_size if hasattr(args, 'min_target_size') else None,
                'target_clustering': args.target_clustering if hasattr(args, 'target_clustering') else None,
                # Processing
                'debayer_method': 'High Quality (Faster)',  # Only method available
                'vignette_correction': args.vignette,
                'reflectance_calibration': args.reflectance,
                'ppk_corrections': args.ppk if hasattr(args, 'ppk') else False,
                'exposure_pin_1': args.exposure_pin_1 if hasattr(args, 'exposure_pin_1') else None,
                'exposure_pin_2': args.exposure_pin_2 if hasattr(args, 'exposure_pin_2') else None,
                'recal_interval': args.recal_interval if hasattr(args, 'recal_interval') else None,
                'timezone_offset': args.timezone_offset if hasattr(args, 'timezone_offset') else None,
                'processing_mode': 'parallel',  # Chloros+ always uses parallel mode
                # Export
                'export_format': args.format,
                # Index
                'indices': args.indices or []
            }
            
            # Process images
            success = cli.process_images(
                args.input,
                args.output,
                project_name=args.project_name if hasattr(args, 'project_name') else None,
                **settings
            )
            
            sys.exit(0 if success else 1)
    
    except KeyboardInterrupt:
        print(f"\n\n{i18n.t('interrupted_short')}")
        sys.exit(130)  # Standard Unix exit code for Ctrl+C
    
    except Exception as e:
        if hasattr(cli, '_print_error'):
            cli._print_error(f"Unexpected error: {e}")
        else:
            print(f"ERROR: Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)
    
    finally:
        # Always stop backend on exit (if it was started)
        # Don't stop for language command (never starts backend)
        if args.command not in ['language']:
            cli.stop_backend()


if __name__ == '__main__':
    main()

