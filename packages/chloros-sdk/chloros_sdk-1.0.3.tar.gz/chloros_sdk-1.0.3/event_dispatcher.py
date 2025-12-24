"""
Event Dispatcher for Server-Sent Events
Shared utility to avoid circular imports and duplicate backend initialization
"""

import time
import queue

def safe_flush():
    """Safely flush stdout if it exists"""
    import sys
    if sys.stdout is not None and hasattr(sys.stdout, 'flush'):
        try:
            sys.stdout.flush()
        except:
            pass

# Use a true global singleton that persists across all module imports
import builtins
if not hasattr(builtins, '_mapir_global_event_queue'):
    builtins._mapir_global_event_queue = queue.Queue()

def get_global_event_queue():
    """Get the true global singleton event queue instance across all threads and imports"""
    return builtins._mapir_global_event_queue

def dispatch_event(event_type, data):
    """
    Dispatch an event to the frontend via Server-Sent Events
    
    This is a shared utility used by both backend servers and the API module.
    Extracted to prevent duplicate backend initialization when api.py imports it.
    """
    try:
        # Always get the singleton queue to ensure thread safety
        queue_instance = get_global_event_queue()
        event_data = {
            'type': event_type,
            'data': data,
            'timestamp': time.time()
        }
        
        # Use non-blocking put to avoid blocking processing thread
        queue_instance.put(event_data, block=False)
        
        # Force flush stdout to ensure immediate output
        safe_flush()
    except queue.Full:
        # Queue full - silently drop event
        safe_flush()
    except Exception as e:
        # Error dispatching event - silently continue
        import traceback
        safe_flush()

def dispatch_ui_event(event_type, data):
    """Alias for dispatch_event for backwards compatibility"""
    dispatch_event(event_type, data)










