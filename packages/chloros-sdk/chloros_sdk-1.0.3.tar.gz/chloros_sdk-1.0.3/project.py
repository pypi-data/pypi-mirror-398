import json
from copy import deepcopy
import json
import os
from pathlib import Path
import datetime
import cv2
import numpy as np
from PIL import Image
from mip.debayer import debayer_HighQuality, debayer_MaximumQuality
import time
from PIL.ExifTags import TAGS
import glob
import re

# Import debug utilities for controlled logging
try:
    from debug_utils import debug_project, debug_error, debug_verbose, debug_normal
except ImportError:
    # Fallback if debug_utils not available
    def debug_project(msg): pass
    def debug_error(msg): pass
    def debug_verbose(msg): pass
    def debug_normal(msg): pass

# Custom JSON encoder to handle NumPy types
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.bool_):
            return bool(obj)
        return super(NumpyEncoder, self).default(obj)


DEFAULT_CONFIG={"Project Settings":{"Target Detection":{
      "Minimum calibration sample area (px)": 25,
      "Minimum calibration target squares" : 4,
      "Minimum Target Clustering (0-100)": 60    },"Processing": {
      "Debayer method": "High Quality (Faster)",
      "Minimum recalibration interval" : 0,
      "Vignette correction": True,
      "Reflectance calibration / white balance": True,
      "Apply PPK corrections": False,
      "Light sensor timezone offset": 0
    },
    "Index": {
      "Add index": []
    },    "Export": {
      "Calibrated image format": "TIFF (16-bit)" 
    },
    "UI": {
      "Grid thumbnail size": 160
    },
    "Save Project Template": ""
  },
  "processing_state": {
    "current_stage": "idle",
    "processing_mode": "serial",
    "serial_stages": {
      "target_detection": {
        "completed": False,
        "images_processed": 0,
        "total_images": 0,
        "completed_images": []
      },
      "image_processing": {
        "completed": False,
        "images_processed": 0,
        "total_images": 0,
        "completed_images": [],
        "exported_images": []
      }
    },
    "parallel_threads": {
      "thread_1_target_detection": {
        "completed": False,
        "images_processed": 0,
        "total_images": 0,
        "completed_images": []
      },
      "thread_2_calibration": {
        "completed": False,
        "images_processed": 0,
        "total_images": 0,
        "completed_images": []
      },
      "thread_3_processing": {
        "completed": False,
        "images_processed": 0,
        "total_images": 0,
        "completed_images": []
      },
      "thread_4_export": {
        "completed": False,
        "images_processed": 0,
        "total_images": 0,
        "completed_images": [],
        "exported_images": []
      }
    },
    "last_processed_image_index": -1,
    "completed_images": [],
    "total_images": 0,
    "timestamp": None
  }}
reprocessing_keys={'Target Detection' : ['calibration','index'],
                   'Processing' : ['calibration','index'],
                   'Index' : ['index'],
                   'Export' : ['calibration','index']}

class Project():

    def __init__(self, fp, template=None):
        # Accept either a folder or a file path
        if os.path.isdir(fp):
            self.fp = fp
            self.configpath = os.path.join(fp, 'project.json')
        else:
            # CRITICAL FIX: If a file path is passed, extract directory and construct proper project.json path
            self.fp = os.path.dirname(fp)
            self.configpath = os.path.join(self.fp, 'project.json')
        debug_verbose(f"Project config path: {self.configpath}")
        self.active_viewer_index=None
        self.active_viewer_layer=None
        self.sandbox_image=None
        self.imagemap = {}
        self.scanmap = {}
        self.files = []
        self.filenames = set()
        self.missing_files = []  # Track missing files for error reporting
        
        # Debayered target cache directory
        self._debayer_cache_dir = os.path.join(self.fp, '.debayer_cache')
        self._cached_targets = {}  # Maps RAW filename -> cached TIFF path
        
        # Ensure cache directory exists
        os.makedirs(self._debayer_cache_dir, exist_ok=True)
        
        if template is not None:
            if os.path.exists(template):
                with open(template) as f:
                    self.data = json.load(f)
                
                # Update project metadata for the new project
                import datetime
                self.data['name'] = os.path.basename(self.fp)  # Use new project folder name
                self.data['created'] = datetime.datetime.now().isoformat() + 'Z'
                self.data['files'] = {}  # Ensure files are empty for new project
                self.data['scanmap'] = {}  # Ensure scanmap is empty
                
                # Update Working Directory to current location
                if 'config' in self.data:
                    self.data['config']['Working Directory'] = os.path.dirname(self.fp)
                
                debug_normal(f"Created new project from template: {template}")
                
                self.write()
        elif self.fp is not None and os.path.exists(self.configpath):
            try:
                with open(self.configpath) as f:
                    file_content = f.read()
                    debug_verbose(f"Loaded project.json content ({len(file_content)} chars)")
                    
                    # Check if file is empty or contains only whitespace
                    if not file_content.strip():
                        debug_normal(f"Project file is empty, creating new project")
                        raise ValueError("Empty project file")
                    
                    self.data = json.loads(file_content)
                
                # Ensure config has all required keys from DEFAULT_CONFIG
                self.ensure_complete_config()
                
                # Migrate old preview image structure to new structure
                self.migrate_preview_images()
                
                self.load_files()
            except Exception as e:
                debug_error(f"Failed to load project file: {e}")
                
                # Check if file is actually corrupted or just temporarily locked
                if os.path.exists(self.configpath):
                    file_size = os.path.getsize(self.configpath)
                    if file_size == 0:
                        debug_normal(f"Project file is empty ({file_size} bytes) - likely corrupted")
                    else:
                        debug_normal(f"Project file exists ({file_size} bytes) but failed to load - may be temporary lock issue")
                        # Try to wait and reload once more
                        import time
                        time.sleep(0.1)
                        try:
                            self.load()
                            debug_normal(f"Successfully loaded project file on retry")
                            return  # Success on retry
                        except:
                            debug_normal(f"Retry failed - treating as corrupted")
                
                debug_normal(f"Creating new project file to replace corrupted one")
                
                # Only create backup if file has content
                if os.path.exists(self.configpath) and os.path.getsize(self.configpath) > 0:
                    backup_path = f"{self.configpath}.backup.{int(time.time())}"
                    try:
                        import shutil
                        shutil.copy2(self.configpath, backup_path)
                        debug_verbose(f"Created backup: {os.path.basename(backup_path)}")
                    except Exception as backup_error:
                        debug_error(f"Could not create backup: {backup_error}")
                else:
                    debug_normal(f"Skipping backup of empty/missing project file")
                
                # Create new project data
                # Get project name from folder name
                import datetime
                project_name = os.path.basename(self.fp)
                # Get working directory (parent of project folder)
                working_directory = os.path.dirname(self.fp)
                
                # Create config with Working Directory included
                config = deepcopy(DEFAULT_CONFIG)
                config['Working Directory'] = working_directory
                
                self.data = {
                    'name': project_name,
                    'created': datetime.datetime.now().isoformat() + 'Z',
                    'config': config,
                    'processing_state': {
                        'current_stage': 'idle',
                        'completed_images': [],
                        'total_images': 0,
                        'parallel_threads': {},
                        'parallel_stages': {
                            'target_detection': {'completed': False},
                            'calibration': {'completed': False},
                            'processing': {'completed': False},
                            'export': {'completed': False}
                        },
                        'processing_mode': 'parallel',
                        'last_processed_image_index': -1,
                        'timestamp': None
                    },
                    'scanmap': {},
                    'files': {},
                    'phase_progress': {
                        'calibration': {
                            'completed_images': [],
                            'total_images': 0
                        },
                        'index': {
                            'completed_images': [],
                            'total_images': 0
                        }
                    }
                }
                
                # Migrate old preview image structure to new structure
                self.migrate_preview_images()
                
                self.write()
                debug_project(f"Created new project file")
        else:
            if not os.path.exists(self.configpath):
                # Get project name from folder name
                import datetime
                project_name = os.path.basename(self.fp)
                # Get working directory (parent of project folder)
                working_directory = os.path.dirname(self.fp)
                
                # Create config with Working Directory included
                config = deepcopy(DEFAULT_CONFIG)
                config['Working Directory'] = working_directory
                
                self.data = {
                    'name': project_name,
                    'created': datetime.datetime.now().isoformat() + 'Z',
                    'config': config,
                    'processing_state': {
                        'current_stage': 'idle',
                        'completed_images': [],
                        'total_images': 0,
                        'parallel_threads': {},
                        'parallel_stages': {
                            'target_detection': {'completed': False},
                            'calibration': {'completed': False},
                            'processing': {'completed': False},
                            'export': {'completed': False}
                        },
                        'processing_mode': 'parallel',
                        'last_processed_image_index': -1,
                        'timestamp': None
                    },
                    'scanmap': {},
                    'files': {},
                    'phase_progress': {
                        'calibration': {
                            'completed_images': [],
                            'total_images': 0
                        },
                        'index': {
                            'completed_images': [],
                            'total_images': 0
                        }
                    }
                }
                
                # Ensure preview directories exist
                self.ensure_preview_directories()
                
                self.write()
            else:
                raise RuntimeError(f"Project file {self.configpath} exists but could not be loaded.")
    
    def migrate_preview_images(self):
        """Migrate old preview image structure to new structure (no-op for now)"""
        # This method is called during project loading but migration is no longer needed
        # as we've moved to the new Preview Images structure
        pass
    
    def ensure_preview_directories(self):
        """Ensure Preview Images directories exist for the project"""
        try:
            # Import helper functions from lab.py
            from lab import ensure_preview_dirs
            
            # Ensure preview directories exist
            ensure_preview_dirs(self.fp)
            
            debug_verbose(f"Preview directories ensured for project")
        except Exception as e:
            debug_error(f"Error ensuring preview directories: {e}")
            # Don't fail the project loading if directory creation fails
            pass
    def write(self):
        debug_verbose(f"Writing project data to {self.configpath}")
        # Ensure parent directory exists
        os.makedirs(os.path.dirname(self.configpath), exist_ok=True)
        
        # Add scanmap data to the project data before saving
        scanmap_data = {}
        for scan_filename, scan_obj in self.scanmap.items():
            scanmap_data[scan_filename] = {
                'path': scan_obj.path,
                'Model': getattr(scan_obj, 'Model', 'Light Sensor'),
                'DateTime': getattr(scan_obj, 'DateTime', 'Unknown')
            }
        self.data['scanmap'] = scanmap_data
        debug_verbose(f"Saving {len(scanmap_data)} scan files to project")
        
        # Add calibration data to the project data before saving
        calibration_data = {}
        # Ensure files section exists before accessing it
        if 'files' not in self.data:
            self.data['files'] = {}
        for base, fileset in self.data['files'].items():
            calibration_info = {}
            
            # Check if we have a JPG file and get its calibration status (JPG takes priority for calibration detection)
            if fileset.get('jpg'):
                jpg_filename = os.path.basename(fileset['jpg'])
                if jpg_filename in self.imagemap:
                    img_obj = self.imagemap[jpg_filename]
                    calibration_info['is_calibration_photo'] = getattr(img_obj, 'is_calibration_photo', False)
                    calibration_info['aruco_id'] = getattr(img_obj, 'aruco_id', None)
                    calibration_info['aruco_corners'] = getattr(img_obj, 'aruco_corners', None)
                    calibration_info['calibration_target_polys'] = getattr(img_obj, 'calibration_target_polys', None)
                    
                    # Store ALS-independent calibration data (sensor response values and base coefficients)
                    # CRITICAL FIX: Validate to prevent string placeholders from being saved
                    if (hasattr(img_obj, 'calibration_xvals') and img_obj.calibration_xvals is not None and 
                        not isinstance(img_obj.calibration_xvals, str)):
                        calibration_info['calibration_xvals'] = img_obj.calibration_xvals
                    elif hasattr(img_obj, 'calibration_xvals') and isinstance(img_obj.calibration_xvals, str):
                        pass  # Skip string placeholders
                    
                    if (hasattr(img_obj, 'calibration_coefficients') and img_obj.calibration_coefficients is not None and 
                        not isinstance(img_obj.calibration_coefficients, str)):
                        calibration_info['calibration_coefficients'] = img_obj.calibration_coefficients
                    elif hasattr(img_obj, 'calibration_coefficients') and isinstance(img_obj.calibration_coefficients, str):
                        pass  # Skip string placeholders
                    
                    if (hasattr(img_obj, 'calibration_limits') and img_obj.calibration_limits is not None and 
                        not isinstance(img_obj.calibration_limits, str)):
                        calibration_info['calibration_limits'] = img_obj.calibration_limits
                    elif hasattr(img_obj, 'calibration_limits') and isinstance(img_obj.calibration_limits, str):
                        pass  # Skip string placeholders
                    
                    # CRITICAL FIX: Store calibration_yvals from ALS data
                    if (hasattr(img_obj, 'calibration_yvals') and img_obj.calibration_yvals is not None and 
                        not isinstance(img_obj.calibration_yvals, str)):
                        calibration_info['calibration_yvals'] = img_obj.calibration_yvals
                    elif hasattr(img_obj, 'calibration_yvals') and isinstance(img_obj.calibration_yvals, str):
                        pass  # Skip string placeholders
                    
                    # Calibration data saved (verbose logging removed)
            
            # Check if we have a RAW file and get its calibration status (fallback if no JPG)
            elif fileset.get('raw'):
                raw_filename = os.path.basename(fileset['raw'])
                if raw_filename in self.imagemap:
                    img_obj = self.imagemap[raw_filename]
                    calibration_info['is_calibration_photo'] = getattr(img_obj, 'is_calibration_photo', False)
                    calibration_info['aruco_id'] = getattr(img_obj, 'aruco_id', None)
                    calibration_info['aruco_corners'] = getattr(img_obj, 'aruco_corners', None)
                    calibration_info['calibration_target_polys'] = getattr(img_obj, 'calibration_target_polys', None)
                    
                    # Store ALS-independent calibration data (sensor response values and base coefficients)
                    # CRITICAL FIX: Validate to prevent string placeholders from being saved
                    if (hasattr(img_obj, 'calibration_xvals') and img_obj.calibration_xvals is not None and 
                        not isinstance(img_obj.calibration_xvals, str)):
                        calibration_info['calibration_xvals'] = img_obj.calibration_xvals
                    elif hasattr(img_obj, 'calibration_xvals') and isinstance(img_obj.calibration_xvals, str):
                        pass  # Skip string placeholders
                    
                    if (hasattr(img_obj, 'calibration_coefficients') and img_obj.calibration_coefficients is not None and 
                        not isinstance(img_obj.calibration_coefficients, str)):
                        calibration_info['calibration_coefficients'] = img_obj.calibration_coefficients
                    elif hasattr(img_obj, 'calibration_coefficients') and isinstance(img_obj.calibration_coefficients, str):
                        pass  # Skip string placeholders
                    
                    if (hasattr(img_obj, 'calibration_limits') and img_obj.calibration_limits is not None and 
                        not isinstance(img_obj.calibration_limits, str)):
                        calibration_info['calibration_limits'] = img_obj.calibration_limits
                    elif hasattr(img_obj, 'calibration_limits') and isinstance(img_obj.calibration_limits, str):
                        pass  # Skip string placeholders
                    
                    # CRITICAL FIX: Store calibration_yvals from ALS data
                    if (hasattr(img_obj, 'calibration_yvals') and img_obj.calibration_yvals is not None and 
                        not isinstance(img_obj.calibration_yvals, str)):
                        calibration_info['calibration_yvals'] = img_obj.calibration_yvals
                    elif hasattr(img_obj, 'calibration_yvals') and isinstance(img_obj.calibration_yvals, str):
                        pass  # Skip string placeholders
                    
                    # Calibration data saved (verbose logging removed)
            
            # Only add calibration info if we have some data
            if calibration_info:
                fileset['calibration'] = calibration_info
        

        
        with open(self.configpath, 'w+') as f:
            f.write(json.dumps(self.data, indent=2, cls=NumpyEncoder))
            f.flush()
            os.fsync(f.fileno())
        debug_project(f"Project data written to {os.path.basename(self.configpath)}")
    
    def save_processing_state(self, stage, mode, thread_states=None, last_image_index=-1, completed_images=None, total_images=0):
        """Save current processing state to project data."""
        import datetime
        
        if 'processing_state' not in self.data:
            self.data['processing_state'] = self.get_processing_state()
        
        self.data['processing_state'].update({
            'current_stage': stage,
            'processing_mode': mode,
            'last_processed_image_index': last_image_index,
            'completed_images': completed_images or [],
            'total_images': total_images,
            'timestamp': datetime.datetime.now().isoformat()
        })
        
        # Update thread states if provided
        if thread_states:
            if mode == 'serial':
                # CLOUD FIX: Ensure serial_stages exists before updating
                if 'serial_stages' not in self.data['processing_state']:
                    self.data['processing_state']['serial_stages'] = self.get_processing_state().get('serial_stages', {})
                self.data['processing_state']['serial_stages'].update(thread_states)
            else:
                # CLOUD FIX: Ensure parallel_threads exists before updating
                if 'parallel_threads' not in self.data['processing_state']:
                    self.data['processing_state']['parallel_threads'] = self.get_processing_state().get('parallel_threads', {})
                self.data['processing_state']['parallel_threads'].update(thread_states)
        
        # Write immediately to ensure state is saved
        self.write()
        debug_verbose(f"Saved processing state: {stage} at image {last_image_index}/{total_images}")
    
    def save_stage_progress(self, mode, stage_name, images_processed, total_images, completed_images, exported_images=None):
        """Save progress for a specific stage or thread."""
        import datetime
        
        if 'processing_state' not in self.data:
            self.data['processing_state'] = self.get_processing_state()
        
        if mode == 'serial':
            if stage_name in ['target_detection', 'image_processing']:
                stage_data = {
                    'completed': images_processed >= total_images,
                    'images_processed': images_processed,
                    'total_images': total_images,
                    'completed_images': completed_images or []
                }
                if exported_images is not None:
                    stage_data['exported_images'] = exported_images
                
                # CLOUD FIX: Ensure serial_stages exists before accessing
                if 'serial_stages' not in self.data['processing_state']:
                    self.data['processing_state']['serial_stages'] = {
                        'target_detection': {'completed': False, 'images_processed': 0, 'total_images': 0, 'completed_images': []},
                        'image_processing': {'completed': False, 'images_processed': 0, 'total_images': 0, 'completed_images': [], 'exported_images': []}
                    }
                self.data['processing_state']['serial_stages'][stage_name] = stage_data
        else:  # parallel mode
            thread_key = f"thread_{stage_name}" if not stage_name.startswith('thread_') else stage_name
            # CLOUD FIX: Ensure parallel_threads exists before checking
            if 'parallel_threads' not in self.data['processing_state']:
                self.data['processing_state']['parallel_threads'] = self.get_processing_state().get('parallel_threads', {})
            if thread_key in self.data['processing_state']['parallel_threads']:
                thread_data = {
                    'completed': images_processed >= total_images,
                    'images_processed': images_processed,
                    'total_images': total_images,
                    'completed_images': completed_images or []
                }
                if exported_images is not None:
                    thread_data['exported_images'] = exported_images
                    
                self.data['processing_state']['parallel_threads'][thread_key] = thread_data
        
        self.data['processing_state']['timestamp'] = datetime.datetime.now().isoformat()
        self.write()
    
    def get_processing_state(self):
        """Get current processing state from project data."""
        return self.data.get('processing_state', {
            'current_stage': 'idle',
            'processing_mode': 'serial',
            'serial_stages': {
                'target_detection': {
                    'completed': False,
                    'images_processed': 0,
                    'total_images': 0,
                    'completed_images': []
                },
                'image_processing': {
                    'completed': False,
                    'images_processed': 0,
                    'total_images': 0,
                    'completed_images': [],
                    'exported_images': []
                }
            },
            'parallel_threads': {
                'thread_1_target_detection': {
                    'completed': False,
                    'images_processed': 0,
                    'total_images': 0,
                    'completed_images': []
                },
                'thread_2_calibration': {
                    'completed': False,
                    'images_processed': 0,
                    'total_images': 0,
                    'completed_images': []
                },
                'thread_3_processing': {
                    'completed': False,
                    'images_processed': 0,
                    'total_images': 0,
                    'completed_images': []
                },
                'thread_4_export': {
                    'completed': False,
                    'images_processed': 0,
                    'total_images': 0,
                    'completed_images': [],
                    'exported_images': []
                }
            },
            'last_processed_image_index': -1,
            'completed_images': [],
            'total_images': 0,
            'timestamp': None
        })
    
    def clear_processing_state(self):
        """Clear processing state when processing completes or is cancelled."""
        self.data['processing_state'] = self.get_processing_state()
        self.data['processing_state']['current_stage'] = 'idle'
        self.write()
    
    # REMOVED: Resume functionality completely removed per user request
    # def is_processing_resumable(self): - method removed

    def add_files(self, files):
        import hashlib
        
        # Helper to extract timestamp and sequence number
        def extract_info(filename):
            # Example: 2025_0327_211651_007.RAW
            m = re.match(r'([0-9]{4}_[0-9]{4}_[0-9]{6})_([0-9]+)', os.path.splitext(os.path.basename(filename))[0])
            if m:
                return m.group(1), int(m.group(2))
            else:
                return os.path.splitext(os.path.basename(filename))[0], 0

        # Collect all files by (timestamp, seq, ext)
        jpgs = []
        raws = []
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            ts, seq = extract_info(file)
            if ext in ['.jpg', '.jpeg']:
                jpgs.append({'file': os.path.abspath(file), 'ts': ts, 'seq': seq})
            elif ext == '.raw':
                raws.append({'file': os.path.abspath(file), 'ts': ts, 'seq': seq})

        # CRITICAL FIX: Sort by timestamp to ensure deterministic pairing
        # Without sorting, glob order is arbitrary and causes non-deterministic results
        jpgs.sort(key=lambda x: (x['ts'], x['seq']))
        raws.sort(key=lambda x: (x['ts'], x['seq']))

        # Get existing files to check for new pairs
        existing_files = []
        if 'files' in self.data:
            for base, fileset in self.data['files'].items():
                if fileset.get('jpg'):
                    existing_files.append(fileset['jpg'])
                if fileset.get('raw'):
                    existing_files.append(fileset['raw'])
        
        # Add existing files to the pairing process
        existing_jpgs = []
        existing_raws = []
        for file in existing_files:
            if os.path.exists(file):  # Only include files that still exist
                ext = os.path.splitext(file)[1].lower()
                ts, seq = extract_info(file)
                if ext in ['.jpg', '.jpeg']:
                    existing_jpgs.append({'file': os.path.abspath(file), 'ts': ts, 'seq': seq})
                elif ext == '.raw':
                    existing_raws.append({'file': os.path.abspath(file), 'ts': ts, 'seq': seq})
        
        # Combine new and existing files for pairing
        all_jpgs = jpgs + existing_jpgs
        all_raws = raws + existing_raws
        


        def parse_timestamp_to_seconds(ts_str):
            """
            Convert timestamp string (YYYY_MMDD_HHMMSS) to total seconds for accurate comparison.
            Handles minute/hour rollovers correctly (e.g., 193858 vs 193900 = 2 seconds, not 42).
            """
            try:
                # ts_str is like "2025_0203_193858" -> extract HHMMSS part
                parts = ts_str.split('_')
                if len(parts) >= 3:
                    time_part = parts[2]  # HHMMSS
                    if len(time_part) == 6:
                        hours = int(time_part[0:2])
                        minutes = int(time_part[2:4])
                        seconds = int(time_part[4:6])
                        return hours * 3600 + minutes * 60 + seconds
            except:
                pass
            return None
        
        # FIXED: Pair JPGs and RAWs using sequence-based matching FIRST, then timestamp fallback
        # This prevents the greedy timestamp algorithm from causing cascading mismatches
        used_raws = set()
        image_sets = {}
        
        # Build a lookup dict for RAWs by sequence number for O(1) access
        raw_by_seq = {}
        for raw in all_raws:
            raw_by_seq[raw['seq']] = raw
        
        def find_best_raw_for_jpg(jpg, used_raws_set):
            """
            Find the best RAW for a JPG using this priority:
            1. Sequence-based: JPG seq N pairs with RAW seq N-1 (camera captures RAW then JPG)
            2. Sequence-based: JPG seq N pairs with RAW seq N+1 (alternate camera behavior)
            3. Timestamp-based: Closest RAW within 10 seconds
            """
            best_raw = None
            
            # PRIORITY 1: Try sequence N-1 (most common: RAW captured before JPG)
            seq_minus_1 = jpg['seq'] - 1
            if seq_minus_1 in raw_by_seq:
                candidate = raw_by_seq[seq_minus_1]
                if candidate['file'] not in used_raws_set:
                    # Verify timestamp is reasonable (within 30 seconds)
                    jpg_secs = parse_timestamp_to_seconds(jpg['ts'])
                    raw_secs = parse_timestamp_to_seconds(candidate['ts'])
                    if jpg_secs and raw_secs and abs(jpg_secs - raw_secs) <= 30:
                        return candidate
            
            # PRIORITY 2: Try sequence N+1 (less common: JPG captured before RAW)
            seq_plus_1 = jpg['seq'] + 1
            if seq_plus_1 in raw_by_seq:
                candidate = raw_by_seq[seq_plus_1]
                if candidate['file'] not in used_raws_set:
                    jpg_secs = parse_timestamp_to_seconds(jpg['ts'])
                    raw_secs = parse_timestamp_to_seconds(candidate['ts'])
                    if jpg_secs and raw_secs and abs(jpg_secs - raw_secs) <= 30:
                        return candidate
            
            # PRIORITY 3: Fallback to timestamp proximity (within 10 seconds)
            best_time_diff = float('inf')
            jpg_seconds = parse_timestamp_to_seconds(jpg['ts'])
            
            for raw in all_raws:
                if raw['file'] in used_raws_set:
                    continue
                
                raw_seconds = parse_timestamp_to_seconds(raw['ts'])
                if jpg_seconds is not None and raw_seconds is not None:
                    time_diff = abs(jpg_seconds - raw_seconds)
                    if time_diff <= 10 and time_diff < best_time_diff:
                        best_raw = raw
                        best_time_diff = time_diff
            
            return best_raw
        
        # First, pair existing files to maintain current structure
        for jpg in existing_jpgs:
            best_raw = find_best_raw_for_jpg(jpg, used_raws)
            
            if best_raw:
                pass  # Best RAW found

            # Generate unique base key using full path hash to avoid overwrites
            filename_base = os.path.splitext(os.path.basename(jpg['file']))[0]
            path_hash = hashlib.md5(jpg['file'].encode()).hexdigest()[:8]
            base = f"{filename_base}_{path_hash}"
            image_sets[base] = {'jpg': jpg['file'], 'raw': best_raw['file'] if best_raw else None, 'processed': [], 'layers': {}}
            if best_raw:
                used_raws.add(best_raw['file'])
        
        # Then, pair new JPGs
        for jpg in jpgs:
            best_raw = find_best_raw_for_jpg(jpg, used_raws)
            
            # Pairing handled - unpaired files will be reported in summary
            try:
                # Generate unique base key using full path hash to avoid overwrites
                filename_base = os.path.splitext(os.path.basename(jpg['file']))[0]

                path_hash = hashlib.md5(jpg['file'].encode()).hexdigest()[:8]

                base = f"{filename_base}_{path_hash}"

                image_sets[base] = {'jpg': jpg['file'], 'raw': best_raw['file'] if best_raw else None, 'processed': [], 'layers': {}}

            except Exception as e:

                import traceback

                raise e
            if best_raw:
                used_raws.add(best_raw['file'])

        # Only add RAW files that have matching JPG files (no unpaired RAWs)

        for raw in all_raws:
            if raw['file'] not in used_raws:


                pass  # Empty block
        # Add any other processed files (tif/tiff)
        processed_extensions = {'.tif', '.tiff'}
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in processed_extensions:
                abs_file = os.path.abspath(file)
                filename_base = os.path.splitext(os.path.basename(file))[0]
                # Try to match to an existing set
                found = False
                for k, v in image_sets.items():
                    # Check if the filename base matches (ignoring the path hash)
                    if k.startswith(filename_base + '_') or k == filename_base:
                        v['processed'].append(abs_file)
                        found = True
                        break
                if not found:
                    # Generate unique base key for processed files too
                    path_hash = hashlib.md5(abs_file.encode()).hexdigest()[:8]
                    base = f"{filename_base}_{path_hash}"
                    image_sets[base] = {'jpg': None, 'raw': None, 'processed': [abs_file], 'layers': {}}

        # Merge new files with existing files instead of replacing
        if 'files' not in self.data:
            self.data['files'] = {}
        
        # Add new image sets to existing ones
        for base, fileset in image_sets.items():
            # Ensure existing filesets have the layers field
            if base in self.data['files'] and 'layers' not in self.data['files'][base]:
                self.data['files'][base]['layers'] = {}
            self.data['files'][base] = fileset
        
        # --- Populate imagemap, files, filenames ---
        self.jpg_name_to_raw_name = {}  # Initialize mapping for JPG to RAW filename conversion
        self.base_to_filenames = {}  # Mapping from base key to actual filenames
        for base, fileset in image_sets.items():
            raw_path = fileset.get('raw')
            jpg_path = fileset.get('jpg')
            try:
                if raw_path and jpg_path:
                    img = LabImage(self, raw_path)
                    img.rawpath = raw_path  # Ensure .rawpath is set
                    img.jpgpath = jpg_path
                    raw_filename = os.path.basename(raw_path)
                    jpg_filename = os.path.basename(jpg_path)
                    
                    # Store image with unique base key instead of filename to avoid overwrites
                    self.imagemap[base] = img
                    
                    # CRITICAL FIX: Copy camera metadata from LabImage to project data
                    try:
                        if base in self.data['files'] and isinstance(self.data['files'][base], dict):
                            # Safely add camera metadata to the fileset
                            if 'camera_metadata_added' not in self.data['files'][base]:
                                # Add metadata directly to the fileset level
                                self.data['files'][base]['camera_model'] = getattr(img, 'camera_model', 'Unknown')
                                self.data['files'][base]['camera_filter'] = getattr(img, 'camera_filter', 'Unknown')
                                self.data['files'][base]['camera_metadata_added'] = True

                                
                                # CRITICAL FIX: Add import_metadata with datetime and path for table display
                                self.data['files'][base]['import_metadata'] = {
                                    'camera_model': getattr(img, 'camera_model', 'Unknown'),
                                    'camera_filter': getattr(img, 'camera_filter', 'Unknown'),
                                    'datetime': getattr(img, 'DateTime', 'Unknown'),
                                    'path': jpg_path  # Add the actual file path for table display
                                }

                    except Exception as e:
                        pass

                        # Continue without camera metadata rather than failing
                    
                    # Keep mapping from base to actual filenames for lookup
                    self.base_to_filenames[base] = {
                        'raw_filename': raw_filename,
                        'jpg_filename': jpg_filename
                    }
                    
                    # Add JPG to RAW mapping
                    self.jpg_name_to_raw_name[jpg_filename] = raw_filename
                    # JPG->RAW mapping added (verbose logging removed)
                    # Image added with base key (verbose logging removed)
                    if raw_path not in self.files:
                        self.files.append(raw_path)
                    if jpg_path not in self.files:
                        self.files.append(jpg_path)
                    self.filenames.add(raw_filename)
                    self.filenames.add(jpg_filename)
                elif jpg_path:
                    # Only add JPG-only images (no RAW-only images allowed)
                    img = LabImage(self, jpg_path)
                    img.jpgpath = jpg_path
                    jpg_filename = os.path.basename(jpg_path)
                    
                    # Store image with unique base key instead of filename to avoid overwrites
                    self.imagemap[base] = img
                    
                    # CRITICAL FIX: Copy camera metadata from LabImage to project data (JPG-only)
                    try:
                        if base in self.data['files'] and isinstance(self.data['files'][base], dict):
                            # Safely add camera metadata to the fileset level
                            if 'camera_metadata_added' not in self.data['files'][base]:
                                self.data['files'][base]['camera_model'] = getattr(img, 'camera_model', 'Unknown')
                                self.data['files'][base]['camera_filter'] = getattr(img, 'camera_filter', 'Unknown')
                                self.data['files'][base]['camera_metadata_added'] = True
                                
                                # CRITICAL FIX: Add import_metadata with datetime for JPG-only files too!
                                self.data['files'][base]['import_metadata'] = {
                                    'camera_model': getattr(img, 'camera_model', 'Unknown'),
                                    'camera_filter': getattr(img, 'camera_filter', 'Unknown'),
                                    'datetime': getattr(img, 'DateTime', 'Unknown'),
                                    'path': jpg_path
                                }

                    except Exception as e:
                        pass

                        # Continue without camera metadata rather than failing
                    
                    # Keep mapping from base to actual filenames for lookup
                    self.base_to_filenames[base] = {
                        'raw_filename': None,
                        'jpg_filename': jpg_filename
                    }
                    
                    # JPG-only image added (verbose logging removed)
                    if jpg_path not in self.files:
                        self.files.append(jpg_path)
                    self.filenames.add(jpg_filename)
            except Exception as e:
                debug_error(f"Error adding image set to imagemap: {e}")
        
        # Write project data and provide summary
        self.write()
        debug_project(f"Added {len(image_sets)} image sets to project")
        
        # CRITICAL: Validate and report unpaired images immediately during import
        unpaired_jpgs = []
        unpaired_raws = []
        paired_count = 0
        
        for base, fileset in image_sets.items():
            jpg_path = fileset.get('jpg')
            raw_path = fileset.get('raw')
            
            if jpg_path and raw_path:
                paired_count += 1
            elif jpg_path and not raw_path:
                unpaired_jpgs.append(os.path.basename(jpg_path))
            elif raw_path and not jpg_path:
                unpaired_raws.append(os.path.basename(raw_path))
        
        # Only report if there are unpaired files (warnings only)
        if unpaired_jpgs or unpaired_raws:
            print(f"[IMPORT] ⚠️ {len(unpaired_jpgs)} JPGs and {len(unpaired_raws)} RAWs could not be paired")
            for jpg in unpaired_jpgs[:3]:  # Show first 3
                print(f"[IMPORT]   - {jpg}")
            if len(unpaired_jpgs) > 3:
                print(f"[IMPORT]   ... and {len(unpaired_jpgs) - 3} more")
        
        # Initialize phase progress for new files
        self._initialize_phase_progress()
    
    def _initialize_phase_progress(self):
        """Initialize phase progress tracking for all images"""
        if 'phase_progress' not in self.data:
            self.data['phase_progress'] = {
                'calibration': {'completed_images': [], 'total_images': 0},
                'index': {'completed_images': [], 'total_images': 0}
            }
        
        # Count image pairs from the files data structure
        # Each entry in self.data['files'] represents one image pair (RAW+JPG)
        total_image_pairs = len(self.data['files'])
        
        # For calibration phase (target detection), we process each pair once
        self.data['phase_progress']['calibration']['total_images'] = total_image_pairs
        
        # For index/processing phase, we also process each pair once (the RAW file)
        self.data['phase_progress']['index']['total_images'] = total_image_pairs
    
    def mark_image_completed(self, phase, image_filename):
        """Mark an image as completed for a specific phase"""
        if 'phase_progress' not in self.data:
            self._initialize_phase_progress()
        
        if phase not in self.data['phase_progress']:
            self.data['phase_progress'][phase] = {'completed_images': [], 'total_images': 0}
        
        # Only mark RAW files as completed for progress tracking
        if image_filename.lower().endswith('.raw'):
            if image_filename not in self.data['phase_progress'][phase]['completed_images']:
                self.data['phase_progress'][phase]['completed_images'].append(image_filename)
                self.write()

        else:

    
            pass  # Empty block
    def _validate_calibration_json_entry(self, image_filename):
        """
        Validate that a calibration image has a valid entry in calibration_data.json
        Returns True if valid calibration data exists, False if missing or invalid
        """
        import os
        import json
        
        # Get the calibration data file path
        calibration_data_file = os.path.join(self.fp, 'calibration_data.json')
        
        if not os.path.exists(calibration_data_file):

            return False
        
        try:
            with open(calibration_data_file, 'r') as f:
                calib_data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:

            return False
        
        if not calib_data:

            return False
        
        # Find the image in the imagemap to get its timestamp and metadata
        image_obj = None
        if hasattr(self, 'imagemap') and image_filename in self.imagemap:
            image_obj = self.imagemap[image_filename]
        
        if not image_obj:

            return False
        
        # Get image metadata for matching
        img_timestamp = getattr(image_obj, 'timestamp', None) or getattr(image_obj, 'capture_time', None)
        img_camera_model = getattr(image_obj, 'camera_model', None)
        img_camera_filter = getattr(image_obj, 'camera_filter', None)
        
        # Convert timestamp to string for JSON key matching
        if hasattr(img_timestamp, 'strftime'):
            timestamp_str = img_timestamp.strftime('%Y-%m-%d %H:%M:%S')
        else:
            timestamp_str = str(img_timestamp) if img_timestamp else None
        
        # Look for matching calibration entry
        matching_entry = None
        for key, entry in calib_data.items():
            # Try exact timestamp match first
            if timestamp_str and key == timestamp_str:
                matching_entry = entry
                break
            # Try filename match as fallback
            if entry.get('filename') == image_filename:
                matching_entry = entry
                break
        
        if not matching_entry:

            return False
        
        # Validate that the entry has required calibration data
        required_fields = ['coefficients', 'xvals', 'yvals']
        for field in required_fields:
            if field not in matching_entry or matching_entry[field] is None:

                return False
        
        # Check that coefficients is not empty
        coeffs = matching_entry['coefficients']
        if not coeffs or (isinstance(coeffs, list) and len(coeffs) == 0):

            return False
        

        return True

    def is_image_completed(self, phase, image_filename):
        """Check if an image is completed for a specific phase"""
        # For calibration images, check BOTH JSON validity AND processing completion
        if hasattr(self, 'imagemap') and image_filename in self.imagemap:
            image_obj = self.imagemap[image_filename]
            if getattr(image_obj, 'is_calibration_photo', False):
                # For calibration images, they must be BOTH in completed_images AND have valid JSON
                has_valid_json = self._validate_calibration_json_entry(image_filename)
                is_in_completed = False
                if 'phase_progress' in self.data and phase in self.data['phase_progress']:
                    is_in_completed = image_filename in self.data['phase_progress'][phase]['completed_images']
                
                is_completed = has_valid_json and is_in_completed

                return is_completed
            
        if 'phase_progress' not in self.data:
            return False
        
        if phase not in self.data['phase_progress']:
            return False
        
        # Only check RAW files for completion status
        if image_filename.lower().endswith('.raw'):
            return image_filename in self.data['phase_progress'][phase]['completed_images']
        else:
            # For non-RAW files, check if their corresponding RAW file is completed
            # This is a simplified approach - in practice, we might want to map JPG to RAW
            return False
    
    def get_phase_progress(self, phase):
        """Get progress percentage for a specific phase (0-100)"""
        if 'phase_progress' not in self.data:
            return 0
        
        if phase not in self.data['phase_progress']:
            return 0
        
        progress_data = self.data['phase_progress'][phase]
        total = progress_data['total_images']
        completed = len(progress_data['completed_images'])
        
        if total == 0:
            return 0
        
        return int((completed / total) * 100)
    
    def get_phase_progress_details(self, phase):
        """Get detailed progress information for a specific phase"""
        if 'phase_progress' not in self.data:
            return {'completed': 0, 'total': 0, 'percentage': 0}
        
        if phase not in self.data['phase_progress']:
            return {'completed': 0, 'total': 0, 'percentage': 0}
        
        progress_data = self.data['phase_progress'][phase]
        total = progress_data['total_images']
        completed = len(progress_data['completed_images'])
        
        if total == 0:
            return {'completed': 0, 'total': 0, 'percentage': 0}
        
        return {
            'completed': completed,
            'total': total,
            'percentage': int((completed / total) * 100)
        }
    
    def get_phase_name(self, phase):
        """Get the display name for a phase"""
        phase_names = {
            'calibration': 'Target Detection',
            'index': 'Processing'
        }
        return phase_names.get(phase, phase.title())
    
    def reset_phase_progress(self, phase=None):
        """Reset progress for a specific phase or all phases"""
        if 'phase_progress' not in self.data:
            return
        
        if phase is None:
            # Reset all phases
            for phase_name in self.data['phase_progress']:
                self.data['phase_progress'][phase_name]['completed_images'] = []

        else:
            # Reset specific phase
            if phase in self.data['phase_progress']:
                self.data['phase_progress'][phase]['completed_images'] = []

            else:

    
                pass  # Empty block
    def get_uncompleted_images(self, phase):
        """Get list of images that haven't been completed for a specific phase"""
        if 'phase_progress' not in self.data:
            # Return only RAW files
            return [fn for fn in self.imagemap.keys() if fn.lower().endswith('.raw')]
        
        if phase not in self.data['phase_progress']:
            # Return only RAW files
            return [fn for fn in self.imagemap.keys() if fn.lower().endswith('.raw')]
        
        completed_images = set(self.data['phase_progress'][phase]['completed_images'])
        # Only consider RAW files
        raw_images = set(fn for fn in self.imagemap.keys() if fn.lower().endswith('.raw'))
        uncompleted = raw_images - completed_images
        
        return list(uncompleted)

    def load_files(self):
        """Load files from the new image set structure"""
        self.imagemap = {}
        self.scanmap = {}
        self.files = []
        self.filenames = set()
        self.missing_files = []
        self.jpg_name_to_raw_name = {}  # Add mapping for JPG to RAW filename conversion
        self.base_to_filenames = {}  # Mapping from base key to actual filenames
        files_dict = self.data.get('files', {})


        for base, fileset in files_dict.items():
            raw_path = fileset.get('raw')
            jpg_path = fileset.get('jpg')
            if raw_path:
                if not os.path.exists(raw_path):
                    self.missing_files.append(raw_path)
                    continue
                if jpg_path and not os.path.exists(jpg_path):
                    pass  # JPG file missing
                try:
                    img = LabImage(self, raw_path)
                    if jpg_path:
                        img.jpgpath = jpg_path
                    raw_filename = os.path.basename(raw_path)
                    
                    # Store image with base key instead of filename to avoid overwrites
                    self.imagemap[base] = img
                    
                    # Keep mapping from base to actual filenames for lookup
                    self.base_to_filenames[base] = {
                        'raw_filename': raw_filename,
                        'jpg_filename': os.path.basename(jpg_path) if jpg_path else None
                    }
                    
                    self.files.append(raw_path)
                    self.filenames.add(raw_filename)
                    
                    # Add JPG to RAW mapping if both exist
                    if jpg_path:
                        jpg_filename = os.path.basename(jpg_path)
                        self.jpg_name_to_raw_name[jpg_filename] = raw_filename
                        # JPG->RAW mapping added (verbose logging removed)
                        
                        # Also add JPG to imagemap for calibration detection
                        try:
                            jpg_img = LabImage(self, jpg_path)
                            jpg_img.jpgpath = jpg_path
                            # Link JPG to RAW for calibration data
                            jpg_img.raw_filename = raw_filename
                            # CRITICAL FIX: Actually store JPG image in imagemap with JPG filename as key
                            self.imagemap[jpg_filename] = jpg_img
                            self.files.append(jpg_path)
                            self.filenames.add(jpg_filename)
                            
                            # Restore calibration data to JPG image as well
                            calibration_info = fileset.get('calibration', {})
                            if calibration_info:
                                jpg_img.is_calibration_photo = calibration_info.get('is_calibration_photo', False)
                                jpg_img.aruco_id = calibration_info.get('aruco_id', None)
                                jpg_img.aruco_corners = calibration_info.get('aruco_corners', None)
                                polys = calibration_info.get('calibration_target_polys', None)
                                if polys is not None:
                                    import numpy as np
                                    # Convert all polygons to numpy arrays if they are lists
                                    if isinstance(polys, list):
                                        polys = [np.array(poly, dtype=np.int32) for poly in polys]
                                jpg_img.calibration_target_polys = polys
                                
                                # Restore ALS-independent calibration data
                                if 'calibration_xvals' in calibration_info:
                                    xvals = calibration_info['calibration_xvals']
                                    if isinstance(xvals, list) and len(xvals) == 4 and not any(isinstance(v, list) for v in xvals):
                                        xvals = [xvals, [0,0,0,0], [0,0,0,0]]
                                    jpg_img.calibration_xvals = xvals
                                if 'calibration_coefficients' in calibration_info:
                                    jpg_img.calibration_coefficients = calibration_info['calibration_coefficients']
                                if 'calibration_limits' in calibration_info:
                                    jpg_img.calibration_limits = calibration_info['calibration_limits']
                                # CRITICAL FIX: Load calibration_yvals from project data
                                if 'calibration_yvals' in calibration_info:
                                    jpg_img.calibration_yvals = calibration_info['calibration_yvals']

                                

                            

                        except Exception as e:

                    
                            pass  # Empty block
                    # CRITICAL FIX: Restore layers from project data
                    layers_data = fileset.get('layers', {})
                    if layers_data:

                        for layer_name, layer_path in layers_data.items():
                            if layer_path and os.path.exists(layer_path):
                                # Add layer to RAW image object
                                img.layers[layer_name] = layer_path

                                
                                # Also add layer to JPG image object if it exists
                                if jpg_path:
                                    jpg_filename = os.path.basename(jpg_path)
                                    if jpg_filename in self.imagemap:
                                        self.imagemap[jpg_filename].layers[layer_name] = layer_path

                            else:

                    
                                pass  # Empty block
                    # Restore calibration data if available
                    calibration_info = fileset.get('calibration', {})
                    if calibration_info:
                        img.is_calibration_photo = calibration_info.get('is_calibration_photo', False)
                        img.aruco_id = calibration_info.get('aruco_id', None)
                        img.aruco_corners = calibration_info.get('aruco_corners', None)
                        polys = calibration_info.get('calibration_target_polys', None)
                        if polys is not None:
                            import numpy as np
                            # Convert all polygons to numpy arrays if they are lists
                            if isinstance(polys, list):
                                polys = [np.array(poly, dtype=np.int32) for poly in polys]
                        img.calibration_target_polys = polys
                        
                        # Restore ALS-independent calibration data
                        if 'calibration_xvals' in calibration_info:
                            xvals = calibration_info['calibration_xvals']
                            if isinstance(xvals, list) and len(xvals) == 4 and not any(isinstance(v, list) for v in xvals):
                                xvals = [xvals, [0,0,0,0], [0,0,0,0]]
                            img.calibration_xvals = xvals
                        if 'calibration_coefficients' in calibration_info:
                            img.calibration_coefficients = calibration_info['calibration_coefficients']
                        if 'calibration_limits' in calibration_info:
                            img.calibration_limits = calibration_info['calibration_limits']
                        # CRITICAL FIX: Load calibration_yvals from project data
                        if 'calibration_yvals' in calibration_info:
                            img.calibration_yvals = calibration_info['calibration_yvals']

                        

                    

                except Exception as e:
                    # File loading failed
                    self.missing_files.append(raw_path)
            elif jpg_path:
                try:
                    img = LabImage(self, jpg_path)
                    img.jpgpath = jpg_path
                    jpg_filename = os.path.basename(jpg_path)
                    
                    # Store image with base key instead of filename to avoid overwrites
                    self.imagemap[base] = img
                    
                    # Keep mapping from base to actual filenames for lookup
                    self.base_to_filenames[base] = {
                        'raw_filename': None,
                        'jpg_filename': jpg_filename
                    }
                    self.files.append(jpg_path)
                    self.filenames.add(jpg_filename)
                    
                    # CRITICAL FIX: Restore layers from project data for JPG-only images
                    layers_data = fileset.get('layers', {})
                    if layers_data:

                        for layer_name, layer_path in layers_data.items():
                            if layer_path and os.path.exists(layer_path):
                                img.layers[layer_name] = layer_path

                            else:

                    
                                pass  # Empty block
                    # Restore calibration data if available
                    calibration_info = fileset.get('calibration', {})
                    if calibration_info:
                        img.is_calibration_photo = calibration_info.get('is_calibration_photo', False)
                        img.aruco_id = calibration_info.get('aruco_id', None)
                        img.aruco_corners = calibration_info.get('aruco_corners', None)
                        polys = calibration_info.get('calibration_target_polys', None)
                        if polys is not None:
                            import numpy as np
                            # Convert all polygons to numpy arrays if they are lists
                            if isinstance(polys, list):
                                polys = [np.array(poly, dtype=np.int32) for poly in polys]
                        img.calibration_target_polys = polys
                        
                        # Restore ALS-independent calibration data
                        if 'calibration_xvals' in calibration_info:
                            xvals = calibration_info['calibration_xvals']
                            if isinstance(xvals, list) and len(xvals) == 4 and not any(isinstance(v, list) for v in xvals):
                                xvals = [xvals, [0,0,0,0], [0,0,0,0]]
                            img.calibration_xvals = xvals
                        if 'calibration_coefficients' in calibration_info:
                            img.calibration_coefficients = calibration_info['calibration_coefficients']
                        if 'calibration_limits' in calibration_info:
                            img.calibration_limits = calibration_info['calibration_limits']
                        # CRITICAL FIX: Load calibration_yvals from project data
                        if 'calibration_yvals' in calibration_info:
                            img.calibration_yvals = calibration_info['calibration_yvals']

                        

                    

                except Exception as e:
                    # JPG-only file loading failed
                    self.missing_files.append(jpg_path)


        
        # Load scanmap data from project JSON
        scanmap_data = self.data.get('scanmap', {})

        for scan_filename, scan_info in scanmap_data.items():
            try:
                scan_path = scan_info.get('path')
                if scan_path and os.path.exists(scan_path):
                    scan_obj = ScanFile(self, scan_path)
                    scan_obj.Model = scan_info.get('Model', 'Light Sensor')
                    scan_obj.DateTime = scan_info.get('DateTime', 'Unknown')
                    self.scanmap[scan_filename] = scan_obj

                else:

                    pass  # Empty block
            except Exception as e:
                pass  # Empty block
        
        # File loading complete
        
    def remove_files(self, files):
        # files: list of JPG filenames to remove (from UI)

        to_remove = []
        for base, fileset in self.data['files'].items():
            if fileset.get('jpg') and os.path.basename(fileset['jpg']) in files:
                to_remove.append(base)
        for base in to_remove:

            del self.data['files'][base]
        self.write()




    def set_config(self, path, value):
        keys = path.split('.')
        
        # Handle both formats: "Target Detection.Minimum calibration sample area (px)" 
        # and "Project Settings.Target Detection.Minimum calibration sample area (px)"
        if len(keys) >= 2 and keys[0] != 'Project Settings':
            # Add "Project Settings" prefix if not present
            keys = ['Project Settings'] + keys
            # print(f"🔄 Auto-prefixed path with 'Project Settings': {path} -> {'.'.join(keys)}")
        
        cfg = self.data['config']
        for key in keys[:-1]:
            if key not in cfg:
                cfg[key] = {}
            cfg = cfg[key]
        cfg[keys[-1]] = value
        
        # Safely handle reprocessing keys update
        try:
            if len(keys) >= 3 and keys[1] in reprocessing_keys:
                for key in reprocessing_keys[keys[1]]:
                    self.data['phases'][key] = True
                print(f"🔄 Updated reprocessing phases for {keys[1]}: {reprocessing_keys[keys[1]]}")
            else:
                # print(f"⚠️ No reprocessing keys found for path: {path}")
                pass
        except Exception as e:
            pass
        
        self.write()

    def ensure_complete_config(self):
        """Ensure the project config contains all keys from DEFAULT_CONFIG."""
        if 'config' not in self.data:
            self.data['config'] = deepcopy(DEFAULT_CONFIG)
            debug_normal("Created missing config section from DEFAULT_CONFIG")
            return
        
        # Deep merge DEFAULT_CONFIG into existing config
        def deep_merge(default, existing):
            """Recursively merge default config into existing config."""
            for key, value in default.items():
                if key not in existing:
                    existing[key] = deepcopy(value)
                    debug_normal(f"Added missing config key: {key}")
                elif isinstance(value, dict) and isinstance(existing[key], dict):
                    deep_merge(value, existing[key])
        
        deep_merge(DEFAULT_CONFIG, self.data['config'])
        debug_normal("Ensured project config is complete with all default values")

    def get_config(self, section, key):
        """Get a configuration value from the specified section and key."""
        try:
            return self.data['config']['Project Settings'][section][key]
        except KeyError:
            # Fallback to default config if key doesn't exist in project config
            if section in DEFAULT_CONFIG['Project Settings'] and key in DEFAULT_CONFIG['Project Settings'][section]:
                default_value = DEFAULT_CONFIG['Project Settings'][section][key]
                # Optionally update the project config with the missing key
                if 'Project Settings' not in self.data['config']:
                    self.data['config']['Project Settings'] = {}
                if section not in self.data['config']['Project Settings']:
                    self.data['config']['Project Settings'][section] = {}
                self.data['config']['Project Settings'][section][key] = default_value
                self.write()
                return default_value
            else:
                # Re-raise the KeyError if the key doesn't exist in defaults either
                raise

    def auto_detect_timezone_offset(self, user_timezone_offset=7):
        """Auto-detect timezone offset based on light sensor file types."""
        
        # Check for scan files in scanmap to determine appropriate timezone offset
        daq_files = []
        csv_files = []
        
        # Look for scan files in scanmap (where they are actually stored)
        for scan_filename, scan_obj in self.scanmap.items():
            file_ext = os.path.splitext(scan_filename)[1].lower()
            if file_ext == '.daq':
                daq_files.append(scan_filename)
            elif file_ext == '.csv':
                csv_files.append(scan_filename)
        
        # Also check filenames for any scan files that might be there
        for file_path in self.filenames:
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext == '.daq':
                daq_files.append(file_path)
            elif file_ext == '.csv':
                csv_files.append(file_path)
        
        # Auto-detection logic: .daq files -> offset 0, .csv files -> user's timezone (fallback to 7)
        if daq_files:
            new_offset = 0
            file_type = ".daq"
        elif csv_files:
            new_offset = user_timezone_offset
            file_type = ".csv"
            print(f"Using user's timezone offset ({user_timezone_offset}) for .csv files")
        else:
            print("No light sensor files found, keeping current timezone offset")
            return
        
        current_offset = self.get_config('Processing', 'Light sensor timezone offset')
        
        if current_offset != new_offset:
            self.set_config('Project Settings.Processing.Light sensor timezone offset', new_offset)

    def stringify_cfg(self):
        # Ensure config exists before accessing it
        if 'config' not in self.data:
            self.data['config'] = {}
        
        # Debug: Print config structure

        
        return json.dumps(self.data['config'], cls=NumpyEncoder)

    def export_template(self, name):
        tpl = deepcopy(self.data)
        tpl['files'] = {}
        os.makedirs(os.path.join(Path.home(),'Mapir Lab Projects', 'Project Templates'), exist_ok=True)
        with open(os.path.join(Path.home(),'Mapir Lab Projects', 'Project Templates', name+'.json'), 'w') as f:
            f.write(json.dumps(tpl, cls=NumpyEncoder))

    def add_scan_file(self, scan_file_path):
        """Add a scan file (.daq or .csv) to the project and persist its path"""
        if not os.path.exists(scan_file_path):

            return False
        
        scan_filename = os.path.basename(scan_file_path)
        file_ext = os.path.splitext(scan_filename)[1].lower()
        
        # Only process .daq and .csv files
        if file_ext not in ['.daq', '.csv']:

            return False
        
        # Check if already added
        if scan_filename in self.scanmap:

            return True
        
        try:
            # Create ScanFile object and add to scanmap
            scan_obj = ScanFile(self, scan_file_path)
            self.scanmap[scan_filename] = scan_obj
            
            # Ensure scanmap data exists in project data
            if 'scanmap' not in self.data:
                self.data['scanmap'] = {}
            
            # Save scan file path and metadata to project JSON
            self.data['scanmap'][scan_filename] = {
                'path': scan_file_path,
                'Model': getattr(scan_obj, 'Model', 'Light Sensor'),
                'DateTime': getattr(scan_obj, 'DateTime', 'Unknown')
            }
            


            
            # Write project data to persist the changes
            self.write()
            
            return True
            
        except Exception as e:

            return False

    def get_cached_debayered_tiff(self, raw_filename):
        """Get path to cached debayered TIFF for a RAW file if it exists.
        
        Args:
            raw_filename: The RAW filename (not full path)
            
        Returns:
            str: Path to cached TIFF or None if not cached
        """
        # First check in-memory dictionary (fast path)
        if raw_filename in self._cached_targets:
            cached_path = self._cached_targets[raw_filename]
            if os.path.exists(cached_path):
                return cached_path
            else:
                # Cache file no longer exists, remove from dictionary
                del self._cached_targets[raw_filename]
        
        # Check disk for cache files (for RAY workers with new Project instances)
        base_filename = os.path.splitext(raw_filename)[0]
        cache_filename = f"{base_filename}_debayered.tif"
        cache_path = os.path.join(self._debayer_cache_dir, cache_filename)
        
        if os.path.exists(cache_path):
            # Add to in-memory dictionary for future fast lookups
            self._cached_targets[raw_filename] = cache_path
            return cache_path
        
        return None
    
    def cache_debayered_tiff(self, raw_filename, debayered_image_data):
        """Cache a debayered image as TIFF for later reuse.
        
        Args:
            raw_filename: The RAW filename (not full path)
            debayered_image_data: numpy array of debayered image data (BGR format, uint16)
            
        Returns:
            str: Path to cached TIFF file
        """
        # CRITICAL FIX: Ensure cache directory exists (may have been deleted by previous run)
        os.makedirs(self._debayer_cache_dir, exist_ok=True)
        
        # Generate cache filename
        base_name = os.path.splitext(raw_filename)[0]
        cache_filename = f"{base_name}_debayered.tif"
        cache_path = os.path.join(self._debayer_cache_dir, cache_filename)
        
        # Save debayered data to cache
        try:
            import tifffile as tiff
            
            # CRITICAL: debayered_image_data is in BGR format (OpenCV convention from debayer output)
            # Convert to RGB for standard TIFF storage
            import cv2
            rgb_data = cv2.cvtColor(debayered_image_data, cv2.COLOR_BGR2RGB)
            tiff.imwrite(cache_path, rgb_data, photometric='rgb')
            
            self._cached_targets[raw_filename] = cache_path
            return cache_path
        except Exception as e:
            return None
    
    def delete_cached_tiff(self, raw_filename):
        """Delete a single cached TIFF file immediately after it's no longer needed.
        
        Args:
            raw_filename: The RAW filename whose cache should be deleted
        """
        # CRITICAL FIX: Check both in-memory dictionary AND disk for cache files
        # In Ray/premium mode, each worker has its own _cached_targets dictionary,
        # so we must also check disk to ensure deletion works across workers
        cached_path = None
        
        # First check in-memory dictionary
        if raw_filename in self._cached_targets:
            cached_path = self._cached_targets[raw_filename]
        else:
            # Construct expected cache path from filename (for Ray workers)
            base_filename = os.path.splitext(raw_filename)[0]
            cache_filename = f"{base_filename}_debayered.tif"
            potential_cache_path = os.path.join(self._debayer_cache_dir, cache_filename)
            if os.path.exists(potential_cache_path):
                cached_path = potential_cache_path
        
        # Delete the cache file if found
        if cached_path:
            try:
                if os.path.exists(cached_path):
                    os.unlink(cached_path)
                # Remove from dictionary if present
                if raw_filename in self._cached_targets:
                    del self._cached_targets[raw_filename]
            except Exception as e:
                pass
    
    def clear_debayer_cache(self):
        """Clear all cached debayered TIFF files and remove cache directory."""
        import shutil
        
        if os.path.exists(self._debayer_cache_dir):
            try:
                # Remove entire cache directory and all contents
                shutil.rmtree(self._debayer_cache_dir)
                
                # Clear the cache mapping
                self._cached_targets.clear()
            except Exception as e:
                # Fallback: try to remove files individually
                try:
                    for filename in os.listdir(self._debayer_cache_dir):
                        file_path = os.path.join(self._debayer_cache_dir, filename)
                        try:
                            if os.path.isfile(file_path):
                                os.unlink(file_path)
                        except Exception as e2:
                            pass
                    # Try to remove empty directory
                    os.rmdir(self._debayer_cache_dir)
                except Exception as e3:
                    pass


class ScanFile():
    def __init__(self,project,path):
        self.project=project
        self.path=path
        self.Model = 'Light Sensor'
        self.DateTime = 'Unknown'
        self.layers={}
        
        # Try to read timestamp from .daq file if it's a SQLite database
        file_ext = (os.path.splitext(self.path)[-1][1:]).lower()
        if file_ext == 'daq':
            self.Model = 'DAQ-A-SD'
            self.DateTime = self._read_daq_timestamp()
        elif file_ext == 'csv':
            self.Model = 'DAQ-M'
        
    def _read_daq_timestamp(self):
        """Read the first timestamp from a .daq SQLite database file"""
        try:
            import sqlite3
            from datetime import datetime
            
            # SQL query to get the first timestamp
            sql_get_first_timestamp = '''
                SELECT created_on
                FROM als_log
                WHERE created_on IS NOT NULL
                ORDER BY id ASC
                LIMIT 1
            '''
            
            conn = sqlite3.connect(self.path)
            cursor = conn.cursor()
            cursor.execute(sql_get_first_timestamp)
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0]:
                timestamp_str = result[0]
                # Parse the timestamp and format it for display
                try:
                    # Handle both formats: "2025-02-03 19:29:10.123456" and "2025-02-03 19:29:10"
                    if '.' in timestamp_str:
                        dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S.%f")
                    else:
                        dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                    return dt.strftime("%Y:%m:%d %H:%M:%S")
                except ValueError as e:
                    print(f"Warning: Could not parse DAQ timestamp '{timestamp_str}': {e}")
                    return 'Unknown'
            else:
                print(f"Warning: No timestamp found in DAQ file: {self.path}")
                return 'Unknown'
                
        except Exception as e:
            print(f"Warning: Could not read timestamp from DAQ file {self.path}: {e}")
            return 'Unknown'
        
    @property
    def ext(self):
        return (os.path.splitext(self.path)[-1][1:]).lower()
    @property
    def fn(self):
        return os.path.basename(self.path)
    @property
    def dir(self):
        return os.path.dirname(self.path)

TAGMAP={v:k for k,v in TAGS.items()}

class LabImage():

    def __init__(self, project, path, jpgpath=None):
        self.project=project
        self.path=path
        self.jpgpath=jpgpath
        # Ensure .rawpath and .jpgpath are set appropriately
        ext = (os.path.splitext(self.path)[-1][1:]).lower()
        if ext == 'raw':
            self.rawpath = self.path
        if ext == 'jpg':
            self.jpgpath = self.path
        self._data=None
        self.is_calibration_photo=False
        self.aruco_id=None
        self.aruco_corners=None
        self.calibration_target_polys=None
        self.calibration_poly_size=None
        self.calibration_target_averages=None
        
        if ext == 'raw':
            if self.jpgpath is None:
                self.jpgpath=find_paired_jpg(self.path)
            self.exif_source=self.jpgpath
            try:
                if self.jpgpath and os.path.exists(self.jpgpath):
                    exif=Image.open(self.jpgpath).getexif()
                else:
                    exif = {}
            except Exception as e:
                print(f"Warning: Could not read EXIF from {self.jpgpath}: {e}")
                exif = {}
        else:
            self.exif_source=self.path
            try:
                if os.path.exists(self.path):
                    exif=Image.open(self.path).getexif()
                else:
                    exif = {}
            except Exception as e:
                print(f"Warning: Could not read EXIF from {self.path}: {e}")
                exif = {}

        self.exif={TAGS[k] : v for k,v in dict(exif).items() }
        
        # Get Model and DateTime from EXIF, or set defaults
        try:
            model_from_exif = self.exif.get('Model', 'Unknown')
            datetime_from_exif = self.exif.get('DateTime', 'Unknown')
        except:
            model_from_exif = 'Unknown'
            datetime_from_exif = 'Unknown'
        
        # Set the values directly to the instance (not in exif dict)
        self.Model = model_from_exif
        self.DateTime = datetime_from_exif
        # PATCH: Always set project_path
        self.project_path = getattr(self.project, 'fp', None)

        
        if len(self.exif)!=0 and datetime_from_exif != 'Unknown':
            try:
                self.timestamp=datetime.datetime.strptime(datetime_from_exif, '%Y:%m:%d %H:%M:%S')
                if model_from_exif and model_from_exif != 'Unknown' and '_' in model_from_exif:
                    model=model_from_exif.split('_')
                    self.camera_model=model[0]
                    self.camera_filter=model[1]
                else:
                    self.camera_model='Unknown'
                    self.camera_filter='Unknown'
            except Exception as e:
                print(f"Warning: Could not parse EXIF data for {self.path}: {e}")
                self.camera_model='Unknown'
                self.camera_filter='Unknown'
        else:
            self.camera_model='Unknown'
            self.camera_filter='Unknown'
            
        self.colorspace=None
        self.target_ppi=None
        self.target_sample_diameter=None
        self.calibration_image=None
        self.calibration_coefficients=None
        self.calibration_limits=None
        self.calibration_xvals=None
        self.calibration_yvals=None
        self.vignette_corrected=False
        self.als_log_id=None
        self.als_data=None
        self.als_magnitude=None
        self.parent=None
        self.children=[]
        self.index_image=None
        self.lut_image=None
        self.layers={}
    def __getattr__(self, attr):
        if 'exif' in self.__dict__:
            if attr in self.__dict__['exif'].keys():
                return self.__dict__['exif'].get(attr)
        raise AttributeError(f"MCCImage has no attribute {attr}")
    
    def __setattr__(self,attr,value):
        if 'exif' in self.__dict__:
            if attr in TAGS.values():
                self.exif[attr]=value
                return
        if attr=='data':
            self.__dict__['_data']=value
        if attr=='ext':
            self._setext(value)
        self.__dict__[attr]=value

    @property
    def ext(self):
        return (os.path.splitext(self.path)[-1][1:]).lower()

    def _setext(self,new):
        self.path=self.dir+os.path.splitext(self.fn)[0]+'.'+new.replace('.','')

    @property
    def fn(self):
        return os.path.basename(self.path)
    @property
    def dir(self):
        return os.path.dirname(self.path)

    @property
    def data(self):
        if self._data is None and os.path.exists(self.path):
            # Import cv2 at the start since it's needed for both RAW and JPG paths
            import cv2
            
            # OPTIMIZATION: Check for cached debayered TIFF before debayering
            # This avoids re-debayering target images multiple times
            if self.ext == 'raw' and hasattr(self, 'project') and self.project:
                cached_path = self.project.get_cached_debayered_tiff(self.fn)
                if cached_path:
                    try:
                        import tifffile as tiff
                        # Production: Load from cache silently
                        cached_data = tiff.imread(cached_path)
                        if cached_data is not None:
                            # CRITICAL FIX: Cache stores RGB but OpenCV/calibration code expects BGR
                            # Convert RGB back to BGR to match the rest of the pipeline
                            self._data = cv2.cvtColor(cached_data, cv2.COLOR_RGB2BGR)
                            self.colorspace = "BGR"
                            # Production: Cache loaded successfully (silently)
                            return self._data
                        else:
                            pass  # Fall through to debayering
                    except Exception as e:
                        pass
            
            if self.ext =='raw':
                data = np.fromfile(self.path, dtype=np.uint8)
                data = np.unpackbits(data)
                datsize = data.shape[0]
                data = data.reshape((int(datsize / 4), 4))
                
                # Truncate to expected size for 4000x3000 image (36M rows = 12M pixels × 3)
                # RAW files may have padding bytes at the end
                expected_rows = 36000000
                if data.shape[0] > expected_rows:
                    data = data[:expected_rows]
            
                # Switch even rows and odd rows
                temp = deepcopy(data[0::2])
                temp2 = deepcopy(data[1::2])
                data[0::2] = temp2
                data[1::2] = temp
                
                # Repack into image file
                udata = np.packbits(np.concatenate([data[0::3], np.zeros((12000000,4),dtype=np.uint8),   data[2::3], data[1::3]], axis=1).reshape(192000000, 1)).tobytes()
                
                img = np.frombuffer(udata, np.dtype('u2'), (4000 * 3000)).reshape((3000, 4000))

                # Fix: Properly access Project Settings for Debayer method
                try:
                    if 'Project Settings' in self.project.data['config']:
                        debayer_method = self.project.data['config']["Project Settings"]['Processing']["Debayer method"]
                    else:
                        debayer_method = self.project.data['config']['Processing']["Debayer method"]
                except (KeyError, TypeError):
                    debayer_method = 'High Quality (Faster)'  # Default debayer method
                

                    
                # Use new debayer methods

                t0=time.time()
                
                # Select debayer method
                if debayer_method in ['High Quality (Faster)', 'Edge-Aware', 'VNG']:
                    # Support old names for backward compatibility
                    color = debayer_HighQuality(img)
                elif debayer_method in ['Maximum Quality (Slower)', 'Super Quality', 'SuperQuality', 'Maximum Quality']:
                    # Support old names for backward compatibility
                    color = debayer_MaximumQuality(img)
                else:
                    # Default to High Quality for unknown methods

                    color = debayer_HighQuality(img)
                
                color=np.swapaxes(color,0,2)
                color=np.swapaxes(color,0,1)
                # Clip values to valid range
                color[color>=65535] = 65535
                # CRITICAL FIX: OpenCV's cv2.COLOR_BAYER_RG2RGB_EA outputs BGR format (OpenCV convention)
                # Despite "RGB" in the name, OpenCV always outputs BGR. No conversion needed!
                self._data = color
                self.colorspace = "BGR"  # Debayer outputs BGR format (OpenCV convention)
                
                # OPTIMIZATION: Cache debayered RAW images for reuse
                # This avoids re-debayering when image.copy() is used
                if hasattr(self, 'project') and self.project and hasattr(self, 'fn'):
                    try:
                        cache_path = self.project.cache_debayered_tiff(self.fn, self._data)
                        if cache_path:
                            pass
                    except Exception as e:
                        pass

            else:
                # Load TIFF/JPG/PNG files
                # Use IMREAD_UNCHANGED (-1) to preserve multi-channel TIFFs (e.g., reflectance exports)
                self._data=cv2.imread(self.path, -1)
                # CRITICAL FIX: Check if image has channels before color conversion
                if len(self._data.shape) == 3 and self._data.shape[2] >= 3:
                    # Image has 3+ channels - cv2.imread returns BGR for standard images
                    # Multi-channel TIFFs (reflectance) are preserved as-is
                    self.colorspace = "BGR"
                elif len(self._data.shape) == 2:
                    # Image is grayscale (1 channel) - convert to BGR by duplicating channels
                    self._data = cv2.cvtColor(self._data, cv2.COLOR_GRAY2BGR)
                    self.colorspace = "BGR"
                    self.colorspace = "BGR"
                else:
                    # Unknown format
                    self.colorspace = "UNKNOWN"
        return self._data

    @property
    def raw_data(self):
        """
        Load the original raw data directly from the file without any processing.
        This is used for calibration target images to ensure they show the original raw TIFF data.
        """
        if not os.path.exists(self.path):
            return None
            
        if self.ext == 'raw':
            # For RAW files, return the unprocessed raw data
            data = np.fromfile(self.path, dtype=np.uint8)
            data = np.unpackbits(data)
            datsize = data.shape[0]
            data = data.reshape((int(datsize / 4), 4))
            
            # Switch even rows and odd rows
            temp = deepcopy(data[0::2])
            temp2 = deepcopy(data[1::2])
            data[0::2] = temp2
            data[1::2] = temp
            
            # Repack into image file
            udata = np.packbits(np.concatenate([data[0::3], np.zeros((12000000,4),dtype=np.uint8), data[2::3], data[1::3]], axis=1).reshape(192000000, 1)).tobytes()
            
            img = np.frombuffer(udata, np.dtype('u2'), (4000 * 3000)).reshape((3000, 4000))
            
            # Return the raw debayered data without any additional processing or color space conversion
            # Use the same debayer method as the project config but without color space conversion
            # Fix: Properly access Project Settings for Debayer method
            try:
                if 'Project Settings' in self.project.data['config']:
                    debayer_method = self.project.data['config']["Project Settings"]['Processing']["Debayer method"]
                else:
                    debayer_method = self.project.data['config']['Processing']["Debayer method"]
            except (KeyError, TypeError):
                debayer_method = 'High Quality (Faster)'  # Default debayer method
            
            # Select debayer method
            if debayer_method in ['High Quality (Faster)', 'Edge-Aware', 'VNG']:
                # Support old names for backward compatibility
                color = debayer_HighQuality(img)
            elif debayer_method in ['Maximum Quality (Slower)', 'Super Quality', 'SuperQuality', 'Maximum Quality']:
                # Support old names for backward compatibility
                color = debayer_MaximumQuality(img)
            else:
                # Default to High Quality for unknown methods

                color = debayer_HighQuality(img)
            
            color=np.swapaxes(color,0,2)
            color=np.swapaxes(color,0,1)
            # Return in BGR format (no color space conversion)
            return color
            
            # Old else branch removed - all methods now use same path
            if False:
                # Use OpenCV bilinear debayering without color space conversion
                color = cv2.cvtColor(img, cv2.COLOR_BAYER_RG2BGR)
                return color
        else:
            # For TIFF/JPG files, load directly without any processing or color space conversion
            raw_data = cv2.imread(self.path, -1)
            # Return in BGR format (no color space conversion)
            return raw_data

    def copy(self):
        # Handle circular reference in calibration_image to prevent stack overflow
        original_calibration_image = getattr(self, 'calibration_image', None)
        self_reference = original_calibration_image is self
        
        # CRITICAL: Preserve _data before deepcopy (deepcopy can lose numpy arrays in __dict__)
        original_data = self.__dict__.get('_data', None)
        
        # Temporarily break circular reference for deepcopy
        if self_reference:
            self.calibration_image = None
        
        try:
            copied = deepcopy(self)
            
            # CRITICAL: Restore _data after deepcopy to prevent reloading from disk
            if original_data is not None:
                copied.__dict__['_data'] = original_data.copy()
            
            # Restore circular reference in both original and copy
            if self_reference:
                self.calibration_image = self
                copied.calibration_image = copied
            return copied
        except:
            # Restore original state in case of error
            if self_reference:
                self.calibration_image = self
            raise

    def fork(self):
        new = self.copy()
        return new

    def __getstate__(self):
        # Return a dict of all attributes except _data (to avoid huge pickles)
        state = self.__dict__.copy()
        # Optionally, you can include _data if you want to serialize it, but it's safer to reload
        # Remove _data from state to avoid pickling large arrays
        state['_data'] = None
        
        # CRITICAL FIX: Don't deep copy the project reference - keep the original
        # This ensures cached debayered TIFFs can be accessed by copied images
        # Store a flag to restore the original project reference after unpickling
        if 'project' in state:
            state['_original_project'] = state['project']
            # Don't remove it, but mark it for special handling
        
        # Handle circular reference in calibration_image to prevent pickle recursion
        if 'calibration_image' in state and state['calibration_image'] is self:
            state['_self_calibration_reference'] = True
            state['calibration_image'] = None
        else:
            state['_self_calibration_reference'] = False
        
        return state

    def __setstate__(self, state):
        # Restore circular reference if it was a self-reference
        if state.pop('_self_calibration_reference', False):
            state['calibration_image'] = None  # Will be set to self after update
        
        # CRITICAL FIX: Restore original project reference (not a deep copy)
        # This ensures the copied image can access the same cache as the original
        if '_original_project' in state:
            state['project'] = state['_original_project']
            del state['_original_project']
        
        self.__dict__.update(state)
        
        # Restore self-reference after unpickling
        if hasattr(self, '_self_calibration_reference') or state.get('_self_calibration_reference', False):
            self.calibration_image = self
        
        # After unpickling, _data will be None; it will be reloaded from disk on demand

def find_paired_jpg(raw_path):
    path = os.path.abspath(raw_path)
    path_dir = os.path.dirname(raw_path)
    name = str(os.path.basename(raw_path).split(".")[0])    
    target = "_"
    last_pos = len(name) - 1 - name[::-1].index(target[::-1])
    number = int(name[(last_pos+1):])
    number += 1
    if number < 10:
        number_str = "00" + str(number)
    elif number <100:
        number_str = "0" + str(number)
    else:
        number_str = str(number)
    name_start = str(name[0:16])     # name_start = YYYY_MMDD_HHMMSS
    name_date_time = datetime.datetime.strptime(name_start, "%Y_%m%d_%H%M%S")  
    for count in range(6):  # Check up to 5 seconds ahead (0, 1, 2, 3, 4, 5)
        name_date_time_next = name_date_time + datetime.timedelta(hours=0, minutes=0, seconds=(count))
        name_date_time_next_frmtd = name_date_time_next.strftime("%Y_%m%d_%H%M%S")
        
        new_name = str(name_date_time_next_frmtd + '_' + number_str + ".JPG")
        new_path = os.path.join(path_dir,new_name)
        if (os.path.exists(new_path)):
            return new_path
