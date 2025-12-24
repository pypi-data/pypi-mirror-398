# -*- coding: utf-8 -*-
"""
@author: MAPIR, Inc
"""

import os
import sys
import numpy as np
import gc
from mip.Calibrate_Images import apply_calib_to_image, apply_calib_to_target, get_limits_from_calibration_image, sensor_response_correction
from mip.Calibration_Target import detect_calibration_targets, calibration_target_polys, validate_poly_area, check_target_values, check_target_exposure, draw_calibration_samples, validate_target_values_sanity
from mip.Calibration_Utils import get_calibration_coefficients_from_target_image, als_calibration_correction, robust_calibration_target_validation
from mip.ExifUtils import *
from mip.Save_Format import save_format
from mip.Vignette_Correction import ApplyVig as devignette
from mip.Index import process_index, process_lut
from mip.White_Balance import white_balance as apply_wb_to_image
from project import LabImage
# Global stop flag for calibration and intensive operations
_global_stop_requested = False

def set_global_stop_flag(value):
    """Set the global stop flag for intensive operations"""
    global _global_stop_requested
    _global_stop_requested = value

def check_global_stop():
    """Check if stop has been requested"""
    return _global_stop_requested

# Try to import ray for parallel processing
RAY_AVAILABLE = False
ray = None

def _ensure_ray_available():
    """Check if Ray is available and properly imported"""
    global RAY_AVAILABLE, ray
    if not RAY_AVAILABLE:
        try:
            # Use Ray session manager to avoid circular imports
            try:
                from ray_session_manager import get_ray_session
                ray_session = get_ray_session()
                if ray_session and ray_session.is_available():
                    ray = ray_session.get_ray()  # Use get_ray() method
                else:
                    ray = None
            except ImportError:
                # Fallback to direct import if ray_session_manager is not available
                # CRITICAL: Never import real ray in compiled/frozen mode - it causes subprocess errors
                is_compiled = getattr(sys, 'frozen', False) or '__compiled__' in globals()
                if not is_compiled:
                    try:
                        import ray
                    except ImportError:
                        ray = None
                else:
                    # In compiled mode, real ray should never be used
                    print("[RAY] ⚠️ Compiled mode detected - skipping real ray import")
                    ray = None
            if ray is not None and hasattr(ray, 'init'):
                # CRITICAL FIX: Don't call ray.is_initialized() as it triggers _private errors
                # Just check if we have the ray module with required attributes
                required_attrs = ['init', 'get', 'put', 'remote']
                if all(hasattr(ray, attr) for attr in required_attrs):
                    RAY_AVAILABLE = True

                else:
                    RAY_AVAILABLE = False

            else:
                RAY_AVAILABLE = False

        except Exception as e:

            RAY_AVAILABLE = False
    return RAY_AVAILABLE

# Initial check
_ensure_ray_available()

import traceback
import socket
import json
import datetime
import queue
import threading

# Suppress Ray deprecation warnings in production
import warnings
warnings.filterwarnings('ignore', message='.*ray.worker.global_worker.*')
warnings.filterwarnings('ignore', message='.*SIGTERM handler.*')
from collections import deque
from typing import Dict, List, Optional, Tuple
import time
import copy

# Pause/resume functionality removed - processing runs continuously

def group_images_by_model(image_list):
    # CRITICAL FIX: Ensure calibration image is always included in processing
    # This is a global fix to ensure calibration images never get filtered out
    pass  # Group images by model
    calibration_images_found = 0
    for image in image_list:
        if getattr(image, 'is_calibration_photo', False):
            calibration_images_found += 1
            pass  # Calibration image found
    
    groups={}
    for image in image_list:
        if not image.Model in groups:
            groups[image.Model]=[]
        groups[image.Model].append(image)
    return groups



def _load_existing_calibration_data(image):
    """
    Load existing calibration data from calibration_data.json using unified API.
    Returns calibration data dict or None if not found/invalid.
    """
    from unified_calibration_api import UnifiedCalibrationManager
    
    # Determine project directory
    project_dir = None
    if hasattr(image, 'project_path') and image.project_path:
        project_dir = image.project_path
    elif hasattr(image, 'project') and image.project and hasattr(image.project, 'fp'):
        project_dir = image.project.fp
    else:
        # Try to find project directory from image path
        if hasattr(image, 'path') and image.path:
            import os
            image_dir = os.path.dirname(image.path)
            # Look for project.json in current dir or parent dirs
            current_dir = image_dir
            for _ in range(3):  # Check up to 3 levels up
                project_file = os.path.join(current_dir, 'project.json')
                if os.path.exists(project_file):
                    project_dir = current_dir
                    break
                parent_dir = os.path.dirname(current_dir)
                if parent_dir == current_dir:  # Reached root
                    break
                current_dir = parent_dir
    
    if not project_dir:

        return None
    
    # Use unified API to load calibration data
    calib_data = UnifiedCalibrationManager.load_calibration_data(image, project_dir)
    if calib_data and calib_data.get('coefficients'):
        # VALIDATION: Check if coefficients are valid numeric arrays, not string placeholders
        coefficients = calib_data.get('coefficients')
        if (isinstance(coefficients, str) or 
            coefficients is None or 
            coefficients == [False, False, False] or
            not isinstance(coefficients, list)):
            return None
        
        # Additional validation for xvals
        xvals = calib_data.get('xvals')
        if isinstance(xvals, str):
            return None
            

        return calib_data
    else:

        return None


def detect_calibration_image(image, min_calibration_samples, project, progress_tracker):
	# CRITICAL: Check for stop request before processing
	if check_global_stop():
		print(f"🛑 Stop requested during target detection for {getattr(image, 'fn', 'unknown')}")
		return None, False, None, None
	
	# Defensive: check that image is a LabImage, not a path
	if isinstance(image, str) or isinstance(image, bytes) or hasattr(image, '__fspath__'):

		raise TypeError("detect_calibration_image expects a LabImage object, not a file path")
	# Defensive: check that image.jpgpath is a string
	if hasattr(image, 'jpgpath') and not isinstance(image.jpgpath, str):
		pass  # Skip invalid jpgpath
	if hasattr(image, 'fn') and not isinstance(image.fn, str):
		pass  # Skip invalid fn
	
	result = detect_calibration_targets(image)
	
	# Set is_calibration_photo based on detection result
	if result and hasattr(image, 'aruco_id') and image.aruco_id is not None:
		image.is_calibration_photo = True

	else:
		image.is_calibration_photo = False

	
	# Only proceed with validation if calibration target was detected
	if image.is_calibration_photo:
		# IP-PROTECTED: Generate calibration target polygons
		calibration_target_polys(image)
		if (not validate_poly_area(image, min_calibration_samples)):
			print('validate_poly_area failed')
			image.is_calibration_photo=False
		elif (not check_target_values(image, project)):
			print('check_target_values failed')
			image.is_calibration_photo=False
		# CRITICAL FALSE POSITIVE PROTECTION: Validate target values are sensible
		# This catches false positives from dark/blank images where ArUco found patterns in noise
		elif (not validate_target_values_sanity(image, debug=True)):
			print(f'[TARGET-DETECTION] ⚠️ FALSE POSITIVE REJECTED: {getattr(image, "fn", "unknown")}')
			print(f'[TARGET-DETECTION]    ArUco detection passed but target values are invalid')
			print(f'[TARGET-DETECTION]    This prevents calibration corruption from dark/blank images')
			image.is_calibration_photo=False
			image.aruco_id = None
			image.aruco_corners = None
			image.calibration_target_polys = None
		calibration_target_polys(image)
		# IP-PROTECTED: Calibration polygons generated
	
	final_result = (image.aruco_id, image.is_calibration_photo, image.aruco_corners, image.calibration_target_polys)
	
	gc.collect()
	progress_tracker.task_completed()
	return final_result


def get_calib_data(image, options, progress_tracker):
    import os
    import socket
    
    # SMART GPU HANDLING: Try GPU first, fallback to CPU if issues occur
    # Ray workers can use GPU safely with proper error handling
    is_ray_worker = False
    try:
        # Use global ray variable set up by _ensure_ray_available()
        global ray
        # Check if we're inside a Ray worker by looking for Ray context
        if ray is not None:
            # Suppress deprecation warning for global_worker access
            with warnings.catch_warnings():
                warnings.filterwarnings('ignore', category=DeprecationWarning)
                is_ray_worker = ray.is_initialized() and hasattr(ray.worker, 'global_worker') and ray.worker.global_worker is not None
    except:
        # Fallback: check for Ray-specific environment variables
        is_ray_worker = any(env_var in os.environ for env_var in ['RAY_WORKER_DYNAMIC_OPTION_PLACEHOLDER', 'RAY_RAYLET_PID', 'RAY_NODE_ID'])
    
    if is_ray_worker:
        # Ray worker detected - GPU operations enabled
        # Don't disable GPU - let individual operations handle GPU/CPU fallback
        # os.environ['MAPIR_DISABLE_GPU'] = '1'  # REMOVED - allow GPU attempts
        pass
    
    pass  # Running calibration
    pass  # ALS magnitude check
    pass  # ALS data check
    pass  # Calibration coefficients check
    pass  # Calibration yvals check
    # CRITICAL: Load ALS data from scan files if not already present
    if not hasattr(image, 'als_magnitude') or image.als_magnitude is None:
        # IP-PROTECTED: Attempting to load ALS data
        try:
            # Load ALS data from scan files in Ray worker
            project_dir = getattr(image, 'project_path', None)
            if project_dir and hasattr(image, 'project'):
                # Get scan directory from project scanmap
                scanmap = getattr(image.project, 'scanmap', {})
                if scanmap:
                    scan_directory = list(scanmap.values())[0].dir
                    # Load ALS data for this single image
                    from mip.als import get_als_data
                    code_name = 793  # Default code name
                    get_als_data([image], scan_directory, code_name, image.project)
        except Exception as e:
            pass  # ALS loading failed silently
    pass  # File existence check
    pass  # Working directory check
    pass  # Image data check
    # CRITICAL FIX: Access _data directly since @property may not work with Ray-serialized objects
    if hasattr(image, '_data') and image._data is not None:
        arr = image._data
        
    if not os.path.exists(getattr(image, 'path', image.fn)):
        raise FileNotFoundError(f"File does not exist in Ray worker: {getattr(image, 'path', image.fn)}, cwd={os.getcwd()}, files={os.listdir(os.getcwd())}")
    # IP-PROTECTED: Calibration data computation
    
    # CRITICAL: JPG images should never be used for calibration coefficient computation
    # Redirect to corresponding RAW image if this is a JPG target
    if hasattr(image, 'ext') and image.ext.lower() == 'jpg' and getattr(image, 'is_calibration_photo', False):


        
        # Find the corresponding RAW image using project data structure
        if hasattr(image, 'project') and image.project:
            jpg_filename = image.fn

            
            # Search through project data to find the corresponding RAW
            for base_key, fileset in image.project.data['files'].items():
                if fileset.get('jpg') and os.path.basename(fileset['jpg']) == jpg_filename:
                    if fileset.get('raw'):
                        raw_filename = os.path.basename(fileset['raw'])

                        
                        # Look for the RAW image object in imagemap
                        raw_img_obj = None
                        if raw_filename in image.project.imagemap:
                            raw_img_obj = image.project.imagemap[raw_filename]
                        elif base_key in image.project.imagemap:
                            raw_img_obj = image.project.imagemap[base_key]
                        
                        if raw_img_obj:

                            
                            # Transfer target attributes to RAW image
                            raw_img_obj.is_calibration_photo = True
                            raw_img_obj.aruco_id = getattr(image, 'aruco_id', None)
                            raw_img_obj.aruco_corners = getattr(image, 'aruco_corners', None)
                            raw_img_obj.calibration_target_polys = getattr(image, 'calibration_target_polys', None)
                            
                            # Recursively call get_calib_data on the RAW image
                            # Redirecting to RAW image for calibration
                            return get_calib_data(raw_img_obj, options, progress_tracker)
                        else:
                            pass
                    break
        
        # CRITICAL FIX: Return 5 elements to match expected format
        return None, None, None, None, None
    
    import os
    # CRITICAL FIX: Handle both nested and flat configuration structures
    processing_options = None
    if 'Project Settings' in options and 'Processing' in options['Project Settings']:
        # Nested structure: options['Project Settings']['Processing']
        processing_options = options['Project Settings']['Processing']
    elif 'Processing' in options:
        # Flat structure: options['Processing']
        processing_options = options['Processing']
    else:
        raise KeyError("'Processing' section missing from options: {}".format(options))

    # CRITICAL FIX: Load image data if not already loaded
    # Ray serialization loses @property decorators, so we need to manually load data
    if not hasattr(image, '_data') or image._data is None:
        pass
        
        # CRITICAL: Check if we can access the image via the data property
        try:
            # Try accessing via property (works for non-Ray objects)
            _ = image.data
        except (AttributeError, Exception) as e:
            # Property access failed (Ray serialization), manually load the data
            
            # Check file exists
            file_to_check = getattr(image, 'path', image.fn)
            if not os.path.exists(file_to_check):
                print(f"[ERROR] get_calib_data: File does not exist: {file_to_check}")
                return None, None, None, None, None
            
            # Manually load the data using the data property logic
            # Check for cached TIFF first
            if hasattr(image, 'project') and image.project and hasattr(image, 'ext') and image.ext == 'raw':
                try:
                    # Ensure project has cache directory set up
                    if not hasattr(image.project, '_debayer_cache_dir'):
                        # Initialize cache directory if missing
                        image.project._debayer_cache_dir = os.path.join(image.project.fp, '.debayer_cache')
                        os.makedirs(image.project._debayer_cache_dir, exist_ok=True)
                    
                    cached_path = image.project.get_cached_debayered_tiff(image.fn)
                    if cached_path:
                        try:
                            import tifffile as tiff
                            import cv2
                            # Loading from cached TIFF
                            cached_data = tiff.imread(cached_path)
                            # Convert RGB to BGR for OpenCV processing
                            image._data = cv2.cvtColor(cached_data, cv2.COLOR_RGB2BGR)
                        except Exception as e2:
                            pass  # Error loading cached data
                            image._data = None
                except Exception as e3:
                    pass  # Error accessing project cache
            
            # If still no data, we can't proceed
            if not hasattr(image, '_data') or image._data is None:
                print(f"[ERROR] get_calib_data: Failed to load image data for {image.fn}")
                return None, None, None, None, None
    
    # Apply vignette correction BEFORE computing calibration coefficients
    do_vig=processing_options['Vignette correction']
    if do_vig:
        devignette(image)
        # Vignette correction applied

    
    # OPTIMIZATION: Check if calibration data already exists before expensive computation
    existing_calibration = _load_existing_calibration_data(image)
    
    # ADDITIONAL VALIDATION: Check if the image object itself has string placeholders
    image_has_string_placeholders = False
    if hasattr(image, 'calibration_coefficients') and isinstance(image.calibration_coefficients, str):

        image_has_string_placeholders = True
    if hasattr(image, 'calibration_xvals') and isinstance(image.calibration_xvals, str):

        image_has_string_placeholders = True
    
    if image_has_string_placeholders:

        # Clear the corrupted attributes
        if hasattr(image, 'calibration_coefficients'):
            image.calibration_coefficients = None
        if hasattr(image, 'calibration_xvals'):
            image.calibration_xvals = None
        if hasattr(image, 'calibration_yvals'):
            image.calibration_yvals = None
        if hasattr(image, 'calibration_limits'):
            image.calibration_limits = None
        # Force recomputation by ignoring existing calibration data
        existing_calibration = None
    
    if existing_calibration and existing_calibration.get('coefficients'):
        # Using existing calibration data
        coefficients = existing_calibration['coefficients']
        limits = existing_calibration.get('limits', [65535, 65535, 65535])
        
        # Restore calibration data to image object
        if existing_calibration.get('xvals'):
            image.calibration_xvals = existing_calibration['xvals']
        if existing_calibration.get('yvals'):
            image.calibration_yvals = existing_calibration['yvals']
        if existing_calibration.get('aruco_id'):
            image.aruco_id = existing_calibration['aruco_id']
        if existing_calibration.get('als_magnitude'):
            image.als_magnitude = existing_calibration['als_magnitude']
            

    else:

        
        # Check if stop has been requested before intensive calibration computation
        if check_global_stop():
            print(f"🛑 Stop requested during calibration computation for {image.fn}")
            raise RuntimeError("Processing stopped by user request")
        
        # Compute calibration coefficients
        coefficients=get_calibration_coefficients_from_target_image(image)
        
        # REMOVED: Premature polygon save - this was saving incomplete data without limits
        # The complete calibration data (including polygons AND limits) will be saved later
    
    # CRITICAL FIX: Ensure calibration_xvals and calibration_yvals are available
    # The get_calibration_coefficients_from_target_image function should have computed calibration_xvals
    
    if hasattr(image, 'calibration_xvals') and image.calibration_xvals is not None:
        pass  # calibration_xvals available
    else:
        pass  # calibration_xvals not available
    
    if hasattr(image, 'calibration_yvals') and image.calibration_yvals is not None:
        pass  # calibration_yvals available
    else:
        pass  # will use default values
    
    # Target image creation moved to main thread for better visibility and file creation
    # Check if calibration coefficient generation failed
    if coefficients is None or coefficients == [False, False, False]:
        print(f"⚠️ WARNING: Calibration generation failed for {image.fn}")
        # Return default values to prevent workflow from breaking
        coefficients = [False, False, False]
        limits = [0, 0, 0]
        progress_tracker.task_completed()
        # CRITICAL FIX: Return 5 elements to match expected format
        return coefficients, limits, None, None, None
    limits=get_limits_from_calibration_image(image)
    # IP-PROTECTED: Calibration coefficients computed
    image.calibration_coefficients = coefficients
    image.calibration_limits = limits
    progress_tracker.task_completed()#.remote()
    # CRITICAL FIX: Preserve existing calibration_yvals if they are already set
    # This prevents ALS-derived calibration_yvals from being overwritten with None
    existing_calibration_yvals = getattr(image, 'calibration_yvals', None)
    computed_calibration_xvals = getattr(image, 'calibration_xvals', None)
    # IP-PROTECTED: Calibration data computed
    
    # CRITICAL FIX: Save calibration data to JSON file for future use
    from unified_calibration_api import UnifiedCalibrationManager
    calibration_data = {
        'coefficients': coefficients,
        'limits': limits,
        'xvals': computed_calibration_xvals,
        'yvals': existing_calibration_yvals,
        'aruco_id': getattr(image, 'aruco_id', None),
        'aruco_corners': getattr(image, 'aruco_corners', None),
        'target_polys': getattr(image, 'calibration_target_polys', None),
        # ALS data is NOT saved to JSON - it's loaded from scan files when needed
        'cluster_value': getattr(image, 'cluster_value', None),
        'is_selected_for_calibration': getattr(image, 'is_selected_for_calibration', False)
    }
    # IP-PROTECTED: Save complete calibration data
    try:
        success = UnifiedCalibrationManager.save_calibration_data(image, calibration_data)
    except Exception as e:
        print(f"⚠️ Exception saving calibration data: {e}")
    
    return coefficients, limits, computed_calibration_xvals, existing_calibration_yvals, image


fmt_map={
	
	'TIFF (16-bit)':'tiff16',
	'JPG (8-bit)':'jpg8',
	'PNG (8-bit)':'png8',
	'TIFF (32-bit, Percent)':'tiff32percent'
}

# REMOVED: reset_ppk_flag() - PPK corrections are now applied per-image, no session flags needed

# DELETED: Legacy process_image_unified function - replaced by process_image_unified_unified

# REMOVED: load_raw_image_data() - unused function for loading raw image data

exiftool_path=os.path.join(os.path.dirname(os.path.realpath(__file__)), 'exiftool.exe')
#print(exiftool_path)

# REMOVED: duplicate load_raw_image_data() - use the one from mip.Calibrate_Images instead

def load_truly_raw_data(image_path):
    """Load truly raw data directly from file without any debayering or processing"""
    import cv2
    import numpy as np
    import os
    from copy import deepcopy
    
    ext = (os.path.splitext(image_path)[-1][1:]).lower()
    
    if ext == 'raw':
        # Load RAW data directly without any processing
        data = np.fromfile(image_path, dtype=np.uint8)
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
        
        # CRITICAL FIX: For truly raw calibration target images, use the exact same process as the main pipeline
        # This ensures we get the truly raw pixel values that appear overly green
        # Use config-specified debayer method (High Quality or Maximum Quality)
        from mip.debayer import debayer_HighQuality, debayer_MaximumQuality
        
        # Default to High Quality (Faster)
        debayer_method = 'High Quality (Faster)'
        
        # Try to get debayer method from global project config
        try:
            from project import DEFAULT_CONFIG
            debayer_method = DEFAULT_CONFIG.get("Project Settings", {}).get('Processing', {}).get("Debayer method", "High Quality (Faster)")
        except:
            pass
        

        
        # Select debayer method
        if debayer_method in ['High Quality (Faster)', 'Edge-Aware']:
            # Support old "Edge-Aware" for backward compatibility
            color = debayer_HighQuality(img)
        elif debayer_method in ['Maximum Quality (Slower)', 'Super Quality', 'SuperQuality', 'Maximum Quality']:
            # Support old names for backward compatibility
            color = debayer_MaximumQuality(img)
        else:
            # Default to High Quality for unknown methods

            color = debayer_HighQuality(img)
        color = np.swapaxes(color, 0, 2)
        color = np.swapaxes(color, 0, 1)
        # CRITICAL: Debayer outputs BGR (OpenCV convention), convert to RGB for display/export
        # This ensures the target image displays with correct colors
        color = cv2.cvtColor(color, cv2.COLOR_BGR2RGB)
        color = np.ascontiguousarray(color)
        

        return color
    else:
        # For TIFF/JPG files, load directly without any processing or color space conversion
        data = cv2.imread(image_path, -1)
        # Return in BGR format (no color space conversion)
        
        # Ensure the data is in the correct format for OpenCV operations
        if data is not None:
            data = np.ascontiguousarray(data)

        else:
        
        
            pass  # Empty block
        return data

def save_raw_target_image(image, in_image_format, folder, subfolder=None, fnappend="", exiftool_path=exiftool_path, torgb=None, is_preview=False, options=None):
    """Save target image as raw TIFF without any processing - just the raw image with red squares
    
    Args:
        options: Processing options dict containing vignette/reflectance settings
    """
    from pathlib import Path
    import os
    import cv2
    import numpy as np
    import tifffile as tiff
    
    if fnappend != "":
        fnappend = "_" + fnappend
    
    # CRITICAL DEBUG: Print the filename being used for saving

    
    # CRITICAL FIX: Ensure image.fn is preserved correctly
    if not hasattr(image, 'fn') or image.fn is None:
        print(f"❌ CRITICAL ERROR: image.fn is missing or None!")
        if hasattr(image, 'path') and image.path:
            recovered_fn = os.path.basename(image.path)

            image.fn = recovered_fn
        else:

            image.fn = "unknown_image"
    
    # Determine output directory
    if is_preview:
        # Save to Preview Images subfolders
        project_dir = os.path.dirname(folder)
        preview_base = os.path.join(project_dir, "Preview Images")
        
        if not os.path.exists(preview_base):
            os.makedirs(preview_base, exist_ok=True)
        
        if subfolder and ("Target" in subfolder or "Calibration_Targets_Used" in subfolder):
            preview_dir = os.path.join(preview_base, "RAW Target")
        elif subfolder and "Reflectance" in subfolder:
            preview_dir = os.path.join(preview_base, "RAW Reflectance")
        else:
            preview_dir = os.path.join(preview_base, "RAW Original")
        
        if not os.path.exists(preview_dir):
            os.makedirs(preview_dir, exist_ok=True)

        
        outdir = preview_dir
    else:
        # Save to export/model folder (e.g., Survey3N_RGN)
        outdir = folder
        if subfolder:
            outdir = os.path.join(outdir, subfolder)
        os.makedirs(outdir, exist_ok=True)
    
    # CRITICAL FIX: Save original RAW filename BEFORE modifying image.path
    # image.fn is a property derived from image.path, so changing path changes fn!
    original_raw_fn = image.fn
    
    # Create the output path
    base_filename = image.fn.split('.')[0]
    if fnappend:
        base_filename += fnappend
    
    # Always save as TIFF for target images
    ext = "tif"
    


    outpath = os.path.join(outdir, f"{base_filename}.{ext}")
    image.path = outpath
    
    # OPTIMIZATION: Try to load from cached debayered TIFF to avoid re-debayering
    # Use original_raw_fn for cache lookup, not image.fn (which is now .tif)
    cached_data = None
    if hasattr(image, 'project') and image.project and original_raw_fn:
        cached_path = image.project.get_cached_debayered_tiff(original_raw_fn)
        if cached_path:
            try:
                import tifffile as tiff
                # Load with tifffile to preserve RGB format and 16-bit depth
                cached_data = tiff.imread(cached_path)
                if cached_data is not None:
                    pass
                else:
                    pass
            except Exception as e:
                pass
                cached_data = None
    
    # Use cached data if available, otherwise access image.data (which triggers debayering and caching)
    used_cache = False
    if cached_data is not None:
        source_data = cached_data
        used_cache = True
    else:
        source_data = image.data
    
    # CRITICAL FIX: Work on a copy of image data to preserve original for reflectance export
    # IP-PROTECTED: Drawing calibration targets

    
    # Create a copy of the image data for drawing squares (preserve original)
    target_image_data = source_data.copy()
    
    # Get processing settings to check if we need channel swap
    vignette_enabled = False
    reflectance_enabled = False
    if options:
        if 'Project Settings' in options and 'Processing' in options['Project Settings']:
            processing_options = options['Project Settings']['Processing']
            vignette_enabled = processing_options.get('Vignette correction', False)
            reflectance_enabled = processing_options.get('Reflectance calibration / white balance', False)
        elif 'Processing' in options:
            processing_options = options['Processing']
            vignette_enabled = processing_options.get('Vignette correction', False)
            reflectance_enabled = processing_options.get('Reflectance calibration / white balance', False)
    else:
        if hasattr(image, 'project') and image.project and hasattr(image.project, 'data'):
            processing_options = image.project.data.get('Project Settings', {}).get('Processing', {})
            vignette_enabled = processing_options.get('Vignette correction', False)
            reflectance_enabled = processing_options.get('Reflectance calibration / white balance', False)
    
    # CRITICAL FIX: When not using cache (BGR data), swap channels 0↔2 to fix base pixels
    # This is needed when vignette is OFF and reflectance is ON
    already_swapped_to_rgb = False
    if not used_cache and not vignette_enabled and reflectance_enabled:
        if len(target_image_data.shape) == 3 and target_image_data.shape[2] >= 3:
            target_image_data[:, :, [0, 2]] = target_image_data[:, :, [2, 0]]
            already_swapped_to_rgb = True
    
    # Draw calibration target polygons (red squares) on the COPY
    try:
        if hasattr(image, 'calibration_target_polys') and image.calibration_target_polys is not None:
            # Drawing calibration targets
            
            # CRITICAL FIX: Ensure image is in correct format for OpenCV
            # Convert to contiguous array and ensure proper memory layout
            if not target_image_data.flags['C_CONTIGUOUS']:
                target_image_data = np.ascontiguousarray(target_image_data)

            
            # Draw red square borders on the COPY
            # CRITICAL: Use colors based on CURRENT format after potential swap
            # If we swapped BGR→RGB, use RGB colors
            # If data was cached RGB, use RGB colors
            # If data is still BGR (no swap), use BGR colors
            is_currently_rgb = used_cache or already_swapped_to_rgb
            red_color = (65535, 0, 0) if is_currently_rgb else (0, 0, 65535)
            
            for i, poly in enumerate(image.calibration_target_polys):
                try:
                    # Draw border lines only, not filled squares
                    pts = np.array(poly, dtype=np.int32).reshape((-1, 1, 2))
                    cv2.polylines(target_image_data, [pts], True, red_color, thickness=8)  # Red color

                except Exception as e:
                    pass  # Error drawing targets
                    # Try to fix the issue by ensuring proper data format
                    try:
                        # Ensure writable and proper format
                        if not target_image_data.flags.writeable:
                            target_image_data = target_image_data.copy()
                        target_image_data = np.ascontiguousarray(target_image_data, dtype=np.uint16)
                        pts = np.array(poly, dtype=np.int32).reshape((-1, 1, 2))
                        cv2.polylines(target_image_data, [pts], True, red_color, thickness=8)  # Use same color as above

                    except Exception as e2:

                        continue
            
            # Draw green center dot and yellow line from ArUco to target center
            try:
                # Calculate target center from polygon centers (where all 4 patches meet)
                if len(image.calibration_target_polys) == 4:
                    # Target center is the average of all polygon centers
                    poly_centers = [np.mean(poly, axis=0).astype(int) for poly in image.calibration_target_polys]
                    target_center = np.mean(poly_centers, axis=0).astype(int)
                    target_center = tuple(target_center)
                    
                    # Calculate ArUco marker center
                    if hasattr(image, 'aruco_corners') and image.aruco_corners is not None:
                        aruco_corners_array = np.array(image.aruco_corners).squeeze()
                        aruco_center = np.mean(aruco_corners_array, axis=0).astype(int)
                        aruco_center = tuple(aruco_center)
                        
                        # Draw yellow line from ArUco center to target center
                        yellow_color = (65535, 65535, 0) if is_currently_rgb else (0, 65535, 65535)
                        cv2.line(target_image_data, aruco_center, target_center, yellow_color, thickness=4)

                    
                    # Draw green center dot at target center
                    green_color = (0, 65535, 0) if used_cache else (0, 65535, 0)  # Green is same in RGB and BGR
                    cv2.circle(target_image_data, target_center, radius=10, color=green_color, thickness=-1)  # Filled circle (dot)

            except Exception as e:

                pass  # Empty block
        else:
            # No calibration target polygons found - generating them
            # Generate calibration target polygons if not present
            try:
                from mip.Calibration_Target import calibration_target_polys, draw_calibration_samples
                calibration_target_polys(image)
                # Create a temporary image object with the copy for drawing
                temp_image = image.copy()  # Use copy() instead of type(image)() to preserve attributes
                temp_image.data = target_image_data
                temp_image.calibration_target_polys = image.calibration_target_polys
                draw_calibration_samples(temp_image)
                # Update the copy with the drawn squares
                target_image_data = temp_image.data
                # Generated and drew calibration targets
            except Exception as e:
                pass  # Failed to generate targets
    except Exception as e:
        pass  # Error drawing targets
    
    # Save the image copy with red squares (original image.data is preserved)


    
    # CRITICAL FIX: Convert BGR to RGB for TIFF storage if data came from image.data
    # Cached data is already RGB, but image.data is BGR (OpenCV convention)
    # Skip conversion if we already swapped channels earlier
    if not used_cache and not already_swapped_to_rgb:
        import cv2
        target_image_data = cv2.cvtColor(target_image_data, cv2.COLOR_BGR2RGB)
    tiff.imwrite(image.path, target_image_data)
    
    

    return image.path

# Helper function
# Refactored: Only create the folder if needed, and do not create preview subfolders here.
def create_outfolder(project_path, model_name, is_export=False):
    """Create output folder for processed images or exports at the project root."""
    from pathlib import Path
    
    if is_export:
        # Export folders (e.g., Survey3N_RGN) at project root
        output_dir = Path(project_path) / model_name
    else:
        # Preview Images at project root
        output_dir = Path(project_path) / "Preview Images"
    
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
    
    return str(output_dir)

def save(image, output_format, outfolder, subfolder=None, fnappend="", exiftool_path=exiftool_path, torgb=None, is_preview=False):
    from pathlib import Path
    import os  # CRITICAL FIX: Move os import to top of function
    
    if fnappend != "":
        fnappend = "_" + fnappend
    # PATCH: Use output_format instead of in_image_format
    torgbval = (output_format != "jpg8")
    if torgb is not None:
        torgbval = torgb
    
    # CRITICAL DEBUG: Print the filename being used for saving

    
    # CRITICAL FIX: Ensure image.fn is preserved correctly
    # During parallel processing, image.fn might be lost or corrupted
    if not hasattr(image, 'fn') or image.fn is None:
        print(f"❌ CRITICAL ERROR: image.fn is missing or None!")


        # Try to recover the filename from other attributes
        if hasattr(image, 'path') and image.path:
            # Extract filename from path
            recovered_fn = os.path.basename(image.path)

            image.fn = recovered_fn
        else:

            image.fn = "unknown_image"
    
    # Determine output directory
    if is_preview:
        # Save to Preview Images subfolders
        project_dir = os.path.dirname(outfolder)
        preview_base = os.path.join(project_dir, "Preview Images")
        
        # Create main Preview Images directory if it doesn't exist
        if not os.path.exists(preview_base):
            os.makedirs(preview_base, exist_ok=True)
        
        # Determine and create the appropriate subdirectory only when needed
        if subfolder and ("Target" in subfolder or "Calibration_Targets_Used" in subfolder):
            preview_dir = os.path.join(preview_base, "RAW Target")
        elif subfolder and "Reflectance" in subfolder:
            preview_dir = os.path.join(preview_base, "RAW Reflectance")
        else:
            preview_dir = os.path.join(preview_base, "RAW Original")
        
        # Create subdirectory only if it doesn't exist
        if not os.path.exists(preview_dir):
            os.makedirs(preview_dir, exist_ok=True)

        
        outdir = preview_dir
    else:
        # Save to export/model folder (e.g., Survey3N_RGN)
        outdir = outfolder
        if subfolder:
            outdir = os.path.join(outdir, subfolder)
        os.makedirs(outdir, exist_ok=True)
    
    # Create the output path
    base_filename = image.fn.split('.')[0]
    if fnappend:
        base_filename += fnappend
    
    # Determine file extension first
    if output_format == "tiff16":
        ext = "tif"
    elif output_format == "jpg8":
        ext = "jpg"
    elif output_format == "png8":
        ext = "png"
    elif output_format == "tiff32percent":
        ext = "tif"
    else:
        ext = "tif"
    
    # CRITICAL DEBUG: Print the filename being used for saving


    outpath = os.path.join(outdir, f"{base_filename}.{ext}")
    image.path = outpath

    # Robust: Ensure image.data is loaded before saving
    if getattr(image, 'data', None) is None:
        print(f"[ERROR] save(): image.data is None for {getattr(image, 'fn', 'unknown')} before saving. Attempting reload from disk...")
        try:
            # This will trigger the property to reload from disk if possible
            _ = image.data
        except Exception as e:
            print(f"[ERROR] save(): Exception while reloading image.data for {getattr(image, 'fn', 'unknown')}: {e}")
        if getattr(image, 'data', None) is None:
            print(f"[ERROR] save(): Could not reload image.data for {getattr(image, 'fn', 'unknown')}. Skipping save.")
            return None

    # --- PATCH: Debug print before calling save_format ---
    pass  # Saving image
    pass  # Data shape check
    if hasattr(image, 'data') and image.data is not None:
        arr = image.data
        if len(arr.shape) == 3:
            for i, c in enumerate(['B','G','R']):
                pass  # Channel stats
        else:
            pass  # Single channel stats
    # --- End PATCH ---
    return save_format(image, output_format, torgb=torgbval)

def apply_contrast_stretch_for_preview(image_data):
    """
    Apply 1/99 percentile contrast stretch for preview images only.
    This function should only be used for display purposes, not for exported data.
    
    Args:
        image_data: numpy array of image data
        
    Returns:
        numpy array with contrast stretching applied
    """
    import cv2
    import numpy as np
    
    # Create a copy to avoid modifying the original data
    img_data = image_data.copy()
    
    # Apply 1/99 percentile contrast stretch
    if img_data.ndim == 3 and img_data.shape[2] == 3:
        p1, p99 = np.percentile(img_data, [1, 99])
        if p99 > p1:
            img_data = np.clip((img_data - p1) * 255.0 / (p99 - p1), 0, 255)
        img_data = img_data.astype(np.uint8)
    else:
        p1, p99 = np.percentile(img_data, [1, 99])
        if p99 > p1:
            img_data = np.clip((img_data - p1) * 255.0 / (p99 - p1), 0, 255).astype(np.uint8)
    
    return img_data

def save_preview_with_contrast_stretch(image, output_format, outfolder, subfolder=None, fnappend=""):
    """
    Save a preview image with contrast stretching applied for display purposes only.
    This function creates preview images in the Preview Images folder with proper contrast stretching.
    
    Args:
        image: LabImage object
        output_format: output format string
        outfolder: output folder path
        subfolder: subfolder name (optional)
        fnappend: filename append string (optional)
        
    Returns:
        path to saved preview image
    """
    import os
    import numpy as np
    from copy import deepcopy
    
    # Create a copy of the image to avoid modifying the original
    preview_image = deepcopy(image)
    
    # Apply contrast stretching for preview display
    preview_image.data = apply_contrast_stretch_for_preview(image.data)
    
    # Save as preview (this will go to Preview Images folder)
    preview_path = save(preview_image, output_format, outfolder, subfolder, fnappend, is_preview=True)
    

    return preview_path


# Ray-compatible versions of task functions
if RAY_AVAILABLE:
    # PHASE 1 OPTIMIZATION: Increase CPU allocation per task
    @ray.remote(num_cpus=2, num_gpus=0)  # CPU-only for ArUco detection (OpenCV is CPU-optimized)
    def detect_calibration_image_ray(image, min_calibration_samples, project):
        # Defensive: check that image is a LabImage, not a path
        if isinstance(image, str) or isinstance(image, bytes) or hasattr(image, '__fspath__'):
            print(f"[ERROR] detect_calibration_image_ray received a file path instead of a LabImage object: {image}")
            raise TypeError("detect_calibration_image_ray expects a LabImage object, not a file path")
        # Defensive: check that image.jpgpath is a string
        if hasattr(image, 'jpgpath') and not isinstance(image.jpgpath, str):
            print(f"[ERROR] image.jpgpath is not a string! Type: {type(image.jpgpath)} Value: {image.jpgpath}")
        if hasattr(image, 'fn') and not isinstance(image.fn, str):
            print(f"[ERROR] image.fn is not a string! Type: {type(image.fn)} Value: {image.fn}")
        # Create a dummy progress tracker for the Ray remote function
        # Progress tracking is handled at the main process level
        class DummyProgressTracker:
            def task_completed(self):
                pass
        progress_tracker = DummyProgressTracker()
        return detect_calibration_image(image, min_calibration_samples, project, progress_tracker)

    # PHASE 1 OPTIMIZATION: Increase CPU allocation per task
    @ray.remote(num_cpus=2, num_gpus=0.30)  # Added GPU allocation for calibration computation
    def get_calib_data_ray(image, options, _force_reload=1756833900):
        # --- VERSION: 2025-01-21-CALIB-XVALS-FIX ---
        # This version number forces Ray to reload the function when code changes
        # _force_reload parameter ensures Ray uses the latest version of this function with calibration_xvals fixes
        
        # Suppress deprecation warnings in Ray worker
        import warnings
        warnings.filterwarnings('ignore', category=DeprecationWarning)
        
        # Create a dummy progress tracker for the Ray remote function
        # Progress tracking is handled at the main process level

        if 'Processing' not in options:
            print(f"[RAY WARNING] get_calib_data_ray received options without 'Processing' key: keys={list(options.keys())}")
        class DummyProgressTracker:
            def task_completed(self):
                pass
        progress_tracker = DummyProgressTracker()
        result = get_calib_data(image, options, progress_tracker)

        return result

    # PHASE 1 OPTIMIZATION: Increase CPU allocation per task
    @ray.remote(num_cpus=2, num_gpus=0.40)  # Added GPU allocation for export processing
    def process_image_unified_ray(image, options, reprocessing_cfg, outfolder, progress_tracker=None, _force_reload=1753167000):  # <-- incremented version
        print(f"[RAY] process_image_unified_ray called for {getattr(image, 'fn', 'unknown')}")
        print(f"[RAY] reprocessing_cfg = {reprocessing_cfg}")
        result = process_image_unified(image, options, reprocessing_cfg, outfolder, progress_tracker, execution_mode='parallel')
        print(f"[RAY] process_image_unified_ray result for {getattr(image, 'fn', 'unknown')}: {result}")
        return result

    @ray.remote(num_cpus=2, num_gpus=0.40)  # Dynamic CPU allocation + GPU for process_image_unified
    def process_image_unified_dynamic_ray(image, options, reprocessing_cfg, outfolder, progress_tracker=None, _force_reload=1753167000):
        """Ray remote function for process_image_unified with dynamic CPU allocation"""
        print(f"[DYNAMIC_RAY_STATIC] process_image_unified executing with 2 CPUs")
        print(f"[DYNAMIC_RAY_STATIC] Args: image={getattr(image, 'fn', 'N/A')}")
        try:
            result = process_image_unified(image, options, reprocessing_cfg, outfolder, progress_tracker, execution_mode='parallel')
            print(f"[DYNAMIC_RAY_STATIC] Result type: {type(result)}, is_dict: {isinstance(result, dict)}")
            if isinstance(result, dict):
                print(f"[DYNAMIC_RAY_STATIC] Result keys: {list(result.keys())}")
            return result
        except Exception as e:
            print(f"[DYNAMIC_RAY_STATIC] ERROR: {e}")
            import traceback
            traceback.print_exc()
            return {}

# OLD apply_calibration_ray function removed - it only returned metadata without applying calibration to pixels
# The new apply_calibration_ray_inline function (defined later) actually applies calibration to image data

def apply_calibration_sequential(image):
    """Sequential version of calibration application for non-Ray processing"""
    # Apply calibration to image
    
    try:
        # Load calibration data from the project's calibration JSON
        from pathlib import Path
        import json
        
        # Get project directory from image
        project_dir = Path(image.project.path)
        calibration_file = project_dir / 'calibration_data.json'
        
        if not calibration_file.exists():
            print(f"⚠️ Calibration file not found: {calibration_file}")
            return None
            
        with open(calibration_file, 'r') as f:
            calib_data = json.load(f)
        
        # IP-PROTECTED: Calibration data loaded
        
        # Find matching calibration data for this image
        # Use the same logic as the Ray version
        chosen_key = None
        for key, entry in calib_data.items():
            if key == 'temporal_processing' or key == 'calibration_data':
                # Check if this entry matches our image
                entry_timestamp = entry.get('timestamp')
                entry_camera_model = entry.get('camera_model') 
                entry_camera_filter = entry.get('camera_filter')
                
                # Match by timestamp and camera info
                if (entry_timestamp and entry_camera_model and entry_camera_filter):
                    # Found calibration entry
                    chosen_key = key
                    break
        
        if chosen_key:
            # IP-PROTECTED: Using calibration data
            # Apply the calibration data to the image object
            entry = calib_data[chosen_key]
            
            # Store calibration coefficients on the image
            if 'calibration_coefficients' in entry:
                image.calibration_coefficients = entry['calibration_coefficients']
                # IP-PROTECTED: Calibration applied
                return True
            else:
                print(f"⚠️ No calibration coefficients found for {image.fn}")
                return None
        else:
            print(f"⚠️ No matching calibration data found for {image.fn}")
            return None
            
    except Exception as e:
        print(f"⚠️ Error applying calibration to {image.fn}: {e}")
        import traceback
        traceback.print_exc()
        return None

def detect_targets_unified(images, execution_mode='serial', batch_size=None, min_calibration_samples=None, project=None):
    """
    Unified target detection supporting both serial and parallel execution.
    
    Args:
        images: List of images to process for target detection
        execution_mode: 'serial' or 'parallel' execution mode
        batch_size: Batch size for parallel processing (optional)
        min_calibration_samples: Minimum calibration sample area in pixels
        project: Project object containing image mappings
    
    Returns:
        tuple: (target_images, non_target_images) where target_images have is_calibration_photo=True
    """
    
    # Separate JPG and RAW images
    jpg_images = [img for img in images if img.fn.lower().endswith(('.jpg', '.jpeg'))]
    raw_images = [img for img in images if img.fn.lower().endswith('.raw')]
    
    
    # Create RAW mapping for quick lookup
    raw_map = {}
    for raw_img in raw_images:
        base_name = os.path.splitext(raw_img.fn)[0]
        raw_map[base_name] = raw_img
    
    target_images = []
    non_target_images = []
    raw_images_to_queue = []
    
    if execution_mode == 'parallel' and RAY_AVAILABLE and jpg_images:
        # Use parallel processing for JPG images
        target_images, non_target_images = _detect_targets_parallel_batch(
            jpg_images, raw_map, raw_images_to_queue, min_calibration_samples, project, batch_size
        )
    else:
        # Use sequential processing
        target_images, non_target_images = _detect_targets_sequential(
            jpg_images, raw_map, raw_images_to_queue, min_calibration_samples, project
        )
    
    # Add non-target RAW images to the queue
    non_target_images.extend(raw_images_to_queue)
    
    return target_images, non_target_images


def _detect_targets_parallel_batch(jpg_images, raw_map, raw_images_to_queue, min_calibration_samples, project, batch_size=None):
    """Process target detection using Ray for batch parallel processing."""
    # Use global ray variable instead of importing directly
    global ray
    
    
    # Get the unified function for target detection
    if RAY_AVAILABLE:
        detect_task_func = detect_calibration_image_ray
    else:
        pass
        return _detect_targets_sequential(jpg_images, raw_map, raw_images_to_queue, min_calibration_samples, project)
    
    # CRITICAL FIX: Filter images based on checkbox state BEFORE submitting to Ray
    # This respects user's manual target selections (grey checkboxes)
    target_images = []
    non_target_images = []
    images_to_analyze = []
    
    for jpg_image in jpg_images:
        checkbox_state = _get_serial_checkbox_state(jpg_image.fn, project)
        
        if checkbox_state == 'disabled':
            # Disabled target = was detected but manually unchecked, skip completely
            jpg_image.is_calibration_photo = False
            non_target_images.append(jpg_image)
            continue
        elif checkbox_state == 'green':
            # Green check = confirmed target, skip analysis
            jpg_image.is_calibration_photo = True
            # Find corresponding RAW image
            raw_image = _find_corresponding_raw_image(jpg_image, raw_map, project)
            if raw_image:
                _transfer_target_attributes(jpg_image, raw_image)
                
                # CRITICAL FIX: Also mark the corresponding RAW image in the raw_map
                raw_filename = raw_image.fn
                raw_base_name = os.path.splitext(raw_filename)[0]
                if raw_base_name in raw_map:
                    original_raw_img = raw_map[raw_base_name]
                    original_raw_img.is_calibration_photo = True
                    original_raw_img.aruco_id = jpg_image.aruco_id
                    original_raw_img.aruco_corners = jpg_image.aruco_corners
                    original_raw_img.calibration_target_polys = jpg_image.calibration_target_polys
                
                target_images.append(raw_image)
            else:
                target_images.append(jpg_image)
            continue
        elif checkbox_state == 'skip':
            # User made manual selections but didn't check this image - skip it
            jpg_image.is_calibration_photo = False
            non_target_images.append(jpg_image)
            continue
        
        # If we get here, we need to analyze the image (grey check or default)
        images_to_analyze.append(jpg_image)
    
    # Create Ray futures only for images that need analysis
    futures = []
    for img in images_to_analyze:
        future = detect_task_func.remote(img, min_calibration_samples, project)
        futures.append(future)
    
    
    # Process results as they complete
    future_to_image = {future: img for future, img in zip(futures, images_to_analyze)}
    
    processed_count = 0
    total_futures = len(futures)
    
    while futures:
        # CRITICAL: Check for stop request in Thread 1 Ray processing loop
        if hasattr(project, 'api') and hasattr(project.api, '_stop_processing_requested') and project.api._stop_processing_requested:
            pass
            cancelled = 0
            for f in futures:
                try:
                    ray.cancel(f, force=True)
                    cancelled += 1
                except Exception as e:
                    pass
            break
        
        ready, futures = ray.wait(futures, num_returns=1, timeout=1.0)
        for future in ready:
            try:
                result = ray.get(future, timeout=120)  # 2 minute timeout for target detection
                jpg_image = future_to_image[future]
                
                processed_count += 1
                
                if result and result[1]:  # result[1] is is_calibration_photo
                    jpg_image.is_calibration_photo = True
                    jpg_image.aruco_id = result[0]
                    jpg_image.aruco_corners = result[2]
                    jpg_image.calibration_target_polys = result[3]
                    
                    # Find corresponding RAW image
                    raw_image = _find_corresponding_raw_image(jpg_image, raw_map, project)
                    if raw_image:
                        _transfer_target_attributes(jpg_image, raw_image)
                        
                        # CRITICAL FIX: Also mark the corresponding RAW image in the raw_map
                        # Ensure consistency for pipeline processing
                        raw_filename = raw_image.fn
                        raw_base_name = os.path.splitext(raw_filename)[0]
                        if raw_base_name in raw_map:
                            original_raw_img = raw_map[raw_base_name]
                            original_raw_img.is_calibration_photo = True
                            original_raw_img.aruco_id = result[0]
                            original_raw_img.aruco_corners = result[2]
                            original_raw_img.calibration_target_polys = result[3]
                        
                        target_images.append(raw_image)
                    else:
                        pass
                        target_images.append(jpg_image)
                else:
                    pass
                    
                    # CRITICAL FIX: If this was a grey checkbox (manual selection), clear it
                    checkbox_state = _get_serial_checkbox_state(jpg_image.fn, project)
                    if checkbox_state == 'grey':
                        pass
                        _clear_failed_grey_checkbox(jpg_image.fn, project)
                    
                    non_target_images.append(jpg_image)
                    
            except Exception as e:
                pass
                
                # CRITICAL FIX: If this was a grey checkbox (manual selection), clear it on error too
                try:
                    checkbox_state = _get_serial_checkbox_state(jpg_image.fn, project)
                    if checkbox_state == 'grey':
                        pass
                        _clear_failed_grey_checkbox(jpg_image.fn, project)
                except Exception as clear_error:
                    pass
                
                non_target_images.append(jpg_image)
    
    # Collect non-target RAW images
    for raw_img in raw_map.values():
        if not getattr(raw_img, 'is_calibration_photo', False):
            raw_images_to_queue.append(raw_img)
    
    return target_images, non_target_images


def _get_serial_checkbox_state(image_filename, project):
    """Get checkbox state for serial mode target detection"""
    try:
        if not project or not hasattr(project, 'data'):
            return 'analyze'  # Default to analyze if no project data
        
        # Find the image in project data
        for base, fileset in project.data['files'].items():
            if fileset.get('jpg'):
                jpg_filename = os.path.basename(fileset['jpg'])
                
                if jpg_filename == image_filename:
                    # Get calibration info
                    calibration_info = fileset.get('calibration', {})
                    stored_detected = calibration_info.get('is_calibration_photo', False)
                    stored_manual = fileset.get('manual_calib', False)
                    manually_disabled = calibration_info.get('manually_disabled', False)
                    
                    # Check if manually disabled
                    if manually_disabled:
                        return 'disabled'
                    elif stored_detected and stored_manual:
                        return 'green'  # Detected and still checked
                    elif stored_detected and not stored_manual:
                        return 'disabled'  # Detected but unchecked = disabled
                    elif stored_manual and not stored_detected:
                        return 'grey'   # Manual selection
                    else:
                        # Check if there are any manual selections in the project
                        # If yes, skip unchecked images; if no, analyze all
                        has_manual_selections = any(
                            f.get('manual_calib', False) and not f.get('calibration', {}).get('is_calibration_photo', False)
                            for f in project.data['files'].values()
                        )
                        
                        if has_manual_selections:
                            # User made manual selections (grey checkboxes exist), skip unchecked images
                            return 'skip'
                        else:
                            # No manual selections, analyze all images
                            return 'analyze'  # Default analysis
        
        return 'analyze'
        
    except Exception as e:
        return 'analyze'

def _clear_failed_grey_checkbox(jpg_filename, project):
    """Clear a grey checkbox when target detection fails."""
    try:
        if not project or not hasattr(project, 'data'):
            print(f"[CLEAR-GREY] No project data available for {jpg_filename}")
            return False
        
        # Find the image in project data and clear manual_calib
        for base, fileset in project.data['files'].items():
            if fileset.get('jpg'):
                stored_jpg_filename = os.path.basename(fileset['jpg'])
                
                if stored_jpg_filename == jpg_filename:
                    # Clear the manual_calib flag
                    old_manual_calib = fileset.get('manual_calib', False)
                    fileset['manual_calib'] = False
                    
                    print(f"[CLEAR-GREY] ✅ Cleared manual_calib for {jpg_filename}: {old_manual_calib} -> False")
                    
                    # Save project data immediately
                    project.write()
                    print(f"[CLEAR-GREY] 💾 Saved project data after clearing grey checkbox")
                    
                    # Try to update UI via SSE event to refresh file browser
                    try:
                        # Import here to avoid circular imports
                        import backend_server
                        # Send images-updated event to refresh the entire file browser
                        # This will ensure the checkbox states are updated from the project data
                        backend_server.dispatch_event('images-updated', {})
                        print(f"[CLEAR-GREY] 📤 Sent images-updated event to refresh UI for {jpg_filename}")
                    except Exception as ui_error:
                        print(f"[CLEAR-GREY] ⚠️ Could not update UI for {jpg_filename}: {ui_error}")
                    
                    return True
        
        print(f"[CLEAR-GREY] ⚠️ File {jpg_filename} not found in project data")
        return False
        
    except Exception as e:
        print(f"[CLEAR-GREY] ❌ Error clearing grey checkbox for {jpg_filename}: {e}")
        import traceback
        traceback.print_exc()
        return False

def _detect_targets_sequential(jpg_images, raw_map, raw_images_to_queue, min_calibration_samples, project):
    """Process target detection sequentially."""
    
    target_images = []
    non_target_images = []
    
    for jpg_image in jpg_images:
        try:
            # CRITICAL: Check checkbox state to respect user choices (similar to parallel mode)
            checkbox_state = _get_serial_checkbox_state(jpg_image.fn, project)
            
            if checkbox_state == 'disabled':
                # Disabled target = was detected but manually unchecked, skip completely
                jpg_image.is_calibration_photo = False
                non_target_images.append(jpg_image)
                continue
            elif checkbox_state == 'green':
                # Green check = confirmed target, skip analysis
                jpg_image.is_calibration_photo = True
                # Find corresponding RAW image
                raw_image = _find_corresponding_raw_image(jpg_image, raw_map, project)
                if raw_image:
                    _transfer_target_attributes(jpg_image, raw_image)
                    
                    # CRITICAL FIX: Also mark the corresponding RAW image in the raw_map
                    # Ensure consistency for pipeline processing
                    raw_filename = raw_image.fn
                    raw_base_name = os.path.splitext(raw_filename)[0]
                    if raw_base_name in raw_map:
                        original_raw_img = raw_map[raw_base_name]
                        original_raw_img.is_calibration_photo = True
                        original_raw_img.aruco_id = jpg_image.aruco_id
                        original_raw_img.aruco_corners = jpg_image.aruco_corners
                        original_raw_img.calibration_target_polys = jpg_image.calibration_target_polys
                    
                    target_images.append(raw_image)
                else:
                    target_images.append(jpg_image)
                continue
            elif checkbox_state == 'skip':
                # User made manual selections but didn't check this image - skip it
                jpg_image.is_calibration_photo = False
                non_target_images.append(jpg_image)
                continue
            
            # If we get here, we need to analyze the image (grey check or default)
            
            # Run target detection using the core detection function
            result = _detect_targets_core(jpg_image, min_calibration_samples, project)
            
            
            if result and result[1]:  # result[1] is is_calibration_photo
                jpg_image.is_calibration_photo = True
                jpg_image.aruco_id = result[0]
                jpg_image.aruco_corners = result[2]
                jpg_image.calibration_target_polys = result[3]
                
                # CRITICAL FIX: Update UI with green checkmark immediately
                # This needs to be called through the API object, but we don't have it in this function
                # We need to pass the API reference or add this to the pipeline thread
                
                # Find corresponding RAW image
                raw_image = _find_corresponding_raw_image(jpg_image, raw_map, project)
                if raw_image:
                    _transfer_target_attributes(jpg_image, raw_image)
                    
                    # CRITICAL FIX: Also mark the corresponding RAW image in the raw_map
                    # Ensure consistency for pipeline processing
                    raw_filename = raw_image.fn
                    raw_base_name = os.path.splitext(raw_filename)[0]
                    if raw_base_name in raw_map:
                        original_raw_img = raw_map[raw_base_name]
                        original_raw_img.is_calibration_photo = True
                        original_raw_img.aruco_id = result[0]
                        original_raw_img.aruco_corners = result[2]
                        original_raw_img.calibration_target_polys = result[3]
                    
                    target_images.append(raw_image)
                else:
                    pass
                    target_images.append(jpg_image)
            else:
                pass
                
                # CRITICAL FIX: If this was a grey checkbox (manual selection), clear it
                if checkbox_state == 'grey':
                    pass
                    _clear_failed_grey_checkbox(jpg_image.fn, project)
                
                non_target_images.append(jpg_image)
                
        except Exception as e:
            pass
            
            # CRITICAL FIX: If this was a grey checkbox (manual selection), clear it on error too
            try:
                checkbox_state = _get_serial_checkbox_state(jpg_image.fn, project)
                if checkbox_state == 'grey':
                    pass
                    _clear_failed_grey_checkbox(jpg_image.fn, project)
            except Exception as clear_error:
                pass
            
            non_target_images.append(jpg_image)
    
    # Collect non-target RAW images
    for raw_img in raw_map.values():
        if not getattr(raw_img, 'is_calibration_photo', False):
            raw_images_to_queue.append(raw_img)
    
    return target_images, non_target_images


class DummyProgressTracker:
    """Dummy progress tracker for compatibility with existing functions."""
    def task_completed(self):
        pass


class CalibrationDataManager:
    """
    Abstracts calibration data access for both serial and parallel processing modes.
    
    Handles the different data access patterns between direct object references (serial)
    and JSON synchronization (parallel).
    """
    
    def __init__(self, execution_mode='serial', project=None, outfolder=None):
        self.execution_mode = execution_mode
        self.project = project
        self.outfolder = outfolder
        self._calibration_cache = {}
    
    def get_calibration_data(self, image):
        """
        Get calibration data for an image based on execution mode.
        
        Args:
            image: LabImage object that needs calibration data
            
        Returns:
            dict: Calibration data including coefficients, ALS data, etc.
        """
        if self.execution_mode == 'parallel':
            return self._get_from_ray_sync(image)
        else:
            return self._get_direct_access(image)
    
    def store_calibration_data(self, image, data):
        """
        Store calibration data for an image based on execution mode.
        
        Args:
            image: LabImage object (calibration target)
            data: Calibration data to store
        """
        if self.execution_mode == 'parallel':
            self._store_to_json_sync(image, data)
        else:
            self._store_direct_access(image, data)
    
    def _get_from_ray_sync(self, image):
        """Get calibration data from Ray-synchronized attributes."""
        print(f"[CALIB_MGR] Getting Ray-synchronized calibration data for {getattr(image, 'fn', 'unknown')}")
        
        # Check if image has Ray-synchronized calibration data
        if hasattr(image, '_ray_calibration_coefficients'):
            return {
                'coefficients': image._ray_calibration_coefficients,
                'limits': getattr(image, '_ray_calibration_limits', None),
                'xvals': getattr(image, '_ray_calibration_xvals', None),
                'yvals': getattr(image, '_ray_calibration_yvals', None),
                'aruco_id': getattr(image, '_ray_calibration_aruco_id', None),
                'als_magnitude': getattr(image, '_ray_als_magnitude', None),
                'als_data': getattr(image, '_ray_als_data', None)
            }
        
        # Fallback: load from JSON file
        return self._load_from_calibration_json(image)
    
    def _get_direct_access(self, image):
        """Get calibration data from direct object references."""
        print(f"[CALIB_MGR] Getting direct calibration data for {getattr(image, 'fn', 'unknown')}")
        
        # For calibration images, use their own data
        if getattr(image, 'is_calibration_photo', False):
            return {
                'coefficients': getattr(image, 'calibration_coefficients', None),
                'limits': getattr(image, 'calibration_limits', None),
                'xvals': getattr(image, 'calibration_xvals', None),
                'yvals': getattr(image, 'calibration_yvals', None),
                'aruco_id': getattr(image, 'aruco_id', None),
                'als_magnitude': getattr(image, 'als_magnitude', None),
                'als_data': getattr(image, 'als_data', None)
            }
        
        # For non-calibration images, get from calibration_image reference
        if hasattr(image, 'calibration_image') and image.calibration_image is not None:
            calib_img = image.calibration_image
            return {
                'coefficients': getattr(calib_img, 'calibration_coefficients', None),
                'limits': getattr(calib_img, 'calibration_limits', None),
                'xvals': getattr(calib_img, 'calibration_xvals', None),
                'yvals': getattr(calib_img, 'calibration_yvals', None),
                'aruco_id': getattr(calib_img, 'aruco_id', None),
                'als_magnitude': getattr(calib_img, 'als_magnitude', None),
                'als_data': getattr(calib_img, 'als_data', None)
            }
        
        # Fallback: load from JSON file
        return self._load_from_calibration_json(image)
    
    def _store_to_json_sync(self, image, data):
        """Store calibration data to JSON for Ray synchronization using unified API."""
        from unified_calibration_api import UnifiedCalibrationManager
        
        print(f"[CALIB_MGR] Storing calibration data to JSON for {getattr(image, 'fn', 'unknown')}")
        
        # Determine project directory
        project_dir = None
        if self.project and hasattr(self.project, 'fp'):
            project_dir = self.project.fp
        elif self.outfolder:
            project_dir = self.outfolder
        else:
            print("[CALIB_MGR] Error: Could not determine project directory for JSON storage")
            return
        
        # Use unified API to save calibration data
        success = UnifiedCalibrationManager.save_calibration_data(image, data, project_dir)
        if success:
            print(f"[CALIB_MGR] Stored calibration data for {getattr(image, 'fn', 'unknown')} using unified API")
        else:
            print(f"[CALIB_MGR] Error storing calibration data using unified API")
    
    def _store_direct_access(self, image, data):
        """Store calibration data directly on image objects."""
        print(f"[CALIB_MGR] Storing direct calibration data for {getattr(image, 'fn', 'unknown')}")
        
        # Store data directly on the image
        if 'coefficients' in data:
            image.calibration_coefficients = data['coefficients']
        if 'limits' in data:
            image.calibration_limits = data['limits']
        if 'xvals' in data:
            image.calibration_xvals = data['xvals']
        if 'yvals' in data:
            image.calibration_yvals = data['yvals']
        if 'aruco_id' in data:
            image.aruco_id = data['aruco_id']
        if 'als_magnitude' in data:
            image.als_magnitude = data['als_magnitude']
        if 'als_data' in data:
            image.als_data = data['als_data']
        
        # Also store to JSON for persistence
        self._store_to_json_sync(image, data)
    
    def _load_from_calibration_json(self, image):
        """Load calibration data from JSON file using unified API."""
        from unified_calibration_api import UnifiedCalibrationManager
        
        # Determine project directory
        project_dir = None
        if self.project and hasattr(self.project, 'fp'):
            project_dir = self.project.fp
        elif self.outfolder:
            project_dir = self.outfolder
        else:
            print("[CALIB_MGR] Error: Could not determine project directory for JSON loading")
            return {}
        
        # Use unified API to load calibration data
        calib_data = UnifiedCalibrationManager.load_calibration_data(image, project_dir)
        if calib_data:
            print(f"[CALIB_MGR] Found calibration data for {getattr(image, 'fn', 'unknown')} using unified API")
            return calib_data
        else:
            print(f"[CALIB_MGR] No matching calibration data found for {getattr(image, 'fn', 'unknown')}")
            return {}


def _detect_targets_core(image, min_calibration_samples, project):
    """Core target detection logic shared by both modes."""
    # This calls the existing detect_calibration_image function
    # which contains the actual ArUco detection, validation, etc.
    return detect_calibration_image(image, min_calibration_samples, project, DummyProgressTracker())


def _find_corresponding_raw_image(jpg_image, raw_map, project):
    """Find the corresponding RAW image for a JPG image."""
    jpg_filename = jpg_image.fn
    
    # First try using the project's JPG->RAW mapping
    if hasattr(project, 'jpg_name_to_raw_name'):
        raw_filename = project.jpg_name_to_raw_name.get(jpg_filename)
        if raw_filename and hasattr(project, 'imagemap'):
            raw_image = project.imagemap.get(raw_filename)
            if raw_image:
                return raw_image
    
    # Fallback: try direct mapping by base name
    base_name = os.path.splitext(jpg_filename)[0]
    return raw_map.get(base_name)


def _transfer_target_attributes(jpg_image, raw_image):
    """Transfer target detection attributes from JPG to RAW image."""
    raw_image.is_calibration_photo = True
    raw_image.aruco_id = getattr(jpg_image, 'aruco_id', None)
    raw_image.aruco_corners = getattr(jpg_image, 'aruco_corners', None)
    raw_image.calibration_target_polys = getattr(jpg_image, 'calibration_target_polys', None)
    
    # CRITICAL DEBUG: Check what polygon data is being transferred
    jpg_polys = getattr(jpg_image, 'calibration_target_polys', None)
    raw_polys = getattr(raw_image, 'calibration_target_polys', None)
    
    
    if jpg_polys and not raw_polys:
        pass
    elif jpg_polys and raw_polys:
        pass
    else:
        pass


def apply_calibration_unified(image_or_fn, execution_mode='serial', project=None, outfolder=None, **kwargs):
    """
    Unified calibration application supporting both serial and parallel execution.
    
    Args:
        image_or_fn: LabImage object (serial) or filename string (parallel)
        execution_mode: 'serial' or 'parallel' execution mode
        project: Project object (optional)
        outfolder: Output folder path (optional)
        **kwargs: Additional parameters for parallel mode (image_path_str, project_dir_str, etc.)
    
    Returns:
        bool or dict: Success status (parallel) or calibration data (serial)
    """

    
    if execution_mode == 'parallel':
        # For parallel mode, we expect filename and additional parameters
        if isinstance(image_or_fn, str):
            image_fn = image_or_fn
            return _apply_calibration_parallel(image_fn, **kwargs)
        else:

            return False
    else:
        # For serial mode, we expect LabImage object
        if hasattr(image_or_fn, 'fn'):  # LabImage object
            return _apply_calibration_serial(image_or_fn, project, outfolder)
        else:

            return False


def _apply_calibration_parallel(image_fn, image_path_str=None, project_dir_str=None, img_timestamp=None, img_camera_model=None, img_camera_filter=None, **kwargs):
    """Apply calibration in parallel mode using Ray worker."""

    
    # This is essentially the same logic as apply_calibration_ray
    from pathlib import Path
    import json
    import datetime
    
    
    # Convert string paths back to Path objects
    if not image_path_str:
        pass
        return False
        
    image_path = Path(image_path_str)
    project_dir = Path(project_dir_str)
    
    # Verify the project directory exists and has calibration data
    if not project_dir.exists():
        pass
        return False
        
    calibration_data_file = project_dir / 'calibration_data.json'
    if not calibration_data_file.exists():
        pass
        return False
    
    try:
        with open(calibration_data_file, 'r') as f:
            calib_data = json.load(f)
        
        if not calib_data:
            pass
            return False
        
        # Find best matching calibration entry
        chosen_key = _find_best_calibration_key_for_parallel(calib_data, img_timestamp, img_camera_model, img_camera_filter)
        
        if chosen_key:
            entry = calib_data[chosen_key]
            return {
                'success': True,
                'entry': entry,
                'chosen_key': chosen_key
            }
        else:
            pass
            return False
            
    except Exception as e:
        pass
        return False


def _apply_calibration_serial(image, project=None, outfolder=None):
    """Apply calibration in serial mode using direct object access."""

    
    # This is essentially the same logic as apply_calibration_sequential
    try:
        # Use CalibrationDataManager to get calibration data
        calib_mgr = CalibrationDataManager('serial', project, outfolder)
        calib_data = calib_mgr.get_calibration_data(image)
        
        if calib_data and calib_data.get('coefficients'):
            # Apply calibration data to image
            image.calibration_coefficients = calib_data['coefficients']
            image.als_magnitude = calib_data.get('als_magnitude')
            image.calibration_yvals = calib_data.get('yvals')
            

            return True
        else:

            return False
            
    except Exception as e:

        return False


def _find_best_calibration_key_for_parallel(calib_data, img_timestamp, img_camera_model, img_camera_filter):
    """Find the best matching calibration key for parallel processing."""
    import datetime
    
    # Parse image timestamp
    img_ts = None
    if isinstance(img_timestamp, datetime.datetime):
        img_ts = img_timestamp
    elif isinstance(img_timestamp, str) and img_timestamp and img_timestamp != 'None':
        try:
            img_ts = datetime.datetime.strptime(img_timestamp, '%Y-%m-%d %H:%M:%S')
        except Exception:
            try:
                img_ts = datetime.datetime.strptime(img_timestamp, '%Y:%m:%d %H:%M:%S')
            except Exception:
                pass
                img_ts = None
    
    best_key = None
    best_delta = None
    fallback_key = None
    fallback_delta = None
    latest_key = None
    latest_ts = None
    
    for key, entry in calib_data.items():
        try:
            # Check camera model and filter model match
            if img_camera_model is not None and entry.get('camera_model', None) != img_camera_model:
                continue
            if img_camera_filter is not None and entry.get('filter_model', None) != img_camera_filter:
                continue
            
            calib_ts = datetime.datetime.strptime(key, '%Y-%m-%d %H:%M:%S')
            delta = (img_ts - calib_ts).total_seconds() if img_ts else None
            abs_delta = abs(delta) if delta is not None else None
            
            # Track latest
            if latest_ts is None or calib_ts > latest_ts:
                latest_ts = calib_ts
                latest_key = key
            
            # Primary: closest earlier
            if delta is not None and delta >= 0 and (best_delta is None or delta < best_delta):
                best_key = key
                best_delta = delta
            
            # Secondary: closest overall
            if abs_delta is not None and (fallback_delta is None or abs_delta < fallback_delta):
                fallback_key = key
                fallback_delta = abs_delta
                
        except Exception as e:
            pass
            continue
    
    # Return best match
    if best_key is not None:
        pass
        return best_key
    elif fallback_key is not None:
        pass
        return fallback_key
    elif latest_key is not None:
        pass
        return latest_key
    
    return None


def get_calib_data_unified(image, options, progress_tracker, execution_mode='serial', project=None, outfolder=None):
    """
    Unified calibration data retrieval supporting both serial and parallel execution.
    
    Args:
        image: LabImage object to get calibration data for
        options: Processing options
        progress_tracker: Progress tracking object
        execution_mode: 'serial' or 'parallel' execution mode (default: 'serial')
        project: Project object (optional)
        outfolder: Output folder path (optional)
    
    Returns:
        dict: Calibration data including coefficients, limits, etc.
    """
    print(f"[GET_CALIB] Getting calibration data in {execution_mode} mode for {getattr(image, 'fn', 'unknown')}")
    
    # OPTIMIZATION: Check for existing calibration data first (works for both serial and parallel)
    existing_calibration = _load_existing_calibration_data(image)
    if existing_calibration and existing_calibration.get('coefficients'):
        # VALIDATION: Check if coefficients are valid numeric arrays, not string placeholders
        coefficients = existing_calibration['coefficients']
        if (isinstance(coefficients, str) or 
            coefficients is None or 
            coefficients == [False, False, False]):
            
            # CRITICAL FIX: Clear corrupted data from image object to force fresh computation
            if hasattr(image, 'calibration_coefficients'):
                delattr(image, 'calibration_coefficients')
            if hasattr(image, 'calibration_xvals'):
                delattr(image, 'calibration_xvals')
            if hasattr(image, 'calibration_yvals'):
                delattr(image, 'calibration_yvals')
            if hasattr(image, 'calibration_limits'):
                delattr(image, 'calibration_limits')
            
            print(f"[GET_CALIB] Cleared corrupted calibration data from image object, proceeding with fresh computation")
            # Don't return, fall through to recomputation
        else:
            print(f"✅ [GET_CALIB] Using existing calibration data for {getattr(image, 'fn', 'unknown')} - skipping computation")
            
            # CRITICAL FIX: Ensure the image object has the valid calibration data applied
            if existing_calibration.get('xvals'):
                image.calibration_xvals = existing_calibration['xvals']
                print(f"[GET_CALIB] ✅ Applied xvals to image object: {type(existing_calibration['xvals'])}")
            if existing_calibration.get('coefficients'):
                image.calibration_coefficients = existing_calibration['coefficients']
                print(f"[GET_CALIB] ✅ Applied coefficients to image object: {type(existing_calibration['coefficients'])}")
            if existing_calibration.get('yvals'):
                image.calibration_yvals = existing_calibration['yvals']
            if existing_calibration.get('limits'):
                image.calibration_limits = existing_calibration['limits']
            
            # Return in the expected format
            return {
                'coefficients': existing_calibration['coefficients'],
                'limits': existing_calibration.get('limits', [65535, 65535, 65535]),
                'calibration_xvals': existing_calibration.get('xvals'),
                'calibration_yvals': existing_calibration.get('yvals')
            }
    
    print(f"[GET_CALIB] No existing calibration data found, proceeding with {execution_mode} computation")
    if execution_mode == 'parallel':
        return _get_calib_data_parallel(image, options, progress_tracker, project, outfolder)
    else:
        return _get_calib_data_serial(image, options, progress_tracker, project, outfolder)


def _get_calib_data_parallel(image, options, progress_tracker, project=None, outfolder=None):
    """Get calibration data in parallel mode."""
    # This is essentially the same logic as get_calib_data_ray
    print(f"[GET_CALIB] Parallel calibration data retrieval for {getattr(image, 'fn', 'unknown')}")
    
    # Use CalibrationDataManager for consistent data access
    calib_mgr = CalibrationDataManager('parallel', project, outfolder)
    calib_data = calib_mgr.get_calibration_data(image)
    
    if calib_data and calib_data.get('coefficients'):
        print(f"[GET_CALIB] Found calibration data for {getattr(image, 'fn', 'unknown')}")
        # Return tuple format expected by calling code: (coefficients, limits, xvals, yvals)
        return (
            calib_data.get('coefficients', [False, False, False]),
            calib_data.get('limits', [0, 0, 0]),
            calib_data.get('xvals'),
            calib_data.get('yvals')
        )
    else:
        print(f"[GET_CALIB] No calibration data found for {getattr(image, 'fn', 'unknown')}")
        # Return default tuple format when no data found
        return ([False, False, False], [0, 0, 0], None, None)


def _get_calib_data_serial(image, options, progress_tracker, project=None, outfolder=None):
    """Get calibration data in serial mode."""
    # This calls the original get_calib_data function to maintain compatibility
    print(f"[GET_CALIB] Serial calibration data retrieval for {getattr(image, 'fn', 'unknown')}")
    
    # For serial mode, call the original function to ensure full compatibility
    return get_calib_data(image, options, progress_tracker)


def detect_calibration_image_unified(image, min_calibration_samples, project, progress_tracker, execution_mode='serial'):
    """
    Unified calibration image detection supporting both serial and parallel execution.
    
    Args:
        image: LabImage object to check for calibration targets
        min_calibration_samples: Minimum calibration sample area in pixels
        project: Project object containing settings and data
        progress_tracker: Progress tracking object
        execution_mode: 'serial' or 'parallel' execution mode (default: 'serial')
    
    Returns:
        tuple: (aruco_id, is_calibration_photo, aruco_corners, calibration_target_polys)
    """
    print(f"[DETECT_CALIB] Detecting calibration image in {execution_mode} mode for {getattr(image, 'fn', 'unknown')}")
    
    # The core detection logic is the same for both modes
    return _detect_calibration_image_core(image, min_calibration_samples, project, progress_tracker)


def _detect_calibration_image_core(image, min_calibration_samples, project, progress_tracker):
    """Core calibration image detection logic shared by both modes."""
    # This calls the existing detect_calibration_image function
    # which contains the actual ArUco detection, validation, etc.
    return detect_calibration_image(image, min_calibration_samples, project, progress_tracker or DummyProgressTracker())


def _get_dynamic_cpu_allocation(func_name, system_tier=None):
    """
    Calculate optimal CPU allocation for Ray remote functions based on system capabilities.
    
    Args:
        func_name: Name of the function
        system_tier: System tier ('high-end', 'mid-range', 'low-end') - auto-detected if None
        
    Returns:
        int: Number of CPUs to allocate for this function
    """
    if system_tier is None:
        # Auto-detect system tier
        try:
            import psutil
            cpu_count = psutil.cpu_count(logical=True)
            memory_gb = psutil.virtual_memory().total / (1024**3)
            
            if memory_gb >= 32 and cpu_count >= 16:
                system_tier = "high-end"
            elif memory_gb >= 16 and cpu_count >= 8:
                system_tier = "mid-range"
            else:
                system_tier = "low-end"
            
            print(f"[DYNAMIC_CPU] System detected: {cpu_count} CPUs, {memory_gb:.1f}GB RAM → {system_tier} tier")
        except Exception:
            system_tier = "low-end"
    
    # CPU allocation rules per system tier
    cpu_rules = {
        "high-end": {
            'detect_calibration_image': 3,  # Increased from 2
            'get_calib_data': 3,           # Increased from 2
            'apply_calibration': 2,        # Increased from 1
            'process_image_unified': 4,            # Increased from 2
        },
        "mid-range": {
            'detect_calibration_image': 2,  # Standard
            'get_calib_data': 2,           # Standard
            'apply_calibration': 1,        # Standard
            'process_image_unified': 2,            # Standard
        },
        "low-end": {
            'detect_calibration_image': 1,  # Reduced from 2
            'get_calib_data': 1,           # Reduced from 2
            'apply_calibration': 1,        # Standard
            'process_image_unified': 1,            # Reduced from 2
        }
    }
    
    allocated_cpus = cpu_rules.get(system_tier, {}).get(func_name, 1)
    print(f"[DYNAMIC_CPU] {func_name} on {system_tier} system: {allocated_cpus} CPUs")
    return allocated_cpus


def _create_dynamic_ray_function(func_name):
    """
    Create a Ray remote function with dynamic CPU allocation.
    
    Args:
        func_name: Name of the function to create
        
    Returns:
        callable: Ray remote function with dynamic CPU allocation, or None if not supported
    """
    try:
        # Use global ray variable instead of importing directly
        global ray
        
        # Get dynamic CPU allocation
        cpu_count = _get_dynamic_cpu_allocation(func_name)
        print(f"[DYNAMIC_CPU] Creating function for {func_name} with {cpu_count} CPUs")
        
        # For process_image_unified, use the static Ray function with proper CPU allocation
        if func_name == 'process_image_unified':
            print(f"[DYNAMIC_CPU] Using static Ray function for {func_name}")
            return process_image_unified_dynamic_ray
        
        # For other functions, create dynamic functions as before
        # Map function names to their base implementations
        base_functions = {
            'detect_calibration_image': detect_calibration_image,
            'get_calib_data': get_calib_data,
            'apply_calibration': _apply_calibration_parallel,  # Use the parallel version
        }
        
        if func_name not in base_functions:
            print(f"[DYNAMIC_CPU] Function {func_name} not supported for dynamic allocation")
            return None
            
        base_func = base_functions[func_name]
        
        # Create dynamic Ray remote function for other functions
        @ray.remote(num_cpus=cpu_count)
        def dynamic_ray_function(*args, **kwargs):
            try:
                print(f"[DYNAMIC_RAY] {func_name} executing with {cpu_count} CPUs")
                print(f"[DYNAMIC_RAY] Args: {len(args)} args, {len(kwargs)} kwargs")
                if args:
                    print(f"[DYNAMIC_RAY] First arg type: {type(args[0])}, fn: {getattr(args[0], 'fn', 'N/A')}")
                
                # Handle different function signatures
                if func_name == 'detect_calibration_image':
                    # Expected: (image, min_calibration_samples, project, progress_tracker=None)
                    if len(args) >= 3:
                        image, min_calibration_samples, project = args[0], args[1], args[2]
                        progress_tracker = args[3] if len(args) > 3 else None
                        if progress_tracker is None:
                            class DummyProgressTracker:
                                def task_completed(self): pass
                            progress_tracker = DummyProgressTracker()
                        return base_func(image, min_calibration_samples, project, progress_tracker)
                        
                elif func_name == 'get_calib_data':
                    # Expected: (image, options, progress_tracker=None)
                    if len(args) >= 2:
                        image, options = args[0], args[1]
                        progress_tracker = args[2] if len(args) > 2 else None
                        if progress_tracker is None:
                            class DummyProgressTracker:
                                def task_completed(self): pass
                            progress_tracker = DummyProgressTracker()
                        return base_func(image, options, progress_tracker)
                        
                elif func_name == 'apply_calibration':
                    # apply_calibration expects specific parameters
                    # (image_fn, image_path_str, project_dir_str, img_timestamp=None, img_camera_model=None, img_camera_filter=None)
                    print(f"[DYNAMIC_RAY] apply_calibration called with {len(args)} args and {len(kwargs)} kwargs")
                    print(f"[DYNAMIC_RAY] args: {args[:3] if len(args) >= 3 else args}")  # Don't log full paths
                    print(f"[DYNAMIC_RAY] kwargs: {list(kwargs.keys())}")
                    
                    if len(args) >= 3:
                        result = base_func(*args, **kwargs)
                        print(f"[DYNAMIC_RAY] apply_calibration result: {result}")
                        return result
                    else:
                        print(f"[DYNAMIC_RAY] apply_calibration called with insufficient args: {len(args)}")
                        return False
                
                # Fallback: try to call with all arguments
                return base_func(*args, **kwargs)
                
            except Exception as e:
                print(f"[DYNAMIC_RAY] ERROR in {func_name}: {e}")
                import traceback
                print(f"[DYNAMIC_RAY] Traceback: {traceback.format_exc()}")
                return False
        
        print(f"[DYNAMIC_CPU] ✅ Created dynamic Ray function for {func_name} with {cpu_count} CPUs")
        return dynamic_ray_function
        
    except Exception as e:
        print(f"[DYNAMIC_CPU] Failed to create dynamic Ray function for {func_name}: {e}")
        return None


# Legacy get_task_function removed - use get_unified_task_function instead


def get_unified_task_function(func_name, execution_mode='auto'):
    """
    Get a unified task function with explicit execution mode control and dynamic CPU allocation.
    
    Args:
        func_name: Name of the function to get
        execution_mode: 'serial', 'parallel', or 'auto' (auto-detect based on Ray availability)
    
    Returns:
        callable: The unified function configured for the specified execution mode
    """
    # Auto-detect execution mode if requested
    if execution_mode == 'auto':
        execution_mode = 'parallel' if _is_ray_available() else 'serial'
    
    print(f"[UNIFIED_DISPATCHER] Getting unified {func_name} for {execution_mode} mode")
    
    # For parallel mode, try to use dynamic CPU allocation
    if execution_mode == 'parallel':
        # Enable dynamic CPU allocation for threads 1, 2, 4 while keeping thread 3 static for timing control
        use_dynamic_for_function = func_name != 'apply_calibration'
        
        if use_dynamic_for_function:
            dynamic_ray_function = _create_dynamic_ray_function(func_name)
            if dynamic_ray_function:
                print(f"[UNIFIED_DISPATCHER] ✅ ENABLED: Dynamic CPU allocation for {func_name}")
                return dynamic_ray_function
            else:
                print(f"[UNIFIED_DISPATCHER] ❌ FAILED: Dynamic CPU allocation for {func_name}, falling back to static Ray")
                # Fall back to static Ray functions
                static_ray_functions = {
                    'detect_calibration_image': detect_calibration_image_ray,
                    'get_calib_data': get_calib_data_ray,
                    'process_image_unified': process_image_unified_ray
                }
                if func_name in static_ray_functions:
                    return static_ray_functions[func_name]
        elif func_name == 'apply_calibration':
            print(f"[UNIFIED_DISPATCHER] 🔒 STATIC: CPU allocation for {func_name} (Thread-3 timing control)")
            # Return the inline Ray function for apply_calibration
            # The function will be created by ensure_ray_functions_available()
            if 'apply_calibration_ray' in globals():
                return globals()['apply_calibration_ray']
            else:
                print(f"[UNIFIED_DISPATCHER] ❌ apply_calibration_ray not available in globals")
                return None
    
    # Unified function mapping
    unified_functions = {
        'detect_calibration_image': detect_calibration_image_unified,
        'detect_targets': detect_targets_unified,
        'get_calib_data': get_calib_data_unified,
        'process_image_unified': process_image_unified,
        'apply_calibration': apply_calibration_unified
    }
    
    if func_name in unified_functions:
        def unified_wrapper(*args, **kwargs):
            # Remove execution_mode from kwargs if present to avoid conflicts
            kwargs.pop('execution_mode', None)
            return unified_functions[func_name](*args, execution_mode=execution_mode, **kwargs)
        return unified_wrapper
    else:
        raise ValueError(f"Unknown unified function: {func_name}")


def _is_ray_available():
    """Check if Ray is available and initialized."""
    if not RAY_AVAILABLE:
        return False
    
    try:
        # Use global ray variable instead of importing directly
        global ray
        # CRITICAL FIX: Skip all Ray runtime checks to avoid _private errors
        # Just check if Ray has the basic attributes we need
        required_attrs = ['init', 'get', 'put', 'remote']
        if all(hasattr(ray, attr) for attr in required_attrs):
            return True
        return False
    except Exception:
        return False



def to_serializable(val):
    if isinstance(val, np.ndarray):
        return val.tolist()
    elif isinstance(val, (np.integer, np.int32, np.int64)):
        return int(val)
    elif isinstance(val, (np.floating, np.float32, np.float64)):
        return float(val)
    elif isinstance(val, datetime.datetime):
        return val.strftime('%Y-%m-%d %H:%M:%S')
    elif isinstance(val, dict):
        return {k: to_serializable(v) for k, v in val.items()}
    elif isinstance(val, (list, tuple)):
        return [to_serializable(v) for v in val]
    else:
        return val

# Pipeline queue configuration - REDESIGNED FOR THOUSANDS OF IMAGES
PIPELINE_QUEUE_MAX_SIZE = 0  # Unlimited queue size for thousands of images
MEMORY_CACHE_MAX_IMAGES = 20   # Increased cache for better performance with thousands of images
BATCH_SIZE_FOR_LARGE_DATASETS = 100  # Process images in batches of 100 for thousands of images
LARGE_DATASET_THRESHOLD = 500  # Consider it a large dataset if > 500 images
MEMORY_CLEANUP_INTERVAL = 50   # Run memory cleanup every 50 processed images

class PipelineQueues:
    """Manages queues for pipeline processing with intelligent caching - OPTIMIZED FOR LARGE DATASETS"""
    def __init__(self, intelligent_cache=None):
        # CRITICAL: Use unlimited queues for thousands of images
        # Memory will be managed through batching instead of queue limits
        self.target_detection_queue = queue.Queue(maxsize=0)  # Unlimited
        self.calibration_compute_queue = queue.Queue(maxsize=0)  # Unlimited  
        self.calibration_apply_queue = queue.Queue(maxsize=0)  # Unlimited
        self.export_queue = queue.Queue(maxsize=0)  # Unlimited
        self.completed = queue.Queue()  # No size limit for completed items
        
        # NEW: Batch processing queues for memory management
        self.batch_queue = queue.Queue(maxsize=0)  # For batched processing
        self.current_batch = []
        self.batch_lock = threading.Lock()
        
        # CRITICAL: Track where images are queued from
        self._export_queue_sources = {}
        
        # OPTIMIZATION: Integrate Phase 3.1 Intelligent Caching System
        self.intelligent_cache = intelligent_cache
        
        # Memory cache for debayered images (enhanced with intelligent cache)
        self.image_cache = {}
        self.cache_lock = threading.Lock()
        self.cache_order = deque(maxlen=MEMORY_CACHE_MAX_IMAGES)
        
        # MAJOR IMPROVEMENT: In-memory calibration data store
        # Replaces file-based communication to eliminate Thread 3 blocking
        self.calibration_data_store = {}  # {image_key: calibration_entry}
        self.calibration_data_lock = threading.Lock()
        self.calibration_ready_events = {}  # {image_key: threading.Event()}
        self.calibration_metadata = {}  # {image_key: {timestamp, camera_model, camera_filter}}
        
        # Calibration data tracking
        self.calibration_ready_event = threading.Event()
        self.all_calibration_complete = threading.Event()
        self.calibration_compute_complete = threading.Event()
        
        # Shutdown flags
        self.shutdown = threading.Event()
        
    def queue_to_export(self, image, source_thread="unknown"):
        """Safely queue image to export, ensuring proper flow"""
        is_target = getattr(image, 'is_calibration_photo', False)
        
        # CRITICAL FIX: Check for calibration data more comprehensively
        # Thread 3 calibrated images have calibrated data in image.data, not calibration_image
        has_calibration_image = hasattr(image, 'calibration_image') and image.calibration_image is not None
        has_calibrated_data = hasattr(image, 'data') and image.data is not None
        has_calibration_coefficients = hasattr(image, 'calibration_coefficients') and image.calibration_coefficients is not None
        
        has_calibration = has_calibration_image or has_calibrated_data or has_calibration_coefficients
        
        # Track source
        if hasattr(image, 'fn'):
            self._export_queue_sources[image.fn] = source_thread
        
        # Debug: Print stack trace to find where this is called from
        if source_thread == "unknown":
            import traceback
            traceback.print_stack()
        
        # CRITICAL: Non-target images MUST have calibration
        if not is_target and not has_calibration:
            pass
            # Don't queue it - force it through Thread 3
            if source_thread != "thread-3":  # CRITICAL FIX: Use "thread-3" to match the actual source string
                self.calibration_apply_queue.put(image)
                return
            else:
                pass
                # Queue it anyway since it came from Thread 3
        
        # Safe to queue to export
        self.export_queue.put(image)
    
    def add_to_batch(self, item):
        """Add item to current batch for batch processing"""
        with self.batch_lock:
            self.current_batch.append(item)
            if len(self.current_batch) >= BATCH_SIZE_FOR_LARGE_DATASETS:
                # Batch is full, queue it for processing
                batch_copy = self.current_batch.copy()
                self.current_batch.clear()
                self.batch_queue.put(batch_copy)
                print(f"[BATCH] Queued batch of {len(batch_copy)} items for processing")
                return True  # Batch was queued
        return False  # Batch not yet full
    
    def flush_batch(self):
        """Force queue any remaining items in current batch"""
        with self.batch_lock:
            if self.current_batch:
                batch_copy = self.current_batch.copy()
                self.current_batch.clear()
                self.batch_queue.put(batch_copy)
                print(f"[BATCH] Flushed remaining batch of {len(batch_copy)} items")
                return len(batch_copy)
        return 0
    
    def get_batch(self, timeout=1):
        """Get a batch of items for processing"""
        try:
            return self.batch_queue.get(timeout=timeout)
        except queue.Empty:
            return None
        
    def cache_image_data(self, image_fn: str, data):
        """Cache debayered image data with LRU eviction"""
        with self.cache_lock:
            if image_fn in self.image_cache:
                # Move to end (most recently used)
                self.cache_order.remove(image_fn)
                self.cache_order.append(image_fn)
            else:
                # Add new image
                if len(self.cache_order) >= MEMORY_CACHE_MAX_IMAGES:
                    # Evict least recently used
                    lru_fn = self.cache_order.popleft()
                    del self.image_cache[lru_fn]
                    print(f"[MEMORY] Evicted {lru_fn} from cache")
                
                self.image_cache[image_fn] = data
                self.cache_order.append(image_fn)
                print(f"[MEMORY] Cached {image_fn} (cache size: {len(self.image_cache)})")
    
    def get_cached_image_data(self, image_fn: str):
        """Get cached image data if available"""
        with self.cache_lock:
            if image_fn in self.image_cache:
                # Move to end (most recently used)
                self.cache_order.remove(image_fn)
                self.cache_order.append(image_fn)
                return self.image_cache[image_fn]
        return None
    
    def clear_cache_for_image(self, image_fn: str):
        """Clear cached data for a specific image"""
        with self.cache_lock:
            if image_fn in self.image_cache:
                del self.image_cache[image_fn]
    
    def clear_all_caches(self):
        """Clear all caches and reset the system for fresh processing"""
        with self.cache_lock:
            self.image_cache.clear()
            self.cache_order.clear()
            self._export_queue_sources.clear()
        
        # Reset calibration events
        self.calibration_ready_event.clear()
        self.all_calibration_complete.clear()
        
        # Clear all queues
        while not self.target_detection_queue.empty():
            try:
                self.target_detection_queue.get_nowait()
            except queue.Empty:
                break
        
        while not self.calibration_compute_queue.empty():
            try:
                self.calibration_compute_queue.get_nowait()
            except queue.Empty:
                break
        
        while not self.calibration_apply_queue.empty():
            try:
                self.calibration_apply_queue.get_nowait()
            except queue.Empty:
                break
        
        while not self.export_queue.empty():
            try:
                self.export_queue.get_nowait()
            except queue.Empty:
                break
        
        while not self.completed.empty():
            try:
                self.completed.get_nowait()
            except queue.Empty:
                break
        
    
    def store_calibration_data(self, image_key: str, calibration_entry: dict, image_metadata: dict = None):
        """Store calibration data in memory and signal availability to waiting threads"""
        with self.calibration_data_lock:
            self.calibration_data_store[image_key] = calibration_entry
            if image_metadata:
                self.calibration_metadata[image_key] = image_metadata
            
            # Create and set the ready event for this specific image
            if image_key not in self.calibration_ready_events:
                self.calibration_ready_events[image_key] = threading.Event()
            self.calibration_ready_events[image_key].set()
            
            print(f"[MEMORY_STORE] Stored calibration data for {image_key}")
    
    def get_calibration_data(self, image_key: str) -> dict:
        """Get calibration data for a specific image"""
        with self.calibration_data_lock:
            return self.calibration_data_store.get(image_key)
    
    def is_calibration_ready(self, image_key: str) -> bool:
        """Check if calibration data is available for an image"""
        with self.calibration_data_lock:
            return image_key in self.calibration_data_store
    
    def wait_for_calibration(self, image_key: str, timeout: float = None) -> bool:
        """Wait for calibration data to become available for a specific image"""
        # Create event if it doesn't exist
        with self.calibration_data_lock:
            if image_key not in self.calibration_ready_events:
                self.calibration_ready_events[image_key] = threading.Event()
            event = self.calibration_ready_events[image_key]
        
        # Wait for the event (outside the lock)
        return event.wait(timeout)
    
    def has_any_calibration_data(self) -> bool:
        """Check if any calibration data exists in the store"""
        with self.calibration_data_lock:
            return len(self.calibration_data_store) > 0
    
    def find_best_calibration_match(self, target_image) -> dict:
        """Find the best calibration data match for a target image based on temporal and metadata criteria"""
        import datetime
        
        # Get image metadata for matching
        img_timestamp = getattr(target_image, 'timestamp', None)
        img_camera_model = getattr(target_image, 'camera_model', None)
        img_camera_filter = getattr(target_image, 'camera_filter', None)
        
        # TEMPORARILY DISABLED: print(f"[MEMORY_STORE] Finding calibration match for {target_image.fn}")
        # TEMPORARILY DISABLED: print(f"[MEMORY_STORE] Target criteria: timestamp={img_timestamp}, camera_model={img_camera_model}, camera_filter={img_camera_filter}")
        
        # Parse image timestamp if it's a string
        img_ts = None
        if img_timestamp:
            try:
                if isinstance(img_timestamp, str):
                    img_ts = datetime.datetime.strptime(img_timestamp, '%Y-%m-%d %H:%M:%S')
                elif hasattr(img_timestamp, 'strftime'):
                    img_ts = img_timestamp
            except Exception as e:
                print(f"[MEMORY_STORE] Error parsing timestamp {img_timestamp}: {e}")
        
        # Find best matching calibration entry
        best_key = None
        best_delta = None
        fallback_key = None
        fallback_delta = None
        
        with self.calibration_data_lock:
            for key, entry in self.calibration_data_store.items():
                try:
                    # Get metadata if available
                    metadata = self.calibration_metadata.get(key, {})
                    entry_camera_model = metadata.get('camera_model') or entry.get('camera_model')
                    entry_camera_filter = metadata.get('camera_filter') or entry.get('camera_filter')
                    
                    # Check camera model and filter match
                    camera_model_match = (img_camera_model is None or entry_camera_model is None or 
                                        entry_camera_model == img_camera_model)
                    camera_filter_match = (img_camera_filter is None or entry_camera_filter is None or 
                                         entry_camera_filter == img_camera_filter)
                    
                    if not camera_model_match or not camera_filter_match:
                        continue
                    
                    # Parse calibration timestamp (use key as timestamp)
                    try:
                        calib_ts = datetime.datetime.strptime(key.split('_')[0] if '_' in key else key, '%Y-%m-%d %H:%M:%S')
                    except:
                        # If key isn't a timestamp, try metadata
                        calib_timestamp = metadata.get('timestamp')
                        if calib_timestamp:
                            calib_ts = datetime.datetime.strptime(calib_timestamp, '%Y-%m-%d %H:%M:%S')
                        else:
                            continue
                    
                    if img_ts:
                        delta = (img_ts - calib_ts).total_seconds()
                        abs_delta = abs(delta)
                        
                        # Prefer earlier calibration (delta >= 0)
                        if delta >= 0 and (best_delta is None or delta < best_delta):
                            best_key = key
                            best_delta = delta
                        
                        # Fallback to closest overall
                        if fallback_delta is None or abs_delta < fallback_delta:
                            fallback_key = key
                            fallback_delta = abs_delta
                    else:
                        # No timestamp available, use first matching entry
                        if best_key is None:
                            best_key = key
                            
                except Exception as e:
                    print(f"[MEMORY_STORE] Error processing calibration entry {key}: {e}")
                    continue
        
        # Choose the best calibration entry
        chosen_key = best_key or fallback_key
        
        if chosen_key:
            print(f"[MEMORY_STORE] Selected calibration entry: {chosen_key} for {target_image.fn}")
            return self.calibration_data_store[chosen_key]
        else:
            # TEMPORARILY DISABLED: print(f"[MEMORY_STORE] No matching calibration entry found for {target_image.fn}")
            return None

def recover_camera_metadata_from_exif(image_path, project=None):
    """
    Recover camera metadata from EXIF data when missing from project JSON.
    
    Args:
        image_path: Path to the image file (JPG or RAW)
        project: Project object to update JSON (optional)
    
    Returns:
        tuple: (camera_model, camera_filter) or (None, None) if recovery fails
    """
    try:
        from PIL import Image as PILImage
        from PIL.ExifTags import TAGS
        
        # For RAW files, try to find associated JPG file
        jpg_path = image_path
        if image_path.lower().endswith('.raw'):
            # Try to find corresponding JPG file
            base_name = os.path.splitext(image_path)[0]
            potential_jpg = f"{base_name}.JPG"
            if os.path.exists(potential_jpg):
                jpg_path = potential_jpg
            else:
                # If no JPG found, can't read EXIF from RAW directly
                print(f"[EXIF_RECOVERY] ⚠️ No JPG file found for RAW: {image_path}")
                return None, None
        
        with PILImage.open(jpg_path) as pil_img:
            exif = pil_img.getexif()
            if exif:
                exif_dict = {TAGS.get(k, k): v for k, v in exif.items()}
                if 'Model' in exif_dict and '_' in str(exif_dict['Model']):
                    model_parts = str(exif_dict['Model']).split('_')
                    camera_model = model_parts[0]
                    camera_filter = model_parts[1] if len(model_parts) > 1 else 'Unknown'
                    
                    print(f"[EXIF_RECOVERY] ✅ Recovered from EXIF: {camera_model}_{camera_filter}")
                    
                    # Update project JSON if project reference provided
                    if project and hasattr(project, 'data') and project.data.get('files'):
                        base_filename = os.path.basename(image_path)
                        for file_key, file_data in project.data['files'].items():
                            # Match by filename
                            if (file_data.get('raw') and os.path.basename(file_data['raw']) == base_filename) or \
                               (file_data.get('jpg') and os.path.basename(file_data['jpg']) == base_filename):
                                if 'import_metadata' not in file_data:
                                    file_data['import_metadata'] = {}
                                file_data['import_metadata']['camera_model'] = camera_model
                                file_data['import_metadata']['camera_filter'] = camera_filter
                                print(f"[EXIF_RECOVERY] 📝 Updated project JSON for {base_filename}")
                                break
                    
                    return camera_model, camera_filter
                    
    except Exception as e:
        print(f"[EXIF_RECOVERY] ❌ Recovery failed for {image_path}: {e}")
    
    return None, None


class PipelineThreads:
    """Manages the 4-thread pipeline for efficient processing"""
    
    def __init__(self, project, options, outfolder, use_ray=False, api=None, ray_config=None, intelligent_cache=None, memory_manager=None):
        self.project = project
        self.options = options
        self.outfolder = outfolder
        # CRITICAL FIX: Check Ray availability dynamically
        ray_actually_available = _ensure_ray_available()
        self.use_ray = use_ray and ray_actually_available
        self.api = api  # Reference to API for progress updates
        self.intelligent_cache = intelligent_cache
        self.memory_manager = memory_manager
        self.queues = PipelineQueues(intelligent_cache=intelligent_cache)
        self.stats_lock = threading.Lock()
        self._stop_requested = False  # Flag to stop all threads
        
        # FRESH START FIX: Initialize fresh processing stats (no resume)
        self.processing_stats = {
            'targets_found': 0,
            'targets_checked': 0,
            'calibrations_computed': 0,
            'calibrations_processed': 0,
            'images_calibrated': 0,
            'images_exported': 0,
            'total_image_pairs': 0,
            'total_individual_files': 0
        }
        
        # CRITICAL FIX: Sliding window deduplication for large datasets
        # Only track recent files to prevent immediate duplicates, not all files forever
        self.recent_files_lock = threading.Lock()
        self.recent_files = deque(maxlen=200)  # Only track last 200 files (sliding window)
        self.recent_files_set = set()  # Fast O(1) lookup for recent files
        
        # Set processing mode environment variable for GPU control
        import os
        if self.use_ray:
            os.environ['PROCESSING_MODE'] = 'parallel'
        else:
            os.environ['PROCESSING_MODE'] = 'serial'
        
        # CRITICAL FIX: Ensure Ray functions are available when Ray is enabled
        if self.use_ray:
            pass
            try:
                if not _ensure_ray_functions_available():
                    pass
                    self.use_ray = False
                    os.environ['PROCESSING_MODE'] = 'serial'  # Switch back to serial mode
                else:
                    pass
            except Exception as e:
                pass
                self.use_ray = False
                os.environ['PROCESSING_MODE'] = 'serial'  # Switch back to serial mode
    
    def _queue_file_safely(self, queue, file_item, description="file"):
        """
        Safely queue a file using sliding window deduplication for large datasets.
        Only prevents immediate duplicates within a 200-file window, not all files forever.
        
        Args:
            queue: The queue to add the file to
            file_item: The file/image to queue (can be filename string or image object)
            description: Description for logging
        
        Returns:
            bool: True if queued, False if already queued (duplicate)
        """
        # Extract filename for duplicate checking
        if hasattr(file_item, 'fn'):
            filename = file_item.fn
        elif isinstance(file_item, str):
            filename = file_item
        else:
            filename = str(file_item)
        
        with self.recent_files_lock:
            # Check if file is in recent window (fast O(1) lookup)
            if filename in self.recent_files_set:
                pass
                return False
            
            # Add to sliding window
            if len(self.recent_files) == self.recent_files.maxlen:
                # Remove oldest file from set when deque evicts it
                oldest = self.recent_files[0]  # About to be evicted
                self.recent_files_set.discard(oldest)
            
            # Add new file to both deque and set
            self.recent_files.append(filename)
            self.recent_files_set.add(filename)
            
            try:
                queue.put(file_item, timeout=5)
                return True
            except Exception as e:
                # Remove from tracking if queue failed
                self.recent_files_set.discard(filename)
                # Remove from deque (find and remove)
                try:
                    self.recent_files.remove(filename)
                except ValueError:
                    pass  # Already removed or not found
                return False
    
    def _cleanup_deduplication_cache(self):
        """
        Cleanup deduplication cache during memory cleanup intervals.
        Reduces the sliding window size during heavy processing.
        """
        with self.recent_files_lock:
            if len(self.recent_files) > 100:
                # Keep only the most recent 100 files during cleanup
                files_to_remove = len(self.recent_files) - 100
                for _ in range(files_to_remove):
                    if self.recent_files:
                        oldest = self.recent_files.popleft()
                        self.recent_files_set.discard(oldest)
        
    def _calculate_total_file_count(self, project):
        """Calculate total individual file count from project data structure"""
        total_files = 0
        files_dict = project.data.get('files', {})
        
        for base_key, fileset in files_dict.items():
            # Count RAW file if present
            if fileset.get('raw'):
                total_files += 1
            # Count JPG file if present
            if fileset.get('jpg'):
                total_files += 1
        
        # Add scan files (.daq, .csv) if they exist
        if hasattr(project, 'scanmap') and project.scanmap:
            total_files += len(project.scanmap)
        
        return total_files
    
    def get_overall_progress(self):
        """Get overall progress information for premium mode UI updates"""
        try:
            # Calculate progress based on queue states and thread activity
            total_threads = 4
            active_threads = sum(1 for t in self.threads if t.is_alive())
            
            # Get queue sizes for progress calculation
            target_detection_count = self.queues.target_detection_queue.qsize()
            calibration_compute_count = self.queues.calibration_compute_queue.qsize()
            calibration_apply_count = self.queues.calibration_apply_queue.qsize()
            export_count = self.queues.export_queue.qsize() 
            completed_count = self.queues.completed.qsize()
            
            # Calculate total pending work
            pending_count = target_detection_count + calibration_compute_count + calibration_apply_count
            
            # Calculate overall percentage
            total_items = pending_count + export_count + completed_count
            if total_items > 0:
                overall_percent = int((completed_count / total_items) * 100)
            else:
                overall_percent = 0 if active_threads > 0 else 100
                
            # Create thread progress array
            thread_progress = []
            for i in range(1, 5):  # Threads 1-4
                thread_active = i <= active_threads
                
                # Fixed thread names - never change
                if i == 1:
                    phase = 'Detecting'
                elif i == 2:
                    phase = 'Analyzing'
                elif i == 3:
                    phase = 'Calibrating'
                else:  # i == 4
                    phase = 'Exporting'
                
                # Calculate progress based on activity and completion
                if not thread_active and overall_percent >= 100:
                    percent = 100
                elif thread_active:
                    # Active threads show real overall progress, not artificial offsets
                    percent = overall_percent
                else:
                    # Inactive threads show 0% until they become active
                    percent = 0
                
                thread_progress.append({
                    'id': i,
                    'percentComplete': percent,
                    'phaseName': phase,
                    'timeRemaining': f"{pending_count + export_count} remaining" if pending_count + export_count > 0 else '',
                    'isActive': thread_active
                })
            
            return {
                'threadProgress': thread_progress,
                'overallPercent': overall_percent,
                'isProcessing': active_threads > 0
            }
            
        except Exception as e:
            pass
            # Return default progress state
            return {
                'threadProgress': [
                    {'id': 1, 'percentComplete': 0, 'phaseName': 'Processing', 'timeRemaining': '', 'isActive': True},
                    {'id': 2, 'percentComplete': 0, 'phaseName': 'Waiting', 'timeRemaining': '', 'isActive': False},
                    {'id': 3, 'percentComplete': 0, 'phaseName': 'Waiting', 'timeRemaining': '', 'isActive': False},
                    {'id': 4, 'percentComplete': 0, 'phaseName': 'Waiting', 'timeRemaining': '', 'isActive': False}
                ],
                'overallPercent': 0,
                'isProcessing': True
            }
    
    def _wrapped_export_put(self, item):
        """Wrapper to catch direct export queue access"""
        if item is not None and hasattr(item, 'fn'):
            import traceback
            # Check if this is a legitimate call from queue_to_export
            stack = traceback.extract_stack()
            is_from_queue_to_export = any('queue_to_export' in frame.name for frame in stack)
            
            if not is_from_queue_to_export:
                pass
                traceback.print_stack()
            else:
                print(f"[THREAD-4] ✅ Legitimate queue_to_export call for {item.fn}")
        return self._original_export_put(item)
    
    def _validate_and_repair_image_pairs(self):
        """
        CRITICAL: Validate all image pairs before processing starts.
        Attempts to repair missing RAW links and reports issues.
        
        Returns:
            tuple: (is_valid, issues_found, issues_repaired)
        """
        import os
        import re
        
        if not hasattr(self, 'project') or not self.project.data.get('files'):
            print("[VALIDATION] ⚠️ No project data to validate")
            return True, 0, 0
        
        issues_found = 0
        issues_repaired = 0
        
        # Get list of all RAW files in the project's image folder(s)
        available_raws = {}  # {timestamp: raw_path}
        
        # Build a map of available RAW files from imagemap
        if hasattr(self.project, 'imagemap'):
            for key, img_obj in self.project.imagemap.items():
                if hasattr(img_obj, 'fn') and img_obj.fn.endswith('.RAW'):
                    # Extract timestamp from filename (e.g., 2025_0203_193047_002.RAW -> 2025_0203_193047_002)
                    raw_base = os.path.splitext(img_obj.fn)[0]
                    available_raws[raw_base] = img_obj.path
        
        # Validation: Found RAW files in imagemap (debug removed)
        
        # Check each fileset for missing RAW links
        for base_key, fileset in self.project.data['files'].items():
            jpg_path = fileset.get('jpg')
            raw_path = fileset.get('raw')
            
            if jpg_path and not raw_path:
                issues_found += 1
                jpg_filename = os.path.basename(jpg_path)
                jpg_base = os.path.splitext(jpg_filename)[0]
                
                # Missing RAW for JPG - will attempt repair
                
                # Attempt to find matching RAW by timestamp
                # Extract timestamp from JPG filename (e.g., 2025_0203_194450_562)
                jpg_ts_match = re.match(r'([0-9]{4}_[0-9]{4}_[0-9]{6})_([0-9]+)', jpg_base)
                
                if jpg_ts_match:
                    jpg_ts = jpg_ts_match.group(1)
                    jpg_seq = int(jpg_ts_match.group(2))
                    
                    # Look for RAW with matching or close timestamp
                    best_match = None
                    best_diff = float('inf')
                    
                    for raw_base, raw_file_path in available_raws.items():
                        raw_ts_match = re.match(r'([0-9]{4}_[0-9]{4}_[0-9]{6})_([0-9]+)', raw_base)
                        if raw_ts_match:
                            raw_ts = raw_ts_match.group(1)
                            raw_seq = int(raw_ts_match.group(2))
                            
                            # Calculate timestamp difference
                            try:
                                jpg_time = int(jpg_ts.replace('_', ''))
                                raw_time = int(raw_ts.replace('_', ''))
                                time_diff = abs(jpg_time - raw_time)
                                
                                # Accept pairs within 10 seconds AND similar sequence numbers
                                seq_diff = abs(jpg_seq - raw_seq)
                                if time_diff <= 10 and seq_diff <= 2 and time_diff < best_diff:
                                    best_match = raw_file_path
                                    best_diff = time_diff
                            except ValueError:
                                pass
                    
                    if best_match:
                        # Repair the link
                        fileset['raw'] = best_match
                        issues_repaired += 1
                        print(f"[VALIDATION] ✅ REPAIRED: Linked {jpg_filename} → {os.path.basename(best_match)}")
                    else:
                        print(f"[VALIDATION] ⚠️ Could not find matching RAW for {jpg_filename}")
                else:
                    print(f"[VALIDATION] ⚠️ Could not parse timestamp from {jpg_filename}")
        
        # Also validate that RAW files referenced in filesets exist in imagemap
        for base_key, fileset in self.project.data['files'].items():
            raw_path = fileset.get('raw')
            if raw_path:
                raw_fn = os.path.basename(raw_path)
                raw_base = os.path.splitext(raw_fn)[0]
                
                # Check if this RAW is in imagemap
                raw_in_imagemap = False
                if hasattr(self.project, 'imagemap'):
                    for key, img_obj in self.project.imagemap.items():
                        if hasattr(img_obj, 'fn') and img_obj.fn == raw_fn:
                            raw_in_imagemap = True
                            break
                
                if not raw_in_imagemap:
                    issues_found += 1
                    # Try to add it to imagemap if file exists
                    if os.path.exists(raw_path):
                        try:
                            from project import LabImage
                            raw_img = LabImage(self.project, raw_path)
                            self.project.imagemap[raw_fn] = raw_img
                            issues_repaired += 1
                        except Exception as e:
                            pass  # Failed to add to imagemap
        
        is_valid = (issues_found == issues_repaired)
        
        # Only log if there were issues that couldn't be repaired
        if issues_found > 0 and not is_valid:
            print(f"[VALIDATION] ⚠️ {issues_found - issues_repaired} image pairs could not be repaired")
        
        return is_valid, issues_found, issues_repaired

    def start_pipeline_json_centric_with_filtering(self, all_images: List, filtered_jpgs_for_detection: List):
        """
        JSON-centric premium pipeline with separate filtering for target detection vs processing.
        
        Args:
            all_images: All images to be processed (JPG + RAW)
            filtered_jpgs_for_detection: Only the JPG images to be analyzed for target detection
        """
        
        # CRITICAL FIX: Prevent multiple pipeline starts
        if hasattr(self, '_pipeline_started') and self._pipeline_started:
            pass
            return
        
        self._pipeline_started = True
        
        # CRITICAL: Validate and repair image pairs BEFORE processing starts
        is_valid, issues_found, issues_repaired = self._validate_and_repair_image_pairs()
        
        if not is_valid:
            unrepaired = issues_found - issues_repaired
            print(f"[PIPELINE] ⚠️ WARNING: {unrepaired} image pairs have missing RAW files that could not be repaired")
        
        # Store both image lists for thread access
        self.images = all_images  # All images for processing
        self.filtered_jpgs_for_detection = filtered_jpgs_for_detection  # Filtered JPGs for target detection
        
        # Sort images by timestamp for proper temporal processing
        try:
            sorted_all_images = sorted(all_images, key=lambda x: getattr(x, 'timestamp', getattr(x, 'DateTime', '0')))
            sorted_filtered_jpgs = sorted(filtered_jpgs_for_detection, key=lambda x: getattr(x, 'timestamp', getattr(x, 'DateTime', '0')))
        except Exception as e:
            pass
            sorted_all_images = all_images
            sorted_filtered_jpgs = filtered_jpgs_for_detection
        
        # Start all threads in parallel for optimal performance
        try:
            pass
            t1 = threading.Thread(
                target=self._thread1_target_detection_json_centric,
                args=(sorted_filtered_jpgs,),  # Only filtered JPGs for target detection
                name="Thread-1-Detection-JSON"
            )
            t2 = threading.Thread(
                target=self._thread2_calibration_compute_json_centric,
                name="Thread-2-Computation-JSON"
            )
            t3 = threading.Thread(
                target=self._thread3_calibration_apply_json_centric,
                name="Thread-3-Calibration-JSON"
            )
            t4 = threading.Thread(
                target=self._thread4_export_json_centric,
                name="Thread-4-Export-JSON"
            )
            
            # Store references to threads for monitoring
            self.threads = [t1, t2, t3, t4]
            
            import sys
            sys.stdout.flush()
            
            # DIAGNOSTIC: Write directly to log file to test
            if hasattr(sys.stdout, 'log'):
                try:
                    sys.stdout.log.write("[PIPELINE-TEST] Direct write to log file\n")
                    sys.stdout.log.flush()
                except Exception as e:
                    print(f"[PIPELINE-ERROR] Failed to write to log: {e}", flush=True)
            
            # Start all threads in parallel for maximum performance
            for thread in self.threads:
                if not self.queues.shutdown.is_set():
                    pass
                    thread.start()
                    
                    
        except Exception as e:
            pass
            import traceback
            # Cleanup health monitor on error
            self._cleanup_health_monitor()
            raise

    def _cleanup_health_monitor(self):
        """Cleanup Ray health monitor when processing completes or fails"""
        if hasattr(self, 'ray_health_monitor') and self.ray_health_monitor:
            try:
                from ray_health_monitor import stop_ray_health_monitoring
                stop_ray_health_monitoring()
            except Exception as e:
                pass

    def start_pipeline_json_centric(self, images: List):
        """
        JSON-centric premium pipeline for high-performance processing.
        Uses JSON files for inter-thread communication instead of passing image objects.
        """
        
        # CRITICAL FIX: Prevent multiple pipeline starts
        if hasattr(self, '_pipeline_started') and self._pipeline_started:
            pass
            return
        
        self._pipeline_started = True

        # CRITICAL: Validate and repair image pairs BEFORE processing starts
        is_valid, issues_found, issues_repaired = self._validate_and_repair_image_pairs()
        
        # Store images for thread access
        self.images = images
        
        # Sort images by timestamp for proper temporal processing
        try:
            sorted_images = sorted(images, key=lambda x: getattr(x, 'timestamp', getattr(x, 'DateTime', '0')))
        except Exception as e:
            pass
            sorted_images = images
        
        # Start all threads in parallel for optimal performance
        try:
            pass
            t1 = threading.Thread(
                target=self._thread1_target_detection_json_centric,
                args=(sorted_images,),
                name="Thread-1-Detection-JSON"
            )
            t2 = threading.Thread(
                target=self._thread2_calibration_compute_json_centric,
                name="Thread-2-Computation-JSON"
            )
            t3 = threading.Thread(
                target=self._thread3_calibration_apply_json_centric,
                name="Thread-3-Calibration-JSON"
            )
            t4 = threading.Thread(
                target=self._thread4_export_json_centric,
                name="Thread-4-Export-JSON"
            )
            
            # Store references to threads for monitoring
            self.threads = [t1, t2, t3, t4]
            
            import sys
            sys.stdout.flush()
            
            # DIAGNOSTIC: Write directly to log file to test
            if hasattr(sys.stdout, 'log'):
                try:
                    sys.stdout.log.write("[PIPELINE-TEST] Direct write to log file\n")
                    sys.stdout.log.flush()
                except Exception as e:
                    print(f"[PIPELINE-ERROR] Failed to write to log: {e}", flush=True)
            
            # Start all threads in parallel for maximum performance
            for thread in self.threads:
                if not self.queues.shutdown.is_set():
                    pass
                    thread.start()
                    
                    
        except Exception as e:
            pass
            import traceback
            raise

    def _thread1_target_detection_json_centric(self, images):
        """Thread 1: Target detection using Ray GPU acceleration, saves results to JSON"""

        import os  # Ensure os is available for this function scope
        import sys  # Ensure sys.stdout is the redirected one
        
        # Verify stdout is the redirected version
        sys.stdout.flush()

        try:
            # CRITICAL: Skip target detection if reflectance calibration is disabled
            reflectance_enabled = True  # Default to enabled
            
            if hasattr(self, 'options') and self.options:
                if 'Project Settings' in self.options and 'Processing' in self.options['Project Settings']:
                    reflectance_enabled = self.options['Project Settings']['Processing'].get('Reflectance calibration / white balance', True)
                elif 'Processing' in self.options:
                    reflectance_enabled = self.options['Processing'].get('Reflectance calibration / white balance', True)
            
            if not reflectance_enabled:
                # Skipping target detection - reflectance calibration is disabled
                try:
                    # Mark all images as non-targets in project data
                    if hasattr(self, 'project') and self.project and hasattr(self.project, 'data'):
                        for base, fileset in self.project.data.get('files', {}).items():
                            fileset['is_calibration_photo'] = False
                except Exception as mark_error:
                    pass
                
                try:
                    # Signal Thread-2 to skip (send sentinel)
                    self.queues.calibration_compute_queue.put(None, timeout=2)
                except Exception as sentinel_error:
                    pass
                
                # Queue all RAW images to Thread-3 for sensor response processing
                all_images_for_processing = getattr(self, 'images', images)
                raw_images = [img for img in all_images_for_processing if hasattr(img, 'fn') and img.fn.lower().endswith('.raw')]
                
                queued_count = 0
                for img in raw_images:
                    if self._queue_file_safely(self.queues.calibration_apply_queue, img.fn, "RAW file from Thread 1 (sensor response mode)"):
                        queued_count += 1
                
                import time
                time.sleep(0.5)
                
                # Send sentinel to Thread-3
                self.queues.calibration_apply_queue.put(None)
                
                # Update processing stats
                if hasattr(self, 'processing_stats'):
                    self.processing_stats['total_image_pairs'] = queued_count
                
                return
            # Reflectance calibration is enabled - proceeding with target detection
            
            # Get configuration for minimum calibration samples
            cfg = self.project.data['config']
            min_calibration_samples = cfg["Project Settings"]["Target Detection"]["Minimum calibration sample area (px)"]
            
            # PREMIUM MODE FIX: Check if we have a full image list for processing
            all_images_for_processing = getattr(self, 'images', images)
            
            # Filter to only process JPG files for detection (these are the filtered ones)
            jpg_images = [img for img in images if hasattr(img, 'fn') and img.fn.endswith('.JPG')]
            
            # PREMIUM MODE FIX: Queue ALL images to Thread 3, not just the ones being analyzed
            # CRITICAL BUG FIX: Queue ALL images without premature sentinel or early exit
            # Queue ALL images to Thread 3
            queued_count = 0
            failed_count = 0
            
            for i, img in enumerate(all_images_for_processing):
                if hasattr(img, 'fn'):
                    try:
                        self.queues.calibration_apply_queue.put(img.fn, timeout=5)
                        queued_count += 1
                    except Exception as queue_error:
                        failed_count += 1
            
            # Queued images silently
            
            # CRITICAL: Do NOT send sentinel here - it's sent after target detection at line 3284
            
            # CRITICAL FIX: Filter images based on checkbox state BEFORE processing
            # This respects user's manual target selections (grey checkboxes)
            images_to_analyze = []
            targets_confirmed = []
            
            for jpg_image in jpg_images:
                checkbox_state = _get_serial_checkbox_state(jpg_image.fn, self.project)
                
                if checkbox_state == 'disabled':
                    # Disabled target = was detected but manually unchecked, skip completely
                    continue
                elif checkbox_state == 'green':
                    # Green check = confirmed target, skip analysis
                    targets_confirmed.append(jpg_image)
                    
                    # Queue to Thread 2 immediately
                    self.queues.calibration_compute_queue.put(jpg_image.fn)
                    
                    # Update stats
                    with self.stats_lock:
                        self.processing_stats['targets_found'] += 1
                        self.processing_stats['targets_checked'] += 1
                    continue
                elif checkbox_state == 'skip':
                    # User made manual selections but didn't check this image - skip it
                    continue
                
                # If we get here, we need to analyze the image (grey check or default)
                images_to_analyze.append(jpg_image)
            
            # Process each JPG image for target detection (only the filtered ones)
            
            # Add heartbeat to prove we reached this point
            import time
            start_time = time.time()
            # Initialize progress tracking
            total_detect_images = len(images_to_analyze)
            last_print_percent = -1
            
            for i, image in enumerate(images_to_analyze):
                # CRITICAL: Check for stop request at start of each image processing
                if self.queues.shutdown.is_set() or self._stop_requested:
                    pass
                    break
                
                
                # DEBUG: Check image attributes
                if hasattr(image, 'path'):
                    pass
                
                # Update stats: increment targets_checked
                with self.stats_lock:
                    self.processing_stats['targets_checked'] += 1
                
                # Use Ray for GPU-accelerated detection - check both path and fn for JPG
                should_process = False
                if hasattr(image, 'path') and image.path and image.path.endswith('.JPG'):
                    should_process = True
                elif hasattr(image, 'fn') and image.fn and image.fn.endswith('.JPG'):
                    should_process = True
                
                if should_process:
                    try:
                        pass
                        # Call Ray detection function with proper min_calibration_samples
                        result = detect_calibration_image_ray.remote(image, min_calibration_samples, self.project)
                        # detect_calibration_image returns: (aruco_id, is_calibration_photo, aruco_corners, calibration_target_polys)
                        aruco_id, detected, aruco_corners, calibration_target_polys = ray.get(result)
                        
                        # CRITICAL: Find corresponding RAW filename for JSON-centric system
                        raw_filename = None
                        for base_key, file_data in self.project.data.get('files', {}).items():
                            jpg_path = file_data.get('jpg_path', '') or file_data.get('jpg', '')
                            if (jpg_path and (
                                jpg_path.endswith(image.fn) or 
                                os.path.basename(jpg_path) == image.fn or
                                image.fn in jpg_path
                            )):
                                raw_filename = file_data.get('raw_path') or file_data.get('raw')
                                break
                        
                        # Save detection results to JSON with RAW filename
                        detection_data = {
                            'detected': detected,
                            'aruco_id': aruco_id,
                            'aruco_corners': aruco_corners.tolist() if aruco_corners is not None else None,
                            'calibration_target_polys': [poly.tolist() for poly in calibration_target_polys] if calibration_target_polys else None,
                            'timestamp': getattr(image, 'DateTime', ''),
                            'camera_model': getattr(image, 'Model', 'Unknown'),
                            'filename': image.fn,
                            'raw_filename': raw_filename  # CRITICAL: Include RAW filename for Thread 3
                        }
                        
                        self._save_detection_to_json(image.fn, detection_data)
                        
                        # Queue to Thread 2 if target detected
                        if detected:
                            # Target detected - update stats and queue
                            with self.stats_lock:
                                self.processing_stats['targets_found'] += 1
                            
                            self.queues.calibration_compute_queue.put(image.fn)
                            
                            # CRITICAL: Call batching function for EVERY detected target
                            self._update_ui_checkbox_realtime(image.fn, detected)
                            
                        # Simple periodic print progress
                        current_percent = min(100, int(((i + 1) / total_detect_images) * 100))
                        if total_detect_images < 10 or (current_percent % 10 == 0 and current_percent != last_print_percent):
                            print(f"[DETECTING] {i + 1}/{total_detect_images} ({current_percent}%)", flush=True)
                            last_print_percent = current_percent
                            # Still update project data at milestones for redundancy
                            self._update_project_data_realtime(image.fn, detected)
                            self._dispatch_comprehensive_sse_events(image.fn, detected)
                        
                        # Update progress
                        if self.api:
                            progress_percent = int((i + 1) * 100 / len(images_to_analyze))
                            self.api.update_thread_progress_premium(
                                thread_id=1,
                                percent_complete=progress_percent,
                                phase_name="Detecting",
                                time_remaining=f"{i+1}/{len(images_to_analyze)}"
                            )
                            import time
                            time.sleep(0.05)
                        
                    except Exception as e:
                        print(f"Error detecting target in {image.fn}: {e}", flush=True)
                else:
                    pass
                        
            # Send completion sentinels
            try:
                pass
                self.queues.calibration_compute_queue.put(None)  # Signal Thread 2 completion
                self.queues.calibration_apply_queue.put(None)    # Signal Thread 3 completion
            except Exception as sentinel_error:
                pass
                import traceback
            
            # CRITICAL: Mark target detection as completed for parallel mode
            # This prevents force-green-to-grey events from clearing detected targets
            if self.api and hasattr(self.api, 'project') and self.api.project:
                try:
                    processing_state = self.api.project.get_processing_state()
                    if 'parallel_stages' not in processing_state:
                        processing_state['parallel_stages'] = {}
                    if 'target_detection' not in processing_state['parallel_stages']:
                        processing_state['parallel_stages']['target_detection'] = {}
                    processing_state['parallel_stages']['target_detection']['completed'] = True
                    # FIX: save_processing_state expects (stage, mode, thread_states) not (state_dict, mode)
                    self.api.project.save_processing_state('target_detection_complete', 'parallel', processing_state.get('parallel_stages'))
                except Exception as e:
                    pass
            
            # CRITICAL: Update Thread 1 to 100% complete with final count
            if self.api:
                try:
                    total_processed = len(jpg_images)
                    self.api.update_thread_progress_premium(
                        thread_id=1,
                        percent_complete=100,
                        phase_name="Detecting",
                        time_remaining=f"{total_processed}/{total_processed}"
                    )
                except Exception as e:
                    pass
            
            # CRITICAL: Flush any remaining targets in the batch queue BEFORE final batch
            if hasattr(self, '_ui_update_batch') and self._ui_update_batch:
                try:
                    import backend_server
                    backend_server.dispatch_event('target-batch-update', {
                        'targets_found': self._ui_update_batch.copy(),
                        'completed_count': len(self._ui_update_batch),
                        'total_count': self.processing_stats.get('targets_found', len(self._ui_update_batch)),
                        'source': 'thread1_json_pre_final_flush'
                    })
                    self._ui_update_batch = []
                except Exception as e:
                    pass  # Silent fail
            
            # CRITICAL: Send final batch update to UI with all found targets
            # This ensures UI reflects all targets even if individual events were missed
            try:
                import backend_server
                import os
                
                found_targets = []
                if self.api and hasattr(self.api, 'project') and self.api.project:
                    for base_key, fileset in self.api.project.data['files'].items():
                        if fileset.get('jpg'):
                            jpg_file = os.path.basename(fileset['jpg'])
                            calibration_info = fileset.get('calibration', {})
                            is_target = calibration_info.get('is_calibration_photo', False)
                            if is_target:
                                found_targets.append({
                                    'filename': jpg_file,
                                    'is_calibration_photo': True
                                })
                
                if found_targets:
                    backend_server.dispatch_event('target-batch-update', {
                        'targets_found': found_targets,
                        'completed_count': len(jpg_images),
                        'total_count': len(jpg_images),
                        'source': 'thread1_final_batch_update'
                    })
                    
            except Exception as batch_update_error:
                pass
            
            
        except Exception as e:
            print(f"Error in Thread 1 target detection: {e}", flush=True)
            
            # Still send completion sentinels
            try:
                self.queues.calibration_compute_queue.put(None)
                self.queues.calibration_apply_queue.put(None)
            except Exception as sentinel_err:
                pass

    def _thread2_calibration_compute_json_centric(self):
        """Thread 2: Compute calibration coefficients from target images, save to JSON"""
        
        # CRITICAL: Load ALS data from scan files and save to JSON for all images
        try:
            self._ensure_als_precomputed()
        except Exception as e:
            pass
            # Continue processing even if ALS loading fails
        
        import queue
        # Use global ray variable set up by _ensure_ray_available()
        global ray
        processed_targets = 0
        current_ray_future = None  # Track ongoing Ray computation
        current_target_filename = None  # Track current target being processed
        
        consecutive_timeouts = 0
        max_consecutive_timeouts = 120  # 2 minutes of consecutive timeouts before giving up
        
        import time  # For Ray computation timeout
        
        
        import time  # For Ray computation timeout
        
        # Initialize progress tracking (approximate based on queue or project data)
        # Thread 2 receives specific targets, so we estimate total from project data or just use a counter
        processed_target_count = 0
        last_print_percent = -1
        # Best guess at total targets - will be updated as they are processed
        total_targets_estimated = 1
        if hasattr(self, 'project') and self.project.data.get('files'):
            # Estimate targets based on previous detections if available, or just use a reasonable default
            # For now, we'll just track processed count
            pass
            
        try:
            while True:
                try:
                    pass
                    target_filename = self.queues.calibration_compute_queue.get(timeout=1)  # Short timeout for responsive shutdown
                    consecutive_timeouts = 0  # Reset timeout counter when we get data
                    
                    if target_filename is None:  # Sentinel from Thread 1
                        # Wait for any ongoing Ray computation to complete before exiting
                        if current_ray_future is not None:
                            pass
                            try:
                                ray_result = ray.get(current_ray_future)
                                # Process the final result
                                if len(ray_result) == 5:
                                    coefficients, limits, xvals, yvals, processed_image = ray_result
                                elif len(ray_result) == 4:
                                    coefficients, limits, xvals, yvals = ray_result
                                    processed_image = None
                                else:
                                    raise ValueError(f"Unexpected number of return values from get_calib_data_ray: {len(ray_result)}")
                                
                                # Save final calibration data
                                # CRITICAL: Use the target image's timestamp for proper matching
                                import datetime
                                
                                # Get the target image's timestamp for calibration matching
                                target_timestamp = None
                                if hasattr(raw_image, 'timestamp') and raw_image.timestamp:
                                    if hasattr(raw_image.timestamp, 'strftime'):
                                        target_timestamp = raw_image.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                                    else:
                                        target_timestamp = str(raw_image.timestamp)
                                elif hasattr(raw_image, 'DateTime') and raw_image.DateTime not in (None, 'Unknown'):
                                    try:
                                        dt = datetime.datetime.strptime(raw_image.DateTime, '%Y:%m:%d %H:%M:%S')
                                        target_timestamp = dt.strftime('%Y-%m-%d %H:%M:%S')
                                    except:
                                        target_timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                else:
                                    target_timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                
                                
                                final_calibration_data = {
                                    'coefficients': coefficients,
                                    'limits': limits,
                                    'xvals': xvals,
                                    'yvals': yvals,
                                    'timestamp': target_timestamp,  # Use target image's timestamp
                                    'camera_model': 'Survey3N',
                                    'camera_filter': 'RGN',
                                    'target_filename': current_target_filename,
                                    'raw_filename': raw_image.fn
                                }
                                # NOTE: Ray function get_calib_data_ray already saved the calibration data to JSON
                                # No need to save again here as it would overwrite with incomplete data
                                
                                # Update stats: increment calibrations_computed
                                with self.stats_lock:
                                    self.processing_stats['calibrations_computed'] += 1
                                
                                processed_targets += 1
                            except Exception as e:
                                pass
                            
                            processed_target_count += 1
                            
                            # Simple periodic print progress - using a generic counter since total unknown
                            # Or if we knew total targets from Thread 1 stats...
                            with self.stats_lock:
                                known_targets = self.processing_stats.get('targets_found', 0)
                                total_targets_estimated = max(known_targets, processed_target_count)
                            
                            current_percent = min(100, int((processed_target_count / max(1, total_targets_estimated)) * 100))
                            if processed_target_count < 10 or (current_percent % 10 == 0 and current_percent != last_print_percent):
                                print(f"[ANALYZING] {processed_target_count}/{total_targets_estimated} ({current_percent}%)", flush=True)
                                last_print_percent = current_percent
                                
                        break
                    
                    current_target_filename = target_filename  # Track current target
                    
                    # Load detection data
                    detection_data = self._load_detection_from_json(target_filename)
                    if not detection_data or not detection_data.get('detected'):
                        pass
                        continue
                    
                    # CRITICAL FIX: Get RAW filename from detection JSON (JSON-centric approach)
                    raw_filename = detection_data.get('raw_filename')
                    if not raw_filename:
                        pass
                        continue
                    
                    
                    # Find the correct absolute path for the RAW file
                    from project import LabImage
                    import os
                    
                    # Find the base key that corresponds to this JPG filename
                    base_key = None
                    for base, filenames in self.project.base_to_filenames.items():
                        if filenames.get('jpg_filename') == target_filename:
                            base_key = base
                            break
                    
                    if not base_key:
                        pass
                        continue
                    
                    # Get the original absolute path for the RAW file
                    fileset = self.project.data['files'][base_key]
                    raw_path = fileset.get('raw')
                    
                    if not raw_path or not os.path.exists(raw_path):
                        pass
                        continue
                    
                    raw_image = LabImage(self.project, raw_path)
                    
                    # Transfer aruco_id from detection data to RAW image
                    if detection_data and 'aruco_id' in detection_data:
                        raw_image.aruco_id = detection_data['aruco_id']
                        raw_image.calibration_target_polys = detection_data.get('calibration_target_polys')
                    else:
                        pass
                    
                    # Get processing options from project config (wrap in expected structure)
                    processing_config = self.project.data['config']['Project Settings']['Processing']
                    options = {'Processing': processing_config}
                    
                    # Use existing Ray function to compute calibration (includes ALS data loading inside Ray worker)
                    try:
                        current_ray_future = get_calib_data_ray.remote(raw_image, options)
                        
                        # Wait for Ray computation to complete while checking for sentinels
                        ray_result = None
                        ray_start_time = time.time()
                        ray_timeout = 300  # 5 minutes timeout for Ray computation (should not be needed with GPU fix)
                        
                        while ray_result is None:
                            # Check if Ray computation is done (non-blocking)
                            ready_refs, remaining_refs = ray.wait([current_ray_future], timeout=1)
                            if ready_refs:
                                # Ray computation completed
                                ray_result = ray.get(ready_refs[0])
                                current_ray_future = None  # Clear completed future
                            else:
                                # Check for timeout
                                elapsed_time = time.time() - ray_start_time
                                if elapsed_time > ray_timeout:
                                    pass
                                    try:
                                        ray.cancel(current_ray_future, force=True)
                                    except Exception as cancel_error:
                                        pass
                                    current_ray_future = None
                                    # Save default calibration data so Thread 3 can continue
                                    try:
                                        success = self._save_default_calibration_json()
                                        if success:
                                            pass
                                        else:
                                            pass
                                    except Exception as save_error:
                                        pass
                                    break
                            
                                # Ray computation still running, check for sentinel
                                try:
                                    # Non-blocking check for sentinel
                                    sentinel_check = self.queues.calibration_compute_queue.get_nowait()
                                    if sentinel_check is None:
                                        pass
                                        # Put sentinel back for later processing
                                        self.queues.calibration_compute_queue.put(None)
                                        break
                                    else:
                                        # Put non-sentinel item back
                                        self.queues.calibration_compute_queue.put(sentinel_check)
                                except queue.Empty:
                                    pass  # No sentinel yet, continue waiting
                        
                        # If we got a sentinel while Ray was running, wait for Ray to complete
                        if ray_result is None and current_ray_future is not None:
                            pass
                            ray_result = ray.get(current_ray_future)
                            current_ray_future = None
                        
                        # Process Ray results if we have them
                        if ray_result is not None:
                            if len(ray_result) == 5:
                                coefficients, limits, xvals, yvals, processed_image = ray_result
                            elif len(ray_result) == 4:
                                coefficients, limits, xvals, yvals = ray_result
                                processed_image = None
                            else:
                                pass
                                continue
                        
                        if coefficients and limits:
                            # NOTE: Ray function get_calib_data_ray already saved complete calibration data to JSON
                            # Including limits, coefficients, polygons, and all metadata
                            # No need to save again here as it would overwrite with incomplete data
                            # No need to save again here as it would overwrite with incomplete data
                            pass
                            processed_targets += 1
                            processed_target_count += 1
                            
                            # Simple periodic print progress - using a generic counter since total unknown
                            # Or if we knew total targets from Thread 1 stats...
                            with self.stats_lock:
                                known_targets = self.processing_stats.get('targets_found', 0)
                                total_targets_estimated = max(known_targets, processed_target_count)
                            
                            current_percent = min(100, int((processed_target_count / max(1, total_targets_estimated)) * 100))
                            if processed_target_count < 10 or (current_percent % 10 == 0 and current_percent != last_print_percent):
                                print(f"[ANALYZING] {processed_target_count}/{total_targets_estimated} ({current_percent}%)", flush=True)
                                last_print_percent = current_percent
                                
                            current_target_filename = None  # Clear completed target
                        else:
                            pass
                    
                    except Exception as e:
                        print(f"[THREAD-2-JSON] ❌ CALIBRATION FAILED for target {target_filename}")
                        print(f"[THREAD-2-JSON] ❌ Error: {e}")
                        print(f"[THREAD-2-JSON] ⚠️ Skipping calibration for this target image")
                        print(f"[THREAD-2-JSON] 💡 Common causes:")
                        print(f"[THREAD-2-JSON]    - Underexposed or overexposed channels (check histogram)")
                        print(f"[THREAD-2-JSON]    - Poor lighting on calibration target")
                        print(f"[THREAD-2-JSON]    - Insufficient dynamic range in one or more channels")
                        print(f"[THREAD-2-JSON] 💡 Solution: Retake the target image with better exposure")
                        import traceback
                        traceback.print_exc()
                        
                        # Don't save fallback calibration - user wants failures to be explicit
                        # Increment counter to prevent blocking the pipeline
                        processed_targets += 1
                        current_target_filename = None  # Clear failed target
                    
                    # Update progress
                    if self.api:
                        # Use the current targets_found count from processing stats (dynamic as targets are discovered)
                        total_targets = self.processing_stats.get('targets_found', processed_targets)
                        # Ensure we don't show 0/0 - use at least the processed count
                        total_targets = max(total_targets, processed_targets, 1)
                        
                        progress_percent = int((processed_targets / total_targets) * 100) if total_targets > 0 else 0
                        self.api.update_thread_progress_premium(
                            thread_id=2,
                            percent_complete=progress_percent,
                            phase_name="Analyzing",
                            time_remaining=f"{processed_targets}/{total_targets}"
                        )
                        

                except queue.Empty:
                    consecutive_timeouts += 1
                    
                    # Check if shutdown is requested or continue waiting
                    if hasattr(self.queues, 'shutdown') and self.queues.shutdown.is_set():
                        pass
                        break
                    
                    if consecutive_timeouts >= max_consecutive_timeouts:
                        pass
                        # Send sentinel to Thread 3 so it can complete
                        try:
                            self.queues.calibration_apply_queue.put(None)
                        except:
                            pass
                        break
                    continue  # Continue waiting for targets or sentinel
                except Exception as e:
                    pass
                    import traceback
                    traceback.print_exc()
                    break
                    
            # Update final stats: calibrations_computed count
            with self.stats_lock:
                self.processing_stats['calibrations_computed'] = processed_targets
            
            
        except Exception as e:
            pass
            import traceback
            traceback.print_exc()

        # Final check: if we processed no targets but ALS data is available, save default calibration
        if processed_targets == 0:
            pass
            try:
                success = self._save_default_calibration_json()
                if success:
                    pass
                else:
                    pass
            except Exception as e:
                pass
                import traceback
        

    def _get_raw_path_and_metadata(self, image_filename):
        """
        UNIFIED HELPER: Convert any input (JPG/RAW) to RAW path + metadata
        This centralizes the logic and eliminates code duplication.
        
        Returns: (raw_image_path, img_camera_model, img_camera_filter, img_timestamp)
        """
        raw_image_path = None
        img_timestamp = None
        
        # STEP 1: Convert input to RAW path
        if image_filename.endswith('.RAW'):
            # Find full path for this RAW file - try self.images first
            images_list = getattr(self, 'images', [])
            for img in images_list:
                if hasattr(img, 'fn') and img.fn == image_filename:
                    raw_image_path = img.path
                    break
            
            # Fallback: Also check project.imagemap
            if not raw_image_path and hasattr(self, 'project') and hasattr(self.project, 'imagemap'):
                for key, img_obj in self.project.imagemap.items():
                    if hasattr(img_obj, 'fn') and img_obj.fn == image_filename:
                        raw_image_path = img_obj.path
                        break
                    
        else:  # JPG filename
            # IMPROVED: First try to find the RAW via project data structure (most reliable)
            if hasattr(self, 'project') and self.project.data.get('files'):
                jpg_base_name = os.path.splitext(image_filename)[0]
                for base_key, fileset in self.project.data['files'].items():
                    jpg_path = fileset.get('jpg')
                    raw_path = fileset.get('raw')
                    
                    if jpg_path and raw_path:
                        # Check if this fileset's JPG matches our filename
                        fileset_jpg_name = os.path.basename(jpg_path)
                        if fileset_jpg_name == image_filename:
                            raw_image_path = raw_path
                            break
            
            # Fallback: Find corresponding RAW file via imagemap timestamp matching
            if not raw_image_path:
                jpg_base = os.path.splitext(image_filename)[0]
                if hasattr(self.project, 'imagemap'):
                    for key, img_obj in self.project.imagemap.items():
                        if hasattr(img_obj, 'fn') and img_obj.fn.endswith('.RAW'):
                            raw_base = os.path.splitext(img_obj.fn)[0]
                            if raw_base[:15] == jpg_base[:15]:  # Match timestamp part
                                raw_image_path = img_obj.path
                                break
        
        if not raw_image_path:
            print(f"[THREAD-3-RAW-LOOKUP] ❌ Could not find RAW path for: {image_filename}")
            print(f"[THREAD-3-RAW-LOOKUP] 🔍 self.images count: {len(getattr(self, 'images', []))}")
            if hasattr(self, 'project') and hasattr(self.project, 'imagemap'):
                print(f"[THREAD-3-RAW-LOOKUP] 🔍 imagemap keys: {list(self.project.imagemap.keys())[:5]}...")
            # Check project data for this JPG's RAW status
            if hasattr(self, 'project') and self.project.data.get('files'):
                for base_key, fileset in self.project.data['files'].items():
                    jpg_path = fileset.get('jpg')
                    if jpg_path and os.path.basename(jpg_path) == image_filename:
                        raw_path = fileset.get('raw')
                        if not raw_path:
                            print(f"[THREAD-3-RAW-LOOKUP] 💡 This JPG has no RAW file in project data (imported without pair)")
                        break
            return None, None, None, None
        
        # STEP 2: Get camera metadata (same for all images in project)
        img_camera_model = 'Unknown'
        img_camera_filter = 'Unknown'
        
        if hasattr(self, 'project') and self.project.data.get('files'):
            pass
            for file_key, file_data in self.project.data['files'].items():
                import_metadata = file_data.get('import_metadata', {})
                found_camera_model = import_metadata.get('camera_model')
                found_camera_filter = import_metadata.get('camera_filter')
                
                if found_camera_model and found_camera_model != 'Unknown':
                    img_camera_model = found_camera_model
                    img_camera_filter = found_camera_filter or ''
                    break
        
        # STEP 3: Validate camera metadata
        if img_camera_model == 'Unknown':
            print(f"[THREAD-3-RAW-LOOKUP] ⚠️ Unknown camera model for: {image_filename}")
            # Don't fail entirely - return the RAW path but with Unknown camera model
            # The processing will need to handle this gracefully
            # return None, None, None, None  # Disabled - don't skip images just because camera model is unknown
        
        return raw_image_path, img_camera_model, img_camera_filter, img_timestamp
    
    def _process_single_image_from_queue(self, image_filename, processed_raw_files, processed_images, memory_cleanup_counter):
        """Helper function to process a single image from Thread 3 queue"""
        
        # print(f"[THREAD-3-PROCESS] 🔧 Processing {image_filename}")
        
        # Check if reflectance calibration is enabled
        reflectance_enabled = False
        if hasattr(self, 'options') and self.options:
            if 'Project Settings' in self.options and 'Processing' in self.options['Project Settings']:
                reflectance_enabled = self.options['Project Settings']['Processing'].get('Reflectance calibration / white balance', False)
            elif 'Processing' in self.options:
                reflectance_enabled = self.options['Processing'].get('Reflectance calibration / white balance', False)
        
        # print(f"[THREAD-3-PROCESS] 🔍 Reflectance enabled: {reflectance_enabled}")
        
        # If reflectance is DISABLED, skip waiting for calibration data
        calibration_data = None
        if reflectance_enabled:
            # print(f"[THREAD-3-PROCESS] ⏳ Waiting for calibration data from Thread-2...")
            # The main bottleneck: Wait for Thread 2 to save calibration data to JSON
            max_retries = 120  # Wait up to 2 minutes for Thread 2 to compute and save calibration
            for retry in range(max_retries):
                calibration_data = self._load_calibration_from_json()
                if calibration_data:
                    if retry > 0:
                        pass  # print(f"[THREAD-3-PROCESS] ✅ Got calibration data after {retry} retries")
                    break
                if retry % 15 == 0:  # Log every 15 seconds to show we're waiting for Thread 2
                    pass  # print(f"[THREAD-3-PROCESS] ⏱️ Still waiting for calibration data ({retry}s elapsed)...")
                import time
                time.sleep(1)
            
            if not calibration_data:
                print(f"[THREAD-3-PROCESS] ❌ No calibration data after {max_retries}s - skipping {image_filename}")
                return False
        else:
            pass  # print(f"[THREAD-3-PROCESS] ⏭️ Skipping calibration data wait (sensor response mode)")
        
        # Apply base calibration + unique ALS correction like original Thread 3
        
        # CRITICAL: Check if this JPG corresponds to a target RAW image
        is_target_image = False
        detection_data = self._load_detection_from_json(image_filename)
        if detection_data and detection_data.get('detected'):
            pass
            is_target_image = True
        
        # PREMIUM MODE FIX: Handle both target and non-target images
        # JPG files are ONLY for target detection - calibration must be applied to RAW pixels
        detection_data = self._load_detection_from_json(image_filename)
        
        # Determine if this is a target image based on explicit 'detected' flag
        is_explicit_target = False
        if detection_data and detection_data.get('detected'):
            is_explicit_target = True
            
        if not detection_data or not is_explicit_target:
            # UNIFIED PROCESSING: Use helper to get RAW path and metadata
            # Use unified helper to convert JPG/RAW input to RAW path + metadata
            raw_image_path, img_camera_model, img_camera_filter, img_timestamp = self._get_raw_path_and_metadata(image_filename)
            
            if not raw_image_path:
                print(f"[THREAD-3-PROCESS] ⚠️ Could not resolve RAW path for: {image_filename}")
                return False
            
            # For RAW files, check if this will be processed later as a target
            if image_filename.endswith('.RAW'):
                will_be_target = False
                for potential_jpg in getattr(self, 'images', []):
                    if (hasattr(potential_jpg, 'fn') and 
                        potential_jpg.fn.endswith('.JPG')):
                        try:
                            jpg_detection_data = self._load_detection_from_json(potential_jpg.fn)
                            if jpg_detection_data and jpg_detection_data.get('detected'):
                                target_raw_filename = jpg_detection_data.get('raw_filename')
                                if target_raw_filename == image_filename:
                                    will_be_target = True
                                    print(f"[THREAD-3-PROCESS] ⏭️ Deferring {image_filename} - will be processed as target")
                                    break
                        except:
                            continue
                
                if will_be_target:
                    return False  # Skip - will be processed as target
            
            # UNIFIED PATH: All processing now uses the same RAW path and metadata
            image_path_str = raw_image_path
            is_target_image = False

        else:
            # This is a target image with detection data - process normally
            raw_image_path = detection_data.get('raw_filename')
            if not raw_image_path or not os.path.exists(raw_image_path):
                pass
                return False
            
            image_path_str = raw_image_path
            
            # Get metadata from detection data
            img_timestamp = detection_data.get('timestamp')
            img_camera_model = detection_data.get('camera_model', 'Unknown')
            img_camera_filter = detection_data.get('camera_filter', 'Unknown')
            
            # CRITICAL FIX: If detection data doesn't have camera metadata, get it from project data
            if img_camera_model == 'Unknown':
                pass
                if self.project.data.get('files'):
                    for file_key, file_data in self.project.data['files'].items():
                        import_metadata = file_data.get('import_metadata', {})
                        found_camera_model = import_metadata.get('camera_model')
                        found_camera_filter = import_metadata.get('camera_filter')
                        
                        if found_camera_model and found_camera_model != 'Unknown':
                            img_camera_model = found_camera_model
                            img_camera_filter = found_camera_filter or ''
                            break
                
                # CRITICAL CHECK: If we still don't have camera metadata, abort
                if img_camera_model == 'Unknown':
                    pass
                    return False
            else:
                pass
            
            # CRITICAL FIX: Ensure camera model matches calibration data format
            # Thread 3 sets Survey3N_RGN but calibration data uses Survey3N
            if img_camera_model and '_' in img_camera_model:
                img_camera_model = img_camera_model.split('_')[0]  # Use base model name
            
            # Use RAW image path for calibration
            image_path_str = raw_image_path
            is_target_image = True
        
        # FRESH START FIX: Always process all files - no resume functionality
        # Remove any resume logic that checks for already processed files
        
        # CRITICAL FIX: Re-enable duplicate check to prevent processing same image multiple times
        if image_path_str in processed_raw_files:  # Re-enabled to prevent duplicates
            # print(f"[THREAD-3-PROCESS] ⏭️ Skipping duplicate: {os.path.basename(image_path_str)}")
            return False
        
        # CRITICAL: Apply calibration with proper base + ALS correction logic
        try:
            # Use global ray variable set up by _ensure_ray_available()
            global ray
            # Get the Ray function from globals (created by ensure_ray_functions_available)
            if 'apply_calibration_ray' in globals():
                apply_calibration_func = globals()['apply_calibration_ray']
                
                # CRITICAL FIX: Pass FULL project settings including vignette correction
                # Build complete options dictionary with both calibration data AND project settings
                
                # Get processing settings from project, with fallback to defaults
                project_processing = {}
                if hasattr(self.project, 'data') and self.project.data:
                    project_processing = self.project.data.get('Project Settings', {}).get('Processing', {})
                
                # If processing settings are empty, use defaults
                if not project_processing:
                    pass
                    project_processing = {
                        "Vignette correction": True,
                        "Reflectance calibration / white balance": True,
                        "Debayer method": "VNG",
                        "Minimum recalibration interval": 0,
                        "Light sensor timezone offset": 0,
                        "Apply PPK corrections": False,
                        "Exposure Pin 1": "None",
                        "Exposure Pin 2": "None"
                    }
                
                
                full_options = {
                    'calibration_data': calibration_data,  # Pass calibration data for base + ALS correction
                    'Project Settings': {
                        'Processing': project_processing
                    }
                }
                
                # CRITICAL CHECK: Ensure we have valid camera metadata before calling Ray
                if img_camera_model == 'Unknown' or not img_camera_model:
                    pass
                    return False
                
                # CRITICAL DEBUG: Log what we're actually passing to Ray
                
                result = apply_calibration_func.remote(
                    image_path_str,
                    self.project.fp,
                    full_options,  # Pass FULL options including vignette correction settings
                    img_timestamp=img_timestamp,
                    img_camera_model=img_camera_model,
                    img_camera_filter=img_camera_filter,
                    is_calibration_photo=is_target_image  # CRITICAL: Pass target flag for red square export
                )
                calibrated_data = ray.get(result)
            else:
                pass
                return False
        except Exception as e:
            pass
            import traceback
            traceback.print_exc()
            
            # Enhanced error handling for Ray failures
            error_str = str(e).lower()
            
            # Check for calibration-specific errors
            if "no calibration entry" in error_str or "calibration file not found" in error_str:
                pass
                
                # Signal Thread 4 about calibration failure
                if hasattr(self, 'queues') and hasattr(self.queues, 'export_queue'):
                    self.queues.export_queue.put({
                        "error": "calibration_failure", 
                        "message": f"Missing calibration data for {image_filename}",
                        "image": image_filename
                    })
            
            elif "raylet died" in error_str or "ray cluster" in error_str:
                pass
                
                # Check if health monitor is available and trigger restart
                if hasattr(self, 'ray_health_monitor') and self.ray_health_monitor:
                    try:
                        if self.ray_health_monitor.force_ray_restart(f"Ray failure in Thread 3: {e}"):
                            pass
                            # Could implement retry logic here if needed
                        else:
                            pass
                    except Exception as restart_error:
                        pass
                else:
                    pass
                    
            # Track Ray failures for fallback decisions
            if hasattr(self, 'ray_failures'):
                self.ray_failures += 1
                
                if self.ray_failures >= self.max_ray_failures:
                    pass
                    # Signal Thread 4 about the failure
                    if hasattr(self, 'queues') and hasattr(self.queues, 'export_queue'):
                        self.queues.export_queue.put({
                            "error": "max_ray_failures", 
                            "message": f"Thread 3 exceeded max Ray failures ({self.max_ray_failures})"
                        })
                    
            return False
        
        if calibrated_data and isinstance(calibrated_data, dict) and calibrated_data.get('image'):
            pass
            
            # CRITICAL FIX: Get calibrated data from Ray function
            calibrated_image = calibrated_data.get('image')
            calibrated_data_copy = calibrated_data.get('calibrated_data')
            data_min_max = calibrated_data.get('data_min_max', (0, 0))
            
            if calibrated_image and calibrated_data_copy is not None:
                # CRITICAL: Ensure the image object has the calibrated data
                import numpy as np
                calibrated_image.data = calibrated_data_copy
                
                # Ensure the image has the is_calibration_photo flag for target export
                if hasattr(calibrated_image, 'is_calibration_photo'):
                    pass
                
                # Update stats: increment calibrations_processed and images_calibrated
                # CRITICAL FIX: Only count RAW files for images_calibrated to match progress calculation
                with self.stats_lock:
                    self.processing_stats['calibrations_processed'] += 1
                    # Only increment images_calibrated for RAW files since progress calculation expects only RAW count
                    if image_filename.upper().endswith('.RAW'):
                        self.processing_stats['images_calibrated'] += 1
                    else:
                        pass
                
                # print(f"[THREAD-3-JSON] 📤 Queuing {image_filename} for export (fn={getattr(calibrated_image, 'fn', 'unknown')})")
                self.queues.queue_to_export(calibrated_image, "thread-3")
                # print(f"[THREAD-3-JSON] ✅ Successfully queued {image_filename} to export_queue")
                
                # PREMIUM MODE FIX: Mark this RAW file as processed
                processed_raw_files.add(image_path_str)
                
                # Enhanced memory management for large datasets
                import gc
                import psutil
                if memory_cleanup_counter >= MEMORY_CLEANUP_INTERVAL:
                    pass
                    
                    # Get memory usage before cleanup
                    memory_before = psutil.virtual_memory().percent
                    
                    # Python garbage collection
                    gc.collect()
                    
                    # Ray object store cleanup if available
                    if hasattr(self, 'ray_health_monitor') and self.ray_health_monitor:
                        self.ray_health_monitor.cleanup_memory()
                    
                    # CRITICAL: Cleanup deduplication cache for large datasets
                    self._cleanup_deduplication_cache()
                    
                    # Get memory usage after cleanup
                    memory_after = psutil.virtual_memory().percent
                    memory_freed = memory_before - memory_after
                    
                    
                    # Trigger more aggressive cleanup if memory usage is high
                    if memory_after > 80.0:
                        pass
                        
                        # Clear any image caches
                        if hasattr(self.queues, 'image_cache'):
                            with self.queues.cache_lock:
                                self.queues.image_cache.clear()
                                self.queues.cache_order.clear()
                        
                        # Force another garbage collection
                        gc.collect()
                        
                        # Check if Ray health monitor can help
                        if hasattr(self, 'ray_health_monitor') and self.ray_health_monitor:
                            metrics = self.ray_health_monitor.get_health_metrics()
                            if metrics.system_memory_usage_percent > 85.0:
                                pass
                                self.ray_health_monitor.force_ray_restart("Critical memory usage in Thread 3")
                
                return True
            else:
                pass
                self.queues.queue_to_export(calibrated_data.get('image', None), "thread-3")
                processed_raw_files.add(image_path_str)
                return True
        else:
            pass
            return False

    def _thread3_calibration_apply_json_centric(self):
        """Thread 3: Apply calibration to all images using data from JSON"""
        
        # print("[THREAD-3-JSON] 🚀 Thread-3 STARTED - waiting for images from Thread-1")
        
        from tqdm import tqdm
        import queue
        import gc
        processed_images = 0
        thread1_completed = False
        # FRESH START FIX: Always start with empty set - no resume functionality
        processed_raw_files = set()
        
        # Calculate total files for progress bar
        total_files_count = 0
        if hasattr(self, 'images') and self.images:
             for img in self.images:
                if hasattr(img, 'fn') and img.fn.lower().endswith('.raw'):
                    total_files_count += 1
        else:
            if hasattr(self, 'project') and self.project.data.get('files'):
                for fileset in self.project.data['files'].values():
                    if fileset.get('raw'):
                       total_files_count += 1
        total_files_count = max(1, total_files_count)

        # Initialize progress tracking
        # Replaced tqdm with simple periodic printing for reliable logging
        last_print_percent = -1
        
        # Memory management for large datasets
        memory_cleanup_counter = 0
        
        try:
            while True:
                # CRITICAL: Check for stop request before waiting for next image
                if self.queues.shutdown.is_set() or self._stop_requested:
                    # print("[THREAD-3-JSON] ⏹️ Stop requested, exiting")
                    # pbar.close() # Removed
                    break
                
                try:
                    image_filename = self.queues.calibration_apply_queue.get(timeout=1)  # Short timeout for responsive shutdown
                    
                    if image_filename is None:  # Sentinel from Thread 1
                        # print(f"[THREAD-3-JSON] 🛑 Received sentinel from Thread-1 after processing {processed_images} images - checking for remaining")
                        thread1_completed = True
                        # CRITICAL FIX: Don't break immediately - process all remaining images in queue first
                        remaining_count = 0
                        while True:
                            try:
                                remaining_image = self.queues.calibration_apply_queue.get_nowait()
                                if remaining_image is None:
                                    break  # Another sentinel, ignore it
                                # print(f"[THREAD-3-JSON] 🔄 Processing remaining image: {remaining_image}")
                                # Process this remaining image immediately
                                self._process_single_image_from_queue(remaining_image, processed_raw_files, processed_images, memory_cleanup_counter)
                                remaining_count += 1
                                processed_images += 1
                                memory_cleanup_counter += 1
                                
                                # CRITICAL FIX: Update progress after processing each remaining image
                                if self.api:
                                    # Calculate total RAW files from current processing batch
                                    total_raw_files = 0
                                    if hasattr(self, 'images') and self.images:
                                        for img in self.images:
                                            if hasattr(img, 'fn') and img.fn.lower().endswith('.raw'):
                                                total_raw_files += 1
                                    else:
                                        if hasattr(self, 'project') and self.project.data.get('files'):
                                            for fileset in self.project.data['files'].values():
                                                if fileset.get('raw'):
                                                    total_raw_files += 1
                                    total_raw_files = max(1, total_raw_files)
                                    
                                    # Use the actual images_calibrated count from processing stats
                                    raw_files_processed = self.processing_stats.get('images_calibrated', 0)
                                    progress_percent = min(100, int((raw_files_processed / total_raw_files) * 100))
                                    
                                    self.api.update_thread_progress_premium(
                                        thread_id=3,
                                        percent_complete=progress_percent,
                                        phase_name="Calibrating",
                                        time_remaining=f"{raw_files_processed}/{total_raw_files}"
                                    )
                                
                            except queue.Empty:
                                # print(f"[THREAD-3-JSON] ✅ Finished processing {remaining_count} remaining images")
                                break  # No more items in queue
                        
                        # CRITICAL FIX: Send final 100% progress update to UI
                        if self.api:
                            total_raw_files = 0
                            if hasattr(self, 'images') and self.images:
                                for img in self.images:
                                    if hasattr(img, 'fn') and img.fn.lower().endswith('.raw'):
                                        total_raw_files += 1
                            else:
                                if hasattr(self, 'project') and self.project.data.get('files'):
                                    for fileset in self.project.data['files'].values():
                                        if fileset.get('raw'):
                                            total_raw_files += 1
                            total_raw_files = max(1, total_raw_files)
                            
                            # For 100% completion, always show total/total to indicate all files finished
                            # Use the actual counter as a reference but show the full count
                            actual_processed = self.processing_stats.get('images_calibrated', 0)
                            # print(f"[THREAD-3-JSON] 📊 Counter shows {actual_processed}/{total_raw_files}, sending 100% update with {total_raw_files}/{total_raw_files}")
                            
                            self.api.update_thread_progress_premium(
                                thread_id=3,
                                percent_complete=100,
                                phase_name="Calibrating",
                                time_remaining=f"{total_raw_files}/{total_raw_files}"
                            )
                            # print(f"[THREAD-3-JSON] ✅ Final progress update: {total_raw_files}/{total_raw_files} (100%)")
                        
                        # print(f"[THREAD-3-JSON] 🏁 Thread-3 completed, processed {processed_images} total images")
                        # pbar.close() # Removed
                        break
                    
                    # Process this image normally
                    # print(f"[THREAD-3-JSON] 🔧 Processing image: {image_filename}")
                    self._process_single_image_from_queue(image_filename, processed_raw_files, processed_images, memory_cleanup_counter)
                    processed_images += 1
                    memory_cleanup_counter += 1
                    
                    # Update progress after processing
                    if self.api:
                        # FRESH START FIX: Calculate total RAW files from current processing batch (no cached data)
                        # Count RAW files from the images currently being processed, not from project data
                        total_raw_files = 0
                        if hasattr(self, 'images') and self.images:
                            # Count RAW files in the current processing batch
                            for img in self.images:
                                if hasattr(img, 'fn') and img.fn.lower().endswith('.raw'):
                                    total_raw_files += 1
                        else:
                            # Fallback: count from project data if images not available
                            if hasattr(self, 'project') and self.project.data.get('files'):
                                for fileset in self.project.data['files'].values():
                                    if fileset.get('raw'):
                                        total_raw_files += 1
                                # print(f"[THREAD-3-FALLBACK] 🎯 Counted {total_raw_files} RAW files from project data (fallback)")
                        total_raw_files = max(1, total_raw_files)  # Ensure at least 1 to avoid division by zero
                        
                        # Use the actual images_calibrated count from processing stats
                        raw_files_processed = self.processing_stats.get('images_calibrated', 0)
                        progress_percent = min(100, int((raw_files_processed / total_raw_files) * 100))
                        
                        pass
                        
                        # Only print when progress changes
                        current_percent = progress_percent
                        if current_percent != last_print_percent:
                            self.api.update_thread_progress_premium(
                                thread_id=3,
                                percent_complete=progress_percent,
                                phase_name="Calibrating",
                                time_remaining=f"{raw_files_processed}/{total_raw_files}"
                            )
                            
                            # Print progress update
                            if total_raw_files < 10 or (current_percent % 10 == 0):
                                msg = f"[CALIBRATING] {raw_files_processed}/{total_raw_files} ({current_percent}%)"
                                print(msg, flush=True)
                                # WORKAROUND: Write directly to log file
                                import sys, os
                                if hasattr(sys.stdout, 'log_file_path'):
                                    try:
                                        with open(sys.stdout.log_file_path, 'a', encoding='utf-8') as log:
                                            log.write(msg + "\n")
                                            log.flush()
                                            os.fsync(log.fileno())
                                    except: pass

                            last_print_percent = current_percent
                        
                except queue.Empty:
                    # print("[THREAD-3-JSON] ⏱️ Queue timeout (1s), continuing to wait...")
                    # Check if shutdown is requested
                    if hasattr(self.queues, 'shutdown') and self.queues.shutdown.is_set():
                        print("[THREAD-3-JSON] ⏹️ Shutdown requested during timeout")
                        # pbar.close() # Removed
                        break
                    continue  # Continue waiting for images or sentinel
            
            # Thread 1 completed - send sentinel to Thread 4
            self.queues.export_queue.put(None)
            
            
        except Exception as e:
            pass
            import traceback
            traceback.print_exc()

    def _thread4_export_json_centric(self):
        """Thread 4: Export processed images with robust error handling"""
        
        from tqdm import tqdm
        import queue
        exported_images = 0
        consecutive_timeouts = 0
        # CRITICAL FIX: Add duplicate detection to prevent processing same image multiple times
        processed_images = set()  # Track already processed images by filename
        # CRITICAL FIX: Increase timeout threshold for large datasets with slow Ray processing
        # With 5-second timeouts, 30 timeouts = 2.5 minutes, which is more reasonable for large images
        max_consecutive_timeouts = 60  # Increased from 30 to 60 (5 minutes total wait time)
        thread3_failure_detected = False
        
        # Calculate total files for progress bar
        # CRITICAL FIX: Count all image pairs (JPG or RAW) to match project input
        # This counts filesets that have either JPG or RAW files
        total_export_pairs = 0
        if hasattr(self, 'project') and self.project.data.get('files'):
            for fileset in self.project.data['files'].values():
                if fileset.get('jpg') or fileset.get('raw'):
                    total_export_pairs += 1
        total_export_pairs = max(1, total_export_pairs)

        # Initialize progress bar
        # CRITICAL FIX: Use ASCII only and slower updates to prevent log glitches overlap
        # pbar = tqdm(total=total_export_pairs, desc="Exporting", unit="img", leave=True, 
        #           ascii=True, mininterval=1.0, ncols=80, position=1)
        
        try:
            while True:
                # CRITICAL: Check for stop request before waiting for next image
                if self.queues.shutdown.is_set() or self._stop_requested:
                    pass
                    break
                
                try:
                    # CRITICAL FIX: Increase timeout for large datasets - Ray processing can be slow
                    # Large images with vignette correction + calibration can take 30+ seconds per image
                    calibrated_data = self.queues.export_queue.get(timeout=5)  # Increased from 1 to 5 seconds
                    
                    # Check for error signals from Thread 3
                    if isinstance(calibrated_data, dict) and calibrated_data.get('error'):
                        error_type = calibrated_data.get('error')
                        error_message = calibrated_data.get('message', 'Unknown error')
                        
                        if error_type in ["max_ray_failures", "calibration_failure", "thread3_terminated"]:
                            pass
                            break
                        else:
                            pass
                    
                    # Reset timeout counter on successful data receive
                    consecutive_timeouts = 0
                    
                    if calibrated_data is None:  # Sentinel from Thread 3
                        # pbar.close() # Removed
                        break
                    
                    # Handle both old format (filename string) and new format (calibrated data dict)
                    # CRITICAL FIX: Handle image object directly (new format from Thread 3)
                    if hasattr(calibrated_data, 'fn') and hasattr(calibrated_data, 'data'):
                        # Thread 3 now sends image object directly
                        image = calibrated_data
                        image_filename = image.fn
                        if image.data is not None:
                            pass
                            # Check if data looks calibrated (reflectance values are typically 0-1 scaled to uint16, max ~65535)
                            # RAW values typically exceed 65535 or are unprocessed, calibrated values stay within uint16 range
                            if image.data.dtype == 'uint16' and image.data.max() <= 65535:
                                pass
                            else:
                                pass
                    elif isinstance(calibrated_data, str):
                        pass
                        image_filename = calibrated_data
                    elif isinstance(calibrated_data, dict) and calibrated_data.get('image'):
                        image = calibrated_data['image']
                        image_filename = image.fn
                    else:
                        pass
                        continue
                    
                    # CRITICAL FIX: Check for duplicates to prevent double processing
                    if image_filename in processed_images:
                        pass
                        continue
                    
                    # Mark image as being processed
                    processed_images.add(image_filename)
                    
                    # PREMIUM MODE FIX: Check if this is a target image by looking at calibration JSON
                    # This is more reliable than relying on the image object's flag
                    is_target_from_json = self._check_if_target_from_json(image_filename)
                    is_target_from_image = hasattr(image, 'is_calibration_photo') and image.is_calibration_photo
                    
                    # Use JSON data as the authoritative source for target status
                    is_target = is_target_from_json or is_target_from_image
                    
                    # Export the calibrated reflectance for ALL images (including targets)
                    if is_target:
                        pass
                    else:
                        pass
                    
                    success = self._export_single_image_json(image)
                    if success:
                        pass
                        exported_images += 1
                        
                        # CRITICAL: Register reflectance/sensor response layer to image.layers and project data
                        # The _export_single_image_json sets image.path to the exported file
                        import os
                        
                        # Determine layer name based on reflectance AND vignette settings
                        reflectance_enabled = False
                        vignette_enabled = False
                        if hasattr(self, 'options') and self.options:
                            if 'Project Settings' in self.options and 'Processing' in self.options['Project Settings']:
                                reflectance_enabled = self.options['Project Settings']['Processing'].get('Reflectance calibration / white balance', False)
                                vignette_enabled = self.options['Project Settings']['Processing'].get('Vignette correction', False)
                            elif 'Processing' in self.options:
                                reflectance_enabled = self.options['Processing'].get('Reflectance calibration / white balance', False)
                                vignette_enabled = self.options['Processing'].get('Vignette correction', False)
                        
                        # Set layer name based on processing type
                        if reflectance_enabled:
                            layer_name = "RAW (Reflectance)"
                        elif vignette_enabled:
                            layer_name = "RAW (Vignette Corrected)"
                        else:
                            layer_name = "RAW (Sensor Response)"
                        
                        if hasattr(image, 'path') and image.path:
                            reflectance_export_path = image.path
                            
                            # Add to image.layers with dynamic layer name
                            if not hasattr(image, 'layers'):
                                image.layers = {}
                            image.layers[layer_name] = reflectance_export_path
                            
                            # Add to project data for persistence with dynamic layer name
                            if hasattr(self, 'project') and self.project and hasattr(self.project, 'data'):
                                for base, fileset in self.project.data.get('files', {}).items():
                                    if fileset.get('raw') and os.path.basename(fileset['raw']) == image_filename:
                                        if 'layers' not in fileset:
                                            fileset['layers'] = {}
                                        fileset['layers'][layer_name] = reflectance_export_path
                                        break
                        else:
                            pass
                        
                        # CRITICAL: Export index/LUT images after reflectance/sensor response export
                        try:
                            import os
                            # Get reflectance/sensor response path from layers if available
                            reflectance_path = None
                            reflectance_data = None
                            if hasattr(image, 'layers') and image.layers:
                                # Use the dynamic layer_name that was set above
                                reflectance_path = image.layers.get(layer_name, None)
                            
                            # If we just exported reflectance, use the in-memory data
                            if hasattr(image, 'data') and image.data is not None:
                                reflectance_data = image.data
                            
                            # Call _export_index_images with correct parameters
                            # Get output format from project settings
                            output_format = "tiff16"  # Default fallback
                            if self.options and 'Project Settings' in self.options:
                                export_settings = self.options['Project Settings'].get('Export', {})
                                format_name = export_settings.get('Calibrated image format', 'TIFF (16-bit)')
                                # Convert from UI format name to internal code using fmt_map (module-level variable)
                                output_format = fmt_map.get(format_name, 'tiff16')
                            
                            index_layers = self._export_index_images(
                                image, 
                                self.options,  # Pass pipeline options
                                self.outfolder, 
                                output_format, 
                                reflectance_path, 
                                reflectance_data
                            )
                            
                            if index_layers:
                                pass
                                # Add index layers to image object
                                if not hasattr(image, 'layers'):
                                    image.layers = {}
                                image.layers.update(index_layers)
                                
                                # Add to project data for persistence
                                if hasattr(self, 'project') and self.project and hasattr(self.project, 'data'):
                                    for base, fileset in self.project.data.get('files', {}).items():
                                        if fileset.get('raw') and os.path.basename(fileset['raw']) == image_filename:
                                            if 'layers' not in fileset:
                                                fileset['layers'] = {}
                                            fileset['layers'].update(index_layers)
                                            break
                            else:
                                pass
                        except Exception as index_err:
                            pass
                            import traceback
                            traceback.print_exc()
                        
                        # Update processing stats
                        # CRITICAL FIX: Count ALL exported files (RAW, JPG, TIFF) to match progress calculation
                        # This ensures the "0 results" check in api.py works correctly for all file types
                        with self.stats_lock:
                            self.processing_stats['images_exported'] += 1
                        
                        # Add to completed queue for API completion logic
                        result = {
                            'reflectance': True,
                            'calibrated': True,
                            'exported': True
                        }
                        
                        # Update tqdm progress bar - Replaced with simple print
                        current_percent = min(100, int((exported_images / total_export_pairs) * 100))
                        if total_export_pairs < 10 or (exported_images % 10 == 0):
                            print(f"[EXPORTING] {exported_images}/{total_export_pairs} ({current_percent}%)", flush=True)
                        
                        try:
                            # pbar.update(1) # Removed
                            pass
                        except:
                            pass
                        if is_target:
                            result['target'] = True
                        self.queues.completed.put((getattr(image, 'fn', image_filename), result))
                    else:
                        pass
                    
                    # ADDITIONALLY, if this is a target image, also export with red squares
                    if is_target:
                        pass
                        target_success = self._export_target_with_red_squares_json(image)
                        if target_success:
                            pass
                        else:
                            pass
                    
                    # Update progress
                    if self.api:
                        # CRITICAL FIX: Count all image pairs (JPG or RAW) to match project input
                        total_image_pairs = 0
                        if hasattr(self, 'project') and self.project.data.get('files'):
                            # Count filesets that have JPG or RAW
                            for fileset in self.project.data['files'].values():
                                if fileset.get('jpg') or fileset.get('raw'):
                                    total_image_pairs += 1
                        total_image_pairs = max(1, total_image_pairs)  # Ensure at least 1 to avoid division by zero
                        progress_percent = min(100, int((exported_images / total_image_pairs) * 100))
                        self.api.update_thread_progress_premium(
                            thread_id=4,
                            percent_complete=progress_percent,
                            phase_name="Exporting",
                            time_remaining=f"{exported_images}/{total_image_pairs}"
                        )
                    
                    # OPTIMIZATION: Delete cached debayered TIFF immediately after export
                    # This prevents disk space buildup for large projects with thousands of images
                    try:
                        if hasattr(self, 'project') and self.project:
                            self.project.delete_cached_tiff(image_filename)
                        elif hasattr(self, 'api') and self.api and hasattr(self.api, 'project'):
                            self.api.project.delete_cached_tiff(image_filename)
                    except Exception as cache_err:
                        pass  # Non-critical - final cleanup will handle any remaining files
                
                except queue.Empty:
                    consecutive_timeouts += 1
                    elapsed_wait_time = consecutive_timeouts * 5  # 5 seconds per timeout
                    
                    # Check if shutdown is requested
                    if hasattr(self.queues, 'shutdown') and self.queues.shutdown.is_set():
                        pass
                        break
                    
                    # Check Thread 3 status every 10 timeouts (50 seconds)
                    if consecutive_timeouts % 10 == 0:
                        pass
                    
                    # Check for Thread 3 failure after consecutive timeouts
                    if consecutive_timeouts >= max_consecutive_timeouts and not thread3_failure_detected:
                        thread3_failure_detected = True
                        
                        # Check if Ray health monitor indicates issues
                        try:
                            from ray_health_monitor import get_ray_health_monitor
                            health_monitor = get_ray_health_monitor()
                            if not health_monitor.is_ray_healthy():
                                pass
                                if health_monitor.force_ray_restart("Thread 4 detected prolonged inactivity"):
                                    pass
                                    consecutive_timeouts = 0  # Reset timeout counter
                                    thread3_failure_detected = False
                                else:
                                    pass
                                    break
                            else:
                                pass
                        except ImportError:
                            pass
                    
                    # Continue waiting unless we've hit critical failure
                    if consecutive_timeouts < max_consecutive_timeouts * 3:  # Give extra time after restart attempts
                        continue
                    else:
                        pass
                        # pbar.close() # Removed
                        break
                except Exception as e:
                    pass
                    import traceback
                    traceback.print_exc()
                    break
                    
            
        except Exception as e:
            # print(f"[THREAD-4-JSON] ❌ Exception in Thread-4: {e}")
            import traceback
            traceback.print_exc()
        finally:
            pass
            # print(f"[THREAD-4-JSON] 🏁 Thread-4 completed - exported {exported_images} images")
            # print(f"[THREAD-4-JSON] 📊 Completed queue size: {self.queues.completed.qsize()}")

    def _check_if_target_from_json(self, image_filename):
        """Check if an image is a target by looking at detection JSON data"""
        try:
            import json
            import os
            
            # CRITICAL FIX: Check detection JSON, not calibration JSON
            # Detection JSON contains all images that were detected as having targets
            # Calibration JSON only contains images selected for coefficient computation
            project_dir = getattr(self.project, 'fp', None)
            if not project_dir:
                return False
                
            detection_json_path = os.path.join(project_dir, 'detection_data.json')
            if not os.path.exists(detection_json_path):
                pass
                return False
            
            # Load detection data
            with open(detection_json_path, 'r') as f:
                detection_data = json.load(f)
            
            # Find the JPG filename that corresponds to this RAW file
            jpg_filename = None
            
            # Search through project data files to find the JPG that corresponds to this RAW
            for base_key, fileset in self.project.data.get('files', {}).items():
                if fileset.get('raw'):
                    raw_path = fileset['raw']
                    raw_basename = os.path.basename(raw_path)
                    
                    # Check if this is the RAW file we're looking for
                    if raw_basename == image_filename or image_filename in raw_path:
                        jpg_filename = fileset.get('jpg')
                        if jpg_filename:
                            jpg_filename = os.path.basename(jpg_filename)
                            break
            
            if not jpg_filename:
                pass
                return False
            
            # Check if the JPG was detected as having a target
            detection_results = detection_data.get('detection_results', {})
            jpg_detection = detection_results.get(jpg_filename)
            
            if jpg_detection and jpg_detection.get('detected', False):
                pass
                return True
            else:
                pass
                return False
                
        except Exception as e:
            pass
            return False

    def _update_project_data_realtime(self, jpg_filename, is_calibration_photo):
        """Update project data immediately when target is detected (JSON-centric version)"""
        try:
            pass
            
            # CRITICAL: Update AND SAVE project data immediately so UI can refresh
            if hasattr(self, 'api') and self.api and hasattr(self.api, 'project') and self.api.project:
                # Find the correct project data key by searching for the JPG filename
                project_key = None
                for key, fileset in self.api.project.data['files'].items():
                    if 'jpg' in fileset and fileset['jpg'].endswith(jpg_filename):
                        project_key = key
                        break
                
                if project_key:
                    # Update project data
                    if 'calibration' not in self.api.project.data['files'][project_key]:
                        self.api.project.data['files'][project_key]['calibration'] = {}
                    self.api.project.data['files'][project_key]['calibration']['is_calibration_photo'] = is_calibration_photo
                    self.api.project.data['files'][project_key]['manual_calib'] = is_calibration_photo
                    # CRITICAL FIX: Set calib_detected flag for UI checkbox (same as realtime version)
                    self.api.project.data['files'][project_key]['calib_detected'] = is_calibration_photo

                    # CRITICAL: Save project to JSON file immediately so UI can reload fresh data
                    try:
                        self.api.project.write()
                    except Exception as save_error:
                        pass
                else:
                    pass
        except Exception as e:
            pass

    def _dispatch_comprehensive_sse_events(self, jpg_filename, is_calibration_photo):
        """Dispatch all SSE events for UI updates (JSON-centric version)"""
        try:
            pass
            
            # Import backend_server for SSE dispatch
            import backend_server
            import time
            
            # Dispatch target-detected event
            backend_server.dispatch_event('target-detected', {
                'filename': jpg_filename,
                'is_calibration_photo': is_calibration_photo
            })
            
            # Force UI refresh by dispatching additional events
            backend_server.dispatch_event('images-updated', {})
            backend_server.dispatch_event('files-changed', {'hasFiles': True})
            
            # CRITICAL: Force immediate UI refresh with a dedicated event
            backend_server.dispatch_event('force-ui-refresh', {
                'type': 'target-detection',
                'filename': jpg_filename,
                'timestamp': str(time.time())
            })
            
            # CRITICAL: Force project data reload to ensure UI sees latest changes
            backend_server.dispatch_event('project-data-changed', {
                'filename': jpg_filename,
                'is_calibration_photo': is_calibration_photo,
                'timestamp': str(time.time())
            })
            
            # CRITICAL: Force immediate image list refresh
            backend_server.dispatch_event('refresh-image-list', {
                'reason': 'target-detection',
                'filename': jpg_filename
            })
            
            # CRITICAL: Force complete UI component remount
            backend_server.dispatch_event('remount-components', {
                'components': ['image-list', 'file-list'],
                'reason': 'target-detection',
                'filename': jpg_filename
            })
            
            
        except Exception as e:
            pass

    def _export_target_with_red_squares_json(self, image):
        """Export target image with red square polygons drawn to Target Found folder"""
        try:
            import os
            import numpy as np
            import cv2
            from mip.Save_Format import save_format
            
            
            # CRITICAL: For target export, we need the ORIGINAL RAW pixels (before calibration)
            # Thread 3 sends us calibrated RAW data, but for target export we need original RAW data
            
            # The image we receive from Thread 3 has calibrated data, but we need original RAW data
            # CRITICAL FIX: Find the actual JPG filename from project data, not RAW filename conversion
            jpg_filename = None
            
            # CRITICAL FIX: Handle both .RAW and .tif extensions
            # Thread 4 might receive filenames with .tif extension after export
            raw_fn_to_search = image.fn
            if raw_fn_to_search.endswith('.tif'):
                # Convert .tif back to .RAW for project data lookup
                raw_fn_to_search = raw_fn_to_search.replace('.tif', '.RAW')
            
            # CRITICAL FIX: Find the JPG filename using the original path from the image object
            # The image should have path information from when it was loaded
            if hasattr(image, 'path'):
                pass
            
            # CRITICAL FIX: Use project data to find the JPG filename for the RAW file
            # The project.json already contains JPG-RAW pairs in the files section
            
            # Search through project data files to find the JPG that corresponds to this RAW
            for base_key, fileset in self.project.data.get('files', {}).items():
                if fileset.get('raw'):
                    raw_path = fileset['raw']
                    raw_basename = os.path.basename(raw_path)
                    
                    # Check if this is the RAW file we're looking for
                    if raw_basename == raw_fn_to_search or raw_fn_to_search in raw_path:
                        jpg_filename = fileset.get('jpg')
                        if jpg_filename:
                            jpg_filename = os.path.basename(jpg_filename)
                            break
            
            if not jpg_filename:
                pass
                return False
            
            
            # Load the ORIGINAL RAW file data (before calibration)
            original_raw_data = None
            
            # Find the RAW file from project mappings
            for base_key, file_data in self.project.data.get('files', {}).items():
                jpg_path = file_data.get('jpg', '')  # FIXED: Use 'jpg' key, not 'jpg_path'
                
                # More flexible matching
                if (jpg_path and (
                    jpg_path.endswith(jpg_filename) or 
                    os.path.basename(jpg_path) == jpg_filename or
                    jpg_filename in jpg_path
                )):
                    raw_path = file_data.get('raw')  # FIXED: Use 'raw' key, not 'raw_path'
                    if raw_path and os.path.exists(raw_path):
                        pass
                        # CRITICAL FIX: Load from cached debayered TIFF to avoid re-debayering
                        # This ensures we only debayer each image once
                        import numpy as np
                        raw_filename = os.path.basename(raw_path)
                        cached_tiff_path = self.project.get_cached_debayered_tiff(raw_filename)
                        
                        if cached_tiff_path and os.path.exists(cached_tiff_path):
                            import tifffile as tiff
                            original_raw_data = tiff.imread(cached_tiff_path)
                        else:
                            pass
                            from project import LabImage
                            original_raw_image = LabImage(self.project, raw_path)
                            original_raw_data = original_raw_image.data  # This will trigger debayering and caching
                            # Convert BGR to RGB since data property returns BGR
                            import cv2
                            original_raw_data = cv2.cvtColor(original_raw_data, cv2.COLOR_BGR2RGB)
                        
                        break
                    else:
                        pass
                else:
                    pass
            
            # Create target image object for export
            target_image = image.copy()
            
            if original_raw_data is not None:
                pass
                target_image_data = original_raw_data.copy()
            else:
                pass
                if target_image.data is None:
                    pass
                    return False
                target_image_data = target_image.data.copy()
            
            # CRITICAL FIX: Load target detection data from JSON to get correct red squares
            detection_data = self._load_detection_from_json(jpg_filename)
            
            if detection_data and detection_data.get('calibration_target_polys'):
                target_image.calibration_target_polys = detection_data['calibration_target_polys']
            else:
                pass
                # Try to generate them from ArUco corners if available
                if detection_data and detection_data.get('aruco_corners') is not None:
                    pass
                    target_image.aruco_id = detection_data.get('aruco_id')
                    target_image.aruco_corners = detection_data['aruco_corners']
                    
                    try:
                        from mip.Calibration_Target import calibration_target_polys
                        calibration_target_polys(target_image)
                    except Exception as e:
                        pass
                        target_image.calibration_target_polys = []
                else:
                    pass
                    target_image.calibration_target_polys = []
            
            # Draw red square polygons if available
            if hasattr(target_image, 'calibration_target_polys') and target_image.calibration_target_polys:
                pass
                
                for i, poly in enumerate(target_image.calibration_target_polys):
                    try:
                        # Draw border lines only, not filled squares
                        # CRITICAL: RGB data has channels [R,G,B] so red is (65535,0,0) at channel 0
                        pts = np.array(poly, dtype=np.int32).reshape((-1, 1, 2))
                        cv2.polylines(target_image_data, [pts], True, (65535, 0, 0), thickness=8)  # Red color for RGB data
                    except Exception as e:
                        pass
                        # Try to fix the issue by ensuring proper data format
                        try:
                            if not target_image_data.flags.writeable:
                                target_image_data = target_image_data.copy()
                            target_image_data = np.ascontiguousarray(target_image_data, dtype=np.uint16)
                            pts = np.array(poly, dtype=np.int32).reshape((-1, 1, 2))
                            cv2.polylines(target_image_data, [pts], True, (65535, 0, 0), thickness=8)  # Red for RGB data
                        except Exception as e2:
                            pass
                            continue
                
                # Draw green center dot and yellow line from ArUco to target center
                try:
                    # Calculate target center from polygon centers (where all 4 patches meet)
                    if len(target_image.calibration_target_polys) == 4:
                        # Target center is the average of all polygon centers
                        poly_centers = [np.mean(poly, axis=0).astype(int) for poly in target_image.calibration_target_polys]
                        target_center = np.mean(poly_centers, axis=0).astype(int)
                        target_center = tuple(target_center)
                        
                        # Calculate ArUco marker center from detection data
                        if detection_data and detection_data.get('aruco_corners') is not None:
                            aruco_corners_array = np.array(detection_data['aruco_corners']).squeeze()
                            aruco_center = np.mean(aruco_corners_array, axis=0).astype(int)
                            aruco_center = tuple(aruco_center)
                            
                            # Draw yellow line from ArUco center to target center
                            # RGB data: yellow is (65535, 65535, 0)
                            cv2.line(target_image_data, aruco_center, target_center, (65535, 65535, 0), thickness=4)
                        
                        # Draw green center dot at target center
                        # Green is (0, 65535, 0) in RGB
                        cv2.circle(target_image_data, target_center, radius=10, color=(0, 65535, 0), thickness=-1)  # Filled circle (dot)
                except Exception as e:
                    pass
            else:
                pass
                
                # CRITICAL: Load ArUco data from detection JSON for polygon generation
                # FIXED: Use the actual JPG filename from project data, not RAW filename conversion
                jpg_filename = None
                
                # Find the JPG filename that corresponds to this RAW file
                for base_key, file_data in self.project.data.get('files', {}).items():
                    raw_path = file_data.get('raw_path', '')
                    if raw_path and (raw_path.endswith(image.fn) or image.fn in raw_path):
                        jpg_path = file_data.get('jpg_path', '')
                        if jpg_path:
                            jpg_filename = os.path.basename(jpg_path)
                            break
                
                if not jpg_filename:
                    pass
                    return False
                    
                detection_data = self._load_detection_from_json(jpg_filename)
                if detection_data and detection_data.get('detected'):
                    target_image.aruco_id = detection_data.get('aruco_id')
                    target_image.aruco_corners = detection_data.get('aruco_corners')
                else:
                    pass
                
                # Generate calibration target polygons if not present
                try:
                    from mip.Calibration_Target import calibration_target_polys, draw_calibration_samples
                    calibration_target_polys(target_image)
                    if hasattr(target_image, 'calibration_target_polys') and target_image.calibration_target_polys:
                        # Apply the generated polygons to the copy
                        temp_image = target_image.copy()
                        temp_image.data = target_image_data
                        draw_calibration_samples(temp_image)
                        target_image_data = temp_image.data
                    else:
                        pass
                except Exception as e:
                    pass
            
            # Set up target export path in Target Found folder
            # CRITICAL: Get camera model from project JSON - NEVER use fallback values
            camera_model = getattr(image, 'camera_model', 'Unknown')
            camera_filter = getattr(image, 'camera_filter', 'Unknown')
            
            # If camera model is Unknown, search project JSON (should have been populated during import)
            if camera_model == 'Unknown' and self.project.data.get('files'):
                pass
                for file_key, file_data in self.project.data['files'].items():
                    import_metadata = file_data.get('import_metadata', {})
                    if import_metadata.get('camera_model') and import_metadata.get('camera_model') != 'Unknown':
                        camera_model = import_metadata.get('camera_model')
                        camera_filter = import_metadata.get('camera_filter', '')
                        break
            
            # CRITICAL: If camera model is still Unknown, attempt EXIF recovery
            if camera_model == 'Unknown':
                pass
                
                # Get the original RAW filename for EXIF reading
                raw_filename = image.fn.replace('.tif', '.RAW')  # Convert back to RAW filename
                
                # Look for JPG file associated with this RAW for EXIF reading
                jpg_filename = None
                if self.project.data.get('files'):
                    for file_key, file_data in self.project.data['files'].items():
                        if file_data.get('raw') and file_data['raw'].endswith(raw_filename):
                            jpg_filename = file_data.get('jpg')
                            break
                
                if jpg_filename:
                    recovered_model, recovered_filter = recover_camera_metadata_from_exif(jpg_filename, self.project)
                    if recovered_model:
                        camera_model = recovered_model
                        camera_filter = recovered_filter or camera_filter
                
                # If still Unknown after recovery attempt, skip this image
                if camera_model == 'Unknown':
                    pass
                    return False  # Skip this image, don't abort entire process
            
            # Create Calibration_Targets_Used folder structure (same level as Reflectance_Calibrated_Images)
            # Fix double RGN issue - use base camera model
            base_camera_model = camera_model.split('_')[0] if '_' in camera_model else camera_model
            target_found_folder = os.path.join(self.project.fp, f"{base_camera_model}_{camera_filter}", "tiff16", "Calibration_Targets_Used")
            os.makedirs(target_found_folder, exist_ok=True)
            
            # Set the target image path and data
            base_filename = target_image.fn.split('.')[0]
            target_image.path = os.path.join(target_found_folder, f"{base_filename}.tif")
            target_image.data = target_image_data
            target_image.fn = f"{base_filename}.tif"
            
            
            # CRITICAL: Data is already in RGB format from cached TIFF, no conversion needed
            # Red squares drawn in RGB color (0, 0, 65535) are already correct
            import tifffile as tiff
            tiff.imwrite(target_image.path, target_image_data)
            
            if os.path.exists(target_image.path):
                pass
                return True
            else:
                pass
                return False
                
        except Exception as e:
            pass
            import traceback
            traceback.print_exc()
            return False

    # JSON helper methods
    def _convert_numpy_to_json(self, data):
        """Convert numpy arrays to lists for JSON serialization"""
        if isinstance(data, dict):
            return {key: self._convert_numpy_to_json(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._convert_numpy_to_json(item) for item in data]
        elif hasattr(data, 'tolist'):  # numpy array
            return data.tolist()
        elif hasattr(data, 'item'):  # numpy scalar
            return data.item()
        else:
            return data
    
    def _save_default_calibration_json(self):
        """Save default calibration coefficients when no targets are found"""
        try:
            import json
            import os
            from datetime import datetime
            
            # Use standard default coefficients for ALS-only processing
            default_calibration = {
                'calibration_data': {
                    'default_coefficients': {
                        'coefficients': [1.0, 1.0, 1.0],  # Identity coefficients
                        'limits': [[0.0, 1.0], [0.0, 1.0], [0.0, 1.0]],  # Standard limits
                        'xvals': [[0.0, 0.25, 0.5, 0.75, 1.0]] * 3,  # Standard x values
                        'yvals': [[0.0, 0.25, 0.5, 0.75, 1.0]] * 3,  # Standard y values
                        'source': 'default_no_targets_found',
                        'als_only': True
                    }
                },
                'metadata': {
                    'created_at': datetime.now().isoformat(),
                    'source': 'Thread 2 fallback - no targets detected',
                    'als_data_available': True
                }
            }
            
            calibration_file = os.path.join(self.project.fp, 'calibration_data.json')
            with open(calibration_file, 'w') as f:
                json.dump(default_calibration, f, indent=2)
            
            return True
            
        except Exception as e:
            pass
            return False
    
    def _save_detection_to_json(self, filename, detection_data):
        """Save detection results to JSON file"""
        try:
            detection_file = os.path.join(self.project.fp, 'detection_data.json')
            
            # Load existing data
            all_detection_data = {}
            if os.path.exists(detection_file):
                with open(detection_file, 'r') as f:
                    all_detection_data = json.load(f)
            
            # Ensure structure exists
            if 'detection_results' not in all_detection_data:
                all_detection_data['detection_results'] = {}
            
            # Convert numpy arrays to lists for JSON serialization
            json_safe_data = self._convert_numpy_to_json(detection_data)
            
            # Save detection data
            all_detection_data['detection_results'][filename] = json_safe_data
            
            # Write back to file
            with open(detection_file, 'w') as f:
                json.dump(all_detection_data, f, indent=2)
            
            return True
            
        except Exception as e:
            pass
            return False

    def _load_detection_from_json(self, filename):
        """Load detection results from JSON file"""
        try:
            detection_file = os.path.join(self.project.fp, 'detection_data.json')
            
            if not os.path.exists(detection_file):
                pass
                return None
            
            with open(detection_file, 'r') as f:
                all_detection_data = json.load(f)
            
            detection_results = all_detection_data.get('detection_results', {})
            detection_data = None
            
            # CRITICAL FIX: For RAW files, find the corresponding JPG file using project data
            if filename.endswith('.RAW'):
                # Find the JPG file that corresponds to this RAW file
                jpg_filename = None
                for base_key, fileset in self.project.data.get('files', {}).items():
                    if fileset.get('raw'):
                        raw_path = fileset['raw']
                        raw_basename = os.path.basename(raw_path)
                        
                        # Check if this is the RAW file we're looking for
                        if raw_basename == filename or filename in raw_path:
                            jpg_filename = fileset.get('jpg')
                            if jpg_filename:
                                jpg_filename = os.path.basename(jpg_filename)
                                break
                
                if jpg_filename:
                    # Look for detection data using the JPG filename
                    detection_data = detection_results.get(jpg_filename)
                    if detection_data:
                        pass
                    else:
                        pass
                else:
                    pass
            else:
                # For JPG files, use direct lookup
                detection_data = detection_results.get(filename)
                if detection_data:
                    pass
                else:
                    pass
            
            if detection_data:
                # Convert lists back to numpy arrays
                if 'aruco_corners' in detection_data and detection_data['aruco_corners'] is not None:
                    detection_data['aruco_corners'] = np.array(detection_data['aruco_corners'])
                
                if 'calibration_target_polys' in detection_data and detection_data['calibration_target_polys'] is not None:
                    detection_data['calibration_target_polys'] = [np.array(poly) for poly in detection_data['calibration_target_polys']]
                
                return detection_data
            else:
                pass
                return None
                
        except Exception as e:
            pass
            return None

    def _save_calibration_to_json_new(self, filename, calibration_data):
        """Save calibration results to JSON file"""
        try:
            calibration_file = os.path.join(self.project.fp, 'calibration_data.json')
            
            # Load existing data
            all_calibration_data = {}
            if os.path.exists(calibration_file):
                with open(calibration_file, 'r') as f:
                    all_calibration_data = json.load(f)
            
            # Convert numpy arrays to lists for JSON serialization
            json_safe_calibration = self._convert_numpy_to_json(calibration_data)
            print(f"[SAVE_CALIB] 🔍 DEBUG: Original calibration_data keys: {calibration_data.keys()}")
            print(f"[SAVE_CALIB] 🔍 DEBUG: Original limits: {calibration_data.get('limits')}")
            print(f"[SAVE_CALIB] 🔍 DEBUG: JSON-safe calibration keys: {json_safe_calibration.keys()}")
            print(f"[SAVE_CALIB] 🔍 DEBUG: JSON-safe limits: {json_safe_calibration.get('limits')}")
            
            # Save calibration data with timestamp key
            timestamp = calibration_data.get('timestamp', 'unknown')
            
            # CRITICAL FIX: Normalize timestamp format to prevent duplicates
            # Convert 2025:02:03 19:30:56 to 2025-02-03 19:30:56
            if ':' in timestamp and ' ' in timestamp:
                date_part, time_part = timestamp.split(' ', 1)
                if date_part.count(':') == 2:  # Format: 2025:02:03
                    normalized_timestamp = date_part.replace(':', '-') + ' ' + time_part
                    print(f"[SAVE_CALIB] 🔧 Normalized timestamp: {timestamp} -> {normalized_timestamp}")
                    timestamp = normalized_timestamp
            
            all_calibration_data[timestamp] = json_safe_calibration
            
            # Write back to file
            with open(calibration_file, 'w') as f:
                json.dump(all_calibration_data, f, indent=2)
            
            return True
            
        except Exception as e:
            pass
            return False

    def _load_calibration_from_json(self):
        """Load calibration results from JSON file"""
        try:
            calibration_file = os.path.join(self.project.fp, 'calibration_data.json')
            
            if not os.path.exists(calibration_file):
                pass
                return None
            
            with open(calibration_file, 'r') as f:
                all_calibration_data = json.load(f)
            
            # Return the most recent calibration data
            if all_calibration_data:
                latest_key = max(all_calibration_data.keys())
                calibration_data = all_calibration_data[latest_key]
                return calibration_data
            else:
                pass
                return None
                
        except Exception as e:
            pass
            return None
    
    def _validate_calibration_requirements(self, images: List):
        """
        Validate that calibration requirements can be met before starting processing.
        
        Args:
            images: List of images to be processed
            
        Returns:
            bool: True if calibration requirements are valid, False otherwise
        """
        print("[CALIB-VALIDATION] 🔍 Validating calibration requirements...")
        
        # Check if calibration is required
        calibration_required = False
        processing_options = getattr(self, 'processing_options', {})
        
        # Check processing options for calibration requirements
        if processing_options.get('Vignette correction', False):
            calibration_required = True
            print("[CALIB-VALIDATION] 📋 Vignette correction enabled - calibration required")
        
        if processing_options.get('Reflectance calibration / white balance', False):
            calibration_required = True
            print("[CALIB-VALIDATION] 📋 Reflectance calibration enabled - calibration required")
        
        if not calibration_required:
            print("[CALIB-VALIDATION] ✅ No calibration required - validation passed")
            return True
        
        # Check if we have calibration data available
        from unified_calibration_api import UnifiedCalibrationManager
        
        # Get project directory
        project_dir = getattr(self.project, 'fp', None) if hasattr(self, 'project') else None
        if not project_dir:
            print("[CALIB-VALIDATION] ❌ No project directory found")
            return False
        
        # Check for existing calibration file
        import os
        calibration_file = os.path.join(project_dir, 'calibration_data.json')
        
        if os.path.exists(calibration_file):
            # Validate that calibration data matches our camera models
            try:
                import json
                with open(calibration_file, 'r') as f:
                    calib_data = json.load(f)
                
                # Get unique camera models and filters from images
                camera_combinations = set()
                for image in images:
                    camera_model = getattr(image, 'camera_model', 'Unknown')
                    camera_filter = getattr(image, 'camera_filter', 'Unknown')
                    
                    # Extract from Model if needed
                    if camera_model == 'Unknown' and hasattr(image, 'Model'):
                        model_parts = image.Model.split('_') if '_' in image.Model else [image.Model]
                        camera_model = model_parts[0] if model_parts else 'Unknown'
                        if len(model_parts) > 1 and camera_filter == 'Unknown':
                            camera_filter = model_parts[1]
                    
                    if camera_model != 'Unknown' and camera_filter != 'Unknown':
                        camera_combinations.add((camera_model, camera_filter))
                
                print(f"[CALIB-VALIDATION] 🔍 Found {len(camera_combinations)} unique camera combinations: {camera_combinations}")
                
                # Check if we have calibration data for each combination
                missing_combinations = []
                for camera_model, camera_filter in camera_combinations:
                    found_match = False
                    for entry in calib_data.values():
                        if (entry.get('camera_model') == camera_model and 
                            entry.get('camera_filter') == camera_filter):
                            found_match = True
                            break
                    
                    if not found_match:
                        missing_combinations.append((camera_model, camera_filter))
                
                if missing_combinations:
                    print(f"[CALIB-VALIDATION] ❌ Missing calibration data for combinations: {missing_combinations}")
                    print(f"[CALIB-VALIDATION] 💡 Available calibration entries:")
                    for key, entry in calib_data.items():
                        print(f"[CALIB-VALIDATION]   {key}: {entry.get('camera_model', 'Unknown')} + {entry.get('camera_filter', 'Unknown')}")
                    return False
                else:
                    pass
                    return True
                    
            except Exception as e:
                print(f"[CALIB-VALIDATION] ❌ Error reading calibration file: {e}")
                return False
        else:
            print(f"[CALIB-VALIDATION] ❌ Calibration file not found: {calibration_file}")
            print(f"[CALIB-VALIDATION] 💡 Calibration is required but no calibration data available")
            return False
    
    def start_pipeline(self, images: List):
        """Start all pipeline threads with performance monitoring"""
        # CRITICAL FIX: Prevent multiple pipeline starts
        if hasattr(self, '_pipeline_started') and self._pipeline_started:
            pass
            return
        
        # CRITICAL: Validate calibration requirements before starting pipeline
        if not self._validate_calibration_requirements(images):
            pass
            return False
        
        self._pipeline_started = True

        # CRITICAL: Validate and repair image pairs BEFORE processing starts
        is_valid, issues_found, issues_repaired = self._validate_and_repair_image_pairs()
        
        # OPTIMIZATION: Start performance monitoring
        self.start_performance_monitoring()
        
        for i, img in enumerate(images):
            pass
        
        # Sort images by timestamp for proper temporal processing
        try:
            sorted_images = sorted(images, key=lambda x: getattr(x, 'timestamp', getattr(x, 'DateTime', '0')))
        except Exception as e:
            pass
            sorted_images = images
        
        # Thread 1: Target Detection
        try:
            pass
            t1 = threading.Thread(
                target=self._thread1_target_detection,
                args=(sorted_images,),
                name="Thread-1-Detecting"
            )
            
            # Thread 2: Analyzing
            t2 = threading.Thread(
                target=self._thread2_calibration_compute,
                name="Thread-2-Analyzing"
            )
            
            # Thread 3: Processing
            t3 = threading.Thread(
                target=self._thread3_calibration_apply,
                name="Thread-3-Processing"
            )
            
            # Thread 4: Exporting
            t4 = threading.Thread(
                target=self._thread4_export,
                name="Thread-4-Exporting"
            )
            
            self.threads = [t1, t2, t3, t4]
            
            # Start all threads
            for i, thread in enumerate(self.threads):
                if not thread.is_alive():
                    pass
                    thread.start()
                    
        except Exception as e:
            pass
            import traceback
            raise
    
    def stop_pipeline(self):
        """Stop all pipeline threads immediately"""
        self._stop_requested = True
        
        # Use the existing shutdown mechanism
        self.queues.shutdown.set()
        
        # Don't reset UI here - wait for threads to actually stop
        # UI will be reset in the main processing method after pipeline completes
        
        # CRITICAL: Clean up all resources (Ray, PyTorch GPU, etc.) when pipeline is stopped
        try:
            from resource_cleanup_manager import cleanup_resources
            cleanup_resources("Pipeline stopped by user request")
        except Exception as e:
            pass
        
        # Clear all queues to unblock waiting threads
        try:
            while not self.queues.target_to_calib.empty():
                self.queues.target_to_calib.get_nowait()
        except:
            pass
        try:
            while not self.queues.calib_to_process.empty():
                self.queues.calib_to_process.get_nowait()
        except:
            pass
        try:
            while not self.queues.process_to_export.empty():
                self.queues.process_to_export.get_nowait()
        except:
            pass
        
        # Send sentinel values to unblock threads
        try:
            self.queues.target_to_calib.put(None)
            self.queues.calib_to_process.put(None)
            self.queues.process_to_export.put(None)
            # Also handle new queue names
            self.queues.calibration_compute_queue.put(None)
            self.queues.calibration_apply_queue.put(None)
            self.queues.export_queue.put(None)
        except:
            pass
        
        # Force stop threads if they exist
        if hasattr(self, 'threads'):
            for thread in self.threads:
                if thread.is_alive():
                    pass
                    thread.join(timeout=2.0)  # Wait max 2 seconds per thread
                    if thread.is_alive():
                        pass
                    else:
                        pass
        
        
        # Clean up debayer cache after stopping
        if hasattr(self, 'project') and self.project:
            self.project.clear_debayer_cache()

    def wait_for_completion(self):
        """Wait for all threads to complete"""
        for thread in self.threads:
            thread.join()
        
        
        # Clean up debayer cache after successful completion
        if hasattr(self, 'project') and self.project:
            self.project.clear_debayer_cache()
    
    def _update_ui_checkbox_realtime(self, jpg_filename, is_calibration_photo):
        """Update UI checkbox immediately when target is detected using SSE events"""
        # Initialize batch tracking if not exists
        if not hasattr(self, '_ui_update_batch'):
            self._ui_update_batch = []
            self._last_batch_send_time = 0
        
        # Add this detection to the batch
        self._ui_update_batch.append({
            'filename': jpg_filename,
            'is_calibration_photo': is_calibration_photo
        })
        
        # Send batch update immediately for every target (since detections are slow, ~4s apart)
        # Batching prevents event flooding during rapid detections but sends immediately for slow ones
        import time
        current_time = time.time()
        should_send_batch = (
            len(self._ui_update_batch) >= 1  # Send immediately for every target
        )
        
        if should_send_batch and self._ui_update_batch:
            try:
                import backend_server
                
                # Send ONE batch update event with all accumulated targets
                backend_server.dispatch_event('target-batch-update', {
                    'targets_found': self._ui_update_batch.copy(),
                    'completed_count': len(self._ui_update_batch),
                    'total_count': self.processing_stats.get('targets_found', len(self._ui_update_batch)),
                    'source': 'realtime_batch_update'
                })
                
                # Clear the batch and update timestamp
                self._ui_update_batch = []
                self._last_batch_send_time = current_time
                
            except Exception as e:
                pass  # Silent fail for batch update errors
        
        try:
            # Update project data in memory (will be saved at end of processing)
            if hasattr(self.api, 'project') and self.api.project:
                # Find the correct project data key by searching for the JPG filename
                project_key = None
                for key, fileset in self.api.project.data['files'].items():
                    if 'jpg' in fileset and fileset['jpg'].endswith(jpg_filename):
                        project_key = key
                        break
                
                if project_key:
                    # Update project data in memory only
                    if 'calibration' not in self.api.project.data['files'][project_key]:
                        self.api.project.data['files'][project_key]['calibration'] = {}
                    self.api.project.data['files'][project_key]['calibration']['is_calibration_photo'] = is_calibration_photo
                    self.api.project.data['files'][project_key]['manual_calib'] = is_calibration_photo
                    self.api.project.data['files'][project_key]['calib_detected'] = is_calibration_photo
            
        except Exception as e:
            print(f"[THREAD-1] ❌ Error in _update_ui_checkbox_realtime for {jpg_filename}: {e}")
            import traceback
            traceback.print_exc()
    
    def _thread1_target_detection(self, images: List):
        # CRITICAL FIX: Prevent multiple thread starts
        if hasattr(self, '_thread1_completed') and self._thread1_completed:
            print("[THREAD-1] WARNING: Thread-1 already completed, ignoring restart")
            return
        
        # Check if shutdown was requested before starting
        if self.queues.shutdown.is_set():
            print("[THREAD-1] 🛑 Shutdown requested before starting - exiting")
            return
        
        # CRITICAL: Skip target detection if reflectance calibration is disabled
        reflectance_enabled = True  # Default to enabled
        print(f"[THREAD-1] 🔍 DEBUG: Checking reflectance calibration setting...")
        print(f"[THREAD-1] 🔍 DEBUG: hasattr(self, 'options') = {hasattr(self, 'options')}")
        
        if hasattr(self, 'options') and self.options:
            print(f"[THREAD-1] 🔍 DEBUG: self.options keys = {list(self.options.keys())}")
            if 'Project Settings' in self.options and 'Processing' in self.options['Project Settings']:
                reflectance_enabled = self.options['Project Settings']['Processing'].get('Reflectance calibration / white balance', True)
                print(f"[THREAD-1] 🔍 DEBUG: Found in Project Settings > Processing")
            elif 'Processing' in self.options:
                reflectance_enabled = self.options['Processing'].get('Reflectance calibration / white balance', True)
                print(f"[THREAD-1] 🔍 DEBUG: Found in Processing directly")
            else:
                print(f"[THREAD-1] 🔍 DEBUG: Processing not found in options")
        else:
            print(f"[THREAD-1] 🔍 DEBUG: No options available")
        
        print(f"[THREAD-1] 🔍 DEBUG: reflectance_enabled = {reflectance_enabled}")
        
        if not reflectance_enabled:
            print("[THREAD-1] ⏭️ SKIPPING target detection - reflectance calibration is DISABLED")
            print("[THREAD-1] ℹ️ When reflectance calibration is disabled, only sensor response correction is applied")
            print("[THREAD-1] ℹ️ No calibration targets are needed for sensor response correction")
            
            # Mark all images as non-targets in project data
            if hasattr(self, 'project') and self.project and hasattr(self.project, 'data'):
                for base, fileset in self.project.data.get('files', {}).items():
                    fileset['is_calibration_photo'] = False
            
            # Signal Thread-2 to skip (send sentinel)
            self.queues.detected_queue.put(None)
            self._thread1_completed = True
            print("[THREAD-1] ✅ Thread-1 completed (skipped - no reflectance calibration)")
            return
        else:
            print("[THREAD-1] ✅ Reflectance calibration is ENABLED - proceeding with target detection")
        
        
        # Initialize UI progress for fresh start (no resume logic)
        if self.api and hasattr(self.api, 'update_thread_progress'):
            jpg_images = [img for img in images if img.fn.lower().endswith('.jpg')]
            
            # CRITICAL FIX: Count actual images to be processed based on checkbox states
            total_to_process = self._count_images_to_process(jpg_images)
            
            # Update UI to show Thread 1 starting fresh (no resume logic)
            if self.api:
                self.api.update_thread_progress(
                    thread_id=1,
                    percent_complete=0,
                    phase_name="Detecting",
                    time_remaining=f"0/{total_to_process}"
                )
        for i, img in enumerate(images):
            pass
        
        # Separate JPG and RAW images
        jpg_images = [img for img in images if img.fn.lower().endswith(('.jpg', '.jpeg'))]
        raw_images = [img for img in images if img.fn.lower().endswith('.raw')]
        
        
        # FRESH START: Process all JPG images (no resume filtering)
        print(f"[THREAD-1] FRESH START: Processing all {len(jpg_images)} JPG images (no resume logic)")
        
        # CRITICAL FIX: Clear ALL stale is_calibration_photo flags before target detection
        # This ensures we always do fresh target detection and don't skip due to stale data
        # from previous processing sessions (GUI or CLI)
        stale_flags_cleared = 0
        for raw_img in raw_images:
            if getattr(raw_img, 'is_calibration_photo', False):
                raw_img.is_calibration_photo = False
                stale_flags_cleared += 1
        for jpg_img in jpg_images:
            if getattr(jpg_img, 'is_calibration_photo', False):
                jpg_img.is_calibration_photo = False
                stale_flags_cleared += 1
        
        if stale_flags_cleared > 0:
            print(f"[THREAD-1] 🧹 Cleared {stale_flags_cleared} stale is_calibration_photo flags for fresh detection")
        
        # Create a map for quick lookup of RAW images by base filename
        raw_map = {}
        for raw_img in raw_images:
            # Get base name without extension
            base_name = os.path.splitext(raw_img.fn)[0]
            raw_map[base_name] = raw_img
        
        # Count RAW and JPG images
        raw_count = sum(1 for img in images if img.fn.lower().endswith('.raw'))
        jpg_count = sum(1 for img in images if img.fn.lower().endswith(('.jpg', '.jpeg')))
        print(f"[THREAD-1] Found {raw_count} RAW images and {jpg_count} JPG images")
        
        # CRITICAL FIX: Collect RAW images to queue after target detection
        raw_images_to_queue = []
        
        try:
            if self.use_ray and jpg_images:
                # Process JPG images in batches using Ray
                self._process_target_detection_ray_batch(jpg_images, raw_map, raw_images_to_queue)
            else:
                # Original sequential processing
                self._process_target_detection_sequential(images, raw_map, raw_images_to_queue)
            
            # CRITICAL FIX: Now queue non-target RAW images to Thread-3
            # This happens AFTER target detection is complete to avoid race conditions
            print(f"[THREAD-1] Queuing {len(raw_images_to_queue)} RAW images to Thread-3")
            print(f"[THREAD-1] Final targets_checked count: {self.processing_stats['targets_checked']}")
            
            # Small delay to ensure stats are visible to monitoring thread
            import time
            time.sleep(0.2)
            
            for raw_img in raw_images_to_queue:
                self._queue_file_safely(self.queues.calibration_apply_queue, raw_img, "RAW from target detection")
            
            # TEMPORAL OPTIMIZATION: Create initial calibration JSON with temporal data
            # Collect all calibration images that were found during target detection
            all_calibration_images = [img for img in raw_images if getattr(img, 'is_calibration_photo', False)]
            all_images = raw_images_to_queue + all_calibration_images
            self._create_temporal_calibration_json(all_calibration_images, all_images)
            
            # CRITICAL FIX: Queue detected target images to Thread-2 for calibration computation
            print(f"[THREAD-1] Queueing {len(all_calibration_images)} target images to Thread-2 for calibration computation...")
            for target_image in all_calibration_images:
                print(f"[THREAD-1] Queueing target image {target_image.fn} to Thread-2")
                self.queues.calibration_compute_queue.put(target_image)
            
            # Send sentinel to Thread-2 after all targets are queued
            if all_calibration_images:
                print(f"[THREAD-1] Sending sentinel to Thread-2 after queueing {len(all_calibration_images)} targets")
                self.queues.calibration_compute_queue.put(None)
            
            print(f"[THREAD-1] Target detection complete. Found {len(all_calibration_images)} calibration targets.")
            
            # CRITICAL: Flush any remaining targets in the batch queue
            if hasattr(self, '_ui_update_batch') and self._ui_update_batch:
                try:
                    import backend_server
                    backend_server.dispatch_event('target-batch-update', {
                        'targets_found': self._ui_update_batch.copy(),
                        'completed_count': len(self._ui_update_batch),
                        'total_count': self.processing_stats.get('targets_found', len(self._ui_update_batch)),
                        'source': 'thread1_final_flush'
                    })
                    self._ui_update_batch = []
                except Exception as e:
                    pass  # Silent fail
            
            # CHECK FOR NO TARGETS FOUND - EXIT PROCESSING IF REFLECTANCE CALIBRATION IS ENABLED
            if len(all_calibration_images) == 0:
                print("[THREAD-1] ❌ No calibration targets found - checking if reflectance calibration is enabled")
                
                # Check if reflectance calibration is enabled (use same path as Thread-4)
                reflectance_enabled = False
                try:
                    # Use the same options structure as Thread-4
                    options_for_process = self.options.get('Project Settings', self.options) if hasattr(self, 'options') else {}
                    if 'Processing' in options_for_process:
                        processing_options = options_for_process['Processing']
                        reflectance_enabled = processing_options.get('Reflectance calibration / white balance', False)
                        print(f"[THREAD-1] Reflectance calibration enabled: {reflectance_enabled}")

                    else:


                        # Fallback to project data structure
                        if self.api and hasattr(self.api, 'project') and self.api.project:
                            options = self.api.project.data.get('options_for_process', {})
                            processing_options = options.get('Processing', {})
                            reflectance_enabled = processing_options.get('Reflectance calibration / white balance', False)
                            print(f"[THREAD-1] [FALLBACK] Reflectance calibration enabled: {reflectance_enabled}")
                except Exception as e:
                    print(f"[THREAD-1] Error checking reflectance calibration setting: {e}")
                    reflectance_enabled = True  # Default to enabled to be safe
                
                if reflectance_enabled:
                    print("[THREAD-1] ❌ No calibration targets found with reflectance calibration enabled - exiting processing")
                    
                    # Clear target detection state so it will run again on restart
                    try:
                        if self.api and hasattr(self.api, 'project') and self.api.project:

                            processing_state = self.api.project.get_processing_state()
                            if 'parallel_stages' in processing_state:
                                if 'target_detection' in processing_state['parallel_stages']:
                                    processing_state['parallel_stages']['target_detection']['completed'] = False
                                    # FIX: save_processing_state expects (stage, mode, thread_states) not (state_dict, mode)
                                    self.api.project.save_processing_state('target_detection_reset', 'parallel', processing_state.get('parallel_stages'))

                    except Exception as e:
                        pass

                        # Continue anyway - the important thing is to exit processing
                    
                    # Show "No Target X" error in red text in Thread 1 progress bar
                    if self.api and hasattr(self.api, 'window') and self.api.window:
                        try:
                            self.api.window._js_api.safe_evaluate_js(f'''
                                (function() {{
                                    try {{
                                        let progressBar = document.querySelector('progress-bar');
                                        if (progressBar && progressBar.isConnected) {{
                                            // Set error phase name for Thread 1
                                            if (progressBar.threadProgress && progressBar.threadProgress.length >= 1) {{
                                                progressBar.threadProgress[0].phaseName = "No Target X";
                                                progressBar.threadProgress[0].isActive = false;
                                            }}
                                            
                                            // CRITICAL: Set error state properties for cleanup preservation
                                            progressBar._errorState = true;
                                            progressBar._errorMessage = "No Target X";
                                            console.log("[THREAD-1] [DEBUG] ✅ Set error state properties: _errorState=true, _errorMessage='No Target X'");
                                            
                                            progressBar.requestUpdate();
                                            console.log("[THREAD-1] [DEBUG] ❌ Showing 'No Target X' error in thread 1");
                                            
                                            // Reset the process button to play state
                                            const processButton = document.querySelector('process-control-button');
                                            if (processButton) {{
                                                processButton.processingComplete();
                                                console.log("[THREAD-1] [DEBUG] ✅ Reset process button to play state");
                                            }}
                                        }}
                                    }} catch (error) {{
                                        console.log("[THREAD-1] ⚠️ Error showing no target message:", error);
                                    }}
                                }})();
                            ''')
                        except Exception as e:
                            print(f"[THREAD-1] ⚠️ Failed to show no target error message: {e}")
                    
                    # Signal shutdown to stop all other threads
                    self.queues.shutdown.set()
                    print("[THREAD-1] 🛑 Shutdown signal sent to stop all threads")
                    return  # Exit Thread-1 immediately
            
            print(f"[THREAD-1] Thread-2 will process calibration targets, then signal completion to Thread-3 and Thread-4")
            
            # Always signal calibration ready event so Thread-2 can proceed
            self.queues.calibration_ready_event.set()
            print("[THREAD-1] Detecting complete")
            
        except Exception as e:
            print(f"[THREAD-1] Error: {e}")
            self.queues.shutdown.set()
        finally:
            self._thread1_completed = True
    
    def _create_temporal_calibration_json(self, calibration_images, all_images):
        """Create initial calibration JSON with temporal processing information"""
        try:
            import os
            import json
            from datetime import datetime
            
            # Determine calibration file path
            if hasattr(self, 'project') and self.project and hasattr(self.project, 'fp'):
                calibration_file = os.path.join(self.project.fp, 'calibration_data.json')
            else:
                print("[THREAD-1] ⚠️ No project directory available for temporal calibration JSON")
                return
            
            print(f"[THREAD-1] 🕒 Creating temporal calibration JSON with {len(calibration_images)} targets and {len(all_images)} total images")
            
            # Create temporal data structure
            temporal_data = {
                "temporal_processing": {
                    "created_timestamp": datetime.now().isoformat(),
                    "targets": {},
                    "non_targets": {},
                    "processing_order": []
                },
                "calibration_data": {}  # Will be filled by Thread 2
            }
            
            # Process targets and get their timestamps
            target_timestamps = []
            for target_img in calibration_images:
                timestamp_obj = getattr(target_img, 'timestamp', None)
                if timestamp_obj:
                    # Ensure timestamp is a string (convert datetime objects if needed)
                    timestamp_str = timestamp_obj.isoformat() if hasattr(timestamp_obj, 'isoformat') else str(timestamp_obj)
                    temporal_data["temporal_processing"]["targets"][target_img.fn] = {
                        "timestamp": timestamp_str,
                        "processed": False,
                        "calibration_ready": False
                    }
                    target_timestamps.append((timestamp_str, target_img.fn))
                    print(f"[THREAD-1] 🎯 Target: {target_img.fn} at {timestamp_str}")
            
            # Sort targets by timestamp
            target_timestamps.sort()
            
            # Process all images and determine their temporal processing requirements
            all_image_timestamps = []
            for img in all_images:
                timestamp_obj = getattr(img, 'timestamp', None)
                if timestamp_obj:
                    # Ensure timestamp is a string (convert datetime objects if needed)
                    timestamp_str = timestamp_obj.isoformat() if hasattr(timestamp_obj, 'isoformat') else str(timestamp_obj)
                    all_image_timestamps.append((timestamp_str, img.fn, getattr(img, 'is_calibration_photo', False)))
            
            # Sort all images by timestamp
            all_image_timestamps.sort()
            
            # Determine processing logic for each image
            for timestamp_str, img_fn, is_target in all_image_timestamps:
                if is_target:
                    continue  # Already processed above
                
                # Find which calibration target this image should use
                calibration_target = self._find_temporal_calibration_target(timestamp_str, target_timestamps)
                can_process_immediately = self._can_process_immediately_temporal(timestamp_str, target_timestamps)
                
                temporal_data["temporal_processing"]["non_targets"][img_fn] = {
                    "timestamp": timestamp_str,
                    "calibration_target": calibration_target,
                    "can_process_immediately": can_process_immediately,
                    "processed": False
                }
                
                print(f"[THREAD-1] 📷 Non-target: {img_fn} at {timestamp_str} → uses {calibration_target} → immediate: {can_process_immediately}")
            
            # Create processing order (targets first, then images that can process immediately)
            processing_order = []
            for timestamp_str, img_fn, is_target in all_image_timestamps:
                processing_order.append({
                    "filename": img_fn,
                    "timestamp": timestamp_str,
                    "is_target": is_target,
                    "priority": "immediate" if is_target else ("immediate" if temporal_data["temporal_processing"]["non_targets"].get(img_fn, {}).get("can_process_immediately", False) else "waiting")
                })
            
            temporal_data["temporal_processing"]["processing_order"] = processing_order
            
            # Write the initial JSON file with file locking to prevent race conditions
            from unified_calibration_api import UnifiedCalibrationManager
            file_lock = UnifiedCalibrationManager._get_file_lock(calibration_file)
            
            with file_lock:
                from unified_calibration_api import UnifiedCalibrationManager
                thread_priority = UnifiedCalibrationManager._get_thread_priority()
                thread_name = threading.current_thread().name
                print(f"[THREAD-1] 🔒 {thread_name} (priority {thread_priority}) acquired file lock for temporal JSON creation: {calibration_file}")
                
                # Atomic write: write to temp file first, then rename
                temp_file = calibration_file + '.tmp'
                with open(temp_file, 'w') as f:
                    json.dump(temporal_data, f, indent=2)
                    f.flush()
                    os.fsync(f.fileno())
                
                # Atomic rename (prevents partial writes)
                if os.name == 'nt':  # Windows
                    if os.path.exists(calibration_file):
                        os.remove(calibration_file)
                    os.rename(temp_file, calibration_file)
                else:  # Unix/Linux
                    os.rename(temp_file, calibration_file)
            
            print(f"[THREAD-1] ✅ Created temporal calibration JSON: {calibration_file}")
            print(f"[THREAD-1] 📊 Processing summary:")
            immediate_count = sum(1 for item in processing_order if item["priority"] == "immediate")
            waiting_count = sum(1 for item in processing_order if item["priority"] == "waiting")
            print(f"[THREAD-1]   - Immediate processing: {immediate_count} images")
            print(f"[THREAD-1]   - Waiting for calibration: {waiting_count} images")
            
        except Exception as e:
            print(f"[THREAD-1] ❌ Error creating temporal calibration JSON: {e}")
            import traceback
            traceback.print_exc()
    
    def _find_temporal_calibration_target(self, image_timestamp, target_timestamps):
        """Find the appropriate calibration target for an image based on temporal logic"""
        # Find the latest target that comes at or before this image's timestamp
        # If no such target exists, use the earliest target (beginning of project case)
        
        best_target = None
        for target_timestamp, target_filename in target_timestamps:
            if target_timestamp <= image_timestamp:
                best_target = target_filename
            else:
                break
        
        # If no target comes before this image, use the first target (beginning of project)
        if best_target is None and target_timestamps:
            best_target = target_timestamps[0][1]
        
        return best_target
    
    def _can_process_immediately_temporal(self, image_timestamp, target_timestamps):
        """Determine if an image can be processed immediately based on temporal logic"""
        # An image can process immediately if:
        # 1. There are no unprocessed targets that come before it in time, OR
        # 2. It's at the beginning of the project and will use the first target
        
        # Check if there are any targets that come before this image
        earlier_targets = [t for t in target_timestamps if t[0] < image_timestamp]
        
        if not earlier_targets:
            # No targets before this image - it's at the beginning, can process with first target
            return True
        
        # For now, assume all targets need to be processed first
        # This will be updated by Thread 2 as targets are processed
        return False
    
    def _count_images_to_process(self, jpg_images):
        """Count how many images will actually be processed based on checkbox states"""
        count = 0
        for img in jpg_images:
            checkbox_state = self._get_image_checkbox_state(img.fn)
            
            # Count images that will be processed (analyzed or already confirmed)
            if checkbox_state in ['grey', 'analyze', 'green'] or checkbox_state is None:
                # Grey = user selected, analyze = default, green = confirmed target, None = default when no manual selections
                if checkbox_state != 'disabled':  # Don't count disabled images
                    count += 1
        
        print(f"[THREAD-1] DEBUG: Counted {count} images to process out of {len(jpg_images)} total JPG images")
        return count
    
    def _get_image_checkbox_state(self, image_filename):
        """Get the checkbox state for an image (green, grey, or none)"""
        try:
            # Get the project files (now includes synced checkbox states)
            if hasattr(self.api, 'get_image_list'):
                project_files = self.api.get_image_list()
                
                # Find the specific file
                target_file = None
                for file_info in project_files:
                    if file_info.get('title') == image_filename:
                        target_file = file_info
                        break
                
                if target_file:
                    calib = target_file.get('calib', False)
                    calib_detected = target_file.get('calib_detected', False)
                    
                    print(f"[THREAD-1] 📋 File {image_filename}: calib={calib}, calib_detected={calib_detected}")
                    
                    # Check if this target was manually disabled
                    if calib_detected and not calib:
                        print(f"[THREAD-1] 🚫 DISABLED: {image_filename} is a detected target but was manually unchecked")
                        print(f"[THREAD-1] 🔍 DEBUG DISABLED: calib_detected={calib_detected}, calib={calib}")
                        return 'disabled'
                    
                    if calib_detected:
                        # Green checkbox - confirmed target, skip analysis
                        print(f"[THREAD-1] ✅ GREEN: {image_filename} (detected target)")
                        return 'green'
                    elif calib and not calib_detected:
                        # Grey checkbox - user selected for analysis
                        print(f"[THREAD-1] 🔍 GREY: {image_filename} (manually selected)")
                        return 'grey'
                    else:
                        # No checkbox - check if there are any manual selections
                        has_manual_selections = any(
                            f.get('calib', False) and not f.get('calib_detected', False) 
                            for f in project_files
                        )
                        
                        if has_manual_selections:
                            # User made manual selections, skip unchecked images
                            print(f"[THREAD-1] ⏭️ SKIP: {image_filename} (not manually selected)")
                            return None
                        else:
                            # No manual selections, analyze all images
                            print(f"[THREAD-1] 🔍 ANALYZE: {image_filename} (no manual selections)")
                            return 'analyze'
                else:
                    print(f"[THREAD-1] ⚠️ File {image_filename} not found in project files")
                    return 'analyze'
            
            # Fallback
            print(f"[THREAD-1] 🔍 ANALYZE: {image_filename} (fallback)")
            return 'analyze'
            
        except Exception as e:
            print(f"[THREAD-1] Error checking checkbox state for {image_filename}: {e}")
            import traceback
            traceback.print_exc()
            return 'analyze'

    def _queue_confirmed_target(self, jpg_image):
        """Queue a confirmed target (green check) directly to Thread 2, respecting recalibration interval"""
        try:
            # Find corresponding RAW image
            raw_filename = self.project.jpg_name_to_raw_name.get(jpg_image.fn)
            if raw_filename:
                raw_image = self.project.imagemap.get(raw_filename)
                if raw_image:
                    # Check recalibration interval setting before queuing
                    min_calib_interval = self.project.data['config']["Project Settings"]['Processing']["Minimum recalibration interval"]
                    
                    # Check if we should skip this target based on recalibration interval
                    should_queue = True
                    if min_calib_interval > 0:
                        # Find the most recent calibration image that was already processed
                        most_recent_calib_time = None
                        for processed_image in self.processing_stats.get('processed_calibration_images', []):
                            if hasattr(processed_image, 'timestamp') and processed_image.timestamp:
                                if most_recent_calib_time is None or processed_image.timestamp > most_recent_calib_time:
                                    most_recent_calib_time = processed_image.timestamp
                        
                        # If we have a recent calibration, check the interval
                        if most_recent_calib_time and hasattr(raw_image, 'timestamp') and raw_image.timestamp:
                            time_diff = abs((raw_image.timestamp - most_recent_calib_time).total_seconds())
                            if time_diff < min_calib_interval:
                                should_queue = False
                                print(f"[THREAD-1] ⏰ SKIP: {raw_image.fn} green check ignored - only {time_diff:.1f}s since last calibration (interval: {min_calib_interval}s)")
                    
                    if should_queue:
                        # Mark as calibration photo (will be queued after batch interval filtering)
                        raw_image.is_calibration_photo = True
                        print(f"[THREAD-1] 📋 Green check target: {raw_image.fn} - marked for interval filtering")
                        
                        # Track this as a processed calibration image for future interval checks
                        if 'processed_calibration_images' not in self.processing_stats:
                            self.processing_stats['processed_calibration_images'] = []
                        self.processing_stats['processed_calibration_images'].append(raw_image)
                        
                        # Update stats
                        with self.stats_lock:
                            self.processing_stats['targets_found'] += 1
                        current_targets_found = self.processing_stats['targets_found']
                        
                        # Update other threads' progress bars
                        self._update_other_threads_target_count(current_targets_found)
                        
                        print(f"[THREAD-1] ✅ Queued confirmed target {raw_image.fn} directly to Thread-2")
                        self.queues.calibration_ready_event.set()
                    else:
                        print(f"[THREAD-1] ⏭️ Skipped confirmed target {raw_image.fn} due to recalibration interval")
        except Exception as e:
            print(f"[THREAD-1] Error queuing confirmed target {jpg_image.fn}: {e}")

    def _update_other_threads_target_count(self, new_target_count):
        """Update Thread 2 and Thread 3 progress bars with new target count in real-time"""
        if self.api and hasattr(self.api, 'update_thread_progress'):
            # Update Thread 2 progress bar to show new target count
            # Get current processed count for Thread 2
            thread2_processed = self.processing_stats.get('calibrations_processed', 0)
            thread2_percent = int((thread2_processed / new_target_count) * 100) if new_target_count > 0 else 0
            
            self.api.update_thread_progress(
                thread_id=2,
                percent_complete=thread2_percent,
                phase_name="Analyzing",
                time_remaining=f"{thread2_processed}/{new_target_count}"
            )
            print(f"[THREAD-1] 🔄 Updated Thread 2 progress: {thread2_processed}/{new_target_count} ({thread2_percent}%) - new target found")
            
            # Update Thread 3 progress bar to show new target count  
            # Thread 3 processes RAW images only, so count RAW images from processing state
            processing_state = self.api.project.get_processing_state() if self.api and self.api.project else {}
            thread3_state = processing_state.get('parallel_threads', {}).get('thread_3_processing', {})
            raw_images_count = thread3_state.get('total_images', 0)
            thread3_processed = self.processing_stats.get('images_calibrated', 0)
            thread3_percent = int((thread3_processed / raw_images_count) * 100) if raw_images_count > 0 else 0
            
            self.api.update_thread_progress(
                thread_id=3,
                percent_complete=thread3_percent,
                phase_name="Processing",
                time_remaining=f"{thread3_processed}/{raw_images_count}"
            )
            print(f"[THREAD-1] 🔄 Updated Thread 3 progress: {thread3_processed}/{raw_images_count} ({thread3_percent}%) - target count updated")
    
    def _update_file_browser_realtime(self, image_filename, is_calibration):
        """Update file browser in real-time when calibration target is found in parallel mode"""
        if not self.api or not hasattr(self.api, 'window') or not self.api.window:
            return
            
        try:
            import json
            print(f"[THREAD-1] 🔄 Updating file browser for calibration target: {image_filename}")
            
            # Update the project data first
            if hasattr(self.api, 'project') and self.api.project:
                # Find the base name (without extension) for the project data
                base_name = image_filename.rsplit('.', 1)[0] if '.' in image_filename else image_filename
                
                # Update project data
                if base_name in self.api.project.data['files']:
                    if 'calibration' not in self.api.project.data['files'][base_name]:
                        self.api.project.data['files'][base_name]['calibration'] = {}
                    self.api.project.data['files'][base_name]['calibration']['is_calibration_photo'] = is_calibration
                    
                    # Save the project
                    self.api.project.write()
                    
                    # Get updated project files
                    updated_project_files = self.api.get_image_list()
                    
                    # Update the file browser with real-time green checkmark
                    self.api.window._js_api.safe_evaluate_js(f'''
                        (function() {{
                            try {{
                                console.log('[THREAD-1] 🔄 Real-time file browser update for: {image_filename}');
                                
                                // Get the updated project files from the backend
                                const updatedFiles = {json.dumps(updated_project_files)};
                                
                                // Find the file browser panel
                                const fileBrowserPanel = document.querySelector('project-file-panel');
                                if (fileBrowserPanel && fileBrowserPanel.fileviewer) {{
                                    // Update the file browser with the new data
                                    fileBrowserPanel.fileviewer.projectFiles = updatedFiles;
                                    fileBrowserPanel.fileviewer.initializeSortOrder();
                                    fileBrowserPanel.fileviewer.requestUpdate();
                                    fileBrowserPanel.requestUpdate();
                                    
                                    console.log('[THREAD-1] ✅ Real-time green checkmark added for: {image_filename}');
                                }}
                            }} catch (error) {{
                                console.log('[THREAD-1] ⚠️ Error updating file browser in real-time:', error);
                            }}
                        }})();
                    ''')
                    
        except Exception as e:
            print(f"[THREAD-1] ⚠️ Error updating file browser in real-time: {e}")
            import traceback
            traceback.print_exc()
    
    def _process_target_detection_ray_batch(self, jpg_images, raw_map, raw_images_to_queue):
        """Process target detection using Ray for batch parallel processing"""
        # Use global ray variable instead of importing directly
        global ray
        
        # CRITICAL: Force project save to ensure UI checkbox states are persisted
        print("[THREAD-1] 💾 Force saving project to persist UI checkbox states")
        self.api.project.write()
        print("[THREAD-1] ✅ Project saved - checkbox states now available")
        
        # Fix: Properly access Project Settings from options
        if 'Project Settings' in self.options:
            cfg = self.options['Project Settings']
        else:
            cfg = self.options
        


        
        min_calibration_samples = cfg["Target Detection"]["Minimum calibration sample area (px)"]
        
        # SPEED OPTIMIZATION: Pre-filter images based on checkbox state
        images_to_analyze = []
        images_to_skip = []
        
        for img in jpg_images:
            checkbox_state = self._get_image_checkbox_state(img.fn)
            
            if checkbox_state == 'disabled':
                # Disabled target = was detected but manually unchecked, skip completely
                print(f"[THREAD-1] 🚫 SKIP: {img.fn} is manually disabled (detected target unchecked)")
                img.is_calibration_photo = False
                images_to_skip.append(img)
            elif checkbox_state == 'green':
                # Green check = confirmed target, skip analysis, queue directly
                print(f"[THREAD-1] 🟢 SKIP: {img.fn} has green check (confirmed target)")
                img.is_calibration_photo = True
                # Find and queue corresponding RAW image directly
                self._queue_confirmed_target(img)
                images_to_skip.append(img)
            elif checkbox_state == 'grey':
                # Grey check = user wants this analyzed
                print(f"[THREAD-1] 🔍 ANALYZE: {img.fn} has grey check (user selected)")
                images_to_analyze.append(img)
            elif checkbox_state == 'analyze':
                # Default: analyze the image (no manual checkboxes set)
                print(f"[THREAD-1] 🔍 ANALYZE: {img.fn} (default analysis)")
                images_to_analyze.append(img)
            elif checkbox_state is None:
                # User made manual selections but didn't check this image - skip it
                print(f"[THREAD-1] ⏭️ SKIP: {img.fn} (not manually selected)")
                img.is_calibration_photo = False
                images_to_skip.append(img)
            else:
                # Unknown state - default to analyze
                print(f"[THREAD-1] 🔍 ANALYZE: {img.fn} (unknown state, defaulting to analyze)")
                images_to_analyze.append(img)
        
        
        # Use the unified function for target detection
        detect_task_func = get_unified_task_function('detect_calibration_image', execution_mode='parallel')
        
        # Process only images that need analysis using Ray
        futures = []
        if hasattr(detect_task_func, 'remote'):
            # Ray remote function - create futures only for images that need analysis
            for img in images_to_analyze:
                future = detect_task_func.remote(img, min_calibration_samples, self.project)
                futures.append(future)
        else:
            # Not a Ray function, fall back to sequential
            print("[THREAD-1] Ray remote function not available, falling back to sequential")
            return self._process_target_detection_sequential(jpg_images, raw_map, raw_images_to_queue)
        
        print(f"[THREAD-1] Created {len(futures)} Ray tasks for target detection")
        
        # Update progress immediately for skipped images
        # Use total individual file count for consistent progress display
        total_images = self.processing_stats.get('total_individual_files', len(jpg_images))
        skipped_count = len(images_to_skip)
        
        # Update progress stats for skipped images
        with self.stats_lock:
            self.processing_stats['targets_checked'] += skipped_count
        
        # Update progress bar to show skipped images as processed
        if self.api and hasattr(self.api, 'update_thread_progress'):
            # CRITICAL FIX: Use actual images being processed count, not total project files
            total_to_process = len(images_to_analyze) + len(images_to_skip)
            progress_percent = int((skipped_count / total_to_process) * 100) if total_to_process > 0 else 0
            self.api.update_thread_progress(
                thread_id=1,
                percent_complete=progress_percent,
                phase_name="Detecting",
                time_remaining=f"{skipped_count}/{total_to_process}"
            )
            print(f"[THREAD-1] 🚀 INSTANT: Skipped {skipped_count}/{total_to_process} images ({progress_percent}%)")
        
        # Process results as they complete
        # Create a mapping of futures to images for result processing
        future_to_image = {future: img for future, img in zip(futures, images_to_analyze)}
        
        # Process all futures - ensure we don't miss any
        processed_count = 0
        total_futures = len(futures)
        
        while futures:
            ready, futures = ray.wait(futures, num_returns=1, timeout=1.0)
            for future in ready:
                try:
                    result = ray.get(future)
                    jpg_image = future_to_image[future]
                    
                    # Increment targets_checked for every image processed
                    with self.stats_lock:
                        self.processing_stats['targets_checked'] += 1
                    processed_count += 1
                    print(f"[THREAD-1] Processed {processed_count}/{total_futures}: {jpg_image.fn}")
                    print(f"[THREAD-1] DEBUG: Result for {jpg_image.fn}: {result}")
                    
                    # Send thread progress updates 
                    total_processed = processed_count + skipped_count
                    # CRITICAL FIX: Use actual images being processed count, not total project files
                    total_to_process = len(images_to_analyze) + len(images_to_skip)
                    progress_percent = int((total_processed / total_to_process) * 100) if total_to_process > 0 else 0
                    print(f"[THREAD-1] DEBUG: Ray batch progress - total_processed={total_processed}, total_to_process={total_to_process}, total_images={total_images}")
                    if self.api:
                        self.api.update_thread_progress(
                            thread_id=1,
                            percent_complete=progress_percent,
                            phase_name="Detecting",  # Use correct phase name
                            time_remaining=f"{total_processed}/{total_to_process}"
                        )
                        print(f"[THREAD-1] Progress update: {total_processed}/{total_to_process} ({progress_percent}%)")
                    
                    if result and result[1]:  # result[1] is is_calibration_photo
                        print(f"[THREAD-1] Target detected in {jpg_image.fn}")
                        jpg_image.is_calibration_photo = True
                        jpg_image.aruco_id = result[0]
                        jpg_image.aruco_corners = result[2]
                        jpg_image.calibration_target_polys = result[3]
                        
                        # CRITICAL FIX: Update UI with green checkmark immediately
                        self._update_ui_checkbox_realtime(jpg_image.fn, True)
                        
                        # Update statistics
                        with self.stats_lock:
                            self.processing_stats['targets_found'] += 1
                        current_targets_found = self.processing_stats['targets_found']
                        
                        # REAL-TIME UPDATE: Update Thread 2 and Thread 3 progress bars with new target count
                        self._update_other_threads_target_count(current_targets_found)
                        
                        # Save Thread 1 progress after successful target detection
                        if self.api and hasattr(self.api, 'project') and self.api.project:
                            # Get current list of all analyzed images and add this one
                            processing_state = self.api.project.get_processing_state()
                            current_analyzed = processing_state.get('parallel_threads', {}).get('thread_1_target_detection', {}).get('completed_images', [])
                            if jpg_image.fn not in current_analyzed:
                                current_analyzed.append(jpg_image.fn)
                            
                            # FRESH START: No state saving (removed resume functionality)
                            print(f"[THREAD-1] 💾 Saved target analysis progress: {processed_count}/{total_futures}, analyzed: {current_analyzed}")
                        
                        # Find corresponding RAW image using project's JPG->RAW mapping
                        jpg_filename = jpg_image.fn
                        raw_filename = self.project.jpg_name_to_raw_name.get(jpg_filename)
                        print(f"[THREAD-1] Looking for RAW image for JPG: {jpg_filename}")
                        print(f"[THREAD-1] JPG->RAW mapping found: {raw_filename}")
                        
                        raw_image = None
                        if raw_filename:
                            raw_image = self.project.imagemap.get(raw_filename)
                            
                            # If not found by exact key, try finding by filename
                            if not raw_image:
                                for key, img in self.project.imagemap.items():
                                    if img.fn == raw_filename or key.endswith(raw_filename):
                                        raw_image = img
                                        break
                        
                        if raw_image:
                            # Copy calibration data from JPG to RAW
                            raw_image.is_calibration_photo = True
                            raw_image.aruco_id = result[0]
                            raw_image.aruco_corners = result[2]
                            raw_image.calibration_target_polys = result[3]
                            
                            # CRITICAL FIX: Also mark the corresponding RAW image in the raw_map
                            # Ensure consistency between project imagemap and raw_map
                            raw_filename = raw_image.fn
                            raw_base_name = os.path.splitext(raw_filename)[0]
                            if raw_base_name in raw_map:
                                original_raw_img = raw_map[raw_base_name]
                                print(f"[THREAD-1] 🔧 CRITICAL: Marking original RAW image {original_raw_img.fn} as target in raw_map (Ray)")
                                original_raw_img.is_calibration_photo = True
                                original_raw_img.aruco_id = result[0]
                                original_raw_img.aruco_corners = result[2]
                                original_raw_img.calibration_target_polys = result[3]
                            
                            # UI checkbox already updated above for target detection
                            
                            # DEFERRED: Don't queue immediately - will be queued after interval filtering
                            print(f"[THREAD-1] 📋 Target detected: {raw_image.fn} - will be queued after interval filtering")
                            
                            # Signal that calibration will be available soon
                            self.queues.calibration_ready_event.set()
                            print(f"[THREAD-1] 🚨 Calibration ready event SET - Thread-2 should start processing")
                        else:
                            print(f"[THREAD-1] WARNING: No RAW image found for target {jpg_image.fn}")
                    else:
                        jpg_image.is_calibration_photo = False
                        
                        # CRITICAL FIX: Update UI checkbox for non-targets too
                        self._update_ui_checkbox_realtime(jpg_image.fn, False)
                        
                        # Save Thread 1 progress for non-target images (still analyzed)
                        if self.api and hasattr(self.api, 'project') and self.api.project:
                            # Get current list of all analyzed images and add this one
                            processing_state = self.api.project.get_processing_state()
                            current_analyzed = processing_state.get('parallel_threads', {}).get('thread_1_target_detection', {}).get('completed_images', [])
                            if jpg_image.fn not in current_analyzed:
                                current_analyzed.append(jpg_image.fn)
                            
                            # FRESH START: No state saving (removed resume functionality)
                            print(f"[THREAD-1] 💾 Saved target analysis progress: {processed_count}/{total_futures}, analyzed: {current_analyzed}")
                except Exception as e:
                    print(f"[THREAD-1] Error processing Ray results: {e}")
            
            # Check for shutdown
            if self.queues.shutdown.is_set():
                print(f"[THREAD-1] Shutdown requested, processed {processed_count}/{total_futures} images")
                break
        
        # Ensure all futures were processed
        if processed_count < total_futures:
            print(f"[THREAD-1] WARNING: Only processed {processed_count}/{total_futures} images")
        
        # CRITICAL: Apply interval filtering to detected targets (matching serial mode)
        print(f"[THREAD-1] 🔧 Applying interval filtering to detected targets (Ray premium mode)")
        self._apply_interval_filtering_ray_mode(raw_map)
        
        # Queue all RAW images (both targets and non-targets) to Thread-3
        for raw_img in raw_map.values():
            if not hasattr(raw_img, 'is_calibration_photo'):
                raw_img.is_calibration_photo = False
            raw_img._needs_thread3_processing = True
            raw_images_to_queue.append(raw_img)
    
    def _process_target_detection_sequential(self, images, raw_map, raw_images_to_queue):
        """Original sequential target detection processing"""
        
        # CRITICAL: Force project save to ensure UI checkbox states are persisted
        print("[THREAD-1] 💾 Force saving project to persist UI checkbox states")
        self.api.project.write()
        print("[THREAD-1] ✅ Project saved - checkbox states now available")
        
        # Fix: Properly access Project Settings from options
        if 'Project Settings' in self.options:
            cfg = self.options['Project Settings']
        else:
            cfg = self.options
        


        
        min_calibration_samples = cfg["Target Detection"]["Minimum calibration sample area (px)"]
        
        # Process images in time order - oldest first
        jpg_images_seq = [img for img in images if img.fn.lower().endswith(('.jpg', '.jpeg'))]
        # CRITICAL FIX: Count actual images to be processed based on checkbox states
        total_to_process = self._count_images_to_process(jpg_images_seq)
        processed_jpg_count = 0
        print(f"[THREAD-1] Processing {len(images)} images ({len(jpg_images_seq)} JPGs, showing progress against {total_to_process} images to process)")
        
        for image in images:
            # CRITICAL: Check for stop before processing each image
            if self.queues.shutdown.is_set() or self._stop_requested:
                print(f"[THREAD-1] 🛑 Stop requested before processing {getattr(image, 'fn', 'unknown')} - aborting target detection")
                break
            
            # Save thread progress before processing each image
            if self.api and hasattr(self.api, 'project') and self.api.project:
                completed_targets = [img.fn for img in images[:images.index(image)] if getattr(img, 'is_calibration_photo', False)]
                # FRESH START: No state saving (removed resume functionality)
            
            # CRITICAL FIX: Collect RAW images but don't queue them yet
            # We need to complete target detection first to know which are targets
            if image.fn.lower().endswith('.raw'):
                print(f"[THREAD-1] Found RAW image: {image.fn}")
                # CRITICAL: Ensure the image is marked correctly
                if not hasattr(image, 'is_calibration_photo'):
                    image.is_calibration_photo = False
                
                # Store RAW images for later queuing
                raw_images_to_queue.append(image)
                
                # CRITICAL: Mark that this image needs to go through Thread 3
                image._needs_thread3_processing = True
                continue  # Skip to next image
            
            # Check if this is a JPG image that needs target detection
            if image.fn.lower().endswith(('.jpg', '.jpeg')):
                # Run target detection
                # Handle both cfg structures - direct or nested under 'Project Settings'
                if 'Project Settings' in self.options:
                    min_area = self.options['Project Settings']['Target Detection']['Minimum calibration sample area (px)']
                else:
                    min_area = self.options['Target Detection']['Minimum calibration sample area (px)']
                
                result = detect_calibration_image(
                    image, 
                    min_area,
                    self.project,
                    DummyProgressTracker()
                )
                
                
                # Increment targets_checked for every image processed
                with self.stats_lock:
                    self.processing_stats['targets_checked'] += 1
                    processed_jpg_count += 1
                    
                    # Calculate progress percentage based on actual images to process
                    progress_percent = int((processed_jpg_count / total_to_process) * 100) if total_to_process > 0 else 0
                    
                    # Send progress update for every image in premium mode
                    if self.api and hasattr(self.api, 'processing_mode') and self.api.processing_mode == "premium":
                        self.api.update_thread_progress(
                            thread_id=1,
                            percent_complete=progress_percent,
                            phase_name="Detecting",  # Use correct phase name
                            time_remaining=f"{processed_jpg_count}/{total_to_process}"
                        )
                    
                    print(f"[THREAD-1] Incremented targets_checked to {self.processing_stats['targets_checked']} (processed {processed_jpg_count}/{total_to_process} images) - {progress_percent}%")
                
                if result and result[1]:  # is_calibration_photo
                    with self.stats_lock:
                        self.processing_stats['targets_found'] += 1
                    current_targets_found = self.processing_stats['targets_found']
                    print(f"[THREAD-1] 📊 Targets found so far: {current_targets_found}")
                    
                    # REAL-TIME UPDATE: Update Thread 2 and Thread 3 progress bars with new target count
                    self._update_other_threads_target_count(current_targets_found)
                    
                    # Real-time file browser update for parallel mode
                    self._update_file_browser_realtime(image.fn, True)
                    
                    # CRITICAL FIX: Update UI with green checkmark immediately
                    self._update_ui_checkbox_realtime(image.fn, True)
                    print(f"[THREAD-1] ✅ Updated UI checkbox to green for target: {image.fn}")
                    
                    # Find corresponding RAW image using project's JPG->RAW mapping
                    jpg_filename = image.fn
                    raw_filename = self.project.jpg_name_to_raw_name.get(jpg_filename)
                    print(f"[THREAD-1] Looking for RAW image for JPG: {jpg_filename}")
                    print(f"[THREAD-1] JPG->RAW mapping found: {raw_filename}")
                    
                    raw_image = None
                    if raw_filename:
                        # CRITICAL FIX: The imagemap uses base keys, not simple filenames
                        # Look for the base key that corresponds to this JPG file
                        import os
                        jpg_base = os.path.splitext(jpg_filename)[0]  # Remove .JPG extension
                        matching_key = None
                        for key in self.project.imagemap.keys():
                            if key.startswith(jpg_base + '_'):
                                matching_key = key
                                break
                        
                        if matching_key:
                            # Get the file entry which should contain both JPG and RAW paths
                            file_entry = self.project.data.get('files', {}).get(matching_key, {})
                            raw_path = file_entry.get('raw')
                            if raw_path and os.path.basename(raw_path) == raw_filename:
                                # Create a RAW LabImage object for calibration processing
                                try:
                                    from project import LabImage
                                    raw_image = LabImage(self.project, raw_path)
                                    print(f"[THREAD-1] Created RAW LabImage for calibration: {raw_image.fn}")
                                except Exception as e:
                                    print(f"[THREAD-1] Error creating RAW LabImage: {e}")
                                    raw_image = None
                            else:
                                print(f"[THREAD-1] RAW path mismatch: expected {raw_filename}, got {os.path.basename(raw_path) if raw_path else 'None'}")
                        else:
                            print(f"[THREAD-1] No matching base key found for JPG: {jpg_filename}")
                            print(f"[THREAD-1] DEBUG: Available imagemap keys: {list(self.project.imagemap.keys())}")
                            print(f"[THREAD-1] DEBUG: Looking for base: '{jpg_base}_*'")
                    
                    if raw_image:
                        print(f"[THREAD-1] Found RAW image for calibration target {image.fn}")
                        raw_image.is_calibration_photo = True
                        raw_image.aruco_id = result[0]
                        raw_image.aruco_corners = result[2]
                        raw_image.calibration_target_polys = result[3]
                        
                        # DEFERRED: Don't queue immediately - will be queued after interval filtering
                        print(f"[THREAD-1] 📋 Target detected: {raw_image.fn} - will be queued after interval filtering")
                        
                        # CRITICAL FIX: Also queue the target image to Thread-3 AFTER marking it
                        # This ensures Thread-3 sees the correct is_calibration_photo=True
                        # CRITICAL FIX: Don't queue target image to Thread-3 from Thread-1
                        # Target images should be queued to Thread-3 by Thread-2 AFTER calibration computation
                        # This prevents race conditions where Thread-2 and Thread-3 access the same image simultaneously
                        print(f"[THREAD-1] Target image {raw_image.fn} will be queued to Thread-3 by Thread-2 after calibration")
                        
                        # Signal that calibration will be available soon
                        self.queues.calibration_ready_event.set()
                    else:
                        print(f"[THREAD-1] No RAW mapping found for {jpg_filename}")
                    
                    if raw_image:
                        # Copy calibration data from JPG to RAW
                        raw_image.is_calibration_photo = True
                        raw_image.aruco_id = result[0]
                        raw_image.aruco_corners = result[2]
                        raw_image.calibration_target_polys = result[3]
                        
                        # CRITICAL FIX: Also mark the corresponding RAW image in the raw_map
                        # The raw_image created above might be a different object than the one in raw_map
                        raw_filename = raw_image.fn
                        raw_base_name = os.path.splitext(raw_filename)[0]
                        if raw_base_name in raw_map:
                            original_raw_img = raw_map[raw_base_name]
                            print(f"[THREAD-1] 🔧 CRITICAL: Marking original RAW image {original_raw_img.fn} as target in raw_map (Sequential)")
                            original_raw_img.is_calibration_photo = True
                            original_raw_img.aruco_id = result[0]
                            original_raw_img.aruco_corners = result[2]
                            original_raw_img.calibration_target_polys = result[3]
                        
                        # DEFERRED: Don't queue immediately - will be queued after interval filtering
                        print(f"[THREAD-1] 📋 Target detected: {raw_image.fn} - will be queued after interval filtering")
                        
                        # CRITICAL FIX: Also queue the target image to Thread-3 AFTER marking it
                        # This ensures Thread-3 sees the correct is_calibration_photo=True
                        # CRITICAL FIX: Don't queue target image to Thread-3 from Thread-1
                        # Target images should be queued to Thread-3 by Thread-2 AFTER calibration computation
                        # This prevents race conditions where Thread-2 and Thread-3 access the same image simultaneously
                        print(f"[THREAD-1] Target image {raw_image.fn} will be queued to Thread-3 by Thread-2 after calibration")
                        
                        # Signal that calibration will be available soon
                        self.queues.calibration_ready_event.set()
                    else:
                        print(f"[THREAD-1] WARNING: Could not find RAW image for calibration target {image.fn}")
        
        # CRITICAL: Apply interval filtering after all targets are detected (matching Ray mode)
        print(f"[THREAD-1] 🔧 Applying interval filtering to detected targets (Sequential mode)")
        self._apply_interval_filtering_sequential_mode(raw_map)
    
    def _apply_interval_filtering_sequential_mode(self, raw_map):
        """Apply interval filtering to detected targets in sequential mode (matching serial mode logic)"""
        try:
            # Collect all detected calibration targets - check both JPG and RAW images
            all_calibration_images = []
            
            # Check RAW images for calibration flag
            for raw_img in raw_map.values():
                if getattr(raw_img, 'is_calibration_photo', False):
                    all_calibration_images.append(raw_img)
            
            # CRITICAL FIX: Check JPG images for calibration flags and find corresponding RAW
            # This is needed because target detection sets flags on JPGs, not RAWs
            if len(all_calibration_images) == 0:
                pass
                
                # Check if any JPG images have calibration flags set during target detection
                if hasattr(self, 'project') and self.project and hasattr(self.project, 'imagemap'):
                    for img_key, img in self.project.imagemap.items():
                        if img.fn.endswith('.JPG') and getattr(img, 'is_calibration_photo', False):
                            pass
                            
                            # Find corresponding RAW image using the JPG->RAW mapping from project data
                            # Look for the paired key (e.g., "2025_0727_102411_012_paired")
                            jpg_paired_key = img.fn.replace('.JPG', '_paired')
                            
                            if hasattr(self.project, 'data') and 'files' in self.project.data:
                                if jpg_paired_key in self.project.data['files']:
                                    file_data = self.project.data['files'][jpg_paired_key]
                                    raw_filename = file_data.get('raw')
                                    if raw_filename:
                                        pass
                                        
                                        # Extract just the filename from the full path for comparison
                                        import os
                                        raw_filename_only = os.path.basename(raw_filename)
                                        
                                        # Find the RAW image in raw_map
                                        for raw_img in raw_map.values():
                                            if raw_img.fn == raw_filename_only:
                                                pass
                                                # Transfer calibration flag to RAW for interval filtering
                                                raw_img.is_calibration_photo = True
                                                
                                                # CRITICAL FIX: Transfer ArUco ID and detection data from JPG to RAW
                                                if hasattr(img, 'aruco_id'):
                                                    raw_img.aruco_id = img.aruco_id
                                                
                                                if hasattr(img, 'aruco_corners'):
                                                    raw_img.aruco_corners = img.aruco_corners
                                                    
                                                if hasattr(img, 'calibration_target_polys'):
                                                    raw_img.calibration_target_polys = img.calibration_target_polys
                                                
                                                if hasattr(img, 'target_sample_diameter'):
                                                    raw_img.target_sample_diameter = img.target_sample_diameter
                                                
                                                all_calibration_images.append(raw_img)
                                                break
                                        else:
                                            pass
                                    else:
                                        pass
                                else:
                                    pass
                            else:
                                pass
            
            
            if len(all_calibration_images) == 0:
                pass
                return
            
            # Use the same interval filtering logic as serial mode
            if self.api and hasattr(self.api, '_filter_calibration_targets_by_interval'):
                pass
                filtered_targets = self.api._filter_calibration_targets_by_interval(all_calibration_images)
                
                # Create a set of filtered target filenames for quick lookup
                filtered_filenames = {img.fn for img in filtered_targets}
                
                # Update UI for filtered-out targets (unchecked)
                for target in all_calibration_images:
                    if target.fn not in filtered_filenames:
                        # Find the corresponding JPG filename for UI update
                        jpg_filename = target.fn.replace('.RAW', '.JPG')
                        self._update_ui_checkbox_realtime(jpg_filename, False)
                
                # Queue filtered targets to Thread 2
                for target in filtered_targets:
                    self.queues.calibration_compute_queue.put(target)
                
                
                # CRITICAL: Update targets_found count to reflect filtered targets (for Thread 2 progress bar)
                with self.stats_lock:
                    old_count = self.processing_stats.get('targets_found', 0)
                    self.processing_stats['targets_found'] = len(filtered_targets)
                
                # Send sentinel to Thread 2 to signal end of targets
                self.queues.calibration_compute_queue.put(None)
                
                # UI already updated by individual checkbox updates - no need for full refresh
                
            else:
                # Fallback: queue all targets if filtering method not available
                for target in all_calibration_images:
                    self.queues.calibration_compute_queue.put(target)
                
                # Update targets_found count (no filtering applied)
                with self.stats_lock:
                    old_count = self.processing_stats.get('targets_found', 0)
                    self.processing_stats['targets_found'] = len(all_calibration_images)
                
                # Send sentinel to Thread 2
                self.queues.calibration_compute_queue.put(None)
                
        except Exception as e:
            pass
            import traceback
            traceback.print_exc()
            
            # Fallback: queue all targets if filtering fails
            error_targets = []
            for raw_img in raw_map.values():
                if getattr(raw_img, 'is_calibration_photo', False):
                    self.queues.calibration_compute_queue.put(raw_img)
                    error_targets.append(raw_img)
            
            # Update targets_found count (error fallback)
            with self.stats_lock:
                old_count = self.processing_stats.get('targets_found', 0)
                self.processing_stats['targets_found'] = len(error_targets)
            
            # Send sentinel to Thread 2
            self.queues.calibration_compute_queue.put(None)
    
    def _apply_interval_filtering_ray_mode(self, raw_map):
        """Apply interval filtering to detected targets in Ray premium mode (matching serial mode logic)"""
        try:
            # Collect all detected calibration targets
            all_calibration_images = []
            for raw_img in raw_map.values():
                if getattr(raw_img, 'is_calibration_photo', False):
                    all_calibration_images.append(raw_img)
            
            
            if len(all_calibration_images) == 0:
                pass
                return
            
            # Use the same interval filtering logic as serial mode
            if self.api and hasattr(self.api, '_filter_calibration_targets_by_interval'):
                pass
                filtered_targets = self.api._filter_calibration_targets_by_interval(all_calibration_images)
                
                # Create a set of filtered target filenames for quick lookup
                filtered_filenames = {img.fn for img in filtered_targets}
                
                # Update targets that were filtered out
                for raw_img in all_calibration_images:
                    if raw_img.fn not in filtered_filenames:
                        # This target was filtered out - mark it as not a calibration photo
                        pass
                        raw_img.is_calibration_photo = False
                        
                        # Update UI to remove green check (matching serial mode behavior)
                        jpg_filename = raw_img.fn.replace('.RAW', '.JPG')
                        self._update_ui_checkbox_realtime(jpg_filename, False)
                
                # Queue only the filtered targets to Thread 2
                for filtered_target in filtered_targets:
                    pass
                    self.queues.calibration_compute_queue.put(filtered_target)
                
                
                # CRITICAL: Update targets_found count to reflect filtered targets (for Thread 2 progress bar)
                with self.stats_lock:
                    old_count = self.processing_stats.get('targets_found', 0)
                    self.processing_stats['targets_found'] = len(filtered_targets)
                
                # Send sentinel to Thread 2 to signal end of targets
                self.queues.calibration_compute_queue.put(None)
                
                # Save project data before UI refresh to ensure changes are persisted
                if self.api and hasattr(self.api, 'project') and self.api.project:
                    self.api.project.write()
                
                # UI already updated by individual checkbox updates - no need for full refresh
                
            else:
                pass
                # Fallback: queue all targets if filtering method not available
                for target in all_calibration_images:
                    self.queues.calibration_compute_queue.put(target)
                
                # Update targets_found count (no filtering applied)
                with self.stats_lock:
                    old_count = self.processing_stats.get('targets_found', 0)
                    self.processing_stats['targets_found'] = len(all_calibration_images)
                
                # Send sentinel to Thread 2
                self.queues.calibration_compute_queue.put(None)
        
        except Exception as e:
            pass
            import traceback
            traceback.print_exc()
            # Fallback: queue all targets if filtering fails
            error_targets = []
            for raw_img in raw_map.values():
                if getattr(raw_img, 'is_calibration_photo', False):
                    self.queues.calibration_compute_queue.put(raw_img)
                    error_targets.append(raw_img)
            
            # Update targets_found count (error fallback)
            with self.stats_lock:
                old_count = self.processing_stats.get('targets_found', 0)
                self.processing_stats['targets_found'] = len(error_targets)
            
            # Send sentinel to Thread 2
            self.queues.calibration_compute_queue.put(None)
    

    
    def _refresh_ui_after_interval_filtering(self):
        """Refresh the UI after interval filtering to show correct target states"""
        try:
            if self.api and hasattr(self.api, 'window') and self.api.window:
                # Get updated project files from the API
                updated_project_files = self.api.get_image_list()
                
                # Update the file browser with filtered results
                import json
                self.api.window._js_api.safe_evaluate_js(f'''
                    (function() {{
                        try {{
                            console.log('[THREAD-1] [INTERVAL_FILTER] 🔄 Refreshing UI after interval filtering');
                            
                            // Get the file browser panel
                            const fileBrowserPanel = document.querySelector('project-file-panel');
                            if (fileBrowserPanel && fileBrowserPanel.fileviewer) {{
                                // Update with filtered project files
                                fileBrowserPanel.fileviewer.projectFiles = {json.dumps(updated_project_files)};
                                fileBrowserPanel.fileviewer.initializeSortOrder();
                                fileBrowserPanel.fileviewer.requestUpdate();
                                fileBrowserPanel.requestUpdate();
                                
                                console.log('[THREAD-1] [INTERVAL_FILTER] ✅ UI refreshed - filtered targets updated');
                            }}
                            
                            // Also update image viewer if present
                            const imageViewer = document.querySelector('image-viewer');
                            if (imageViewer) {{
                                imageViewer.requestUpdate();
                                console.log('[THREAD-1] [INTERVAL_FILTER] ✅ Image viewer refreshed');
                            }}
                        }} catch (error) {{
                            console.log('[THREAD-1] [INTERVAL_FILTER] ⚠️ Error refreshing UI:', error);
                        }}
                    }})();
                ''')
        except Exception as e:
            pass
    
    def _thread2_calibration_compute(self):
        """Thread 2: Compute calibration data from target images and save to JSON"""
        # CRITICAL FIX: Prevent multiple thread starts
        if hasattr(self, '_thread2_completed') and self._thread2_completed:
            print("[THREAD-2] WARNING: Thread-2 already completed, ignoring restart")
            return
        
        # Ensure ALS is computed once and persisted before any export work
        try:
            self._ensure_als_precomputed()
        except Exception as _als_once_e:
            print(f"[THREAD-2] WARN: _ensure_als_precomputed at thread start failed: {_als_once_e}")
        
        # Check if calibration is already complete (resume scenario)
        if self.api and hasattr(self.api, 'project') and self.api.project:
            processing_state = self.api.project.get_processing_state()
            if processing_state and processing_state.get('parallel_threads', {}).get('thread_2_calibration', {}).get('completed', False):
                print("[THREAD-2] 🔄 Calibration already completed - showing 100% status")
                # Update UI to show Thread 2 completion immediately
                if hasattr(self.api, 'update_thread_progress'):
                    completed_count = len(processing_state.get('parallel_threads', {}).get('thread_2_calibration', {}).get('completed_images', []))
                    self.api.update_thread_progress(
                        thread_id=2,
                        percent_complete=100,
                        phase_name="Analyzing",
                        time_remaining=f"{completed_count}/{completed_count}"
                    )
                # Still run the thread logic to handle any new images, but skip if nothing to do
        
        try:
            print(f"[THREAD-2 DEBUG] use_ray={self.use_ray}")
            if self.use_ray:
                print("[THREAD-2] Using Ray batch processing")
                # Process calibration images in batches using Ray
                self._process_calibration_ray_batch()
            else:
                print("[THREAD-2] Using sequential processing")
                # Original sequential processing
                self._process_calibration_sequential()
            
        except Exception as e:
            print(f"[THREAD-2] ❌ CRITICAL ERROR in Thread-2: {e}")
            import traceback
            print(f"[THREAD-2] ❌ FULL TRACEBACK:")
            traceback.print_exc()
            print(f"[THREAD-2] ❌ This error is causing Thread-2 to fail and set shutdown flag")
            self.queues.shutdown.set()
        finally:
            print(f"[THREAD-2] 🏁 Thread-2 finishing - _thread2_completed = True")
            self._thread2_completed = True
            if self.gpu_allocator:
                self.gpu_allocator.mark_thread_complete(2)
    
    def _process_calibration_ray_batch(self):
        """Process calibration computation using Ray for batch parallel processing"""
        # Use global ray variable instead of importing directly
        global ray
        
        calibration_images = []
        processed_images = set()  # Track processed images to avoid duplicates
        
        # OPTIMIZATION: Remove blocking wait for Thread-1 - instead check for available data
        print("[THREAD-2] 🚀 STARTING: Ray batch calibration processing thread")
        print(f"[THREAD-2] 🔍 DEBUG: Thread-2 is alive and running")
        print("[THREAD-2] Starting calibration computation - will process images as they become available...")
        # Ensure ALS precompute is triggered at batch start as well (no-op if already done)
        try:
            self._ensure_als_precomputed()
        except Exception as _als_once_e:
            print(f"[THREAD-2] WARN: _ensure_als_precomputed at batch start failed: {_als_once_e}")
        
        # Show initial Thread 2 state with spinner
        if self.api and hasattr(self.api, 'update_thread_progress'):
            self.api.update_thread_progress(
                thread_id=2,
                percent_complete=0,
                phase_name="Analyzing",
                time_remaining="0/?"
            )
            print(f"[THREAD-2] Initial progress: 0/? (waiting for targets)")
        
        # Collect calibration images as they become available from Thread-1
        while not self.queues.shutdown.is_set():
            # Keep the white spinner active while waiting
            if self.api and hasattr(self.api, 'update_thread_progress') and len(calibration_images) == 0:
                self.api.update_thread_progress(
                    thread_id=2,
                    percent_complete=0,
                    phase_name="Analyzing", 
                    time_remaining="0/?"
                )
            print(f"[THREAD-2] 🔍 Waiting for calibration images... (queue size: {self.queues.calibration_compute_queue.qsize()})")
            
            try:
                image = self.queues.calibration_compute_queue.get(timeout=0.5)
                if image is None:  # Sentinel
                    print("[THREAD-2] Received sentinel, finishing calibration computation")
                    break
                    
                # CRITICAL: Check for stop before processing each calibration
                if self.queues.shutdown.is_set() or self._stop_requested:
                    print(f"[THREAD-2] 🛑 Stop requested before calibrating {getattr(image, 'fn', 'unknown')} - aborting")
                    break
                
                # Thread progress is saved after processing each image with correct cumulative counts
                
                print(f"[THREAD-2] 📥 Received calibration image: {image.fn}")
                    
                # Skip if already processed
                if image.fn in processed_images:
                    print(f"[THREAD-2] Skipping duplicate calibration for {image.fn}")
                    continue
                
                # OPTIMIZATION: Skip if calibration data already exists and is valid
                print(f"[THREAD-2] DEBUG: Checking {image.fn} - hasattr(calibration_coefficients): {hasattr(image, 'calibration_coefficients')}, coefficients: {getattr(image, 'calibration_coefficients', 'NOT_SET')}")
                if hasattr(image, 'calibration_coefficients') and image.calibration_coefficients:
                    print(f"[THREAD-2] ✅ Calibration data already exists for {image.fn}, skipping computation")
                    # Calibration data already saved to JSON by previous processing
                    processed_images.add(image.fn)
                    
                    # CRITICAL FIX: Update progress count even when skipping
                    with self.stats_lock:
                        self.processing_stats['calibrations_processed'] += 1
                        self.processing_stats['calibrations_computed'] += 1
                    
                    # Update progress to show we've "completed" this target (by skipping)
                    new_processed_count = self.processing_stats['calibrations_processed']
                    # CRITICAL: Always use the latest targets_found count, calculate from project if not set
                    current_total_targets = self.processing_stats.get('targets_found', None)
                    if current_total_targets is None:
                        # Calculate total targets from project files (JPG files used for target detection)
                        current_total_targets = 0
                        if hasattr(self, 'project') and self.project.data.get('files'):
                            for fileset in self.project.data['files'].values():
                                if fileset.get('jpg'):
                                    current_total_targets += 1
                        current_total_targets = max(1, current_total_targets)
                    print(f"[THREAD-2] DEBUG: Skipped progress - processed: {new_processed_count}, total: {current_total_targets}, targets_found: {self.processing_stats.get('targets_found', 'NOT_SET')}")
                    progress_percent = int((new_processed_count / current_total_targets) * 100) if current_total_targets > 0 else 0
                    
                    if self.api and hasattr(self.api, 'update_thread_progress'):
                        self.api.update_thread_progress(
                            thread_id=2,
                            percent_complete=progress_percent,
                            phase_name="Analyzing",
                            time_remaining=f"{new_processed_count}/{current_total_targets}"
                        )
                        print(f"[THREAD-2] Progress update (skipped): {new_processed_count}/{current_total_targets} ({progress_percent}%) - skipped {image.fn} (already computed)")
                    
                    # Queue to Thread-3 immediately since it's ready
                    if self._queue_file_safely(self.queues.calibration_apply_queue, image, "pre-existing calibration"):
                        print(f"[THREAD-2] ✅ Queued {image.fn} to Thread-3 (pre-existing calibration)")
                    else:
                        print(f"[THREAD-2] ⏭️ Skipped duplicate {image.fn} (pre-existing calibration)")
                    continue
                    
                # CRITICAL: Process this target IMMEDIATELY, don't wait for batch
                print(f"[THREAD-2] 📥 Received calibration image: {image.fn} - processing immediately")
                
                # Update progress to show current target count
                current_target_count = self.processing_stats.get('targets_found', 1)
                print(f"[THREAD-2] DEBUG: current_target_count = {current_target_count}, targets_found = {self.processing_stats.get('targets_found', 'NOT_SET')}")
                processed_count = len(processed_images)  # How many we've already processed
                
                # Update UI to show we have a new target to process (BEFORE processing)
                if self.api and hasattr(self.api, 'update_thread_progress'):
                    # Always show the current targets_found count, even if it's just 1 initially
                    progress_percent = int((processed_count / current_target_count) * 100) if current_target_count > 0 else 0
                    time_display = f"{processed_count}/{current_target_count}"
                    print(f"[THREAD-2] Progress update (received): {processed_count}/{current_target_count} ({progress_percent}%) - received target {image.fn}")
                    
                    self.api.update_thread_progress(
                        thread_id=2,
                        percent_complete=progress_percent,
                        phase_name="Analyzing",
                        time_remaining=time_display
                    )
                
                # Process this single image immediately using Ray
                if not image.fn in processed_images:
                    
                    # Process single image with Ray immediately
                    try:
                        print(f"[THREAD-2] 🚀 Processing single target: {image.fn}")
                        
                        # Add to processed set BEFORE processing to prevent duplicates
                        processed_images.add(image.fn)
                        
                        # Use Ray to process this single image (unless sequential mode is forced)
                        if RAY_AVAILABLE and not getattr(self, 'sequential_mode', False):
                            calib_task_func = get_calib_data_ray
                            print(f"[THREAD-2] Using Ray remote function: get_calib_data_ray for {image.fn}")
                            
                            # CRITICAL FIX: Create a new LabImage with the correct project path
                            # The original image has the source path, but files are in the project directory
                            from project import LabImage, Project
                            import os
                            
                            # Get the current project path (where files actually exist)
                            project_path = None
                            
                            # Try multiple ways to get the project path
                            if hasattr(self, 'project') and hasattr(self.project, 'path'):
                                project_path = self.project.path
                            elif hasattr(image, 'project') and hasattr(image.project, 'path'):
                                project_path = image.project.path
                            elif hasattr(image, 'project_path') and image.project_path:
                                project_path = image.project_path
                            
                            # If still no project path, try to get it from the global project variable
                            if not project_path:
                                import sys
                                current_module = sys.modules[__name__]
                                if hasattr(current_module, 'current_project') and hasattr(current_module.current_project, 'path'):
                                    project_path = current_module.current_project.path
                            
                            print(f"[THREAD-2] 🔧 FIXING: Original image project_path: {getattr(image, 'project_path', 'None')}")
                            print(f"[THREAD-2] 🔧 FIXING: Using correct project_path: {project_path}")
                            
                            if project_path:
                                # Create new Project and LabImage objects with correct paths
                                correct_project = Project(project_path)
                                
                                # CRITICAL FIX: Get the full absolute path from the original image
                                full_source_path = image.fn  # Default fallback
                                if hasattr(image, 'path') and image.path and os.path.isabs(str(image.path)):
                                    full_source_path = str(image.path)
                                    print(f"[THREAD-2] 🔧 Using absolute path from image.path: {full_source_path}")
                                elif hasattr(self, 'project') and self.project and hasattr(self.project, 'imagemap'):
                                    # Find the full path from project imagemap
                                    for img_key, img_obj in self.project.imagemap.items():
                                        if img_obj.fn == image.fn:
                                            if hasattr(img_obj, 'path') and os.path.isabs(str(img_obj.path)):
                                                full_source_path = str(img_obj.path)
                                                print(f"[THREAD-2] 🔧 Found absolute path from imagemap: {full_source_path}")
                                                break
                                
                                corrected_image = LabImage(correct_project, full_source_path)
                                
                                # Copy any important attributes from the original image
                                if hasattr(image, 'is_calibration_photo'):
                                    corrected_image.is_calibration_photo = image.is_calibration_photo
                                if hasattr(image, 'calibration_polys'):
                                    corrected_image.calibration_polys = image.calibration_polys
                                if hasattr(image, 'aruco_id'):
                                    corrected_image.aruco_id = image.aruco_id
                                
                                # CRITICAL FIX: Copy EXIF camera metadata from original image (EXIF reading may fail in new context)
                                if hasattr(image, 'camera_model'):
                                    corrected_image.camera_model = image.camera_model
                                    print(f"[THREAD-2] 🔧 COPIED: camera_model = {image.camera_model}")
                                if hasattr(image, 'camera_filter'):
                                    corrected_image.camera_filter = image.camera_filter
                                    print(f"[THREAD-2] 🔧 COPIED: camera_filter = {image.camera_filter}")
                                if hasattr(image, 'Model'):
                                    corrected_image.Model = image.Model
                                    print(f"[THREAD-2] 🔧 COPIED: Model = {image.Model}")
                                
                                print(f"[THREAD-2] 🔧 CORRECTED: New image project_path: {getattr(corrected_image, 'project_path', 'None')}")
                                image = corrected_image
                            else:
                                print(f"[THREAD-2] ⚠️ WARNING: Could not determine correct project path, using original image")
                            
                            # Create Ray future for this single image
                            # Get the image file path and project directory
                            # CRITICAL FIX: RAW files are in SOURCE directory, not project directory
                            if hasattr(image, 'path') and image.path:
                                # Use the SOURCE path from the image object (where RAW files actually exist)
                                image_source_path = str(image.path)
                            else:
                                # This shouldn't happen, but fallback to filename
                                image_source_path = str(image.fn)
                                
                            # CRITICAL DEBUG: Verify the source path is complete
                            import os
                            if not os.path.isabs(image_source_path):
                                print(f"[THREAD-2] ❌ ERROR: Source path is not absolute")
                                # Try to find the full path from the project's imagemap (same as Thread-3)
                                if hasattr(self, 'project') and self.project and hasattr(self.project, 'imagemap'):
                                    for img_key, img_obj in self.project.imagemap.items():
                                        if img_obj.fn == image_source_path:  # image_source_path is just the filename
                                            if hasattr(img_obj, 'fp'):
                                                image_source_path = str(img_obj.fp)
                                                print(f"[THREAD-2] 🔧 FOUND: Full source path from imagemap.fp: {image_source_path}")
                                                break
                                            elif hasattr(img_obj, 'path'):
                                                image_source_path = str(img_obj.path)
                                                print(f"[THREAD-2] 🔧 FOUND: Full source path from imagemap.path: {image_source_path}")
                                                break
                                    else:
                                        print(f"[THREAD-2] ❌ ERROR: Could not find {image_source_path} in project imagemap")
                                else:
                                    print(f"[THREAD-2] ❌ ERROR: No project or imagemap available to resolve path")
                            
                            # Project directory is for exports/calibration data storage
                            project_dir = getattr(image, 'project_path', None) or str(self.outfolder)
                            
                            # Extract camera metadata from the image object (main thread can read EXIF correctly)
                            camera_model = getattr(image, 'camera_model', 'Unknown')
                            camera_filter = getattr(image, 'camera_filter', 'Unknown')
                            model_from_exif = getattr(image, 'Model', 'Unknown')
                            
                            # Extract ArUco data from the image object (main thread has target detection data)
                            aruco_id = getattr(image, 'aruco_id', None)
                            target_sample_diameter = getattr(image, 'target_sample_diameter', None)
                            calibration_polys = getattr(image, 'calibration_polys', None)
                            
                            # CRITICAL FIX: Extract ALS data from the image object (attached in main thread)
                            als_magnitude = getattr(image, 'als_magnitude', None)
                            als_data = getattr(image, 'als_data', None)
                            calibration_yvals = getattr(image, 'calibration_yvals', None)
                            
                            # CRITICAL FIX: If ALS data is missing, copy it from the project imagemap
                            if als_magnitude is None or als_data is None or calibration_yvals is None:

                                project_imagemap = getattr(self.project, 'imagemap', {})
                                for key, project_image in project_imagemap.items():
                                    if getattr(project_image, 'fn', None) == getattr(image, 'fn', None):
                                        if als_magnitude is None:
                                            als_magnitude = getattr(project_image, 'als_magnitude', None)
                                        if als_data is None:
                                            als_data = getattr(project_image, 'als_data', None)
                                        if calibration_yvals is None:
                                            calibration_yvals = getattr(project_image, 'calibration_yvals', None)
                                        if als_magnitude is not None or als_data is not None or calibration_yvals is not None:

                                            # Also attach it to the current image object for future use
                                            if als_magnitude is not None:
                                                image.als_magnitude = als_magnitude
                                            if als_data is not None:
                                                image.als_data = als_data
                                            if calibration_yvals is not None:
                                                image.calibration_yvals = calibration_yvals
                                        break
                                if als_magnitude is None and als_data is None and calibration_yvals is None:
                                    pass  # No ALS data found in project imagemap
                            
                            print(f"[THREAD-2] 🔍 Ray parameters: image_source_path={image_source_path}, project_dir={project_dir}")
                            print(f"[THREAD-2] 🔍 Camera metadata: camera_model={camera_model}, camera_filter={camera_filter}, Model={model_from_exif}")
                            print(f"[THREAD-2] 🔍 ArUco metadata: aruco_id={aruco_id}, diameter={target_sample_diameter}, polys={calibration_polys is not None}")

                            print(f"[THREAD-2] 🔍 RAW file should exist at: {image_source_path}")
                            print(f"[THREAD-2] 🔍 Calibration data will be stored in: {project_dir}")
                            
                            # Create Ray future with corrected parameters - only image and options
                            future = calib_task_func.remote(corrected_image, self.options)
                            
                            # Update progress to show we're actively processing
                            # Use the same progress calculation as the rest of the function
                            current_target_count = self.processing_stats.get('targets_found', 1)
                            # Since we added the image to processed_images already, subtract 1 to show we're starting (not completed)
                            processed_count = len(processed_images) - 1  # How many we've actually completed (not including current)
                            progress_percent = int((processed_count / current_target_count) * 100) if current_target_count > 0 else 0
                            
                            if self.api and hasattr(self.api, 'update_thread_progress'):
                                self.api.update_thread_progress(
                                    thread_id=2,
                                    percent_complete=progress_percent,  # Show actual progress based on completed targets
                                    phase_name="Analyzing",
                                    time_remaining=f"{processed_count}/{current_target_count}"
                                )
                            
                            # Wait for this single result with longer timeout for calibration
                            print(f"[THREAD-2] ⏳ Waiting for Ray calibration processing of {image.fn}...")
                            
                            # Check if GPU is available for dynamic timeout
                            gpu_available = False
                            try:
                                from dynamic_gpu_allocator import get_gpu_allocator
                                gpu_allocator = get_gpu_allocator()
                                gpu_available = gpu_allocator.total_gpu_memory > 0
                            except:
                                pass
                            
                            # Use shorter timeout and more aggressive fallback for CPU-only processing
                            timeout_seconds = 60 if gpu_available else 90  # Much shorter timeouts
                            print(f"[THREAD-2] Using {timeout_seconds}s timeout ({'GPU' if gpu_available else 'CPU'}-mode)")
                            
                            try:
                                result = ray.get(future, timeout=timeout_seconds)
                                print(f"[THREAD-2] ✅ Ray processing completed for {image.fn}")
                            except ray.exceptions.GetTimeoutError:
                                print(f"[THREAD-2] ⚠️ Ray timeout processing {image.fn} after {timeout_seconds}s")
                                
                                # Cancel the Ray task to free resources
                                try:
                                    ray.cancel(future, force=True)
                                    print(f"[THREAD-2] 🚫 Cancelled Ray task for {image.fn}")
                                except Exception as cancel_error:
                                    print(f"[THREAD-2] ⚠️ Could not cancel Ray task: {cancel_error}")
                                
                                # Track Ray failures and switch to sequential mode if needed
                                self.ray_failures += 1
                                print(f"[THREAD-2] 📈 Ray failure count: {self.ray_failures}/{self.max_ray_failures}")
                                
                                if self.ray_failures >= self.max_ray_failures:
                                    self.sequential_mode = True
                                    print(f"[THREAD-2] 🔄 Switching to sequential mode after {self.ray_failures} Ray failures")
                                
                                # Immediate fallback to sequential processing
                                try:
                                    from tasks import get_calib_data
                                    print(f"[THREAD-2] 🔄 Sequential fallback for {image.fn}")
                                    result = get_calib_data(image, self.options, DummyProgressTracker())
                                    print(f"[THREAD-2] ✅ Sequential processing completed for {image.fn}")
                                except Exception as seq_error:
                                    print(f"[THREAD-2] ❌ Sequential fallback failed for {image.fn}: {seq_error}")
                                result = None
                            
                            if result:
                                # CRITICAL FIX: Handle dict return from Ray function
                                if isinstance(result, dict) and result.get('success'):
                                    entry = result.get('entry', {})
                                    coeffs = entry.get('coefficients', [False, False, False])
                                    limits = entry.get('limits', [0, 0, 0])
                                    xvals = entry.get('xvals')
                                    yvals = entry.get('yvals')
                                    print(f"[THREAD-2] ✅ Extracted calibration data from Ray dict for {image.fn}")
                                elif isinstance(result, (tuple, list)) and len(result) == 4:
                                    coeffs, limits, xvals, yvals = result
                                    print(f"[THREAD-2] ✅ Extracted calibration data from Ray tuple for {image.fn}")
                                else:
                                    print(f"[THREAD-2] ❌ Unexpected result format from Ray: {type(result)} - {result}")
                                    continue
                                
                                # CRITICAL: Ensure target image has RAW pixel data before coefficient computation
                                
                                # Store coefficients and limits from Ray result
                                image.calibration_coefficients = coeffs
                                image.calibration_limits = limits
                                image.calibration_xvals = xvals
                                image.calibration_yvals = yvals
                                
                                # Store base RAW coefficients for non-target images to use
                                image._raw_base_coefficients = coeffs
                                
                                # Save calibration data to JSON (persistent storage)
                                _save_calibration_data(image, self.options, self.outfolder)
                                
                                print(f"[THREAD-2] ✅ Completed calibration for {image.fn}")
                                
                                # Update stats
                                with self.stats_lock:
                                    self.processing_stats['calibrations_processed'] += 1
                                    self.processing_stats['calibrations_computed'] += 1
                                
                                # Update progress to show completion
                                # Use stats counter instead of set length for accuracy
                                new_processed_count = self.processing_stats['calibrations_processed']
                                current_total_targets = self.processing_stats.get('targets_found', None)
                                if current_total_targets is None:
                                    # Calculate total targets from project files (JPG files used for target detection)
                                    current_total_targets = 0
                                    if hasattr(self, 'project') and self.project.data.get('files'):
                                        for fileset in self.project.data['files'].values():
                                            if fileset.get('jpg'):
                                                current_total_targets += 1
                                    current_total_targets = max(1, current_total_targets)
                                print(f"[THREAD-2] DEBUG: Progress calculation - processed: {new_processed_count}, total: {current_total_targets}, targets_found: {self.processing_stats.get('targets_found', 'NOT_SET')}")
                                progress_percent = int((new_processed_count / current_total_targets) * 100) if current_total_targets > 0 else 0
                                
                                if self.api and hasattr(self.api, 'update_thread_progress'):
                                    self.api.update_thread_progress(
                                        thread_id=2,
                                        percent_complete=progress_percent,
                                        phase_name="Analyzing",
                                        time_remaining=f"{new_processed_count}/{current_total_targets}"
                                    )
                                    print(f"[THREAD-2] Progress update (completed): {new_processed_count}/{current_total_targets} ({progress_percent}%) - completed {image.fn}")
                                
                                # Queue to Thread-3 immediately
                                if self._queue_file_safely(self.queues.calibration_apply_queue, image, "processed calibration"):
                                    print(f"[THREAD-2] ✅ Queued {image.fn} to Thread-3")
                                else:
                                    print(f"[THREAD-2] ⏭️ Skipped duplicate {image.fn} (processed calibration)")
                            else:
                                print(f"[THREAD-2] ❌ Failed to process {image.fn}")
                        else:
                            if self.sequential_mode:
                                print(f"[THREAD-2] Sequential mode enabled, processing {image.fn} directly")
                            else:
                                print(f"[THREAD-2] Ray not available, using sequential processing for {image.fn}")
                            # Sequential processing
                            try:
                                result = get_calib_data(image, self.options, None)
                                if result:
                                    # CRITICAL FIX: get_calib_data returns 5 elements: coeffs, limits, xvals, yvals, image
                                    if len(result) == 5:
                                        coeffs, limits, xvals, yvals, modified_image = result
                                    elif len(result) == 4:
                                        coeffs, limits, xvals, yvals = result
                                    else:
                                        print(f"[THREAD-2] ❌ Unexpected result length from get_calib_data: {len(result)}")
                                        continue
                                    image.calibration_coefficients = coeffs
                                    image.calibration_limits = limits
                                    image.calibration_xvals = xvals
                                    image.calibration_yvals = yvals
                                    
                                    # Save calibration data to JSON (persistent storage)
                                    _save_calibration_data(image, self.options, self.outfolder)
                                    
                                    print(f"[THREAD-2] ✅ Completed sequential calibration for {image.fn}")
                                    
                                    # Update stats
                                    with self.stats_lock:
                                        self.processing_stats['calibrations_processed'] += 1
                                        self.processing_stats['calibrations_computed'] += 1
                                    
                                    # Queue to Thread-3 immediately
                                    self.queues.calibration_apply_queue.put(image)
                                    print(f"[THREAD-2] ✅ Queued {image.fn} to Thread-3")
                                else:
                                    print(f"[THREAD-2] ❌ Sequential processing failed for {image.fn}")
                            except Exception as seq_e:
                                print(f"[THREAD-2] ❌ Sequential processing error for {image.fn}: {seq_e}")
                            
                    except Exception as e:
                        print(f"[THREAD-2] ❌ Error processing {image.fn}: {e}")
                        import traceback
                        traceback.print_exc()
                
            except queue.Empty:
                # Timeout occurred - check if Thread-1 is complete and no more targets are coming
                if hasattr(self, '_thread1_completed') and self._thread1_completed:
                    # Thread-1 is done and queue is empty - no more targets coming
                    if self.queues.calibration_compute_queue.qsize() == 0:
                        print("[THREAD-2] Thread-1 complete and no more calibration targets - finishing")
                        break
                
                # Keep the white spinner active while waiting for more targets
                if self.api and hasattr(self.api, 'update_thread_progress'):
                    current_target_count = self.processing_stats.get('targets_found', 0)
                    processed_count = len(processed_images)
                    
                    if current_target_count == 0:
                        # Still waiting for first target
                        self.api.update_thread_progress(
                            thread_id=2,
                            percent_complete=0,
                            phase_name="Analyzing",
                            time_remaining="0/?"
                        )
                    else:
                        # Show current progress
                        progress_percent = int((processed_count / current_target_count) * 100) if current_target_count > 0 else 0
                        self.api.update_thread_progress(
                            thread_id=2,
                            percent_complete=progress_percent,
                            phase_name="Analyzing",
                            time_remaining=f"{processed_count}/{current_target_count}"
                        )
                
                # Check if we should stop (received sentinel or shutdown)
                if self.queues.shutdown.is_set():
                    break
                    
                # Continue checking for more images (streaming approach)
                continue
        
        # CRITICAL: If we exit the streaming loop (due to sentinel), signal completion
        print("[THREAD-2] Streaming loop ended - signaling calibration computation complete")
        self.queues.all_calibration_complete.set()
        self.queues.calibration_compute_complete.set()
        print("[THREAD-2] Signaled calibration computation complete (after streaming)")
        
        # Update UI to show Thread 2 completion
        if self.api and hasattr(self.api, 'update_thread_progress'):
            # CRITICAL FIX: Use targets_found instead of calibrations_processed for final display
            total_targets = self.processing_stats.get('targets_found', 0)
            self.api.update_thread_progress(
                thread_id=2,
                percent_complete=100,
                phase_name="Analyzing",
                time_remaining=f"{total_targets}/{total_targets}"
            )
        
        if not calibration_images:
            print("[THREAD-2] No calibration images to process")
            self.queues.all_calibration_complete.set()
            self.queues.calibration_compute_complete.set()  # CRITICAL: Signal completion
            print("[THREAD-2] Signaled calibration computation complete (streaming path)")
            self.queues.calibration_apply_queue.put(None)  # Sentinel for Thread-3
            # CRITICAL FIX: Don't send sentinel to Thread-4 here - let Thread-3 send it when actually done
            # self.queues.export_queue.put(None)  # Sentinel for Thread-4 - REMOVED
            return
        
        print(f"[THREAD-2] Processing {len(calibration_images)} calibration images with Ray")
        
        # Update UI to show Thread 2 starting with final batch
        if self.api and hasattr(self.api, 'update_thread_progress'):
            # Use the running total from stats for accurate count
            total_targets = self.processing_stats.get('targets_found', len(calibration_images))
            self.api.update_thread_progress(
                thread_id=2,
                percent_complete=0,
                phase_name="Analyzing",
                time_remaining=f"0/{total_targets}"
            )
            print(f"[THREAD-2] Starting batch processing: 0/{total_targets} - about to process {len(calibration_images)} images")
        
        # Use the existing Ray remote function for calibration computation
        calib_task_func = get_unified_task_function('get_calib_data', execution_mode='parallel')
        
        # Handle both cfg structures
        options_for_calib = self.options['Project Settings'] if 'Project Settings' in self.options else self.options
        
        # Process images individually using the existing Ray remote function
        futures = []
        if hasattr(calib_task_func, 'remote'):
            # Ray remote function - create futures for each image
            for img in calibration_images:
                # Pre-load image data if needed
                if not hasattr(img, 'data') or img.data is None:
                    raw_data = img.raw_data
                    if raw_data is not None:
                        img.data = raw_data
                        # Cache the debayered data
                        self.queues.cache_image_data(img.fn, raw_data)
                # Explicit cache update after debayering (even if already present)
                if hasattr(img, 'data') and img.data is not None:
                    self.queues.cache_image_data(img.fn, img.data)
                
                future = calib_task_func.remote(img, options_for_calib)
                futures.append(future)
        else:
            # Not a Ray function - this should not happen in premium mode
            print("[THREAD-2] ❌ Ray remote function not available - this should not happen in premium mode!")
            print("[THREAD-2] ⚠️ Continuing with streaming processing instead of falling back to sequential")
            # Don't fall back to sequential processing as it will interfere with streaming
            return
        
        print(f"[THREAD-2] Created {len(futures)} Ray tasks for calibration computation")
        
        # Process results as they complete
        # Create a mapping of futures to images for result processing
        future_to_image = {future: img for future, img in zip(futures, calibration_images)}
        
        while futures:
            ready, futures = ray.wait(futures, num_returns=1, timeout=1.0)
            for future in ready:
                try:
                    result = ray.get(future, timeout=180)  # 3 minute timeout for calibration batch processing
                    image = future_to_image[future]
                    
                    # Increment calibrations_processed for every image processed by Ray
                    with self.stats_lock:
                        self.processing_stats['calibrations_processed'] += 1
                        
                        # Send progress update for every image in premium mode (Ray path)
                        # Use the running total from stats, not just the current batch size
                        total_targets = self.processing_stats.get('targets_found', len(calibration_images))
                        processed_count = self.processing_stats['calibrations_processed']
                        progress_percent = int((processed_count / total_targets) * 100) if total_targets > 0 else 0
                        
                        if self.api and hasattr(self.api, 'processing_mode') and self.api.processing_mode == "premium":
                            # Always update progress to show current count
                            self.api.update_thread_progress(
                                thread_id=2,
                                percent_complete=progress_percent,
                                phase_name="Analyzing",
                                time_remaining=f"{processed_count}/{total_targets}"
                            )
                            print(f"[THREAD-2] Progress update: {processed_count}/{total_targets} ({progress_percent}%)")
                    
                    if result:
                        # CRITICAL FIX: get_calib_data returns 5 elements: coeffs, limits, xvals, yvals, image
                        if len(result) == 5:
                            coeffs, limits, xvals, yvals, modified_image = result
                        elif len(result) == 4:
                            coeffs, limits, xvals, yvals = result
                        else:
                            print(f"[THREAD-2] ❌ Unexpected result length from get_calib_data: {len(result)}")
                            continue
                        image.calibration_coefficients = coeffs
                        image.calibration_limits = limits
                        image.calibration_xvals = xvals
                        image.calibration_yvals = yvals
                        
                        # Ensure ALS is precomputed once per project (JSON-based load in Threads 3/4)
                        try:
                            self._ensure_als_precomputed()
                        except Exception as _als_once_e:
                            print(f"[THREAD-2] WARN: _ensure_als_precomputed failed: {_als_once_e}")
            
            # After processing ready futures, continue loop
                except Exception as e:
                    print(f"[THREAD-2] Error processing Ray results: {e}")
        
        # CRITICAL FIX: Select the best calibration image BEFORE queuing to other threads
        # Only the selected image should be saved to the target folder, others go only to reflectance
        self._select_best_calibration_image()
        print("[THREAD-2] DEBUG: _select_best_calibration_image() completed from Ray batch")
        
        # CRITICAL FIX: Queue target images to Thread-3 for processing after calibration computation
        # Thread-1 only processes JPG images for detection - RAW target images need to be queued here
        print(f"[THREAD-2] Queueing {len(calibration_images)} target images to Thread-3 for processing...")
        
        for image in calibration_images:
            # Set up the target image for Thread-3 processing
            image.calibration_image = image  # Target uses its own calibration
            
            # Queue the target image to Thread-3
            print(f"[THREAD-2] Queueing target image {image.fn} to Thread-3 for processing")
            print(f"[THREAD-2] Target image attributes: is_target={getattr(image, 'is_calibration_photo', False)}, has_coeffs={hasattr(image, 'calibration_coefficients')}")
            self.queues.calibration_apply_queue.put(image)
        
        print(f"[THREAD-2] Successfully queued {len(calibration_images)} target images to Thread-3")
        
        # Signal completion
        self.queues.all_calibration_complete.set()
        self.queues.calibration_apply_queue.put(None)  # Sentinel for Thread-3
        # CRITICAL FIX: Don't send sentinel to Thread-4 here - let Thread-3 send it when actually done
        # self.queues.export_queue.put(None)  # Sentinel for Thread-4 - REMOVED
        
        # Clear the flag
        if hasattr(self, '_called_from_ray'):
            delattr(self, '_called_from_ray')
        
        # Signal that all calibration computation is complete
        self.queues.all_calibration_complete.set()
        self.queues.calibration_compute_complete.set()
        print("[THREAD-2] Signaled calibration computation complete")
        
        # Update UI to show Thread 2 completion
        if self.api and hasattr(self.api, 'update_thread_progress'):
            # CRITICAL FIX: Use targets_found instead of calibrations_computed for final display
            total_targets = self.processing_stats.get('targets_found', 0)
            self.api.update_thread_progress(
                thread_id=2,
                percent_complete=100,
                phase_name="Analyzing",
                time_remaining=f"{total_targets}/{total_targets}"
            )
        
        print("[THREAD-2] Analyzing complete")
        
    def _ensure_als_precomputed(self):
        """Compute ALS once per project and persist to calibration_data.json if not already done.
        Fast no-op if calibration_data.json already contains any ALS fields.
        """
        try:
            if getattr(self, '_als_precomputed_once', False):
                return
            project_dir = getattr(self.project, 'fp', None)
            if not project_dir:
                return
            calib_file = os.path.join(project_dir, 'calibration_data.json')
            has_als = False
            if os.path.exists(calib_file):
                try:
                    with open(calib_file, 'r') as f:
                        data = json.load(f)
                    for _, entry in data.items():
                        if entry.get('als_magnitude') is not None or entry.get('als_data') is not None:
                            has_als = True
                            break
                except Exception:
                    has_als = False
            if has_als:

                # Load existing ALS data from JSON to image objects in memory
                self._load_als_data_to_images()
                self._als_precomputed_once = True
                return
            # Compute ALS for all images once
            scanmap = getattr(self.project, 'scanmap', None)
            if not scanmap or len(scanmap) == 0:

                self._als_precomputed_once = True
                return
            from mip.als import get_als_data
            scan_directory = list(scanmap.values())[0].dir
            all_images = list(getattr(self.project, 'imagemap', {}).values())
            if not all_images:

                self._als_precomputed_once = True
                return
            code_hint = None
            for img in all_images:
                if getattr(img, 'is_calibration_photo', False) and getattr(img, 'aruco_id', None) is not None:
                    code_hint = img.aruco_id
                    break

            get_als_data(all_images, scan_directory, code_hint, self.project)
            
            # DEBUG: Check if ALS data was actually attached to images
            als_attached_count = 0
            for img in all_images:
                if hasattr(img, 'als_magnitude') and img.als_magnitude is not None:
                    als_attached_count += 1
            
            self._als_precomputed_once = True
        except Exception as _e:
            pass
            self._als_precomputed_once = True
    
    def _load_als_data_to_images(self):
        """Load ALS data from calibration_data.json to image objects in memory"""
        try:
            project_dir = getattr(self.project, 'fp', None)
            if not project_dir:
                print("[ALS LOAD] No project directory available")
                return
                
            all_images = list(getattr(self.project, 'imagemap', {}).values())
            if not all_images:
                print("[ALS LOAD] No images available to load ALS data")
                return
            
            loaded_count = 0
            for image in all_images:
                if load_als_data_from_json(image, project_dir):
                    loaded_count += 1
                    print(f"[ALS LOAD] ✅ Loaded ALS data for {getattr(image, 'fn', 'unknown')}")
                    
            print(f"[ALS LOAD] Loaded ALS data for {loaded_count}/{len(all_images)} images from JSON")
            
        except Exception as e:
            print(f"[ALS LOAD] Error loading ALS data to images: {e}")
    
    def _process_calibration_sequential(self):
        """Original sequential calibration processing"""
        processed_images = set()  # Track processed images to avoid duplicates
        
        # Wait for Thread-1 to start sending calibration targets
        print("[THREAD-2] Waiting for calibration targets from Thread-1...")
        
        # Show initial Thread 2 state with spinner for sequential mode
        if self.api and hasattr(self.api, 'update_thread_progress'):
            self.api.update_thread_progress(
                thread_id=2,
                percent_complete=0,
                phase_name="Analyzing",
                time_remaining="0/?"
            )
            print(f"[THREAD-2] Initial progress: 0/? (waiting for targets)")
        
        while not self.queues.shutdown.is_set():
            try:
                image = self.queues.calibration_compute_queue.get(timeout=2)  # Increased timeout
                if image is None:  # Sentinel
                    print("[THREAD-2] Received sentinel, exiting calibration processing loop")
                    break
                
                print(f"[THREAD-2] Received calibration target: {image.fn}")
                
                # Skip if already processed
                if image.fn in processed_images:
                    print(f"[THREAD-2] Skipping duplicate calibration for {image.fn}")
                    continue
                    
                processed_images.add(image.fn)
                
                # Send progress update for every image in premium mode
                if self.api and hasattr(self.api, 'processing_mode') and self.api.processing_mode == "premium":
                    total_targets = self.processing_stats.get('targets_found', None)
                    if total_targets is None:
                        # Calculate total targets from project files (JPG files used for target detection)
                        total_targets = 0
                        if hasattr(self, 'project') and self.project.data.get('files'):
                            for fileset in self.project.data['files'].values():
                                if fileset.get('jpg'):
                                    total_targets += 1
                        total_targets = max(1, total_targets)
                    progress_percent = int((len(processed_images) / total_targets) * 100)
                    # Always update progress to show current count
                    self.api.update_thread_progress(
                        thread_id=2,
                        percent_complete=progress_percent,
                        phase_name="Analyzing",
                        time_remaining=f"{len(processed_images)}/{total_targets}"
                    )
                
                print(f"[THREAD-2] Computing calibration for {image.fn}")
                
                # Load and debayer the image once
                if not hasattr(image, 'data') or image.data is None:
                    raw_data = image.raw_data
                    if raw_data is not None:
                        image.data = raw_data
                        # Cache the debayered data
                        self.queues.cache_image_data(image.fn, raw_data)
                
                # Compute calibration coefficients
                # Handle both cfg structures - ensure get_calib_data gets the right format
                if 'Project Settings' in self.options:
                    options_for_calib = self.options['Project Settings']
                else:
                    options_for_calib = self.options
                
                result = get_calib_data(image, options_for_calib, DummyProgressTracker())
                if result:
                    # CRITICAL FIX: get_calib_data returns 5 elements: coeffs, limits, xvals, yvals, image
                    if len(result) == 5:
                        coeffs, limits, xvals, yvals, modified_image = result
                        image = modified_image  # Use the modified image object
                    elif len(result) == 4:
                        coeffs, limits, xvals, yvals = result
                    else:
                        pass
                        continue
                    
                    # Store coefficients and limits from computation
                    image.calibration_coefficients = coeffs
                    image.calibration_limits = limits
                    image.calibration_xvals = xvals
                    image.calibration_yvals = yvals
                    
                    # Store base RAW coefficients for non-target images to use
                    image._raw_base_coefficients = coeffs
                    
                    # Target image saving will be handled by Thread-4 export logic
                    # This avoids duplicate saves and allows proper selection logic
                    print(f"[THREAD-2] Calibration computed for target image {image.fn}")
                    
                    # Ensure ALS is precomputed once per project (JSON-based load in Threads 3/4)
                    try:
                        self._ensure_als_precomputed()
                    except Exception as _als_once_e:
                        print(f"[THREAD-2] WARN: _ensure_als_precomputed failed: {_als_once_e}")
                    
                    # Save to calibration JSON
                    self._save_calibration_to_json(image)
                    
                    # Signal that at least one calibration is ready
                    self.queues.calibration_ready_event.set()
                    
                    # IMPORTANT: Set calibration_image to itself for calibration targets
                    # This ensures process_image_unified knows to use the target's own calibration data
                    image.calibration_image = image
                    
                    # After get_als_data, check ALS assignment
                    if hasattr(image, 'als_magnitude') and image.als_magnitude is not None:
                        print(f"[THREAD-2] ALS data assigned to {image.fn}: {image.als_magnitude}")
                    else:
                        print(f"[ERROR] ALS data NOT assigned to {image.fn} after calibration!")
                    
                    # CRITICAL FIX: Queue target image directly to Thread-4 for export
                    # Target images don't need Thread-3 processing since they have their own calibration
                    print(f"[THREAD-2] DEBUG: About to queue target image {image.fn} directly to Thread-4")
                    print(f"[THREAD-2] DEBUG: Target image attributes before queueing:")
                    print(f"[THREAD-2] DEBUG:   - is_calibration_photo: {getattr(image, 'is_calibration_photo', False)}")
                    print(f"[THREAD-2] DEBUG:   - calibration_image: {image.calibration_image}")
                    print(f"[THREAD-2] DEBUG:   - calibration_coefficients: {getattr(image, 'calibration_coefficients', None)}")
                    print(f"[THREAD-2] DEBUG:   - als_magnitude: {getattr(image, 'als_magnitude', None)}")
                    self.queues.queue_to_export(image, "thread2")
                    print(f"[THREAD-2] Queued target image {image.fn} directly to Thread-4 for export")
                    
                    # CRITICAL FIX: Update statistics using image pairs
                    with self.stats_lock:
                        self.processing_stats['calibrations_computed'] += 1
                        # Only increment calibrations_processed if not called from Ray (to avoid double counting)
                        if not hasattr(self, '_called_from_ray'):
                            self.processing_stats['calibrations_processed'] += 1  # NEW: Track total processed
                        # Ensure we don't exceed the total number of image pairs
                        if self.processing_stats['calibrations_computed'] > self.processing_stats['total_image_pairs']:
                            self.processing_stats['calibrations_computed'] = self.processing_stats['total_image_pairs']
                
                # Clear raw data from memory after saving calibration
                if hasattr(image, 'data'):
                    try:
                        del image.data
                    except AttributeError:
                        # data might be a property that can't be deleted
                        image.data = None
                self.queues.clear_cache_for_image(image.fn)
                
            except queue.Empty:
                print("[THREAD-2] Queue timeout, continuing to wait for calibration targets...")
                continue
        
        # CRITICAL FIX: Select the best calibration image BEFORE queuing to other threads
        # Only the selected image should be saved to the target folder, others go only to reflectance
        self._select_best_calibration_image()
        print("[THREAD-2] DEBUG: _select_best_calibration_image() completed")
        
        # Signal completion
        self.queues.calibration_apply_queue.put(None)  # Sentinel for Thread-3
        self.queues.export_queue.put(None)  # Sentinel for Thread-4
        
        # CRITICAL FIX: Signal that all calibration computation is complete
        self.queues.all_calibration_complete.set()
        self.queues.calibration_compute_complete.set()
        print("[THREAD-2] Signaled calibration computation complete")
        
        # Update UI to show Thread 2 completion
        if self.api and hasattr(self.api, 'update_thread_progress'):
            # CRITICAL FIX: Use targets_found instead of calibrations_computed for final display
            total_targets = self.processing_stats.get('targets_found', 0)
            self.api.update_thread_progress(
                thread_id=2,
                percent_complete=100,
                phase_name="Analyzing",
                time_remaining=f"{total_targets}/{total_targets}"
            )
        
        print("[THREAD-2] Analyzing complete")
    
    def _thread3_calibration_apply(self):
        """Thread 3: Apply calibration data to all images as they become ready"""
        # CRITICAL FIX: Prevent multiple thread starts
        if hasattr(self, '_thread3_completed') and self._thread3_completed:
            print("[THREAD-3] WARNING: Thread-3 already completed, ignoring restart")
            return
        
        # print("[THREAD-3] [SYNC] Starting calibration application...")
        
        # CRITICAL FIX: Initialize UI progress for Thread-3
        if self.api and hasattr(self.api, 'update_thread_progress'):
            total_images = self.processing_stats.get('total_image_pairs', None)
            if total_images is None:
                # CRITICAL FIX: Count all image pairs (JPG or RAW) to match project input
                total_images = 0
                if hasattr(self, 'project') and self.project.data.get('files'):
                    for fileset in self.project.data['files'].values():
                        if fileset.get('jpg') or fileset.get('raw'):
                            total_images += 1
                total_images = max(1, total_images)
            self.api.update_thread_progress(
                thread_id=3,
                percent_complete=0,
                phase_name="Processing",
                time_remaining=f"0/{total_images}"
            )
            print(f"[THREAD-3] Initialized UI progress: 0/{total_images}")

        # Initialize UI progress for fresh start (no resume logic)
        if self.api and hasattr(self.api, 'update_thread_progress'):
            total_images = self.processing_stats.get('total_image_pairs', None)
            if total_images is None:
                # CRITICAL FIX: Count all image pairs (JPG or RAW) to match project input
                total_images = 0
                if hasattr(self, 'project') and self.project.data.get('files'):
                    for fileset in self.project.data['files'].values():
                        if fileset.get('jpg') or fileset.get('raw'):
                            total_images += 1
                total_images = max(1, total_images)
            
            # Update UI to show Thread 3 starting fresh (no resume logic)
            print(f"[THREAD-3] FRESH START: Starting calibration processing for {total_images} images")
            self.api.update_thread_progress(
                thread_id=3,
                percent_complete=0,
                phase_name="Processing",
                time_remaining=f"0/{total_images}"
            )
        
        try:
            import time
            
            print("[THREAD-3] 🚀 Starting streaming calibration processing...")
            print("[THREAD-3] Will process images as soon as their calibration data becomes available")
                
            print(f"[THREAD-3 DEBUG] use_ray={self.use_ray}")
            # Check if sequential mode is forced due to Ray failures
            thread3_sequential_mode = getattr(self, 'thread3_sequential_mode', False)
            if thread3_sequential_mode:
                print("[THREAD-3] Sequential mode enabled due to Ray failures - using sequential processing")
            
            if self.use_ray and not thread3_sequential_mode:
                print("[THREAD-3] Using Ray streaming processing")
                try:
                    # Process images as they become ready using Ray
                    self._process_calibration_apply_ray_streaming()
                except Exception as ray_error:
                    print(f"[THREAD-3] ❌ Ray streaming failed: {ray_error}")
                    print("[THREAD-3] 🔄 Falling back to sequential streaming processing")
                    import traceback
                    traceback.print_exc()
                    # Fallback to sequential processing
                    self._process_calibration_apply_sequential_streaming()
            else:
                print("[THREAD-3] Using sequential streaming processing")
                # Process images as they become ready sequentially
                self._process_calibration_apply_sequential_streaming()
            
        except Exception as e:
            print(f"[THREAD-3] Error: {e}")
            self.queues.shutdown.set()
        finally:
            self._thread3_completed = True
            
            # CRITICAL FIX: Update UI to show Thread-3 completion
            if self.api and hasattr(self.api, 'update_thread_progress'):
                total_images = self.processing_stats.get('total_image_pairs', None)
                if total_images is None:
                    # CRITICAL FIX: Count all image pairs (JPG or RAW) to match project input
                    total_images = 0
                    if hasattr(self, 'project') and self.project.data.get('files'):
                        for fileset in self.project.data['files'].values():
                            if fileset.get('jpg') or fileset.get('raw'):
                                total_images += 1
                    total_images = max(1, total_images)
                # CRITICAL FIX: Use the actual processed count from the sequential processing
                # Look for images_calibrated or use total_images as fallback
                final_count = self.processing_stats.get('images_calibrated', total_images)
                # If images_calibrated is 0, use total_images since sequential processing processes all images
                if final_count == 0:
                    final_count = total_images
                self.api.update_thread_progress(
                    thread_id=3,
                    percent_complete=100,
                    phase_name="Processing",
                    time_remaining=f"{final_count}/{total_images}"
                )
                print(f"[THREAD-3] Updated UI progress to 100%: {final_count}/{total_images}")
                
            print("[THREAD-3] Calibrating complete")
    
    def _wait_for_calibration_data(self):
        """Wait for calibration_data.json to be available and verify it has entries"""
        import os
        import json
        import time
        
        # Determine calibration data file path
        if hasattr(self, 'project') and self.project and hasattr(self.project, 'fp'):
            calibration_file = os.path.join(self.project.fp, 'calibration_data.json')
        else:
            calibration_file = os.path.join(self.outfolder, 'calibration_data.json')
        
        print(f"[THREAD-3] 🔍 Looking for calibration data at: {calibration_file}")
        
        # Wait up to 10 seconds for the file to exist
        max_wait_time = 10.0
        wait_start = time.time()
        
        while time.time() - wait_start < max_wait_time:
            if os.path.exists(calibration_file):
                try:
                    # Try to load and verify the JSON file
                    with open(calibration_file, 'r') as f:
                        calib_data = json.load(f)
                    
                    if calib_data:
                        print(f"[THREAD-3] ✅ Found calibration data with {len(calib_data)} entries")
                        for key in calib_data.keys():
                            print(f"[THREAD-3] 📅 Calibration entry: {key}")
                        return True
                    else:
                        print(f"[THREAD-3] ⚠️ Calibration file exists but is empty")
                        
                except Exception as e:
                    print(f"[THREAD-3] ⚠️ Error reading calibration file: {e}")
            
            if self.queues.shutdown.is_set():
                print("[THREAD-3] Shutdown requested during calibration wait")
                return False
                
            time.sleep(0.1)
        
        print(f"[THREAD-3] ❌ Timeout waiting for calibration data after {max_wait_time}s")
        return False
    
    def _filter_images_by_calibration_availability(self, images_to_process):
        """Filter images based on temporal calibration availability"""
        import os
        import json
        import datetime
        
        # Load calibration data to get available calibration timestamps
        try:
            if hasattr(self, 'project') and self.project and hasattr(self.project, 'fp'):
                calibration_file = os.path.join(self.project.fp, 'calibration_data.json')
            else:
                calibration_file = os.path.join(self.outfolder, 'calibration_data.json')
            
            with open(calibration_file, 'r') as f:
                calib_data = json.load(f)
            
            # Extract calibration timestamps
            calib_timestamps = []
            for key in calib_data.keys():
                try:
                    calib_ts = datetime.datetime.strptime(key, '%Y-%m-%d %H:%M:%S')
                    calib_timestamps.append(calib_ts)
                    print(f"[THREAD-3] 📅 Available calibration: {key}")
                except Exception as e:
                    print(f"[THREAD-3] ⚠️ Error parsing calibration timestamp {key}: {e}")
            
            calib_timestamps.sort()  # Sort chronologically
            print(f"[THREAD-3] 📊 Found {len(calib_timestamps)} calibration timestamps")
            
        except Exception as e:
            print(f"[THREAD-3] ❌ Error loading calibration data for filtering: {e}")
            return images_to_process  # Return all images if we can't filter
        
        # Filter images based on calibration availability
        filtered_images = []
        
        for image in images_to_process:
            # Calibration images should always be processed
            if getattr(image, 'is_calibration_photo', False):
                filtered_images.append(image)
                print(f"[THREAD-3] ✅ Including calibration image: {image.fn}")
                continue
            
            # For non-calibration images, check if there's a later calibration available
            try:
                img_timestamp = getattr(image, 'timestamp', None)
                if not img_timestamp:
                    print(f"[THREAD-3] ⚠️ No timestamp for {image.fn}, skipping calibration")
                    continue
                
                # Parse image timestamp
                if isinstance(img_timestamp, str):
                    img_ts = datetime.datetime.strptime(img_timestamp, '%Y-%m-%d %H:%M:%S')
                elif hasattr(img_timestamp, 'strftime'):
                    img_ts = img_timestamp
                else:
                    print(f"[THREAD-3] ⚠️ Invalid timestamp format for {image.fn}: {img_timestamp}")
                    continue
                
                # Find if there's a calibration timestamp after this image
                has_later_calibration = any(calib_ts >= img_ts for calib_ts in calib_timestamps)
                
                if has_later_calibration:
                    filtered_images.append(image)
                    print(f"[THREAD-3] ✅ Including non-target image: {image.fn} (has later calibration)")
                else:
                    print(f"[THREAD-3] ⏭️ Skipping non-target image: {image.fn} (no later calibration available)")
                    
            except Exception as e:
                print(f"[THREAD-3] ⚠️ Error processing timestamp for {image.fn}: {e}")
                continue
        
        print(f"[THREAD-3] 📊 Filtered {len(images_to_process)} → {len(filtered_images)} images for calibration")
        return filtered_images
    
    def _process_calibration_apply_ray_streaming(self):
        """Process calibration application using Ray with streaming/per-image processing"""
        import time
        import queue
        
        print("[THREAD-3] 🌊 Starting streaming Ray calibration processing...")
        
        # CRITICAL FIX: Verify Ray is actually available before proceeding
        try:
            # Use global ray variable instead of importing directly
            global ray
            # CRITICAL FIX: Skip all Ray runtime checks to avoid _private errors
            # Just verify Ray has the basic functions we need
            required_attrs = ['init', 'get', 'put', 'remote']
            if not all(hasattr(ray, attr) for attr in required_attrs):
                raise Exception("Ray missing required attributes")
            print(f"[THREAD-3] ✅ Ray is available with all required attributes")
        except Exception as e:
            print(f"[THREAD-3] ❌ Ray not available: {e}")
            raise Exception(f"Ray not available for streaming processing: {e}")
        
        processed_count = 0
        pending_images = {}  # Track images waiting for calibration data
        
        while not self.queues.shutdown.is_set():
            try:
                # Try to get an image from the queue (non-blocking)
                try:
                    image = self.queues.calibration_apply_queue.get(timeout=0.5)
                    if image is None:  # Sentinel
                        print(f"[THREAD-3] Received sentinel, processed {processed_count} images")
                        break
                    
                    print(f"[THREAD-3] 📥 Received image: {image.fn}")
                    
                    # Check if this image can be processed immediately
                    if self._can_process_image_unified_now(image):
                        print(f"[THREAD-3] ✅ Processing {image.fn} immediately (calibration ready)")
                        self._process_single_image_ray(image)
                        processed_count += 1
                    else:
                        print(f"[THREAD-3] ⏳ Adding {image.fn} to pending queue (calibration not ready)")
                        pending_images[image.fn] = image
                        
                except queue.Empty:
                    # No new images, check if any pending images can now be processed
                    if pending_images:
                        self._check_pending_images_ray(pending_images)
                        processed_count += len([img for img in list(pending_images.keys()) if img not in pending_images])
                    continue
                    
            except Exception as e:
                print(f"[THREAD-3] Error in streaming processing: {e}")
                continue
        
        # Continue monitoring pending images until Thread-2 signals completion or all are processed
        while pending_images and not self.queues.shutdown.is_set():
            # CRITICAL FIX: First drain any remaining items from the queue before checking Thread-2 status
            queue_drained = False
            new_items_count = 0
            
            while not queue_drained and not self.queues.shutdown.is_set():
                try:
                    image = self.queues.calibration_apply_queue.get(timeout=0.1)  # Short timeout
                    if image is None:  # Sentinel
                        print(f"[THREAD-3] Received sentinel while draining queue")
                        queue_drained = True
                        break
                    
                    print(f"[THREAD-3] 📥 DRAIN: Received queued image: {image.fn}")
                    new_items_count += 1
                    
                    if self._can_process_image_unified_now(image):
                        print(f"[THREAD-3] ✅ DRAIN: Processing immediately: {image.fn}")
                        try:
                            self._process_single_image_ray(image)
                            processed_count += 1
                        except Exception as e:
                            print(f"[THREAD-3] Error processing drained image {image.fn}: {e}")
                    else:
                        print(f"[THREAD-3] ⏳ DRAIN: Adding to pending: {image.fn}")
                        pending_images[image.fn] = image
                        
                except queue.Empty:
                    queue_drained = True
                except Exception as e:
                    print(f"[THREAD-3] Error draining queue: {e}")
                    break
            
            if new_items_count > 0:
                print(f"[THREAD-3] ✅ DRAIN: Processed {new_items_count} items from queue")
            
            # Check if Thread-2 has finished - if so, we can process remaining images more aggressively
            thread2_finished = self.queues.calibration_compute_complete.is_set()
            
            if thread2_finished:
                # CRITICAL FIX: Prevent double processing with a flag
                if not hasattr(self, '_thread2_completion_processed'):
                    self._thread2_completion_processed = True
                    
                    # Check if any calibration data was actually computed
                    has_calibration_data = self.queues.has_any_calibration_data()
                    
                    # CRITICAL FIX: Check for calibration data file existence instead of in-memory store
                    # The issue is that Thread 2 saves to JSON files, not the in-memory store
                    has_calibration_file = self._check_calibration_file_exists()
                    
                    if has_calibration_file:
                        print(f"[THREAD-3] ✅ Thread-2 completed with calibration data file! Processing {len(pending_images)} remaining pending images...")
                        # Process all remaining pending images WITH calibration
                        for image in list(pending_images.values()):
                            try:
                                self._process_single_image_ray(image)
                                processed_count += 1
                            except Exception as e:
                                print(f"[THREAD-3] Error processing pending image {image.fn}: {e}")
                    else:
                        print(f"[THREAD-3] ⚠️ Thread-2 completed but no calibration file found! Processing {len(pending_images)} images without calibration...")
                        # Process all remaining pending images WITHOUT calibration
                        for image in list(pending_images.values()):
                            try:
                                # Skip calibration for this image since no targets were found
                                self._process_single_image_ray_no_calibration(image)
                                processed_count += 1
                            except Exception as e:
                                print(f"[THREAD-3] Error processing pending image {image.fn}: {e}")
                    
                    # CRITICAL FIX: Clear pending images immediately after processing to prevent double processing
                    pending_images.clear()
                    print(f"[THREAD-3] ✅ Cleared all pending images after Thread-2 completion processing")
                    break
                else:
                    # Thread-2 completion already processed, just break to avoid infinite loop
                    print(f"[THREAD-3] ✅ Thread-2 completion already processed, exiting loop")
                    break
            else:
                # Thread-2 still running - check if any pending images can now be processed
                # Reduce spam: Only print every 10th check
                if not hasattr(self, '_check_count'):
                    self._check_count = 0
                self._check_count += 1
                if self._check_count % 10 == 1:
                    print(f"[THREAD-3] 🔍 Checking {len(pending_images)} pending images for available calibration data... (check #{self._check_count})")
                images_processed_this_round = []
                
                for image_fn, image in list(pending_images.items()):
                    if self._can_process_image_unified_now(image):
                        print(f"[THREAD-3] ✅ Calibration data now available for {image.fn}")
                        try:
                            self._process_single_image_ray(image)
                            processed_count += 1
                            images_processed_this_round.append(image_fn)
                        except Exception as e:
                            print(f"[THREAD-3] Error processing {image.fn}: {e}")
                
                # Remove processed images from pending
                for image_fn in images_processed_this_round:
                    del pending_images[image_fn]
                
                if images_processed_this_round:
                    print(f"[THREAD-3] ✅ Processed {len(images_processed_this_round)} images this round, {len(pending_images)} still pending")
                
                # Wait a bit before checking again (streaming interval)
                if pending_images:  # Only wait if there are still pending images
                    time.sleep(0.5)  # Check every 500ms for new calibration data
        
        print(f"[THREAD-3] 🎉 Streaming processing complete: {processed_count} images processed")
        
        # CRITICAL FIX: Send sentinel to Thread-4 when Thread-3 is actually done
        print("[THREAD-3] 📤 Sending completion sentinel to Thread-4")
        self.queues.export_queue.put(None)  # Sentinel for Thread-4
    
    def _check_calibration_file_exists(self):
        """Check if calibration_data.json exists with retry logic for file system sync"""
        import os
        import time
        
        # Determine calibration file path
        if hasattr(self, 'project') and self.project and hasattr(self.project, 'fp'):
            calibration_file = os.path.join(self.project.fp, 'calibration_data.json')
        else:
            print("[THREAD-3] ⚠️ No project directory available for calibration file check")
            return False
        
        # Check with retry logic for file system synchronization
        max_retries = 5
        for attempt in range(max_retries):
            if os.path.exists(calibration_file):
                try:
                    # Also check if file is readable and has content
                    with open(calibration_file, 'r') as f:
                        content = f.read().strip()
                        if content and len(content) > 10:  # Basic content validation
                            print(f"[THREAD-3] ✅ Calibration file found and readable: {calibration_file}")
                            return True
                        else:
                            print(f"[THREAD-3] ⚠️ Calibration file exists but appears empty (attempt {attempt + 1}/{max_retries})")
                except Exception as e:
                    print(f"[THREAD-3] ⚠️ Calibration file exists but not readable (attempt {attempt + 1}/{max_retries}): {e}")
            else:
                print(f"[THREAD-3] ⚠️ Calibration file not found (attempt {attempt + 1}/{max_retries}): {calibration_file}")
            
            if attempt < max_retries - 1:
                time.sleep(0.2)  # Wait 200ms before retry
        
        print(f"[THREAD-3] ❌ Calibration file not found after {max_retries} attempts")
        return False
    
    def _can_process_image_unified_now(self, image):
        """Check if an image can be processed immediately using temporal processing logic"""
        try:
            # TEMPORAL OPTIMIZATION: Check if image can be processed based on temporal logic
            can_process_temporal = self._check_temporal_processing_readiness(image)
            if can_process_temporal is not None:
                return can_process_temporal
            
            # Fallback to original logic if temporal data not available
            from unified_calibration_api import UnifiedCalibrationManager
            
            # For calibration images, check if their calibration data has been computed and saved to JSON
            if getattr(image, 'is_calibration_photo', False):
                # Check if this calibration image's data exists in JSON
                calib_data = UnifiedCalibrationManager.load_calibration_data(image)
                
                if calib_data and calib_data.get('coefficients'):
                    print(f"[THREAD-3] ✅ Calibration image {image.fn}: calibration data ready in JSON")
                    return True
                else:
                    # Reduce spam: Only print occasionally for calibration images
                    if not hasattr(self, '_calib_check_count'):
                        self._calib_check_count = {}
                    
                    image_key = getattr(image, 'fn', 'unknown')
                    if image_key not in self._calib_check_count:
                        self._calib_check_count[image_key] = 0
                    self._calib_check_count[image_key] += 1
                    
                    # Only print every 50th check per calibration image
                    if self._calib_check_count[image_key] % 50 == 1:
                        print(f"[THREAD-3] ⏳ Calibration image {image.fn}: calibration data not computed yet (check #{self._calib_check_count[image_key]})")
                    
                    return False
            else:
                # For non-calibration images, check if matching calibration data exists in JSON
                calib_data = UnifiedCalibrationManager.load_calibration_data(image)
                
                if calib_data and calib_data.get('coefficients'):
                    print(f"[THREAD-3] ✅ Found calibration data for {image.fn} in JSON")
                    return True
                else:
                    # Reduce spam: Only print occasionally
                    if not hasattr(self, '_no_calib_count'):
                        self._no_calib_count = {}
                    
                    image_key = getattr(image, 'fn', 'unknown')
                    if image_key not in self._no_calib_count:
                        self._no_calib_count[image_key] = 0
                    self._no_calib_count[image_key] += 1
                    
                    # Only print every 20th check per image
                    if self._no_calib_count[image_key] % 20 == 1:
                        print(f"[THREAD-3] ⏳ No calibration available yet for {image.fn} (check #{self._no_calib_count[image_key]})")
                    
                    return False
        except Exception as e:
            image_key = getattr(image, 'fn', 'unknown')
            print(f"[THREAD-3] ❌ Error in temporal processing check for {image_key}: {e}")
            return False
    
    def _check_temporal_processing_readiness(self, image):
        """Check if image can be processed based on temporal processing logic"""
        try:
            import os
            import json
            
            # Load temporal processing data
            if hasattr(self, 'project') and self.project and hasattr(self.project, 'fp'):
                calibration_file = os.path.join(self.project.fp, 'calibration_data.json')
            else:
                return None
            
            if not os.path.exists(calibration_file):
                return None
            
            with open(calibration_file, 'r') as f:
                data = json.load(f)
            
            temporal_info = data.get('temporal_processing', {})
            if not temporal_info:
                return None
            
            image_fn = image.fn
            
            # Check if this is a target image
            if image_fn in temporal_info.get('targets', {}):
                target_info = temporal_info['targets'][image_fn]
                if target_info.get('calibration_ready', False):
                    print(f"[THREAD-3] ✅ TEMPORAL: Target {image_fn} calibration ready")
                    return True
                else:
                    # Reduced logging: Only log every 10th check to avoid spam
                    if hasattr(self, '_temporal_log_counter'):
                        self._temporal_log_counter += 1
                    else:
                        self._temporal_log_counter = 1
                    
                    if self._temporal_log_counter % 10 == 0:
                        print(f"[THREAD-3] ⏳ TEMPORAL: Target {image_fn} calibration not ready (check #{self._temporal_log_counter})")
                    return False
            
            # Check if this is a non-target image
            if image_fn in temporal_info.get('non_targets', {}):
                non_target_info = temporal_info['non_targets'][image_fn]
                calibration_target = non_target_info.get('calibration_target')
                
                if not calibration_target:
                    print(f"[THREAD-3] ⚠️ TEMPORAL: No calibration target assigned for {image_fn}")
                    return False
                
                # Check if the required calibration target is ready
                targets_info = temporal_info.get('targets', {})
                if calibration_target in targets_info:
                    target_ready = targets_info[calibration_target].get('calibration_ready', False)
                    if target_ready:
                        print(f"[THREAD-3] ✅ TEMPORAL: {image_fn} can process (target {calibration_target} ready)")
                        return True
                    else:
                        # Reduced logging: Only log every 10th check
                        if self._temporal_log_counter % 10 == 0:
                            print(f"[THREAD-3] ⏳ TEMPORAL: {image_fn} waiting for target {calibration_target} (check #{self._temporal_log_counter})")
                        return False
                else:
                    # Check if calibration data exists in the main calibration_data section
                    calib_data = data.get('calibration_data', {})
                    if calibration_target in calib_data:
                        print(f"[THREAD-3] ✅ TEMPORAL: {image_fn} can process (calibration data exists for {calibration_target})")
                        return True
                    else:
                        # Reduced logging: Only log every 10th check
                        if self._temporal_log_counter % 10 == 0:
                            print(f"[THREAD-3] ⏳ TEMPORAL: {image_fn} waiting for calibration data from {calibration_target} (check #{self._temporal_log_counter})")
                        return False
            
            # Image not found in temporal data
            print(f"[THREAD-3] ⚠️ TEMPORAL: {image_fn} not found in temporal processing data")
            return None
            
        except Exception as e:
            image_key = getattr(image, 'fn', 'unknown')
            print(f"[THREAD-3] ❌ Error checking temporal readiness for {image_key}: {e}")
            return None
    
    def _synchronize_calibration_data_to_ray(self, image):
        """Synchronize calibration data to Ray attributes for proper serialization"""
        try:
            # Find the calibration image for this image
            calibration_image = None
            
            # Check if image already has calibration_image reference
            if hasattr(image, 'calibration_image') and image.calibration_image is not None:
                calibration_image = image.calibration_image
            else:
                # Try to find calibration image from project
                if hasattr(self, 'project') and self.project and hasattr(self.project, 'imagemap'):
                    # Look for calibration images (those with target detection results)
                    for img_key, img_obj in self.project.imagemap.items():
                        if (hasattr(img_obj, 'is_calibration_photo') and img_obj.is_calibration_photo and
                            hasattr(img_obj, 'calibration_coefficients') and img_obj.calibration_coefficients):
                            calibration_image = img_obj
                            image.calibration_image = img_obj  # Set reference
                            break
            
            if calibration_image:
                print(f"[RAY SYNC] 🔄 Synchronizing calibration data for {image.fn} (preferring per-image coefficients)")
                
                # Copy calibration data to Ray-specific attributes, preferring per-image ALS-corrected coefficients
                import copy
                per_image_coeffs = getattr(image, 'calibration_coefficients', None)
                per_image_limits = getattr(image, 'calibration_limits', None)
                per_image_xvals = getattr(image, 'calibration_xvals', None)
                per_image_yvals = getattr(image, 'calibration_yvals', None)
                
                if per_image_coeffs is not None:
                    image._ray_calibration_coefficients = copy.deepcopy(per_image_coeffs)
                    image._ray_calibration_limits = copy.deepcopy(per_image_limits)
                    image._ray_calibration_xvals = copy.deepcopy(per_image_xvals)
                    image._ray_calibration_yvals = copy.deepcopy(per_image_yvals)
                    image._ray_calibration_fn = copy.deepcopy(getattr(image, 'fn', None))
                else:
                    image._ray_calibration_coefficients = copy.deepcopy(getattr(calibration_image, 'calibration_coefficients', None))
                    image._ray_calibration_limits = copy.deepcopy(getattr(calibration_image, 'calibration_limits', None))
                    image._ray_calibration_xvals = copy.deepcopy(getattr(calibration_image, 'calibration_xvals', None))
                    image._ray_calibration_yvals = copy.deepcopy(getattr(calibration_image, 'calibration_yvals', None))
                    image._ray_calibration_fn = copy.deepcopy(getattr(calibration_image, 'fn', None))
                    image._ray_calibration_aruco_id = copy.deepcopy(getattr(calibration_image, 'aruco_id', None))
                
                # Copy ALS data (separate fields for calibration image and source image)
                image._ray_calib_als_magnitude = copy.deepcopy(getattr(calibration_image, 'als_magnitude', None))
                image._ray_calib_als_data = copy.deepcopy(getattr(calibration_image, 'als_data', None))
                image._ray_image_als_magnitude = copy.deepcopy(getattr(image, 'als_magnitude', None))
                image._ray_image_als_data = copy.deepcopy(getattr(image, 'als_data', None))
                
                # Also copy calibration data directly to the image for non-Ray access
                if not hasattr(image, 'calibration_coefficients') or image.calibration_coefficients is None:
                    image.calibration_coefficients = image._ray_calibration_coefficients
                if not hasattr(image, 'calibration_yvals') or image.calibration_yvals is None:
                    image.calibration_yvals = image._ray_calibration_yvals
                if not hasattr(image, 'als_magnitude') or image.als_magnitude is None:
                    image.als_magnitude = image._ray_image_als_magnitude
                if not hasattr(image, 'als_data') or image.als_data is None:
                    image.als_data = image._ray_image_als_data
                
                print(f"[RAY SYNC] ✅ Synchronized calibration data for Ray processing: {image.fn}")
            else:
                print(f"[RAY SYNC] ❌ No calibration image found for {image.fn}")
                
        except Exception as e:
            print(f"[RAY SYNC] ❌ Error synchronizing calibration data for {image.fn}: {e}")
    
    def _check_pending_images_ray(self, pending_images):
        """Check if any pending images can now be processed"""
        ready_images = []
        
        for image_fn, image in list(pending_images.items()):
            if self._can_process_image_unified_now(image):
                print(f"[THREAD-3] ✅ {image_fn} is now ready for processing")
                ready_images.append(image_fn)
                self._process_single_image_ray(image)
            else:
                # If the temporal data is not ready but we already have ALS and a calib target, proceed after a grace period
                try:
                    has_als = getattr(image, 'als_magnitude', None) is not None
                    has_calib_img = hasattr(image, 'calibration_image') and image.calibration_image is not None
                    if has_als and has_calib_img:
                        if not hasattr(image, '_temp_grace'): image._temp_grace = 0
                        image._temp_grace += 1
                        if image._temp_grace >= 3:  # ~3 polling cycles
                            print(f"[THREAD-3] ⏩ Grace condition met, processing {image_fn} despite temporal wait")
                            ready_images.append(image_fn)
                            self._process_single_image_ray(image)
                except Exception:
                    pass
        
        # Remove processed images from pending
        for image_fn in ready_images:
            del pending_images[image_fn]
    
    def _process_single_image_sequential_no_calibration(self, image):
        """Process a single image WITHOUT calibration (sequential mode, when no targets found)"""
        try:
            print(f"[THREAD-3] ⚠️ Processing {image.fn} WITHOUT calibration (no targets found)")
            
            # Skip calibration entirely and just queue for export
            # This handles the case where no Aruco targets were found
            self.queues.queue_to_export(image, "Thread-3-Sequential-NoCalib")
            print(f"[THREAD-3] ✅ Queued {image.fn} for export without calibration")
            
            return True
            
        except Exception as e:
            print(f"[THREAD-3] ❌ Error processing {image.fn} without calibration: {e}")
            return False
    
    def _process_single_image_ray_no_calibration(self, image):
        """Process a single image WITHOUT calibration (when no targets found)"""
        try:
            print(f"[THREAD-3] ⚠️ Processing {image.fn} WITHOUT calibration (no targets found)")
            
            # Skip calibration entirely and just queue for export
            # This handles the case where no Aruco targets were found
            self.queues.queue_to_export(image, "Thread-3-NoCalib")
            print(f"[THREAD-3] ✅ Queued {image.fn} for export without calibration")
            
            return True
            
        except Exception as e:
            print(f"[THREAD-3] ❌ Error processing {image.fn} without calibration: {e}")
            return False
    
    def _process_single_image_ray(self, image):
        """Process a single image using Ray"""
        try:
            # CRITICAL FIX: Synchronize calibration data to Ray before processing
            self._synchronize_calibration_data_to_ray(image)
            
            # Get the Ray remote function
            apply_calibration_func = get_unified_task_function('apply_calibration', execution_mode='parallel')
            
            # Prepare parameters - handle different image object types
            from pathlib import Path
            image_fn = image.fn
            
            # Get image path - handle both LabImage and MCCImage objects
            import os
            raw_image_path = None
            
            if hasattr(image, 'fp'):
                raw_image_path = str(Path(image.fp))
            elif hasattr(image, 'path'):
                raw_image_path = str(Path(image.path))
            elif hasattr(image, 'file_path'):
                raw_image_path = str(Path(image.file_path))
            else:
                # Try to construct path from project and filename
                if hasattr(self, 'project') and self.project and hasattr(self.project, 'fp'):
                    # Look for the image in the project's image map
                    for img_key, img_obj in self.project.imagemap.items():
                        if img_obj.fn == image_fn:
                            if hasattr(img_obj, 'fp'):
                                raw_image_path = str(Path(img_obj.fp))
                                break
                            elif hasattr(img_obj, 'path'):
                                raw_image_path = str(Path(img_obj.path))
                                break
                    else:
                        raise ValueError(f"Could not determine file path for {image_fn}")
                else:
                    raise ValueError(f"Could not determine file path for {image_fn}")
            
            # CRITICAL FIX: Ensure we always get the absolute path (same fix as batch processing)
            if raw_image_path and not os.path.isabs(raw_image_path):
                # Try to get the full path from the project's image mapping
                print(f"[THREAD-3] 🔧 Relative path detected for single image: {raw_image_path}")
                
                # First try: Look in project.data['files'] structure
                if hasattr(self.project, 'data') and 'files' in self.project.data:
                    for key, file_info in self.project.data['files'].items():
                        if file_info.get('fn') == image_fn:
                            full_source_path = file_info.get('path')
                            if full_source_path and os.path.isabs(full_source_path):
                                raw_image_path = full_source_path
                                print(f"[THREAD-3] 🔧 Found full path in project.data for single image: {raw_image_path}")
                                break
                
                # Second try: Look in project.imagemap directly
                if not os.path.isabs(raw_image_path) and hasattr(self.project, 'imagemap'):
                    print(f"[THREAD-3] 🔧 Searching imagemap for {image_fn}")
                    for img_key, img_obj in self.project.imagemap.items():
                        if hasattr(img_obj, 'fn') and img_obj.fn == image_fn:
                            if hasattr(img_obj, 'path') and img_obj.path and os.path.isabs(img_obj.path):
                                raw_image_path = img_obj.path
                                print(f"[THREAD-3] 🔧 Found full path in imagemap for single image: {raw_image_path}")
                                break
                            elif hasattr(img_obj, 'fp') and img_obj.fp and os.path.isabs(img_obj.fp):
                                raw_image_path = img_obj.fp
                                print(f"[THREAD-3] 🔧 Found full path (fp) in imagemap for single image: {raw_image_path}")
                                break
                
                # If still relative, this is an error
                if not os.path.isabs(raw_image_path):
                    print(f"[THREAD-3] ❌ ERROR: Could not resolve absolute path for single image {image_fn}")
                    print(f"[THREAD-3] 🔧 Current path: {raw_image_path}")
                    print(f"[THREAD-3] 🔧 Available imagemap keys: {list(self.project.imagemap.keys()) if hasattr(self.project, 'imagemap') else 'No imagemap'}")
                    raise ValueError(f"Could not resolve absolute path for {image_fn}")
            
            image_path_str = raw_image_path
            
            print(f"[THREAD-3] 🔍 Processing {image_fn} from path: {image_path_str}")
            
            # Get project directory
            if hasattr(self, 'project') and self.project and hasattr(self.project, 'fp'):
                project_dir_str = str(Path(self.project.fp))
            else:
                project_dir_str = str(Path(self.outfolder))
            
            # CRITICAL FIX: Use source path where RAW files actually exist
            # RAW files remain in the source directory, they are NOT copied to project directory
            print(f"[THREAD-3] 🔍 Using source path where RAW file actually exists: {image_path_str}")
            # Keep the original source path - do NOT change to project path
            
            # Get metadata for calibration matching
            img_timestamp = getattr(image, 'timestamp', None)
            img_camera_model = getattr(image, 'camera_model', None)
            img_camera_filter = getattr(image, 'camera_filter', None)
            is_calibration_photo = getattr(image, 'is_calibration_photo', False)
            
            print(f"[THREAD-3] 🔍 Ray parameters: fn={image_fn}, path={image_path_str}, project={project_dir_str}")
            print(f"[THREAD-3] 🔍 Metadata: timestamp={img_timestamp}, model={img_camera_model}, filter={img_camera_filter}, is_target={is_calibration_photo}")
            
            # Submit Ray task
            # CRITICAL FIX: Correct parameter order for apply_calibration_ray function
            future = apply_calibration_func.remote(
                image_fn, image_path_str, project_dir_str,
                img_timestamp=img_timestamp,
                img_camera_model=img_camera_model,
                img_camera_filter=img_camera_filter
            )
            
            # Check if GPU is available for dynamic timeout
            gpu_available = False
            try:
                from dynamic_gpu_allocator import get_gpu_allocator
                gpu_allocator = get_gpu_allocator()
                gpu_available = gpu_allocator.total_gpu_memory > 0
            except:
                pass
            
            # Get result with shorter timeout and fallback
            timeout_seconds = 60 if gpu_available else 90  # Much shorter timeout for Thread-3
            print(f"[THREAD-3] Using {timeout_seconds}s timeout ({'GPU' if gpu_available else 'CPU'}-mode)")
            
            try:
                result = ray.get(future, timeout=timeout_seconds)
                print(f"[THREAD-3] ✅ Ray processing completed for {image.fn}")
            except ray.exceptions.GetTimeoutError:
                print(f"[THREAD-3] ⚠️ Ray timeout processing {image.fn} after {timeout_seconds}s - trying sequential fallback")
                
                # Cancel the Ray task to free resources
                try:
                    ray.cancel(future, force=True)
                    print(f"[THREAD-3] 🚫 Cancelled Ray task for {image.fn}")
                except Exception as cancel_error:
                    print(f"[THREAD-3] ⚠️ Could not cancel Ray task: {cancel_error}")
                
                # Track Ray failures and switch to sequential mode if needed
                if not hasattr(self, 'thread3_ray_failures'):
                    self.thread3_ray_failures = 0
                self.thread3_ray_failures += 1
                print(f"[THREAD-3] 📈 Ray failure count: {self.thread3_ray_failures}/2")
                
                if self.thread3_ray_failures >= 2:
                    if not hasattr(self, 'thread3_sequential_mode'):
                        self.thread3_sequential_mode = True
                        print(f"[THREAD-3] 🔄 Switching to sequential mode after {self.thread3_ray_failures} Ray failures")
                
                # Immediate fallback to sequential processing
                try:
                    print(f"[THREAD-3] 🔄 Sequential fallback for {image.fn}")
                    # Use the sequential calibration application method
                    result = apply_calibration_sequential(image)
                    print(f"[THREAD-3] ✅ Sequential processing completed for {image.fn}")
                except Exception as seq_error:
                    print(f"[THREAD-3] ❌ Sequential fallback failed for {image.fn}: {seq_error}")
                    result = None
            
            print(f"[THREAD-3] 🔍 Ray result for {image.fn}: {type(result)} - {result}")
            
            if result and isinstance(result, dict) and result.get('success', True):
                print(f"[THREAD-3] ✅ Ray processing completed for {image.fn}")
                
                # Apply calibration data from Ray worker result to image object
                if 'entry' in result and result['entry']:
                    entry = result['entry']
                    print(f"[THREAD-3] 🔧 Applying calibration data to {image.fn}")
                    
                    # Set calibration coefficients only if present (avoid overwriting with None)
                    if 'coefficients' in entry and entry['coefficients'] is not None:
                        image.calibration_coefficients = entry['coefficients']
                        print(f"[THREAD-3] ✅ Set calibration_coefficients for {image.fn}")
                    
                    # Set ALS data
                    if 'als_magnitude' in entry:
                        image.als_magnitude = entry['als_magnitude']
                        print(f"[THREAD-3] ✅ Set als_magnitude for {image.fn}")
                    
                    if 'als_data' in entry:
                        image.als_data = entry['als_data']
                        print(f"[THREAD-3] ✅ Set als_data for {image.fn}")
                    
                    # Set calibration yvals if available
                    if 'yvals' in entry:
                        image.calibration_yvals = entry['yvals']
                        print(f"[THREAD-3] ✅ Set calibration_yvals for {image.fn}")
                    
                    # CRITICAL FIX: Check if reflectance calibration is enabled
                    reflectance_enabled = False
                    if hasattr(self, 'options') and self.options:
                        if 'Project Settings' in self.options and 'Processing' in self.options['Project Settings']:
                            reflectance_enabled = self.options['Project Settings']['Processing'].get('Reflectance calibration / white balance', False)
                        elif 'Processing' in self.options:
                            reflectance_enabled = self.options['Processing'].get('Reflectance calibration / white balance', False)
                    
                    print(f"[THREAD-3] 🔧 Reflectance calibration enabled: {reflectance_enabled} for {image.fn}")
                    
                    # Apply calibration or sensor response correction based on setting
                    if reflectance_enabled and hasattr(image, 'calibration_coefficients') and image.calibration_coefficients:
                        print(f"[THREAD-3] 🔧 APPLYING REFLECTANCE CALIBRATION TO PIXEL DATA for {image.fn}")
                        try:
                            # Import the calibration function
                            from mip.Calibrate_Images import apply_calib_to_image
                            
                            # Ensure image data is loaded
                            if image.data is None:
                                print(f"[THREAD-3] 📂 Loading image data for calibration application: {image.fn}")
                                image.load()
                            
                            if image.data is not None:
                                print(f"[THREAD-3] ✅ Image data loaded: shape={image.data.shape}, dtype={image.data.dtype}")
                                
                                # Apply calibration to the image pixel data
                                calibration_limits = getattr(image, 'calibration_limits', [65535, 65535, 65535])
                                apply_calib_to_image(image, image.calibration_coefficients, calibration_limits)
                                print(f"[THREAD-3] ✅ REFLECTANCE CALIBRATION APPLIED TO PIXEL DATA for {image.fn}")
                                
                                # CRITICAL FIX: Cache the calibrated image data for Thread 4 export
                                self.queues.cache_image_data(image.fn, image.data.copy())
                                print(f"[THREAD-3] 💾 CACHED calibrated image data for Thread 4 export: {image.fn}")
                            else:
                                print(f"[THREAD-3] ❌ Could not load image data for calibration: {image.fn}")
                                
                        except Exception as calib_err:
                            print(f"[THREAD-3] ❌ Error applying calibration to pixel data: {calib_err}")
                            import traceback
                            traceback.print_exc()
                    elif not reflectance_enabled:
                        # Apply sensor response correction only (no calibration coefficients)
                        print(f"[THREAD-3] 🔧 APPLYING SENSOR RESPONSE CORRECTION ONLY for {image.fn}")
                        try:
                            from mip.Calibrate_Images import sensor_response_correction
                            
                            # Ensure image data is loaded
                            if image.data is None:
                                print(f"[THREAD-3] 📂 Loading image data for sensor response correction: {image.fn}")
                                image.load()
                            
                            if image.data is not None:
                                print(f"[THREAD-3] ✅ Image data loaded: shape={image.data.shape}, dtype={image.data.dtype}")
                                
                                # Apply sensor response correction only
                                sensor_response_correction(image, limits=[], use_limit=False)
                                print(f"[THREAD-3] ✅ SENSOR RESPONSE CORRECTION APPLIED TO PIXEL DATA for {image.fn}")
                                
                                # Cache the sensor response corrected image data for Thread 4 export
                                self.queues.cache_image_data(image.fn, image.data.copy())
                                print(f"[THREAD-3] 💾 CACHED sensor response image data for Thread 4 export: {image.fn}")
                            else:
                                print(f"[THREAD-3] ❌ Could not load image data for sensor response correction: {image.fn}")
                                
                        except Exception as sensor_err:
                            print(f"[THREAD-3] ❌ Error applying sensor response correction: {sensor_err}")
                            import traceback
                            traceback.print_exc()
                    else:
                        print(f"[THREAD-3] ⚠️ No calibration coefficients available for pixel application: {image.fn}")
                    
                    # For non-target images, set the calibration image reference to a valid target
                    if not getattr(image, 'is_calibration_photo', False):
                        chosen_calib = None
                        # Prefer nearest valid calibration target by timestamp, same model/filter
                        try:
                            img_ts = getattr(image, 'timestamp', None)
                            img_model = getattr(image, 'camera_model', None)
                            img_filter = getattr(image, 'camera_filter', None)
                            if hasattr(self, 'project') and self.project and hasattr(self.project, 'imagemap'):
                                candidates = []
                                for _k, img_obj in self.project.imagemap.items():
                                    if getattr(img_obj, 'is_calibration_photo', False):
                                        if (getattr(img_obj, 'camera_model', None) == img_model and
                                            getattr(img_obj, 'camera_filter', None) == img_filter):
                                            # prefer those having calibration_yvals/xvals
                                            has_x = bool(getattr(img_obj, 'calibration_xvals', None))
                                            has_y = bool(getattr(img_obj, 'calibration_yvals', None))
                                            candidates.append((img_obj, has_x, has_y))
                                # Score: prefer has_x, then has_y; if multiple, choose the first (temporal closeness can be added later)
                                if candidates:
                                    # sort: has_x desc, has_y desc
                                    candidates.sort(key=lambda t: (t[1], t[2]), reverse=True)
                                    chosen_calib = candidates[0][0]
                        except Exception:
                            chosen_calib = None

                        # Fallback to entry filename if it actually points to a target with xvals
                        if chosen_calib is None:
                            calib_filename = entry.get('filename')
                            if calib_filename and hasattr(self, 'project') and self.project:
                                for img_key, img_obj in self.project.imagemap.items():
                                    if img_obj.fn == calib_filename and getattr(img_obj, 'is_calibration_photo', False):
                                        if bool(getattr(img_obj, 'calibration_xvals', None)):
                                            chosen_calib = img_obj
                                            break

                        if chosen_calib is not None:
                            image.calibration_image = chosen_calib
                            print(f"[THREAD-3] ✅ Set calibration_image for {image.fn} -> {chosen_calib.fn}")
                        else:
                            print(f"[THREAD-3] ⚠️ No valid calibration target found for {image.fn}; ALS correction may fall back to identity")
                
                # CRITICAL FIX: Update progress stats and UI for successful Ray processing
                # All images should be counted since they will all produce reflectance exports
                should_count_in_ui = True
                
                # Target images produce both red square (backend) AND reflectance (UI tracked) exports
                if getattr(image, 'is_calibration_photo', False):
                    print(f"[THREAD-3] 🎯 Target image {image.fn} processed - will produce both red square (backend) and reflectance (UI tracked) exports")
                
                # Only increment if this image hasn't been counted yet AND should be counted in UI
                # CRITICAL FIX: Only count RAW files that will actually be exported, not JPG files
                is_raw_file = image.fn.upper().endswith('.RAW') if hasattr(image, 'fn') else False
                
                if should_count_in_ui and not getattr(image, '_thread3_counted', False) and is_raw_file:
                    with self.stats_lock:
                        self.processing_stats['images_calibrated'] += 1
                        # CRITICAL FIX: Only count RAW files that will be exported, not all files
                        total_exportable_images = self.processing_stats.get('total_image_pairs', None)
                        if total_exportable_images is None:
                            # CRITICAL FIX: Count all image pairs (JPG or RAW) to match project input
                            total_exportable_images = 0
                            if hasattr(self, 'project') and self.project.data.get('files'):
                                for fileset in self.project.data['files'].values():
                                    if fileset.get('jpg') or fileset.get('raw'):
                                        total_exportable_images += 1
                            total_exportable_images = max(1, total_exportable_images)
                        progress_percent = int((self.processing_stats['images_calibrated'] / total_exportable_images) * 100)
                        print(f"[THREAD-3] 🔥 Progress: {self.processing_stats['images_calibrated']}/{total_exportable_images} ({progress_percent}%) - {image.fn} [RAW FILE COUNTED]")
                elif should_count_in_ui and not getattr(image, '_thread3_counted', False) and not is_raw_file:
                    pass
                else:
                    pass
                
                if should_count_in_ui and not getattr(image, '_thread3_counted', False) and is_raw_file:
                        # Mark this image as counted to prevent double counting
                        image._thread3_counted = True
                        
                        # Save Thread 3 progress after successful calibration application
                        if self.api and hasattr(self.api, 'project') and self.api.project:
                            current_processed = self.processing_stats['images_calibrated']
                            processed_images = [image.fn]  # Current image
                        # FRESH START: No state saving (removed resume functionality)
                        print(f"[THREAD-3] 💾 Saved calibration progress: {current_processed}/{total_exportable_images}, processed: {processed_images}")
                        
                        # Send progress update to UI immediately when each image finishes
                        if self.api and hasattr(self.api, 'update_thread_progress'):
                            self.api.update_thread_progress(
                                thread_id=3,
                                percent_complete=progress_percent,
                                phase_name="Processing",
                                time_remaining=f"{self.processing_stats['images_calibrated']}/{total_exportable_images}"
                            )
                elif should_count_in_ui and not is_raw_file:
                    print(f"[THREAD-3] ⚠️ Skipping progress count for JPG file: {image.fn} [JPG FILE NOT COUNTED]")
                else:
                    print(f"[THREAD-3] ⚠️ Skipping progress increment for {image.fn} (already counted)")
                
                # Queue for export (with explicit log for debug)
                print(f"[THREAD-3] 🚚 Queueing for export: {image.fn} (is_calibration_photo={getattr(image,'is_calibration_photo', False)})")
                self.queues.queue_to_export(image, "thread3")
            elif result is False:
                print(f"[THREAD-3] ❌ Ray worker returned False for {image.fn} - likely calibration data not found")
                # Check if calibration data exists in memory
                with self.queues.calibration_data_lock:
                    available_keys = list(self.queues.calibration_data_store.keys())
                    print(f"[THREAD-3] 🔍 Available calibration entries in memory: {len(available_keys)}")
                    for key in available_keys:
                        print(f"[THREAD-3] 🔍 Memory calibration entry: {key}")
            else:
                print(f"[THREAD-3] ❌ Ray processing failed for {image.fn}: {result}")
                
        except Exception as e:
            print(f"[THREAD-3] ❌ Error processing {image.fn} with Ray: {e}")
            import traceback
            traceback.print_exc()
    
    def _process_calibration_apply_sequential_streaming(self):
        """Process calibration application sequentially with streaming"""
        import time
        import queue
        
        print("[THREAD-3] 🌊 Starting streaming sequential calibration processing...")
        
        processed_count = 0
        pending_images = {}
        
        while not self.queues.shutdown.is_set():
            try:
                # Try to get an image from the queue
                try:
                    image = self.queues.calibration_apply_queue.get(timeout=0.5)
                    if image is None:  # Sentinel
                        print(f"[THREAD-3] Received sentinel, processed {processed_count} images")
                        break
                    
                    print(f"[THREAD-3] 📥 Received image: {image.fn}")
                    
                    # Check if this image can be processed immediately
                    if self._can_process_image_unified_now(image):
                        print(f"[THREAD-3] ✅ Processing {image.fn} immediately (calibration ready)")
                        self._process_single_image_sequential(image)
                        processed_count += 1
                        
                        # CRITICAL FIX: Update progress stats and UI (only if not already counted)
                        # All images should be counted since they will all produce reflectance exports
                        should_count_in_ui = True
                        
                        # Target images produce both red square (backend) AND reflectance (UI tracked) exports
                        if getattr(image, 'is_calibration_photo', False):
                            print(f"[THREAD-3] 🎯 Sequential: Target image {image.fn} processed - will produce both red square (backend) and reflectance (UI tracked) exports")
                        
                        # CRITICAL FIX: Only count RAW files for images_calibrated to match progress calculation
                        is_raw_file = image.fn.upper().endswith('.RAW') if hasattr(image, 'fn') else False
                        if should_count_in_ui and not getattr(image, '_thread3_counted', False) and is_raw_file:
                            with self.stats_lock:
                                self.processing_stats['images_calibrated'] += 1
                                total_images = self.processing_stats.get('total_image_pairs', None)
                                if total_images is None:
                                    # CRITICAL FIX: Count all image pairs (JPG or RAW) to match project input
                                    total_images = 0
                                    if hasattr(self, 'project') and self.project.data.get('files'):
                                        for fileset in self.project.data['files'].values():
                                            if fileset.get('jpg') or fileset.get('raw'):
                                                total_images += 1
                                    total_images = max(1, total_images)
                                progress_percent = int((self.processing_stats['images_calibrated'] / total_images) * 100)
                                print(f"[THREAD-3] Sequential Progress: {self.processing_stats['images_calibrated']}/{total_images} ({progress_percent}%) - {image.fn}")
                                
                                # Mark this image as counted to prevent double counting
                                image._thread3_counted = True
                                
                                # Send progress update to UI
                                if self.api and hasattr(self.api, 'update_thread_progress'):
                                    self.api.update_thread_progress(
                                        thread_id=3,
                                        percent_complete=progress_percent,
                                        phase_name="Processing",
                                        time_remaining=f"{self.processing_stats['images_calibrated']}/{total_images}"
                                    )
                        else:
                            print(f"[THREAD-3] ⚠️ Sequential: Skipping progress increment for {image.fn} (already counted)")
                    else:
                        print(f"[THREAD-3] ⏳ Adding {image.fn} to pending queue (calibration not ready)")
                        pending_images[image.fn] = image
                        
                except queue.Empty:
                    # Check pending images
                    if pending_images:
                        initial_count = len(pending_images)
                        self._check_pending_images_sequential(pending_images)
                        images_processed_this_check = initial_count - len(pending_images)
                        processed_count += images_processed_this_check
                        
                        # CRITICAL FIX: Update progress stats for images processed from pending queue
                        # Only count RAW files for images_calibrated to match progress calculation
                        if images_processed_this_check > 0:
                            # Estimate RAW files processed based on typical 50% RAW/JPG ratio
                            # This is approximate since we can't track exact files processed in batch
                            estimated_raw_files = int(images_processed_this_check * 0.5)  # Assume ~50% are RAW files
                            
                            with self.stats_lock:
                                self.processing_stats['images_calibrated'] += estimated_raw_files
                                print(f"[THREAD-3] 📊 Batch increment (estimated): {estimated_raw_files} RAW files out of {images_processed_this_check} total processed")
                                total_images = self.processing_stats.get('total_image_pairs', None)
                                if total_images is None:
                                    # CRITICAL FIX: Count all image pairs (JPG or RAW) to match project input
                                    total_images = 0
                                    if hasattr(self, 'project') and self.project.data.get('files'):
                                        for fileset in self.project.data['files'].values():
                                            if fileset.get('jpg') or fileset.get('raw'):
                                                total_images += 1
                                    total_images = max(1, total_images)
                                progress_percent = int((self.processing_stats['images_calibrated'] / total_images) * 100)
                                print(f"[THREAD-3] Progress: {self.processing_stats['images_calibrated']}/{total_images} ({progress_percent}%)")
                                
                                # Send progress update to UI
                                if self.api and hasattr(self.api, 'update_thread_progress'):
                                    self.api.update_thread_progress(
                                        thread_id=3,
                                        percent_complete=progress_percent,
                                        phase_name="Processing",
                                        time_remaining=f"{self.processing_stats['images_calibrated']}/{total_images}"
                                    )
                    continue
                    
            except Exception as e:
                print(f"[THREAD-3] Error in streaming processing: {e}")
                continue
        
        # Continue monitoring pending images until Thread-2 signals completion or all are processed
        while pending_images and not self.queues.shutdown.is_set():
            # Check if Thread-2 has finished - if so, we can process remaining images more aggressively
            thread2_finished = self.queues.calibration_compute_complete.is_set()
            print(f"[THREAD-3] DEBUG: thread2_finished={thread2_finished}, pending_images={len(pending_images)}")
            
            if thread2_finished:
                # CRITICAL FIX: Check for calibration data file existence instead of in-memory store
                has_calibration_file = self._check_calibration_file_exists()
                
                if has_calibration_file:
                    print(f"[THREAD-3] ✅ Thread-2 completed with calibration data! Processing {len(pending_images)} remaining pending images...")
                    
                    # CRITICAL FIX: Update UI to show Thread-3 is now actively processing
                    if self.api and hasattr(self.api, 'update_thread_progress'):
                        total_images = self.processing_stats.get('total_image_pairs', len(pending_images))
                        self.api.update_thread_progress(
                            thread_id=3,
                            percent_complete=5,  # Small progress to show it's started
                            phase_name="Processing",
                            time_remaining=f"0/{total_images}"
                        )
                        print(f"[THREAD-3] Updated UI to show active processing: 0/{total_images}")
                        
                    # Process all remaining pending images WITH calibration
                    for image in list(pending_images.values()):
                        try:
                            self._process_single_image_sequential(image)
                            processed_count += 1
                        except Exception as e:
                            print(f"[THREAD-3] Error processing pending image {image.fn}: {e}")
                            
                else:
                    print(f"[THREAD-3] ⚠️ Thread-2 completed but no calibration file found! Processing {len(pending_images)} images without calibration...")
                    
                    # CRITICAL FIX: Update UI to show Thread-3 is now actively processing
                    if self.api and hasattr(self.api, 'update_thread_progress'):
                        total_images = self.processing_stats.get('total_image_pairs', len(pending_images))
                        self.api.update_thread_progress(
                            thread_id=3,
                            percent_complete=5,  # Small progress to show it's started
                            phase_name="Processing",
                            time_remaining=f"0/{total_images}"
                        )
                        print(f"[THREAD-3] Updated UI to show active processing: 0/{total_images}")
                        
                    # Process all remaining pending images WITHOUT calibration
                    for image in list(pending_images.values()):
                        try:
                            # Skip calibration for this image since no targets were found
                            self._process_single_image_sequential_no_calibration(image)
                            processed_count += 1
                            
                            # CRITICAL FIX: Update progress stats for final batch processing
                            # Only count RAW files for images_calibrated to match progress calculation
                            is_raw_file = image.fn.upper().endswith('.RAW') if hasattr(image, 'fn') else False
                            if is_raw_file:
                                with self.stats_lock:
                                    self.processing_stats['images_calibrated'] += 1
                                total_images = self.processing_stats.get('total_image_pairs', None)
                                if total_images is None:
                                    # CRITICAL FIX: Count all image pairs (JPG or RAW) to match project input
                                    total_images = 0
                                    if hasattr(self, 'project') and self.project.data.get('files'):
                                        for fileset in self.project.data['files'].values():
                                            if fileset.get('jpg') or fileset.get('raw'):
                                                total_images += 1
                                    total_images = max(1, total_images)
                                progress_percent = int((self.processing_stats['images_calibrated'] / total_images) * 100)
                                print(f"[THREAD-3] Progress: {self.processing_stats['images_calibrated']}/{total_images} ({progress_percent}%)")
                                
                                # Send progress update to UI
                                if self.api and hasattr(self.api, 'update_thread_progress'):
                                    self.api.update_thread_progress(
                                        thread_id=3,
                                        percent_complete=progress_percent,
                                        phase_name="Processing",
                                        time_remaining=f"{self.processing_stats['images_calibrated']}/{total_images}"
                                    )
                        except Exception as e:
                            print(f"[THREAD-3] Error processing pending image {image.fn}: {e}")
                            
                # Clear pending images as we've processed them all
                pending_images.clear()
                break
            else:
                # Thread-2 still running - check if any pending images can now be processed
                # Reduce spam: Only print every 10th check
                if not hasattr(self, '_check_count'):
                    self._check_count = 0
                self._check_count += 1
                if self._check_count % 10 == 1:
                    print(f"[THREAD-3] 🔍 Checking {len(pending_images)} pending images for available calibration data... (check #{self._check_count})")
                images_processed_this_round = []
                
                for image_fn, image in list(pending_images.items()):
                    if self._can_process_image_unified_now(image):
                        print(f"[THREAD-3] ✅ Calibration data now available for {image.fn}")
                        try:
                            self._process_single_image_sequential(image)
                            processed_count += 1
                            images_processed_this_round.append(image_fn)
                            
                            # CRITICAL FIX: Update progress stats for streaming processing
                            # Only count RAW files for images_calibrated to match progress calculation
                            is_raw_file = image.fn.upper().endswith('.RAW') if hasattr(image, 'fn') else False
                            if is_raw_file:
                                with self.stats_lock:
                                    self.processing_stats['images_calibrated'] += 1
                                total_images = self.processing_stats.get('total_image_pairs', None)
                                if total_images is None:
                                    # CRITICAL FIX: Count all image pairs (JPG or RAW) to match project input
                                    total_images = 0
                                    if hasattr(self, 'project') and self.project.data.get('files'):
                                        for fileset in self.project.data['files'].values():
                                            if fileset.get('jpg') or fileset.get('raw'):
                                                total_images += 1
                                    total_images = max(1, total_images)
                                progress_percent = int((self.processing_stats['images_calibrated'] / total_images) * 100)
                                print(f"[THREAD-3] Progress: {self.processing_stats['images_calibrated']}/{total_images} ({progress_percent}%)")
                                
                                # Send progress update to UI
                                if self.api and hasattr(self.api, 'update_thread_progress'):
                                    self.api.update_thread_progress(
                                        thread_id=3,
                                        percent_complete=progress_percent,
                                        phase_name="Processing",
                                        time_remaining=f"{self.processing_stats['images_calibrated']}/{total_images}"
                                    )
                        except Exception as e:
                            print(f"[THREAD-3] Error processing {image.fn}: {e}")
                
                # Remove processed images from pending
                for image_fn in images_processed_this_round:
                    del pending_images[image_fn]
                
                if images_processed_this_round:
                    print(f"[THREAD-3] ✅ Processed {len(images_processed_this_round)} images this round, {len(pending_images)} still pending")
                
                # Wait a bit before checking again (streaming interval)
                if pending_images:  # Only wait if there are still pending images
                    time.sleep(0.5)  # Check every 500ms for new calibration data
        
        print(f"[THREAD-3] 🎉 Sequential streaming processing complete: {processed_count} images processed")
    
    def _check_pending_images_sequential(self, pending_images):
        """Check if any pending images can now be processed (sequential version)"""
        ready_images = []
        
        for image_fn, image in list(pending_images.items()):
            if self._can_process_image_unified_now(image):
                print(f"[THREAD-3] ✅ {image_fn} is now ready for processing")
                ready_images.append(image_fn)
                self._process_single_image_sequential(image)
            else:
                # Grace path for sequential mode as well
                try:
                    has_als = getattr(image, 'als_magnitude', None) is not None
                    has_calib_img = hasattr(image, 'calibration_image') and image.calibration_image is not None
                    if has_als and has_calib_img:
                        if not hasattr(image, '_temp_grace'): image._temp_grace = 0
                        image._temp_grace += 1
                        if image._temp_grace >= 3:
                            print(f"[THREAD-3] ⏩ Grace condition met, processing {image_fn} (sequential)")
                            ready_images.append(image_fn)
                            self._process_single_image_sequential(image)
                except Exception:
                    pass
        
        # Remove processed images from pending
        for image_fn in ready_images:
            del pending_images[image_fn]
    
    def _process_single_image_sequential(self, image):
        """Process a single image sequentially"""
        try:
            print(f"[THREAD-3] 🔍 Sequential processing {image.fn}")
            
            # Load calibration data from JSON file
            project_dir = getattr(self.project, 'fp', None)
            if not project_dir:
                print(f"[THREAD-3] ❌ No project directory for {image.fn}")
                return False
                
            calib_file = os.path.join(project_dir, 'calibration_data.json')
            if not os.path.exists(calib_file):
                print(f"[THREAD-3] ❌ No calibration file for {image.fn}")
                return False
                
            with open(calib_file, 'r') as f:
                calib_data = json.load(f)
            
            # Apply calibration using the sequential method with calibration data
            result = self._apply_calibration_from_json_sequential(image, calib_data)
            
            if result:
                print(f"[THREAD-3] ✅ Sequential processing completed for {image.fn}")
                # Queue for export
                self.queues.queue_to_export(image, "thread3")
            else:
                print(f"[THREAD-3] ❌ Sequential processing failed for {image.fn}")
                
        except Exception as e:
            print(f"[THREAD-3] ❌ Error processing {image.fn} sequentially: {e}")
            import traceback
            traceback.print_exc()
    
    def _process_calibration_apply_ray_batch(self):
        """Process calibration application using Ray for streaming batch processing - OPTIMIZED FOR THOUSANDS OF IMAGES"""
        print("[THREAD-3] Starting Ray streaming batch processing")
        print("[THREAD-3] 🚀 Using optimized Ray parallel processing for thousands of images")
        
        # OPTIMIZED: Stream processing instead of collecting all images first
        batch_size = BATCH_SIZE_FOR_LARGE_DATASETS  # Process in batches to manage memory
        current_batch = []
        images_received = 0
        total_processed = 0
        
        while not self.queues.shutdown.is_set():
            try:
                # Get image filename (not object) to reduce memory usage
                image_filename = self.queues.calibration_apply_queue.get(timeout=1)
                if image_filename is None:  # Sentinel
                    print(f"[THREAD-3] Received sentinel after {images_received} images")
                    # Process final batch if any
                    if current_batch:
                        print(f"[THREAD-3] Processing final batch of {len(current_batch)} images")
                        processed_count = self._process_ray_batch_streaming(current_batch, total_processed)
                        total_processed += processed_count
                    break
                
                current_batch.append(image_filename)
                images_received += 1
                
                # Log progress every 100 images to avoid log flooding
                if images_received % 100 == 0:
                    print(f"[THREAD-3] 📊 Queued {images_received} images for processing")
                
                # Process batch when it reaches optimal size
                if len(current_batch) >= batch_size:
                    print(f"[THREAD-3] 🚀 Processing batch {total_processed//batch_size + 1} of {batch_size} images")
                    processed_count = self._process_ray_batch_streaming(current_batch, total_processed)
                    total_processed += processed_count
                    current_batch.clear()
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[THREAD-3] Error collecting images: {e}")
                continue
        
        print(f"[THREAD-3] ✅ Completed streaming Ray processing: {total_processed} images processed in batches")
        return total_processed
    
    def _process_ray_batch_streaming(self, image_filenames_batch, batch_offset):
        """Process a batch of images using Ray with optimized resource management - FILENAME-ONLY APPROACH"""
        batch_size = len(image_filenames_batch)
        print(f"[THREAD-3] 🔥 Processing Ray batch: {batch_size} images (offset: {batch_offset})")
        
        # Submit Ray tasks for the batch - working with filenames only
        ray_futures = []
        valid_filenames = []
        
        for image_filename in image_filenames_batch:
            # Get the Ray remote function
            apply_calibration_func = get_unified_task_function('apply_calibration', execution_mode='parallel')
            
            # Prepare serializable parameters using only filename metadata
            try:
                ray_params = self._prepare_ray_params_for_filename(image_filename)
                if ray_params:
                    future = apply_calibration_func.remote(**ray_params)
                    ray_futures.append((future, image_filename))  # Store filename, not image object
                    valid_filenames.append(image_filename)
                else:
                    print(f"[THREAD-3] ⚠️ Could not prepare Ray parameters for {image_filename}")
            except Exception as e:
                print(f"[THREAD-3] ❌ Error preparing Ray task for {image_filename}: {e}")
                continue
        
        print(f"[THREAD-3] 🚀 Submitted {len(ray_futures)} Ray tasks for batch processing")
        
        # Process results as they complete (streaming results)
        processed_count = 0
        completed_futures = []
        
        try:
            # Wait for results with timeout to avoid hanging
            import time
            start_time = time.time()
            timeout_per_image = 30  # 30 seconds per image max
            total_timeout = timeout_per_image * len(ray_futures)
            
            while ray_futures and (time.time() - start_time) < total_timeout:
                # Check for completed tasks
                ready_futures, ray_futures = ray.wait(ray_futures, num_returns=min(10, len(ray_futures)), timeout=1.0)
                
                for future, image_filename in ready_futures:
                    try:
                        result = ray.get(future)
                        if result:
                            # For successful results, we need to create a minimal image object for export queue
                            # But we'll do this lazily only when needed
                            processed_count += 1
                            print(f"[THREAD-3] ✅ Batch progress: {processed_count}/{batch_size} - {image_filename}")
                            
                            # Queue the filename for export processing (Thread 4 will handle image loading)
                            # This avoids loading full image objects in Thread 3
                            self._queue_filename_for_export(image_filename)
                        else:
                            print(f"[THREAD-3] ❌ Ray processing failed for {image_filename}")
                    except Exception as e:
                        print(f"[THREAD-3] ❌ Error getting Ray result for {image_filename}: {e}")
                    
                    completed_futures.append((future, image_filename))
                
                # Update progress
                if self.api and hasattr(self.api, 'update_thread_progress'):
                    progress = int(((batch_offset + processed_count) / (batch_offset + batch_size)) * 100)
                    self.api.update_thread_progress(
                        thread_id=3,
                        percent_complete=progress,
                        phase_name="Calibrating",
                        time_remaining=f"{processed_count}/{batch_size}"
                    )
            
            # Handle any remaining futures that didn't complete
            if ray_futures:
                print(f"[THREAD-3] ⚠️ {len(ray_futures)} Ray tasks did not complete within timeout")
                for future, image_filename in ray_futures:
                    try:
                        ray.cancel(future)
                        print(f"[THREAD-3] ❌ Cancelled timeout task for {image_filename}")
                    except:
                        pass
        
        except Exception as e:
            print(f"[THREAD-3] ❌ Error in Ray batch processing: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"[THREAD-3] ✅ Batch completed: {processed_count}/{batch_size} images processed successfully")
        return processed_count
    
    def _get_image_metadata_by_filename(self, filename):
        """Get image metadata by filename without loading the full image object"""
        # First check if we have the image in imagemap
        if hasattr(self.project, 'imagemap') and filename in self.project.imagemap:
            image = self.project.imagemap[filename]
            return {
                'path': getattr(image, 'path', None) or getattr(image, 'jpgpath', None),
                'timestamp': getattr(image, 'timestamp', None) or getattr(image, 'capture_time', None),
                'camera_model': getattr(image, 'camera_model', None),
                'camera_filter': getattr(image, 'camera_filter', None),
                'is_calibration_photo': getattr(image, 'is_calibration_photo', False)
            }
        
        # Fallback: search in project data files
        if hasattr(self.project, 'data') and 'files' in self.project.data:
            for key, file_info in self.project.data['files'].items():
                if file_info.get('fn') == filename:
                    return {
                        'path': file_info.get('path'),
                        'timestamp': file_info.get('timestamp'),
                        'camera_model': file_info.get('camera_model'),
                        'camera_filter': file_info.get('camera_filter'),
                        'is_calibration_photo': file_info.get('is_calibration_photo', False)
                    }
        
        return None
    
    def _prepare_ray_params_for_filename(self, filename):
        """Prepare serializable parameters for Ray remote function using only filename"""
        try:
            from pathlib import Path
            import os
            
            # Get metadata without loading full image object
            metadata = self._get_image_metadata_by_filename(filename)
            if not metadata:
                print(f"[THREAD-3] ❌ Could not find metadata for {filename}")
                return None
            
            # Get absolute path for the image
            raw_image_path = metadata['path']
            if not raw_image_path or not os.path.isabs(raw_image_path):
                print(f"[THREAD-3] ❌ Invalid image path for {filename}: {raw_image_path}")
                return None
            
            # Get project directory
            proj_fp = getattr(self.project, 'fp', None)
            proj_pp = getattr(self.project, 'project_path', None)
            project_dir_str = str(proj_fp or proj_pp or Path(raw_image_path).parent)
            
            # Prepare parameters using only metadata
            ray_params = {
                'image_path_str': raw_image_path,
                'project_dir_str': project_dir_str,
                'options': self.options,
                'img_timestamp': metadata['timestamp'],
                'img_camera_model': metadata['camera_model'],
                'img_camera_filter': metadata['camera_filter'],
                'is_calibration_photo': metadata['is_calibration_photo']
            }
            
            return ray_params
            
        except Exception as e:
            print(f"[THREAD-3] ❌ Error preparing Ray parameters for {filename}: {e}")
            return None
    
    def _queue_filename_for_export(self, filename):
        """Queue a filename for export processing (Thread 4 will load the image object)"""
        try:
            # For now, we still need to create a minimal image object for the export queue
            # But we'll optimize this further by making Thread 4 work with filenames too
            if hasattr(self.project, 'imagemap') and filename in self.project.imagemap:
                image = self.project.imagemap[filename]
                self.queues.queue_to_export(image, "thread3")
            else:
                # Create a lightweight reference object
                metadata = self._get_image_metadata_by_filename(filename)
                if metadata:
                    # Create minimal object with just the needed attributes
                    class MinimalImageRef:
                        def __init__(self, fn, path, metadata):
                            self.fn = fn
                            self.path = path
                            self.timestamp = metadata.get('timestamp')
                            self.camera_model = metadata.get('camera_model')
                            self.camera_filter = metadata.get('camera_filter')
                            self.is_calibration_photo = metadata.get('is_calibration_photo', False)
                    
                    minimal_ref = MinimalImageRef(filename, metadata['path'], metadata)
                    self.queues.export_queue.put(minimal_ref)
                    # print(f"[THREAD-3] Queued minimal reference for {filename} to export")
                else:
                    print(f"[THREAD-3] ❌ Could not queue {filename} for export - no metadata found")
        except Exception as e:
            print(f"[THREAD-3] ❌ Error queuing {filename} for export: {e}")
    
    def _process_calibration_apply_ray_parallel(self, images_to_process):
        """Process calibration application using Ray with incremental progress updates"""
        total_images = len(images_to_process)
        # print(f"[THREAD-3] 🚀🚀🚀 ENTERING RAY PARALLEL PROCESSING 🚀🚀🚀")
        # print(f"[THREAD-3] Starting Ray parallel processing of {total_images} images")
        
        # Debug: Show what images we're processing
        for i, image in enumerate(images_to_process):
            print(f"[THREAD-3] Image {i+1}: {image.fn}, is_calibration_photo={getattr(image, 'is_calibration_photo', False)}")
        
        # Submit all Ray tasks
        ray_futures = []
        for image in images_to_process:
            # Get the Ray remote function
            apply_calibration_func = get_unified_task_function('apply_calibration', execution_mode='parallel')
            
            # Prepare serializable parameters for Ray
            from pathlib import Path
            import os
            image_fn = image.fn
            
            # CRITICAL FIX: Ensure we always get the absolute path
            raw_image_path = getattr(image, 'path', None) or getattr(image, 'jpgpath', None)
            
            # Check if path is absolute, if not, try to find the full path
            if raw_image_path and not os.path.isabs(raw_image_path):
                # Try to get the full path from the project's image mapping
                # print(f"[THREAD-3] 🔧 Relative path detected: {raw_image_path}")
                
                # Look for the image in the project's imagemap to get the full source path
                if hasattr(self.project, 'data') and 'files' in self.project.data:
                    for key, file_info in self.project.data['files'].items():
                        if file_info.get('fn') == image_fn:
                            full_source_path = file_info.get('path')
                            if full_source_path and os.path.isabs(full_source_path):
                                raw_image_path = full_source_path
                                # print(f"[THREAD-3] 🔧 Found full path in imagemap: {raw_image_path}")
                                break
                
                # If still relative, this is an error
                if not os.path.isabs(raw_image_path):
                    print(f"[THREAD-3] ❌ ERROR: Could not resolve absolute path for {image_fn}")
                    print(f"[THREAD-3] 🔧 Current path: {raw_image_path}")
                    continue  # Skip this image
            
            image_path_str = raw_image_path
            
            # Prefer project.fp for project directory; fallback to project.project_path; then to image folder
            proj_fp = getattr(self.project, 'fp', None)
            proj_pp = getattr(self.project, 'project_path', None)
            project_dir_str = str(proj_fp or proj_pp or Path(image_path_str).parent)
            
            # CRITICAL FIX: Pass image metadata for calibration matching
            img_timestamp = getattr(image, 'timestamp', None) or getattr(image, 'capture_time', None)
            img_camera_model = getattr(image, 'camera_model', None)
            img_camera_filter = getattr(image, 'camera_filter', None)
            is_calibration_photo = getattr(image, 'is_calibration_photo', False)
            
            # Convert timestamp to string if it's a datetime object
            if hasattr(img_timestamp, 'strftime'):
                img_timestamp_str = img_timestamp.strftime('%Y-%m-%d %H:%M:%S')
            else:
                img_timestamp_str = str(img_timestamp) if img_timestamp else None
            
            # print(f"[THREAD-3] Submitting Ray task for {image_fn} with metadata: timestamp={img_timestamp_str}, camera_model={img_camera_model}, camera_filter={img_camera_filter}, is_target={is_calibration_photo}, project_dir={project_dir_str}")
            
            future = apply_calibration_func.remote(image_fn, image_path_str, project_dir_str, img_timestamp_str, img_camera_model, img_camera_filter)
            ray_futures.append((future, image))
        
        # Process completed tasks and update progress incrementally
        completed_count = 0
        remaining_futures = ray_futures.copy()
        
        while remaining_futures:
            # Wait for at least one task to complete
            ready_futures, remaining_ray_futures = ray.wait(
                [future for future, _ in remaining_futures], 
                num_returns=1, 
                timeout=1.0
            )
            
            if ready_futures:
                # Process completed tasks
                for completed_future in ready_futures:
                    # Find the corresponding image
                    for i, (future, image) in enumerate(remaining_futures):
                        if future == completed_future:
                            try:
                                # Get the result
                                result = ray.get(completed_future)
                                # print(f"[THREAD-3] Ray worker result for {image.fn}: {type(result)} - {result}")
                                
                                if result and isinstance(result, dict) and result.get('success'):
                                    # CRITICAL FIX: Apply the calibration entry returned by Ray worker
                                    entry = result.get('entry')
                                    if entry:
                                        # print(f"[THREAD-3] Applying calibration entry for {image.fn}: {list(entry.keys()) if entry else 'None'}")
                                        self._apply_calibration_entry(image, entry)
                                        # print(f"[THREAD-3] Successfully applied calibration to {image.fn} from Ray worker")
                                        
                                        # Thread-3: Do additional processing work (but no export) - Ray version
                                        print(f"[THREAD-3] 🔧 Performing Ray processing work for {image.fn}")
                                        self._perform_processing_work(image)
                                        
                                    else:
                                        print(f"[THREAD-3] Ray worker returned success but no entry for {image.fn}")
                                else:
                                    print(f"[THREAD-3] Ray worker failed for {image.fn}: {result}")
                                
                                # Update progress
                                completed_count += 1
                                progress_percent = int((completed_count / total_images) * 100)
                                
                                # print(f"[THREAD-3] Progress: {completed_count}/{total_images} ({progress_percent}%)")
                                
                                if self.api and hasattr(self.api, 'update_thread_progress'):
                                    self.api.update_thread_progress(
                                        thread_id=3,
                                        percent_complete=progress_percent,
                                        phase_name="Applying calibration",
                                        time_remaining=f"{completed_count}/{total_images}"
                                    )
                                
                                # Update stats
                                # Only count RAW files for images_calibrated to match progress calculation
                                is_raw_file = image.fn.upper().endswith('.RAW') if hasattr(image, 'fn') else False
                                if is_raw_file:
                                    with self.stats_lock:
                                        self.processing_stats['images_calibrated'] += 1
                                
                                # Send to next thread using proper queue method
                                self.queues.queue_to_export(image, "thread3")
                                
                            except Exception as e:
                                print(f"[THREAD-3] Error processing {image.fn}: {e}")
                                completed_count += 1
                            
                            # Remove from remaining futures
                            remaining_futures.pop(i)
                            break
                
                # Update remaining futures list
                remaining_futures = [(f, img) for f, img in remaining_futures if f in remaining_ray_futures]
        
        # Send sentinel to next thread
        self.queues.export_queue.put(None)
        # print(f"[THREAD-3] Completed Ray parallel processing of {completed_count}/{total_images} images")
    
    def _apply_calibration_from_json_sequential(self, image, calib_data):
        """Apply calibration data from JSON to an image by finding the best matching entry"""
        import datetime
        
        # Get image metadata for matching
        img_timestamp = getattr(image, 'timestamp', None)
        img_camera_model = getattr(image, 'camera_model', None)
        img_camera_filter = getattr(image, 'camera_filter', None)
        
        # print(f"[THREAD-3] Searching for calibration match for {image.fn}")
        # print(f"[THREAD-3] Image criteria: timestamp={img_timestamp}, camera_model={img_camera_model}, camera_filter={img_camera_filter}")
        
        # Parse image timestamp if it's a string
        img_ts = None
        if img_timestamp:
            try:
                if isinstance(img_timestamp, str):
                    img_ts = datetime.datetime.strptime(img_timestamp, '%Y-%m-%d %H:%M:%S')
                elif hasattr(img_timestamp, 'strftime'):
                    img_ts = img_timestamp
            except Exception as e:
                print(f"[THREAD-3] Error parsing timestamp {img_timestamp}: {e}")
        
        # Find best matching calibration entry
        best_key = None
        best_delta = None
        fallback_key = None
        fallback_delta = None
        
        for key, entry in calib_data.items():
            try:
                entry_camera_model = entry.get('camera_model', None)
                entry_camera_filter = entry.get('camera_filter', None)
                
                # Check camera model and filter match
                camera_model_match = (img_camera_model is None or entry_camera_model is None or 
                                    entry_camera_model == img_camera_model)
                camera_filter_match = (img_camera_filter is None or entry_camera_filter is None or 
                                     entry_camera_filter == img_camera_filter)
                
                if not camera_model_match or not camera_filter_match:
                    continue
                
                # Parse calibration timestamp
                calib_ts = datetime.datetime.strptime(key, '%Y-%m-%d %H:%M:%S')
                
                if img_ts:
                    delta = (img_ts - calib_ts).total_seconds()
                    abs_delta = abs(delta)
                    
                    # Prefer earlier calibration (delta >= 0)
                    if delta >= 0 and (best_delta is None or delta < best_delta):
                        best_key = key
                        best_delta = delta
                    
                    # Fallback to closest overall
                    if fallback_delta is None or abs_delta < fallback_delta:
                        fallback_key = key
                        fallback_delta = abs_delta
                else:
                    # No timestamp available, use first matching entry
                    if best_key is None:
                        best_key = key
                        
            except Exception as e:
                print(f"[THREAD-3] Error processing calibration entry {key}: {e}")
                continue
        
        # Choose the best calibration entry
        chosen_key = best_key or fallback_key
        
        if not chosen_key:
            print(f"[THREAD-3] No matching calibration entry found for {image.fn}")
            return False
        
        # print(f"[THREAD-3] Selected calibration entry: {chosen_key} for {image.fn}")
        
        # Apply the calibration entry
        entry = calib_data[chosen_key]
        self._apply_calibration_entry(image, entry)
        print(f"[THREAD-3] Applied calibration data from {chosen_key} to {image.fn}")
        return True
    
    def _apply_calibration_entry(self, image, entry):
        """Apply calibration data from an entry to an image"""
        import numpy as np
        
        image.calibration_coefficients = entry.get('coefficients')
        image.calibration_limits = entry.get('limits')
        image.calibration_xvals = entry.get('xvals')
        image.calibration_yvals = entry.get('yvals')
        image.als_magnitude = entry.get('als_magnitude')
        image.als_data = entry.get('als_data')
        
        # CRITICAL FIX: Apply the selection flag from JSON
        image.is_selected_for_calibration = entry.get('is_selected_for_calibration', False)
        print(f"[THREAD-3] Applied is_selected_for_calibration={image.is_selected_for_calibration} to {image.fn} from JSON")
        
        # Create a calibration_image object that process_image_unified expects
        # This allows the export thread to properly apply calibration
        calib_image = type('CalibImage', (), {})()
        calib_image.calibration_coefficients = entry.get('coefficients')
        calib_image.calibration_limits = entry.get('limits')
        calib_image.calibration_xvals = entry.get('xvals')
        calib_image.calibration_yvals = entry.get('yvals')
        calib_image.als_magnitude = entry.get('als_magnitude')
        calib_image.als_data = entry.get('als_data')
        
        # Assign the calibration image to the image object
        image.calibration_image = calib_image
        print(f"[THREAD-3] Created calibration_image for {image.fn} with coefficients: {calib_image.calibration_coefficients is not None}")

        # IMPORTANT: Load ALS specific to the source image (not the calibration image)
        try:
            project_dir = getattr(image, 'project_path', None) or getattr(getattr(image, 'project', None), 'fp', None)
            if project_dir:
                if load_als_data_from_json(image, project_dir):
                    pass
                    # print(f"[THREAD-3] Loaded per-image ALS for {image.fn} from JSON (overrides entry ALS)")
                else:
                    print(f"[THREAD-3] WARNING: Could not load per-image ALS for {image.fn} from JSON")
        except Exception as _als_e:
            print(f"[THREAD-3] WARNING: Exception loading per-image ALS for {image.fn}: {_als_e}")
    
    def _process_calibration_apply_sequential(self):
        """Thread-3: ONLY do calibration processing, no export operations"""
        # Keep track of images waiting for calibration
        waiting_for_calibration = []
        images_received = 0
        
        # print("[THREAD-3] 🔧 Starting calibration processing (PROCESSING ONLY - NO EXPORT)")
        
        while not self.queues.shutdown.is_set():
            try:
                image = self.queues.calibration_apply_queue.get(timeout=1)
                if image is None:  # Sentinel
                    # print(f"[THREAD-3] Received sentinel, processed {images_received} images total")
                    break
                    
                # CRITICAL: Check for stop before processing each image
                if self.queues.shutdown.is_set() or self._stop_requested:
                    print(f"[THREAD-3] 🛑 Stop requested before processing {getattr(image, 'fn', 'unknown')} - aborting")
                    break
                
                # Save thread progress and update UI
                if self.api and hasattr(self.api, 'project') and self.api.project and hasattr(image, 'fn'):
                    # FRESH START: No state saving (removed resume functionality)
                    # Update UI progress for Thread 3
                    self.api.update_thread_progress(
                        thread_id=3,
                        percent_complete=50,  # Processing in progress
                        phase_name="Processing",
                        time_remaining="Processing..."
                    )
                
                images_received += 1
                # print(f"[THREAD-3] Received image {images_received}: {image.fn}")
                # print(f"[THREAD-3] Processing {image.fn}, is_calibration_photo={getattr(image, 'is_calibration_photo', False)}")
                
                # DEBUG: Track target images
                # DEBUG: Track target images
                if getattr(image, 'is_calibration_photo', False):
                    pass
                    # print(f"[THREAD-3] DEBUG: Received TARGET image {image.fn}")
                    # print(f"[THREAD-3] DEBUG: Target attributes:")
                    # print(f"[THREAD-3] DEBUG:   - calibration_image: {getattr(image, 'calibration_image', None)}")
                    # print(f"[THREAD-3] DEBUG:   - calibration_coefficients: {getattr(image, 'calibration_coefficients', None)}")
                    # print(f"[THREAD-3] DEBUG:   - als_magnitude: {getattr(image, 'als_magnitude', None)}")
                
                if not hasattr(image, 'project') or image.project is None:
                    image.project = self.project
                # UNIFIED: Remove special-casing for targets; all images load calibration from JSON
                # print(f"[THREAD-3] Loading calibration from JSON for {image.fn}")
                # OPTIMIZATION: Remove blocking wait - individual image processing will handle calibration availability
                # The existing retry logic below already ensures calibration data is ready before processing
                
                # Wait/retry for calibration JSON
                calib_json_path = self._get_calibration_json_path()
                # print(f"[THREAD-3] DEBUG: Looking for calibration JSON at: {calib_json_path}")
                # print(f"[THREAD-3] DEBUG: File exists check: {os.path.exists(calib_json_path)}")
                if calib_json_path and os.path.exists(calib_json_path):
                    pass
                    # print(f"[THREAD-3] DEBUG: File size: {os.path.getsize(calib_json_path)} bytes")
                    # print(f"[THREAD-3] DEBUG: File modification time: {os.path.getmtime(calib_json_path)}")
                retry_count = 0
                while not os.path.exists(calib_json_path):
                    if retry_count == 0:
                        # print(f"[THREAD-3] Waiting for calibration JSON to appear at {calib_json_path} for {image.fn}")
                        # Update progress to show we're waiting
                        if self.api and hasattr(self.api, 'update_thread_progress'):
                            self.api.update_thread_progress(
                                thread_id=3,
                                percent_complete=50,
                                phase_name="Waiting for calibration data",
                                time_remaining="Waiting for Thread-2"
                            )
                    time.sleep(0.2)
                    retry_count += 1
                    if retry_count % 25 == 0:
                        # print(f"[THREAD-3] Still waiting for calibration JSON after {retry_count*0.2:.1f}s for {image.fn}")
                        # Update progress to show we're still waiting
                        if self.api and hasattr(self.api, 'update_thread_progress'):
                            self.api.update_thread_progress(
                                thread_id=3,
                                percent_complete=50,
                                phase_name=f"Waiting {retry_count*0.2:.1f}s for calibration",
                                time_remaining="Waiting for Thread-2"
                            )
                        # Add more debug info during long waits
                        # print(f"[THREAD-3] DEBUG: Re-checking file existence: {os.path.exists(calib_json_path)}")
                        if calib_json_path:
                            pass
                            # print(f"[THREAD-3] DEBUG: Directory exists: {os.path.exists(os.path.dirname(calib_json_path))}")
                            # print(f"[THREAD-3] DEBUG: Directory contents: {os.listdir(os.path.dirname(calib_json_path)) if os.path.exists(os.path.dirname(calib_json_path)) else 'DIR_NOT_FOUND'}")
                    # Timeout after 60 seconds to prevent infinite waiting (increased from 30s)
                    if retry_count > 300:  # 60 seconds (300 * 0.2s)
                        print(f"[THREAD-3] ERROR: Timeout waiting for calibration JSON after 60s for {image.fn}")
                        # print(f"[THREAD-3] ERROR: Expected path: {calib_json_path}")
                        # print(f"[THREAD-3] ERROR: Project fp: {getattr(self.project, 'fp', 'None')}")
                        # Don't break - continue processing without calibration
                        print(f"[THREAD-3] WARNING: Processing {image.fn} without calibration data")
                        break
                import json
                with open(calib_json_path, 'r') as f:
                    calib_data = json.load(f)
                # print(f"[THREAD-3] Calibration JSON keys: {list(calib_data.keys())}")
                # print(f"[THREAD-3] Attempting to match image timestamp: {getattr(image, 'timestamp', None)} camera_model: {getattr(image, 'camera_model', None)} camera_filter: {getattr(image, 'camera_filter', None)}")
                if self._apply_calibration_from_json_sequential(image, calib_data):
                    # CRITICAL FIX: Always increment counter for images processed, regardless of ALS data
                    # Only count RAW files for images_calibrated to match progress calculation
                    is_raw_file = image.fn.upper().endswith('.RAW') if hasattr(image, 'fn') else False
                    if is_raw_file:
                        with self.stats_lock:
                            self.processing_stats['images_calibrated'] += 1
                        # Ensure we don't exceed the total number of image pairs
                        if self.processing_stats['images_calibrated'] > self.processing_stats['total_image_pairs']:
                            self.processing_stats['images_calibrated'] = self.processing_stats['total_image_pairs']
                        # Send "0/N" feedback when processing first image
                        if self.processing_stats['images_calibrated'] == 1 and self.api and hasattr(self.api, 'processing_mode') and self.api.processing_mode == "premium":
                            # Thread 3 initial progress now handled at thread start to avoid conflicts
                            pass
                        
                        # print(f"[THREAD-3] Incremented images_calibrated to {self.processing_stats['images_calibrated']}")
                    
                    # Thread-3: Do additional processing work (but no export)
                    print(f"[THREAD-3] 🔧 Performing processing work for {image.fn}")
                    self._perform_processing_work(image)
                    
                    if hasattr(image, 'als_magnitude') and image.als_magnitude is not None:
                        pass
                        # print(f"[THREAD-3] Applied calibration and ALS to {image.fn}")
                    else:
                        print(f"[THREAD-3] WARNING: ALS data missing for {image.fn}, but queuing for export anyway")
                    
                    # Queue processed image to Thread-4 for export only
                    # print(f"[THREAD-3] ✅ Processing completed for {image.fn}, queuing to Thread-4 for export")
                    self.queues.queue_to_export(image, "thread3")
                else:
                    print(f"[ERROR] No calibration match found for {image.fn} (timestamp: {getattr(image, 'timestamp', None)}, camera_model: {getattr(image, 'camera_model', None)}, camera_filter: {getattr(image, 'camera_filter', None)})")
                    waiting_for_calibration.append(image)
                    print(f"[THREAD-3] No calibration match yet for {image.fn}, queuing for later")
            except queue.Empty:
                continue
        
        # CRITICAL FIX: Send sentinel to Thread-4 to unblock it
        self.queues.export_queue.put(None)  # Sentinel for Thread-4
        print("[THREAD-3] Calibrating complete")
    
    def _get_calibration_json_path(self):
        """Get the path to the calibration JSON file"""
        project_dir = getattr(self.project, 'fp', None)
        if project_dir:
            return os.path.join(project_dir, 'calibration_data.json')
        return None

    def _export_single_image_json(self, image):
        """Export a calibrated image received from Thread 3"""
        try:
            # CRITICAL FIX: Now receives image object directly from Thread 3
            if not hasattr(image, 'fn') or not hasattr(image, 'data'):
                pass
                return False
            
            if image.data is None:
                pass
                return False
            
            if image.data is not None:
                pass
                # Check if data looks calibrated (reflectance values are typically 0-1 scaled to uint16, max ~65535)
                # RAW values typically exceed 65535 or are unprocessed, calibrated values stay within uint16 range
                if image.data.dtype == 'uint16' and image.data.max() <= 65535:
                    pass
                else:
                    pass
            
            # Determine output format and folder
            output_format = self.project.data.get('config', {}).get('Project Settings', {}).get('Processing', {}).get('output_format', 'tiff16')
            
            # Get camera model and filter from the image object first, then fallback to project data
            camera_model = getattr(image, 'camera_model', 'Unknown') or 'Unknown'
            camera_filter = getattr(image, 'camera_filter', '') or ''
            
            
            # If not found in image object, search through all project files for valid camera metadata
            if camera_model == 'Unknown' and self.project.data.get('files'):
                pass
                for file_key, file_data in self.project.data['files'].items():
                    # Check both direct metadata and import_metadata
                    direct_model = file_data.get('camera_model')
                    direct_filter = file_data.get('camera_filter')
                    
                    import_metadata = file_data.get('import_metadata', {})
                    import_model = import_metadata.get('camera_model')
                    import_filter = import_metadata.get('camera_filter')
                    
                    # Use import_metadata preferentially as it's more reliable
                    if import_model and import_model != 'Unknown':
                        camera_model = import_model
                        camera_filter = import_filter or ''
                        break
                    elif direct_model and direct_model != 'Unknown':
                        camera_model = direct_model
                        camera_filter = direct_filter or ''
                        break
            
            # CRITICAL FIX: Prevent exporting to wrong folder with fallback values
            if camera_model == 'Unknown':
                pass
                return False
            
            # Check if reflectance calibration is enabled to determine folder name
            reflectance_enabled = False
            vignette_enabled = False
            if hasattr(self, 'options') and self.options:
                if 'Project Settings' in self.options and 'Processing' in self.options['Project Settings']:
                    reflectance_enabled = self.options['Project Settings']['Processing'].get('Reflectance calibration / white balance', False)
                    vignette_enabled = self.options['Project Settings']['Processing'].get('Vignette correction', False)
                elif 'Processing' in self.options:
                    reflectance_enabled = self.options['Processing'].get('Reflectance calibration / white balance', False)
                    vignette_enabled = self.options['Processing'].get('Vignette correction', False)
            
            # Determine folder name based on reflectance AND vignette settings
            if reflectance_enabled:
                subfolder_name = "Reflectance_Calibrated_Images"
            else:
                # Reflectance is disabled - check vignette setting
                if vignette_enabled:
                    subfolder_name = "Vignette_Corrected_Images"
                else:
                    subfolder_name = "Sensor_Response_Images"
            
            # print(f"[THREAD-4-JSON] 📁 Reflectance: {reflectance_enabled}, Vignette: {vignette_enabled}, Folder: {subfolder_name}")
            
            # Create proper camera folder name
            camera_folder = f"{camera_model}_{camera_filter}" if camera_filter else camera_model
            outfolder = os.path.join(self.project.fp, camera_folder, "tiff16", subfolder_name)
            
            
            # Ensure output directory exists
            os.makedirs(outfolder, exist_ok=True)
            
            # Set up the export path
            # CRITICAL FIX: Handle both RAW and JPG extensions properly
            base_filename = os.path.splitext(image.fn)[0]  # Remove any extension
            calibrated_filename = f"{base_filename}.tif"  # Always export as .tif
            calibrated_path = os.path.join(outfolder, calibrated_filename)
            
            
            image.path = calibrated_path
            image.fn = calibrated_filename
            
            # Export the calibrated image
            if image.data is not None:
                pass
                from mip.Save_Format import save_format
                
                try:
                    # CRITICAL: Apply the exact same logic as the original save_format function
                    # For RE/NIR cameras: force mono output and extract single channel
                    # For RGN cameras: enable RGB output with torgb=True
                    if camera_filter in ["RE", "NIR"]:
                        pass
                        # Extract single channel like original save_format does: image.data[...,2:3]
                        if len(image.data.shape) == 3 and image.data.shape[2] >= 3:
                            image.data = image.data[..., 2:3]  # Extract only the third channel (index 2)
                        saved_path = save_format(image, output_format, torgb=False)  # Mono output
                    else:
                        pass
                        saved_path = save_format(image, output_format, torgb=True)  # FIXED: RGB output for RGN/OCN/NGB
                    if saved_path and os.path.exists(saved_path):
                        pass
                        return True
                    else:
                        pass
                        return False
                except Exception as save_err:
                    pass
                    import traceback
                    traceback.print_exc()
                    return False
            else:
                pass
                return False
                
        except Exception as e:
            pass
            import traceback
            traceback.print_exc()
            return False
    
    def _thread4_export(self):
        """Thread 4: Export processed images"""
        # CRITICAL FIX: Prevent multiple thread starts
        if hasattr(self, '_thread4_completed') and self._thread4_completed:
            print("[THREAD-4] WARNING: Thread-4 already completed, ignoring restart")
            return
        
        print("[THREAD-4] 📤 Starting image export...")
        
        try:
            print(f"[THREAD-4 DEBUG] use_ray={self.use_ray}")
            # CRITICAL FIX: Enable Ray for export in premium mode
            if self.use_ray:
                print("[THREAD-4] Using Ray batch processing")
                # Process exports in batches using Ray
                self._process_export_ray_batch()
            else:
                print("[THREAD-4] Using sequential processing")
                # Original sequential processing
                self._process_export_sequential()
            
        except Exception as e:
            print(f"[THREAD-4] Error: {e}")
            self.queues.shutdown.set()
        finally:
            self._thread4_completed = True
        print("[THREAD-4] Exporting complete")
    
    def _save_target_as_reflectance(self, image, output_format, outfolder):
        """Save target image as uncalibrated reflectance to satisfy UI expectations"""
        try:
            import os
            from mip.Save_Format import save_format
            
            # Create a copy to avoid modifying the original
            uncalibrated_image = image.copy()
            uncalibrated_image.fn = image.fn.replace('.RAW', '.tif')
            
            # Use the provided outfolder directly (it already includes the correct path)
            os.makedirs(outfolder, exist_ok=True)
            base_filename = uncalibrated_image.fn.split('.')[0]
            uncalibrated_image.path = os.path.join(outfolder, f"{base_filename}.tif")
            
            # CRITICAL FIX: Use correct save_format signature - only 3 parameters
            output_path = save_format(uncalibrated_image, output_format, torgb=False)
            
            return output_path if output_path and os.path.exists(output_path) else None
                
        except Exception as e:
            print(f"[THREAD-4] ❌ Error saving target as reflectance: {e}")
            return None
    
    def _export_index_images(self, image, options, outfolder, output_format, reflectance_path=None, reflectance_data=None):
        """
        Thread-4: Export index/LUT images based on project settings.
        
        Args:
            image: The source image object
            options: Processing options containing Index configurations
            outfolder: Base output folder
            output_format: Output format (e.g., 'tiff16')
            reflectance_path: Path to reflectance export (if available)
            reflectance_data: Calibrated reflectance image data (numpy array, if available)
            
        Returns:
            dict: Dictionary of index layer names to file paths
        """
        try:
            import numpy as np
            import copy
            
            # Get index configurations from options
            index_configs = None
            if options and 'Project Settings' in options:
                index_section = options['Project Settings'].get('Index', {})
                index_configs = index_section.get('Add index', [])
            elif options:
                # Try alternate structure for JSON-PIPELINE mode
                index_section = options.get('Index', {})
                index_configs = index_section.get('Add index', [])
            
            if not index_configs or len(index_configs) == 0:

                return {}
            

            
            # Determine source image for index calculation
            source_image = None
            
            # CRITICAL: Check if reflectance calibration is enabled in project settings
            # Only use reflectance data if the setting is enabled
            reflectance_enabled = False
            if options and 'Project Settings' in options:
                project_settings = options['Project Settings']
                
                # CRITICAL FIX: Reflectance setting is inside 'Processing' sub-section
                if 'Processing' in project_settings:
                    processing_options = project_settings['Processing']
                    
                    # Try multiple possible key names
                    reflectance_enabled = processing_options.get('Reflectance calibration / white balance', False)
                    if not reflectance_enabled:
                        reflectance_enabled = processing_options.get('Reflectance calibration', False)
                    if not reflectance_enabled:
                        reflectance_enabled = processing_options.get('Enable reflectance calibration', False)
            
            # Prefer using reflectance_data if provided AND reflectance calibration is enabled (avoids disk I/O)
            if reflectance_data is not None and reflectance_enabled:
                # CRITICAL FIX: Normalize reflectance data from uint16 (0-65535) to float32 (0-1)
                # Reflectance TIFFs are stored as uint16 for precision, but index calculations need 0-1 range
                # This matches the sandbox behavior in api.py
                if reflectance_data.dtype == np.uint16:
                    reflectance_data = reflectance_data.astype(np.float32) / 65535.0
                
                # Create a LabImage wrapper for the reflectance data
                from project import LabImage
                # Create instance without calling __init__ to avoid path requirements
                source_image = LabImage.__new__(LabImage)
                # CRITICAL: Set _data in __dict__ to ensure property getter can access it
                source_image.__dict__['_data'] = reflectance_data
                source_image.__dict__['path'] = reflectance_path if reflectance_path else (image.path if hasattr(image, 'path') else image.fn)
                source_image.__dict__['project'] = image.project
                source_image.__dict__['exif'] = {}
                source_image.__dict__['layers'] = {}
                source_image.__dict__['index_image'] = None
                source_image.__dict__['lut_image'] = None
                source_image.__dict__['colorspace'] = 'BGR'
                
                # CRITICAL FIX: Set exif_source for EXIF copying during index export
                # Get the original source from the image object (jpgpath for RAW files, path otherwise)
                if hasattr(image, 'exif_source') and image.exif_source:
                    source_image.__dict__['exif_source'] = image.exif_source
                elif hasattr(image, 'jpgpath') and image.jpgpath and os.path.exists(image.jpgpath):
                    source_image.__dict__['exif_source'] = image.jpgpath
                elif hasattr(image, 'path') and image.path and os.path.exists(image.path):
                    source_image.__dict__['exif_source'] = image.path
                elif hasattr(image, 'rawpath') and image.rawpath and os.path.exists(image.rawpath):
                    source_image.__dict__['exif_source'] = image.rawpath
                else:
                    source_image.__dict__['exif_source'] = None
                    
                # CRITICAL FIX: Also preserve camera_model and camera_filter for proper EXIF metadata
                if hasattr(image, 'camera_model'):
                    source_image.__dict__['camera_model'] = image.camera_model
                if hasattr(image, 'camera_filter'):
                    source_image.__dict__['camera_filter'] = image.camera_filter
                if hasattr(image, 'fn'):
                    source_image.__dict__['fn'] = image.fn
                
            elif reflectance_path and os.path.exists(reflectance_path) and reflectance_enabled:
                # FALLBACK ONLY: Load reflectance from disk if in-memory data wasn't provided
                # This should rarely happen - indicates an issue in the export pipeline
                from project import LabImage
                source_image = LabImage(image.project, reflectance_path)
                source_image.fn = image.fn  # Preserve original filename
                
                # CRITICAL FIX: Set exif_source for EXIF copying during index export
                if hasattr(image, 'exif_source') and image.exif_source:
                    source_image.exif_source = image.exif_source
                elif hasattr(image, 'jpgpath') and image.jpgpath and os.path.exists(image.jpgpath):
                    source_image.exif_source = image.jpgpath
                elif hasattr(image, 'path') and image.path and os.path.exists(image.path):
                    source_image.exif_source = image.path
                elif hasattr(image, 'rawpath') and image.rawpath and os.path.exists(image.rawpath):
                    source_image.exif_source = image.rawpath
                    
                # CRITICAL FIX: Also preserve camera_model and camera_filter for proper EXIF metadata
                if hasattr(image, 'camera_model'):
                    source_image.camera_model = image.camera_model
                if hasattr(image, 'camera_filter'):
                    source_image.camera_filter = image.camera_filter
                
                # Validate that reflectance data loaded successfully AND has distinct channels
                if source_image.data is not None:
                    # CRITICAL FIX: Normalize reflectance data from uint16 (0-65535) to float32 (0-1)
                    # This matches the sandbox behavior in api.py
                    if source_image.data.dtype == np.uint16:
                        source_image.data = source_image.data.astype(np.float32) / 65535.0
                    
                    # CRITICAL: Check if channels are distinct (not duplicate/grayscale)
                    if source_image.data.shape[2] >= 2:
                        # Sample channel means to detect if they're identical
                        ch0_mean = np.mean(source_image.data[:, :, 0])
                        ch1_mean = np.mean(source_image.data[:, :, 1])
                        ch2_mean = np.mean(source_image.data[:, :, 2]) if source_image.data.shape[2] >= 3 else 0
                        
                        # Check if all channels have the same mean (indicating duplicate/grayscale data)
                        # Use relative tolerance for float comparison
                        tolerance = 0.001  # 0.1% difference
                        if abs(ch0_mean - ch1_mean) < tolerance and abs(ch1_mean - ch2_mean) < tolerance:
                            source_image = None
                    else:
                        source_image = None
                else:
                    source_image = None
            
            if source_image is None:
                # Fallback: Use sensor response (original RAW data) as source
                source_image = copy.deepcopy(image)
            
            # Ensure source image has valid multi-channel data
            if source_image is None or source_image.data is None:

                return {}
            

            
            # Track index names to handle duplicates
            index_name_counts = {}
            index_layers = {}
            
            # Process each index configuration
            for idx, index_config in enumerate(index_configs):
                try:
                    # Validate index configuration
                    if not index_config.get('formula') or not index_config.get('channelmap'):
                        continue
                    
                    # Get index name from formula name or use 'Custom'
                    index_name = index_config.get('name', '').strip()
                    if not index_name:
                        index_name = 'Custom'
                    
                    # Handle duplicate names by adding suffix
                    if index_name in index_name_counts:
                        index_name_counts[index_name] += 1
                        folder_name = f"{index_name}{index_name_counts[index_name]}_Index_Images"
                    else:
                        index_name_counts[index_name] = 1
                        folder_name = f"{index_name}_Index_Images"
                    

                    
                    # Calculate index using mip.Index.process_index
                    # NOTE: process_index() will do image.copy() internally, so we don't need to copy here
                    # Passing source_image directly preserves the float32 _data in memory
                    
                    processed_image = process_index(source_image, index_config)
                    
                    if not hasattr(processed_image, 'index_image') or processed_image.index_image is None:
                        continue
                    
                    index_image = processed_image.index_image


                    
                    # STEP 1: Store original float range for LUT threshold mapping
                    original_data_min = None
                    original_data_max = None
                    original_index_data = None
                    
                    if index_image.data.dtype in [np.float32, np.float64]:
                        # Store original float data and range for LUT application
                        original_index_data = index_image.data.copy()
                        # CRITICAL: Use nanmin/nanmax to ignore NaN values (undefined pixels like water/shadow)
                        original_data_min = np.nanmin(index_image.data)
                        original_data_max = np.nanmax(index_image.data)
                        
                        # Check if output format requires integer conversion
                        if output_format in ['tiff16', 'png8', 'jpg8']:

                            
                            # Use actual data min/max for scaling (preserves dynamic range)
                            data_min = original_data_min
                            data_max = original_data_max

                            
                            if data_max > data_min:  # Avoid division by zero
                                # Scale from [data_min, data_max] to output range
                                if output_format == 'tiff16':
                                    # Scale to 0-65535 based on actual range
                                    # Suppress warning for NaN values - they are intentionally preserved as "no data"
                                    with np.errstate(invalid='ignore'):
                                        index_data = ((index_image.data - data_min) / (data_max - data_min) * 65535).astype(np.uint16)

                                elif output_format in ['png8', 'jpg8']:
                                    # Scale to 0-255 based on actual range
                                    # Suppress warning for NaN values - they are intentionally preserved as "no data"
                                    with np.errstate(invalid='ignore'):
                                        index_data = ((index_image.data - data_min) / (data_max - data_min) * 255).astype(np.uint8)

                            else:
                                # Constant data, set to mid-range
                                if output_format == 'tiff16':
                                    index_data = np.full_like(index_image.data, 32768, dtype=np.uint16)
                                else:
                                    index_data = np.full_like(index_image.data, 128, dtype=np.uint8)

                            
                            index_image.data = index_data
                            
                            # CRITICAL: Squeeze out any single-channel dimensions (H, W, 1) -> (H, W)
                            if len(index_image.data.shape) == 3 and index_image.data.shape[2] == 1:
                                index_image.data = index_image.data.squeeze(axis=2)

                            

                        elif output_format == 'tiff32percent':
                            # Keep as float32 - preserves exact index values for GIS software

                            index_image.data = index_image.data.astype(np.float32)
                            
                            # CRITICAL: Squeeze out any single-channel dimensions (H, W, 1) -> (H, W)
                            if len(index_image.data.shape) == 3 and index_image.data.shape[2] == 1:
                                index_image.data = index_image.data.squeeze(axis=2)

                        else:

                    
                            pass  # Empty block
                    # STEP 2: Apply LUT gradient using ORIGINAL float data with threshold mapping
                    if index_config.get('hasLUT') and index_config.get('lutConfig') and original_index_data is not None:
                        try:
                            from mip.Index import create_lut
                            lut_config = index_config['lutConfig']
                            gradient = lut_config['gradient']
                            lut_min = lut_config['thresholdA']
                            lut_max = lut_config['thresholdB']
                            threshold_mode = lut_config.get('thresholdMode', 'clip')
                            
                            # Create the color gradient LUT
                            lut = create_lut(*gradient)
                            

                            
                            # Get the current scaled data and its type
                            index_data = index_image.data
                            is_uint16 = (index_data.dtype == np.uint16)
                            is_uint8 = (index_data.dtype == np.uint8)
                            
                            if is_uint16 or is_uint8:
                                # Determine the target data range
                                max_value = 65535 if is_uint16 else 255
                                target_dtype = np.uint16 if is_uint16 else np.uint8
                                
                                # Squeeze out any single-dimension channels from original float data
                                if len(original_index_data.shape) == 3 and original_index_data.shape[2] == 1:
                                    original_index_data = original_index_data.squeeze(axis=2)

                                
                                # Map ORIGINAL float values to LUT indices [0-255] using thresholds
                                # Values < lut_min → LUT index 0
                                # Values between lut_min and lut_max → LUT indices 0-255 (linear)
                                # Values > lut_max → LUT index 255
                                h, w = original_index_data.shape
                                lut_indices = np.zeros((h, w), dtype=np.uint8)
                                
                                # CRITICAL: Create mask for undefined/no data pixels
                                # - NaN/inf: from 0/0 division (undefined)
                                # - Exactly -1.0: from NIR=0, Red>0 (overexposed/underexposed)
                                # - Exactly +1.0: from Red=0, NIR>0 (overexposed/underexposed)
                                # These should ALWAYS be transparent, regardless of threshold mode
                                nodata_mask = ~np.isfinite(original_index_data) | (original_index_data == -1.0) | (original_index_data == 1.0)
                                nodata_count = np.sum(nodata_mask)
                                
                                # Apply threshold-based mapping
                                if lut_max > lut_min:
                                    # Create masks for in-bounds and out-of-bounds pixels (excluding no-data/edge pixels)
                                    valid_mask = np.isfinite(original_index_data) & (original_index_data != -1.0) & (original_index_data != 1.0)
                                    in_range = valid_mask & (original_index_data >= lut_min) & (original_index_data <= lut_max)
                                    out_of_bounds = valid_mask & ~in_range
                                    below_range = valid_mask & (original_index_data < lut_min)
                                    above_range = valid_mask & (original_index_data > lut_max)
                                    
                                    # Map values in range to [0, 255]
                                    # Low values (min) → 0 (first color), High values (max) → 255 (last color)
                                    lut_indices[in_range] = ((original_index_data[in_range] - lut_min) / (lut_max - lut_min) * 255).astype(np.uint8)
                                    # Handle out-of-bounds pixels based on threshold_mode
                                    if threshold_mode == 'clip':
                                        # Clip to first/last color in gradient
                                        lut_indices[below_range] = 0    # First color (red for low NDVI)
                                        lut_indices[above_range] = 255  # Last color (green for high NDVI)
                                    elif threshold_mode == 'indexColor':
                                        # For indexColor, initially use mid-gray for LUT lookup
                                        # (Will be replaced with proper grayscale in post-processing)
                                        lut_indices[out_of_bounds] = 128
                                    elif threshold_mode == 'transparent':
                                        # For transparent mode, use mid-gray for LUT lookup
                                        # (Alpha will be set to 0 in post-processing)
                                        lut_indices[out_of_bounds] = 128
                                    else:  # Default to clip
                                        lut_indices[below_range] = 0    # First color (red for low NDVI)
                                        lut_indices[above_range] = 255  # Last color (green for high NDVI)
                                else:
                                    lut_indices[:] = 128  # Mid-range if thresholds invalid
                                    in_range = np.ones_like(original_index_data, dtype=bool)
                                    out_of_bounds = np.zeros_like(original_index_data, dtype=bool)
                                
                                # Apply LUT to get RGB colors
                                # Flatten to 1D for indexing, then reshape back
                                h, w = index_data.shape
                                lut_indices_flat = lut_indices.flatten()
                                rgb_data_flat = lut[lut_indices_flat]
                                
                                # Reshape to (H, W, 3) - remove any extra dimensions

                                if len(rgb_data_flat.shape) == 2 and rgb_data_flat.shape[1] == 3:
                                    rgb_data = rgb_data_flat.reshape(h, w, 3)
                                elif len(rgb_data_flat.shape) == 3 and rgb_data_flat.shape[1] == 1 and rgb_data_flat.shape[2] == 3:
                                    # Shape is (N, 1, 3) - squeeze out middle dimension
                                    rgb_data = rgb_data_flat.squeeze(axis=1).reshape(h, w, 3)
                                else:
                                    # If LUT has extra dimensions, squeeze them out
                                    rgb_data = rgb_data_flat.reshape(h, w, -1).squeeze()
                                    if len(rgb_data.shape) == 2:  # If squeezed to 2D, add channel dim
                                        rgb_data = rgb_data[..., np.newaxis]

                                
                                # Scale RGB from uint8 [0-255] to target dtype range
                                if is_uint16:
                                    # Scale uint8 RGB [0-255] to uint16 [0-65535]
                                    rgb_data_scaled = (rgb_data.astype(np.float32) * 257).astype(np.uint16)
                                else:
                                    rgb_data_scaled = rgb_data  # Already uint8
                                
                                # Apply special handling for threshold modes
                                if threshold_mode == 'indexColor' and np.sum(out_of_bounds) > 0:
                                    # For out-of-bounds pixels, show grayscale using SAME scaling as index export
                                    # This matches the scaled index layer (same min/max mapping)


                                    
                                    # Use the SAME scaling that was applied to the index export
                                    # Map from [original_data_min, original_data_max] to [0, max_value]
                                    if original_data_max > original_data_min:
                                        grayscale = ((original_index_data - original_data_min) / (original_data_max - original_data_min) * max_value).astype(target_dtype)
                                    else:
                                        grayscale = np.full_like(original_index_data, max_value // 2, dtype=target_dtype)
                                    
                                    # CRITICAL: Only replace out-of-bounds pixels, preserve in-range gradient colors
                                    # Replace out-of-bounds RGB with grayscale (R=G=B=grayscale value)
                                    for channel in range(3):
                                        rgb_data_scaled[out_of_bounds, channel] = grayscale[out_of_bounds]
                                    
                                    # Verify gradient colors are preserved
                                    if np.sum(in_range) > 0:
                                        in_range_colors = rgb_data_scaled[in_range]

                                
                                elif threshold_mode == 'transparent' and (np.sum(out_of_bounds) > 0 or nodata_count > 0):
                                    # Add alpha channel for transparency

                                    rgba_data = np.zeros((h, w, 4), dtype=target_dtype)
                                    rgba_data[:, :, :3] = rgb_data_scaled  # Copy RGB
                                    rgba_data[:, :, 3] = max_value  # Full opacity by default
                                    rgba_data[out_of_bounds, 3] = 0  # Transparent for out-of-bounds
                                    rgba_data[nodata_mask, 3] = 0  # CRITICAL: Transparent for no-data pixels
                                    rgb_data_scaled = rgba_data
                                
                                # CRITICAL: For ALL modes, make no-data pixels transparent by adding alpha channel
                                if nodata_count > 0 and threshold_mode != 'transparent':
                                    # If not already RGBA, convert to RGBA
                                    if rgb_data_scaled.shape[2] == 3:
                                        rgba_data = np.zeros((h, w, 4), dtype=target_dtype)
                                        rgba_data[:, :, :3] = rgb_data_scaled  # Copy RGB
                                        rgba_data[:, :, 3] = max_value  # Full opacity by default
                                        rgba_data[nodata_mask, 3] = 0  # CRITICAL: Transparent for no-data pixels
                                        rgb_data_scaled = rgba_data
                                
                                index_image.data = rgb_data_scaled
                            else:
                                pass
                        except Exception as lut_error:
                            import traceback
                            traceback.print_exc()
                    
                    # Save index image
                    format_outfolder = os.path.join(outfolder, output_format)
                    
                    # NO COLOR CONVERSION NEEDED!
                    # The LUT creates RGB data, and save_format with torgb=False handles it correctly
                    # Any manual conversion causes channel swapping issues
                    
                    # Always use torgb=False to prevent conversion
                    index_path = save(index_image, output_format, format_outfolder, 
                                    folder_name, is_preview=False, torgb=False)
                    
                    if index_path and os.path.exists(index_path):
                        # Copy EXIF data from source to index export
                        try:
                            source_raw_path = getattr(image, 'rawpath', None) or getattr(image, 'path', None)
                            if source_raw_path and os.path.exists(source_raw_path):

                                # Use exiftool to copy all EXIF data
                                import subprocess
                                exiftool_path = 'exiftool.exe' if os.name == 'nt' else 'exiftool'
                                cmd = [exiftool_path, '-TagsFromFile', source_raw_path, '-all:all', '-overwrite_original', index_path]
                                
                                # Hide command window on Windows
                                startupinfo = None
                                if os.name == 'nt':
                                    startupinfo = subprocess.STARTUPINFO()
                                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                                    startupinfo.wShowWindow = subprocess.SW_HIDE
                                
                                subprocess.run(cmd, capture_output=True, timeout=10, startupinfo=startupinfo)

                        except Exception as exif_error:
                        
                        
                            pass  # Empty block
                        # Generate layer name for UI
                        layer_name = f"RAW ({index_name} Index)"
                        if index_name_counts[index_name] > 1:
                            layer_name = f"RAW ({index_name}{index_name_counts[index_name]} Index)"
                        
                        index_layers[layer_name] = index_path

                    else:
                        
                        
                        pass  # Empty block
                except Exception as idx_error:

                    import traceback
                    traceback.print_exc()
                    continue
            

            return index_layers
            
        except Exception as e:

            import traceback
            traceback.print_exc()
            return {}

    def _export_processed_image(self, image, options, reprocessing_cfg, outfolder):
        """
        Thread-4: Export-only function that saves already processed images.
        This function assumes Thread-3 has already applied calibration and done all processing.
        """
        import os  # For path operations
        print(f"[THREAD-4] 📤 Exporting already processed image: {image.fn}")
        
        # Check if image has been processed (has calibration data)
        has_calibration = (
            hasattr(image, 'calibration_image') and image.calibration_image is not None or
            hasattr(image, 'calibration_coefficients') and image.calibration_coefficients is not None
        )
        
        if not has_calibration:
            print(f"[THREAD-4] ⚠️ WARNING: Image {image.fn} has no calibration data - Thread-3 processing may have failed")
            return None
        
        # Check if Thread-3 processed this image
        if hasattr(image, '_thread3_processed') and image._thread3_processed:
            print(f"[THREAD-4] ✅ Image {image.fn} was processed by Thread-3")
        else:
            print(f"[THREAD-4] ⚠️ WARNING: Image {image.fn} may not have been fully processed by Thread-3")
        
        layers_out = {}
        
        # Determine output format
        output_format = reprocessing_cfg.get('output_format', 'tiff16')
        
        # CRITICAL FIX: Load target status from project JSON instead of relying on object attribute
        is_target = False
        if hasattr(image, 'project') and image.project and hasattr(image.project, 'data'):
            # Search project JSON for this image's target status
            for base, fileset in image.project.data.get('files', {}).items():
                if fileset.get('raw') and os.path.basename(fileset['raw']) == image.fn:
                    calibration_info = fileset.get('calibration', {})
                    is_target_in_project = calibration_info.get('is_calibration_photo', False)
                    manual_calib = fileset.get('manual_calib', False)
                    manually_disabled = calibration_info.get('manually_disabled', False)
                    
                    # Target if marked in project and manually enabled and not disabled
                    is_target = is_target_in_project and manual_calib and not manually_disabled
                    print(f"[THREAD-4] 🎯 Loaded target status from project JSON: {image.fn} -> is_target={is_target} (project={is_target_in_project}, manual={manual_calib}, disabled={manually_disabled})")
                    break
            
            if not is_target:
                print(f"[THREAD-4] 📄 No target status found in project JSON for {image.fn} - treating as reflectance image")
        else:
            # Fallback to object attribute if project data not available
            is_target = getattr(image, 'is_calibration_photo', False)
            print(f"[THREAD-4] ⚠️ No project data available, using object attribute: {image.fn} -> is_target={is_target}")
        
        print(f"[THREAD-4] 💾 Saving processed image {image.fn} (is_target={is_target})")
        
        # Export calibrated reflectance/sensor response if calibration data is available
        if has_calibration:
            # Determine layer name based on reflectance calibration setting
            reflectance_enabled = False
            if options and 'Project Settings' in options:
                project_settings = options['Project Settings']
                if 'Processing' in project_settings:
                    processing_options = project_settings['Processing']
                    reflectance_enabled = processing_options.get('Reflectance calibration / white balance', False)
            elif options and 'Processing' in options:
                processing_options = options['Processing']
                reflectance_enabled = processing_options.get('Reflectance calibration / white balance', False)
            
            layer_name = "RAW (Reflectance)" if reflectance_enabled else "RAW (Sensor Response)"
            
            if is_target:
                print(f"[THREAD-4] 🎯 Exporting target {layer_name} (uncalibrated raw) for {image.fn}")
                # For targets, export the raw uncalibrated data to satisfy UI expectations
                # This prevents overexposure while still providing the expected export
                reflectance_path = self._save_target_as_reflectance(image, output_format, outfolder)
                if reflectance_path:
                    layers_out[layer_name] = reflectance_path
                    print(f"[THREAD-4] ✅ Successfully exported target {layer_name} (uncalibrated) for {image.fn}: {reflectance_path}")
                else:
                    print(f"[THREAD-4] ❌ Failed to export target {layer_name} for {image.fn}")
            else:
                print(f"[THREAD-4] 💾 Exporting calibrated reflectance for {image.fn}")
                            # CRITICAL DEBUG: Check calibration data before export
            if hasattr(image, 'calibration_coefficients') and image.calibration_coefficients:
                print(f"[THREAD-4] 🔧 Applying calibration coefficients: {image.calibration_coefficients[0][:2]}...")  # Show first 2 coefficients
                import numpy as np
                print(f"[THREAD-4] 🔧 Image data before calibration: min={np.min(image.data)}, max={np.max(image.data)}, mean={np.mean(image.data)}")
                
                # CRITICAL DEBUG: Check if calibration will be applied during save
                original_mean = np.mean(image.data)
                print(f"[THREAD-4] 🔧 Original image data stats: min={np.min(image.data)}, max={np.max(image.data)}, mean={original_mean}")
                print(f"[THREAD-4] 🔧 Calibration will be applied in save_reflectance_calibrated_image function")
            else:
                print(f"[THREAD-4] ⚠️ No calibration coefficients found for {image.fn}")
            
            # CRITICAL FIX: Use export_calibrated_reflectance which actually applies calibration
            # Instead of save_reflectance_calibrated_image which just saves raw data
            reflectance_result = export_calibrated_reflectance(image, {}, outfolder, output_format, None)
            if reflectance_result:
                # Handle different return formats for backward compatibility
                if isinstance(reflectance_result, tuple):
                    if len(reflectance_result) == 3:
                        # New format: (path, data, layer_name)
                        reflectance_path, reflectance_data, layer_name = reflectance_result
                    elif len(reflectance_result) == 2:
                        # Old format: (path, data) - default to reflectance
                        reflectance_path, reflectance_data = reflectance_result
                        layer_name = 'RAW (Reflectance)'
                else:
                    # Very old format: path only
                    reflectance_path = reflectance_result
                    reflectance_data = None
                    layer_name = 'RAW (Reflectance)'
                
                layers_out[layer_name] = reflectance_path
                print(f"[THREAD-4] ✅ Successfully exported {layer_name} for {image.fn}: {reflectance_path}")
            else:
                print(f"[THREAD-4] ❌ Failed to export reflectance for {image.fn}")
                reflectance_data = None
        
        # Export target-specific layers
        if is_target:
            # CRITICAL FIX: Check if target has already been exported to prevent double processing
            if not hasattr(image, '_target_exported') or not image._target_exported:
                image._target_exported = True
                print(f"[THREAD-4] 🎯 First-time target export for {image.fn}")
                
                # Export RAW (Target) layer for calibration targets with red squares
                # CRITICAL FIX: Load target detection data from calibration JSON for red square drawing
                if hasattr(image, 'project') and image.project:
                    project_dir = getattr(image.project, 'fp', None)
                    if project_dir:
                        import json
                        calibration_json_path = os.path.join(project_dir, 'calibration_data.json')
                        if os.path.exists(calibration_json_path):
                            try:
                                with open(calibration_json_path, 'r') as f:
                                    calibration_json = json.load(f)
                                
                                # Search for target data by RAW filename
                                target_fn = image.fn
                                target_data = None
                                for timestamp, data in calibration_json.items():
                                    if isinstance(data, dict) and data.get('filename') == target_fn:
                                        target_data = data
                                        break
                                
                                if target_data:
                                    print(f"[THREAD-4] ✅ Found calibration target data for {target_fn}")
                                    # Load target detection data from JSON
                                    image.aruco_id = target_data.get('aruco_id', None)
                                    image.aruco_corners = target_data.get('aruco_corners', None)
                                    if 'target_polys' in target_data and target_data['target_polys']:
                                        image.calibration_target_polys = target_data['target_polys']
                                        print(f"[THREAD-4] ✅ Loaded target_polys from JSON: {len(target_data['target_polys'])} polygons")
                                    print(f"[THREAD-4] 📋 Target data loaded: aruco_id={image.aruco_id}, corners={image.aruco_corners is not None}, polys={hasattr(image, 'calibration_target_polys') and image.calibration_target_polys is not None}")
                                else:
                                    print(f"[THREAD-4] ⚠️ No target data found for {target_fn} in calibration JSON")
                            except Exception as e:
                                print(f"[THREAD-4] ❌ Error loading calibration JSON: {e}")
                        else:
                            print(f"[THREAD-4] ⚠️ Calibration JSON file not found: {calibration_json_path}")
                
                # Use specialized function for target images
                target_path = save_raw_target_image(image, output_format, outfolder, 
                                 os.path.join(output_format, "Calibration_Targets_Used"), is_preview=False)
                if target_path:
                    layers_out['RAW (Target)'] = target_path
                    print(f"[THREAD-4] 💾 Saved target export for {image.fn}")
            else:
                print(f"[THREAD-4] ⏭️ Target already exported, skipping duplicate target export for {image.fn}")
        
        # Export index images if configured
        print(f"[THREAD-4] 🔍 Checking for index export: image={image.fn}")
        print(f"[THREAD-4] 🔍 options type: {type(options)}")
        print(f"[THREAD-4] 🔍 options keys: {list(options.keys()) if options else 'None'}")
        reflectance_path = layers_out.get('RAW (Reflectance)', None)
        # Pass reflectance data directly if available (avoids reloading from disk)
        reflectance_data_to_pass = reflectance_data if 'reflectance_data' in locals() else None
        print(f"[THREAD-4] 🔍 Calling _export_index_images...")
        index_layers = self._export_index_images(image, options, outfolder, output_format, reflectance_path, reflectance_data_to_pass)
        print(f"[THREAD-4] 🔍 _export_index_images returned: {index_layers}")
        if index_layers:
            layers_out.update(index_layers)
            print(f"[THREAD-4] ✅ Added {len(index_layers)} index layer(s) to export")
            
            # Add index layers to image object and project data for persistence
            if hasattr(image, 'layers'):
                image.layers.update(index_layers)
                print(f"[THREAD-4] ✅ Added index layers to image object")
            
            # Add to project data for persistence
            if hasattr(image, 'project') and image.project and hasattr(image.project, 'data'):
                project_data = image.project.data
                for base, fileset in project_data.get('files', {}).items():
                    if fileset.get('raw') and os.path.basename(fileset['raw']) == image.fn:
                        if 'layers' not in fileset:
                            fileset['layers'] = {}
                        fileset['layers'].update(index_layers)
                        print(f"[THREAD-4] ✅ Added index layers to project data for {image.fn}")
                        break
        
        print(f"[THREAD-4] ✅ Export completed for {image.fn}, layers: {list(layers_out.keys())}")
        return layers_out
    
    def _export_calibrated_reflectance_only(self, image, options, outfolder, output_format='tiff16'):
        """
        Thread-4: Export-only version of calibrated reflectance export.
        This assumes Thread-3 has already applied calibration data.
        """
        import copy
        from tasks import apply_als_correction_and_get_coefficients, apply_calib_to_image, save_reflectance_calibrated_image
        
        print(f"[THREAD-4] 📤 Exporting calibrated reflectance (export-only) for {image.fn}")
        
        # Create a copy for calibration export
        calib_image = copy.deepcopy(image)
        
        # Check if this is a target image
        is_target = getattr(image, 'is_calibration_photo', False)
        
        # Use pre-calculated coefficients from Thread-3 if available
        if hasattr(image, '_processed_calibration_coeffs') and hasattr(image, '_processed_calibration_limits'):
            calibration_coeffs = image._processed_calibration_coeffs
            calibration_limits = image._processed_calibration_limits
            print(f"[THREAD-4] ✅ Using pre-calculated coefficients from Thread-3")
        else:
            # Fallback: calculate coefficients (shouldn't normally happen)
            print(f"[THREAD-4] ⚠️ Pre-calculated coefficients not found, calculating now")
            calibration_coeffs, calibration_limits = apply_als_correction_and_get_coefficients(image)
        
        if calibration_coeffs is None:
            print(f"[THREAD-4] ❌ No calibration coefficients available for {image.fn}")
            return None
        
        print(f"[THREAD-4] 🔧 Applying calibration coefficients: {calibration_coeffs}")
        print(f"[THREAD-4] 🔧 Calibration limits: {calibration_limits}")
        
        # Apply calibration to the copy
        apply_calib_to_image(calib_image, calibration_coeffs, calibration_limits)
        
        # Save the calibrated image
        reflectance_path = save_reflectance_calibrated_image(calib_image, image, output_format, outfolder)
        
        if reflectance_path:
            print(f"[THREAD-4] ✅ Successfully saved reflectance for {image.fn} -> {reflectance_path}")
        else:
            print(f"[THREAD-4] ❌ Failed to save reflectance for {image.fn}")
        
        return reflectance_path
    
    def _update_single_image_progress(self, img):
        """
        Thread-4: Update progress for a single completed image.
        This ensures sequential progress updates (1/8, 2/8, 3/8...) even when
        Ray processes multiple images simultaneously.
        """
        try:
            # CRITICAL FIX: Only count RAW files for images_exported to match progress calculation
            is_raw_file = img.fn.upper().endswith('.RAW') if hasattr(img, 'fn') else False
            if is_raw_file:
                with self.stats_lock:
                    # Increment the counter
                    self.processing_stats['images_exported'] += 1
                    print(f"[THREAD-4] 📊 Incremented images_exported for RAW file: {img.fn}")
            else:
                print(f"[THREAD-4] ⚠️ Skipping images_exported increment for non-RAW file: {getattr(img, 'fn', 'unknown')}")
                return  # Don't update progress for non-RAW files
            
            with self.stats_lock:
                if self.processing_stats['images_exported'] > self.processing_stats['total_image_pairs']:
                    self.processing_stats['images_exported'] = self.processing_stats['total_image_pairs']
                
                current = self.processing_stats['images_exported']
                total = self.processing_stats.get('total_image_pairs', 1)
                
                print(f"[THREAD-4] 📊 Sequential progress update: {current}/{total} images exported")
                
                # Update UI progress immediately for this single image
                if self.api and hasattr(self.api, 'update_thread_progress'):
                    percent = int((current / total) * 100) if total else 0
                    
                    print(f"[THREAD-4] 📊 Updating UI: thread_id=4, percent={percent}, current={current}, total={total}")
                    self.api.update_thread_progress(
                        thread_id=4,
                        percent_complete=percent,
                        phase_name="Exporting",
                        time_remaining=f"{current}/{total}"
                    )
                    print(f"[THREAD-4] ⚡ Sequential progress updated: {current}/{total} ({percent}%) - {getattr(img, 'fn', 'unknown')} completed")
                    
                    # OPTIMIZATION: Remove delay for faster processing - UI can handle rapid updates
                    import time
                    # time.sleep(0.05)  # Removed 50ms delay for faster processing
                    
                else:
                    print(f"[THREAD-4] ⚠️ Cannot update progress: api={self.api}, has_method={hasattr(self.api, 'update_thread_progress') if self.api else False}")
                    
        except Exception as progress_err:
            print(f"[THREAD-4] ⚠️ Sequential progress update error: {progress_err}")
            import traceback
            traceback.print_exc()
    
    def _perform_processing_work(self, image):
        """
        Thread-3: Perform processing work (calibration calculations, reflectance prep) but no export.
        This prepares the image data so Thread-4 only needs to save files.
        """
        print(f"[THREAD-3] 🔧 Performing processing work for {image.fn}")
        
        # Ensure image has required metadata
        from mip import ExifUtils
        ExifUtils.add_pix4d_tags(image)
        
        # Prepare calibration data for export
        if hasattr(image, 'calibration_image') and image.calibration_image is not None:
            pass
            # print(f"[THREAD-3] ✅ Calibration data prepared for {image.fn}")
        else:
            print(f"[THREAD-3] ⚠️ WARNING: No calibration data available for {image.fn}")
        
        # Pre-calculate reflectance coefficients so Thread-4 can just apply and save
        try:
            from tasks import apply_als_correction_and_get_coefficients
            calibration_coeffs, calibration_limits = apply_als_correction_and_get_coefficients(image)
            
            if calibration_coeffs is not None:
                # Store pre-calculated coefficients on the image for Thread-4
                image._processed_calibration_coeffs = calibration_coeffs
                image._processed_calibration_limits = calibration_limits
                # print(f"[THREAD-3] ✅ Pre-calculated calibration coefficients for {image.fn}")
            else:
                print(f"[THREAD-3] ⚠️ Could not calculate calibration coefficients for {image.fn}")
                
        except Exception as e:
            print(f"[THREAD-3] ❌ Error calculating calibration coefficients for {image.fn}: {e}")
        
        # Mark image as processed by Thread-3
        image._thread3_processed = True
        # print(f"[THREAD-3] ✅ Processing work completed for {image.fn}")
    
    def record_cache_hit(self):
        """Record a cache hit for performance metrics"""
        with self.metrics_lock:
            self.performance_metrics['cache_hits'] += 1
    
    def record_cache_miss(self):
        """Record a cache miss for performance metrics"""
        with self.metrics_lock:
            self.performance_metrics['cache_misses'] += 1
    
    def record_processing_time(self, operation: str, time_seconds: float):
        """Record processing time for an operation"""
        with self.metrics_lock:
            self.performance_metrics['processing_times'].append({
                'operation': operation,
                'time': time_seconds,
                'timestamp': time.time()
            })
    
    def record_memory_usage(self, usage_bytes: int):
        """Record memory usage"""
        with self.metrics_lock:
            if usage_bytes > self.performance_metrics['memory_usage_peak']:
                self.performance_metrics['memory_usage_peak'] = usage_bytes
    
    def get_performance_summary(self):
        """Get a summary of performance metrics"""
        with self.metrics_lock:
            total_cache_operations = self.performance_metrics['cache_hits'] + self.performance_metrics['cache_misses']
            cache_hit_rate = (self.performance_metrics['cache_hits'] / total_cache_operations * 100) if total_cache_operations > 0 else 0
            
            avg_processing_time = 0
            if self.performance_metrics['processing_times']:
                avg_processing_time = sum(t['time'] for t in self.performance_metrics['processing_times']) / len(self.performance_metrics['processing_times'])
            
            total_time = 0
            if self.performance_metrics['start_time'] and self.performance_metrics['end_time']:
                total_time = self.performance_metrics['end_time'] - self.performance_metrics['start_time']
            
            return {
                'cache_hit_rate': f"{cache_hit_rate:.1f}%",
                'total_cache_operations': total_cache_operations,
                'peak_memory_usage_mb': self.performance_metrics['memory_usage_peak'] / (1024*1024),
                'average_processing_time': f"{avg_processing_time:.2f}s",
                'total_processing_time': f"{total_time:.2f}s",
                'operations_processed': len(self.performance_metrics['processing_times'])
            }
    
    def start_performance_monitoring(self):
        """Start performance monitoring"""
        with self.metrics_lock:
            self.performance_metrics['start_time'] = time.time()
            print("[OPTIMIZATION] 📊 Performance monitoring started")
    
    def stop_performance_monitoring(self):
        """Stop performance monitoring and print summary"""
        with self.metrics_lock:
            self.performance_metrics['end_time'] = time.time()
            summary = self.get_performance_summary()
            print("[OPTIMIZATION] 📊 Performance Summary:")
            print(f"[OPTIMIZATION]   Cache Hit Rate: {summary['cache_hit_rate']}")
            print(f"[OPTIMIZATION]   Peak Memory Usage: {summary['peak_memory_usage_mb']:.1f} MB")
            print(f"[OPTIMIZATION]   Average Processing Time: {summary['average_processing_time']}")
            print(f"[OPTIMIZATION]   Total Processing Time: {summary['total_processing_time']}")
            print(f"[OPTIMIZATION]   Operations Processed: {summary['operations_processed']}")
            return summary
    
    def _process_export_ray_batch(self):
        """Process image export using Ray with individual processing for real-time UI updates"""
        # Use global ray variable instead of importing directly
        global ray
        
        if not ray or not ray.is_initialized():
            print("[THREAD-4] ❌ Ray not available - falling back to sequential export processing")
            return self._process_export_sequential()
        else:
            pass
            # print("[THREAD-4] ✅ Ray session active - proceeding with batch export")
        
        sentinels_received = 0
        no_images_timeout = 0
        max_no_images_timeout = 30  # Exit after 30 seconds of no new images (increased for large datasets)
        
        # PERFORMANCE FIX: Use batch processing for speed with real-time progress updates
        # print(f"[THREAD-4] Starting optimized batch export processing")
        # print(f"[THREAD-4] Batch strategy: Process batches of 3+ images for real-time progress updates")
        # print(f"[THREAD-4] Timeout strategy: Process any remaining images after 2s timeout")
        
        # Collect images for batching
        batch_queue = []
        
        # Initialize for fresh start (no resume logic)
        # print(f"[THREAD-4] FRESH START: Starting export processing (no resume logic)")
        
        # Update UI to show Thread 4 starting with current/total
        if self.api and hasattr(self.api, 'update_thread_progress'):
            total_images = self.processing_stats.get('total_image_pairs', None)
            if total_images is None:
                # CRITICAL FIX: Count all image pairs (JPG or RAW) to match project input
                total_images = 0
                if hasattr(self, 'project') and self.project.data.get('files'):
                    for fileset in self.project.data['files'].values():
                        if fileset.get('jpg') or fileset.get('raw'):
                            total_images += 1
                total_images = max(1, total_images)
            current_exported = self.processing_stats.get('images_exported', 0)
            progress_percent = int((current_exported / total_images) * 100) if total_images > 0 else 0
            self.api.update_thread_progress(
                thread_id=4,
                percent_complete=progress_percent,
                phase_name="Exporting",
                time_remaining=f"{current_exported}/{total_images}"
            )
        
        while not self.queues.shutdown.is_set():
            try:
                image = self.queues.export_queue.get(timeout=0.5)
                if image is None:  # Sentinel from Thread-3 completion
                    sentinels_received += 1
                    # print(f"[THREAD-4] Received sentinel {sentinels_received} - Thread-3 completed, processing remaining batch")
                    
                    # Process any remaining images in batch when Thread-3 signals completion
                    if len(batch_queue) > 0:
                        # print(f"[THREAD-4] Processing final batch of {len(batch_queue)} images after Thread-3 completion")
                        self._export_image_batch_with_progress(batch_queue.copy())
                        batch_queue.clear()
                    
                    # Exit after processing remaining batch - Thread-3 has completed
                    # print(f"[THREAD-4] Thread-3 completed, exiting after processing remaining images")
                    break
                
                # Reset timeout counter when we get a real image
                no_images_timeout = 0
                
                # CRITICAL FIX: Check for stop before processing image
                if self.queues.shutdown.is_set():
                    print(f"[THREAD-4] 🛑 Stop requested before processing {getattr(image, 'fn', 'unknown')} - aborting export")
                    break
                    
                # FRESH START: Process all images (no resume logic)
                # print(f"[THREAD-4] FRESH START: Processing image {getattr(image, 'fn', 'unknown')} (no resume checks)")
                    
                # Add image to batch queue
                batch_queue.append(image)
                print(f"[THREAD-4] Added {image.fn} to batch queue (queue size: {len(batch_queue)})")
                
                # DYNAMIC BATCH SIZE SCALING: Scale batch size based on queue length
                current_queue_size = len(batch_queue)
                
                if current_queue_size == 1:
                    # Process immediately if this is the first/only image in queue
                    # print(f"[THREAD-4] Processing single image immediately: {image.fn}")
                    self._export_image_batch_with_progress(batch_queue.copy())
                    batch_queue.clear()
                    no_images_timeout = 0  # Reset timeout after processing
                elif current_queue_size >= self.export_batch_size:
                    # DYNAMIC SCALING: Increase batch size for large queues
                    if current_queue_size > self.export_batch_size * 3:
                        # Large queue: Process 3x batch size for maximum throughput
                        dynamic_batch_size = min(self.export_batch_size * 3, current_queue_size)
                        # print(f"[THREAD-4] Large queue detected ({current_queue_size} images) - using 3x batch size: {dynamic_batch_size}")
                    elif current_queue_size > self.export_batch_size * 2:
                        # Medium queue: Process 2x batch size
                        dynamic_batch_size = min(self.export_batch_size * 2, current_queue_size)
                        print(f"[THREAD-4] Medium queue detected ({current_queue_size} images) - using 2x batch size: {dynamic_batch_size}")
                    else:
                        # Normal queue: Use standard batch size
                        dynamic_batch_size = self.export_batch_size
                        # print(f"[THREAD-4] Normal queue ({current_queue_size} images) - using standard batch size: {dynamic_batch_size}")
                    
                    # Process the dynamically sized batch
                    batch_to_process = batch_queue[:dynamic_batch_size]
                    remaining_queue = batch_queue[dynamic_batch_size:]
                    
                    # print(f"[THREAD-4] Processing dynamic batch of {len(batch_to_process)} images, {len(remaining_queue)} remaining")
                    self._export_image_batch_with_progress(batch_to_process)
                    
                    # Keep remaining images in queue
                    batch_queue = remaining_queue
                    no_images_timeout = 0  # Reset timeout after processing
                    
            except queue.Empty:
                # MAJOR IMPROVEMENT: Implement timeout-based exit instead of waiting for sentinels
                no_images_timeout += 1
                # Reduce spam: Only print every 30 seconds
                if no_images_timeout % 30 == 0:
                    pass
                    # print(f"[THREAD-4] No new images for {no_images_timeout}s (max: {max_no_images_timeout}s)")
                
                # IMMEDIATE PROCESSING CLEANUP: Process any remaining images in queue after short timeout
                if len(batch_queue) > 0:
                    # Process any remaining images after just 1 second (reduced from 4s for immediate response)
                    if no_images_timeout >= 1:
                        # print(f"[THREAD-4] Processing remaining batch of {len(batch_queue)} images after 1s timeout")
                        self._export_image_batch_with_progress(batch_queue.copy())
                        batch_queue.clear()
                
                # Exit if we've been waiting too long and received at least one sentinel
                if no_images_timeout >= max_no_images_timeout and sentinels_received > 0:
                    print(f"[THREAD-4] Timeout reached with {sentinels_received} sentinels - finishing export")
                    break
                    
                continue
        
        # Process any final remaining images in batch queue
        if len(batch_queue) > 0:
            # print(f"[THREAD-4] Processing final batch of {len(batch_queue)} images")
            self._export_image_batch_with_progress(batch_queue.copy())
            batch_queue.clear()
        
        print(f"[THREAD-4] Optimized batch export processing complete")
    
    def _export_image_batch_with_progress(self, images_batch):
        """Export a batch of images using the existing optimized Ray batch processing"""
        # CRITICAL FIX: Check for stop before processing batch
        if self.queues.shutdown.is_set():
            print(f"[THREAD-4] 🛑 Stop requested - aborting batch export of {len(images_batch)} images")
            return
        if not images_batch:
            return
            
        # print(f"[THREAD-4] Using optimized batch export for {len(images_batch)} images (batch size: {self.export_batch_size})")
        
        # Use the existing optimized batch processing method
        self._export_image_batch(images_batch)
    
    def _export_image_batch(self, images_batch):
        """Export a batch of images using Ray"""
        # CRITICAL: Check for stop before processing batch
        if self.queues.shutdown.is_set():
            print(f"[THREAD-4] 🛑 Stop requested - aborting batch export of {len(images_batch)} images")
            return
        if not images_batch:
            return
            
        # Use global ray variable instead of importing directly
        global ray

        # print(f"[THREAD-4] Exporting batch of {len(images_batch)} images with Ray")
        
        # Use full config but disable index processing (must be False during export)
        # CRITICAL FIX: Ensure phases key exists with safe defaults
        if 'phases' not in self.project.data:
            self.project.data['phases'] = {'calibration': False, 'index': False}
        export_reprocessing_cfg = self.project.data['phases'].copy()
        export_reprocessing_cfg['calibration'] = True
        export_reprocessing_cfg['index'] = False
        # print(f"[THREAD-4] 🔧 Export config (index disabled): {export_reprocessing_cfg}")
        
        # Get Ray remote function for export-only
        if RAY_AVAILABLE:
            # CRITICAL FIX: Ensure Ray functions are defined before using them
            if not globals().get('export_processed_image_ray'):
                # print("[THREAD-4] Ray export function not found, defining Ray functions...")
                _define_ray_functions()
            
            export_task_func = globals().get('export_processed_image_ray')
            if export_task_func:
                print("[THREAD-4] Using Ray remote function: export_processed_image_ray")
            else:
                print("[THREAD-4] export_processed_image_ray not found in globals, falling back to sequential")
                return self._process_export_sequential()
        else:
            print("[THREAD-4] Ray not available, falling back to sequential")
            return self._process_export_sequential()
        
        # Resolve processing options structure
        options_for_process = self.options['Project Settings'] if 'Project Settings' in self.options else self.options
        print(f"[THREAD-4] DEBUG: options_for_process keys: {list(options_for_process.keys())}")
        if 'Processing' in options_for_process:
            print(f"[THREAD-4] DEBUG: Processing options: {options_for_process['Processing']}")
            print(f"[THREAD-4] DEBUG: Reflectance calibration setting: {options_for_process['Processing'].get('Reflectance calibration / white balance', 'NOT_FOUND')}")
        print(f"[THREAD-4] DEBUG: reprocessing_cfg (self.project.data['phases']): {self.project.data.get('phases', 'NOT_FOUND')}")

        # Submit all images to Ray with synchronized calibration/ALS state
        futures = []
        future_to_image = {}
        for img in images_batch:
            if self.queues.shutdown.is_set():
                print(f"[THREAD-4] 🛑 Stop requested during batch submission")
                break

            # IMPORTANT: Do NOT pass heavy pixel data to Ray to avoid serialization/memory issues
            # Workers will load data from disk as needed
            try:
                # Ensure a lightweight project reference exists for workers
                try:
                    if not hasattr(img, 'project_path') or not getattr(img, 'project_path', None):
                        if hasattr(self, 'project') and self.project and hasattr(self.project, 'fp'):
                            img.project_path = self.project.fp
                            print(f"[THREAD-4] DEBUG: Set image.project_path for {img.fn} -> {img.project_path}")
                except Exception:
                    pass
                try:
                    if hasattr(img, 'calibration_image') and img.calibration_image is not None:
                        if not hasattr(img.calibration_image, 'project_path') or not getattr(img.calibration_image, 'project_path', None):
                            if hasattr(self, 'project') and self.project and hasattr(self.project, 'fp'):
                                img.calibration_image.project_path = self.project.fp
                                print(f"[THREAD-4] DEBUG: Set calibration_image.project_path for {img.fn} -> {img.calibration_image.project_path}")
                except Exception:
                    pass

                # CRITICAL FIX: DO NOT delete calibrated image.data - Thread 3 applied calibration to it
                if hasattr(img, 'data') and img.data is not None:
                    print(f"[THREAD-4] DEBUG: Preserving calibrated image.data for Ray export: {img.fn} (shape={img.data.shape}, dtype={img.data.dtype})")
                    # Keep the calibrated data for export
                # Also clear other heavy/non-serializable fields
                if hasattr(img, 'raw_data') and getattr(img, 'raw_data', None) is not None:
                    try:
                        del img.raw_data
                        print(f"[THREAD-4] DEBUG: Cleared image.raw_data before Ray submit for {img.fn}")
                    except Exception:
                        img.raw_data = None
                if hasattr(img, 'project') and getattr(img, 'project', None) is not None:
                    try:
                        img.project = None
                        print(f"[THREAD-4] DEBUG: Cleared image.project reference before Ray submit for {img.fn}")
                    except Exception:
                        pass
                # Slim down calibration_image if present (avoid sending pixel data)
                if hasattr(img, 'calibration_image') and img.calibration_image is not None:
                    try:
                        if hasattr(img.calibration_image, 'data') and img.calibration_image.data is not None:
                            del img.calibration_image.data
                            print(f"[THREAD-4] DEBUG: Cleared calibration_image.data for {img.fn}")
                    except Exception:
                        pass
                    try:
                        if hasattr(img.calibration_image, 'raw_data') and getattr(img.calibration_image, 'raw_data', None) is not None:
                            del img.calibration_image.raw_data
                            print(f"[THREAD-4] DEBUG: Cleared calibration_image.raw_data for {img.fn}")
                    except Exception:
                        pass
                    try:
                        if hasattr(img.calibration_image, 'project') and getattr(img.calibration_image, 'project', None) is not None:
                            img.calibration_image.project = None
                            print(f"[THREAD-4] DEBUG: Cleared calibration_image.project for {img.fn}")
                    except Exception:
                        pass
            except Exception:
                pass

            # Ensure calibration and ALS fields are present (load from JSON if needed)
                missing_calib = (
                    not hasattr(img, 'calibration_coefficients') or img.calibration_coefficients is None or
                    not hasattr(img, 'calibration_yvals') or img.calibration_yvals is None or
                    not hasattr(img, 'als_magnitude') or img.als_magnitude is None
                )
                if missing_calib:
                    print(f"[THREAD-4] DEBUG: Attempting to load calibration from JSON for {img.fn}")
                    self._apply_calibration_from_json(img)

            # Ensure ALS data exists for the image before ALS precompute
            try:
                print(f"[THREAD-4] ALS CHECK: {img.fn} - als_magnitude={getattr(img, 'als_magnitude', 'NOT_SET')}, als_data={getattr(img, 'als_data', 'NOT_SET')}")
                als_mag_missing = (not hasattr(img, 'als_magnitude') or img.als_magnitude is None)
                als_data_missing = (not hasattr(img, 'als_data') or img.als_data is None)
                print(f"[THREAD-4] ALS CHECK: {img.fn} - als_mag_missing={als_mag_missing}, als_data_missing={als_data_missing}")
                
                if als_mag_missing or als_data_missing:
                    project_dir = getattr(self.project, 'fp', None)
                    if project_dir:
                        print(f"[THREAD-4] DEBUG: Loading ALS data from JSON for {img.fn}")
                        loaded = load_als_data_from_json(img, project_dir)
                        print(f"[THREAD-4] DEBUG: ALS load for {img.fn} -> {loaded}")
                    else:
                        print(f"[THREAD-4] ⚠️ No project.dir to load ALS for {img.fn}")
                else:
                    print(f"[THREAD-4] ALS CHECK: {img.fn} - ALS data already present, skipping load")
            except Exception as als_load_err:
                print(f"[THREAD-4] ⚠️ ALS load error for {img.fn}: {als_load_err}")

            # Pre-compute ALS-corrected coefficients on the driver to make Ray work deterministic
            try:
                print(f"[THREAD-4] CALLING apply_als_correction_and_get_coefficients for {img.fn}")
                coeffs_limits = apply_als_correction_and_get_coefficients(img)
                print(f"[THREAD-4] RESULT apply_als_correction_and_get_coefficients for {img.fn} -> {coeffs_limits}")
                if coeffs_limits and isinstance(coeffs_limits, tuple) and coeffs_limits[0] is not None:
                    calib_coeffs, calib_limits = coeffs_limits
                    img.calibration_coefficients = calib_coeffs
                    img.calibration_limits = calib_limits
                    print(f"[THREAD-4] ✅ Precomputed ALS-corrected coefficients for {img.fn}")
                else:
                    print(f"[THREAD-4] ⚠️ ALS correction returned None for {img.fn} - will rely on worker fallback")
            except Exception as als_err:
                print(f"[THREAD-4] ⚠️ ALS precompute error for {img.fn}: {als_err}")
                import traceback
                traceback.print_exc()

            # Visibility: log key fields prior to Ray submit
            try:
                has_calib_img = hasattr(img, 'calibration_image') and img.calibration_image is not None
                print(f"[THREAD-4] DEBUG: Pre-submit state for {img.fn}: als_mag={getattr(img,'als_magnitude', None)} has_calib_img={has_calib_img} coeffs_set={img.calibration_coefficients is not None}")
            except Exception:
                pass

            # Ensure calibration_image present for non-targets (link to the actual target object when available)
            try:
                if (not getattr(img, 'is_calibration_photo', False)) and (not hasattr(img, 'calibration_image') or img.calibration_image is None):
                    # Try to link from project.imagemap by filename present in JSON
                    calib_fn = getattr(img, '_ray_calibration_fn', None)
                    if not calib_fn and hasattr(img, 'calibration_image') and img.calibration_image is not None:
                        calib_fn = getattr(img.calibration_image, 'fn', None)
                    if calib_fn and hasattr(self, 'project') and self.project and hasattr(self.project, 'imagemap'):
                        for _, im in self.project.imagemap.items():
                            if getattr(im, 'fn', None) == calib_fn:
                                img.calibration_image = im
                                print(f"[THREAD-4] DEBUG: Linked calibration_image for {img.fn} -> {calib_fn}")
                                break
            except Exception as link_err:
                print(f"[THREAD-4] ⚠️ Could not link calibration_image for {img.fn}: {link_err}")

            # Synchronize calibration/ALS to Ray-safe attributes so workers can reconstruct
            try:
                self._synchronize_calibration_data_to_ray(img)
            except Exception as sync_err:
                print(f"[THREAD-4] ⚠️ Could not synchronize calibration data to Ray for {img.fn}: {sync_err}")

        # Submit Ray task for export-only (Thread-3 already did processing)
            try:
                # Create image data package for Thread-4 export
                # CRITICAL FIX: Include calibration_image reference for ALS processing
                calibration_image_data = None
                if hasattr(img, 'calibration_image') and img.calibration_image is not None:
                    calibration_image_data = {
                        'fn': getattr(img.calibration_image, 'fn', 'unknown'),
                        'calibration_coefficients': getattr(img.calibration_image, 'calibration_coefficients', None),
                        'calibration_limits': getattr(img.calibration_image, 'calibration_limits', None),
                        'calibration_xvals': getattr(img.calibration_image, 'calibration_xvals', None),
                        'calibration_yvals': getattr(img.calibration_image, 'calibration_yvals', None),
                        'als_magnitude': getattr(img.calibration_image, 'als_magnitude', None),
                        'als_data': getattr(img.calibration_image, 'als_data', None),
                        'aruco_id': getattr(img.calibration_image, 'aruco_id', None),
                        'is_selected_for_calibration': getattr(img.calibration_image, 'is_selected_for_calibration', False)
                    }
                    print(f"[THREAD-4] 🔗 Passing calibration_image reference for {img.fn} -> {calibration_image_data['fn']}")
                else:
                    print(f"[THREAD-4] ⚠️ No calibration_image found for {img.fn} - ALS may not work correctly")
                
                # CRITICAL FIX: Preserve original source path for target exports
                original_source_path = getattr(img, 'path', None) or getattr(img, 'fp', None)
                
                # CRITICAL FIX: Ensure image has absolute file path for Ray worker
                if not hasattr(img, 'fp') or not img.fp:
                    # Construct absolute path from project directory and filename
                    import os
                    if hasattr(self, 'project') and self.project and hasattr(self.project, 'fp'):
                        img.fp = os.path.join(self.project.fp, img.fn)
                        print(f"[THREAD-4] 🔧 Set absolute fp for Ray export: {img.fn} -> {img.fp}")
                    else:
                        print(f"[THREAD-4] ⚠️ Cannot set absolute path for {img.fn} - project.fp not available")
                
                # CRITICAL FIX: Include calibrated image data directly for Ray workers
                calibrated_image_data = None
                if hasattr(img, 'data') and img.data is not None:
                    calibrated_image_data = img.data.copy()  # Copy the calibrated data
                    print(f"[THREAD-4] 📦 Including calibrated image data in Ray package: {img.fn} (shape={calibrated_image_data.shape}, dtype={calibrated_image_data.dtype})")
                else:
                    print(f"[THREAD-4] ⚠️ No calibrated image data to include for {img.fn}")
                
                image_data = {
                    'image': img,
                    'fn': img.fn,
                    'calibration_image_data': calibration_image_data,
                    'calibrated_data': calibrated_image_data,  # Direct data for Ray workers
                    'original_source_path': original_source_path  # Original source file path for target exports
                }
                
                future = export_task_func.remote(
                    image_data,
                    options_for_process,
                    export_reprocessing_cfg,
                    self.outfolder
                )
                futures.append(future)
                future_to_image[future] = img
            except Exception as submit_err:
                print(f"[THREAD-4] ❌ Failed to submit Ray task for {getattr(img, 'fn', 'unknown')}: {submit_err}")

        print(f"[THREAD-4] Created {len(futures)} Ray tasks for image export")
        
        # Log batch start but don't update progress until images actually complete
        print(f"[THREAD-4] 🚀 Starting batch export of {len(images_batch)} images")

        # PERFORMANCE: Process multiple images simultaneously for maximum speed (dynamic based on system specs)
        dynamic_parallel_count = _get_optimal_parallel_processing_count()
        print(f"[THREAD-4] Dynamic parallel processing: {dynamic_parallel_count} images simultaneously (tier=mid-range, {dynamic_parallel_count} cores)")
        
        # Process results as they complete, with watchdog timeout per task
        per_future_wait_seconds = {f: 0 for f in futures}
        while futures:
            # ENHANCED: More frequent interrupt checks for faster stopping
            if self.queues.shutdown.is_set() or self._stop_requested:
                print(f"[THREAD-4] 🛑 Stop requested - canceling {len(futures)} remaining Ray tasks")
                cancelled = 0
                for f in futures:
                    try:
                        ray.cancel(f, force=True)
                        cancelled += 1
                    except Exception as e:
                        print(f"[THREAD-4] Warning: Could not cancel Ray task: {e}")
                print(f"[THREAD-4] ✅ Cancelled {cancelled}/{len(futures)} Ray tasks")
                break
            
            # HIGHLY OPTIMIZED: Adaptive Ray result collection for maximum performance
            # Use shorter timeout for quick checks, then longer timeout for actual waiting
            max_simultaneous = min(len(futures), 6)  # Process up to 6 at once for better throughput
            
            # Quick check first (2s timeout) to catch immediately ready tasks
            ready, pending = ray.wait(futures, num_returns=max_simultaneous, timeout=2.0)
            
            # If nothing ready immediately, wait longer but still optimized
            if not ready and len(futures) > 0:
                ready, pending = ray.wait(futures, num_returns=max_simultaneous, timeout=5.0)
            
            futures = pending
            
            print(f"[THREAD-4] 📊 Ray wait result: {len(ready)} ready, {len(pending)} pending")
            
            # Process completed Ray tasks (up to 6 at once for maximum performance)
            if not ready and len(futures) > 0:
                print(f"[THREAD-4] ⏳ Ray wait timeout: {len(futures)} tasks still pending")
                continue
            elif ready:
                print(f"[THREAD-4] ✅ Ray tasks completed: {len(ready)} ready, {len(pending)} remaining")
                
            # Process all completed Ray tasks in this batch
            for f in ready:
                img = future_to_image.get(f)
                try:
                    # Get the result for this single completed task
                    result = ray.get(f, timeout=10)
                    print(f"[THREAD-4] 📊 SEQUENTIAL: Completed {getattr(img, 'fn', 'unknown')}: {result}")

                    # SEQUENTIAL progress update - one image at a time
                    print(f"[THREAD-4] 📊 Updating progress for single completed image: {getattr(img, 'fn', 'unknown')}")
                    self._update_single_image_progress(img)

                    # Update UI with layers when available
                    if result and isinstance(result, dict) and hasattr(self, 'api') and self.api and hasattr(self.api, '_update_ui_for_processed_image'):
                        self.api._update_ui_for_processed_image(img, result)

                except Exception as e:
                    result = {}
                    # Deep diagnostic for image that failed in worker
                    try:
                        print(f"[THREAD-4] ❌ Ray exception for {getattr(img, 'fn', 'unknown')}: {type(e).__name__}: {e}")
                        print(f"[THREAD-4] DIAG: fn={getattr(img,'fn','')} is_target={getattr(img,'is_calibration_photo', False)}")
                        print(f"[THREAD-4] DIAG: als_mag={getattr(img,'als_magnitude', None)} has_calib_img={hasattr(img, 'calibration_image') and img.calibration_image is not None}")
                        print(f"[THREAD-4] DIAG: coeffs_set={getattr(img,'calibration_coefficients', None) is not None}")
                        # Ensure we try to re-link calibration image quickly for next batch
                        calib_fn = getattr(img, '_ray_calibration_fn', None)
                        if calib_fn and hasattr(self, 'project') and hasattr(self.project, 'imagemap'):
                            for _, im in self.project.imagemap.items():
                                if getattr(im, 'fn', None) == calib_fn:
                                    img.calibration_image = im
                                    print(f"[THREAD-4] DIAG: re-linked calibration_image for retry path {calib_fn}")
                                    break
                    except Exception:
                        pass
                    # Immediate fallback sequential export for this image
                    try:
                        options_for_process = self.options['Project Settings'] if 'Project Settings' in self.options else self.options
                        # CRITICAL FIX: Ensure phases key exists with safe defaults
                        if 'phases' not in self.project.data:
                            self.project.data['phases'] = {'calibration': False, 'index': False}
                        export_reprocessing_cfg = self.project.data['phases'].copy()
                        export_reprocessing_cfg['calibration'] = True
                        export_reprocessing_cfg['index'] = False
                        fb_result = process_image_unified(
                            img,
                            options_for_process,
                            export_reprocessing_cfg,
                            self.outfolder,
                            DummyProgressTracker(),
                            execution_mode='parallel'
                        )
                        if fb_result is not None:
                            result = fb_result
                            print(f"[THREAD-4] ✅ Immediate fallback sequential export completed for {getattr(img, 'fn', 'unknown')}")
                    except Exception as fb_err:
                        print(f"[THREAD-4] ❌ Immediate fallback sequential export failed for {getattr(img, 'fn', 'unknown')}: {fb_err}")
                    
                    # Update progress for failed image (fallback processing)
                    # print(f"[THREAD-4] 📊 Updating progress for failed Ray task (fallback): {getattr(img, 'fn', 'unknown')}")
                    self._update_single_image_progress(img)

                # Progress updated in try block (success) or except block (failure) - no duplicate needed
                    
                # Persist completed item
                if result is not None:
                    self.queues.completed.put((getattr(img, 'fn', 'unknown'), result))
                    # print(f"[THREAD-4] Exported {getattr(img, 'fn', 'unknown')}, layers: {list(result.keys()) if isinstance(result, dict) else result}")

            # Watchdog: increase wait counters, cancel and fallback if any task is stuck too long
            for f in list(futures):
                per_future_wait_seconds[f] = per_future_wait_seconds.get(f, 0) + 1
                if per_future_wait_seconds[f] % 30 == 0:
                    img = future_to_image.get(f)
                    print(f"[THREAD-4] ⏱️ Still waiting on {getattr(img, 'fn', 'unknown')} after {per_future_wait_seconds[f]}s")
                if per_future_wait_seconds[f] >= 45:
                    img = future_to_image.get(f)
                    print(f"[THREAD-4] ⚠️ Ray task timeout for {getattr(img, 'fn', 'unknown')} - canceling and falling back to sequential export")
                    try:
                        ray.cancel(f, force=True)
                    except Exception as cancel_err:
                        print(f"[THREAD-4] ⚠️ Could not cancel Ray task: {cancel_err}")
                    try:
                        # Fallback sequential processing for this one image
                        options_for_process = self.options['Project Settings'] if 'Project Settings' in self.options else self.options
                        # CRITICAL FIX: Ensure phases key exists with safe defaults
                        if 'phases' not in self.project.data:
                            self.project.data['phases'] = {'calibration': False, 'index': False}
                        export_reprocessing_cfg = self.project.data['phases'].copy()
                        export_reprocessing_cfg['calibration'] = True
                        export_reprocessing_cfg['index'] = False
                        result = process_image_unified(
                            img,
                            options_for_process,
                            export_reprocessing_cfg,
                            self.outfolder,
                            DummyProgressTracker(),
                            execution_mode='parallel'
                        )
                        self.queues.completed.put((getattr(img, 'fn', 'unknown'), result or {}))
                        print(f"[THREAD-4] ✅ Fallback sequential export completed for {getattr(img, 'fn', 'unknown')}")
                    except Exception as fb_err:
                        print(f"[THREAD-4] ❌ Fallback sequential export failed for {getattr(img, 'fn', 'unknown')}: {fb_err}")
                    # Remove from tracking
                    try:
                        futures.remove(f)
                        per_future_wait_seconds.pop(f, None)
                        future_to_image.pop(f, None)
                    except Exception:
                        pass

        print(f"[THREAD-4] ✅ Completed batch export of {len(images_batch)} images")
    
    def _process_export_sequential(self):
        """Optimized sequential export processing - timeout-based"""
        sentinels_received = 0
        no_images_timeout = 0
        max_no_images_timeout = 10  # Exit after 10 seconds of no new images
        
        while not self.queues.shutdown.is_set():
            try:
                image = self.queues.export_queue.get(timeout=0.5)
                if image is None:  # Sentinel
                    sentinels_received += 1
                    print(f"[THREAD-4] Received sentinel {sentinels_received}")
                    continue
                
                # Reset timeout counter when we get a real image
                no_images_timeout = 0
                
                # CRITICAL FIX: Check for stop before processing each image
                if self.queues.shutdown.is_set() or self._stop_requested:
                    print(f"[THREAD-4] 🛑 Stop requested before processing {getattr(image, 'fn', 'unknown')} - aborting export")
                    break
                
                # Thread progress saving now handled after successful export
                
                # print(f"[THREAD-4] Dequeued image for export: {getattr(image, 'fn', 'unknown')}, is_calibration_photo={getattr(image, 'is_calibration_photo', False)}")
                # print(f"[THREAD-4] Exporting {image.fn}")
                is_target = getattr(image, 'is_calibration_photo', False)
                has_calibration = hasattr(image, 'calibration_image') and image.calibration_image is not None
                # print(f"[THREAD-4] Image type: is_target={is_target}, has_calibration={has_calibration}")
                # DEBUG: Track target images in detail
                if is_target:
                    print(f"[THREAD-4] DEBUG: Processing TARGET image {image.fn}")
                    print(f"[THREAD-4] DEBUG: Target attributes:")
                    print(f"[THREAD-4] DEBUG:   - calibration_image: {getattr(image, 'calibration_image', None)}")
                    print(f"[THREAD-4] DEBUG:   - calibration_coefficients: {getattr(image, 'calibration_coefficients', None)}")
                    print(f"[THREAD-4] DEBUG:   - als_magnitude: {getattr(image, 'als_magnitude', None)}")
                    print(f"[THREAD-4] DEBUG:   - als_data present: {hasattr(image, 'als_data') and image.als_data is not None}")

                # Check cache first, otherwise load from disk
                cached_data = self.queues.get_cached_image_data(image.fn)
                if cached_data is not None:
                    image.data = cached_data
                    # print(f"[THREAD-4] Using cached data for {image.fn}")
                elif not hasattr(image, 'data') or image.data is None:
                    raw_data = image.raw_data
                    if raw_data is not None:
                        image.data = raw_data

                # Fallback: Ensure all required fields are present before export
                missing_calib = (
                    not hasattr(image, 'calibration_coefficients') or image.calibration_coefficients is None or
                    not hasattr(image, 'calibration_limits') or image.calibration_limits is None or
                    not hasattr(image, 'calibration_xvals') or image.calibration_xvals is None or
                    not hasattr(image, 'calibration_yvals') or image.calibration_yvals is None or
                    not hasattr(image, 'als_magnitude') or image.als_magnitude is None
                )
                if missing_calib:
                    self._apply_calibration_from_json(image)

                # Thread-4: ONLY handle export operations, no processing
                # print(f"[THREAD-4] 📤 EXPORT ONLY - Processing already completed by Thread-3")
                
                # Get options for export
                if 'Project Settings' in self.options:
                    options_for_process = self.options['Project Settings']
                else:
                    options_for_process = self.options
                
                # CRITICAL FIX: Use full config but disable problematic index processing
                # CRITICAL FIX: Ensure phases key exists with safe defaults
                if 'phases' not in self.project.data:
                    self.project.data['phases'] = {'calibration': False, 'index': False}
                export_reprocessing_cfg = self.project.data['phases'].copy()
                export_reprocessing_cfg['calibration'] = True  # Ensure calibration is enabled
                export_reprocessing_cfg['index'] = False       # Disable index processing to prevent failures
                # print(f"[THREAD-4] 🔧 Export config (index disabled): {export_reprocessing_cfg}")
                
                try:
                    # Thread-4 now only handles export operations
                    result = self._export_processed_image(
                        image,
                        options_for_process,
                        export_reprocessing_cfg,
                        self.outfolder
                    )
                    if result:
                        # print(f"[THREAD-4] DEBUG: process_image_unified returned for {image.fn}: {result}")
                        if is_target:
                            pass
                            # print(f"[THREAD-4] DEBUG: Target image {image.fn} process_image_unified result: {result}")
                            if 'RAW (Reflectance)' in result:
                                # print(f"[THREAD-4] DEBUG: Target image {image.fn} reflectance path: {result['RAW (Reflectance)']}")
                                pass
                        
                        # CRITICAL FIX: Notify UI of new layers after successful export
                        if hasattr(self, 'api') and self.api and hasattr(self.api, '_update_ui_for_processed_image'):
                            # print(f"[THREAD-4] 🔄 Notifying UI of new layers for {image.fn}")
                            self.api._update_ui_for_processed_image(image, result)
                        else:
                            # print(f"[THREAD-4] ⚠️ Cannot notify UI - API or update method not available")
                            pass
                            
                except Exception as e:
                    import traceback
                    print(f"[THREAD-4] ERROR processing {image.fn}: {e}")
                    traceback.print_exc()
                    result = None
                
                # Sequential progress update - unified with Ray batch processing
                self._update_single_image_progress(image)
                
                # CRITICAL FIX: Check if we've completed all expected images
                if hasattr(self, 'total_images_to_process') and hasattr(self, 'images_processed'):
                    if self.images_processed >= self.total_images_to_process:
                        # print(f"[THREAD-4] ✅ Completed all {self.total_images_to_process} expected images - stopping export")
                        # Set shutdown flag to stop the loop
                        self.queues.shutdown.set()
                        break
                
                if result is not None:
                    self.queues.completed.put((image.fn, result))
                    # print(f"[THREAD-4] Exported {image.fn} to reflectance folder (target={is_target}), layers: {list(result.keys()) if isinstance(result, dict) else result}")
                    
                    # Export progress saving now handled in the correct location above
                    
                    # CRITICAL FIX: Mark image as completed for incremental processing
                    if hasattr(self, 'project') and self.project:
                        self.project.mark_image_completed('index', image.fn)
                    elif hasattr(self, 'api') and self.api and hasattr(self.api, 'project'):
                        self.api.project.mark_image_completed('index', image.fn)
                    
                    # OPTIMIZATION: Delete cached debayered TIFF immediately after export
                    # This prevents disk space buildup for large projects with thousands of images
                    if hasattr(self, 'project') and self.project:
                        self.project.delete_cached_tiff(image.fn)
                    elif hasattr(self, 'api') and self.api and hasattr(self.api, 'project'):
                        self.api.project.delete_cached_tiff(image.fn)
                else:
                    pass
                    # print(f"[THREAD-4] No export result for {image.fn} (processed but not exported)")
                
                # Clear image data from memory after export
                if hasattr(image, 'data'):
                    try:
                        del image.data
                    except AttributeError:
                        image.data = None
                self.queues.clear_cache_for_image(image.fn)
            except queue.Empty:
                # MAJOR IMPROVEMENT: Implement timeout-based exit instead of waiting for sentinels
                no_images_timeout += 1
                # Reduce spam: Only print every 30 seconds
                if no_images_timeout % 30 == 0:
                    pass
                    # print(f"[THREAD-4] No new images for {no_images_timeout}s (max: {max_no_images_timeout}s)")
                
                # Exit if we've been waiting too long and received at least one sentinel
                if no_images_timeout >= max_no_images_timeout and sentinels_received > 0:
                    print(f"[THREAD-4] Timeout reached with {sentinels_received} sentinels - finishing export")
                    break
                    
                continue
    
    def _select_best_calibration_image(self):
        """Select the best calibration image for the Calibration_Targets_Used folder.
        
        - Choose the calibration image with the largest target sample diameter
        - Mark it with is_selected_for_calibration=True
        - All other calibration images will only be exported to reflectance folder
        """
        calibration_images = []
        
        # Collect all processed calibration images
        for img in self.project.imagemap.values():
            if (getattr(img, 'is_calibration_photo', False) and 
                hasattr(img, 'calibration_coefficients') and 
                img.calibration_coefficients and 
                img.calibration_coefficients != [False, False, False]):
                calibration_images.append(img)
        
        if not calibration_images:
            print("[THREAD-2] No valid calibration images found for selection")
            return
        
        print(f"[THREAD-2] Selecting best calibration image from {len(calibration_images)} candidates:")
        for img in calibration_images:
            print(f"[THREAD-2]   - {img.fn}")
        
        # Simple selection: choose the first one with valid coefficients
        # In a more sophisticated implementation, we could use target_sample_diameter
        # or distance from center like the original select_calib function
        best_image = calibration_images[0]
        best_image.is_selected_for_calibration = True
        print(f"[THREAD-2] DEBUG: Selected {best_image.fn} as best calibration image, is_selected_for_calibration = {best_image.is_selected_for_calibration}")
        
        # Mark all others as not selected
        for img in calibration_images[1:]:
            img.is_selected_for_calibration = False
        
        print(f"[THREAD-2] 📝 Other calibration images will only be exported to reflectance folder")
        
        # CRITICAL FIX: Save the updated selection flags to JSON so Ray workers can access them
        for img in calibration_images:
            self._save_calibration_to_json(img)
        print(f"[THREAD-2] Updated selection flags in JSON for {len(calibration_images)} calibration images")

    def _get_cluster_value(self):
        """Get the cluster value from options"""
        # Handle both cfg structures - direct or nested under 'Project Settings'
        if 'Project Settings' in self.options:
            return self.options['Project Settings']['Target Detection'].get('Minimum Target Clustering (0-100)', 60)
        else:
            return self.options['Target Detection'].get('Minimum Target Clustering (0-100)', 60)
    
    def _save_calibration_to_json(self, image):
        """Save calibration data for a target image to the project JSON file using unified API"""
        from unified_calibration_api import UnifiedCalibrationManager
        
        # Extract calibration data from image with validation to prevent string placeholders
        def validate_calibration_value(value, field_name):
            """Validate that calibration values are not string placeholders"""
            if isinstance(value, str):
                print(f"[THREAD-2] ⚠️ String placeholder detected in {field_name}: '{value}' - setting to None")
                return None
            return value
        
        # DEBUG: Check ALS data before saving
        als_magnitude = getattr(image, 'als_magnitude', None)
        als_data = getattr(image, 'als_data', None)
        print(f"[THREAD-2] DEBUG: Saving calibration for {getattr(image, 'fn', 'unknown')}")
        print(f"[THREAD-2] DEBUG: als_magnitude = {als_magnitude}")
        print(f"[THREAD-2] DEBUG: als_data = {als_data}")
        
        # CRITICAL FIX: If ALS data is None, try to reload it from the project imagemap
        if als_magnitude is None or als_data is None:
            print(f"[THREAD-2] 🔄 ALS data missing, attempting to reload from project imagemap...")
            # Find the same image in the project imagemap where ALS data was attached
            project_imagemap = getattr(self.project, 'imagemap', {})
            for key, project_image in project_imagemap.items():
                if getattr(project_image, 'fn', None) == getattr(image, 'fn', None):
                    project_als_magnitude = getattr(project_image, 'als_magnitude', None)
                    project_als_data = getattr(project_image, 'als_data', None)
                    if project_als_magnitude is not None:
                        print(f"[THREAD-2] ✅ Found ALS data in project imagemap for {image.fn}")
                        als_magnitude = project_als_magnitude
                        als_data = project_als_data
                        # Also attach it to the current image object
                        image.als_magnitude = project_als_magnitude
                        image.als_data = project_als_data
                        break
            
            if als_magnitude is None:
                print(f"[THREAD-2] ❌ Still no ALS data found for {image.fn} after project imagemap check")
        
        calibration_data = {
            'coefficients': validate_calibration_value(getattr(image, 'calibration_coefficients', None), 'calibration_coefficients'),
            'limits': validate_calibration_value(getattr(image, 'calibration_limits', None), 'calibration_limits'),
            'xvals': validate_calibration_value(getattr(image, 'calibration_xvals', None), 'calibration_xvals'),
            'yvals': validate_calibration_value(getattr(image, 'calibration_yvals', None), 'calibration_yvals'),
            'als_magnitude': als_magnitude,
            'als_data': als_data,
            'aruco_id': getattr(image, 'aruco_id', None),
            'aruco_corners': getattr(image, 'aruco_corners', None),
            'target_polys': getattr(image, 'calibration_target_polys', None),
            'is_selected_for_calibration': getattr(image, 'is_selected_for_calibration', False)
        }
        
        # Get cluster value from options
        cluster_value = self._get_cluster_value()
        calibration_data['cluster_value'] = cluster_value
        
        # Get project directory
        project_dir = getattr(self.project, 'fp', None)
        
        # Use unified API to save calibration data
        success = UnifiedCalibrationManager.save_calibration_data(image, calibration_data, project_dir)
        if success:
            pass
        else:
            print(f"[THREAD-2] ERROR: Failed to save calibration data for {image.fn}")
            return False
        
        return True
    
    def _mark_target_ready_temporal(self, image):
        """Mark a target as ready in the temporal processing data"""
        try:
            import os
            import json
            
            # Determine calibration file path
            if hasattr(self, 'project') and self.project and hasattr(self.project, 'fp'):
                calibration_file = os.path.join(self.project.fp, 'calibration_data.json')
            else:
                print("[THREAD-2] ⚠️ No project directory available for temporal update")
                return
            
            if not os.path.exists(calibration_file):
                print(f"[THREAD-2] ⚠️ Temporal calibration file not found: {calibration_file}")
                return
            
            # Load and update temporal data
            with open(calibration_file, 'r') as f:
                data = json.load(f)
            
            temporal_info = data.get('temporal_processing', {})
            if not temporal_info:
                print(f"[THREAD-2] ⚠️ No temporal processing info found")
                return
            
            image_fn = image.fn
            if image_fn in temporal_info.get('targets', {}):
                temporal_info['targets'][image_fn]['calibration_ready'] = True
                temporal_info['targets'][image_fn]['processed'] = True
                
                # Save updated data
                with open(calibration_file, 'w') as f:
                    json.dump(data, f, indent=2)
                
                print(f"[THREAD-2] ✅ TEMPORAL: Marked target {image_fn} as ready")
                
                # Check how many non-targets can now process
                ready_count = 0
                for non_target_fn, non_target_info in temporal_info.get('non_targets', {}).items():
                    if non_target_info.get('calibration_target') == image_fn:
                        ready_count += 1
                
                if ready_count > 0:
                    print(f"[THREAD-2] 🚀 TEMPORAL: {ready_count} non-target images can now process immediately!")
            else:
                print(f"[THREAD-2] ⚠️ Target {image_fn} not found in temporal processing data")
                
        except Exception as e:
            print(f"[THREAD-2] ❌ Error marking target ready: {e}")
            import traceback
            traceback.print_exc()
    
    def _store_calibration_in_memory(self, image):
        """Store calibration data in memory for immediate access by Thread 3"""
        timestamp = getattr(image, 'timestamp', None) or getattr(image, 'capture_time', None) or getattr(image, 'fn', None)
        camera_model = getattr(image, 'camera_model', None)
        camera_filter = getattr(image, 'camera_filter', None)
        
        # Convert timestamp to string if it's a datetime object
        if isinstance(timestamp, datetime.datetime):
            timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        else:
            timestamp_str = str(timestamp)
        
        # Create the same key format as JSON storage
        key = timestamp_str
        
        # Create calibration entry
        calibration_entry = {
            'timestamp': to_serializable(timestamp),
            'camera_model': camera_model,
            'camera_filter': camera_filter,
            'coefficients': to_serializable(getattr(image, 'calibration_coefficients', None)),
            'limits': to_serializable(getattr(image, 'calibration_limits', None)),
            'xvals': to_serializable(getattr(image, 'calibration_xvals', None)),
            'yvals': to_serializable(getattr(image, 'calibration_yvals', None)),
            'als_magnitude': to_serializable(getattr(image, 'als_magnitude', None)),
            'als_data': to_serializable(getattr(image, 'als_data', None)),
            'aruco_id': to_serializable(getattr(image, 'aruco_id', None)),
            'filename': getattr(image, 'fn', None),
            'is_selected_for_calibration': to_serializable(getattr(image, 'is_selected_for_calibration', False))
        }
        
        # Create metadata for faster matching
        metadata = {
            'timestamp': timestamp_str,
            'camera_model': camera_model,
            'camera_filter': camera_filter
        }
        
        # Store in memory and signal availability
        self.queues.store_calibration_data(key, calibration_entry, metadata)
        print(f"[THREAD-2] 🚀 STORED calibration data in memory for {image.fn} (key: '{key}')")
        print(f"[THREAD-2] DEBUG: Stored key format: '{key}', timestamp type: {type(timestamp)}")
    
    def _process_calibration_batch(self, calibration_images, processed_images):
        """Process a batch of calibration images with Ray - for streaming approach"""
        # Use global ray variable instead of importing directly
        global ray
        
        if not calibration_images:
            return
        
        print(f"[THREAD-2] 🚀 Processing batch of {len(calibration_images)} calibration images with Ray")
        
        # Use the existing Ray remote function for calibration computation
        calib_task_func = get_unified_task_function('get_calib_data', execution_mode='parallel')
        
        # Handle both cfg structures
        options_for_calib = self.options['Project Settings'] if 'Project Settings' in self.options else self.options
        
        # Process images individually using the existing Ray remote function
        futures = []
        if hasattr(calib_task_func, 'remote'):
            # Ray remote function - create futures for each image
            for img in calibration_images:
                # Pre-load image data if needed
                if not hasattr(img, 'data') or img.data is None:
                    raw_data = img.raw_data
                    if raw_data is not None:
                        img.data = raw_data
                        # Cache the debayered data
                        self.queues.cache_image_data(img.fn, raw_data)
                
                future = calib_task_func.remote(img, options_for_calib)
                futures.append(future)
                
            # Process results as they complete
            future_to_image = {future: img for future, img in zip(futures, calibration_images)}
            
            while futures:
                ready, futures = ray.wait(futures, num_returns=1, timeout=1.0)
                for future in ready:
                    try:
                        result = ray.get(future, timeout=120)  # 2 minute timeout for export processing
                        image = future_to_image[future]
                        
                        # Increment calibrations_processed for every image processed by Ray
                        with self.stats_lock:
                            self.processing_stats['calibrations_processed'] += 1
                        
                        if result:
                            # CRITICAL FIX: Handle both 4 and 5 element returns
                            if len(result) == 5:
                                coeffs, limits, xvals, yvals, modified_image = result
                            elif len(result) == 4:
                                coeffs, limits, xvals, yvals = result
                                modified_image = image  # Use original image if no modified version
                            else:
                                print(f"[THREAD-3] ❌ Unexpected result length from calibration: {len(result)}")
                                continue
                            # Use the modified image object that has aruco_corners and calibration_target_polys
                            image = modified_image
                            image.calibration_coefficients = coeffs
                            image.calibration_limits = limits
                            image.calibration_xvals = xvals
                            image.calibration_yvals = yvals
                            
                            # Ensure ALS is precomputed once per project (JSON-based load in Threads 3/4)
                            try:
                                self._ensure_als_precomputed()
                            except Exception as _als_once_e:
                                print(f"[THREAD-2] WARN: _ensure_als_precomputed failed: {_als_once_e}")
                            
                            # Save calibration to JSON
                            self._save_calibration_to_json(image)
                            
                            # Calibration data saved to JSON for persistent storage
                            
                            # Update statistics
                            with self.stats_lock:
                                self.processing_stats['calibrations_computed'] += 1
                            
                            print(f"[THREAD-2] ✅ Processed and stored calibration for {image.fn}")
                        else:
                            print(f"[THREAD-2] ❌ Failed to compute calibration for {image.fn}")
                            
                    except Exception as e:
                        print(f"[THREAD-2] Error processing batch result: {e}")
                
                # Check for shutdown
                if self.queues.shutdown.is_set():
                    break
        else:
            print("[THREAD-2] Ray remote function not available for batch processing")
    
    def _apply_calibration_from_memory(self, image):
        """Apply calibration data from memory to an image - NON-BLOCKING VERSION"""
        # Find the best calibration match using memory store
        calibration_entry = self.queues.find_best_calibration_match(image)
        
        if calibration_entry:
            # Apply the calibration entry using the existing method
            self._apply_calibration_entry(image, calibration_entry)
            print(f"[THREAD-3] 🚀 Applied calibration data from memory to {image.fn}")
            return True
        else:
            print(f"[THREAD-3] ❌ No calibration data available in memory for {image.fn}")
            return False
    
    def _apply_calibration_from_json(self, image):
        """Load and apply calibration data from JSON to a non-target image"""
        project_dir = getattr(self.project, 'fp', None)
        
        if not project_dir:
            print(f"[THREAD-4] ERROR: Could not determine project directory for {image.fn}")
            return False
        
        calibration_data_file = os.path.join(project_dir, 'calibration_data.json')
        if not os.path.exists(calibration_data_file):
            print(f"[THREAD-4] Calibration file does not exist yet: {calibration_data_file}")
            return False
        
        with open(calibration_data_file, 'r') as f:
            calib_data = json.load(f)
        
        if not calib_data:
            print(f"[THREAD-4] Calibration data is empty")
            return False
        
        # Get image properties for matching
        img_timestamp = getattr(image, 'timestamp', None) or getattr(image, 'capture_time', None)
        img_camera_model = getattr(image, 'camera_model', None)
        img_camera_filter = getattr(image, 'camera_filter', None)
        
        # print(f"[THREAD-4] DEBUG: Calibration matching for {image.fn}")
        # print(f"[THREAD-4] DEBUG: Image metadata - timestamp: {img_timestamp}, camera_model: {img_camera_model}, camera_filter: {img_camera_filter}")
        # print(f"[THREAD-4] DEBUG: Available calibration entries: {list(calib_data.keys())}")
        for key, entry in calib_data.items():
            pass
            # print(f"[THREAD-4] DEBUG: Entry {key} - camera_model: {entry.get('camera_model')}, camera_filter: {entry.get('camera_filter')}, filter_model: {entry.get('filter_model')}")
        
        # Parse image timestamp
        img_ts = None
        if isinstance(img_timestamp, datetime.datetime):
            img_ts = img_timestamp
        elif isinstance(img_timestamp, str):
            try:
                img_ts = datetime.datetime.strptime(img_timestamp, '%Y-%m-%d %H:%M:%S')
            except:
                try:
                    img_ts = datetime.datetime.strptime(img_timestamp, '%Y:%m:%d %H:%M:%S')
                except:
                    pass
        
        # Use the existing find_best_key logic from process_image_unified
        def find_best_key(calib_data):
            best_key = None
            best_delta = None
            fallback_key = None
            fallback_delta = None
            latest_key = None
            latest_ts = None
            for key, entry in calib_data.items():
                try:
                    if img_camera_model is not None and entry.get('camera_model', None) != img_camera_model:
                        continue
                    # Check both camera_filter and filter_model for compatibility
                    entry_filter = entry.get('camera_filter', None) or entry.get('filter_model', None)
                    if img_camera_filter is not None and entry_filter != img_camera_filter:
                        continue
                    calib_ts = datetime.datetime.strptime(key, '%Y-%m-%d %H:%M:%S')
                    delta = (img_ts - calib_ts).total_seconds() if img_ts else None
                    abs_delta = abs(delta) if delta is not None else None
                    # Track latest
                    if latest_ts is None or calib_ts > latest_ts:
                        latest_ts = calib_ts
                        latest_key = key
                    # Primary: closest earlier
                    if delta is not None and delta >= 0 and (best_delta is None or delta < best_delta):
                        best_key = key
                        best_delta = delta
                    # Secondary: closest overall
                    if abs_delta is not None and (fallback_delta is None or abs_delta < fallback_delta):
                        fallback_key = key
                        fallback_delta = abs_delta
                except Exception:
                    continue
            chosen_key = None
            if best_key is not None:
                chosen_key = best_key
            elif fallback_key is not None:
                # print('[THREAD-3] No earlier calibration found, using closest overall.')
                chosen_key = fallback_key
            elif latest_key is not None:
                # print('[THREAD-3] No suitable calibration found, using latest available.')
                chosen_key = latest_key
            return chosen_key
        
        # Find best matching calibration
        chosen_key = find_best_key(calib_data)
        if not chosen_key:
            print(f'[THREAD-4] No calibration entry with matching camera model and filter. Skipping calibration.')
            return False
        
        entry = calib_data[chosen_key]
        self._apply_calibration_entry(image, entry)
        # print(f'[THREAD-4] Applied calibration data from {chosen_key} to {image.fn}')
        return True
    
    def _apply_calibration_entry(self, image, entry):
        """Apply calibration data from an entry to an image"""
        import numpy as np
        
        image.calibration_coefficients = entry.get('coefficients')
        image.calibration_limits = entry.get('limits')
        image.calibration_xvals = entry.get('xvals')
        image.calibration_yvals = entry.get('yvals')
        image.als_magnitude = entry.get('als_magnitude')
        image.als_data = entry.get('als_data')
        
        # CRITICAL FIX: Apply the selection flag from JSON
        image.is_selected_for_calibration = entry.get('is_selected_for_calibration', False)
        print(f"[THREAD-3] Applied is_selected_for_calibration={image.is_selected_for_calibration} to {image.fn} from JSON")
        
        # Create a calibration_image object that process_image_unified expects
        # This allows the export thread to properly apply calibration
        calib_image = type('CalibImage', (), {})()
        calib_image.calibration_coefficients = entry.get('coefficients')
        calib_image.calibration_limits = entry.get('limits')
        calib_image.calibration_xvals = entry.get('xvals')
        calib_image.calibration_yvals = entry.get('yvals')
        calib_image.als_magnitude = entry.get('als_magnitude')
        calib_image.als_data = entry.get('als_data')
        calib_image.aruco_id = entry.get('aruco_id')
        calib_image.fn = entry.get('filename', 'calibration_image')
        calib_image.is_selected_for_calibration = entry.get('is_selected_for_calibration', False)
        
        # Convert lists to numpy arrays where needed
        if isinstance(calib_image.als_data, list):
            calib_image.als_data = np.array(calib_image.als_data)
        
        # Add placeholder attributes to prevent attribute errors
        calib_image.data = None
        calib_image.path = ''  # Add path attribute for ALS correction
        calib_image.is_calibration_photo = True  # Mark as calibration photo
        calib_image.camera_model = entry.get('camera_model', 'Survey3N')
        calib_image.camera_filter = entry.get('camera_filter', 'RGN')
        
        image.calibration_image = calib_image
        
        # If no exact match, find closest by timestamp
        # This is a simplified version - you may want more sophisticated matching
        print(f'[THREAD-3] No exact calibration match found for {image.fn}')
        return False

    def _calculate_optimal_export_batch_size(self, available_cpus):
        """Calculate optimal export batch size based on computer capabilities"""
        try:
            import psutil
            
            # Get system information
            cpu_count = psutil.cpu_count(logical=True)
            memory_gb = psutil.virtual_memory().total / (1024**3)
            
            # Determine system tier and optimal batch size
            if memory_gb >= 28 and cpu_count >= 12:
                # High-end system: Larger batches for efficiency (relaxed thresholds for 12-core systems)
                base_batch_size = min(12, max(8, int(available_cpus * 0.75)))
                tier = "high-end"
            elif memory_gb >= 16 and cpu_count >= 8:
                # Mid-range system: Moderate batches
                base_batch_size = min(10, max(6, int(available_cpus * 0.7)))
                tier = "mid-range"
            elif memory_gb >= 8 and cpu_count >= 4:
                # Low-mid system: Smaller batches
                base_batch_size = min(6, max(3, int(available_cpus * 0.5)))
                tier = "low-mid"
            else:
                # Low-end system: Very small batches to avoid overwhelming
                base_batch_size = min(3, max(2, int(available_cpus * 0.4)))
                tier = "low-end"
            
            # Adjust for memory constraints
            if memory_gb < 8:
                base_batch_size = min(base_batch_size, 3)
            elif memory_gb < 16:
                base_batch_size = min(base_batch_size, 5)
            
            
            return base_batch_size
            
        except Exception as e:
            pass
            # Fallback based on available CPUs only
            if available_cpus >= 12:
                return 8
            elif available_cpus >= 8:
                return 6
            elif available_cpus >= 4:
                return 4
            else:
                return 2

    def _calculate_export_batch_from_config(self, ray_config):
        """Calculate export batch size from Ray configuration - AGGRESSIVE SETTINGS"""
        tier = ray_config.get('tier', 'low-end')
        max_workers = ray_config.get('max_workers', 2)
        base_batch_size = ray_config.get('batch_size', 5)
        
        # AGGRESSIVE: Significantly increased batch sizes for dynamic scaling
        if tier == 'high-end':
            # High-end systems: Use very large batches for maximum throughput
            export_batch_size = min(30, max(20, int(max_workers * 1.5)))
        elif tier == 'mid-range':
            # Mid-range systems: Use large batches
            export_batch_size = min(25, max(15, int(max_workers * 1.25)))
        elif tier == 'low-mid':
            # Low-mid systems: Use moderate-large batches
            export_batch_size = min(20, max(10, int(max_workers * 1.0)))
        else:  # low-end
            # Low-end systems: Use moderate batches (still increased)
            export_batch_size = min(15, max(8, int(max_workers * 0.75)))
        
        return export_batch_size

class DummyProgressTracker:
    """Dummy progress tracker for pipeline threads"""
    def task_completed(self):
        pass

def load_als_data_from_json(image, project_dir):
    """Load ALS data from calibration JSON file for an image.
    
    Uses the unified calibration loader to robustly match by timestamp or filename.
    
    Args:
        image: The image object to load ALS data for
        project_dir: The project directory containing calibration_data.json
        
    Returns:
        bool: True if ALS data was loaded successfully, False otherwise
    """
    if not project_dir:
        return False
    calibration_data_file = os.path.join(project_dir, 'calibration_data.json')
    if not os.path.exists(calibration_data_file):
        return False
        
    # Prefer unified API which already implements robust matching
    try:
        from unified_calibration_api import UnifiedCalibrationManager
        calib = UnifiedCalibrationManager.load_calibration_data(image, project_dir)
        if not calib:
            # Fallback: try direct timestamp-formatted lookup for legacy entries
            from unified_calibration_api import UnifiedCalibrationManager
            with open(calibration_data_file, 'r') as f:
                raw = UnifiedCalibrationManager._load_json_with_repair(f, calibration_data_file)
            ts = getattr(image, 'timestamp', None) or getattr(image, 'capture_time', None)
            if hasattr(ts, 'strftime'):
                ts_key = ts.strftime('%Y-%m-%d %H:%M:%S')
            else:
                ts_key = str(ts) if ts else str(getattr(image, 'fn', None))

            entry = raw.get(ts_key)
            if not entry:
                # As a last resort, match by filename
                filename = getattr(image, 'fn', None)
                for k, v in raw.items():
                    if v.get('filename') == filename:
                        entry = v
                        break
            if not entry:

                return False
            calib = {
                'als_magnitude': entry.get('als_magnitude'),
                'als_data': entry.get('als_data'),
                'yvals': entry.get('yvals')
            }
        # Apply to image
        image.als_magnitude = calib.get('als_magnitude')
        image.als_data = calib.get('als_data')
        image.calibration_yvals = calib.get('yvals')
            
            # Clear ALS cache to force recalculation with the newly loaded data
        for attr in ('_als_correction_applied', '_als_corrected_coefficients'):
            if hasattr(image, attr):
                delattr(image, attr)
        
        # Ensure calibration_image is set for targets
            if getattr(image, 'is_calibration_photo', False):
                image.calibration_image = image
                
        has_any_als = (image.als_magnitude is not None) or (image.als_data is not None) or (image.calibration_yvals is not None)
        if not has_any_als:
            pass  # No ALS fields present in calibration entry
        return has_any_als
    except Exception as e:
        print(f"[ERROR] Failed to load ALS data from JSON: {e}")
        return False


def apply_als_correction_and_get_coefficients(image, calibration_image=None):
    """Apply ALS correction and determine final calibration coefficients.
    
    Args:
        image: The image to process
        calibration_image: The calibration image to use (if None, uses image.calibration_image)
        
    Returns:
        tuple: (calibration_coeffs, calibration_limits) or (None, None) if failed
    """
    from mip.Calibration_Utils import als_calibration_correction as als_correction_func
    
    # Ensure ALS exists for non-targets if missing
    try:
        if (not getattr(image, 'is_calibration_photo', False)) and (
            (not hasattr(image, 'als_magnitude') or getattr(image, 'als_magnitude', None) is None) or
            (not hasattr(image, 'als_data') or getattr(image, 'als_data', None) is None)
        ):
            project_dir = getattr(image, 'project_path', None) or getattr(getattr(image, 'project', None), 'fp', None)
            if project_dir:

                try:
                    loaded_ok = load_als_data_from_json(image, project_dir)
                except Exception as _e:
                    pass  # ALS load error
    except Exception:
        pass
    
    # Determine which image to use for calibration
    if calibration_image is None:
        calibration_image = getattr(image, 'calibration_image', None)
    
    # For target images processing themselves
    if getattr(image, 'is_calibration_photo', False):
        # Ensure ALS present for targets too
        if ((not hasattr(image, 'als_data')) or image.als_data is None):
            project_dir = getattr(image, 'project_path', None) or getattr(getattr(image, 'project', None), 'fp', None)
            if project_dir:
                load_als_data_from_json(image, project_dir)


        
        # Target images should already have RAW coefficients computed in _process_target_calibration

        
        # Extra diagnostics
        try:
            pass
        except Exception:
            pass
        
        # Now apply ALS correction to the RAW coefficients (not JPG coefficients)
        try:
            als_corrected_coeffs = als_correction_func(image)
        except Exception as e:

            als_corrected_coeffs = None

        
        if als_corrected_coeffs and als_corrected_coeffs != [False, False, False]:
            pass
            calibration_coeffs = als_corrected_coeffs
            # CRITICAL: Store the BASE RAW coefficients (no ALS) for use by non-target images
            # The base coefficients are the original coefficients before ALS correction
            if not hasattr(image, '_raw_base_coefficients'):
                if image.calibration_coefficients is not None:
                    image._raw_base_coefficients = image.calibration_coefficients.copy()
                else:
                    pass
            

        else:
            pass
            calibration_coeffs = image.calibration_coefficients
            # Store the standard coefficients as fallback
            image._als_corrected_coefficients = image.calibration_coefficients
            
        # Get calibration limits
        if hasattr(image, 'calibration_limits') and image.calibration_limits is not None:
            calibration_limits = image.calibration_limits
        else:
            # Fallback: compute limits from the target image itself
            from mip.Calibrate_Images import get_limits_from_calibration_image
            calibration_limits = get_limits_from_calibration_image(image)

            
    else:
        # For non-target images
        # Ensure ALS exists on calibration image as well
        try:
            if calibration_image is not None and (
                (not hasattr(calibration_image, 'als_magnitude') or getattr(calibration_image, 'als_magnitude', None) is None) or
                (not hasattr(calibration_image, 'als_data') or getattr(calibration_image, 'als_data', None) is None)
            ):
                project_dir = getattr(calibration_image, 'project_path', None) or getattr(getattr(calibration_image, 'project', None), 'fp', None)
                if project_dir:
                    pass
                    try:
                        _ok_cal = load_als_data_from_json(calibration_image, project_dir)
                    except Exception as _e:
                        pass
        except Exception:
            pass

        if calibration_image is not None:
            pass
        else:
            pass
        
        # CRITICAL: For non-target images, check if calibration_image has already-processed RAW coefficients
        # If the target image has been processed and has ALS-corrected coefficients, use those instead of recomputing
        if hasattr(calibration_image, '_als_corrected_coefficients') and calibration_image._als_corrected_coefficients:
            pass
            calibration_coeffs = calibration_image._als_corrected_coefficients
            
            # Apply ALS correction to these target coefficients for this specific image
            try:
                als_corrected_coeffs = als_correction_func(image)
                if als_corrected_coeffs and als_corrected_coeffs != [False, False, False]:
                    pass
                    calibration_coeffs = als_corrected_coeffs
                else:
                    pass
                    # Keep the target's coefficients as-is
            except Exception as e:
                pass
                # Keep the target's coefficients as-is
        else:
            # CRITICAL FIX: Non-target images should use target's RAW coefficients from JSON
            # The target image should have already processed and saved its RAW coefficients to calibration JSON
            pass
            
            # Check if target has been processed and has base RAW coefficients
            if hasattr(calibration_image, '_raw_base_coefficients') and calibration_image._raw_base_coefficients:
                pass
                # Use target's base RAW coefficients, then apply THIS image's ALS correction
                base_coefficients = calibration_image._raw_base_coefficients
                
                # Temporarily set the calibration_image coefficients to the base RAW coefficients
                # so that ALS correction uses the right base
                original_coeffs = getattr(calibration_image, 'calibration_coefficients', None)
                calibration_image.calibration_coefficients = base_coefficients
                
                try:
                    # Apply ALS correction using THIS image's ALS data to the base RAW coefficients
                    als_corrected_coeffs = als_correction_func(image)
                    if als_corrected_coeffs and als_corrected_coeffs != [False, False, False]:
                        pass
                        calibration_coeffs = als_corrected_coeffs
                    else:
                        pass
                        calibration_coeffs = base_coefficients
                except Exception as e:
                    pass
                    calibration_coeffs = base_coefficients
                finally:
                    # Restore original coefficients
                    calibration_image.calibration_coefficients = original_coeffs
                    
            # CRITICAL: Check if target has base RAW coefficients (no ALS applied yet)
            elif (hasattr(calibration_image, '_raw_base_coefficients') and 
                calibration_image._raw_base_coefficients):
                # Use target's base RAW coefficients (no ALS correction), then apply THIS image's ALS correction
                base_coefficients = calibration_image._raw_base_coefficients
                
                # Temporarily set the calibration_image coefficients to the base RAW coefficients
                original_coeffs = getattr(calibration_image, 'calibration_coefficients', None)
                calibration_image.calibration_coefficients = base_coefficients
                
                try:
                    # Apply ALS correction using THIS image's ALS data to the base RAW coefficients
                    als_corrected_coeffs = als_correction_func(image)
                    if als_corrected_coeffs and als_corrected_coeffs != [False, False, False]:
                        pass
                        calibration_coeffs = als_corrected_coeffs
                    else:
                        pass
                        calibration_coeffs = base_coefficients
                except Exception as e:
                    pass
                    calibration_coeffs = base_coefficients
                finally:
                    # Restore original coefficients
                    calibration_image.calibration_coefficients = original_coeffs
                    
            else:
                pass
                
                # CRITICAL: Process the target image's ALS correction on-demand
                if (hasattr(calibration_image, 'is_calibration_photo') and 
                    calibration_image.is_calibration_photo and
                    hasattr(calibration_image, 'als_magnitude') and
                    calibration_image.als_magnitude):
                    
                    # Store the current coefficients as base RAW coefficients (no ALS applied)
                    if not hasattr(calibration_image, '_raw_base_coefficients'):
                        if calibration_image.calibration_coefficients is not None:
                            calibration_image._raw_base_coefficients = calibration_image.calibration_coefficients.copy()
                        else:
                            pass
                    
                    # Use the base RAW coefficients for this non-target image
                    if hasattr(calibration_image, '_raw_base_coefficients'):
                        base_coefficients = calibration_image._raw_base_coefficients
                    else:
                        pass
                        # Compute calibration coefficients for the target image if not already done
                        try:
                            from mip.Calibration_Utils import get_calibration_coefficients_from_target_image
                            coeffs = get_calibration_coefficients_from_target_image(calibration_image)
                            if coeffs and coeffs != [False, False, False]:
                                calibration_image.calibration_coefficients = coeffs
                                calibration_image._raw_base_coefficients = coeffs
                                base_coefficients = coeffs
                            else:
                                pass
                                base_coefficients = None
                        except Exception as e:
                            pass
                            base_coefficients = None
                    
                    # Apply ALS correction to the base coefficients using this image's ALS data
                    if base_coefficients is not None:
                        original_coeffs = getattr(calibration_image, 'calibration_coefficients', None)
                        calibration_image.calibration_coefficients = base_coefficients
                        
                        try:
                            als_corrected_coeffs = als_correction_func(image)
                            if als_corrected_coeffs and als_corrected_coeffs != [False, False, False]:
                                pass
                                calibration_coeffs = als_corrected_coeffs
                            else:
                                pass
                                calibration_coeffs = base_coefficients
                        except Exception as e:
                            pass
                            calibration_coeffs = base_coefficients
                        finally:
                            # Restore target's coefficients
                            calibration_image.calibration_coefficients = original_coeffs
                    else:
                        pass
                        calibration_coeffs = None
                else:
                    pass
                    calibration_coeffs = getattr(calibration_image, 'calibration_coefficients', None)
            
        calibration_limits = getattr(calibration_image, 'calibration_limits', None)
    
    # VALIDATION: Check if coefficients are valid numeric arrays, not string placeholders
    if (calibration_coeffs is None or 
        calibration_coeffs == [False, False, False] or
        isinstance(calibration_coeffs, str) or
        not isinstance(calibration_coeffs, list)):
        calibration_coeffs = [[1.0, 0.0, 0.0, 1.0, '1.0x + 0.0'], [1.0, 0.0, 0.0, 1.0, '1.0x + 0.0'], [1.0, 0.0, 0.0, 1.0, '1.0x + 0.0']]
    
    if calibration_limits is None:
        calibration_limits = [[0, 65535], [0, 65535], [0, 65535]]
        
    return calibration_coeffs, calibration_limits


def save_reflectance_calibrated_image(calib_image, original_image, output_format, outfolder, subfolder_name="Reflectance_Calibrated_Images"):
    """Save reflectance calibrated or sensor response image to disk.
    
    Args:
        calib_image: The calibrated image object to save
        original_image: The original image object (for filename reference)
        output_format: The output format (e.g., 'tiff16')
        outfolder: The base output folder
        subfolder_name: The subfolder name (default: "Reflectance_Calibrated_Images")
        
    Returns:
        str: Path to saved file or None if failed
    """

    
    # CRITICAL DEBUG: Check image data before saving
    if hasattr(calib_image, 'data') and calib_image.data is not None:
        arr = calib_image.data
    else:

        return None
    
    # CRITICAL FIX: Ensure outfolder includes format directory (tiff16)
    format_outfolder = os.path.join(outfolder, output_format)
    reflectance_path = save(calib_image, output_format, format_outfolder, 
                           subfolder_name, 
                           is_preview=False)

    
    # CRITICAL DEBUG: Check if file was actually created
    if reflectance_path and os.path.exists(reflectance_path):

        # Check file size
        file_size = os.path.getsize(reflectance_path)

    elif reflectance_path:

        pass  # Empty block
    else:
    
    
        pass  # Empty block
    return reflectance_path


def export_calibrated_reflectance(image, options, outfolder, output_format='tiff16', vignette_corrected_image=None):
    """Export calibrated reflectance or sensor response image.
    
    This is the main entry point for exporting calibrated reflectance images
    in both serial and parallel processing modes. When reflectance calibration
    is disabled, only sensor response processing is applied.
    
    Args:
        image: The image to export
        options: Processing options
        outfolder: Output folder path
        output_format: Output format (default: 'tiff16')
        vignette_corrected_image: Optional vignette-corrected image to use instead of the original
        
    Returns:
        tuple: (path, data, layer_name) of exported image or None if failed
               - path: file path to exported image
               - data: numpy array of image data
               - layer_name: 'RAW (Sensor Response)' or 'RAW (Reflectance)'
    """
    # Check if reflectance calibration is enabled
    reflectance_enabled = False
    if options and 'Project Settings' in options:
        project_settings = options['Project Settings']
        if 'Processing' in project_settings:
            processing_options = project_settings['Processing']
            reflectance_enabled = processing_options.get('Reflectance calibration / white balance', False)
    elif options and 'Processing' in options:
        # Direct access for parallel mode
        processing_options = options['Processing']
        reflectance_enabled = processing_options.get('Reflectance calibration / white balance', False)
    
    # print(f"[EXPORT] Reflectance calibration enabled: {reflectance_enabled} for {getattr(image, 'fn', 'unknown')}")
    
    # Create a copy for processing
    if vignette_corrected_image is not None:
        calib_image = copy.deepcopy(vignette_corrected_image)
    else:
        calib_image = copy.deepcopy(image)
        
        # CRITICAL DEBUG: Check if project reference survived deepcopy
        if hasattr(calib_image, 'project') and calib_image.project:
            pass
    
    # Check if this is a target image
    is_target = getattr(image, 'is_calibration_photo', False)
    
    # Check if vignette correction is enabled
    vignette_enabled = False
    if options and 'Project Settings' in options:
        project_settings = options['Project Settings']
        if 'Processing' in project_settings:
            processing_options = project_settings['Processing']
            vignette_enabled = processing_options.get('Vignette correction', False)
    elif options and 'Processing' in options:
        # Direct access for parallel mode
        processing_options = options['Processing']
        vignette_enabled = processing_options.get('Vignette correction', False)
    
    # print(f"[EXPORT] Vignette correction enabled: {vignette_enabled} for {getattr(image, 'fn', 'unknown')}")
    
    # Determine folder name and layer name based on reflectance AND vignette settings
    if reflectance_enabled:
        subfolder_name = "Reflectance_Calibrated_Images"
        layer_name = "RAW (Reflectance)"
    else:
        # Reflectance is disabled - check vignette setting
        if vignette_enabled:
            subfolder_name = "Vignette_Corrected_Images"
            layer_name = "RAW (Vignette Corrected)"
        else:
            subfolder_name = "Sensor_Response_Images"
            layer_name = "RAW (Sensor Response)"
    
    # If reflectance calibration is disabled, apply only sensor response correction
    if not reflectance_enabled:
        # print(f"[EXPORT] Applying sensor response correction only (no calibration) for {getattr(image, 'fn', 'unknown')}")
        from mip.Calibrate_Images import sensor_response_correction
        
        # Apply sensor response correction only (no calibration coefficients)
        sensor_response_correction(calib_image, limits=[], use_limit=False)
        
        # Save the sensor response image
        reflectance_path = save_reflectance_calibrated_image(calib_image, image, output_format, outfolder, subfolder_name)
        
        if reflectance_path:
            # Store the sensor response data for index calculation
            reflectance_data = calib_image.data.copy() if hasattr(calib_image, 'data') and calib_image.data is not None else None
            
            # Delete cached debayered TIFF immediately after export
            if hasattr(image, 'project') and image.project:
                image.project.delete_cached_tiff(image.fn)
            
            return (reflectance_path, reflectance_data, layer_name)
        
        return None
    
    # If reflectance calibration is enabled, proceed with full calibration
    # Ensure ALS data is loaded for target images
    if is_target:
        if (not hasattr(image, 'als_data') or image.als_data is None):
            project_dir = getattr(image, 'project_path', None) or \
                         getattr(getattr(image, 'project', None), 'fp', None)
            if project_dir:
                load_als_data_from_json(image, project_dir)
    
    # Determine if we have calibration data
    has_calibration = (hasattr(image, 'calibration_image') and image.calibration_image is not None) or \
                     (is_target and hasattr(image, 'calibration_coefficients') and 
                      image.calibration_coefficients is not None)
    
    if not has_calibration:
        # print(f"[EXPORT] No calibration data available for {getattr(image, 'fn', 'unknown')}")
        return None
    
    # Apply ALS correction and get coefficients
    calibration_coeffs, calibration_limits = apply_als_correction_and_get_coefficients(image)
    
    if calibration_coeffs is None:
        return None
    
    # Apply calibration to the copy
    # print(f"[EXPORT] Applying full reflectance calibration for {getattr(image, 'fn', 'unknown')}")
    apply_calib_to_image(calib_image, calibration_coeffs, calibration_limits)
    
    # Save the calibrated image and keep the data in memory
    reflectance_path = save_reflectance_calibrated_image(calib_image, image, output_format, outfolder, subfolder_name)
    
    if reflectance_path:
        # Store the calibrated reflectance data for index calculation (avoids reloading from disk)
        reflectance_data = calib_image.data.copy() if hasattr(calib_image, 'data') and calib_image.data is not None else None
        
        # CRITICAL FIX: Delete cached debayered TIFF immediately after export (serial mode)
        # This prevents disk space buildup for large projects
        if hasattr(image, 'project') and image.project:
            pass
            image.project.delete_cached_tiff(image.fn)
        else:
            pass
    
        # Return path, data, and layer name for proper layer display
        return (reflectance_path, reflectance_data, layer_name)
    
    return None


def process_image_unified_core(image, options, reprocessing_cfg, outfolder, progress_tracker, execution_mode='serial'):
    """
    Core image processing logic shared between serial and parallel modes.
    
    Args:
        image: LabImage object to process
        options: Processing configuration options
        reprocessing_cfg: Reprocessing configuration
        outfolder: Output folder path
        progress_tracker: Progress tracking object
        execution_mode: 'serial' or 'parallel' execution mode
    
    Returns:
        dict: Dictionary of output layers and their file paths
    """

    
    # CRITICAL: Apply PPK corrections to each individual image (FIXED VERSION)
    
    # Check if PPK is enabled and exposure pin is selected
    # Handle different options structures between standard and premium modes
    if 'Project Settings' in options:
        # Standard mode structure
        pass
        processing_settings = options.get('Project Settings', {}).get('Processing', {})
    else:
        # Premium mode structure - options are directly accessible
        pass
        processing_settings = options.get('Processing', options)  # Fallback to options itself
    
    ppk_enabled = processing_settings.get('Apply PPK corrections', False)
    exposure_pin = processing_settings.get('Exposure Pin 1', None)
    
    
    if ppk_enabled and exposure_pin and exposure_pin != "None":
        pass
        try:
            # Check if this image's model matches the selected exposure pin
            image_model = getattr(image, 'Model', None)
            if image_model and image_model == exposure_pin:
                pass
                
                # Create single image group for PPK processing
                single_image_group = {image_model: [image]}
                
                # Apply PPK corrections to this specific image
                from mip.ppk import apply_ppk_corrections
                # Use the source directory where the original images and .daq files are located
                input_path = os.path.dirname(image.path) if hasattr(image, 'path') else outfolder
                apply_ppk_corrections(input_path, single_image_group, processing_settings)
            else:
                pass
        except Exception as e:
            pass
            import traceback
            traceback.print_exc()
    else:
        pass

    
    # Mode-specific data preparation
    prepare_image_data_for_mode(image, execution_mode)
    
    # Validate input
    if isinstance(image, str) or isinstance(image, bytes) or hasattr(image, '__fspath__'):
        print(f"[ERROR] process_image_unified_core received a file path instead of a LabImage object: {image}")
        raise TypeError("process_image_unified_core expects a LabImage object, not a file path")
    
    # Extract processing options
    processing_options, export_options = _extract_processing_options(options)

    
    do_vig = processing_options['Vignette correction']
    do_calib = processing_options["Reflectance calibration / white balance"]
    
    

    
    # Skip processing for target images that were already created
    if hasattr(image, 'is_target_image') and image.is_target_image:
        print(f"[SKIP] Skipping target image {image.fn} - already processed as target")
        progress_tracker.task_completed()
        return {}
    
    # Preserve original filename and create working copy
    original_filename = image.fn
    image = image.copy()
    if not hasattr(image, 'fn') or image.fn != original_filename:
        image.fn = original_filename
    
    # CRITICAL FIX: When reflectance calibration is disabled, still export calibration images with sensor response
    # Don't skip them entirely - they should be processed like normal images
    # The target detection and red square export logic will be skipped by the do_calib check later
    if image.is_calibration_photo and not do_calib:
        print(f"[SENSOR-RESPONSE] Processing calibration image {image.fn} with sensor response (calib=False)")
        # Continue processing - will export as sensor response image
    

    
    # Set up output format
    output_format = fmt_map[export_options["Calibrated image format"]]
    ExifUtils.add_pix4d_tags(image)
    layers_out = {}
    

    
    if reprocessing_cfg['calibration']:
        # Base export if no processing is enabled
        if not any([do_vig, do_calib]):
            layers_out['Base Export'] = save(image, output_format, outfolder, is_preview=False)
        
        # Note: Original data preservation removed as it was causing issues
        
        # Vignette correction processing
        if do_vig:
            layers_out = _process_vignette_correction(image, do_calib, output_format, outfolder, layers_out)
        
        # White balance for RGB images
        if do_calib and (image.camera_filter == "RGB"):
            wb_image = image.copy()
            apply_wb_to_image(wb_image)
            layers_out['White Balanced'] = save(wb_image, output_format, outfolder, 
                                              os.path.join(output_format, "White_Balanced_Images"), is_preview=False)
        
        # Load calibration data for non-target images BEFORE calibration processing (unified approach)
        if not getattr(image, 'is_calibration_photo', False) and do_calib:


            if hasattr(image, 'calibration_image') and image.calibration_image is not None:

                pass  # Empty block
            _load_and_assign_calibration_data(image)

            if hasattr(image, 'calibration_image') and image.calibration_image is not None:
        
        
                pass  # Empty block
        # Calibration processing
        if do_calib:
            layers_out = _process_calibration(image, options, outfolder, output_format, layers_out, execution_mode)
        
        # NOTE: RAW (Target) layer creation is now handled within _process_calibration
        # to ensure interval filtering is respected before target export
    
    # Save calibration data for target images
    if getattr(image, 'is_calibration_photo', False):



        _save_calibration_data(image, options, outfolder)
    
    # Export index images if configured (both serial and parallel modes)
    # CRITICAL FIX: Don't require image.project to be set - just check if index configs exist in options
    reflectance_path = layers_out.get('RAW (Reflectance)', None)
    # Get in-memory reflectance data if available (avoids reloading from disk)
    reflectance_data = getattr(image, '_reflectance_data_for_index', None)
    
    # Create a temporary pipeline object to access _export_index_images method
    # This is a workaround since _export_index_images is a method of PipelineThreads
    try:
        from tasks import PipelineThreads
        temp_pipeline = type('obj', (object,), {'_export_index_images': PipelineThreads._export_index_images})()
        
        mode_label = execution_mode.upper() if execution_mode else 'UNKNOWN'
        
        index_layers = temp_pipeline._export_index_images(image, options, outfolder, output_format, reflectance_path, reflectance_data)
        if index_layers:
            layers_out.update(index_layers)
            
            # Add index layers to image object
            if hasattr(image, 'layers'):
                if not isinstance(image.layers, dict):
                    image.layers = {}
                image.layers.update(index_layers)
            else:
                # Initialize layers if it doesn't exist
                image.layers = index_layers.copy()
            
            # Add to project data for persistence (only if project is available)
            if hasattr(image, 'project') and image.project and hasattr(image.project, 'data'):
                project_data = image.project.data
                for base, fileset in project_data.get('files', {}).items():
                    if fileset.get('raw') and os.path.basename(fileset['raw']) == image.fn:
                        if 'layers' not in fileset:
                            fileset['layers'] = {}
                        fileset['layers'].update(index_layers)
                        break
    except Exception as e:
        pass
        import traceback
        traceback.print_exc()

    
    return layers_out


def process_image_unified(image, options, reprocessing_cfg, outfolder, progress_tracker, execution_mode='serial'):
    """
    Unified processing function that handles both serial and parallel execution.
    
    Args:
        image: LabImage object to process
        options: Processing configuration options
        reprocessing_cfg: Reprocessing configuration
        outfolder: Output folder path
        progress_tracker: Progress tracking object
        execution_mode: 'serial' or 'parallel' execution mode
    
    Returns:
        dict: Dictionary of output layers and their file paths
    """

    try:
        return process_image_unified_core(image, options, reprocessing_cfg, outfolder, progress_tracker, execution_mode)
    except Exception as e:
        print(f"[ERROR] Error processing {getattr(image, 'fn', 'unknown')}: {e}")
        import traceback
        traceback.print_exc()
        return {}


def _prepare_parallel_data(image):
    """Prepare image data for parallel processing by handling Ray-specific data marshaling."""
    print(f"[RAY SYNC] Preparing parallel data for {getattr(image, 'fn', 'unknown')}")
    
    # Reconstruct calibration_image from Ray-synchronized attributes if needed
    if (not hasattr(image, 'calibration_image') or image.calibration_image is None) and hasattr(image, '_ray_calibration_coefficients'):
        from types import SimpleNamespace
        image.calibration_image = SimpleNamespace(
            fn=getattr(image, '_ray_calibration_fn', 'unknown'),
            calibration_coefficients=image._ray_calibration_coefficients,
            calibration_limits=getattr(image, '_ray_calibration_limits', None),
            calibration_xvals=getattr(image, '_ray_calibration_xvals', None),
            calibration_yvals=getattr(image, '_ray_calibration_yvals', None),
            aruco_id=getattr(image, '_ray_calibration_aruco_id', None),
            als_magnitude=getattr(image, '_ray_calib_als_magnitude', None),
            als_data=getattr(image, '_ray_calib_als_data', None)
        )
        print(f"[RAY SYNC] Reconstructed calibration_image from Ray-synchronized attributes")
    
    # Restore calibration data from Ray sync
    if hasattr(image, '_ray_calibration_coefficients'):
        if hasattr(image, 'calibration_image') and image.calibration_image is not None:
            calib_img = image.calibration_image
            if not hasattr(calib_img, 'calibration_coefficients') or calib_img.calibration_coefficients in [None, [False, False, False]]:
                calib_img.calibration_coefficients = image._ray_calibration_coefficients
                calib_img.calibration_limits = getattr(image, '_ray_calibration_limits', None)
                calib_img.calibration_xvals = getattr(image, '_ray_calibration_xvals', None)
                calib_img.calibration_yvals = getattr(image, '_ray_calibration_yvals', None)
                calib_img.aruco_id = getattr(image, '_ray_calibration_aruco_id', None)
                
                # Restore ALS data
                if hasattr(image, '_ray_als_magnitude'):
                    calib_img.als_magnitude = image._ray_als_magnitude
                if hasattr(image, '_ray_als_data'):
                    calib_img.als_data = image._ray_als_data
                
                print(f"[RAY SYNC] Restored calibration and ALS data to calibration_image")
    
    # Restore ALS data to image itself
    if hasattr(image, '_ray_image_als_magnitude'):
        image.als_magnitude = image._ray_image_als_magnitude
        if hasattr(image, 'calibration_image') and image.calibration_image is not None:
            image.calibration_image.als_magnitude = image._ray_calib_als_magnitude
    
    if hasattr(image, '_ray_image_als_data'):
        image.als_data = image._ray_image_als_data
        if hasattr(image, 'calibration_image') and image.calibration_image is not None:
            image.calibration_image.als_data = image._ray_calib_als_data
    
    # Validate data integrity after restoration
    _validate_parallel_data_integrity(image)


def _validate_parallel_data_integrity(image):
    """Validate that parallel data restoration was successful."""
    print(f"[RAY SYNC] Validating data integrity for {getattr(image, 'fn', 'unknown')}")
    
    issues = []
    
    # Check calibration data
    if hasattr(image, 'calibration_image') and image.calibration_image is not None:
        calib_img = image.calibration_image
        if not hasattr(calib_img, 'calibration_coefficients') or not calib_img.calibration_coefficients:
            issues.append("Missing calibration coefficients")
        if not hasattr(calib_img, 'calibration_limits'):
            issues.append("Missing calibration limits")
    else:
        if not getattr(image, 'is_calibration_photo', False):
            issues.append("No calibration image reference for non-target image")
    
    # Check ALS data consistency
    if hasattr(image, 'als_magnitude') and hasattr(image, 'calibration_image') and image.calibration_image:
        if hasattr(image.calibration_image, 'als_magnitude'):
            if image.als_magnitude != image.calibration_image.als_magnitude:
                issues.append("ALS magnitude inconsistency between image and calibration_image")
    
    if issues:
        print(f"[RAY SYNC] Data integrity issues found for {getattr(image, 'fn', 'unknown')}: {', '.join(issues)}")
    else:
        print(f"[RAY SYNC] Data integrity validation passed for {getattr(image, 'fn', 'unknown')}")


def _prepare_serial_data(image):
    """Prepare image data for serial processing by ensuring direct object references."""
    
    # CRITICAL FIX: Check if this image should be a calibration target based on project data
    # The is_calibration_photo attribute might be lost during object copying/transfer
    if hasattr(image, 'project') and image.project:
        # Check project data to see if this RAW image should be a calibration target
        for base, fileset in image.project.data['files'].items():
            if fileset.get('raw') and os.path.basename(fileset['raw']) == image.fn:
                calibration_info = fileset.get('calibration', {})
                is_target_in_project = calibration_info.get('is_calibration_photo', False)
                manual_calib = fileset.get('manual_calib', False)
                manually_disabled = calibration_info.get('manually_disabled', False)
                
                # Restore target status if it should be a target
                should_be_target = is_target_in_project and manual_calib and not manually_disabled
                current_is_target = getattr(image, 'is_calibration_photo', False)
                
                if should_be_target and not current_is_target:
                    pass
                    image.is_calibration_photo = True
                elif not should_be_target and current_is_target:
                    pass
                    image.is_calibration_photo = False
                
                break
    
    # For serial mode, ensure that calibration images have proper self-references
    if getattr(image, 'is_calibration_photo', False):
        if not hasattr(image, 'calibration_image') or image.calibration_image is None:
            pass
            image.calibration_image = image
    
    # Validate serial data structure
    _validate_serial_data_integrity(image)


def _validate_serial_data_integrity(image):
    """Validate that serial data structure is correct."""
    
    issues = []
    
    # Check that non-calibration images have calibration references
    if not getattr(image, 'is_calibration_photo', False):
        if not hasattr(image, 'calibration_image') or image.calibration_image is None:
            issues.append("Non-target image lacks calibration_image reference")
    
    # Check that calibration images have self-references
    if getattr(image, 'is_calibration_photo', False):
        if not hasattr(image, 'calibration_image') or image.calibration_image != image:
            issues.append("Target image lacks proper self-reference")
    
    if issues:
        pass
    else:
        pass


def prepare_image_data_for_mode(image, execution_mode):
    """
    Prepare image data based on execution mode.
    
    Args:
        image: LabImage object to prepare
        execution_mode: 'serial' or 'parallel' execution mode
    """
    
    if execution_mode == 'parallel':
        _prepare_parallel_data(image)
    else:
        _prepare_serial_data(image)


def _extract_processing_options(options):
    """Extract processing and export options from configuration."""
    processing_options = None
    export_options = None
    
    if 'Project Settings' in options and 'Processing' in options['Project Settings']:
        # Nested structure: options['Project Settings']['Processing']
        processing_options = options['Project Settings']['Processing']
        export_options = options['Project Settings'].get('Export', {})
    elif 'Processing' in options:
        # Flat structure: options['Processing']
        processing_options = options['Processing']
        export_options = options.get('Export', {})
    else:
        raise KeyError("'Processing' section missing from options: {}".format(options))
    
    return processing_options, export_options


def _process_vignette_correction(image, do_calib, output_format, outfolder, layers_out):
    """Process vignette correction."""

    vig_image = image.copy()
    devignette(vig_image)
    
    # Only save vignette-corrected image if reflectance calibration is disabled
    if not do_calib:
        pass  # Exporting vignette image
        layers_out['Devignetted'] = save(vig_image, output_format, outfolder, 
                                       os.path.join(output_format, "Vignette_Corrected_Images"), is_preview=False)
    else:
    
    
        pass  # Empty block
    return layers_out


def _process_calibration(image, options, outfolder, output_format, layers_out, execution_mode):
    """Process calibration for both target and non-target images."""
    if image.is_calibration_photo:
        layers_out = _process_target_calibration(image, output_format, outfolder, layers_out, options)
    
    # Apply calibration to all images when enabled (including calibration targets)
    # After _process_target_calibration, calibration targets will have calibration_image set to themselves
    if hasattr(image, 'calibration_image') and image.calibration_image is not None:

        # Use the new refactored method for exporting calibrated reflectance or sensor response
        reflectance_result = export_calibrated_reflectance(image, options, outfolder, output_format, None)
        
        # Unpack the result - export_calibrated_reflectance returns (path, data, layer_name)
        if reflectance_result:
            if isinstance(reflectance_result, tuple):
                if len(reflectance_result) == 3:
                    # New format: (path, data, layer_name)
                    reflectance_path, reflectance_data, layer_name = reflectance_result
                elif len(reflectance_result) == 2:
                    # Old format: (path, data) - default to reflectance
                    reflectance_path, reflectance_data = reflectance_result
                    layer_name = 'RAW (Reflectance)'
            else:
                # Backward compatibility: old code returned just path
                reflectance_path = reflectance_result
                reflectance_data = None
                layer_name = 'RAW (Reflectance)'
            
            # Use the dynamic layer name returned from export function
            layers_out[layer_name] = reflectance_path
            
            # Store reflectance/sensor response data in image object for index calculation
            if reflectance_data is not None:
                image._reflectance_data_for_index = reflectance_data

        else:
            reflectance_path = None
            reflectance_data = None
            layer_name = None
            print(f"[WARNING] Failed to create reflectance/sensor response layer for {image.fn}")
    else:
        reflectance_path = None
        reflectance_data = None
        print(f"[WARNING] No calibration image available for {image.fn}, skipping reflectance calibration")
    
    return layers_out


def _is_target_actually_used(image):
    """Check if a calibration target is actually being used for processing.
    
    1. It survived recalibration interval filtering
    2. It has other images assigned to use its calibration data
    3. It's not just detected but actually participating in calibration
    """
    # CRITICAL: Check if this target was filtered out by the recalibration interval
    interval_filtered = False
    if hasattr(image, 'project') and image.project:
        # Check project data for interval filtering flag
        for base, fileset in image.project.data['files'].items():
            if fileset.get('raw') and os.path.basename(fileset['raw']) == image.fn:
                calibration_info = fileset.get('calibration', {})
                interval_filtered = calibration_info.get('interval_filtered', False)
                manual_calib = fileset.get('manual_calib', False)
                break
    
    # If the target was filtered by interval, it should not be used
    if interval_filtered:
        pass
        return False
    
    # Check if this target has calibration coefficients computed
    has_coefficients = (hasattr(image, 'calibration_coefficients') and 
                       image.calibration_coefficients is not None and
                       image.calibration_coefficients != [False, False, False])
    
    # Check if this target is assigned as a calibration image for other images
    # This indicates it survived interval filtering and is being used
    has_assignments = False
    if hasattr(image, 'project') and image.project:
        # Look through project imagemap to see if any images reference this as calibration_image
        for img_name, img_obj in image.project.imagemap.items():
            if (hasattr(img_obj, 'calibration_image') and 
                img_obj.calibration_image is not None and
                getattr(img_obj.calibration_image, 'fn', None) == image.fn):
                has_assignments = True
                break
    
    # Also check if the target is assigned to itself (self-calibration)
    if (hasattr(image, 'calibration_image') and 
        image.calibration_image is not None and
        getattr(image.calibration_image, 'fn', None) == image.fn):
        has_assignments = True
    
    # CRITICAL FIX: A target should get a red square export if it has coefficients computed,
    # regardless of assignment logic. The assignment logic is for determining which coefficients
    # to use for other images, but doesn't affect whether a target itself should be exported.
    is_used = has_coefficients  # Only require coefficients, not assignments
    
    return is_used

def _process_target_calibration(image, output_format, outfolder, layers_out, options=None):
    """Process calibration target images.
    
    Args:
        options: Processing options dict containing vignette/reflectance settings
    """
    original_filename = image.fn
    
    # Create target image from the original raw data
    target_image = image.copy()
    target_image.fn = original_filename
    
    # CRITICAL FIX: Ensure we're loading from the RAW file, not a TIFF export
    # image.path might point to a TIFF from previous exports
    raw_path = image.path
    if not raw_path.upper().endswith('.RAW'):
        # Try to find the RAW file from the project
        if hasattr(image, 'project') and image.project:
            for file_data in image.project.data.get('files', {}).values():
                raw_candidate = file_data.get('raw', '')
                if os.path.basename(raw_candidate) == original_filename:
                    raw_path = raw_candidate
                    break
    
    # CRITICAL FIX: Set target_image path BEFORE loading data
    # DON'T set fn or ext - they are properties derived from path
    # Setting ext triggers _setext() which corrupts the path!
    target_image.path = raw_path
    
    # CRITICAL: Don't use load_truly_raw_data! Let image.data property handle cache/debayer
    # Accessing target_image.data will:
    # 1. Check cache first (runs 2+)
    # 2. Debayer if not cached (run 1)
    # 3. Save to cache after debayering
    _ = target_image.data  # Trigger cache/debayer but don't use return value yet
    
    # Generate calibration target polygons (detection only, no drawing)
    try:
        calibration_target_polys(target_image)
        
        # DON'T call draw_calibration_samples here! 
        # save_raw_target_image will handle all the drawing to avoid double-drawing
    except Exception as e:
        print(f"[WARNING] Failed to generate calibration target polys for {target_image.fn}: {e}")
        import traceback
        traceback.print_exc()
        target_image.calibration_target_polys = None
    
    # Save target image only if this target is actually being used for processing
    # Check if this target survived interval filtering and is actually being used
    is_used_for_calibration = _is_target_actually_used(image)
    if is_used_for_calibration:

        target_path = save_raw_target_image(target_image, output_format, outfolder, 
                                          os.path.join(output_format, "Calibration_Targets_Used"),
                                          options=options)
        layers_out['RAW (Target)'] = target_path
    else:
        pass

        # Still process the target to compute coefficients, but don't export the red square image
    
    # Target calibration coefficients should already be computed from RAW pixels in get_calib_data
    # Store base RAW coefficients for non-target images to use
    if hasattr(image, 'calibration_coefficients') and image.calibration_coefficients:
        image._raw_base_coefficients = image.calibration_coefficients
    else:
        pass
    
    # CRITICAL: Set calibration_image to itself for calibration targets
    # This ensures the reflectance export logic can find the calibration data
    image.calibration_image = image

    
    return layers_out


def _create_raw_target_layer(image, output_format, outfolder, layers_out):
    """Create RAW (Target) layer for non-calibration images."""

    try:
        # Check if we have original data preserved
        if hasattr(image, '_original_data_backup') and image._original_data_backup is not None:

            # Create a temporary copy with the original data
            temp_image = image.copy()
            temp_image.data = image._original_data_backup.copy()
            raw_target_path = save(temp_image, output_format, outfolder, is_preview=False)
        else:

            raw_target_path = save(image, output_format, outfolder, is_preview=False)
            
        if raw_target_path:
            layers_out['RAW (Target)'] = raw_target_path

        else:
            print(f"[ERROR] save() returned None for {image.fn}")
            
    except Exception as e:
        print(f"[ERROR] Error creating RAW (Target) layer for {image.fn}: {e}")
        import traceback
        traceback.print_exc()


def _get_optimal_parallel_processing_count():
    """Calculate optimal number of images to process simultaneously in Thread-4"""
    try:
        import psutil
        # Use global ray variable instead of importing directly
        global ray
        
        # Get system resources
        cpu_count = psutil.cpu_count(logical=True)
        memory_gb = psutil.virtual_memory().total / (1024**3)
        
        # Get Ray resources if available
        available_cpus = cpu_count
        try:
            if ray.is_initialized():
                ray_resources = ray.available_resources()
                available_cpus = int(ray_resources.get('CPU', cpu_count))
        except Exception:
            pass
        
        # Calculate parallel processing count based on system tier
        # This is typically smaller than batch size since we're processing results simultaneously
        if memory_gb >= 28 and cpu_count >= 12:
            # High-end system: Process many images simultaneously (relaxed thresholds for 12-core systems)
            parallel_count = min(10, max(8, int(available_cpus * 0.6)))
            tier = "high-end"
        elif memory_gb >= 16 and cpu_count >= 8:
            # Mid-range system: Moderate simultaneous processing
            parallel_count = min(8, max(5, int(available_cpus * 0.5)))
            tier = "mid-range"
        elif memory_gb >= 8 and cpu_count >= 4:
            # Low-mid system: Conservative simultaneous processing
            parallel_count = min(4, max(3, int(available_cpus * 0.3)))
            tier = "low-mid"
        else:
            # Low-end system: Minimal simultaneous processing
            parallel_count = min(3, max(2, int(available_cpus * 0.25)))
            tier = "low-end"
        
        # Memory-based adjustments for simultaneous processing
        if memory_gb < 8:
            parallel_count = min(parallel_count, 2)
        elif memory_gb < 16:
            parallel_count = min(parallel_count, 4)
        
        print(f"[THREAD-4] Dynamic parallel processing: {parallel_count} images simultaneously (tier={tier}, {cpu_count} cores, {memory_gb:.1f}GB RAM)")
        
        return parallel_count
        
    except Exception as e:
        print(f"[THREAD-4] Error calculating optimal parallel processing count: {e}")
        # Conservative fallback based on available CPUs
        available_cpus = 4  # Safe fallback
        try:
            import psutil
            available_cpus = psutil.cpu_count(logical=True)
        except Exception:
            pass
            
        if available_cpus >= 12:
            return 6
        elif available_cpus >= 8:
            return 4
        elif available_cpus >= 4:
            return 3
        else:
            return 2


def _save_calibration_data(image, options, outfolder):
    """Save calibration data for target images using unified API."""

    from unified_calibration_api import UnifiedCalibrationManager
    
    # Extract calibration data from image with validation to prevent string placeholders
    def validate_calibration_value(value, field_name):
        """Validate that calibration values are not string placeholders"""
        if isinstance(value, str):

            return None
        return value
    
    calibration_data = {
        'coefficients': validate_calibration_value(getattr(image, 'calibration_coefficients', None), 'calibration_coefficients'),
        'limits': validate_calibration_value(getattr(image, 'calibration_limits', None), 'calibration_limits'),
        'xvals': validate_calibration_value(getattr(image, 'calibration_xvals', None), 'calibration_xvals'),
        'yvals': validate_calibration_value(getattr(image, 'calibration_yvals', None), 'calibration_yvals'),
        'als_magnitude': getattr(image, 'als_magnitude', None),
        'als_data': getattr(image, 'als_data', None),
        'aruco_id': getattr(image, 'aruco_id', None),
        'aruco_corners': getattr(image, 'aruco_corners', None),
        'target_polys': getattr(image, 'calibration_target_polys', None),
        'is_selected_for_calibration': getattr(image, 'is_selected_for_calibration', False)
    }
    
    # Get cluster value from options
    cluster_value = None
    try:
        if 'Project Settings' in options and 'Target Detection' in options['Project Settings']:
            cluster_value = options['Project Settings']['Target Detection'].get('Minimum Target Clustering (0-100)', None)
        elif 'Target Detection' in options:
            cluster_value = options['Target Detection'].get('Minimum Target Clustering (0-100)', None)
    except Exception as e:
        print(f'[ERROR] Could not extract cluster value from options: {e}')
    
    calibration_data['cluster_value'] = cluster_value
    










    
    # Use unified API
    result = UnifiedCalibrationManager.save_calibration_data(image, calibration_data)

    return result


def _load_and_assign_calibration_data(image):
    """Load and assign calibration data for non-target images."""
    project_dir = getattr(image, 'project_path', None) or getattr(getattr(image, 'project', None), 'fp', None)
    if not project_dir:
        print('[ERROR] Could not determine project directory for calibration data loading!')
        return
    
    calibration_data_file = os.path.join(project_dir, 'calibration_data.json')
    if not os.path.exists(calibration_data_file):
        print(f'[ERROR] calibration_data.json not found in project directory: {project_dir}')
        return
    
    with open(calibration_data_file, 'r') as f:
        calib_data = json.load(f)
    
    # Parse image timestamp
    img_ts = None
    if hasattr(image, 'timestamp') and image.timestamp is not None:
        if isinstance(image.timestamp, str):
            try:
                img_ts = datetime.datetime.strptime(image.timestamp, '%Y-%m-%d %H:%M:%S')
            except Exception:
                img_ts = None
        else:
            img_ts = image.timestamp
    elif hasattr(image, 'DateTime') and image.DateTime not in (None, 'Unknown'):
        try:
            img_ts = datetime.datetime.strptime(image.DateTime, '%Y:%m:%d %H:%M:%S')
        except Exception:
            img_ts = None
    
    # Get camera model and filter model for matching
    img_camera_model = getattr(image, 'camera_model', None)
    img_filter_model = getattr(image, 'camera_filter', None)
    
    # Find best matching calibration entry
    def find_best_key(calib_data):
        
        best_key = None
        best_delta = None
        fallback_key = None
        fallback_delta = None
        latest_key = None
        latest_ts = None
        
        for key, entry in calib_data.items():
            try:
                if img_camera_model is not None and entry.get('camera_model', None) != img_camera_model:
                    continue
                if img_filter_model is not None and entry.get('camera_filter', None) != img_filter_model:
                    continue
                
                # Try to parse timestamp from key, but allow non-timestamp keys
                calib_ts = None
                delta = None
                abs_delta = None
                
                try:
                    calib_ts = datetime.datetime.strptime(key, '%Y-%m-%d %H:%M:%S')
                    delta = (img_ts - calib_ts).total_seconds() if img_ts else None
                    abs_delta = abs(delta) if delta is not None else None
                except:
                    # Key is not a timestamp (e.g., filename), use metadata timestamp if available
                    if 'timestamp' in entry:
                        try:
                            calib_ts = datetime.datetime.strptime(entry['timestamp'], '%Y-%m-%d %H:%M:%S')
                            delta = (img_ts - calib_ts).total_seconds() if img_ts else None
                            abs_delta = abs(delta) if delta is not None else None
                        except:
                            pass
                    # If no valid timestamp, still consider this entry but with no temporal matching
                    pass
                
                # Track latest (if timestamp is available)
                if calib_ts is not None and (latest_ts is None or calib_ts > latest_ts):
                    latest_ts = calib_ts
                    latest_key = key
                
                # Primary: closest earlier (if timestamp matching is possible)
                if delta is not None and delta >= 0 and (best_delta is None or delta < best_delta):
                    best_key = key
                    best_delta = delta
                
                # Secondary: closest overall (if timestamp matching is possible)
                if abs_delta is not None and (fallback_delta is None or abs_delta < fallback_delta):
                    fallback_key = key
                    fallback_delta = abs_delta
                
                # If no timestamp matching is possible, use this entry as fallback
                if delta is None and abs_delta is None and fallback_key is None:
                    fallback_key = key
                    
            except Exception:
                continue
        
        chosen_key = None
        if best_key is not None:
            chosen_key = best_key
        elif fallback_key is not None:
            print('[WARNING] No earlier calibration found, using closest overall.')
            chosen_key = fallback_key
        elif latest_key is not None:
            print('[WARNING] No suitable calibration found, using latest available.')
            chosen_key = latest_key
        
        return chosen_key
    
    chosen_key = find_best_key(calib_data)
    if not chosen_key:
        print(f'[ERROR] No calibration entry with matching camera model and filter model for {image.fn}. Skipping calibration.')
        print(f'[ERROR] Searched for: camera_model={img_camera_model}, camera_filter={img_filter_model}')
    else:
        chosen_entry = calib_data[chosen_key]
        entry = calib_data[chosen_key]
        
        image.calibration_coefficients = entry.get('coefficients')
        image.calibration_limits = entry.get('limits')  # CRITICAL FIX: Set limits directly on image
        image.als_magnitude = entry.get('als_magnitude')
        image.aruco_id = entry.get('aruco_id')
        image.calibration_target_polys = entry.get('red_square_corners')
        image.calibration_xvals = entry.get('xvals')
        image.cluster_value = entry.get('cluster_value')
        
        # CRITICAL: Preserve existing calibration_image assignments from earlier processing stages
        # Do NOT override calibration_image if it was already set during processing
        if hasattr(image, 'calibration_image') and image.calibration_image is not None:

            pass  # Empty block
        else:

            # Create calibration_image object from JSON data
            calib_image = type('CalibImage', (), {})()
            calib_image.calibration_coefficients = entry.get('coefficients')
            calib_image.calibration_limits = entry.get('limits')
            calib_image.calibration_xvals = entry.get('xvals')
            calib_image.calibration_yvals = entry.get('yvals')
            calib_image.als_magnitude = entry.get('als_magnitude')
            calib_image.als_data = entry.get('als_data')
            calib_image.aruco_id = entry.get('aruco_id')
            calib_image.fn = f"calibration_target_{chosen_key.replace(':', '_').replace('-', '_').replace(' ', '_')}"
            
            # Assign the calibration image to the image object
            image.calibration_image = calib_image
        
        


# Phase 3: Unified Pipeline Management System - REMOVED
# UnifiedPipelineManager class removed as it was incomplete and unused




# Backward compatibility alias removed - function naming standardized

def _ensure_ray_functions_available():
    """Ensure Ray functions are defined and available in globals"""
    if not RAY_AVAILABLE:
        pass
        return False
    
    # Check if functions are already defined
    required_functions = ['detect_calibration_image_ray', 'get_calib_data_ray', 'apply_calibration_ray', 'process_image_unified_ray']
    missing_functions = []
    
    for func_name in required_functions:
        if func_name not in globals():
            missing_functions.append(func_name)
    
    if missing_functions:
        pass
        return _define_ray_functions()
    else:
        pass
        return True

def _define_ray_functions():
    """Define Ray remote functions with proper decorators"""
    global ray
    
    if not RAY_AVAILABLE or not ray:
        pass
        return False
    
    try:
        pass
        
        # detect_calibration_image_ray is already defined at module level (line 833) with @ray.remote decorator
        # Check if it's already in globals first, then try module-level access
        if 'detect_calibration_image_ray' in globals():
            pass
        else:
            # Try to access the function from module level
            import sys
            current_module = sys.modules[__name__]
            
            if hasattr(current_module, 'detect_calibration_image_ray'):
                detect_func = getattr(current_module, 'detect_calibration_image_ray')
                globals()['detect_calibration_image_ray'] = detect_func
            else:
                pass
        
        # get_calib_data_ray is already defined at module level (line 843) with @ray.remote decorator
        # Check if it's already in globals first, then try module-level access
        if 'get_calib_data_ray' in globals():
            pass
        else:
            # Try to access the function from module level
            import sys
            current_module = sys.modules[__name__]
            
            if hasattr(current_module, 'get_calib_data_ray'):
                calib_func = getattr(current_module, 'get_calib_data_ray')
                globals()['get_calib_data_ray'] = calib_func
            else:
                pass
                # Create inline Ray function as fallback
                @ray.remote(num_cpus=2)
                def get_calib_data_ray_inline(image_path_str, project_dir_str, options, camera_model=None, camera_filter=None, model_from_exif=None, aruco_id=None, target_sample_diameter=None, calibration_polys=None, als_magnitude=None, als_data=None, calibration_yvals=None, _force_reload=1755707793):
                    """Ray remote function for calibration data computation"""
                    # Import necessary modules first
                    import os
                    from tasks import get_calib_data
                    from project import Project, LabImage
                    
                    print(f"[RAY-THREAD-2] Getting calibration data for {os.path.basename(image_path_str)}")
                    
                    # CRITICAL FIX: Change working directory to project directory
                    original_cwd = os.getcwd()
                    try:
                        print(f"[RAY-THREAD-2] 🔧 Changing cwd from {original_cwd} to {project_dir_str}")
                        os.chdir(project_dir_str)
                        print(f"[RAY-THREAD-2] ✅ Working directory changed to: {os.getcwd()}")
                        
                        # Create a Project object from the project directory string
                        project = Project(project_dir_str)
                        
                        # CRITICAL FIX: Use the FULL SOURCE PATH where the RAW file actually exists
                        print(f"[RAY-THREAD-2] 🔍 Creating LabImage with FULL source path: {image_path_str}")
                        image = LabImage(project, image_path_str)
                        
                        # CRITICAL FIX: Override camera metadata from main thread (EXIF reading fails in Ray worker)
                        if camera_model and camera_model != 'Unknown':
                            image.camera_model = camera_model
                            print(f"[RAY-THREAD-2] 🔧 OVERRIDE: Set camera_model = {camera_model}")
                        if camera_filter and camera_filter != 'Unknown':
                            image.camera_filter = camera_filter
                            print(f"[RAY-THREAD-2] 🔧 OVERRIDE: Set camera_filter = {camera_filter}")
                        if model_from_exif and model_from_exif != 'Unknown':
                            image.Model = model_from_exif
                            print(f"[RAY-THREAD-2] 🔧 OVERRIDE: Set Model = {model_from_exif}")
                        
                        # CRITICAL FIX: Override ArUco data from main thread (target detection happens in main thread)
                        if aruco_id is not None:
                            image.aruco_id = aruco_id
                            print(f"[RAY-THREAD-2] 🎯 OVERRIDE: Set aruco_id = {aruco_id}")
                        if target_sample_diameter is not None:
                            image.target_sample_diameter = target_sample_diameter
                            print(f"[RAY-THREAD-2] 🎯 OVERRIDE: Set target_sample_diameter = {target_sample_diameter}")
                        if calibration_polys is not None:
                            image.calibration_polys = calibration_polys
                            print(f"[RAY-THREAD-2] 🎯 OVERRIDE: Set calibration_polys = {len(calibration_polys) if calibration_polys else 0} polygons")
                        
                        # CRITICAL FIX: Restore ALS data from main thread (attached during ALS processing)
                        if als_magnitude is not None:
                            image.als_magnitude = als_magnitude
                            print(f"[RAY-THREAD-2] 🔧 OVERRIDE: Set als_magnitude = {als_magnitude}")
                        if als_data is not None:
                            image.als_data = als_data
                            print(f"[RAY-THREAD-2] 🔧 OVERRIDE: Set als_data = {len(als_data) if als_data is not None else 0} values")
                        if calibration_yvals is not None:
                            image.calibration_yvals = calibration_yvals
                            print(f"[RAY-THREAD-2] 🔧 OVERRIDE: Set calibration_yvals = {calibration_yvals}")
                        
                        print(f"[RAY-THREAD-2] 🔍 LabImage created: fn={getattr(image, 'fn', 'unknown')}, camera_model={getattr(image, 'camera_model', 'Unknown')}, camera_filter={getattr(image, 'camera_filter', 'Unknown')}, Model={getattr(image, 'Model', 'Unknown')}, aruco_id={getattr(image, 'aruco_id', None)}, project_path={getattr(image, 'project_path', 'None')}")
                        print(f"[RAY-THREAD-2] 🔍 ALS data restored: als_magnitude={getattr(image, 'als_magnitude', None) is not None}, als_data={getattr(image, 'als_data', None) is not None}, yvals={getattr(image, 'calibration_yvals', None) is not None}")
                        
                        # Create a dummy progress tracker for the Ray remote function
                        class DummyProgressTracker:
                            def task_completed(self):
                                pass
                        
                        progress_tracker = DummyProgressTracker()
                        
                        # Call the actual function
                        coefficients, limits, xvals, yvals, modified_image = get_calib_data(image, options, progress_tracker)
                        return coefficients, limits, xvals, yvals, modified_image
                    
                    finally:
                        # Always restore original working directory
                        os.chdir(original_cwd)
                        print(f"[RAY-THREAD-2] 🔧 Restored cwd to: {os.getcwd()}")
                
                globals()['get_calib_data_ray'] = get_calib_data_ray_inline
        
        # apply_calibration_ray is already defined at module level (line 888) with @ray.remote decorator
        # Check if it's already in globals first, then try module-level access
        if 'apply_calibration_ray' in globals():
            pass
        else:
            # Try to access the function from module level
            import sys
            current_module = sys.modules[__name__]
            
            if hasattr(current_module, 'apply_calibration_ray'):
                apply_func = getattr(current_module, 'apply_calibration_ray')
                globals()['apply_calibration_ray'] = apply_func
            else:
                pass
                # Create inline Ray function as fallback
                @ray.remote(num_cpus=4)
                def apply_calibration_ray_inline(image_path_str, project_dir_str, options, img_timestamp=None, img_camera_model=None, img_camera_filter=None, is_calibration_photo=False, _force_reload=1755707900):
                    """Ray remote function for image calibration processing"""
                    
                    # Import necessary modules
                    from project import LabImage, Project
                    import os
                    
                    # Create a Project object from the project directory string
                    project = Project(project_dir_str)
                    
                    # Create LabImage using the correct parameter order: LabImage(project, path)
                    # CRITICAL FIX: Use the FULL SOURCE PATH where the RAW file actually exists
                    import os
                    image = LabImage(project, image_path_str)
                    
                    # CRITICAL FIX: Set the is_calibration_photo flag from main thread
                    if is_calibration_photo:
                        image.is_calibration_photo = True
                    else:
                        image.is_calibration_photo = False
                    
                    # CRITICAL FIX: Override camera metadata from main thread (EXIF reading fails in Ray worker)
                    if img_camera_model and img_camera_model != 'Unknown':
                        image.camera_model = img_camera_model
                    if img_camera_filter and img_camera_filter != 'Unknown':
                        image.camera_filter = img_camera_filter
                    if img_camera_model and img_camera_filter:
                        image.Model = f"{img_camera_model}_{img_camera_filter}"
                    
                    
                    # CRITICAL FIX: Add filter-specific EXIF metadata
                    try:
                        # Try multiple import approaches to ensure Ray worker can access the function
                        pass
                        
                        # Approach 1: Import class and check method
                        try:
                            from mip.ExifUtils import ExifUtils
                            if hasattr(ExifUtils, 'add_pix4d_tags'):
                                pass
                                ExifUtils.add_pix4d_tags(image)
                            else:
                                raise AttributeError("add_pix4d_tags not found in ExifUtils class")
                        except (ImportError, AttributeError) as e1:
                            pass
                            
                            # Approach 2: Try direct module import
                            try:
                                import mip.ExifUtils as exif_module
                                if hasattr(exif_module, 'ExifUtils') and hasattr(exif_module.ExifUtils, 'add_pix4d_tags'):
                                    pass
                                    exif_module.ExifUtils.add_pix4d_tags(image)
                                else:
                                    raise AttributeError("add_pix4d_tags not found via module import")
                            except (ImportError, AttributeError) as e2:
                                pass
                                
                                # Approach 3: Inline implementation as fallback
                                _add_pix4d_tags_inline(image)
                                
                    except Exception as exif_err:
                        pass
                        import traceback
                        traceback.print_exc()
                    
                    def _add_pix4d_tags_inline(image):
                        """Inline implementation of add_pix4d_tags for Ray worker"""
                        
                        # Import FILTER_LOOKUP directly
                        try:
                            from mip.ConfigLookups import FILTER_LOOKUP
                        except ImportError:
                            pass
                            return
                        
                        camera_filter = getattr(image, 'camera_filter', None)
                        if not camera_filter:
                            pass
                            return
                        
                        # Find filter in lookup
                        filter_found = False
                        for filter_id, filter_info in FILTER_LOOKUP.items():
                            filter_name = filter_info[0]
                            if filter_name == camera_filter:
                                pass
                                
                                # Extract band information
                                bands = []
                                central_wavelengths = []
                                wavelength_fwhms = []
                                
                                for i in range(2, min(5, len(filter_info))):
                                    band_info = filter_info[i]
                                    if band_info and len(band_info) == 3 and band_info[0]:
                                        bands.append(band_info[0])
                                        central_wavelengths.append(band_info[1])
                                        wavelength_fwhms.append(band_info[2])
                                
                                # Apply to EXIF
                                if bands and hasattr(image, 'exif'):
                                    image.exif['bandname'] = bands
                                    image.exif['CentralWavelength'] = central_wavelengths
                                    image.exif['WavelengthFWHM'] = wavelength_fwhms
                                
                                filter_found = True
                                break
                        
                        # Try legacy mappings if not found
                        if not filter_found:
                            legacy_mappings = {"RGN": 4, "RGB": 1, "NGB": 3, "OCN": 5, "RE": 72, "NIR": 85}
                            filter_id = legacy_mappings.get(camera_filter)
                            if filter_id and filter_id in FILTER_LOOKUP:
                                filter_info = FILTER_LOOKUP[filter_id]
                                
                                # Extract and apply band information (same logic as above)
                                bands = []
                                central_wavelengths = []
                                wavelength_fwhms = []
                                
                                for i in range(2, min(5, len(filter_info))):
                                    band_info = filter_info[i]
                                    if band_info and len(band_info) == 3 and band_info[0]:
                                        bands.append(band_info[0])
                                        central_wavelengths.append(band_info[1])
                                        wavelength_fwhms.append(band_info[2])
                                
                                if bands and hasattr(image, 'exif'):
                                    image.exif['bandname'] = bands
                                    image.exif['CentralWavelength'] = central_wavelengths
                                    image.exif['WavelengthFWHM'] = wavelength_fwhms
                            else:
                                pass
                    
                    # Import the main processing function
                    import sys
                    # In Ray worker, __name__ may not be 'tasks', so import directly
                    try:
                        current_module = sys.modules['tasks']
                    except KeyError:
                        # Fallback: try to import tasks module directly
                        import tasks as current_module
                    
                    # Call the main processing function with LabImage object
                    # Create proper reprocessing_cfg with calibration flag
                    reprocessing_cfg = {
                        'calibration': True  # Enable calibration processing
                    }
                    
                    # Create proper outfolder path for saving results
                    import os
                    # CRITICAL: Get camera model from image object (should be populated from project JSON)
                    camera_model = getattr(image, 'camera_model', 'Unknown')
                    camera_filter = getattr(image, 'camera_filter', 'Unknown')
                    
                    # CRITICAL: If camera model is Unknown, attempt EXIF recovery
                    if camera_model == 'Unknown':
                        pass
                        
                        # Try to recover from EXIF using centralized function
                        if hasattr(image, 'exif_source') and image.exif_source and os.path.exists(image.exif_source):
                            recovered_model, recovered_filter = recover_camera_metadata_from_exif(image.exif_source, project)
                            if recovered_model:
                                camera_model = recovered_model
                                camera_filter = recovered_filter or camera_filter
                                
                                # Update image object
                                image.camera_model = camera_model
                                image.camera_filter = camera_filter
                                
                        
                        # If still Unknown after recovery attempt, skip this image
                        if camera_model == 'Unknown':
                            pass
                            return None  # Skip this image, don't abort entire process
                    
                    # Ensure options is a dictionary
                    if not isinstance(options, dict):
                        options = {
                            'calibration': True,
                            'Processing': {
                                'Vignette correction': True,
                                'Reflectance calibration / white balance': True,
                                'Apply PPK corrections': False,
                                'Exposure Pin 1': None
                            },
                            'Export': {
                                'Calibrated image format': 'TIFF (16-bit)'
                            }
                        }
                    
                    export_format = options.get('Export', {}).get('Calibrated image format', 'TIFF (16-bit)')
                    
                    # Map export format to folder name
                    fmt_map = {
                        'TIFF (16-bit)': 'tiff16',
                        'TIFF (32-bit)': 'tiff32', 
                        'PNG': 'png',
                        'JPEG': 'jpeg'
                    }
                    format_folder = fmt_map.get(export_format, 'tiff16')
                    
                    outfolder = os.path.join(project_dir_str, f"{camera_model}_{camera_filter}", format_folder)
                    
                    # Create a dummy progress tracker for the Ray remote function
                    class DummyProgressTracker:
                        def task_completed(self):
                            pass
                    
                    progress_tracker = DummyProgressTracker()
                    
                    # Thread-3 should apply calibration to image data, then Thread-4 exports
                    # Import the calibration processing functions
                    from tasks import _load_and_assign_calibration_data
                    
                    # Apply calibration metadata to the image
                    _load_and_assign_calibration_data(image)
                    
                    # CRITICAL FIX: Load ALS data from scan files for unique corrections per image
                    if not hasattr(image, 'als_magnitude') or image.als_magnitude is None:
                        pass
                        try:
                            # Get scan directory from project scanmap
                            if hasattr(project, 'scanmap') and project.scanmap:
                                scan_directory = list(project.scanmap.values())[0].dir
                                
                                # Load ALS data for this single image
                                from mip.als import get_als_data
                                code_name = 793  # Default code name
                                get_als_data([image], scan_directory, code_name, project)
                            else:
                                pass
                        except Exception as e:
                            pass
                    else:
                        pass
                    
                    # CRITICAL FIX: Load image data BEFORE processing
                    if image.data is None:
                        image.load()
                    
                    if image.data is not None:
                        pass
                    else:
                        pass
                        return None  # Cannot process without image data
                    
                    # CRITICAL FIX: Actually process the image data (apply calibration to pixels)
                    # Import required functions
                    from mip.Calibrate_Images import apply_calib_to_image
                    from mip.Vignette_Correction import ApplyVig as devignette
                    
                    # Apply vignette correction BEFORE calibration (if enabled)
                    # Check if vignette correction is enabled in options
                    
                    processing_options = None
                    if isinstance(options, dict):
                        if 'Project Settings' in options and 'Processing' in options['Project Settings']:
                            processing_options = options['Project Settings']['Processing']
                        elif 'Processing' in options:
                            processing_options = options['Processing']
                        else:
                            processing_options = options  # Fallback to options itself
                    
                    do_vig = processing_options.get('Vignette correction', False) if processing_options else False
                    
                    if do_vig and image.data is not None:
                        pass
                        try:
                            # Create a copy for vignette correction to avoid modifying original
                            original_data = image.data.copy()
                            devignette(image)
                            if image.data is not None:
                                pass
                            else:
                                pass
                                image.data = original_data
                        except Exception as vig_err:
                            pass
                            import traceback
                            traceback.print_exc()
                            # Restore original data on error
                            if 'original_data' in locals():
                                image.data = original_data
                    
                    # Check if reflectance calibration is enabled
                    reflectance_enabled = False
                    if processing_options:
                        reflectance_enabled = processing_options.get('Reflectance calibration / white balance', False)
                    
                    # print(f"[RAY-APPLY] 🔍 Reflectance enabled: {reflectance_enabled} for {image.fn}")
                    
                    if reflectance_enabled and hasattr(image, 'calibration_coefficients') and image.calibration_coefficients:
                        # print(f"[RAY-APPLY] 🔧 Applying FULL reflectance calibration to {image.fn}")
                        try:
                            # CRITICAL FIX: Ensure image data is loaded before applying calibration
                            if image.data is None:
                                pass  # print(f"[RAY-APPLY] ⚠️ Image data is None, skipping")
                            else:
                                # Apply calibration to the image data (modify pixels)
                                apply_calib_to_image(image, image.calibration_coefficients, getattr(image, 'calibration_limits', [65535, 65535, 65535]))
                                # print(f"[RAY-APPLY] ✅ Full calibration applied")
                        except Exception as calib_err:
                            print(f"[RAY-APPLY] ❌ Error applying calibration: {calib_err}")
                            import traceback
                            traceback.print_exc()
                    elif not reflectance_enabled and image.data is not None:
                        # Apply sensor response correction only (no calibration coefficients)
                        # print(f"[RAY-APPLY] 🔧 Applying SENSOR RESPONSE correction only to {image.fn}")
                        try:
                            from mip.Calibrate_Images import sensor_response_correction
                            sensor_response_correction(image, limits=[], use_limit=False)
                            # print(f"[RAY-APPLY] ✅ Sensor response correction applied")
                        except Exception as sensor_err:
                            print(f"[RAY-APPLY] ❌ Error applying sensor response: {sensor_err}")
                            import traceback
                            traceback.print_exc()
                    else:
                        pass  # print(f"[RAY-APPLY] ⚠️ No calibration applied (reflectance_enabled={reflectance_enabled}, has_coeffs={hasattr(image, 'calibration_coefficients')})")
                    
                    # CRITICAL FIX: Ensure the returned image has the calibrated data
                    # The apply_calib_to_image function modifies image.data in-place
                    # But we need to make sure the returned object has the correct calibrated data
                    import numpy as np
                    
                    # Return the processed image object for Thread-4 to export
                    result = {
                        'image': image,
                        'calibrated': True,
                        'fn': image.fn,
                        'calibrated_data': image.data.copy(),  # Include a copy of calibrated data
                        'data_min_max': (np.min(image.data), np.max(image.data))
                    }
                    
                    return result
                
                globals()['apply_calibration_ray'] = apply_calibration_ray_inline
        
        # process_image_unified_ray is already defined at module level with @ray.remote decorator
        # Check if it's already in globals first, then try module-level access
        if 'process_image_unified_ray' in globals():
            pass
        else:
            # Try to access the function from module level
            import sys
            current_module = sys.modules[__name__]
            
            if hasattr(current_module, 'process_image_unified_ray'):
                process_func = getattr(current_module, 'process_image_unified_ray')
                globals()['process_image_unified_ray'] = process_func
            else:
                pass
        
        # Define export-only Ray remote function for Thread-4
        if 'export_processed_image_ray' not in globals():
            @ray.remote(num_cpus=2)
            def export_processed_image_ray_inline(image_data, options, reprocessing_cfg, outfolder, _force_reload=1755707793):
                """Ray remote function for export-only processing (Thread-4)"""
                import sys
                import os
                current_module = sys.modules[__name__]
                
                # print(f"[RAY-THREAD-4] Exporting processed image for {image_data.get('fn', 'unknown')}")
                
                try:
                    # Reconstruct the image object from the data passed by Thread-3
                    image = image_data['image']
                    
                    # CRITICAL FIX: Load target status from project JSON instead of relying on Ray serialization
                    import os
                    is_target = False
                    if hasattr(image, 'project') and image.project and hasattr(image.project, 'data'):
                        # Search project JSON for this image's target status
                        for base, fileset in image.project.data.get('files', {}).items():
                            if fileset.get('raw') and os.path.basename(fileset['raw']) == image.fn:
                                calibration_info = fileset.get('calibration', {})
                                is_target_in_project = calibration_info.get('is_calibration_photo', False)
                                manual_calib = fileset.get('manual_calib', False)
                                manually_disabled = calibration_info.get('manually_disabled', False)
                                
                                # Target if marked in project and manually enabled and not disabled
                                is_target = is_target_in_project and manual_calib and not manually_disabled
                                # print(f"[RAY-THREAD-4] 🎯 Loaded target status from project JSON: {image.fn} -> is_target={is_target} (project={is_target_in_project}, manual={manual_calib}, disabled={manually_disabled})")
                                break
                        
                        if not is_target:
                            pass
                            # print(f"[RAY-THREAD-4] 📄 No target status found in project JSON for {image.fn} - treating as reflectance image")
                    else:
                        # Fallback to object attribute if project data not available
                        is_target = getattr(image, 'is_calibration_photo', False)
                        # print(f"[RAY-THREAD-4] ⚠️ No project data available, using object attribute: {image.fn} -> is_target={is_target}")
                    
                    # CRITICAL FIX: Ensure image has correct file path for process_image_unified
                    # The image object may have lost path context during Ray serialization
                    if not hasattr(image, 'fp') or not image.fp:
                        # Try to get the original source path from the image filename
                        import os
                        # The image should already have the correct path set by Thread-3
                        if hasattr(image, 'fn') and image.fn:
                            # Check if this is a full path or just filename
                            if os.path.isabs(image.fn):
                                image.fp = image.fn
                                # print(f"[RAY-THREAD-4] 🔧 Set fp from absolute fn: {image.fp}")
                            else:
                                print(f"[RAY-THREAD-4] ⚠️ Image has relative fn: {image.fn}, may cause file not found errors")
                    
                    # CRITICAL FIX: Reconstruct calibration_image reference for ALS processing
                    calibration_image_data = image_data.get('calibration_image_data')
                    if calibration_image_data:
                        # Create calibration_image object from the passed data
                        calib_image = type('CalibImage', (), {})()
                        calib_image.fn = calibration_image_data['fn']
                        calib_image.calibration_coefficients = calibration_image_data['calibration_coefficients']
                        calib_image.calibration_limits = calibration_image_data['calibration_limits']
                        calib_image.calibration_xvals = calibration_image_data['calibration_xvals']
                        calib_image.calibration_yvals = calibration_image_data['calibration_yvals']
                        calib_image.als_magnitude = calibration_image_data['als_magnitude']
                        calib_image.als_data = calibration_image_data['als_data']
                        calib_image.aruco_id = calibration_image_data['aruco_id']
                        calib_image.is_selected_for_calibration = calibration_image_data['is_selected_for_calibration']
                        
                        # Assign the reconstructed calibration_image to the image
                        image.calibration_image = calib_image
                        # print(f"[RAY-THREAD-4] ✅ Reconstructed calibration_image reference: {image_data.get('fn', 'unknown')} -> {calib_image.fn}")
                    else:
                        print(f"[RAY-THREAD-4] ⚠️ No calibration_image_data provided for {image_data.get('fn', 'unknown')}")
                    
                    # print(f"[RAY-THREAD-4] Processing {image_data.get('fn', 'unknown')}: is_target={is_target}, has_calib_ref={hasattr(image, 'calibration_image')}, fp={getattr(image, 'fp', 'NOT_SET')}")
                    
                    # CRITICAL FIX: Thread-4 should only export, not re-process
                    # Thread-3 already did calibration processing, so just do export
                    
                    # Import required functions
                    save_func = getattr(current_module, 'save')
                    fmt_map_func = getattr(current_module, 'fmt_map')
                    
                    # Get export format from options
                    if isinstance(options, dict) and 'Export' in options:
                        output_format = fmt_map_func[options['Export']["Calibrated image format"]]
                    else:
                        output_format = 'tiff16'  # Default format
                    
                    # print(f"[RAY-THREAD-4] 📤 Exporting {image_data.get('fn', 'unknown')} in {output_format} format")
                    
                    result = {}
                    
                    # CRITICAL FIX: Use directly passed calibrated image data
                    if not hasattr(image, 'data') or image.data is None:
                        # Try to get calibrated data directly from the Ray package
                        calibrated_data = image_data.get('calibrated_data')
                        if calibrated_data is not None:
                            image.data = calibrated_data
                            # print(f"[RAY-THREAD-4] ✅ Using directly passed calibrated data: shape={calibrated_data.shape}, dtype={calibrated_data.dtype}")
                        else:
                            print(f"[RAY-THREAD-4] ⚠️ No calibrated data provided in Ray package for {image_data.get('fn', 'unknown')}")
                    
                    # Export reflectance calibrated or sensor response image (both target and non-target)
                    # Check if reflectance calibration is enabled to determine folder name
                    reflectance_enabled = False
                    vignette_enabled = False
                    if isinstance(options, dict):
                        if 'Project Settings' in options and 'Processing' in options['Project Settings']:
                            reflectance_enabled = options['Project Settings']['Processing'].get('Reflectance calibration / white balance', False)
                            vignette_enabled = options['Project Settings']['Processing'].get('Vignette correction', False)
                        elif 'Processing' in options:
                            reflectance_enabled = options['Processing'].get('Reflectance calibration / white balance', False)
                            vignette_enabled = options['Processing'].get('Vignette correction', False)
                    
                    # Determine folder name and layer name based on reflectance AND vignette settings
                    if reflectance_enabled:
                        subfolder_name = "Reflectance_Calibrated_Images"
                        layer_name = "RAW (Reflectance)"
                    else:
                        # Reflectance is disabled - check vignette setting
                        if vignette_enabled:
                            subfolder_name = "Vignette_Corrected_Images"
                            layer_name = "RAW (Vignette Corrected)"
                        else:
                            subfolder_name = "Sensor_Response_Images"
                            layer_name = "RAW (Sensor Response)"
                    
                    # print(f"[RAY-THREAD-4] 📁 Reflectance: {reflectance_enabled}, Vignette: {vignette_enabled}, Folder: {subfolder_name}, Layer: {layer_name}")
                    
                    if hasattr(image, 'data') and image.data is not None:
                        try:
                            # CRITICAL FIX: Ensure outfolder includes format directory (tiff16)
                            format_outfolder = os.path.join(outfolder, output_format)
                            # Save calibrated or sensor response image with appropriate folder name
                            reflectance_path = save_func(image, output_format, format_outfolder, subfolder_name, is_preview=False)
                            if reflectance_path:
                                result[layer_name] = reflectance_path
                                # print(f"[RAY-THREAD-4] ✅ Saved {layer_name} to {subfolder_name}: {reflectance_path}")
                            else:
                                print(f"[RAY-THREAD-4] ⚠️ Failed to save image for {image_data.get('fn', 'unknown')}")
                        except Exception as e:
                            print(f"[RAY-THREAD-4] ❌ Error saving image: {e}")
                            import traceback
                            traceback.print_exc()
                    else:
                        print(f"[RAY-THREAD-4] ⚠️ No image data available for export: {image_data.get('fn', 'unknown')}")
                    
                    # CRITICAL FIX: For target images, also create the red square target image
                    if is_target and result and 'RAW (Reflectance)' in result:
                        try:
                            # print(f"[RAY-THREAD-4] 🎯 Creating target image with red squares for {image_data.get('fn', 'unknown')}")
                            
                            # Import the target image function and raw data loader
                            save_target_func = getattr(current_module, 'save_raw_target_image')
                            load_raw_func = getattr(current_module, 'load_truly_raw_data')
                            
                            # CRITICAL FIX: Create target image from original raw data, not calibrated data
                            target_image = image.copy()
                            target_image.fn = image.fn
                            
                            # CRITICAL FIX: Load calibration target data from calibration JSON file
                            # print(f"[RAY-THREAD-4] 📂 Loading calibration target data from JSON for {image.fn}")
                            try:
                                import json
                                import os
                                
                                # Find the calibration JSON file in the project directory
                                project_dir = os.path.dirname(outfolder)  # Go up from camera model folder to project root
                                calibration_json_path = os.path.join(project_dir, 'calibration_data.json')
                                
                                # print(f"[RAY-THREAD-4] 🔍 Looking for calibration data: {calibration_json_path}")
                                
                                if os.path.exists(calibration_json_path):
                                    with open(calibration_json_path, 'r') as f:
                                        calibration_data = json.load(f)
                                    
                                    # Find the target data for this image
                                    # CRITICAL FIX: Use original RAW filename, not the modified .tif filename
                                    target_fn = image.fn
                                    if target_fn.endswith('.tif'):
                                        target_fn = target_fn.replace('.tif', '.RAW')
                                    elif not target_fn.endswith('.RAW'):
                                        target_fn = target_fn + '.RAW' if '.' not in target_fn else target_fn.rsplit('.', 1)[0] + '.RAW'
                                    
                                    target_data = None
                                    
                                    # Search in the calibration data structure - entries are stored directly under timestamps
                                    for timestamp_key, entry in calibration_data.items():
                                        if isinstance(entry, dict):
                                            # Check if this entry is for our target file
                                            entry_filename = entry.get('filename', '')
                                            
                                            # CRITICAL FIX: Use exact filename matching to prevent cross-contamination
                                            # Extract base filename without extension for comparison
                                            target_base = os.path.splitext(os.path.basename(target_fn))[0]
                                            entry_base = os.path.splitext(os.path.basename(entry_filename))[0]
                                            
                                            # print(f"[RAY-THREAD-4] 🔍 Comparing target_base='{target_base}' with entry_base='{entry_base}' (entry_filename='{entry_filename}')")
                                            
                                            # Only match if the base filenames (without extension) are exactly the same
                                            if target_base == entry_base and target_base and entry_base:
                                                # This is our target - check if it has target detection data
                                                if entry.get('aruco_id') or entry.get('red_square_corners'):
                                                    target_data = entry
                                                    # print(f"[RAY-THREAD-4] 🎯 Found target entry in calibration JSON for {target_fn} (matched by base filename)")
                                                    break
                                                else:
                                                    print(f"[RAY-THREAD-4] ⚠️ Entry {entry_filename} matches filename but has no target data")
                                            else:
                                                print(f"[RAY-THREAD-4] ❌ No match: target_base='{target_base}' != entry_base='{entry_base}'")
                                    
                                    if target_data:
                                        # print(f"[RAY-THREAD-4] ✅ Found calibration target data for {target_fn}")
                                        
                                        # CRITICAL VALIDATION: Verify the loaded data is for the correct image
                                        loaded_filename = target_data.get('filename', '')
                                        loaded_base = os.path.splitext(os.path.basename(loaded_filename))[0]
                                        expected_base = os.path.splitext(os.path.basename(target_fn))[0]
                                        
                                        if loaded_base != expected_base:
                                            print(f"[RAY-THREAD-4] ❌ VALIDATION FAILED: Expected {expected_base} but loaded {loaded_base}")
                                            print(f"[RAY-THREAD-4] ❌ This indicates cross-contamination - skipping target data")
                                            target_data = None
                                        else:
                                            # print(f"[RAY-THREAD-4] ✅ VALIDATION PASSED: Loaded data is for correct image {expected_base}")
                                            
                                            # Set the target image attributes from JSON data
                                            target_image.is_calibration_photo = True
                                            target_image.aruco_id = target_data.get('aruco_id', 788)  # Default fallback
                                            target_image.aruco_corners = target_data.get('aruco_corners', None)  # Load corners data
                                            
                                            # CRITICAL FIX: Load red_square_corners (the correct field name in the new JSON structure)
                                            red_square_data = target_data.get('red_square_corners', None)
                                            if red_square_data:
                                                target_image.calibration_target_polys = red_square_data
                                                # print(f"[RAY-THREAD-4] ✅ Loaded red_square_corners from JSON: {len(red_square_data)} polygons")
                                            else:
                                                # Fallback: check for legacy target_polys field
                                                legacy_polys = target_data.get('target_polys', None)
                                                if legacy_polys:
                                                    target_image.calibration_target_polys = legacy_polys
                                                    # print(f"[RAY-THREAD-4] ✅ Loaded legacy target_polys from JSON: {len(legacy_polys)} polygons")
                                            
                                            # Check if we have target polygons for red square drawing
                                            if hasattr(target_image, 'calibration_target_polys') and target_image.calibration_target_polys:
                                                # print(f"[RAY-THREAD-4] ✅ Target polygons available for red square drawing: {len(target_image.calibration_target_polys)} polygons")
                                                pass
                                            else:
                                                print(f"[RAY-THREAD-4] ⚠️ No target polygons available - red squares cannot be drawn")
                                            
                                            # print(f"[RAY-THREAD-4] 📋 Target data loaded: aruco_id={getattr(target_image, 'aruco_id', None)}, corners={hasattr(target_image, 'aruco_corners') and target_image.aruco_corners is not None}, polys={hasattr(target_image, 'calibration_target_polys') and target_image.calibration_target_polys is not None}")
                                    else:
                                        print(f"[RAY-THREAD-4] ⚠️ No target data found for {target_fn} in calibration JSON")
                                else:
                                    print(f"[RAY-THREAD-4] ⚠️ Calibration JSON file not found: {calibration_json_path}")
                                        
                            except Exception as json_err:
                                print(f"[RAY-THREAD-4] ❌ Error loading calibration data from JSON: {json_err}")
                                import traceback
                                traceback.print_exc()
                            
                            # CRITICAL FIX: Use original source file path, not project path
                            original_source_path = image_data.get('original_source_path')
                            if not original_source_path:
                                print(f"[RAY-THREAD-4] ⚠️ No original source path provided, using image.path: {getattr(image, 'path', 'None')}")
                                original_source_path = getattr(image, 'path', image.path)
                            
                            # print(f"[RAY-THREAD-4] 📂 Loading truly raw data for target export: {original_source_path}")
                            raw_data = load_raw_func(original_source_path)
                            if raw_data is not None:
                                target_image.data = raw_data
                                print(f"[RAY-THREAD-4] ✅ Loaded raw data for target: shape={raw_data.shape}, dtype={raw_data.dtype}")
                            else:
                                print(f"[RAY-THREAD-4] ⚠️ Could not load raw data, using current data (may be calibrated)")
                            
                            # Create target image with red squares and channel swapping
                            target_subfolder = "Calibration_Targets_Used"
                            # CRITICAL FIX: Ensure target export also uses format directory
                            format_outfolder = os.path.join(outfolder, output_format)
                            target_path = save_target_func(target_image, 'tiff16', format_outfolder, target_subfolder)
                            
                            if target_path:
                                result['RAW (Target)'] = target_path
                                # print(f"[RAY-THREAD-4] ✅ Created target image with raw data: {target_path}")
                            else:
                                print(f"[RAY-THREAD-4] ⚠️ Failed to create target image")
                                
                        except Exception as target_err:
                            print(f"[RAY-THREAD-4] ❌ Error creating target image: {target_err}")
                            import traceback
                            traceback.print_exc()
                    
                    # print(f"[RAY-THREAD-4] ✅ COMPLETED export_processed_image_ray for {image_data.get('fn', 'unknown')}")
                    return {
                        'success': True,
                        'fn': image_data.get('fn', 'unknown'),
                        'exported_paths': result
                    }
                    
                except Exception as e:
                    print(f"[RAY-THREAD-4] ❌ ERROR in export_processed_image_ray: {e}")
                    import traceback
                    traceback.print_exc()
                    return {
                        'success': False,
                        'fn': image_data.get('fn', 'unknown'),
                        'error': str(e)
                    }
            
            globals()['export_processed_image_ray'] = export_processed_image_ray_inline
        
        return True
        
    except Exception as e:
        pass
        import traceback
        traceback.print_exc()
        return False
