"""
Chloros Authentication Middleware
Provides secure authentication with offline grace period support

Features:
- Token-based authentication
- Server-side validation against MAPIR API
- 30-day offline grace period
- Hardware-locked licensing (optional)
- Rate limiting support
- Works with both Electron GUI and CLI/API
"""

import os
import sys
import json
import time
import threading
import hashlib
import hmac
from datetime import datetime, timedelta
from pathlib import Path
from functools import wraps
from flask import request, jsonify
import requests
from typing import Optional, Dict, Any, Tuple

# Import license cache manager
from license_cache import LicenseCache


class AuthenticationError(Exception):
    """Custom exception for authentication failures"""
    pass


class AuthMiddleware:
    """
    Authentication middleware for Chloros backend
    
    Validates user tokens against MAPIR server and manages offline licenses
    """
    
    def __init__(self, mapir_api_url: str = "https://dynamic.cloud.mapir.camera"):
        self.mapir_api_url = mapir_api_url
        self.license_cache = LicenseCache()
        
        # Rate limiting tracking
        self.request_counts = {}  # {user_email: [(timestamp, count)]}
        
        # SECURITY: Instance protection and heartbeat
        self.instance_id = None
        self.heartbeat_thread = None
        self.heartbeat_interval = 60  # 60 seconds
        self.heartbeat_active = False
        self.concurrent_check_thread = None
        self.concurrent_check_interval = 300  # 5 minutes
        self.concurrent_check_active = False
        self.current_user_token = None
        self.current_user_email = None
        
        # PERFORMANCE: Validation result caching (5 minute TTL)
        # Format: {email: (timestamp, is_valid, validation_data)}
        self._validation_cache = {}
        self._validation_cache_ttl = 300  # 5 minutes
        
        # Get instance protection if available
        try:
            from instance_protection import get_instance_protection
            instance_protection = get_instance_protection()
            self.instance_id = instance_protection.instance_id
            # Instance ID retrieved silently (privacy)
        except Exception as e:
            # Generate fallback instance ID
            import uuid
            self.instance_id = hashlib.sha256(f"{os.getpid()}:{time.time()}:{uuid.uuid4()}".encode()).hexdigest()[:32]
        
        # Authentication middleware initialized (API URL hidden for security)
    
    def validate_token_online(self, token: str, email: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate token against MAPIR server with device registration
        
        Returns: (is_valid, user_data)
        """
        # PERFORMANCE: Check cache first (5 minute TTL)
        # SECURITY: Cache has short TTL to ensure regular server validation
        current_time = time.time()
        if email in self._validation_cache:
            cached_time, cached_valid, cached_data = self._validation_cache[email]
            age = current_time - cached_time
            
            # SECURITY: Verify device ID hasn't changed (prevents license cloning)
            current_machine_id = self.license_cache._get_machine_id()
            cached_device_id = cached_data.get('device_id', '')
            current_device_id = hashlib.sha256(current_machine_id.encode()).hexdigest()
            
            if current_device_id != cached_device_id:
                del self._validation_cache[email]
            elif age < self._validation_cache_ttl:
                # Using cached validation
                return cached_valid, cached_data
            else:
                # Cache expired, remove it
                del self._validation_cache[email]
        
        # Get machine ID for device registration
        machine_id = self.license_cache._get_machine_id()
        device_id = hashlib.sha256(machine_id.encode()).hexdigest()
        
        try:
            # CRITICAL: First check device count to see if limit is reached
            # This prevents auto-registration when limit is exceeded
            # EXCEPTION: Iron plan users (plan_id=0) are allowed to login even when limit is reached
            try:
                devices_response = requests.get(
                    f"{self.mapir_api_url}/api/devices",
                    headers={
                        'Authorization': f'Bearer {token}',
                        'Content-Type': 'application/json',
                        'User-Agent': 'Chloros-Backend/1.0'
                    },
                    timeout=10
                )
                
                if devices_response.status_code == 200:
                    devices_data = devices_response.json()
                    device_limit = devices_data.get('device_limit')
                    devices_registered = devices_data.get('devices_registered')
                    devices_list = devices_data.get('devices', [])
                    plan_id = devices_data.get('plan_id')  # Get plan_id to check if Iron user
                    
                    # Device count checked silently
                    
                    # Check if this device_id is already in the list
                    current_device_registered = any(
                        dev.get('device_id') == device_id for dev in devices_list
                    )
                    
                    # Check if this is an Iron plan user (plan_id = 0 or '0')
                    is_iron_plan = plan_id in [0, '0', 'standard']
                    
                    # CRITICAL: If limit is exceeded, reject ALL logins (even for registered devices)
                    # User must remove a device to get back under the limit
                    # EXCEPTION: Iron plan users are allowed to login (they use Chloros, not Chloros+)
                    if device_limit is not None and devices_registered is not None and not is_iron_plan:
                        if devices_registered > device_limit:
                            manage_url = devices_data.get('manage_url', 'https://dynamic.cloud.mapir.camera')
                            return False, {
                                'error': 'Device limit reached',
                                'error_code': 'DEVICE_LIMIT_EXCEEDED',
                                'warning_message': 'Device limit reached.',
                                'manage_url': manage_url,
                                'show_device_warning': True
                            }
                        elif devices_registered >= device_limit and not current_device_registered:
                            manage_url = devices_data.get('manage_url', 'https://dynamic.cloud.mapir.camera')
                            return False, {
                                'error': 'Device limit reached',
                                'error_code': 'DEVICE_LIMIT_EXCEEDED',
                                'warning_message': 'Device limit reached.',
                                'manage_url': manage_url,
                                'show_device_warning': True
                            }
                    elif is_iron_plan and device_limit is not None and devices_registered is not None:
                        # Iron plan users can login even with device limit reached
                        # They will use Chloros (not Chloros+)
                        if devices_registered >= device_limit:
                            pass  # Iron plan users allowed despite limit
            except requests.exceptions.Timeout:
                # Network timeout - allow offline validation fallback
                # Continue to device validation endpoint, it will handle offline fallback
                pass
            except requests.exceptions.ConnectionError:
                # Network error - allow offline validation fallback
                # Continue to device validation endpoint, it will handle offline fallback
                pass
            except Exception as devices_error:
                # Log unexpected errors but continue with validation
                # Continue to device validation endpoint, it will handle the validation
                pass
            
            # Try device validation endpoint first (includes token validation)
            validate_url = f"{self.mapir_api_url}/api/devices/validate"
            # Device validation (silent in production)
            response = requests.post(
                validate_url,
                json={
                    'device_id': device_id,
                },
                headers={
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json',
                    'User-Agent': 'Chloros-Backend/1.0'
                },
                timeout=10  # 10 second timeout
            )
            # Validation response received (silent in production)
            
            if response.status_code == 200:
                data = response.json()
                
                # CRITICAL: Check for device limit error even if valid is true
                # The server might return valid=true with auto_registered=true even when limit exceeded
                error_code = data.get('error_code')
                if error_code == 'DEVICE_LIMIT_EXCEEDED':
                    plan_id = data.get('plan_id')  # Get plan_id to check if Iron user
                    is_iron_plan = plan_id in [0, '0', 'standard']
                    
                    # EXCEPTION: Iron plan users can login even with device limit exceeded
                    if not is_iron_plan:
                        manage_url = data.get('manage_url', 'https://dynamic.cloud.mapir.camera')
                        warning_message = f"Device limit reached."
                        
                        return False, {
                            'error': data.get('error', 'Device limit reached'),
                            'error_code': 'DEVICE_LIMIT_EXCEEDED',
                            'warning_message': warning_message,
                            'manage_url': manage_url,
                            'show_device_warning': True
                        }
                    else:
                        # Iron plan users - continue with validation instead of rejecting
                        pass
                
                if data.get('valid'):
                    # Check if device was auto-registered when limit might be exceeded
                    auto_registered = data.get('auto_registered', False)
                    device_limit = data.get('device_limit')
                    devices_registered = data.get('devices_registered')
                    plan_id = data.get('plan_id')  # Get plan_id to check if Iron user
                    
                    # Check if this is an Iron plan user (plan_id = 0 or '0')
                    is_iron_plan = plan_id in [0, '0', 'standard']
                    
                    # Log device status for monitoring (silently)
                    if device_limit is not None and devices_registered is not None:
                        # Device count checked silently
                        
                        # Safety check: Only reject if device count EXCEEDS limit (not equals)
                        # If server returned valid=True, we trust its decision
                        # This check is only for detecting server-side bugs
                        # EXCEPTION: Iron plan users are allowed to login even with limit exceeded
                        if devices_registered > device_limit and not is_iron_plan:
                            manage_url = data.get('manage_url', 'https://dynamic.cloud.mapir.camera')
                            return False, {
                                'error': 'Device limit reached',
                                'error_code': 'DEVICE_LIMIT_EXCEEDED',
                                'warning_message': 'Device limit reached.',
                                'manage_url': manage_url,
                                'show_device_warning': True
                            }
                        elif devices_registered > device_limit and is_iron_plan:
                            # Iron plan users can login even with device limit exceeded
                            pass
                    
                    user_data = {
                        'email': email,
                        'token': token,
                        'device_id': device_id,
                        'device_registered': True,
                        'auto_registered': auto_registered,
                        'validated_at': time.time(),
                        'instance_id': self.instance_id,  # SECURITY: Track instance ID
                        'subscription_level': data.get('subscription_level', 'standard'),
                        'plan_id': data.get('plan_id'),
                        'plan_expiration': data.get('plan_expiration'),  # Cache for offline display
                        'allow_multiple_instances': data.get('allow_multiple_instances', False)  # Server-side flag
                    }
                    
                    # SECURITY: Check if subscription allows multiple instances
                    subscription_level = user_data.get('subscription_level', 'standard')
                    allow_multiple = user_data.get('allow_multiple_instances', False)
                    
                    # Enterprise/Cloud subscriptions typically allow multiple instances
                    cloud_subscriptions = ['enterprise', 'cloud', 'robotics', 'fleet']
                    if subscription_level.lower() in cloud_subscriptions or allow_multiple:
                        # Enable cloud mode for this session
                        try:
                            from instance_protection import get_instance_protection
                            instance_protection = get_instance_protection()
                            instance_protection.set_cloud_mode(
                                True,
                                f"{subscription_level} subscription allows multiple instances"
                            )
                        except Exception:
                            pass
                    
                    # Cache the validated license for offline use
                    self.license_cache.cache_license(user_data)
                    
                    # SECURITY: Start heartbeat for concurrent instance detection
                    self.current_user_token = token
                    self.current_user_email = email
                    self._start_heartbeat()
                    
                    # SECURITY: Check for concurrent instances (immediate check)
                    # In cloud mode, this still runs but doesn't block
                    self._check_concurrent_instances()
                    
                    # SECURITY: Start periodic concurrent instance checks
                    self._start_periodic_concurrent_checks()
                    
                    # PERFORMANCE: Cache successful validation for 5 minutes
                    self._validation_cache[email] = (time.time(), True, user_data)
                    
                    # User authenticated (print handled by api.py)
                    return True, user_data
                else:
                    # Device not registered or limit exceeded
                    error_code = data.get('error_code')
                    plan_id = data.get('plan_id')  # Get plan_id to check if Iron user
                    is_iron_plan = plan_id in [0, '0', 'standard']
                    
                    if error_code == 'DEVICE_LIMIT_EXCEEDED':
                        # EXCEPTION: Iron plan users can login even with device limit exceeded
                        if is_iron_plan:
                            # Continue to allow login by treating as valid
                            # Create user_data for Iron user
                            user_data = {
                                'email': email,
                                'token': token,
                                'device_id': device_id,
                                'device_registered': True,
                                'auto_registered': False,
                                'validated_at': time.time(),
                                'instance_id': self.instance_id,
                                'subscription_level': 'standard',  # Iron plan = standard
                                'plan_id': plan_id,
                                'plan_expiration': data.get('plan_expiration'),
                                'allow_multiple_instances': False
                            }
                            
                            # Cache the validated license for offline use
                            self.license_cache.cache_license(user_data)
                            
                            # Start heartbeat and concurrent checks
                            self.current_user_token = token
                            self.current_user_email = email
                            self._start_heartbeat()
                            self._check_concurrent_instances()
                            self._start_periodic_concurrent_checks()
                            
                            # Cache successful validation
                            self._validation_cache[email] = (time.time(), True, user_data)
                            
                            return True, user_data
                        
                        # For non-Iron users, show warning as before
                        manage_url = data.get('manage_url', 'https://dynamic.cloud.mapir.camera')
                        warning_message = f"Device limit reached."
                        
                        # Return error with warning for GUI to display
                        return False, {
                            'error': data.get('error'),
                            'error_code': 'DEVICE_LIMIT_EXCEEDED',
                            'warning_message': warning_message,
                            'manage_url': manage_url,
                            'show_device_warning': True
                        }
                    elif error_code == 'NO_CHLOROS_PLUS_ACCESS':
                        return False, {
                            'error': 'Chloros+ requires a paid subscription plan',
                            'error_code': 'NO_CHLOROS_PLUS_ACCESS'
                        }
                    
                    return False, data
            elif response.status_code == 403:
                # Device limit or access denied
                data = response.json()
                error_code = data.get('error_code')
                
                if error_code == 'DEVICE_LIMIT_EXCEEDED':
                    plan_id = data.get('plan_id')  # Get plan_id to check if Iron user
                    is_iron_plan = plan_id in [0, '0', 'standard']
                    
                    # EXCEPTION: Iron plan users can login even with device limit exceeded
                    if is_iron_plan:
                        # Create user_data for Iron user
                        user_data = {
                            'email': email,
                            'token': token,
                            'device_id': device_id,
                            'device_registered': True,
                            'auto_registered': False,
                            'validated_at': time.time(),
                            'instance_id': self.instance_id,
                            'subscription_level': 'standard',  # Iron plan = standard
                            'plan_id': plan_id,
                            'plan_expiration': data.get('plan_expiration'),
                            'allow_multiple_instances': False
                        }
                        
                        # Cache the validated license for offline use
                        self.license_cache.cache_license(user_data)
                        
                        # Start heartbeat and concurrent checks
                        self.current_user_token = token
                        self.current_user_email = email
                        self._start_heartbeat()
                        self._check_concurrent_instances()
                        self._start_periodic_concurrent_checks()
                        
                        # Cache successful validation
                        self._validation_cache[email] = (time.time(), True, user_data)
                        
                        return True, user_data
                    
                    # For non-Iron users, show warning as before
                    manage_url = data.get('manage_url', 'https://dynamic.cloud.mapir.camera')
                    warning_message = f"Device limit reached."
                    
                    return False, {
                        'error': data.get('error'),
                        'error_code': 'DEVICE_LIMIT_EXCEEDED',
                        'warning_message': warning_message,
                        'manage_url': manage_url,
                        'show_device_warning': True
                    }
                
                return False, data
            elif response.status_code == 401:
                # Unauthorized - invalid token or user deleted from database
                # Clear any cached license for this user
                self.license_cache.clear_cache(email)
                return False, {
                    'error': 'Invalid or expired token. Please login again.',
                    'error_code': 'INVALID_TOKEN',
                    'logout_required': True
                }
            elif response.status_code == 404:
                # Not found - user deleted from database
                # Clear any cached license for this user
                self.license_cache.clear_cache(email)
                return False, {
                    'error': 'User not found. Please login again.',
                    'error_code': 'USER_NOT_FOUND',
                    'logout_required': True
                }
            elif response.status_code >= 500:
                # SECURITY: Server error during device validation
                # Check if it's actually a user not found error (some APIs return 500 instead of 401/404)
                try:
                    data = response.json()
                    error_msg = data.get('error', '').lower() if isinstance(data.get('error'), str) else ''
                    message = data.get('message', '').lower() if isinstance(data.get('message'), str) else ''
                    
                    # Log the error for debugging
                    
                    # Check if error indicates user not found/deleted
                    user_not_found_phrases = [
                        'user not found', 
                        'user does not exist', 
                        'invalid user', 
                        'no user found',
                        'user was not found',
                        'could not find user',
                        'user is not found',
                        'no such user'
                    ]
                    
                    if any(phrase in error_msg for phrase in user_not_found_phrases) or \
                       any(phrase in message for phrase in user_not_found_phrases):
                        self.license_cache.clear_cache(email)
                        return False, {
                            'error': 'User not found. Please login again.',
                            'error_code': 'USER_NOT_FOUND',
                            'logout_required': True
                        }
                    
                    # STRICTER APPROACH: Check if we have a very recent cached license
                    # If the last validation was recent (< 1 hour), this is likely a genuine server issue
                    # If not, require re-authentication to be safe
                    cached_license = self.license_cache.get_cached_license(email, token)
                    if cached_license:
                        last_validated = cached_license.get('validated_at', 0)
                        time_since_last_validation = time.time() - last_validated
                        
                        if time_since_last_validation > 3600:  # More than 1 hour
                            self.license_cache.clear_cache(email)
                            return False, {
                                'error': 'Authentication required. Please login again.',
                                'error_code': 'STALE_CACHE_SERVER_ERROR',
                                'logout_required': True
                            }
                    else:
                        # No cached license - require re-authentication on server error
                        return False, {
                            'error': 'Authentication required. Please login again.',
                            'error_code': 'NO_CACHE_SERVER_ERROR',
                            'logout_required': True
                        }
                except Exception as e:
                    pass
                
                # Only reach here if we have a recent cached license (< 1 hour)
                # This is likely a temporary server issue, allow offline mode
                return self._validate_offline(token, email)
            else:
                # Other unexpected client error (4xx)
                return False, {
                    'error': 'Authentication failed. Please login again.',
                    'error_code': 'AUTH_FAILED',
                    'logout_required': True
                }
            
        except requests.exceptions.Timeout:
            # Network timeout - allow offline validation for already-registered devices
            return self._validate_offline(token, email)
        except requests.exceptions.ConnectionError:
            # Network error - allow offline validation for already-registered devices
            return self._validate_offline(token, email)
        except Exception as e:
            # SECURITY: For unexpected errors during device validation, fail securely
            # This prevents bypassing device limits by causing errors
            return False, {
                'error': 'Device validation failed - unexpected error',
                'error_code': 'DEVICE_VALIDATION_ERROR',
                'warning_message': 'Device limit reached.',
                'show_device_warning': True
            }
    
    def _validate_offline(self, token: str, email: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate token using cached license data (offline mode)
        
        SECURITY: Offline mode has restrictions:
        - Allows 30-day grace period from last online validation
        - Device registration requires online validation (cannot register new devices offline)
        - Only allows use of already-registered devices
        """
        cached_license = self.license_cache.get_cached_license(email, token)
        
        if not cached_license:
            return False, {
                'error': 'No cached license available',
                'error_code': 'NO_CACHED_LICENSE'
            }
        
        # SECURITY: Check if device was previously registered
        # If device_registered is False or missing, this is a new device registration attempt
        # New device registrations MUST be done online to enforce device limits
        device_registered = cached_license.get('device_registered', False)
        if not device_registered:
            return False, {
                'error': 'Device registration requires online validation',
                'error_code': 'OFFLINE_DEVICE_REGISTRATION_DENIED',
                'warning_message': 'Device limit reached.'
            }
        
        # Check if cache is still valid (30-day grace period)
        last_validated = cached_license.get('validated_at', 0)
        grace_period_seconds = 30 * 24 * 60 * 60  # 30 days
        
        if time.time() - last_validated > grace_period_seconds:
            return False, {
                'error': 'Cached license expired',
                'error_code': 'CACHED_LICENSE_EXPIRED'
            }
        
        days_remaining = int((grace_period_seconds - (time.time() - last_validated)) / 86400)
        # Offline validation message
        
        return True, cached_license
    
    def authenticate_request(self, token: Optional[str] = None, email: Optional[str] = None) -> Tuple[bool, Dict[str, Any], str]:
        """
        Authenticate a request using token and email
        
        Returns: (is_authenticated, user_data, error_message)
        """
        if not token or not email:
            return False, {}, "Missing authentication credentials"
        
        try:
            # Try online validation first
            is_valid, user_data = self.validate_token_online(token, email)
            
            if is_valid:
                # Check rate limits
                if not self._check_rate_limit(email):
                    return False, {}, "Rate limit exceeded. Please try again later."
                
                return True, user_data, ""
            
            return False, {}, "Invalid or expired token. Please login again."
            
        except Exception as e:
            return False, {}, f"Authentication error: {str(e)}"
    
    def _start_heartbeat(self):
        """Start heartbeat thread to detect concurrent instances"""
        if self.heartbeat_active:
            return
        
        if not self.current_user_token or not self.current_user_email:
            return
        
        self.heartbeat_active = True
        
        def heartbeat_loop():
            while self.heartbeat_active:
                try:
                    self._send_heartbeat()
                    time.sleep(self.heartbeat_interval)
                except Exception as e:
                    time.sleep(self.heartbeat_interval)
        
        self.heartbeat_thread = threading.Thread(target=heartbeat_loop, daemon=True)
        self.heartbeat_thread.start()
    
    def _stop_heartbeat(self):
        """Stop heartbeat thread"""
        self.heartbeat_active = False
        if self.heartbeat_thread:
            self.heartbeat_thread.join(timeout=2)
        
        # SECURITY: Clear validation cache on logout
        if self.current_user_email and self.current_user_email in self._validation_cache:
            del self._validation_cache[self.current_user_email]
    
    def _start_periodic_concurrent_checks(self):
        """Start periodic concurrent instance detection"""
        if self.concurrent_check_active:
            return
        
        self.concurrent_check_active = True
        
        def check_loop():
            while self.concurrent_check_active:
                try:
                    self._check_concurrent_instances()
                    time.sleep(self.concurrent_check_interval)
                except Exception as e:
                    time.sleep(self.concurrent_check_interval)
        
        self.concurrent_check_thread = threading.Thread(target=check_loop, daemon=True)
        self.concurrent_check_thread.start()
    
    def _stop_periodic_concurrent_checks(self):
        """Stop periodic concurrent instance checks"""
        self.concurrent_check_active = False
        if self.concurrent_check_thread:
            self.concurrent_check_thread.join(timeout=2)
    
    def _send_heartbeat(self):
        """Send heartbeat to server with instance ID"""
        if not self.current_user_token or not self.current_user_email:
            return
        
        try:
            import hashlib
            machine_id = self.license_cache._get_machine_id()
            device_id = hashlib.sha256(machine_id.encode()).hexdigest()
            
            # Send heartbeat to server
            response = requests.post(
                f"{self.mapir_api_url}/api/heartbeat",
                json={
                    'token': self.current_user_token,
                    'email': self.current_user_email,
                    'device_id': device_id,
                    'instance_id': self.instance_id,
                    'timestamp': time.time()
                },
                headers={
                    'Authorization': f'Bearer {self.current_user_token}',
                    'Content-Type': 'application/json',
                    'User-Agent': 'Chloros-Backend/1.0'
                },
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                # Check if server detected concurrent instances
                concurrent_instances = data.get('concurrent_instances', 0)
                if concurrent_instances > 1:
                    # Server can reject or take action
                    if data.get('action') == 'reject':
                        self._stop_heartbeat()
                        # Could trigger logout here
                        pass
        except requests.exceptions.RequestException:
            # Network error - continue heartbeat silently
            pass
        except Exception as e:
            pass
    
    def _check_concurrent_instances(self):
        """Check for concurrent instances on this machine"""
        try:
            from instance_protection import get_instance_protection
            instance_protection = get_instance_protection()
            has_concurrent, count, pids = instance_protection.detect_concurrent_instances()
            
            if has_concurrent:
                if not instance_protection.cloud_mode:
                    pass  # Warning logged (silent in production)
                
                # SECURITY: Report to server (even in cloud mode for monitoring)
                try:
                    import hashlib
                    machine_id = self.license_cache._get_machine_id()
                    device_id = hashlib.sha256(machine_id.encode()).hexdigest()
                    
                    requests.post(
                        f"{self.mapir_api_url}/api/security-event",
                        json={
                            'event_type': 'CONCURRENT_INSTANCE_DETECTED',
                            'device_id': device_id,
                            'instance_id': self.instance_id,
                            'concurrent_count': count,
                            'concurrent_pids': pids,
                            'cloud_mode': instance_protection.cloud_mode,
                            'timestamp': time.time()
                        },
                        headers={
                            'Authorization': f'Bearer {self.current_user_token}',
                            'Content-Type': 'application/json',
                            'User-Agent': 'Chloros-Backend/1.0'
                        },
                        timeout=5
                    )
                except Exception:
                    pass  # Don't fail if reporting fails
        except Exception as e:
            pass
    
    def _check_rate_limit(self, email: str, max_requests: int = 100, time_window: int = 3600) -> bool:
        """
        Check if user has exceeded rate limits
        
        Args:
            email: User email
            max_requests: Maximum requests allowed in time window
            time_window: Time window in seconds (default: 1 hour)
        
        Returns: True if within limits, False if exceeded
        """
        current_time = time.time()
        
        # Initialize tracking for user if not exists
        if email not in self.request_counts:
            self.request_counts[email] = []
        
        # Clean up old entries outside time window
        self.request_counts[email] = [
            (ts, count) for ts, count in self.request_counts[email]
            if current_time - ts < time_window
        ]
        
        # Count requests in current time window
        total_requests = sum(count for ts, count in self.request_counts[email])
        
        if total_requests >= max_requests:
            return False
        
        # Add current request
        self.request_counts[email].append((current_time, 1))
        return True
    
    def require_auth(self, f):
        """
        Decorator to require authentication for Flask routes
        
        Usage:
            @app.route('/api/process')
            @auth_middleware.require_auth
            def process():
                # Access user data via request.user_data
                user = request.user_data
                ...
        """
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Extract authentication from headers or request body
            auth_header = request.headers.get('Authorization')
            email = request.headers.get('X-User-Email')
            
            # Fallback: Check request body
            if not auth_header or not email:
                try:
                    data = request.get_json()
                    if data:
                        auth_header = data.get('auth_token')
                        email = data.get('user_email')
                except:
                    pass
            
            # SECURITY: Fallback for Electron compatibility (localhost only)
            if not auth_header or not email:
                # SECURITY: Only allow localhost fallback - prevent IP spoofing
                client_ip = request.remote_addr
                is_localhost = client_ip in ['127.0.0.1', '::1', 'localhost']
                
                # SECURITY: Verify X-Forwarded-For header isn't being spoofed
                forwarded_for = request.headers.get('X-Forwarded-For')
                if forwarded_for and not is_localhost:
                    # SECURITY: If X-Forwarded-For is set but IP isn't localhost, require explicit auth
                    is_localhost = False
                
                if is_localhost:
                    # SECURITY: Check if we have cached credentials for this session
                    cached = self.license_cache.get_latest_cached_license()
                    if cached:
                        # SECURITY: Verify cached license integrity
                        if self.license_cache._verify_integrity(cached):
                            auth_header = cached.get('token')
                            email = cached.get('email')
                        else:
                            auth_header = None
                            email = None
            
            if not auth_header or not email:
                return jsonify({
                    'success': False,
                    'error': 'Authentication required',
                    'error_code': 'AUTH_REQUIRED'
                }), 401
            
            # Remove "Bearer " prefix if present
            token = auth_header.replace('Bearer ', '') if auth_header.startswith('Bearer ') else auth_header
            
            # Authenticate the request
            is_authenticated, user_data, error_message = self.authenticate_request(token, email)
            
            if not is_authenticated:
                return jsonify({
                    'success': False,
                    'error': error_message,
                    'error_code': 'AUTH_FAILED'
                }), 401
            
            # Store user data in request context for use in route
            request.user_data = user_data
            
            
            # Call the actual route function
            return f(*args, **kwargs)
        
        return decorated_function
    
    def optional_auth(self, f):
        """
        Decorator for routes that support optional authentication
        
        If authenticated, user_data is available via request.user_data
        If not authenticated, request.user_data is None
        """
        @wraps(f)
        def decorated_function(*args, **kwargs):
            auth_header = request.headers.get('Authorization')
            email = request.headers.get('X-User-Email')
            
            if auth_header and email:
                token = auth_header.replace('Bearer ', '') if auth_header.startswith('Bearer ') else auth_header
                is_authenticated, user_data, _ = self.authenticate_request(token, email)
                
                if is_authenticated:
                    request.user_data = user_data
                else:
                    request.user_data = None
            else:
                request.user_data = None
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    def get_user_subscription_level(self) -> str:
        """
        Get current user's subscription level from request context
        
        Returns: 'premium', 'standard', or 'free'
        """
        if hasattr(request, 'user_data') and request.user_data:
            return request.user_data.get('subscription_level', 'standard')
        return 'free'
    
    def require_subscription_level(self, required_level: str = 'standard'):
        """
        Decorator to require specific subscription level
        
        Usage:
            @app.route('/api/premium-feature')
            @auth_middleware.require_auth
            @auth_middleware.require_subscription_level('premium')
            def premium_feature():
                ...
        """
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                user_data = getattr(request, 'user_data', None)
                
                if not user_data:
                    return jsonify({
                        'success': False,
                        'error': 'Authentication required',
                        'error_code': 'AUTH_REQUIRED'
                    }), 401
                
                user_level = user_data.get('subscription_level', 'free')
                
                # Define level hierarchy
                levels = {'free': 0, 'standard': 1, 'premium': 2}
                
                if levels.get(user_level, 0) < levels.get(required_level, 0):
                    return jsonify({
                        'success': False,
                        'error': f'This feature requires {required_level} subscription',
                        'error_code': 'SUBSCRIPTION_REQUIRED',
                        'required_level': required_level,
                        'current_level': user_level
                    }), 403
                
                return f(*args, **kwargs)
            
            return decorated_function
        
        return decorator


# Global singleton instance
_auth_middleware = None

def get_auth_middleware() -> AuthMiddleware:
    """Get the global authentication middleware instance"""
    global _auth_middleware
    if _auth_middleware is None:
        _auth_middleware = AuthMiddleware()
    return _auth_middleware

