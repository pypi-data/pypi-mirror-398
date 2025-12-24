#!/usr/bin/env python3
"""
Chloros Backend Server for Electron
Provides API endpoints without pywebview
"""

# CRITICAL: Print IMMEDIATELY before any imports to verify executable starts
import sys
import os

# Suppress all deprecation warnings and Ray's SIGTERM warnings globally
import warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', message='.*SIGTERM.*')
warnings.filterwarnings('ignore', message='.*signal.*main thread.*')
os.environ['PYTHONWARNINGS'] = 'ignore::DeprecationWarning'

# Suppress Ray's verbose logging and SIGTERM messages
os.environ['RAY_DISABLE_IMPORT_WARNING'] = '1'
os.environ['RAY_LOG_TO_STDERR'] = '0'
os.environ['RAY_DEDUP_LOGS'] = '0'

# Suppress Ray's signal handler warning by setting logging level
import logging
logging.getLogger('ray').setLevel(logging.ERROR)
logging.getLogger('ray.tune').setLevel(logging.ERROR)
logging.getLogger('ray.rllib').setLevel(logging.ERROR)
logging.getLogger('ray.train').setLevel(logging.ERROR)
logging.getLogger('ray.serve').setLevel(logging.ERROR)

# CRITICAL: Set up file logging FIRST for compiled EXE (no console output)
import logging
import datetime
log_dir = os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'Chloros', 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f'backend_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.log')

# CRITICAL: Redirect stdout to also write to log file BEFORE setting up logging
class StdoutTee:
    """Redirect stdout to both console and log file - thread-safe"""
    def __init__(self, log_file_path):
        import threading
        self.terminal = sys.__stdout__  # Keep reference to original stdout
        self.log_file_path = log_file_path
        self.lock = threading.Lock()  # Thread-safe writes
        try:
            # Use write mode to truncate, then switch to append mode
            # This ensures we start with a fresh log for each session
            with open(log_file_path, 'w', encoding='utf-8') as f:
                pass  # Create/truncate file
            
            # Now open in append mode with line buffering
            self.log = open(log_file_path, 'a', encoding='utf-8', buffering=1)
            self.log_enabled = True
            # Log file opened silently
            self.log.flush()
        except Exception as e:
            self.log_enabled = False
            self.terminal.write(f"[LOG-INIT] ERROR: Failed to open log file: {e}\n")
            self.terminal.flush()
    
    def write(self, message):
        # Write to terminal (always)
        try:
            self.terminal.write(message)
            self.terminal.flush()
        except Exception as e:
            pass  # Can't do anything if terminal fails
        
        # Write to log file (if enabled) - with thread safety
        if self.log_enabled:
            try:
                with self.lock:
                    self.log.write(message)
                    self.log.flush()
                    # Force OS sync for important messages
                    if any(keyword in message for keyword in ['[DETECTING]', '[ANALYZING]', '[CALIBRATING]', '[EXPORTING]']):
                        try:
                            import os
                            os.fsync(self.log.fileno())
                        except:
                            pass
            except Exception as e:
                # Disable logging if it fails
                self.log_enabled = False
    
    def flush(self):
        try:
            self.terminal.flush()
        except:
            pass
        
        if self.log_enabled:
            with self.lock:
                try:
                    self.log.flush()
                except:
                    pass

# Redirect stdout to write to both console and log file
sys.stdout = StdoutTee(log_file)
# Also redirect stderr to the same log file
sys.stderr = StdoutTee(log_file)

# Startup banner suppressed for clean logs in Electron mode

# Now set up logging - it will use the redirected stdout
logging.basicConfig(
    level=logging.ERROR,  # Only show errors, suppress warnings and info
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger('chloros_backend')

# Startup logging
logger.info("============================================")
logger.info(f"Backend log file: {log_file}")
logger.info("============================================")
logger.info(f"Python: {sys.version}")
logger.info(f"Platform: {sys.platform}")
logger.info(f"Working Directory: {os.getcwd()}")
logger.info(f"Script Path: {os.path.abspath(__file__)}")

# Check for safe mode / debug flags
safe_mode = os.environ.get('CHLOROS_SAFE_MODE', '').lower() in ('1', 'true', 'yes')
if safe_mode:
    print("⚠️ SAFE MODE ENABLED", flush=True)

sys.stdout.flush()

# CRITICAL: Configure Ray for Nuitka compatibility FIRST
# This must be the VERY FIRST thing we do
try:
    from nuitka_ray_compatibility_fix import configure_ray_for_nuitka
    ray_config = configure_ray_for_nuitka()
except Exception as e:
    print(f"❌ ERROR in Ray configuration: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.stdout.flush()

import os

# Ray configuration will be handled by ray_session_manager.py
# Environment variables set above for Nuitka compatibility
import time
import threading
import json
from flask import Flask, request, jsonify, send_file, Response, send_from_directory

# Suppress warnings for cleaner output
import warnings
warnings.filterwarnings('ignore', category=FutureWarning, module='pandas')
warnings.filterwarnings('ignore', message='.*PerformanceWarning.*')
warnings.filterwarnings('ignore', message='.*Adding/subtracting object-dtype.*')
warnings.filterwarnings('ignore', category=RuntimeWarning, message='overflow encountered')
warnings.filterwarnings('ignore', message='Dtype inference on a pandas object')

def safe_flush():
    """Safely flush stdout if it exists"""
    if sys.stdout is not None and hasattr(sys.stdout, 'flush'):
        try:
            sys.stdout.flush()
        except:
            pass

# Add the current directory to the Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Apply Unicode encoding patch before importing api.py
try:
    import unicode_patch
except Exception as e:
    # Non-critical failure
    pass

# Import the main API directly (not the simplified eel wrapper)
try:
    from api import API
except Exception as e:
    print(f"❌ CRITICAL ERROR: Failed to import API: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.stdout.flush()
    sys.exit(1)

# Import authentication middleware
# SECURITY: Authentication is MANDATORY in production - cannot be disabled
# BUT: Check environment BEFORE initializing to allow CLI login
import os
skip_auth_env = os.environ.get('CHLOROS_SKIP_AUTH', '').lower() in ('1', 'true', 'yes')
is_production = os.environ.get('CHLOROS_PRODUCTION', '').lower() in ('1', 'true', 'yes')

if skip_auth_env and is_production:
    print("❌ ERROR: Cannot disable authentication in production!")
    raise SecurityError("Authentication cannot be disabled in production")

try:
    if skip_auth_env and not is_production:
        AUTH_ENABLED = False
        auth_middleware = None
    else:
        from auth_middleware import get_auth_middleware
        auth_middleware = get_auth_middleware()
        AUTH_ENABLED = True
except ImportError as e:
    # SECURITY: In production, auth middleware must be available
    import os
    is_production = os.environ.get('CHLOROS_PRODUCTION', '').lower() in ('1', 'true', 'yes')
    
    if is_production:
        print(f"❌ ERROR: Authentication middleware required in production!")
        print(f"❌ ERROR: Import failed: {e}")
        raise SecurityError("Authentication middleware must be available in production")
    
    print(f"⚠️ WARNING: Running in development mode - authentication disabled")
    AUTH_ENABLED = False
    auth_middleware = None

class SecurityError(Exception):
    """Security-related error that should not be ignored"""
    pass

# SECURITY: Instance protection will be initialized in main() to avoid Ray worker conflicts
instance_protection = None

# Create API instance
try:
    api = API()
except Exception as e:
    print(f"❌ CRITICAL ERROR: Failed to create API instance: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.stdout.flush()
    sys.exit(1)

# Debug patch removed - file not found

app = Flask(__name__)

# Disable Flask/Werkzeug HTTP request logging for cleaner output
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)  # Only show errors
log.disabled = True  # Disable completely

# Disable Flask app logger for cleaner output
app.logger.disabled = True
app.logger.setLevel(logging.ERROR)

# Global event queue for Server-Sent Events
import queue

# Use a true global singleton that persists across all module imports
import builtins
if not hasattr(builtins, '_mapir_global_event_queue'):
    builtins._mapir_global_event_queue = queue.Queue()

    safe_flush()

def get_global_event_queue():
    """Get the true global singleton event queue instance across all threads and imports"""
    return builtins._mapir_global_event_queue

# Initialize the global queue
event_queue = get_global_event_queue()



def dispatch_event(event_type, data):
    """Dispatch an event to the frontend via Server-Sent Events"""
    try:
        # Always get the singleton queue to ensure thread safety
        queue_instance = get_global_event_queue()
        event_data = {
            'type': event_type,
            'data': data,
            'timestamp': time.time()
        }
        
        # CRITICAL FIX: Add debug logging for target-detected events
        if event_type == 'target-detected':
            # print(f"[SSE-DISPATCH] 🎯 Dispatching target-detected event: {data.get('filename')} -> {data.get('is_calibration_photo')}")
            safe_flush()
        
        # Debug logging for files-changed events
        if event_type == 'files-changed':
            pass  # Files changed event queued
        
        # Use non-blocking put to avoid blocking processing thread
        queue_instance.put(event_data, block=False)
        
        # CRITICAL FIX: Add queue size monitoring
        queue_size = queue_instance.qsize()
        if event_type == 'target-detected':
            # print(f"[SSE-DISPATCH] 🎯 Event queued successfully. Queue size: {queue_size}")
            safe_flush()

        # Force flush stdout to ensure immediate output
        safe_flush()
    except queue.Full:
        # print(f"[SSE-DISPATCH] ❌ Queue full! Failed to dispatch {event_type} event")
        safe_flush()
    except Exception as e:
        # print(f"[SSE-DISPATCH] ❌ Error dispatching {event_type} event: {e}")
        import traceback
        # print(f"[SSE-DISPATCH] ❌ Full traceback: {traceback.format_exc()}")
        safe_flush()

def process_files_with_progress(file_paths):
    """Process files with progress updates"""
    try:

        total_files = len(file_paths)
        
        # REMOVED: Initialize import event - Ray callback now handles all progress via SSE
        
        # REMOVED: All simulation steps - Ray callback now handles all progress via SSE
        
        # Actually call the real function


        result = api.add_files_to_project(file_paths)

        
        if result is None:

            result = []
        
        # REMOVED: Completion event - Ray callback now handles all progress via SSE
        

        return result
        
    except Exception as e:
        import traceback
        return {'success': False, 'error': str(e)}

# Simple CORS handling without flask_cors
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response



@app.route('/')
def health_check():
    """Health check endpoint for the launcher"""
    return "Chloros Backend Server is running"

# ========================================
# AUTHENTICATION ENDPOINTS
# ========================================

@app.route('/api/login', methods=['POST'])
def login():
    """
    User login endpoint with device registration check
    Validates credentials against MAPIR server and checks device limit
    """
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({
                'success': False,
                'error': 'Email and password required'
            }), 400
        
        # Use existing API login method
        result = api.remote_user_login(email, password)
        
        if result.get('success'):
            # Check device registration if auth middleware is enabled
            if AUTH_ENABLED and auth_middleware:
                user_data = result.get('user', {})
                token = user_data.get('token')
                
                # Validate device registration
                is_valid, validation_data = auth_middleware.validate_token_online(token, email)
                
                if is_valid:
                    result['device_registered'] = True
                else:
                    # Device validation failed - check if it's a device limit issue
                    error_code = validation_data.get('error_code')
                    
                    if error_code == 'DEVICE_LIMIT_EXCEEDED':
                        # CRITICAL: Reject login when device limit is exceeded
                        print(f"[LOGIN] ❌ Device limit exceeded - rejecting login")
                        return jsonify({
                            'success': False,
                            'error': validation_data.get('error', 'Device limit reached'),
                            'error_code': 'DEVICE_LIMIT_EXCEEDED',
                            'message': 'Device limit reached.',
                            'manage_url': validation_data.get('manage_url', 'https://dynamic.cloud.mapir.camera')
                        }), 403
                    else:
                        # Other validation errors - still reject but with different error
                        result['device_registered'] = False
                        result['error'] = validation_data.get('error', 'Device validation failed')
                        result['error_code'] = error_code
                        print(f"[LOGIN] ⚠️ Device validation failed: {validation_data.get('error', 'Unknown')}")
                        return jsonify(result), 403
            
            return jsonify(result)
        else:
            return jsonify(result), 401
            
    except Exception as e:
        import traceback
        print(f"[LOGIN] ❌ Login error: {e}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/license-status', methods=['GET'])
def get_license_status():
    """
    Get current license/authentication status for CLI
    
    Returns detailed user subscription and authentication info
    """
    try:
        # Check if user is logged in
        if not api.user_logged_in or not api.user_email:
            return jsonify({
                'authenticated': False,
                'message': 'Not logged in'
            }), 200
        
        # Get plan details
        plan_id = api.user_plan_id if hasattr(api, 'user_plan_id') else 0
        
        # Return license info
        return jsonify({
            'authenticated': True,
            'email': api.user_email,
            'plan_id': plan_id,
            'plan_name': api.user_subscription_level.capitalize() if hasattr(api, 'user_subscription_level') else 'Unknown',
            'expires': api.user_plan_expiration if hasattr(api, 'user_plan_expiration') else None,
            'subscription_level': api.user_subscription_level if hasattr(api, 'user_subscription_level') else 'standard'
        }), 200
        
    except Exception as e:
        print(f"[LICENSE-STATUS] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/ui')
@app.route('/ui/')
def serve_main_ui():
    """Serve the main UI"""
    return send_from_directory('ui', 'main.html')

@app.route('/ui/<path:filename>')
def serve_ui_files(filename):
    """Serve static UI files"""
    return send_from_directory('ui', filename)

@app.route('/node_modules/<path:filename>')
def serve_node_modules(filename):
    """Serve node_modules for browser mode"""
    # Try multiple possible locations for node_modules
    possible_paths = [
        # Development: node_modules in project root
        os.path.join(os.path.dirname(__file__), 'node_modules'),
        os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'node_modules')),
        # Installed: backend is in resources/backend, node_modules is in resources/app/node_modules
        os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app', 'node_modules')),
        # Also try relative to exe location
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'app', 'node_modules'),
    ]
    
    for node_modules_path in possible_paths:
        if os.path.exists(node_modules_path):
            try:
                return send_from_directory(node_modules_path, filename)
            except:
                continue
    
    # Log error for debugging
    print(f"[ERROR] Could not find node_modules. Tried: {possible_paths}")
    return "node_modules not found", 404

@app.route('/api/events')
def stream_events():
    """Server-Sent Events endpoint for real-time communication"""
    def generate():
        try:
            # Send initial connection confirmation
            initial_event = json.dumps({'type': 'connected', 'timestamp': time.time()})
            yield "data: {}\n\n".format(initial_event)
            
            # Send backend-ready event to show terminal/logs are available
            backend_ready = json.dumps({
                'type': 'backend-ready', 
                'data': {'status': 'ready', 'version': '5.2.1'},
                'timestamp': time.time()
            })
            yield "data: {}\n\n".format(backend_ready)
            
            # Send initial backend status
            status_event = json.dumps({
                'type': 'backend-status',
                'data': {'status': 'running', 'message': 'Backend server is ready'},
                'timestamp': time.time()
            })
            yield "data: {}\n\n".format(status_event)
            
            while True:
                try:
                    # Always get the singleton queue to ensure thread safety
                    queue_instance = get_global_event_queue()
                    
                    # Check queue size before attempting to get
                    queue_size = queue_instance.qsize()
                    if queue_size > 0:
                        # print(f"[SSE-STREAM] 📦 Queue has {queue_size} events waiting")
                        safe_flush()
                    
                    # Use much longer timeout to wait for processing events during long operations
                    event = queue_instance.get(timeout=2.0)  # 2 second timeout for processing events
                    
                    # CRITICAL FIX: Add debug logging for target-detected events
                    if event.get('type') == 'target-detected':
                        # print(f"[SSE-STREAM] 🎯 Processing target-detected event: {event.get('data', {}).get('filename')} -> {event.get('data', {}).get('is_calibration_photo')}")
                        safe_flush()
                    
                    # Debug logging for files-changed events
                    if event.get('type') == 'files-changed':
                        pass  # Sending files-changed event
                    
                    event_json = json.dumps(event)
                    # print(f"[SSE-STREAM] 📤 Sending event: {event.get('type', 'unknown')}")
                    safe_flush()
                    
                    # Send SSE formatted data with retry for critical events
                    sse_data = "data: {}\n\n".format(event_json)
                    
                    # For target-detected events, send multiple times to ensure delivery (no delays to avoid blocking)
                    if event.get('type') == 'target-detected':
                        # print(f"[SSE-STREAM] 🎯 CRITICAL EVENT - Sending target-detected with enhanced reliability")
                        # Send the event multiple times immediately (no blocking delays)
                        yield sse_data
                        yield sse_data  # Send again for reliability
                        yield sse_data  # Send third time for maximum reliability
                        safe_flush()
                        # print(f"[SSE-STREAM] 🎯 CRITICAL EVENT - Sent target-detected 3 times for {event.get('data', {}).get('filename')} -> {event.get('data', {}).get('is_calibration_photo')}")
                    else:
                        yield sse_data
                    
                    queue_instance.task_done()
                    
                except queue.Empty:
                    # Check if queue actually has items but we got Empty exception (race condition)
                    queue_size_after = queue_instance.qsize()
                    if queue_size_after > 0:
                        # print(f"[SSE-STREAM] ⚠️ Race condition detected: queue had {queue_size_after} items after Empty exception")
                        safe_flush()
                        continue  # Retry immediately instead of sending heartbeat
                    
                    # Send heartbeat to keep connection alive
                    heartbeat = json.dumps({'type': 'heartbeat', 'timestamp': time.time()})
                    yield "data: {}\n\n".format(heartbeat)
                except Exception as e:
                    # print(f"[SSE-STREAM] ❌ Stream error: {e}")
                    safe_flush()
                    # Send heartbeat to keep connection alive even during errors
                    try:
                        heartbeat = json.dumps({'type': 'heartbeat', 'timestamp': time.time()})
                        yield "data: {}\n\n".format(heartbeat)
                    except:
                        pass  # If we can't send heartbeat, connection is likely dead
                    continue
        except GeneratorExit:
            pass  # SSE client disconnected
        except Exception as e:
            pass  # SSE stream error
    
    response = Response(generate(), mimetype='text/event-stream')
    response.headers['Cache-Control'] = 'no-cache'
    # Note: 'Connection' is a hop-by-hop header managed by the WSGI server (Waitress)
    # and should not be set by the application per PEP 3333
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Cache-Control'
    return response

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get system status"""
    try:
        status_info = api.get_project_status()
        return jsonify({
            'success': True,
            'status': status_info
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/fetch-version-file', methods=['POST'])
def fetch_version_file():
    """Fetch version file from remote URL (bypasses CORS for browser mode)"""
    import urllib.request
    import ssl
    
    try:
        data = request.get_json() or {}
        url = data.get('url', '')
        
        if not url:
            return jsonify({'success': False, 'error': 'No URL provided'}), 400
        
        # Only allow Google Drive URLs for security
        if not url.startswith('https://drive.google.com/'):
            return jsonify({'success': False, 'error': 'Only Google Drive URLs are allowed'}), 400
        
        # Fetch the version file
        # Create SSL context that handles certificates properly
        ssl_context = ssl.create_default_context()
        
        req = urllib.request.Request(
            url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/plain,text/html,*/*',
            }
        )
        
        with urllib.request.urlopen(req, timeout=15, context=ssl_context) as response:
            version_text = response.read().decode('utf-8').strip()
            
            # Validate that it looks like a version string (e.g., "1.0.3" or "1.2.0")
            if not version_text or len(version_text) > 20:
                return jsonify({'success': False, 'error': 'Invalid version format'}), 400
            
            # Basic validation - should contain only digits, dots, and maybe letters
            import re
            if not re.match(r'^[\d.]+[a-zA-Z0-9.-]*$', version_text):
                return jsonify({'success': False, 'error': 'Invalid version format'}), 400
            
            return jsonify({
                'success': True,
                'data': version_text
            })
            
    except urllib.error.URLError as e:
        print(f"[API] Error fetching version file: {e}", flush=True)
        return jsonify({'success': False, 'error': f'Network error: {str(e)}'}), 500
    except Exception as e:
        print(f"[API] Error fetching version file: {e}", flush=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/shutdown', methods=['POST'])
def shutdown_backend():
    """Gracefully shutdown the backend server.
    Called by browser mode when page closes, or by CLI on exit.
    """
    import threading
    import os
    import signal
    
    print("[BACKEND] 🛑 Shutdown requested via API", flush=True)
    
    def delayed_shutdown():
        """Perform shutdown after response is sent"""
        import time
        time.sleep(0.5)  # Allow response to be sent
        print("[BACKEND] 🛑 Executing shutdown...", flush=True)
        
        # Clean up API resources
        try:
            if api:
                api.close()
                print("[BACKEND] ✅ API cleanup complete", flush=True)
        except Exception as e:
            print(f"[BACKEND] ⚠️ API cleanup error: {e}", flush=True)
        
        # Exit the process
        print("[BACKEND] 👋 Goodbye!", flush=True)
        os._exit(0)
    
    # Start shutdown in background thread so response can be sent
    shutdown_thread = threading.Thread(target=delayed_shutdown, daemon=True)
    shutdown_thread.start()
    
    return jsonify({
        'success': True,
        'message': 'Shutdown initiated'
    })

# Browser mode API endpoints
@app.route('/api/test', methods=['GET'])
def test_api():
    """Test endpoint to verify API is working"""
    print("[API-TEST] /api/test endpoint called!", flush=True)
    return jsonify({'status': 'ok', 'message': 'API routes are working!'})

@app.route('/api/processing-mode', methods=['GET'])
def get_processing_mode_api():
    """Get current processing mode (parallel/serial)"""
    try:
        mode_info = api.get_processing_mode()
        return jsonify(mode_info)
    except Exception as e:
        return jsonify({'mode': 'parallel', 'error': str(e)})

@app.route('/api/config', methods=['GET'])
def get_config_api():
    """Get application configuration (app-level config, not project config)"""
    try:
        # This is for app-level config, not project config
        # Project config is served via /api/get-config (defined later)
        return jsonify({})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/config', methods=['POST'])
def set_config_api():
    """Set application configuration"""
    try:
        data = request.get_json()
        if api.project and api.project.config:
            for key, value in data.items():
                setattr(api.project.config, key, value)
            api.project.save()
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'No project loaded'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/user', methods=['GET'])
def get_user_api():
    """Get current user information"""
    try:
        # Check if user is logged in via middleware
        if hasattr(api, 'current_user') and api.current_user:
            return jsonify({'email': api.current_user})
        # Try to get from license manager
        if hasattr(api, 'license_manager') and api.license_manager:
            email = api.license_manager.get_email()
            return jsonify({'email': email if email else None})
        return jsonify({'email': None})
    except Exception as e:
        return jsonify({'email': None, 'error': str(e)})

@app.route('/api/user/language', methods=['GET'])
def get_user_language_api():
    """Get user's language preference"""
    try:
        # Return default language for now
        return jsonify({'language': 'en'})
    except Exception as e:
        return jsonify({'language': 'en', 'error': str(e)})

@app.route('/api/project/status', methods=['GET'])
def get_project_status_api():
    """Get project load status"""
    try:
        project_loaded = api.project is not None
        status = {
            'project_loaded': project_loaded,
            'project_path': api.project.project_path if project_loaded else None,
            'file_count': len(api.project.data.get('files', {})) if project_loaded else 0
        }
        return jsonify(status)
    except Exception as e:
        return jsonify({'project_loaded': False, 'error': str(e)})

@app.route('/api/exposure-pin-info', methods=['GET'])
def get_exposure_pin_info_api():
    """Get exposure and pin information"""
    try:
        if api.project and api.project.data:
            return jsonify({
                'exposure_info': api.project.data.get('exposure_info', {}),
                'pin_info': api.project.data.get('pin_info', {})
            })
        return jsonify(None)
    except Exception as e:
        return jsonify(None)

@app.route('/api/camera-models', methods=['GET'])
def get_camera_models_api():
    """Get list of available camera models"""
    try:
        # Return list of camera models from project or default
        if api.project and api.project.data:
            files = api.project.data.get('files', {})
            models = set()
            for file_info in files.values():
                if isinstance(file_info, dict):
                    model = file_info.get('cameraModel', '')
                    if model:
                        models.add(model)
            return jsonify(list(models))
        return jsonify([])
    except Exception as e:
        return jsonify([])

@app.route('/api/working-directory', methods=['GET'])
def get_working_directory_api():
    """Get current working directory"""
    try:
        if api.project and api.project.project_path:
            return jsonify({'path': api.project.project_path})
        return jsonify({'path': os.getcwd()})
    except Exception as e:
        return jsonify({'path': os.getcwd()})

@app.route('/api/projects', methods=['GET'])
def get_projects_api():
    """Get list of project names (for duplicate checking)"""
    try:
        # Return just project names, not full objects
        # This is used by the UI to check for duplicate project names
        projects = []
        
        # Get the projects directory from the API
        # Projects are stored directly in the working directory, not in a "Projects" subdirectory
        if hasattr(api, 'get_working_directory'):
            projects_dir = api.get_working_directory()
        else:
            # Fallback to a common location
            projects_dir = os.path.join(os.path.expanduser('~'), 'Documents', 'MAPIR', 'Chloros Projects')
        
        # Scan for valid project directories (those with project.json)
        if os.path.exists(projects_dir):
            for item in os.listdir(projects_dir):
                item_path = os.path.join(projects_dir, item)
                if os.path.isdir(item_path):
                    # Check if it's a valid project (has project.json)
                    config_path = os.path.join(item_path, 'project.json')
                    if os.path.exists(config_path):
                        projects.append(item)  # Just the project name (directory basename)
        return jsonify(projects)
    except Exception as e:
        print(f"[API] Error in get_projects_api: {e}", flush=True)
        import traceback
        print(f"[API] Traceback: {traceback.format_exc()}", flush=True)
        return jsonify([])

@app.route('/api/project-templates', methods=['GET'])
def get_project_templates_api():
    """Get list of project templates"""
    try:
        # Return empty list for now, or check if api has templates
        templates = []
        if hasattr(api, 'get_project_templates'):
            templates = api.get_project_templates()
        return jsonify(templates)
    except Exception as e:
        print(f"[API] Error in get_project_templates_api: {e}", flush=True)
        return jsonify([])

@app.route('/api/new-project', methods=['POST'])
def new_project_api():
    """Create a new project"""
    try:
        data = request.get_json()
        # Handle both array args format and object format
        if isinstance(data, list):
            project_name = data[0] if len(data) > 0 else None
            template = data[1] if len(data) > 1 else None
        else:
            project_name = data.get('projectName') or data.get('name')
            template = data.get('template')

        if not project_name:
            return jsonify({'success': False, 'error': 'Project name is required'}), 400
        
        # Call the API's new_project method
        api.new_project(project_name, template)

        return jsonify({'success': True, 'message': f'Project "{project_name}" created'})
    except Exception as e:
        import traceback
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/open-project', methods=['POST'])
@app.route('/api/load-project', methods=['POST'])
def load_project():
    """Load/open a project"""
    try:
        data = request.get_json()
        # Handle both formats: {"project_path": ...} and direct project name
        project_path = data.get('project_path') if isinstance(data, dict) else data
        
        # If it's just a project name (not a full path), construct the full path
        if project_path and not os.path.isabs(project_path):
            if hasattr(api, 'get_working_directory'):
                working_dir = api.get_working_directory()
                project_path = os.path.join(working_dir, project_path)
        
        # The main API's open_project method returns a file list, not a success object
        files = api.open_project(project_path)
        actual_project_fp = api.project.fp if api.project else 'None'
        
        # Verify the path matches what was requested (silent check)
        # Path mismatch is logged internally if needed
        
        # CRITICAL: Dispatch files-changed event if project has files
        # This enables the process button when reopening projects with files
        if files and len(files) > 0:
            dispatch_event('files-changed', {'hasFiles': True})
            
            # FAILSAFE: Dispatch again after delay to ensure SSE client and components are ready
            import threading
            def delayed_dispatch():
                import time
                time.sleep(1.0)
                dispatch_event('files-changed', {'hasFiles': True})
            
            threading.Thread(target=delayed_dispatch, daemon=True).start()
        
        return jsonify({
            'success': True,
            'message': 'Project loaded successfully',
            'files': files,
            'project_info': {
                'path': project_path,
                'loaded_at': time.time()
            }
        })
    except Exception as e:
        print(f"❌ ERROR loading project: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/import-from-folder', methods=['POST'])
def import_from_folder():
    """Import images from a folder into the current project"""
    try:
        print("[IMPORT-FROM-FOLDER] Endpoint called", flush=True)
        data = request.get_json()
        folder_path = data.get('folder_path', '')
        recursive = data.get('recursive', False)
        
        print(f"[IMPORT-FROM-FOLDER] Folder path: {folder_path}", flush=True)
        print(f"[IMPORT-FROM-FOLDER] Recursive: {recursive}", flush=True)
        print(f"[IMPORT-FROM-FOLDER] Folder exists: {os.path.exists(folder_path)}", flush=True)
        
        if not api.project:
            return jsonify({
                'success': False,
                'error': 'No project loaded'
            }), 400
        
        # Import files from the folder
        api.process_folder(folder_path, recursive=recursive)
        
        # Get the updated file list
        files = list(api.project.data.get('files', {}).keys())
        print(f"[IMPORT-FROM-FOLDER] Imported {len(files)} files total", flush=True)
        
        # CRITICAL: Ensure project is saved after import for GUI compatibility
        if api.project and len(files) > 0:
            try:
                api.project.write()
                print(f"[IMPORT-FROM-FOLDER] Project saved with {len(files)} files", flush=True)
            except Exception as save_error:
                print(f"[IMPORT-FROM-FOLDER] Warning: Could not save project: {save_error}", flush=True)
        
        return jsonify({
            'success': True,
            'message': f'Imported {len(files)} files from folder',
            'files': files
        })
    except Exception as e:
        print(f"[IMPORT-FROM-FOLDER] Error: {e}", flush=True)
        import traceback
        print(f"[IMPORT-FROM-FOLDER] Traceback: {traceback.format_exc()}", flush=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/upload-files', methods=['POST'])
def upload_files():
    """Upload files from browser and add to project (browser mode fallback)"""
    try:
        if api.project is None:
            return jsonify({'success': False, 'error': 'No project loaded'}), 400
        
        if 'files' not in request.files:
            return jsonify({'success': False, 'error': 'No files uploaded'}), 400
        
        files = request.files.getlist('files')
        
        if not files:
            return jsonify({'success': False, 'error': 'No files uploaded'}), 400
        
        # Get the project's working directory or use temp
        working_dir = api.project.project_path if hasattr(api.project, 'project_path') else None
        if not working_dir:
            working_dir = api.project.data.get('working_directory', '')
        if not working_dir:
            import tempfile
            working_dir = tempfile.gettempdir()
        
        # Create uploads subdirectory
        upload_dir = os.path.join(working_dir, 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        
        saved_paths = []
        for file in files:
            if file.filename:
                # Secure the filename
                from werkzeug.utils import secure_filename
                filename = secure_filename(file.filename)
                # Preserve original extension case for RAW files
                if file.filename.lower().endswith(('.raw', '.daq', '.csv')):
                    filename = file.filename.replace('/', '_').replace('\\', '_')
                
                filepath = os.path.join(upload_dir, filename)
                file.save(filepath)
                saved_paths.append(filepath)
        
        if not saved_paths:
            return jsonify({'success': False, 'error': 'No files saved'}), 400
        
        # Now add the saved files to the project using existing logic
        try:
            result = process_files_with_progress(saved_paths)
            if result is None:
                result = []
        except Exception as e:
            result = []
        
        # Return the file list for the UI
        if isinstance(result, dict) and result.get('success') == False:
            return jsonify(result), 400
        return jsonify({
            'success': True,
            'files': result if result else []
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/add-files', methods=['POST'])
def add_files():
    """Add files to project"""
    try:
        # print("[PYTHON BACKEND] 🎯 /api/add-files endpoint called - NEW CODE!")
        # print(f"[PYTHON BACKEND] Request content type: {request.content_type}")
        # print(f"[PYTHON BACKEND] Request data: {request.get_data()}")
        
        data = request.get_json()
        # print(f"[PYTHON BACKEND] Parsed JSON data: {data}")
        
        if data is None:
            # print("[PYTHON BACKEND] ERROR: No JSON data received!")
            return jsonify({'success': False, 'error': 'No JSON data received'}), 400
            
        file_paths = data.get('file_paths', [])
        
        # print("[PYTHON BACKEND] Received add files request with {} files".format(len(file_paths)))
        # print(f"[PYTHON BACKEND] File paths: {file_paths}")
        # print("[PYTHON BACKEND] Current project loaded: {}".format(api.project is not None))
        
        if api.project is None:
            # print("[PYTHON BACKEND] ERROR: No project is loaded!")
            return jsonify({'success': False, 'error': 'No project loaded'}), 400
        
        if not file_paths:
            # print("[PYTHON BACKEND] ERROR: No file paths provided!")
            return jsonify({
                'success': False,
                'error': 'No file paths provided'
            }), 400
        
        # print("[PYTHON BACKEND] File paths to process: {}".format(file_paths))
        
        # Check if files actually exist
        for file_path in file_paths:
            import os
            exists = os.path.exists(file_path)
            # print("[PYTHON BACKEND] File exists {}: {}".format(exists, file_path))
        
        # REMOVED: Import animation - Ray callback now handles all progress via SSE
            

        
        # Check project state before adding files
        project_files_before = len(api.project.data.get('files', {})) if api.project else 0
        # print("[PYTHON BACKEND] Project files before: {}".format(project_files_before))
        
        try:
            result = process_files_with_progress(file_paths)
            # print("[PYTHON BACKEND] process_files_with_progress returned: {}".format(type(result)))
            if result is None:
                # print("[PYTHON BACKEND] WARNING: process_files_with_progress returned None, using empty list")
                result = []
        except Exception as e:
            # print("[PYTHON BACKEND] Exception in process_files_with_progress: {}".format(str(e)))
            import traceback
            # print("[PYTHON BACKEND] Traceback: {}".format(traceback.format_exc()))
            result = []
        
        # Check project state after adding files
        project_files_after = len(api.project.data.get('files', {})) if api.project else 0
        # print("[PYTHON BACKEND] Project files after: {}".format(project_files_after))
        
        # print("[PYTHON BACKEND] Add files result type: {}".format(type(result)))
        # print("[PYTHON BACKEND] Add files result length: {}".format(len(result) if result else 0))
        if result:
            # print("[PYTHON BACKEND] First result item: {}".format(result[0] if result else None))
            # print("[PYTHON BACKEND] All result items:")
            # for i, item in enumerate(result):
                # print("[PYTHON BACKEND] Item {}: {}".format(i+1, item))
            pass
        
        # Check if the result is an error response
        if isinstance(result, dict) and result.get('success') == False:
            # print("[PYTHON BACKEND] Returning error: {}".format(result.get('error', 'Unknown error')))
            return jsonify({
                'success': False,
                'error': result.get('error', 'Unknown error')
            }), 400
        
        # print("[PYTHON BACKEND] Returning success with {} files".format(len(result) if result else 0))
        
        # Hide import animation and show completion - smart threshold based on processing mode
        # Get processing mode to determine appropriate threshold
        try:
            processing_mode = api.get_processing_mode()
            is_serial_mode = processing_mode.get('mode') == 'serial'
            animation_threshold = 5 if is_serial_mode else 15
        except:
            animation_threshold = 10  # Default fallback
        
        # REMOVED: Completion event - Ray callback now handles all progress via SSE
        
        # Trigger comprehensive UI refresh events via SSE
        dispatch_event('images-updated', {})
        dispatch_event('files-changed', {'hasFiles': True})
        dispatch_event('refresh-components', {})
        
        # Get complete current file list for UI updates using same logic as get_image_list
        if api.project:
            complete_file_list = api.get_image_list()
        else:
            complete_file_list = result
        
        # Send direct file data to UI components for immediate updates
        dispatch_event('direct-images-updated', {
            'images': complete_file_list,
            'total_count': len(complete_file_list),
            'newly_added': result
        })
        
        # Force refresh image viewer with complete file list
        dispatch_event('force-refresh-images', {
            'images': complete_file_list,
            'total_count': len(complete_file_list),
            'reason': 'files_added',
            'newly_added': result
        })
        
        # print("[PYTHON BACKEND] Triggered comprehensive UI refresh events via SSE")
        
        return jsonify({
            'success': True,
            'files': result
        })
    except Exception as e:
        # print("[PYTHON BACKEND] Add files error: {}".format(str(e)))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/remove-files', methods=['POST'])
def remove_files():
    """Remove files from project (original files are preserved on filesystem)"""
    try:
        # print("[PYTHON BACKEND] 🗑️ /api/remove-files endpoint called")
        data = request.get_json()
        filenames = data.get('filenames', [])
        
        # print("[PYTHON BACKEND] Received remove files request for {} files".format(len(filenames)))
        # print("[PYTHON BACKEND] Current project loaded: {}".format(api.project is not None))
        
        if api.project is None:
            # print("[PYTHON BACKEND] ERROR: No project is loaded!")
            return jsonify({'success': False, 'error': 'No project loaded'}), 400
        
        if not filenames:
            return jsonify({
                'success': False,
                'error': 'No filenames provided'
            }), 400
        
        # print("[PYTHON BACKEND] Files to remove: {}".format(filenames))
        
        # Get the current project files to find full paths
        project_files = api.project.data.get('files', {})
        removed_files = []
        errors = []
        
        for filename in filenames:
            if filename in project_files:
                try:
                    # Get the full file path from project data
                    file_info = project_files[filename]
                    full_path = file_info.get('path', filename)  # fallback to filename if no path
                    
                    # print("[PYTHON BACKEND] Removing file: {} (path: {})".format(filename, full_path))
                    
                    # Remove from project data only - NEVER delete the original files
                    del project_files[filename]
                    # print("[PYTHON BACKEND] ✅ Removed file from project (original file preserved): {}".format(full_path))
                    
                    removed_files.append(filename)
                    
                except Exception as file_error:
                    error_msg = "Failed to remove {}: {}".format(filename, str(file_error))
                    # print("[PYTHON BACKEND] ❌ {}".format(error_msg))
                    errors.append(error_msg)
            else:
                error_msg = "File not found in project: {}".format(filename)
                # print("[PYTHON BACKEND] ❌ {}".format(error_msg))
                errors.append(error_msg)
        
        # Update project data
        api.project.data['files'] = project_files
        
        # Save project changes
        try:
            api.project.save()
            # print("[PYTHON BACKEND] ✅ Project saved after file removal")
        except Exception as save_error:
            # print("[PYTHON BACKEND] ⚠️ Failed to save project: {}".format(str(save_error)))
            pass
        
        result = {
            'success': True,
            'removed_files': removed_files,
            'errors': errors,
            'message': 'Removed {} files from project (original files preserved)'.format(len(removed_files))
        }
        
        if errors:
            result['message'] += ' with {} errors'.format(len(errors))
        
        # print("[PYTHON BACKEND] Remove files result: {}".format(result))
        
        # Send comprehensive SSE events to update UI
        if removed_files:
            # Get remaining files for UI updates
            remaining_files = []
            for filename, file_info in project_files.items():
                remaining_files.append({
                    'type': file_info.get('type', 'image'),
                    'title': filename,
                    'calib': file_info.get('calib', False),
                    'calib_detected': file_info.get('calib_detected', False),
                    'cameraModel': file_info.get('cameraModel', 'Unknown'),
                    'datetime': file_info.get('datetime', 'Unknown'),
                    'layers': file_info.get('layers', [])
                })
            
            # Send specific removal event
            dispatch_event('files-removed', {
                'removed_files': removed_files,
                'remaining_count': len(project_files)
            })
            
            # Send general update events
            dispatch_event('images-updated', {})
            dispatch_event('files-changed', {'hasFiles': len(project_files) > 0})
            dispatch_event('refresh-components', {})
            
            # Send direct file data to UI components for immediate updates
            dispatch_event('direct-images-updated', {
                'images': remaining_files,
                'total_count': len(remaining_files)
            })
            
            # Force refresh image viewer with remaining files
            dispatch_event('force-refresh-images', {
                'images': remaining_files,
                'total_count': len(remaining_files),
                'reason': 'files_removed',
                'removed_files': removed_files
            })
            
            # print("[PYTHON BACKEND] Triggered comprehensive UI refresh events via SSE after file removal")
        
        return jsonify(result)
        
    except Exception as e:
        # print("[PYTHON BACKEND] Remove files error: {}".format(str(e)))
        import traceback
        # print("[PYTHON BACKEND] Traceback: {}".format(traceback.format_exc()))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/thumb/<filename>')
def get_thumbnail(filename):
    """Serve image thumbnails with 1/99% contrast stretch"""
    try:
        # print("[PYTHON BACKEND] Thumbnail request for: {}".format(filename))
        
        if not api.project:
            # print("[PYTHON BACKEND] Thumbnail error: No project loaded")
            return jsonify({'error': 'No project loaded'}), 404
        
        # Find the image file in the project data
        image_path = None
        for base, fileset in api.project.data.get('files', {}).items():
            jpg_path = fileset.get('jpg')
            raw_path = fileset.get('raw')
            
            if jpg_path and os.path.basename(jpg_path) == filename:
                image_path = jpg_path
                # print("[PYTHON BACKEND] Found JPG file: {}".format(image_path))
                break
            elif raw_path and os.path.basename(raw_path) == filename:
                image_path = raw_path
                # print("[PYTHON BACKEND] Found RAW file: {}".format(image_path))
                break
        
        if not image_path or not os.path.exists(image_path):
            # print("[PYTHON BACKEND] Thumbnail error: Image file not found: {}".format(filename))
            return jsonify({'error': 'Image file not found'}), 404
        
        # print("[PYTHON BACKEND] Generating thumbnail with contrast stretch for: {}".format(image_path))
        
        # Generate thumbnail with contrast stretch for JPG files
        if image_path.lower().endswith(('.jpg', '.jpeg')):
            from PIL import Image
            import numpy as np
            import io
            
            try:
                with Image.open(image_path) as img:
                    # Create thumbnail maintaining aspect ratio
                    max_size = 512
                    ratio = min(max_size / img.width, max_size / img.height)
                    new_size = (int(img.width * ratio), int(img.height * ratio))
                    img.thumbnail(new_size, Image.LANCZOS)
                    
                    # Apply 1/99% contrast stretch
                    arr = np.array(img)
                    if arr.ndim == 3 and arr.shape[2] == 3:
                        # Color image
                        p1, p99 = np.percentile(arr, [1, 99])
                        if p99 > p1:
                            arr = np.clip((arr - p1) * 255.0 / (p99 - p1), 0, 255)
                        arr = arr.astype(np.uint8)
                    else:
                        # Grayscale image
                        p1, p99 = np.percentile(arr, [1, 99])
                        if p99 > p1:
                            arr = np.clip((arr - p1) * 255.0 / (p99 - p1), 0, 255).astype(np.uint8)
                    
                    # Convert back to PIL Image
                    processed_img = Image.fromarray(arr)
                    
                    # Save as JPEG in memory
                    buffer = io.BytesIO()
                    processed_img.save(buffer, format='JPEG', quality=85)
                    buffer.seek(0)
                    
                    # print("[PYTHON BACKEND] Contrast stretch applied, serving processed thumbnail")
                    return send_file(buffer, mimetype='image/jpeg', as_attachment=False)
                    
            except Exception as e:
                # print("[PYTHON BACKEND] Error processing thumbnail: {}".format(str(e)))
                # Fallback to serving original file
                return send_file(image_path, mimetype='image/jpeg')
        
        # For RAW files, we'd need to generate thumbnails, but for now serve a placeholder
        else:
            # print("[PYTHON BACKEND] RAW file thumbnail requested - would need thumbnail generation")
            return jsonify({'error': 'RAW thumbnail generation not implemented'}), 501
            
    except Exception as e:
        # print("[PYTHON BACKEND] Thumbnail error: {}".format(str(e)))
        return jsonify({'error': str(e)}), 500

def get_preview_cache_path(project_path, filename, layer='JPG'):
    """Get the cache path for a preview PNG image"""
    preview_base = os.path.join(project_path, 'Preview Images')
    
    # Create Preview Images directory if it doesn't exist
    if not os.path.exists(preview_base):
        os.makedirs(preview_base, exist_ok=True)
    
    # Map layer names to subdirectories
    # Handle actual layer names which include parentheses: 'RAW (Target)', 'RAW (Reflectance)', 'RAW (Original)'
    if 'Target' in layer or layer == 'Target':
        subdir = 'RAW Target'
    elif 'Reflectance' in layer or layer == 'Reflectance':
        subdir = 'RAW Reflectance'
    elif 'Original' in layer or layer == 'RAW':
        subdir = 'RAW Original'
    elif layer == 'JPG':
        subdir = 'JPG'
    else:
        # For any other layers (indices, custom layers), use a general folder
        subdir = 'Other'
    
    preview_dir = os.path.join(preview_base, subdir)
    if not os.path.exists(preview_dir):
        os.makedirs(preview_dir, exist_ok=True)
    
    # Create cache filename: base_name_layer.png
    # Include layer name in filename to avoid collisions between different layers of same image
    base_name = os.path.splitext(filename)[0]
    # Sanitize layer name for filename (remove special characters)
    layer_safe = layer.replace(' ', '_').replace('(', '').replace(')', '').replace('/', '_')
    cache_path = os.path.join(preview_dir, "{}_{}.png".format(base_name, layer_safe))
    
    return cache_path

def save_preview_cache(image_data, cache_path):
    """Save processed image data to preview cache"""
    try:
        from PIL import Image
        import numpy as np
        
        # Ensure data is uint8
        if image_data.dtype != np.uint8:
            image_data = image_data.astype(np.uint8)
        
        # Convert to PIL and save
        if image_data.ndim == 3:
            img = Image.fromarray(image_data)
        else:
            img = Image.fromarray(image_data)
        
        img.save(cache_path, format='PNG', optimize=True)
        return True
    except Exception as e:
        return False

def serve_cached_preview(cache_path):
    """Serve cached preview PNG directly from disk (fast path)"""
    if not os.path.exists(cache_path):
        return None
    
    try:
        # Serve the PNG file directly without any conversion - much faster!
        # Use send_from_directory for better reliability with file paths
        directory = os.path.dirname(cache_path)
        filename = os.path.basename(cache_path)
        return send_from_directory(directory, filename, mimetype='image/png')
    except Exception as e:
        return None

@app.route('/image/<filename>/')
def send_image(filename):
    """Serve full images with contrast stretch"""
    try:
        # print("[PYTHON BACKEND] Full image request for: {}".format(filename))
        
        if not api.project:
            # print("[PYTHON BACKEND] Full image error: No project loaded")
            return jsonify({'error': 'No project loaded'}), 404
        
        # Find the image file in the project data
        base = os.path.splitext(filename)[0]
        image_set = api.project.data['files'].get(base)
        
        # If not found, try to find it by matching the JPG filename
        if not image_set:
            for key, fileset in api.project.data.get('files', {}).items():
                if fileset.get('jpg') and os.path.basename(fileset['jpg']) == filename:
                    image_set = fileset
                    break
        
        if not image_set:
            # print("[PYTHON BACKEND] Full image error: No image set found for: {}".format(filename))
            return jsonify({'error': 'Image not found'}), 404
        
        image_path = image_set.get('jpg')
        if not image_path or not os.path.exists(image_path):
            # print("[PYTHON BACKEND] Full image error: Image file not found: {}".format(image_path))
            return jsonify({'error': 'Image file not found'}), 404
        
        # Check for cached preview first
        project_path = api.project.fp
        cache_path = get_preview_cache_path(project_path, filename, 'JPG')
        
        # Check if cache exists and is newer than source file
        cache_valid = False
        if os.path.exists(cache_path):
            source_mtime = os.path.getmtime(image_path)
            cache_mtime = os.path.getmtime(cache_path)
            if cache_mtime >= source_mtime:
                cache_valid = True
        
        if cache_valid:
            # Serve from cache - fast path, no conversion needed
            cached_response = serve_cached_preview(cache_path)
            if cached_response is not None:
                return cached_response
        
        # print("[PYTHON BACKEND] Serving full image: {}".format(image_path))
        
        # Load and process the image with contrast stretch
        if image_path.lower().endswith(('.jpg', '.jpeg')):
            from PIL import Image
            import numpy as np
            import cv2
            import io
            
            try:
                with Image.open(image_path) as img:
                    arr = np.array(img)
                    
                    # Apply 1/99% contrast stretch
                    if arr.ndim == 3 and arr.shape[2] == 3:
                        p1, p99 = np.percentile(arr, [1, 99])
                        if p99 > p1:
                            arr = np.clip((arr - p1) * 255.0 / (p99 - p1), 0, 255)
                        arr = arr.astype(np.uint8)
                    else:
                        p1, p99 = np.percentile(arr, [1, 99])
                        if p99 > p1:
                            arr = np.clip((arr - p1) * 255.0 / (p99 - p1), 0, 255).astype(np.uint8)
                    
                    # Save to cache for next time
                    save_preview_cache(arr, cache_path)
                    
                    # Convert RGB to BGR for OpenCV
                    if len(arr.shape) == 3 and arr.shape[2] == 3:
                        arr_bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
                    else:
                        arr_bgr = arr
                    
                    # Encode as PNG
                    _, buffer = cv2.imencode('.png', arr_bgr)
                    byte_io = io.BytesIO(buffer)
                    
                    # print("[PYTHON BACKEND] Full image processed and served")
                    return send_file(byte_io, mimetype='image/png', as_attachment=False)
                    
            except Exception as e:
                # print("[PYTHON BACKEND] Error processing full image: {}".format(str(e)))
                # Fallback to serving original file
                return send_file(image_path, mimetype='image/jpeg')
        
        else:
            return jsonify({'error': 'Unsupported image format'}), 501
            
    except Exception as e:
        # print("[PYTHON BACKEND] Full image error: {}".format(str(e)))
        return jsonify({'error': str(e)}), 500

@app.route('/image/<filename>/<layer>')
def send_image_layer(filename, layer):
    """Serve image layers (JPG, RAW, Target, Reflectance, indices, etc.)"""
    try:
        import urllib.parse
        from PIL import Image
        import numpy as np
        import io
        
        # URL decode the layer name
        layer = urllib.parse.unquote(layer)
        # print("[PYTHON BACKEND] Layer request for: {} layer: {}".format(filename, layer))
        
        if not api.project:
            return jsonify({'error': 'No project loaded'}), 404
        
        # Special handling for JPG layer - serve the JPG file directly with contrast stretch
        if layer == 'JPG' or layer == '':
            return send_image(filename)
        
        # Get the image object from the project
        imageobj = None
        if filename in api.project.imagemap:
            imageobj = api.project.imagemap[filename]
            # print("[PYTHON BACKEND] Found image object for: {}".format(filename))
        
        if not imageobj:
            # print("[PYTHON BACKEND] Image object not found: {}".format(filename))
            return jsonify({'error': 'Image not found'}), 404
        
        # Get layers for this image
        layers = api.get_image_layers(filename)
        # print("[PYTHON BACKEND] Available layers for {}: {}".format(filename, layers))
        
        # Check if the requested layer exists
        if layer not in imageobj.layers:
            # print("[PYTHON BACKEND] Layer '{}' not found in image layers: {}".format(layer, list(imageobj.layers.keys())))
            return jsonify({'error': 'Layer not found: {}'.format(layer)}), 404
        
        # Get the layer file path
        layer_path = imageobj.layers[layer]
        if not layer_path or not os.path.exists(layer_path):
            # print("[PYTHON BACKEND] Layer file not found: {}".format(layer_path))
            return jsonify({'error': 'Layer file not found'}), 404
        
        # print("[PYTHON BACKEND] Serving layer file: {}".format(layer_path))
        
        # Check for cached preview first
        project_path = api.project.fp
        cache_path = get_preview_cache_path(project_path, filename, layer)
        
        # Check if cache exists and is newer than source file
        cache_valid = False
        if os.path.exists(cache_path):
            source_mtime = os.path.getmtime(layer_path)
            cache_mtime = os.path.getmtime(cache_path)
            if cache_mtime >= source_mtime:
                cache_valid = True
        
        if cache_valid:
            # Serve from cache - fast path, no conversion needed
            cached_response = serve_cached_preview(cache_path)
            if cached_response is not None:
                return cached_response
        
        # Handle RAW files (need special processing)
        if layer_path.lower().endswith('.raw'):
            # print("[PYTHON BACKEND] Processing RAW file: {}".format(layer_path))
            try:
                # Use the LabImage to load RAW data properly
                from project import LabImage
                raw_image = LabImage(api.project, layer_path)
                raw_data = raw_image.data
                
                if raw_data is None:
                    # print("[PYTHON BACKEND] Failed to load RAW data")
                    return jsonify({'error': 'Failed to load RAW data'}), 500
                
                # print("[PYTHON BACKEND] RAW data shape: {}, dtype: {}".format(raw_data.shape, raw_data.dtype))
                
                # Apply 1/99% contrast stretch
                if raw_data.ndim == 3 and raw_data.shape[2] == 3:
                    p1, p99 = np.percentile(raw_data, [1, 99])
                    if p99 > p1:
                        raw_data = np.clip((raw_data - p1) * 255.0 / (p99 - p1), 0, 255)
                    raw_data = raw_data.astype(np.uint8)
                    # Swap channels 0 and 2 (BGR to RGB) for RAW (Original)
                    raw_data = raw_data[:, :, [2, 1, 0]]
                    # print("[PYTHON BACKEND] Swapped BGR to RGB for RAW (Original)")
                else:
                    p1, p99 = np.percentile(raw_data, [1, 99])
                    if p99 > p1:
                        raw_data = np.clip((raw_data - p1) * 255.0 / (p99 - p1), 0, 255).astype(np.uint8)
                
                # Save to cache for next time
                save_preview_cache(raw_data, cache_path)
                
                # Convert to PIL Image and send
                processed_img = Image.fromarray(raw_data)
                buffer = io.BytesIO()
                processed_img.save(buffer, format='PNG')
                buffer.seek(0)
                
                # print("[PYTHON BACKEND] RAW layer processed and served")
                return send_file(buffer, mimetype='image/png', as_attachment=False)
                
            except Exception as e:
                # print("[PYTHON BACKEND] Error processing RAW file: {}".format(str(e)))
                import traceback
                traceback.print_exc()
                return jsonify({'error': 'Failed to process RAW file: {}'.format(str(e))}), 500
        
        # Handle TIFF files (common for exported layers)
        elif layer_path.lower().endswith(('.tif', '.tiff')):
            # print("[PYTHON BACKEND] Processing TIFF file: {}".format(layer_path))
            try:
                # CRITICAL: Use tifffile for Index layers to preserve uint16 RGBA correctly
                # PIL.Image.open() auto-converts uint16 RGBA → uint8, corrupting LUT colors
                is_index_layer = 'Index' in layer
                
                if is_index_layer:
                    # Use tifffile to load uint16 RGBA correctly
                    import tifffile
                    arr = tifffile.imread(layer_path)
                    # print("[PYTHON BACKEND] Index TIFF (tifffile) shape: {}, dtype: {}".format(arr.shape, arr.dtype))
                else:
                    # Use PIL for other layers
                    with Image.open(layer_path) as img:
                        arr = np.array(img)
                        # print("[PYTHON BACKEND] TIFF shape: {}, dtype: {}".format(arr.shape, arr.dtype))
                    
                # CRITICAL: Index layers are display-ready RGB/RGBA - don't apply contrast stretch!
                # They already have correct LUT colors. Just convert uint16 → uint8.
                if is_index_layer and arr.ndim == 3 and arr.shape[2] >= 3:
                    if arr.dtype == np.uint16:
                        # Simple scaling: 65535 → 255
                        arr = (arr / 257).astype(np.uint8)
                    
                    # If RGBA, strip alpha channel for PNG output
                    if arr.shape[2] == 4:
                        arr = arr[:, :, :3]  # Keep only RGB, drop alpha
                # For non-index layers, apply contrast stretch as before
                elif arr.ndim == 3 and arr.shape[2] == 3:
                    p1, p99 = np.percentile(arr, [1, 99])
                    if p99 > p1:
                        arr = np.clip((arr - p1) * 255.0 / (p99 - p1), 0, 255)
                    arr = arr.astype(np.uint8)
                else:
                    p1, p99 = np.percentile(arr, [1, 99])
                    if p99 > p1:
                        arr = np.clip((arr - p1) * 255.0 / (p99 - p1), 0, 255).astype(np.uint8)
                
                # Save to cache for next time
                save_preview_cache(arr, cache_path)
                
                # Convert to PIL and send
                processed_img = Image.fromarray(arr)
                buffer = io.BytesIO()
                processed_img.save(buffer, format='PNG')
                buffer.seek(0)
                
                # print("[PYTHON BACKEND] TIFF layer processed and served")
                return send_file(buffer, mimetype='image/png', as_attachment=False)
                    
            except Exception as e:
                # print("[PYTHON BACKEND] Error processing TIFF file: {}".format(str(e)))
                import traceback
                traceback.print_exc()
                return jsonify({'error': 'Failed to process TIFF file: {}'.format(str(e))}), 500
        
        # Handle JPG/PNG files (direct serve with contrast stretch)
        elif layer_path.lower().endswith(('.jpg', '.jpeg', '.png')):
            # print("[PYTHON BACKEND] Serving JPG/PNG file with contrast stretch: {}".format(layer_path))
            try:
                with Image.open(layer_path) as img:
                    arr = np.array(img)
                    
                    # Apply 1/99% contrast stretch
                    if arr.ndim == 3 and arr.shape[2] == 3:
                        p1, p99 = np.percentile(arr, [1, 99])
                        if p99 > p1:
                            arr = np.clip((arr - p1) * 255.0 / (p99 - p1), 0, 255)
                        arr = arr.astype(np.uint8)
                    else:
                        p1, p99 = np.percentile(arr, [1, 99])
                        if p99 > p1:
                            arr = np.clip((arr - p1) * 255.0 / (p99 - p1), 0, 255).astype(np.uint8)
                    
                    # Save to cache for next time
                    save_preview_cache(arr, cache_path)
                    
                    processed_img = Image.fromarray(arr)
                    buffer = io.BytesIO()
                    processed_img.save(buffer, format='PNG')
                    buffer.seek(0)
                    
                    # print("[PYTHON BACKEND] JPG/PNG layer processed and served")
                    return send_file(buffer, mimetype='image/png', as_attachment=False)
                    
            except Exception as e:
                # print("[PYTHON BACKEND] Error processing JPG/PNG file: {}".format(str(e)))
                return jsonify({'error': 'Failed to process JPG/PNG file: {}'.format(str(e))}), 500
        
        else:
            # print("[PYTHON BACKEND] Unsupported layer file format: {}".format(layer_path))
            return jsonify({'error': 'Unsupported file format'}), 501
            
    except Exception as e:
        # print("[PYTHON BACKEND] Layer error: {}".format(str(e)))
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/get-image-list', methods=['GET'])
@app.route('/api/backend-get-image-list', methods=['GET'])  # Alias
def get_image_list():
    """Get list of images in the current project"""
    try:
        if not api or not hasattr(api, 'project') or not api.project:
            return jsonify({'success': False, 'error': 'No project loaded', 'images': []})
        
        result = api.get_image_list()
        return jsonify({
            'success': True,
            'images': result
        })
        
    except Exception as e:
        # print("[PYTHON BACKEND] ERROR in get_image_list: {}".format(str(e)))
        return jsonify({
            'success': False,
            'error': str(e),
            'images': []
        }), 500

@app.route('/api/has-project-loaded', methods=['GET'])
def has_project_loaded():
    """Check if a project is currently loaded"""
    try:
        loaded = api and hasattr(api, 'project') and api.project is not None
        return jsonify({'loaded': loaded})
    except Exception as e:
        return jsonify({'loaded': False, 'error': str(e)}), 500

@app.route('/api/open-projects-folder', methods=['POST'])
def open_projects_folder():
    """Open the projects folder in file explorer"""
    try:
        import subprocess
        import platform
        
        if hasattr(api, 'get_working_directory'):
            projects_dir = api.get_working_directory()
        else:
            projects_dir = os.path.join(os.path.expanduser('~'), 'Documents', 'MAPIR', 'Chloros Projects')
        
        if platform.system() == 'Windows':
            os.startfile(projects_dir)
        elif platform.system() == 'Darwin':  # macOS
            subprocess.run(['open', projects_dir])
        else:  # Linux
            subprocess.run(['xdg-open', projects_dir])
        
        return jsonify({'success': True, 'message': 'Projects folder opened'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def _open_file_dialog_windows():
    """Windows-native file dialog using win32 API - works from any thread"""
    import ctypes
    from ctypes import wintypes
    
    # Constants
    OFN_ALLOWMULTISELECT = 0x200
    OFN_EXPLORER = 0x80000
    OFN_FILEMUSTEXIST = 0x1000
    OFN_HIDEREADONLY = 0x4
    OFN_NOCHANGEDIR = 0x8
    
    # Structure for OPENFILENAME
    class OPENFILENAME(ctypes.Structure):
        _fields_ = [
            ('lStructSize', wintypes.DWORD),
            ('hwndOwner', wintypes.HWND),
            ('hInstance', wintypes.HINSTANCE),
            ('lpstrFilter', wintypes.LPCWSTR),
            ('lpstrCustomFilter', wintypes.LPWSTR),
            ('nMaxCustFilter', wintypes.DWORD),
            ('nFilterIndex', wintypes.DWORD),
            ('lpstrFile', wintypes.LPWSTR),
            ('nMaxFile', wintypes.DWORD),
            ('lpstrFileTitle', wintypes.LPWSTR),
            ('nMaxFileTitle', wintypes.DWORD),
            ('lpstrInitialDir', wintypes.LPCWSTR),
            ('lpstrTitle', wintypes.LPCWSTR),
            ('Flags', wintypes.DWORD),
            ('nFileOffset', wintypes.WORD),
            ('nFileExtension', wintypes.WORD),
            ('lpstrDefExt', wintypes.LPCWSTR),
            ('lCustData', wintypes.LPARAM),
            ('lpfnHook', ctypes.c_void_p),
            ('lpTemplateName', wintypes.LPCWSTR),
            ('pvReserved', ctypes.c_void_p),
            ('dwReserved', wintypes.DWORD),
            ('FlagsEx', wintypes.DWORD),
        ]
    
    # Create buffer for file paths (multiple files separated by null)
    MAX_PATH_BUFFER = 65536
    file_buffer = ctypes.create_unicode_buffer(MAX_PATH_BUFFER)
    
    # File filter: Supported Files (*.jpg;*.jpeg;*.raw;*.daq;*.csv)\0*.jpg;*.jpeg;*.raw;*.daq;*.csv\0All Files (*.*)\0*.*\0\0
    file_filter = "Supported Files (*.jpg;*.jpeg;*.raw;*.daq;*.csv)\0*.jpg;*.jpeg;*.raw;*.daq;*.csv;*.JPG;*.JPEG;*.RAW;*.DAQ;*.CSV\0All Files (*.*)\0*.*\0\0"
    
    ofn = OPENFILENAME()
    ofn.lStructSize = ctypes.sizeof(OPENFILENAME)
    ofn.hwndOwner = None
    ofn.lpstrFilter = file_filter
    ofn.lpstrFile = ctypes.cast(file_buffer, wintypes.LPWSTR)
    ofn.nMaxFile = MAX_PATH_BUFFER
    ofn.lpstrTitle = "Select Images"
    ofn.Flags = OFN_ALLOWMULTISELECT | OFN_EXPLORER | OFN_FILEMUSTEXIST | OFN_HIDEREADONLY | OFN_NOCHANGEDIR
    
    # Call GetOpenFileName
    comdlg32 = ctypes.windll.comdlg32
    result = comdlg32.GetOpenFileNameW(ctypes.byref(ofn))
    
    if result:
        # Parse the result - for multiple files, format is: dir\0file1\0file2\0\0
        raw_result = file_buffer.value
        
        # Check if there's a null in the result (indicating multiple files)
        null_pos = raw_result.find('\0') if '\0' in file_buffer[:] else -1
        
        # Read the raw buffer to find all files
        files = []
        i = 0
        parts = []
        current = ""
        
        # Parse null-separated strings from buffer
        for j in range(MAX_PATH_BUFFER):
            char = file_buffer[j]
            if char == '\0':
                if current:
                    parts.append(current)
                    current = ""
                else:
                    # Double null = end
                    break
            else:
                current += char
        
        if len(parts) == 1:
            # Single file selected
            files = [parts[0]]
        elif len(parts) > 1:
            # Multiple files: first part is directory, rest are filenames
            directory = parts[0]
            for filename in parts[1:]:
                files.append(os.path.join(directory, filename))
        
        return files
    else:
        return []

@app.route('/api/select-files-dialog', methods=['POST'])
def select_files_dialog():
    """Open a file selection dialog and return selected file paths"""
    try:
        print("[SELECT-FILES-DIALOG] Starting file dialog...", flush=True)
        
        # Use tkinter directly for consistent icon display and reliability
        # (Windows native GetOpenFileName doesn't support custom icons easily)
        import tkinter as tk
        from tkinter import filedialog
        
        # Create a hidden root window
        root = tk.Tk()
        root.withdraw()
        
        # Set the corn logo icon for the dialog
        try:
            # Find the icon file relative to this script
            script_dir = os.path.dirname(os.path.abspath(__file__))
            icon_path = os.path.join(script_dir, 'ui', 'corn_logo_single_256.ico')
            if os.path.exists(icon_path):
                root.iconbitmap(icon_path)
                print(f"[SELECT-FILES-DIALOG] Set icon: {icon_path}", flush=True)
        except Exception as icon_err:
            print(f"[SELECT-FILES-DIALOG] Could not set icon: {icon_err}", flush=True)
        
        # Windows-specific: Make dialog appear on top
        root.attributes('-topmost', True)
        root.update()  # Process pending events
        root.lift()    # Bring to front
        root.focus_force()  # Force focus
        
        # On Windows, we may need to call update_idletasks to ensure the window is ready
        root.update_idletasks()
        
        print("[SELECT-FILES-DIALOG] Opening tkinter file dialog...", flush=True)
        
        # Open file dialog with EXACT same file types as Electron
        # Electron uses: jpg, jpeg, raw, daq, csv
        file_paths = filedialog.askopenfilenames(
            parent=root,
            title='Select Images',
            filetypes=[
                ('Supported Files', '*.jpg *.jpeg *.raw *.daq *.csv *.JPG *.JPEG *.RAW *.DAQ *.CSV'),
                ('All Files', '*.*')
            ]
        )
        
        print(f"[SELECT-FILES-DIALOG] Dialog closed, files: {file_paths}", flush=True)
        
        # Cleanup
        root.destroy()
        
        # Convert tuple to list
        selected_files = list(file_paths) if file_paths else []
        
        print(f"[SELECT-FILES-DIALOG] Selected {len(selected_files)} files", flush=True)
        
        return jsonify({'success': True, 'files': selected_files})
    except Exception as e:
        print(f"[SELECT-FILES-DIALOG] Error: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

def _open_folder_dialog_windows():
    """Windows-native folder dialog using shell API - works from any thread"""
    import ctypes
    from ctypes import wintypes
    
    # Constants
    BIF_RETURNONLYFSDIRS = 0x0001
    BIF_NEWDIALOGSTYLE = 0x0040
    MAX_PATH = 260
    
    # Structure for BROWSEINFOW (must match Windows SDK exactly)
    class BROWSEINFOW(ctypes.Structure):
        _fields_ = [
            ('hwndOwner', wintypes.HWND),
            ('pidlRoot', ctypes.c_void_p),
            ('pszDisplayName', ctypes.c_wchar_p),
            ('lpszTitle', ctypes.c_wchar_p),
            ('ulFlags', wintypes.UINT),
            ('lpfn', ctypes.c_void_p),
            ('lParam', wintypes.LPARAM),
            ('iImage', ctypes.c_int),
        ]
    
    # Load shell32 and ole32
    shell32 = ctypes.windll.shell32
    ole32 = ctypes.windll.ole32
    
    # Define function signatures AFTER defining BROWSEINFOW
    SHBrowseForFolderW = shell32.SHBrowseForFolderW
    SHBrowseForFolderW.argtypes = [ctypes.POINTER(BROWSEINFOW)]
    SHBrowseForFolderW.restype = ctypes.c_void_p
    
    SHGetPathFromIDListW = shell32.SHGetPathFromIDListW
    SHGetPathFromIDListW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p]
    SHGetPathFromIDListW.restype = wintypes.BOOL
    
    # Initialize COM for this thread
    ole32.CoInitialize(None)
    
    try:
        # Create buffer for display name
        display_name = ctypes.create_unicode_buffer(MAX_PATH)
        
        # Set up BROWSEINFO structure
        bi = BROWSEINFOW()
        bi.hwndOwner = None
        bi.pidlRoot = None
        bi.pszDisplayName = ctypes.cast(display_name, ctypes.c_wchar_p)
        bi.lpszTitle = "Select Folder Containing Images"
        bi.ulFlags = BIF_RETURNONLYFSDIRS | BIF_NEWDIALOGSTYLE
        bi.lpfn = None
        bi.lParam = 0
        bi.iImage = 0
        
        # Call SHBrowseForFolderW with pointer to structure
        pidl = SHBrowseForFolderW(ctypes.byref(bi))
        
        if pidl:
            # Get the path from the PIDL
            path_buffer = ctypes.create_unicode_buffer(MAX_PATH)
            success = SHGetPathFromIDListW(pidl, path_buffer)
            
            # Free the PIDL using CoTaskMemFree
            ole32.CoTaskMemFree(pidl)
            
            if success:
                return path_buffer.value
            else:
                return None
        else:
            return None
    finally:
        # Uninitialize COM
        ole32.CoUninitialize()

@app.route('/api/select-folder-dialog', methods=['POST'])
def select_folder_dialog():
    """Open a folder selection dialog and return selected folder path"""
    try:
        print("[SELECT-FOLDER-DIALOG] Starting folder dialog...", flush=True)
        
        # Use tkinter directly - Windows native SHBrowseForFolder has issues with ctypes
        # (causes double dialog, overflow errors, etc.)
        import tkinter as tk
        from tkinter import filedialog
        
        # Create a hidden root window
        root = tk.Tk()
        root.withdraw()
        
        # Set the corn logo icon for the dialog
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            icon_path = os.path.join(script_dir, 'ui', 'corn_logo_single_256.ico')
            if os.path.exists(icon_path):
                root.iconbitmap(icon_path)
                print(f"[SELECT-FOLDER-DIALOG] Set icon: {icon_path}", flush=True)
        except Exception as icon_err:
            print(f"[SELECT-FOLDER-DIALOG] Could not set icon: {icon_err}", flush=True)
        
        # Windows-specific: Make dialog appear on top
        root.attributes('-topmost', True)
        root.update()  # Process pending events
        root.lift()    # Bring to front
        root.focus_force()  # Force focus
        
        # On Windows, we may need to call update_idletasks to ensure the window is ready
        root.update_idletasks()
        
        print("[SELECT-FOLDER-DIALOG] Opening tkinter folder dialog...", flush=True)
        
        # Open folder dialog with same title as Electron
        folder_path = filedialog.askdirectory(
            parent=root,
            title='Select Folder Containing Images'
        )
        
        # Cleanup
        root.destroy()
        
        print(f"[SELECT-FOLDER-DIALOG] Selected folder: {folder_path}", flush=True)
        
        if not folder_path:
            return jsonify({'success': False, 'message': 'No folder selected'})
        
        # Scan folder recursively for EXACT same file types as Electron
        # Electron uses: .jpg, .jpeg, .raw, .daq, .csv
        supported_extensions = ['.jpg', '.jpeg', '.raw', '.daq', '.csv']
        files = []
        
        def scan_directory_recursive(dir_path):
            """Recursively scan directory for supported files (matches Electron behavior)"""
            try:
                for entry in os.listdir(dir_path):
                    full_path = os.path.join(dir_path, entry)
                    if os.path.isdir(full_path):
                        # Recursively scan subdirectories
                        scan_directory_recursive(full_path)
                    elif os.path.isfile(full_path):
                        # Check if file has supported extension (case-insensitive)
                        ext = os.path.splitext(entry)[1].lower()
                        if ext in supported_extensions:
                            files.append(full_path)
            except Exception as e:
                print(f"[SELECT-FOLDER-DIALOG] Warning: Error scanning {dir_path}: {e}", flush=True)
        
        scan_directory_recursive(folder_path)
        
        print(f"[SELECT-FOLDER-DIALOG] Found {len(files)} supported files (jpg, jpeg, raw, daq, csv)", flush=True)
        
        if len(files) == 0:
            print(f"[SELECT-FOLDER-DIALOG] No supported files found in folder: {folder_path}", flush=True)
        
        return jsonify({'success': True, 'folder': folder_path, 'files': files})
    except Exception as e:
        print(f"[SELECT-FOLDER-DIALOG] Error: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/save-project-template', methods=['POST'])
def save_project_template():
    """Save current project as a template"""
    try:
        data = request.get_json()
        template_name = data.get('templateName') if isinstance(data, dict) else data
        
        if not template_name:
            return jsonify({'success': False, 'error': 'Template name is required'}), 400
        
        # Check if API has save_project_template method
        if hasattr(api, 'save_project_template'):
            api.save_project_template(template_name)
            return jsonify({'success': True, 'message': f'Template "{template_name}" saved'})
        else:
            return jsonify({'success': False, 'error': 'Template saving not implemented'}), 501
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/add-folder', methods=['POST'])
def add_folder():
    """Add all images from a folder"""
    try:
        data = request.get_json()
        folder_path = data.get('folderPath') if isinstance(data, dict) else data
        
        if not folder_path:
            return jsonify({'success': False, 'error': 'Folder path is required'}), 400
        
        # Check if API has add_folder method
        if hasattr(api, 'add_folder'):
            result = api.add_folder(folder_path)
            return jsonify({'success': True, 'files': result})
        else:
            # Fallback: scan folder for images and add them
            import glob
            extensions = ['*.jpg', '*.jpeg', '*.tif', '*.tiff', '*.png', '*.JPG', '*.JPEG', '*.TIF', '*.TIFF', '*.PNG']
            files = []
            for ext in extensions:
                files.extend(glob.glob(os.path.join(folder_path, ext)))
            
            if files and hasattr(api, 'add_files'):
                api.add_files(files)
                return jsonify({'success': True, 'files': files})
            
            return jsonify({'success': False, 'error': 'No images found in folder'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/get-scan-data', methods=['POST'])
def get_scan_data():
    """Get scan/calibration data for an image"""
    try:
        data = request.get_json()
        filename = data.get('filename') if isinstance(data, dict) else data
        
        if not filename:
            return jsonify({'success': False, 'error': 'Filename is required'}), 400
        
        # Check if API has get_scan_data method
        if hasattr(api, 'get_scan_data'):
            scan_data = api.get_scan_data(filename)
            return jsonify({'success': True, 'data': scan_data})
        else:
            return jsonify({'success': False, 'error': 'Scan data not available'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/get-processing-progress', methods=['GET'])
def get_processing_progress():
    """Get current processing progress"""
    try:
        # Check if API has get_progress method
        if hasattr(api, 'get_progress'):
            progress = api.get_progress()
            return jsonify(progress)
        else:
            return jsonify({'percent': 0, 'phase': 'idle'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/load-user-email', methods=['GET'])
def load_user_email():
    """Get user email"""
    try:
        # Check if API has get_user_email method
        if hasattr(api, 'user_email'):
            return jsonify({'email': api.user_email or ''})
        elif hasattr(api, 'get_user_email'):
            email = api.get_user_email()
            return jsonify({'email': email or ''})
        else:
            return jsonify({'email': ''})
    except Exception as e:
        return jsonify({'email': '', 'error': str(e)}), 500

@app.route('/api/save-user-email', methods=['POST'])
def save_user_email():
    """Save user email"""
    try:
        data = request.get_json()
        email = data.get('email') if isinstance(data, dict) else data
        
        # Check if API has set_user_email method
        if hasattr(api, 'set_user_email'):
            api.set_user_email(email)
            return jsonify({'success': True})
        elif hasattr(api, 'user_email'):
            api.user_email = email
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'User email saving not implemented'}), 501
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/save-user-language', methods=['POST'])
def save_user_language():
    """Save user language preference"""
    try:
        data = request.get_json()
        language = data.get('language') if isinstance(data, dict) else data
        
        # Check if API has set_user_language method
        if hasattr(api, 'set_user_language'):
            api.set_user_language(language)
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Language saving not implemented'}), 501
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/clear-jpg-cache', methods=['POST'])
def clear_jpg_cache():
    """Clear JPG cache for a specific file"""
    try:
        data = request.get_json()
        filename = data.get('filename') if isinstance(data, dict) else data
        
        # Check if API has clear_jpg_cache method
        if hasattr(api, 'clear_jpg_cache'):
            api.clear_jpg_cache(filename)
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Cache clearing not implemented'}), 501
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/clear-thumbnail-cache', methods=['POST'])
def clear_thumbnail_cache():
    """Clear thumbnail cache for a specific file"""
    try:
        data = request.get_json()
        filename = data.get('filename') if isinstance(data, dict) else data
        
        # Check if API has clear_thumbnail_cache method
        if hasattr(api, 'clear_thumbnail_cache'):
            api.clear_thumbnail_cache(filename)
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Cache clearing not implemented'}), 501
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/clear-cache', methods=['POST'])
def clear_cache():
    """Clear preview image caches"""
    try:
        if not api.project:
            return jsonify({'success': False, 'error': 'No project loaded'})
        
        import shutil
        project_path = api.project.fp
        preview_folder = os.path.join(project_path, 'Preview Images')
        
        if os.path.exists(preview_folder):
            shutil.rmtree(preview_folder)
            # print("[PYTHON BACKEND] Preview cache cleared: {}".format(preview_folder))
            return jsonify({'success': True, 'message': 'Preview cache cleared'})
        else:
            # print("[PYTHON BACKEND] No preview cache to clear")
            return jsonify({'success': True, 'message': 'No cache to clear'})
    except Exception as e:
        # print("[PYTHON BACKEND] Error clearing cache: {}".format(str(e)))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/process-images', methods=['POST'])
def process_images():
    """Process images"""
    try:
        data = request.get_json()
        result = api.process_images(data)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500



@app.route('/api/set-processing-mode', methods=['POST'])
def set_processing_mode():
    """Set processing mode via API"""
    try:
        data = request.get_json() or {}
        mode = data.get('mode', 'serial')
        
        # SECURITY: Enforce Chloros+ requirement for premium mode
        if mode == 'premium' or mode == 'parallel':
            # Check if user has valid Chloros+ subscription
            if not api.user_logged_in:
                return jsonify({
                    'success': False,
                    'error': 'Premium mode requires Chloros+ subscription',
                    'message': 'Please login with a Chloros+ account to use premium mode'
                }), 403
            
            if api.user_subscription_level != "premium":
                return jsonify({
                    'success': False,
                    'error': 'Premium mode requires Chloros+ subscription',
                    'message': 'Your current plan does not include premium processing mode',
                    'subscription_level': api.user_subscription_level
                }), 403
        
        result = api.set_processing_mode(mode)
        
        return jsonify({
            'success': result,
            'message': f'Processing mode set to {mode}' if result else f'Failed to set processing mode to {mode}'
        })
    except Exception as e:
        # print(f"[PYTHON BACKEND] ❌ set_processing_mode endpoint error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/get-processing-mode', methods=['GET'])
def get_processing_mode():
    """Get current processing mode via API"""
    try:
        # print(f"[PYTHON BACKEND] 🔧 get_processing_mode endpoint called")
        
        result = api.get_processing_mode()
        
        return jsonify({
            'success': True,
            'data': result,
            'message': 'Processing mode retrieved successfully'
        })
    except Exception as e:
        # print(f"[PYTHON BACKEND] ❌ get_processing_mode endpoint error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/interrupt-project', methods=['POST'])
def interrupt_project():
    """Interrupt current project processing"""
    try:
        # print("[PYTHON BACKEND] 🛑 interrupt_project endpoint called - STOPPING PROCESSING", flush=True)
        
        result = api.interrupt_project()
        
        return jsonify({
            'success': True,
            'message': 'Processing interrupted successfully'
        })
        
    except Exception as e:
        # print(f"[PYTHON BACKEND] ❌ Error interrupting processing: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/process-project', methods=['POST'])
def process_project():
    """Process project using the main API method"""
    # Force immediate output to ensure we see this
    import sys
    # print("[PYTHON BACKEND] 🚀 process_project endpoint called - ENTRY POINT", flush=True)
    safe_flush()
    # print("[PYTHON BACKEND] 🚀 This function is definitely being called!", flush=True)
    safe_flush()
    
    def run_processing():
        """Run processing in a separate thread to avoid blocking SSE"""
        try:
            # Send a starting event
            dispatch_event('processing-started', {
                'message': 'Processing has begun'
            })
            
            try:
                result = api.process_project()
            except Exception as method_error:
                print(f"[BACKEND] 💥 EXCEPTION in api.process_project(): {method_error}", flush=True)
                import traceback
                traceback.print_exc()
                raise method_error
            
            # CRITICAL: Save project after processing to ensure all data is persisted (CLI compatibility)
            if api.project:
                try:
                    api.project.write()
                except Exception as save_error:
                    print(f"[BACKEND] ⚠ Warning: Could not save project: {save_error}", flush=True)
            
            # Send completion event
            dispatch_event('processing-complete', {
                'success': True,
                'result': result
            })
            
            print("✅ Processing complete event dispatched", flush=True)
            safe_flush()
            
        except Exception as e:
            print(f"[BACKEND] ❌ run_processing error: {e}", flush=True)
            import traceback
            traceback.print_exc()
            safe_flush()
            
            # Send error event
            dispatch_event('processing-error', {
                'success': False,
                'error': str(e)
            })
    
    try:
        # Check if project has files
        if not api.project or not api.project.data.get('files'):
            print("[BACKEND] ❌ No files loaded in project!", flush=True)
            return jsonify({
                'success': False,
                'error': 'No files loaded in project'
            }), 400
        
        # Processing starting silently
        
        # Start processing in a daemon thread (lightweight, no executor needed)
        import threading
        processing_thread = threading.Thread(target=run_processing, daemon=True, name="ProcessingThread")
        processing_thread.start()
        
        # Verify thread is running
        import time
        time.sleep(0.1)  # Brief pause to let thread start
        if not processing_thread.is_alive():
            print("[BACKEND] ⚠ WARNING: Processing thread died immediately!", flush=True)
        
        return jsonify({
            'success': True,
            'message': 'Processing started in background',
            'async': True,
            'thread_alive': processing_thread.is_alive()
        })
    except Exception as e:
        print(f"[BACKEND] ❌ process_project endpoint error: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/detect-export-layers', methods=['POST'])
def detect_export_layers():
    """Detect and add export layers (Reflectance, Target) to imagemap after processing"""
    try:
        # print("[PYTHON BACKEND] 🔍 Detecting export layers...", flush=True)
        safe_flush()
        
        if not api.project:
            return jsonify({
                'success': False,
                'error': 'No project loaded'
            }), 400
        
        # Call the layer detection methods
        layers_found = 0
        try:
            api._detect_existing_reflectance_layers()
            api._detect_existing_target_layers()
            
            # Count layers in all filesets
            for fileset in api.project.data.get('files', {}).values():
                if 'layers' in fileset:
                    layers_found += len(fileset['layers'])
            
            # print(f"[PYTHON BACKEND] ✅ Layer detection complete: {layers_found} layers found", flush=True)
            
            return jsonify({
                'success': True,
                'layers_found': layers_found,
                'message': f'Detected {layers_found} export layers'
            })
        except Exception as e:
            # print(f"[PYTHON BACKEND] ❌ Error detecting layers: {e}", flush=True)
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'error': str(e),
                'layers_found': 0
            }), 500
            
    except Exception as e:
        # print(f"[PYTHON BACKEND] ❌ detect_export_layers endpoint error: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/sync-checkbox-state', methods=['POST'])
def sync_checkbox_state():
    """Sync checkbox state from frontend to backend"""
    try:
        data = request.get_json()
        filename = data.get('filename')
        calib_state = data.get('calib_state')
        
        # print(f"[PYTHON BACKEND] [SYNC] Received checkbox sync request: {filename} = {calib_state}", flush=True)
        
        # Call the API method
        result = api.sync_checkbox_state(filename, calib_state)
        
        # print(f"[PYTHON BACKEND] [SYNC] sync_checkbox_state returned: {result}", flush=True)
        
        return jsonify({
            'success': True,
            'result': result,
            'message': f'Checkbox state synced for {filename}'
        })
    except Exception as e:
        # print(f"[PYTHON BACKEND] [SYNC] Error syncing checkbox state: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/get-viewer-index-value', methods=['GET'])
def get_viewer_index_value():
    """Get viewer index value for specific coordinates"""
    try:
        imageX = float(request.args.get('imageX'))
        imageY = float(request.args.get('imageY'))
        
        # Get the current active viewer index image data
        if hasattr(api.project, 'active_viewer_index') and api.project.active_viewer_index is not None:
            # active_viewer_index is directly the numpy array, not an Image object
            index_data = api.project.active_viewer_index
            
            # Convert coordinates to integers (pixel positions)
            # Frontend sends pixel-center coordinates, so we need to floor instead of round
            # Pixel (0,0) center is at (0.5, 0.5), so coordinate 0.5 should map to pixel 0
            x = int(imageX)
            y = int(imageY)
            
            # Check bounds
            if 0 <= y < index_data.shape[0] and 0 <= x < index_data.shape[1]:
                # Get the value at this pixel
                # Handle both 2D and 3D arrays (squeeze if needed)
                if len(index_data.shape) == 3:
                    value = float(index_data[y, x, 0])
                else:
                    value = float(index_data[y, x])
                
                return jsonify({'value': value, 'imageX': str(imageX), 'imageY': str(imageY)})
            else:
                # Out of bounds
                return jsonify({'value': None, 'imageX': str(imageX), 'imageY': str(imageY)})
        else:
            # No active index image
            return jsonify({'value': None, 'imageX': str(imageX), 'imageY': str(imageY)})
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/get-image-layers', methods=['GET'])
def get_image_layers():
    """Get layers for a specific image"""
    try:
        image_name = request.args.get('image')
        
        if not api.project:
            return jsonify([]), 200  # Return empty array, not error
        
        # Call the API method to get layers
        layers = api.get_image_layers(image_name)
        
        # Return as JSON array directly (not wrapped in object)
        return jsonify(layers if layers else [])
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify([]), 200  # Return empty array on error to avoid breaking frontend

@app.route('/api/get-calibration-target-polys', methods=['GET'])
def get_calibration_target_polys():
    """Get calibration target polygons for a specific image"""
    try:
        image_name = request.args.get('image')
        # Placeholder implementation - replace with actual logic
        return jsonify({'polygons': [], 'image': image_name})
    except Exception as e:
        print(f"Error getting calibration target polys: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/create-sandbox-image', methods=['POST'])
def create_sandbox_image():
    """Create sandbox image for index/LUT visualization"""
    try:
        data = request.get_json()
        
        # FIX: Frontend uses different key names
        image = data.get('selectedImage') or data.get('image')  # Support both
        index_type = data.get('selectedOption') or data.get('index_type')  # Support both
        index_config = data.get('currentIndexConfig') or data.get('index_config')  # Support both
        selected_layer = data.get('selectedLayer') or data.get('selected_layer')  # Support both
        
        # Call the API's create_sandbox_image method
        result = api.create_sandbox_image(image, index_type, index_config, selected_layer)
        
        if result:
            return jsonify(result)
        else:
            return jsonify({'error': 'Failed to create sandbox image'}), 500
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/sandbox/<filename>/<index_type>/<timestamp>')
def serve_sandbox_image(filename, index_type, timestamp):
    """Serve generated sandbox image (index or LUT)"""
    try:
        import urllib.parse
        from PIL import Image
        import numpy as np
        import io
        
        # URL decode parameters
        filename = urllib.parse.unquote(filename)
        index_type = urllib.parse.unquote(index_type)
        
        if not api.project or not api.project.sandbox_image:
            return jsonify({'error': 'No sandbox image available'}), 404
        
        # Get the appropriate image data based on type
        if index_type == 'lut':
            if not api.project.sandbox_image.lut_image:
                return jsonify({'error': 'LUT image not generated'}), 404
            # Make an immediate deep copy to disconnect from the source
            image_data = api.project.sandbox_image.lut_image.data.copy()
        elif index_type == 'index':
            if not api.project.sandbox_image.index_image:
                return jsonify({'error': 'Index image not generated'}), 404
            # Make an immediate deep copy and convert through bytes to completely disconnect
            source_data = api.project.sandbox_image.index_image.data
            data_bytes = source_data.tobytes()
            image_data = np.frombuffer(data_bytes, dtype=source_data.dtype).reshape(source_data.shape).copy()
        else:
            return jsonify({'error': f'Unknown index type: {index_type}'}), 400
        
        # Convert to displayable format
        # Check if it's a single-channel image (even if 3D with shape [..., 1])
        if image_data.ndim == 3 and image_data.shape[2] == 1:
            # Single channel stored as 3D, squeeze it
            image_data = image_data.squeeze()
        
        # Handle NaN and Inf values
        if np.any(np.isnan(image_data)) or np.any(np.isinf(image_data)):
            image_data = np.nan_to_num(image_data, nan=0.0, posinf=None, neginf=None, copy=True)
        
        if image_data.ndim == 3 and image_data.shape[2] in [3, 4]:
            # True RGB or RGBA image
            if image_data.dtype == np.uint8:
                display_image = image_data
            else:
                # Normalize to 0-255
                min_val = np.min(image_data)
                max_val = np.max(image_data)
                if max_val > min_val:
                    display_image = ((image_data - min_val) * 255 / (max_val - min_val)).astype(np.uint8)
                else:
                    display_image = np.zeros_like(image_data, dtype=np.uint8)
            
            # Handle RGBA vs RGB mode for PIL
            if image_data.shape[2] == 4:
                pil_image = Image.fromarray(display_image)  # PIL infers RGBA from shape
            else:
                pil_image = Image.fromarray(display_image)  # PIL infers RGB from shape
        else:
            # Single channel (2D) - convert to grayscale for display
            if image_data.dtype == np.uint8:
                normalized = image_data
            else:
                # Get threshold values from LUT config if available
                threshold_min = None
                threshold_max = None
                if hasattr(api.project, 'sandbox_lut_config') and api.project.sandbox_lut_config:
                    lut_config = api.project.sandbox_lut_config
                    threshold_min = lut_config.get('thresholdA')
                    threshold_max = lut_config.get('thresholdB')
                
                # Get actual data range
                data_min = float(np.min(image_data))
                data_max = float(np.max(image_data))
                
                # Use thresholds if provided, otherwise use data range
                if threshold_min is not None and threshold_max is not None:
                    min_val = float(threshold_min)
                    max_val = float(threshold_max)
                else:
                    min_val = data_min
                    max_val = data_max
                
                if max_val > min_val:
                    # CRITICAL: Create a COMPLETE COPY of image_data first so operations don't create views
                    image_data_copy = image_data.copy()
                    
                    # Clip to threshold range
                    image_data_clipped = np.clip(image_data_copy, min_val, max_val)
                    
                    # Normalize using the clipped copy
                    # Low values (min) → black (0), High values (max) → white (255)
                    normalized_float = (image_data_clipped - min_val) / (max_val - min_val)
                    normalized = (normalized_float * 255).astype(np.uint8)
                    
                    # Keep the copy alive to prevent GC
                    del image_data_copy
                    del image_data_clipped
                else:
                    normalized = np.zeros_like(image_data, dtype=np.uint8)
            
            # ULTRA CRITICAL: Save normalized to a temp variable to prevent garbage collection
            
            # Make a COMPLETE independent copy of normalized that definitely owns its data
            normalized_copy = normalized.copy()
            
            # Allocate new array and manually copy data using the copy
            # Convert grayscale to RGB
            height, width = normalized_copy.shape
            rgb_array = np.empty((height, width, 3), dtype=np.uint8)
            rgb_array[:, :, 0] = normalized_copy
            rgb_array[:, :, 1] = normalized_copy
            rgb_array[:, :, 2] = normalized_copy
            
            # Ensure array is C-contiguous for PIL
            if not rgb_array.flags['C_CONTIGUOUS']:
                rgb_array = np.ascontiguousarray(rgb_array)
            
            # Create PIL image from bytes
            pil_image = Image.frombytes('RGB', (width, height), rgb_array.tobytes())
            
        buffer = io.BytesIO()
        pil_image.save(buffer, format='PNG')
        buffer.seek(0)
        
        return send_file(buffer, mimetype='image/png', as_attachment=False)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/get-viewer-index-min-max', methods=['GET'])
def get_viewer_index_min_max():
    """Get viewer index min/max values"""
    try:
        result = api.get_viewer_index_min_max()
        return jsonify({'min': result[0], 'max': result[1]})
    except Exception as e:
        print(f"Error getting viewer index min/max: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/update-sandbox-thresholds', methods=['POST'])
def update_sandbox_thresholds():
    """Update sandbox LUT thresholds without regenerating the image"""
    try:
        data = request.get_json()
        threshold_a = data.get('thresholdA')
        threshold_b = data.get('thresholdB')
        
        if not hasattr(api.project, 'sandbox_lut_config') or not api.project.sandbox_lut_config:
            api.project.sandbox_lut_config = {}
        
        api.project.sandbox_lut_config['thresholdA'] = threshold_a
        api.project.sandbox_lut_config['thresholdB'] = threshold_b
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/get-viewer-lut-gradient', methods=['GET'])
def get_viewer_lut_gradient():
    """Get viewer LUT gradient for specific index"""
    try:
        index = request.args.get('index')
        # Placeholder implementation - replace with actual logic
        return jsonify({'gradient': [], 'index': index})
    except Exception as e:
        print(f"Error getting viewer LUT gradient: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/get-exposure-pin-info', methods=['GET'])
def get_exposure_pin_info():
    """Get exposure pin information from .daq files"""
    try:
        if api is None or api.project is None:
            return jsonify({'hasExposureData': False, 'hasPin1': False, 'hasPin2': False})
        
        # Call the API method to get exposure pin info
        exposure_info = api.get_exposure_pin_info()
        return jsonify(exposure_info)
    except Exception as e:
        print(f"Error getting exposure pin info: {e}")
        return jsonify({'hasExposureData': False, 'hasPin1': False, 'hasPin2': False}), 500

@app.route('/api/get-minimum-window-size', methods=['GET'])
def get_minimum_window_size():
    """Get minimum window size"""
    try:
        # Placeholder implementation - replace with actual logic
        return jsonify({'width': 800, 'height': 600})
    except Exception as e:
        print(f"Error getting minimum window size: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/get-camera-models', methods=['GET'])
def get_camera_models():
    """Get available camera models from the project"""
    try:
        # Use the API method which correctly gets full model names (e.g., 'Survey3W_OCN')
        models = api.get_camera_models()
        # print(f"[API] /api/get-camera-models returning: {models}")
        return jsonify(models)
    except Exception as e:
        print(f"Error getting camera models: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/get-config', methods=['GET'])
def get_config():
    """Get the current project's configuration"""
    try:
        config = api.get_config()
        if config is None:
            return jsonify({'success': False, 'error': 'No project loaded'}), 404
        return jsonify({'success': True, 'config': config})
    except Exception as e:
        print(f"Error getting config: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/set-config', methods=['POST'])
def set_config():
    """Set a configuration value in the current project"""
    try:
        data = request.get_json()
        path = data.get('path', [])
        value = data.get('value')
        
        if not path:
            return jsonify({'error': 'No path provided'}), 400
        
        # Call the API's set_config method
        api.set_config(path, value)
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error setting config: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/update-project-config', methods=['POST'])
def update_project_config():
    """Update project configuration with full config object (CLI compatibility)"""
    try:
        if not api.project:
            return jsonify({'success': False, 'error': 'No project loaded'}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No configuration data provided'}), 400
        
        print(f"[UPDATE-PROJECT-CONFIG] Received config update: {list(data.keys())}", flush=True)
        
        # Merge the provided config with existing project config
        project_settings = data.get('Project Settings', {})
        
        for section, settings in project_settings.items():
            if isinstance(settings, dict):
                for key, value in settings.items():
                    # Build the path for set_config as dot-separated string
                    # CRITICAL FIX: set_config expects string, not list
                    path_string = f"Project Settings.{section}.{key}"
                    try:
                        api.project.set_config(path_string, value)
                        print(f"[UPDATE-PROJECT-CONFIG] Set {section}/{key} = {value}", flush=True)
                    except Exception as e:
                        print(f"[UPDATE-PROJECT-CONFIG] Warning: Could not set {path_string}: {e}", flush=True)
        
        # Save the project to persist changes
        api.project.write()
        print(f"[UPDATE-PROJECT-CONFIG] Project config saved", flush=True)
        
        return jsonify({'success': True, 'message': 'Configuration updated'})
    except Exception as e:
        print(f"[UPDATE-PROJECT-CONFIG] Error: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/get-working-directory', methods=['GET'])
def get_working_directory():
    """Get the current working directory for projects"""
    try:
        working_dir = api.get_working_directory()
        return jsonify({'success': True, 'path': working_dir})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/set-working-directory', methods=['POST'])
def set_working_directory():
    """Set the working directory for projects"""
    try:
        data = request.get_json()
        path = data.get('path')

        if not path:
            return jsonify({'success': False, 'error': 'No path provided'}), 400

        api.set_working_directory(path)
        return jsonify({'success': True, 'path': path})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/move-project', methods=['POST'])
def move_project():
    """Move the current project to a new working directory"""
    try:
        data = request.get_json()
        new_path = data.get('path')
        
        if not new_path:
            return jsonify({'success': False, 'error': 'No path provided'}), 400
        
        result = api.move_project_to_new_directory(new_path)
        return jsonify(result)
    except Exception as e:
        print(f"[MOVE-PROJECT] Error: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/browse-folders', methods=['POST'])
def browse_folders():
    """Browse folders on the server for working directory selection"""
    try:
        from pathlib import Path
        
        data = request.get_json()
        current_path = data.get('path', str(Path.home()))
        
        # Validate and normalize path
        try:
            browse_path = Path(current_path).resolve()
            if not browse_path.exists() or not browse_path.is_dir():
                browse_path = Path.home()
        except:
            browse_path = Path.home()
        
        # Get folders in current directory
        folders = []
        try:
            for item in sorted(browse_path.iterdir()):
                if item.is_dir():
                    try:
                        # Only include accessible directories
                        list(item.iterdir())  # Test access
                        folders.append({
                            'name': item.name,
                            'path': str(item)
                        })
                    except (PermissionError, OSError):
                        # Skip inaccessible folders
                        pass
        except Exception as e:
            print(f"[BROWSE-FOLDERS] Error listing {browse_path}: {e}", flush=True)
        
        # Get parent folder
        parent = str(browse_path.parent) if browse_path.parent != browse_path else None
        
        # Get common locations
        common_locations = []
        for name, path_str in [
            ('Home', str(Path.home())),
            ('Documents', str(Path.home() / 'Documents')),
            ('Desktop', str(Path.home() / 'Desktop')),
            ('C:\\', 'C:\\'),
            ('D:\\', 'D:\\'),
        ]:
            p = Path(path_str)
            if p.exists() and p.is_dir():
                common_locations.append({'name': name, 'path': path_str})
        
        return jsonify({
            'success': True,
            'current_path': str(browse_path),
            'parent': parent,
            'folders': folders[:100],  # Limit to first 100 folders
            'common_locations': common_locations
        })
        
    except Exception as e:
        print(f"[BROWSE-FOLDERS] Error: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/resolve-working-directory', methods=['POST'])
def resolve_working_directory():
    """
    Resolve working directory from browser folder picker.
    The browser sends a file from the selected folder, and we use it to determine the path.
    """
    try:
        folder_name = request.form.get('folder_name', '')
        relative_path = request.form.get('relative_path', '')
        
        print(f"[RESOLVE-WORKING-DIR] Folder name: {folder_name}, Relative path: {relative_path}", flush=True)
        
        # Try to find this folder in common locations
        import os
        from pathlib import Path
        
        # Common base paths to search
        home = str(Path.home())
        search_paths = [
            home,
            os.path.join(home, 'Documents'),
            os.path.join(home, 'Desktop'),
            os.path.join(home, 'Downloads'),
            'C:\\',
            'D:\\',
            'E:\\',
        ]
        
        # Also add current working directory and its parents
        cwd = os.getcwd()
        search_paths.insert(0, cwd)
        search_paths.insert(1, os.path.dirname(cwd))
        
        # Search for the folder
        found_path = None
        for base_path in search_paths:
            potential_path = os.path.join(base_path, folder_name)
            if os.path.isdir(potential_path):
                found_path = potential_path
                print(f"[RESOLVE-WORKING-DIR] Found folder at: {found_path}", flush=True)
                break
        
        if found_path:
            # Set the working directory
            api.set_working_directory(found_path)
            return jsonify({'success': True, 'path': found_path})
        else:
            # Couldn't find automatically, return suggested path for user confirmation
            suggested = os.path.join(home, folder_name)
            print(f"[RESOLVE-WORKING-DIR] Could not find folder, suggesting: {suggested}", flush=True)
            return jsonify({
                'success': False, 
                'message': 'Could not automatically find folder path',
                'suggested_path': suggested
            })
            
    except Exception as e:
        print(f"[RESOLVE-WORKING-DIR] Error: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/select-working-directory-dialog', methods=['POST'])
def select_working_directory_dialog():
    """Open a folder selection dialog for working directory"""
    try:
        print("[SELECT-WORKING-DIR] Starting folder dialog...", flush=True)
        
        import tkinter as tk
        from tkinter import filedialog
        
        # Create a hidden root window
        root = tk.Tk()
        root.withdraw()
        
        # Set the corn logo icon for the dialog
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            icon_path = os.path.join(script_dir, 'ui', 'corn_logo_single_256.ico')
            if os.path.exists(icon_path):
                root.iconbitmap(icon_path)
        except Exception as icon_err:
            print(f"[SELECT-WORKING-DIR] Could not set icon: {icon_err}", flush=True)
        
        # Windows-specific: Make dialog appear on top
        root.attributes('-topmost', True)
        root.update()
        root.lift()
        root.focus_force()
        root.update_idletasks()
        
        # Get current working directory as default
        current_dir = None
        try:
            current_dir = api.get_working_directory()
        except:
            pass
        
        print("[SELECT-WORKING-DIR] Opening folder dialog...", flush=True)
        
        # Open folder dialog with correct title for working directory
        folder_path = filedialog.askdirectory(
            parent=root,
            title='Select Working Directory',
            initialdir=current_dir
        )
        
        # Cleanup
        root.destroy()
        
        print(f"[SELECT-WORKING-DIR] Selected folder: {folder_path}", flush=True)
        
        if not folder_path:
            return jsonify({'success': False, 'message': 'No folder selected'})
        
        return jsonify({'success': True, 'folder': folder_path})
    except Exception as e:
        print(f"[SELECT-WORKING-DIR] Error: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/get-autothreshold', methods=['POST'])
def get_autothreshold():
    """Get auto-calculated thresholds for a vegetation index"""
    try:
        data = request.get_json()
        image = data.get('image', '')
        index = data.get('index', 'NDVI')
        
        # Call the API's get_autothreshold method
        thresholds = api.get_autothreshold(image, index)
        return jsonify({'thresholds': thresholds})
    except Exception as e:
        print(f"Error getting autothreshold: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/latexify', methods=['POST'])
def latexify():
    """Convert a mathematical formula to LaTeX format"""
    try:
        data = request.get_json()
        formula = data.get('formula', '')
        
        if not formula:
            return jsonify({'error': 'No formula provided'}), 400
        
        # Call the API's latexify method
        latex_result = api.latexify(formula)
        return jsonify({'latex': latex_result})
    except Exception as e:
        print(f"Error latexifying formula: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/sync-login-state', methods=['POST'])
def sync_login_state():
    """Sync frontend login state with backend (fixes login-before-backend-ready race condition)"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Call the API's sync method
        result = api.sync_frontend_login_state(data)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user-logout', methods=['POST'])
@app.route('/api/logout', methods=['POST'])
def user_logout():
    """
    Handle user logout and clear session
    
    SECURITY: Stop heartbeat, clear cache
    """
    try:
        if AUTH_ENABLED and auth_middleware:
            # SECURITY: Stop heartbeat and concurrent checks on logout
            auth_middleware._stop_heartbeat()
            auth_middleware._stop_periodic_concurrent_checks()
            auth_middleware.current_user_token = None
            auth_middleware.current_user_email = None
            
            data = request.get_json() or {}
            email = data.get('email')
            
            # SECURITY: Clear cached license if email provided
            if email:
                auth_middleware.license_cache.clear_cache(email)
        
        api.user_logout()
        return jsonify({
            'success': True,
            'message': 'User logged out successfully'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/get-session-info', methods=['GET'])
def get_session_info():
    """Get current backend session information"""
    try:
        session_info = api.get_user_session_info()
        return jsonify(session_info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/get-thread-4-progress', methods=['GET'])
def get_thread_4_progress():
    """Get Thread 4 (export) progress percentage
    
    Returns:
        JSON with:
        - percent: 0-100 progress percentage
        - phase: Current phase name (e.g., "Exporting")
        - timeRemaining: Time/count remaining (e.g., "45/100")
        - isActive: Whether thread is currently active
    """
    try:
        # Get Thread 4 progress from API's premium thread state
        if hasattr(api, '_premium_thread_state') and 4 in api._premium_thread_state:
            thread_4_state = api._premium_thread_state[4]
            return jsonify({
                'success': True,
                'percent': thread_4_state.get('percentComplete', 0),
                'phase': thread_4_state.get('phaseName', 'Exporting'),
                'timeRemaining': thread_4_state.get('timeRemaining', ''),
                'isActive': thread_4_state.get('isActive', False)
            })
        else:
            # Thread 4 not initialized yet or not in parallel mode
            return jsonify({
                'success': True,
                'percent': 0,
                'phase': 'Not Started',
                'timeRemaining': '',
                'isActive': False
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def main():
    """Main entry point for backend server"""
    # SECURITY: Instance protection - prevent multiple instances
    # This is done in main() to avoid conflicts with Ray worker processes
    # CRITICAL: Can be disabled via environment variable for debugging/safe mode
    global instance_protection
    
    # Check if safe mode is enabled (disables instance protection and auth checks)
    safe_mode = os.environ.get('CHLOROS_SAFE_MODE', '').lower() in ('1', 'true', 'yes')
    disable_instance_protection = os.environ.get('CHLOROS_DISABLE_INSTANCE_PROTECTION', '').lower() in ('1', 'true', 'yes')
    
    if safe_mode:
        instance_protection = None
    elif disable_instance_protection:
        instance_protection = None
    else:
        try:
            from instance_protection import get_instance_protection
            instance_protection = get_instance_protection(lock_port=5000, app_name='chloros-backend')
            
            # Acquire instance lock
            lock_success, lock_error = instance_protection.acquire_instance_lock()
            if not lock_success:
                print(f"❌ ERROR: Another instance is already running. Exiting.")
                print(f"To bypass this check, set CHLOROS_DISABLE_INSTANCE_PROTECTION=1")
                sys.exit(1)
            
            # Check for concurrent instances
            has_concurrent, concurrent_count, concurrent_pids = instance_protection.detect_concurrent_instances()
            if has_concurrent and not instance_protection.cloud_mode:
                print(f"⚠️ WARNING: {concurrent_count} concurrent Chloros process(es) detected")
            
            # Log environment warnings
            env_info = instance_protection.get_environment_info()
            if env_info['is_containerized']:
                print(f"⚠️ WARNING: Running in containerized environment")
            if env_info['is_virtual_machine']:
                print(f"⚠️ WARNING: Running in virtual machine")
                
        except ImportError as e:
            print(f"⚠️ WARNING: Instance protection not available: {e}")
            instance_protection = None
        except Exception as e:
            print(f"❌ ERROR: Instance protection error: {e}")
            import traceback
            traceback.print_exc()
            instance_protection = None
    
    print("Starting Chloros Backend Server...")
    print("   Port: 5000")
    print("=" * 50)
    sys.stdout.flush()
    
    # IMPORTANT: Use Flask's built-in server (same as GUI version)
    # Note: The werkzeug logger was already disabled earlier in the code
    # Browser mode log file endpoint
    @app.route('/api/get-log-file-path', methods=['GET'])
    def get_log_file_path():
        """Get the path to the current backend log file"""
        try:
            return jsonify({
                'success': True,
                'logFile': log_file,
                'logDir': log_dir
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/open-log-file', methods=['POST'])
    def open_log_file():
        """Open/download the log file"""
        try:
            # In browser mode, we can't open files on the client machine
            # So we'll return the log file path for display
            return jsonify({
                'success': True, 
                'message': 'Log file path retrieved',
                'logFile': log_file,
                'logDir': log_dir
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/download-log-file', methods=['GET'])
    def download_log_file():
        """Download the current log file"""
        try:
            # CRITICAL: Flush all logs to disk WITHOUT closing (threads need the file handles!)
            import time
            import os
            
            # Get the ACTUAL current log file path from stdout (not the stale global variable)
            current_log_file = log_file  # Default to global
            if hasattr(sys.stdout, 'log_file_path'):
                current_log_file = sys.stdout.log_file_path
            
            # Flush stdout log file
            if hasattr(sys.stdout, 'lock') and hasattr(sys.stdout, 'log'):
                try:
                    with sys.stdout.lock:
                        sys.stdout.log.flush()
                        os.fsync(sys.stdout.log.fileno())
                except:
                    pass
            
            # Flush stderr log file
            if hasattr(sys.stderr, 'lock') and hasattr(sys.stderr, 'log'):
                try:
                    with sys.stderr.lock:
                        sys.stderr.log.flush()
                        os.fsync(sys.stderr.log.fileno())
                except:
                    pass
            
            # Wait for OS to finish writing
            time.sleep(0.2)
            
            # Read the log file contents directly to ensure we get the most recent data
            try:
                with open(current_log_file, 'r', encoding='utf-8', buffering=1) as f:
                    log_contents = f.read()
                
                # Create a temporary in-memory file with the contents
                from io import BytesIO
                log_bytes = BytesIO(log_contents.encode('utf-8'))
                log_bytes.seek(0)
                
                from flask import send_file
                return send_file(
                    log_bytes,
                    as_attachment=True,
                    download_name=f'chloros-backend-{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.log',
                    mimetype='text/plain'
                )
            except Exception as read_error:
                # Fallback to direct file send if reading fails
                from flask import send_file
                return send_file(
                    current_log_file,
                    as_attachment=True,
                    download_name=f'chloros-backend-{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.log',
                    mimetype='text/plain'
                )
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    # Determine host binding based on environment
    cloud_mode = os.environ.get('CHLOROS_CLOUD_MODE', '').lower() in ('1', 'true', 'yes')
    
    if cloud_mode:
        # CLOUD MODE: Use werkzeug directly for better control on Windows Server
        server_host = '0.0.0.0'
        server_port = 5000
        
        try:
            from werkzeug.serving import make_server
            server = make_server(server_host, server_port, app, threaded=True)
            print(f"[SERVER] Server ready and listening on {server_host}:{server_port}", flush=True)
            sys.stdout.flush()
            server.serve_forever()
        except Exception as e:
            print(f"❌ ERROR: Server failed: {e}", flush=True)
            import traceback
            traceback.print_exc()
            sys.exit(1)
    else:
        # DESKTOP MODE: Use Waitress for production-ready WSGI server
        server_host = 'localhost'
        
        try:
            from waitress import serve
            sys.stdout.flush()
            serve(app, host=server_host, port=5000, threads=6, channel_timeout=300)
        except Exception as e:
            print(f"❌ ERROR: Waitress failed to start: {e}", flush=True)
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == '__main__':
    main()
