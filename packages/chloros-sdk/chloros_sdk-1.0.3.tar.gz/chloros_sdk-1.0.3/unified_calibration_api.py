# =============================================================================
# UNIFIED CALIBRATION DATA MANAGEMENT API
# =============================================================================

import os
import json
import datetime
import threading
import time
import queue
import signal

class TimeoutError(Exception):
    """Custom timeout exception for file operations."""
    pass

class UnifiedCalibrationManager:
    """
    Unified calibration data management API that consolidates all save/load operations.
    
    This replaces the multiple scattered calibration save/load functions with a single,
    consistent interface that works across all processing modes.
    """
    
    # Class-level priority-based locking system
    _file_locks = {}
    _locks_lock = threading.Lock()
    
    @staticmethod
    def _timeout_handler(signum, frame):
        """Signal handler for file operation timeouts."""
        raise TimeoutError("File operation timed out")
    
    @staticmethod
    def _with_timeout(func, timeout_seconds=10):
        """Execute a function with a timeout (Windows compatible)."""
        if os.name == 'nt':  # Windows - use threading timeout
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(func)
                try:
                    return future.result(timeout=timeout_seconds)
                except concurrent.futures.TimeoutError:
                    raise TimeoutError(f"Operation timed out after {timeout_seconds} seconds")
        else:  # Unix/Linux - use signal timeout
            old_handler = signal.signal(signal.SIGALRM, UnifiedCalibrationManager._timeout_handler)
            signal.alarm(timeout_seconds)
            try:
                result = func()
                signal.alarm(0)  # Cancel alarm
                return result
            except TimeoutError:
                raise
            finally:
                signal.signal(signal.SIGALRM, old_handler)
                signal.alarm(0)
    
    @staticmethod
    def _get_thread_priority():
        """Get priority for current thread (lower number = higher priority)."""
        thread_name = threading.current_thread().name
        
        # Extract thread number from thread name patterns
        if 'Thread-1' in thread_name or 'THREAD-1' in thread_name:
            return 1
        elif 'Thread-2' in thread_name or 'THREAD-2' in thread_name:
            return 2
        elif 'Thread-3' in thread_name or 'THREAD-3' in thread_name:
            return 3
        elif 'Thread-4' in thread_name or 'THREAD-4' in thread_name:
            return 4
        else:
            # Unknown threads get lowest priority
            return 99
    
    @staticmethod
    def _get_file_lock(file_path):
        """Get or create a priority-based lock for a specific file path."""
        with UnifiedCalibrationManager._locks_lock:
            if file_path not in UnifiedCalibrationManager._file_locks:
                UnifiedCalibrationManager._file_locks[file_path] = UnifiedCalibrationManager.PriorityLock()
            return UnifiedCalibrationManager._file_locks[file_path]
    
    class PriorityLock:
        """A lock that gives priority to lower-numbered threads."""
        
        def __init__(self):
            self._lock = threading.Lock()
            self._waiting_queue = queue.PriorityQueue()
            self._current_holder = None
            self._queue_lock = threading.Lock()
        
        def __enter__(self):
            self.acquire()
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            self.release()
        
        def acquire(self, timeout=30.0):
            thread_priority = UnifiedCalibrationManager._get_thread_priority()
            thread_name = threading.current_thread().name
            start_time = time.time()
            
            with self._queue_lock:
                # If no one is holding the lock, acquire immediately
                if self._current_holder is None and self._waiting_queue.empty():
                    if self._lock.acquire(blocking=False):
                        self._current_holder = thread_name

                        return
                
                # Add to priority queue (priority, timestamp for tie-breaking, thread info)
                entry = (thread_priority, time.time(), thread_name, threading.current_thread())
                self._waiting_queue.put(entry)

            
            # Wait for our turn based on priority
            while time.time() - start_time < timeout:
                with self._queue_lock:
                    if not self._waiting_queue.empty():
                        # Check if we're next in line (highest priority)
                        queue_items = list(self._waiting_queue.queue)
                        queue_items.sort()  # Sort by priority (lower number = higher priority)
                        
                        if queue_items and queue_items[0][3] == threading.current_thread():
                            # Our turn - try to acquire
                            if self._lock.acquire(blocking=False):
                                # Remove ourselves from queue
                                temp_queue = queue.PriorityQueue()
                                while not self._waiting_queue.empty():
                                    item = self._waiting_queue.get()
                                    if item[3] != threading.current_thread():
                                        temp_queue.put(item)
                                self._waiting_queue = temp_queue
                                
                                self._current_holder = thread_name

                                return
                
                # Brief sleep to avoid busy waiting
                time.sleep(0.001)
            
            # Timeout - remove ourselves from queue and raise exception
            with self._queue_lock:
                temp_queue = queue.PriorityQueue()
                while not self._waiting_queue.empty():
                    item = self._waiting_queue.get()
                    if item[3] != threading.current_thread():
                        temp_queue.put(item)
                self._waiting_queue = temp_queue
            
            raise TimeoutError(f"[PRIORITY_LOCK] ❌ {thread_name} (priority {thread_priority}) timeout after {timeout}s waiting for lock")
        
        def release(self):
            thread_name = threading.current_thread().name
            thread_priority = UnifiedCalibrationManager._get_thread_priority()
            
            with self._queue_lock:
                self._current_holder = None

            
            self._lock.release()
    
    @staticmethod
    def _load_json_with_repair(file_handle, file_path):
        """
        Load JSON with automatic repair for common corruption issues.
        
        Handles "Extra data" errors by attempting to extract valid JSON objects.
        
        Args:
            file_handle: Open file handle
            file_path: File path for logging
            
        Returns:
            dict: Parsed JSON data or empty dict if repair fails
        """
        try:
            # First, try normal JSON loading
            file_handle.seek(0)
            return json.load(file_handle)
            
        except json.JSONDecodeError as e:

            
            # Handle "Extra data" error by attempting to extract valid JSON
            if "Extra data" in str(e):
                try:
                    file_handle.seek(0)
                    content = file_handle.read()

                    
                    # Try to find the end of the first valid JSON object
                    decoder = json.JSONDecoder()
                    try:
                        # This will parse the first valid JSON object and tell us where it ends
                        obj, idx = decoder.raw_decode(content)

                        
                        # Create backup of corrupted file
                        backup_path = file_path + '.corrupted.backup'
                        with open(backup_path, 'w') as backup:
                            backup.write(content)

                        
                        # Save repaired JSON
                        with open(file_path, 'w') as repaired:
                            json.dump(obj, repaired, indent=2)
                            repaired.flush()
                            os.fsync(repaired.fileno())

                        
                        return obj
                        
                    except (json.JSONDecodeError, ValueError) as repair_error:
                        pass  # JSON repair failed
                        
                except Exception as repair_exception:
                    pass  # JSON repair process failed
            
            # If repair fails, return empty dict to allow processing to continue
            return {}
            
        except Exception as e:

            return {}
    
    @staticmethod
    def save_calibration_data(image, calibration_data, project_dir=None):
        """
        Unified function to save calibration data to project's calibration_data.json
        
        Args:
            image: LabImage object with calibration data
            calibration_data: Dict containing calibration coefficients, xvals, etc.
            project_dir: Project directory path (auto-detected if None)
            
        Returns:
            bool: True if successful, False otherwise
        """
        from tasks import to_serializable
        
        # Auto-detect project directory if not provided
        if project_dir is None:
            project_dir = getattr(image, 'project_path', None) or getattr(getattr(image, 'project', None), 'fp', None)
            if not project_dir:

                return False
        
        # Get image metadata
        timestamp = getattr(image, 'timestamp', None) or getattr(image, 'capture_time', None) or getattr(image, 'fn', None)
        if hasattr(timestamp, 'strftime'):
            timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        else:
            timestamp_str = str(timestamp) if timestamp else None
        
        # Extract camera model and filter with fallback logic
        camera_model = getattr(image, 'camera_model', None)
        camera_filter = getattr(image, 'camera_filter', None)
        
        # CRITICAL FIX: If camera_model is 'Unknown', try to extract from Model attribute
        if camera_model == 'Unknown' or camera_model is None:
            model_from_exif = getattr(image, 'Model', None)
            
            # Parse the full model name (e.g., "Survey3W_OCN") 
            if model_from_exif and model_from_exif != 'Unknown':
                if '_' in model_from_exif:
                    # Full format like "Survey3W_OCN"
                    model_parts = model_from_exif.split('_')
                    camera_model = model_parts[0]  # "Survey3W"
                    if camera_filter == 'Unknown' or camera_filter is None:
                        camera_filter = model_parts[1]  # "OCN"
                else:
                    # Partial format like just "Survey3W" - this shouldn't happen but handle it
                    camera_model = model_from_exif

        
        # Prepare calibration entry with standardized field names
        calib_entry = {
            'timestamp': timestamp_str,
            'filename': getattr(image, 'fn', None),
            'camera_model': camera_model,
            'camera_filter': camera_filter,
            'coefficients': calibration_data.get('coefficients'),
            'limits': calibration_data.get('limits'),
            'xvals': calibration_data.get('xvals'),
            'yvals': calibration_data.get('yvals'),
            'als_magnitude': calibration_data.get('als_magnitude'),
            'als_data': calibration_data.get('als_data'),
            'aruco_id': calibration_data.get('aruco_id'),
            'aruco_corners': calibration_data.get('aruco_corners'),
            'red_square_corners': calibration_data.get('target_polys'),
            'cluster_value': calibration_data.get('cluster_value'),
            'is_selected_for_calibration': calibration_data.get('is_selected_for_calibration', False)
        }
        
        # Load existing data and add new entry with file locking to prevent corruption
        calibration_file = os.path.join(project_dir, 'calibration_data.json')
        file_lock = UnifiedCalibrationManager._get_file_lock(calibration_file)
        
        try:
            with file_lock:
                thread_priority = UnifiedCalibrationManager._get_thread_priority()
                thread_name = threading.current_thread().name

                
                try:
                    # Enhanced concurrent-safe JSON loading with retry mechanism
                    max_read_attempts = 5
                    read_delay = 0.1
                    calib_data = {}
                    
                    for read_attempt in range(max_read_attempts):
                        try:
                            if os.path.exists(calibration_file):
                                def read_json_file():
                                    with open(calibration_file, 'r') as f:
                                        return UnifiedCalibrationManager._load_json_with_repair(f, calibration_file)
                                
                                calib_data = UnifiedCalibrationManager._with_timeout(read_json_file, timeout_seconds=10)
                                break
                            else:
                                calib_data = {}
                                break
                                
                        except (TimeoutError, json.JSONDecodeError, IOError) as e:
                            if read_attempt == max_read_attempts - 1:
                                calib_data = {}
                                break
                            else:
                                time.sleep(read_delay)
                    
                    # Validate that we have a proper dictionary
                    if not isinstance(calib_data, dict):
                        calib_data = {}
                    
                    # Use timestamp as key with collision handling
                    original_timestamp = timestamp_str
                    collision_counter = 0
                    
                    # Handle timestamp collisions by adding suffix
                    while timestamp_str in calib_data:
                        collision_counter += 1
                        timestamp_str = f"{original_timestamp}_{collision_counter}"
                    
                    # Try to serialize - handle missing to_serializable function
                    try:
                        serialized_entry = to_serializable(calib_entry)
                    except NameError as e:
                        serialized_entry = calib_entry
                    except Exception as e:
                        serialized_entry = calib_entry
                    
                    # Add the new entry
                    calib_data[timestamp_str] = serialized_entry
                    
                    # Enhanced atomic write with validation
                    temp_file = calibration_file + f'.tmp.{thread_priority}_{int(time.time() * 1000)}'  # Unique temp file per process
                    
                    # Write with timeout protection and validation
                    def write_json_file():
                        with open(temp_file, 'w') as f:
                            json.dump(calib_data, f, indent=2)
                            f.flush()
                            os.fsync(f.fileno())
                        
                        # Validate the written file
                        with open(temp_file, 'r') as f:
                            test_data = json.load(f)
                            if len(test_data) != len(calib_data):
                                raise ValueError(f"Written data length mismatch: expected {len(calib_data)}, got {len(test_data)}")
                    
                    try:
                        UnifiedCalibrationManager._with_timeout(write_json_file, timeout_seconds=15)
                    except TimeoutError as te:
                        if os.path.exists(temp_file):
                            os.remove(temp_file)
                        raise te
                    except Exception as e:
                        if os.path.exists(temp_file):
                            os.remove(temp_file)
                        raise e
                    
                    # Enhanced atomic rename with retry mechanism
                    max_rename_attempts = 3
                    rename_delay = 0.05
                    
                    for rename_attempt in range(max_rename_attempts):
                        try:
                            def atomic_rename():
                                if os.name == 'nt':  # Windows
                                    if os.path.exists(calibration_file):
                                        backup_file = calibration_file + '.backup'
                                        if os.path.exists(backup_file):
                                            os.remove(backup_file)
                                        os.rename(calibration_file, backup_file)
                                    os.rename(temp_file, calibration_file)
                                    # Remove backup after successful rename
                                    backup_file = calibration_file + '.backup'
                                    if os.path.exists(backup_file):
                                        os.remove(backup_file)
                                else:  # Unix/Linux
                                    os.rename(temp_file, calibration_file)
                            
                            UnifiedCalibrationManager._with_timeout(atomic_rename, timeout_seconds=10)
                            break
                            
                        except Exception as e:
                            if rename_attempt == max_rename_attempts - 1:
                                if os.path.exists(temp_file):
                                    os.remove(temp_file)
                                raise e
                            else:
                                time.sleep(rename_delay)
                    
                    return True
                    
                except Exception as inner_e:
                    # Clean up temp file if it exists
                    temp_file = calibration_file + '.tmp'
                    if os.path.exists(temp_file):
                        try:
                            os.remove(temp_file)
                            print(f"[UNIFIED_CALIB] 🧹 Cleaned up temp file: {temp_file}")
                        except Exception as cleanup_e:
                            print(f"[UNIFIED_CALIB] ⚠️ Failed to cleanup temp file {temp_file}: {cleanup_e}")
                    raise inner_e
            
        except Exception as e:
            print(f"[UNIFIED_CALIB] ❌ Error saving calibration data: {e}")
            # Clean up temp file if it exists
            temp_file = calibration_file + '.tmp'
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception:
                    pass
            return False
    
    @staticmethod
    def load_calibration_data(image, project_dir=None):
        """
        Unified function to load calibration data from project's calibration_data.json
        
        Args:
            image: LabImage object to find calibration data for
            project_dir: Project directory path (auto-detected if None)
            
        Returns:
            dict: Calibration data or empty dict if not found
        """
        # Auto-detect project directory if not provided
        if project_dir is None:
            project_dir = getattr(image, 'project_path', None) or getattr(getattr(image, 'project', None), 'fp', None)
            if not project_dir:
                return {}
        
        calibration_file = os.path.join(project_dir, 'calibration_data.json')
        if not os.path.exists(calibration_file):
            return {}
        
        file_lock = UnifiedCalibrationManager._get_file_lock(calibration_file)
        
        try:
            with file_lock:
                with open(calibration_file, 'r') as f:
                    calib_data = UnifiedCalibrationManager._load_json_with_repair(f, calibration_file)
            
            # Find best matching calibration entry
            chosen_key = UnifiedCalibrationManager._find_best_calibration_match(image, calib_data)
            if chosen_key:
                entry = calib_data[chosen_key]
                
                # VALIDATION: Check if loaded data contains string placeholders
                coefficients = entry.get('coefficients')
                xvals = entry.get('xvals')
                yvals = entry.get('yvals')
                limits = entry.get('limits')
                
                if (isinstance(coefficients, str) or isinstance(xvals, str) or isinstance(yvals, str) or isinstance(limits, str)):
                    return {}
                
                return {
                    'coefficients': entry.get('coefficients'),
                    'limits': entry.get('limits'),
                    'xvals': entry.get('xvals'),
                    'yvals': entry.get('yvals'),
                    'aruco_id': entry.get('aruco_id'),
                    'als_magnitude': entry.get('als_magnitude'),
                    'als_data': entry.get('als_data'),
                    'target_polys': entry.get('red_square_corners'),
                    'cluster_value': entry.get('cluster_value'),
                    'is_selected_for_calibration': entry.get('is_selected_for_calibration', False)
                }
            else:
                return {}
                
        except Exception as e:
            return {}
    
    @staticmethod
    def apply_calibration_to_image(image, project_dir=None):
        """
        Unified function to load and apply calibration data to an image
        
        Args:
            image: LabImage object to apply calibration data to
            project_dir: Project directory path (auto-detected if None)
            
        Returns:
            bool: True if calibration data was found and applied, False otherwise
        """
        calib_data = UnifiedCalibrationManager.load_calibration_data(image, project_dir)
        if not calib_data:
            return False
        
        # Apply calibration data to image with validation to prevent string placeholders
        def validate_and_apply(value, field_name, attr_name):
            """Validate that calibration values are not string placeholders before applying"""
            if isinstance(value, str):
                return False
            setattr(image, attr_name, value)
            return True
        
        if calib_data.get('coefficients'):
            validate_and_apply(calib_data['coefficients'], 'coefficients', 'calibration_coefficients')
        if calib_data.get('limits'):
            validate_and_apply(calib_data['limits'], 'limits', 'calibration_limits')
        if calib_data.get('xvals'):
            validate_and_apply(calib_data['xvals'], 'xvals', 'calibration_xvals')
        if calib_data.get('yvals'):
            validate_and_apply(calib_data['yvals'], 'yvals', 'calibration_yvals')
        if calib_data.get('aruco_id'):
            image.aruco_id = calib_data['aruco_id']
        if calib_data.get('als_magnitude'):
            image.als_magnitude = calib_data['als_magnitude']
        if calib_data.get('als_data'):
            image.als_data = calib_data['als_data']
        if calib_data.get('target_polys'):
            image.calibration_target_polys = calib_data['target_polys']
        if calib_data.get('cluster_value'):
            image.cluster_value = calib_data['cluster_value']
        if 'is_selected_for_calibration' in calib_data:
            image.is_selected_for_calibration = calib_data['is_selected_for_calibration']
        
        return True
    
    @staticmethod
    def _find_best_calibration_match(image, calib_data):
        """Find the best matching calibration entry for an image."""
        img_timestamp = getattr(image, 'timestamp', None) or getattr(image, 'capture_time', None)
        img_camera_model = getattr(image, 'camera_model', None)
        img_camera_filter = getattr(image, 'camera_filter', None)
        img_filename = getattr(image, 'fn', None)
        
        # Convert timestamp to string for matching
        if hasattr(img_timestamp, 'strftime'):
            timestamp_str = img_timestamp.strftime('%Y-%m-%d %H:%M:%S')
        else:
            timestamp_str = str(img_timestamp) if img_timestamp else None
        
        best_key = None
        fallback_key = None
        camera_match_key = None
        
        for key, entry in calib_data.items():
            entry_camera_model = entry.get('camera_model')
            entry_camera_filter = entry.get('camera_filter')
            entry_filename = entry.get('filename')
            
            # Try exact timestamp match first
            if timestamp_str and key == timestamp_str:
                best_key = key
                break
            
            # Try filename match (high priority)
            if entry_filename == img_filename:
                best_key = key
                break
            
            # Exact camera model and filter match
            if (entry_camera_model == img_camera_model and 
                entry_camera_filter == img_camera_filter):
                camera_match_key = key
            
            # CRITICAL FIX: Handle Survey3W/Survey3N variations
            # Survey3W and Survey3N are essentially the same camera with different filters
            if (img_camera_model in ['Survey3W', 'Survey3N'] and 
                entry_camera_model in ['Survey3W', 'Survey3N'] and
                entry_camera_filter == img_camera_filter):
                fallback_key = key
            
            # Even broader fallback - any Survey3 with any filter if desperate
            if (img_camera_model in ['Survey3W', 'Survey3N'] and 
                entry_camera_model in ['Survey3W', 'Survey3N'] and
                not fallback_key):
                fallback_key = key
        
        result_key = best_key or camera_match_key or fallback_key
        return result_key
