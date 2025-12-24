#!/usr/bin/env python3
"""
Chloros Browser Launcher
Starts the backend and opens the UI in a browser (app mode)
Works on low-GPU systems where Electron fails!

Usage:
  python chloros_browser_launcher.py              # Use compiled backend (production)
  python chloros_browser_launcher.py --dev        # Use Python source (development)
  python chloros_browser_launcher.py --source     # Use Python source (development)
"""

import subprocess
import time
import webbrowser
import socket
import os
import sys
import signal
import platform

# Configuration
BACKEND_PORT = 5000
BACKEND_URL = f"http://localhost:{BACKEND_PORT}/ui/"
STARTUP_TIMEOUT = 30  # seconds

backend_process = None

# Check if running in development mode (from source)
DEV_MODE = '--dev' in sys.argv or '--source' in sys.argv

# Auto-detect Chloros installation
def find_chloros_installation():
    """Find Chloros installation directory"""
    possible_locations = [
        r"C:\Program Files\MAPIR\Chloros",
        r"C:\Program Files (x86)\MAPIR\Chloros",
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Programs', 'Chloros'),
        os.path.join(os.environ.get('PROGRAMDATA', ''), 'MAPIR', 'Chloros'),
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'MAPIR', 'Chloros'),
    ]
    
    for location in possible_locations:
        backend_exe = os.path.join(location, 'resources', 'backend', 'chloros-backend.exe')
        if os.path.exists(backend_exe):
            return location, backend_exe
    
    return None, None

# Find installation at startup
INSTALL_DIR, BACKEND_EXE = find_chloros_installation()


def is_port_open(port, host='localhost'):
    """Check if a port is open (backend is running)"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            return result == 0
    except:
        return False


def kill_existing_backend():
    """Kill any existing backend processes"""
    if platform.system() == 'Windows':
        os.system('taskkill /F /IM chloros-backend.exe >nul 2>&1')
    else:
        os.system('pkill -f chloros-backend')


def start_backend():
    """Start the Chloros backend process"""
    global backend_process
    
    if DEV_MODE:
        print("🚀 Starting Chloros backend from Python source (DEV MODE)...")
        
        # Check if backend_server.py exists in current directory
        backend_source = os.path.join(os.getcwd(), 'backend_server.py')
        if not os.path.exists(backend_source):
            print(f"❌ ERROR: backend_server.py not found at: {backend_source}")
            print(f"   Current directory: {os.getcwd()}")
            input("Press Enter to exit...")
            sys.exit(1)
        
        # Start backend from source
        try:
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            env['PYTHONUTF8'] = '1'
            
            backend_process = subprocess.Popen(
                [sys.executable, 'backend_server.py'],
                stdout=None,  # Don't capture stdout - let it go to terminal AND log file
                stderr=None,  # Don't capture stderr - let it go to terminal AND log file
                cwd=os.getcwd(),
                env=env
            )
            print(f"✅ Backend process started from source (PID: {backend_process.pid})")
        except Exception as e:
            print(f"❌ ERROR starting backend: {e}")
            input("Press Enter to exit...")
            sys.exit(1)
    else:
        print("🚀 Starting Chloros backend (compiled)...")
        
        # Check if backend exe exists
        if not os.path.exists(BACKEND_EXE):
            print(f"❌ ERROR: Backend not found at: {BACKEND_EXE}")
            input("Press Enter to exit...")
            sys.exit(1)
        
        # Start backend as subprocess with environment variables
        try:
            # Set environment variables (keep instance protection enabled)
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            env['PYTHONUTF8'] = '1'
            
            backend_process = subprocess.Popen(
                [BACKEND_EXE],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.path.dirname(BACKEND_EXE),
                env=env
            )
            print(f"✅ Backend process started (PID: {backend_process.pid})")
        except Exception as e:
            print(f"❌ ERROR starting backend: {e}")
            input("Press Enter to exit...")
            sys.exit(1)
    
    # Wait for backend to be ready
    print(f"⏳ Waiting for backend to start (timeout: {STARTUP_TIMEOUT}s)...")
    
    for i in range(STARTUP_TIMEOUT):
        if is_port_open(BACKEND_PORT):
            print(f"✅ Backend is ready on port {BACKEND_PORT}!")
            return True
        
        # Check if process died
        if backend_process.poll() is not None:
            print("❌ ERROR: Backend process died unexpectedly")
            return False
        
        time.sleep(1)
        if (i + 1) % 5 == 0:
            print(f"   Still waiting... ({i + 1}s)")
    
    print("❌ ERROR: Backend failed to start within timeout")
    return False


def open_browser():
    """Open the UI in browser (app mode if possible)"""
    print(f"🌐 Opening Chloros in browser...")
    
    # Try to use Chrome/Edge in app mode (looks like desktop app)
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    ]
    
    edge_paths = [
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    ]
    
    # Try Chrome first
    for chrome_path in chrome_paths:
        if os.path.exists(chrome_path):
            print("✅ Opening in Chrome (app mode)...")
            subprocess.Popen([
                chrome_path,
                f"--app={BACKEND_URL}",
                "--window-size=1400,900",
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows"
            ])
            return True
    
    # Try Edge
    for edge_path in edge_paths:
        if os.path.exists(edge_path):
            print("✅ Opening in Edge (app mode)...")
            subprocess.Popen([
                edge_path,
                f"--app={BACKEND_URL}",
                "--window-size=1400,900",
                "--disable-background-timer-throttling"
            ])
            return True
    
    # Fallback to default browser
    print("✅ Opening in default browser...")
    webbrowser.open(BACKEND_URL)
    return True


def cleanup(signum=None, frame=None):
    """Cleanup: kill backend on exit"""
    global backend_process
    
    print("\n🧹 Cleaning up...")
    
    if backend_process:
        print("🛑 Stopping backend...")
        backend_process.terminate()
        try:
            backend_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            backend_process.kill()
    
    kill_existing_backend()
    print("✅ Cleanup complete")
    sys.exit(0)


def main():
    """Main launcher logic"""
    # Register cleanup handlers
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    
    print()
    print("=" * 60)
    print("  CHLOROS - Browser Launcher")
    print("  For Intel HD Graphics 620 and other low-GPU systems")
    if DEV_MODE:
        print("  MODE: Development (Python Source)")
    else:
        print("  MODE: Production (Compiled)")
    print("=" * 60)
    print()
    
    # In dev mode, skip installation check
    if DEV_MODE:
        print("Running in development mode - using Python source from current directory")
        print(f"Working directory: {os.getcwd()}")
        print()
    # Check if Chloros installation was found
    elif not INSTALL_DIR or not BACKEND_EXE:
        print("❌ ERROR: Cannot find Chloros installation")
        print()
        print("Searched locations:")
        print("  - C:\\Program Files\\MAPIR\\Chloros")
        print("  - C:\\Program Files (x86)\\MAPIR\\Chloros")
        print(f"  - {os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Programs', 'Chloros')}")
        print(f"  - {os.path.join(os.environ.get('PROGRAMDATA', ''), 'MAPIR', 'Chloros')}")
        print()
        print("Please ensure Chloros is installed.")
        print()
        input("Press Enter to exit...")
        sys.exit(1)
    
    if not DEV_MODE:
        print(f"Installation: {INSTALL_DIR}")
        print(f"Backend:      {BACKEND_EXE}")
        print()
    
    # Check if backend is already running
    if is_port_open(BACKEND_PORT):
        print("⚠️  Backend already running on port 5000, opening browser...")
        open_browser()
        print()
        print("✅ Chloros is now open in your browser!")
        print("   Close the browser tab when you're done.")
        print()
        input("Press Enter to exit launcher...")
        return
    
    # No backend on port 5000, so clean up any zombie processes
    print("No backend detected on port 5000, cleaning up zombie processes...")
    kill_existing_backend()
    time.sleep(3)  # Give more time for cleanup
    
    # Start backend
    if not start_backend():
        input("Press Enter to exit...")
        sys.exit(1)
    
    # Open browser
    if not open_browser():
        print("⚠️  Could not open browser automatically")
        print(f"   Please open: {BACKEND_URL}")
    
    print()
    print("=" * 60)
    print("✅ Chloros is now running in your browser!")
    print("=" * 60)
    print()
    print("  ℹ️  Keep this window open while using Chloros")
    print(f"  🌐 URL: {BACKEND_URL}")
    print("  🛑 Press Ctrl+C to stop")
    print()
    
    # Keep running until user stops
    try:
        while True:
            # Check if backend is still alive
            if backend_process.poll() is not None:
                print("❌ Backend process died unexpectedly!")
                break
            
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    
    cleanup()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        input("Press Enter to exit...")
        sys.exit(1)

