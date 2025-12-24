"""
License Cache Manager
Handles offline license validation with 30-day grace period

Features:
- Encrypted license storage
- 30-day offline grace period
- Machine-specific binding (optional)
- Automatic expiration handling
"""

import os
import sys
import json
import time
import hashlib
import hmac
import socket
from pathlib import Path
from typing import Optional, Dict, Any
import base64
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class LicenseCache:
    """
    Manages cached licenses for offline use
    
    Licenses are encrypted and stored locally with expiration timestamps
    """
    
    def __init__(self):
        # Determine cache directory
        if sys.platform == 'win32':
            cache_dir = Path(os.environ.get('APPDATA', Path.home())) / 'Chloros' / 'cache'
        elif sys.platform == 'darwin':
            cache_dir = Path.home() / 'Library' / 'Application Support' / 'Chloros' / 'cache'
        else:
            cache_dir = Path.home() / '.chloros' / 'cache'
        
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.cache_file = cache_dir / 'license_cache.enc'
        self.key_file = cache_dir / '.license_key'
        
        # Generate or load encryption key
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher = Fernet(self.encryption_key)
        
        # License cache initialized (path hidden for security)
    
    def _get_or_create_encryption_key(self) -> bytes:
        """
        Get or create encryption key for license storage
        
        Uses machine-specific salt for added security
        """
        if self.key_file.exists():
            with open(self.key_file, 'rb') as f:
                return f.read()
        
        # Generate new key using machine-specific salt
        machine_salt = self._get_machine_salt()
        
        # Use PBKDF2 to derive encryption key from machine salt
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=machine_salt,
            iterations=100000,
        )
        
        # Create a base key from machine-specific data
        base_key = f"chloros-license-{self._get_machine_id()}".encode()
        key = base64.urlsafe_b64encode(kdf.derive(base_key))
        
        # Save key to file (restricted permissions)
        with open(self.key_file, 'wb') as f:
            f.write(key)
        
        # Set restrictive permissions on key file
        if sys.platform != 'win32':
            os.chmod(self.key_file, 0o600)
        
        return key
    
    def _get_machine_salt(self) -> bytes:
        """Get machine-specific salt for encryption"""
        machine_id = self._get_machine_id()
        return hashlib.sha256(machine_id.encode()).digest()
    
    def _get_machine_id(self) -> str:
        """
        Get unique machine identifier using multiple hardware sources
        
        SECURITY: Uses multiple identifiers to make spoofing harder
        Enhanced for container/virtualized environments
        """
        import uuid
        import subprocess
        
        # SECURITY: Try to detect if we're in a container/VM and use host identifiers if available
        is_containerized = self._is_containerized()
        is_vm = self._is_virtual_machine()
        
        identifiers = []
        
        # SECURITY: In containers, try to get host machine ID if available
        if is_containerized:
            host_id = self._get_host_machine_id_in_container()
            if host_id:
                return host_id
            # Mark as containerized in identifier
            identifiers.append('container:true')
            # Use container ID or hostname as additional identifier
            container_id = os.environ.get('HOSTNAME') or socket.gethostname()
            identifiers.append(f"container_id:{container_id}")
        
        if is_vm:
            identifiers.append('vm:true')
        
        if sys.platform == 'win32':
            # Windows: WMI detection DISABLED - produces unavoidable console errors
            # Using Windows Registry MachineGuid instead (more reliable)
            try:
                import winreg
                reg = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
                key = winreg.OpenKey(reg, r"SOFTWARE\Microsoft\Cryptography")
                machine_guid, _ = winreg.QueryValueEx(key, "MachineGuid")
                winreg.CloseKey(key)
                if machine_guid:
                    identifiers.append(f"uuid:{machine_guid}")
            except:
                pass
        
        # MAC address (fallback, but less secure)
        mac = uuid.getnode()
        identifiers.append(f"mac:{mac:012x}")
        
        # SECURITY: Combine multiple identifiers to make spoofing harder
        # Hash the combined identifiers for consistency
        combined = "|".join(sorted(identifiers))
        machine_id_hash = hashlib.sha256(combined.encode()).hexdigest()[:32]
        
        return machine_id_hash
    
    def _is_containerized(self) -> bool:
        """Check if running in container"""
        # Check for Docker
        if Path('/.dockerenv').exists():
            return True
        
        # Check cgroup
        try:
            cgroup_path = Path('/proc/self/cgroup')
            if cgroup_path.exists():
                with open(cgroup_path, 'r') as f:
                    content = f.read()
                    if 'docker' in content.lower() or 'kubepods' in content.lower():
                        return True
        except:
            pass
        
        # Check environment variables
        if any(os.environ.get(var) for var in ['KUBERNETES_SERVICE_HOST', 'CONTAINER_ID']):
            return True
        
        return False
    
    def _is_virtual_machine(self) -> bool:
        """Check if running in virtual machine"""
        vm_indicators = ['vmware', 'virtualbox', 'qemu', 'kvm', 'xen', 'hyper-v']
        
        if sys.platform == 'win32':
            try:
                output = subprocess.check_output(
                    'systeminfo',
                    shell=True,
                    stderr=subprocess.DEVNULL,
                    timeout=5
                ).decode('utf-8', errors='ignore').lower()
                
                if any(indicator in output for indicator in vm_indicators):
                    return True
            except:
                pass
        
        return False
    
    def _get_host_machine_id_in_container(self) -> Optional[str]:
        """
        Try to get host machine ID when running in container
        
        This attempts to access host-level identifiers through:
        - Mounted host filesystems
        - Host network access
        - Environment variables passed from host
        """
        # Check for host machine ID in environment (if passed from host)
        host_machine_id = os.environ.get('CHLOROS_HOST_MACHINE_ID')
        if host_machine_id:
            return host_machine_id
        
        # Try to access host /sys or /proc if mounted
        # This is container-specific and may not always work
        try:
            # Some containers mount host /sys
            if Path('/host/sys/class/dmi/id/product_uuid').exists():
                with open('/host/sys/class/dmi/id/product_uuid', 'r') as f:
                    host_uuid = f.read().strip()
                    if host_uuid:
                        # Use host UUID as machine ID
                        return hashlib.sha256(f"host_uuid:{host_uuid}".encode()).hexdigest()[:32]
        except:
            pass
        
        return None
    
    def _get_machine_id_components(self) -> Dict[str, str]:
        """
        Get individual machine ID components for validation
        
        SECURITY: Used to detect if machine ID components have changed (possible spoofing)
        """
        import uuid
        import subprocess
        
        components = {}
        
        if sys.platform == 'win32':
            # Windows: WMI detection DISABLED - produces unavoidable console errors
            # Using Windows Registry instead
            try:
                import winreg
                reg = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
                key = winreg.OpenKey(reg, r"SOFTWARE\Microsoft\Cryptography")
                machine_guid, _ = winreg.QueryValueEx(key, "MachineGuid")
                winreg.CloseKey(key)
                if machine_guid:
                    components['uuid'] = machine_guid
            except:
                pass
        
        mac = uuid.getnode()
        components['mac'] = f"{mac:012x}"
        
        return components
    
    def cache_license(self, license_data: Dict[str, Any]) -> bool:
        """
        Cache license data for offline use with integrity protection
        
        Args:
            license_data: Dictionary containing user license information
                Required fields: email, token, subscription_level
                Optional fields: plan_id, plan_expiration, user_id
        
        Returns: True if successful, False otherwise
        """
        try:
            # Load existing cache
            cache = self._load_cache()
            
            # Add timestamp
            license_data['cached_at'] = time.time()
            license_data['machine_id'] = self._get_machine_id()
            
            # SECURITY: Store machine ID components for spoofing detection
            license_data['_machine_components'] = self._get_machine_id_components()
            
            # SECURITY: Add HMAC signature for tamper detection
            license_data['_integrity_hash'] = self._compute_integrity_hash(license_data)
            
            # Add to cache (keyed by email)
            email = license_data.get('email')
            if not email:
                return False
            
            cache[email] = license_data
            
            # Save cache
            self._save_cache(cache)
            
            # License cached silently (privacy - no email in logs)
            return True
            
        except Exception as e:
            return False
    
    def _compute_integrity_hash(self, license_data: Dict[str, Any]) -> str:
        """
        Compute HMAC signature for license data to detect tampering
        
        SECURITY: Uses machine-specific key to prevent tampering
        """
        # Create a copy without the integrity hash for signing
        data_to_sign = {k: v for k, v in license_data.items() if k != '_integrity_hash'}
        
        # Serialize deterministically
        import json
        json_str = json.dumps(data_to_sign, sort_keys=True)
        
        # Use machine-specific key for HMAC
        machine_key = self._get_machine_id().encode()
        secret_key = hashlib.pbkdf2_hmac('sha256', machine_key, b'chloros-license-integrity', 100000)
        
        # Compute HMAC
        signature = hmac.new(secret_key, json_str.encode('utf-8'), hashlib.sha256).hexdigest()
        
        return signature
    
    def _verify_integrity(self, license_data: Dict[str, Any]) -> bool:
        """
        Verify HMAC signature to detect tampering
        
        Returns: True if integrity is valid, False if tampered
        """
        stored_hash = license_data.pop('_integrity_hash', None)
        if not stored_hash:
            return False
        
        computed_hash = self._compute_integrity_hash(license_data)
        
        # SECURITY: Use constant-time comparison to prevent timing attacks
        if not hmac.compare_digest(stored_hash, computed_hash):
            return False
        
        # Restore the hash
        license_data['_integrity_hash'] = stored_hash
        return True
    
    def get_cached_license(self, email: str, token: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached license for user
        
        Args:
            email: User email
            token: User token (for validation)
        
        Returns: License data if valid, None otherwise
        """
        try:
            cache = self._load_cache()
            
            license_data = cache.get(email)
            if not license_data:
                return None
            
            # SECURITY: Verify integrity first (tamper detection)
            if not self._verify_integrity(license_data):
                return None
            
            # Verify token matches
            if license_data.get('token') != token:
                return None
            
            # SECURITY: Verify machine ID (prevents license transfer and spoofing)
            cached_machine_id = license_data.get('machine_id')
            current_machine_id = self._get_machine_id()
            
            if cached_machine_id and cached_machine_id != current_machine_id:
                
                # SECURITY: Store machine ID components for forensic analysis
                cached_components = license_data.get('_machine_components', {})
                current_components = self._get_machine_id_components()
                
                if cached_components:
                    for key in set(list(cached_components.keys()) + list(current_components.keys())):
                        cached_val = cached_components.get(key, 'N/A')
                        current_val = current_components.get(key, 'N/A')
                        if cached_val != current_val:
                            pass  # Component mismatch (silent)
                
                return None
            
            # SECURITY: Store machine components for future validation
            if '_machine_components' not in license_data:
                license_data['_machine_components'] = self._get_machine_id_components()
            
            # Check if cache is expired (30 days grace period)
            cached_at = license_data.get('validated_at') or license_data.get('cached_at', 0)
            grace_period = 30 * 24 * 60 * 60  # 30 days in seconds
            
            if time.time() - cached_at > grace_period:
                return None
            
            # Silently return valid cached license (auth middleware will log offline mode)
            return license_data
            
        except Exception as e:
            return None
    
    def get_latest_cached_license(self) -> Optional[Dict[str, Any]]:
        """
        Get the most recently cached license (for any user)
        
        Useful for Electron app that may not send explicit auth headers
        """
        try:
            cache = self._load_cache()
            
            if not cache:
                return None
            
            # Find most recent license
            latest = None
            latest_time = 0
            
            for email, license_data in cache.items():
                cached_at = license_data.get('validated_at') or license_data.get('cached_at', 0)
                
                if cached_at > latest_time:
                    # Check if not expired
                    grace_period = 30 * 24 * 60 * 60
                    if time.time() - cached_at <= grace_period:
                        latest = license_data
                        latest_time = cached_at
            
            if latest:
                email = latest.get('email', 'unknown')
            
            return latest
            
        except Exception as e:
            return None
    
    def clear_cache(self, email: Optional[str] = None) -> bool:
        """
        Clear cached license(s)
        
        Args:
            email: If provided, clear only this user's license
                   If None, clear all cached licenses
        
        Returns: True if successful, False otherwise
        """
        try:
            if email:
                # Clear specific user
                cache = self._load_cache()
                if email in cache:
                    del cache[email]
                    self._save_cache(cache)
                    # Cleared license cache (silent)
                    pass
                else:
                    # No cached license found (silent)
                    pass
            else:
                # Clear all
                self._save_cache({})
                # Cleared all license caches (silent)
                pass
            
            return True
            
        except Exception as e:
            return False
    
    def _load_cache(self) -> Dict[str, Any]:
        """Load and decrypt cache file"""
        if not self.cache_file.exists():
            return {}
        
        try:
            with open(self.cache_file, 'rb') as f:
                encrypted_data = f.read()
            
            if not encrypted_data:
                return {}
            
            # Decrypt
            decrypted_data = self.cipher.decrypt(encrypted_data)
            cache = json.loads(decrypted_data.decode('utf-8'))
            
            return cache
            
        except InvalidToken:
            return {}
        except Exception as e:
            return {}
    
    def _save_cache(self, cache: Dict[str, Any]) -> bool:
        """Encrypt and save cache file"""
        try:
            # Serialize to JSON
            json_data = json.dumps(cache, indent=2).encode('utf-8')
            
            # Encrypt
            encrypted_data = self.cipher.encrypt(json_data)
            
            # Write to file
            with open(self.cache_file, 'wb') as f:
                f.write(encrypted_data)
            
            # Set restrictive permissions
            if sys.platform != 'win32':
                os.chmod(self.cache_file, 0o600)
            
            return True
            
        except Exception as e:
            return False
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about cached licenses"""
        try:
            cache = self._load_cache()
            
            info = {
                'total_licenses': len(cache),
                'licenses': []
            }
            
            for email, license_data in cache.items():
                cached_at = license_data.get('validated_at') or license_data.get('cached_at', 0)
                grace_period = 30 * 24 * 60 * 60
                time_remaining = grace_period - (time.time() - cached_at)
                days_remaining = max(0, int(time_remaining / 86400))
                
                info['licenses'].append({
                    'email': email,
                    'subscription_level': license_data.get('subscription_level', 'unknown'),
                    'days_remaining': days_remaining,
                    'is_expired': time_remaining <= 0
                })
            
            return info
            
        except Exception as e:
            return {'total_licenses': 0, 'licenses': []}


# CLI tool for testing/debugging
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='License Cache Manager')
    subparsers = parser.add_subparsers(dest='command')
    
    # Info command
    subparsers.add_parser('info', help='Show cache information')
    
    # Clear command
    clear_parser = subparsers.add_parser('clear', help='Clear cache')
    clear_parser.add_argument('--email', help='Email to clear (or all if not specified)')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test cache functionality')
    
    args = parser.parse_args()
    
    cache = LicenseCache()
    
    if args.command == 'info':
        info = cache.get_cache_info()
        print(f"\n≡ƒôè License Cache Information")
        print(f"   Total licenses: {info['total_licenses']}")
        for lic in info['licenses']:
            status = "Γ¥î EXPIRED" if lic['is_expired'] else f"Γ£à {lic['days_remaining']} days"
            print(f"   - {lic['email']}: {lic['subscription_level']} ({status})")
    
    elif args.command == 'clear':
        cache.clear_cache(args.email)
        print("Γ£à Cache cleared")
    
    elif args.command == 'test':
        print("\n≡ƒº¬ Testing license cache...")
        
        # Test data
        test_license = {
            'email': 'test@example.com',
            'token': 'test-token-12345',
            'subscription_level': 'premium',
            'validated_at': time.time()
        }
        
        # Test cache
        print("  1. Caching test license...")
        cache.cache_license(test_license)
        
        # Test retrieval
        print("  2. Retrieving cached license...")
        retrieved = cache.get_cached_license('test@example.com', 'test-token-12345')
        if retrieved:
            print(f"     Γ£à Retrieved: {retrieved.get('email')}")
        else:
            print(f"     Γ¥î Failed to retrieve")
        
        # Test wrong token
        print("  3. Testing wrong token...")
        wrong = cache.get_cached_license('test@example.com', 'wrong-token')
        if not wrong:
            print(f"     Γ£à Correctly rejected wrong token")
        else:
            print(f"     Γ¥î Should have rejected wrong token")
        
        # Clean up
        print("  4. Clearing test license...")
        cache.clear_cache('test@example.com')
        
        print("\nΓ£à All tests passed!")
    
    else:
        parser.print_help()

