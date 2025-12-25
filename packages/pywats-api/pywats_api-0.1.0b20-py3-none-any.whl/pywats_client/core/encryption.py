"""
Token encryption utilities for pyWATS Client.

Provides secure encryption/decryption of API tokens using machine-specific keys.
"""

import os
import hashlib
import base64
import subprocess
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging

logger = logging.getLogger(__name__)


def get_machine_id() -> str:
    """
    Get a machine-specific identifier.
    
    Uses platform-specific methods to get a unique machine ID.
    On Windows: Uses MachineGuid from registry
    On Linux: Uses /etc/machine-id
    On Mac: Uses IOPlatformUUID
    
    Returns:
        Machine-specific identifier string
    """
    try:
        if os.name == 'nt':  # Windows
            import winreg
            try:
                with winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"SOFTWARE\Microsoft\Cryptography",
                    0,
                    winreg.KEY_READ | winreg.KEY_WOW64_64KEY
                ) as key:
                    machine_guid = winreg.QueryValueEx(key, "MachineGuid")[0]
                    return machine_guid
            except Exception as e:
                logger.warning(f"Could not read MachineGuid: {e}")
                # Fallback to computername
                return os.environ.get('COMPUTERNAME', 'default-machine')
        
        elif os.path.exists('/etc/machine-id'):  # Linux
            with open('/etc/machine-id', 'r') as f:
                return f.read().strip()
        
        elif os.path.exists('/var/lib/dbus/machine-id'):  # Linux fallback
            with open('/var/lib/dbus/machine-id', 'r') as f:
                return f.read().strip()
        
        else:  # Mac or unknown
            import subprocess
            try:
                result = subprocess.run(
                    ['ioreg', '-rd1', '-c', 'IOPlatformExpertDevice'],
                    capture_output=True,
                    text=True,
                    check=True
                )
                for line in result.stdout.split('\n'):
                    if 'IOPlatformUUID' in line:
                        return line.split('"')[3]
            except (subprocess.SubprocessError, FileNotFoundError, IndexError) as e:
                logger.debug(f"Could not get macOS IOPlatformUUID: {e}")
            
            # Final fallback
            return os.environ.get('HOSTNAME', 'default-machine')
    
    except Exception as e:
        logger.error(f"Error getting machine ID: {e}")
        return 'default-machine'


def derive_encryption_key(salt: Optional[bytes] = None) -> bytes:
    """
    Derive an encryption key from machine ID.
    
    Uses PBKDF2 to derive a strong encryption key from the machine ID.
    
    Args:
        salt: Optional salt (defaults to fixed salt for deterministic keys)
    
    Returns:
        32-byte encryption key
    """
    machine_id = get_machine_id()
    
    # Use fixed salt for deterministic key derivation per machine
    if salt is None:
        salt = b'pywats-client-encryption-v1'
    
    # Derive key using PBKDF2HMAC
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    
    key = kdf.derive(machine_id.encode())
    return base64.urlsafe_b64encode(key)


def encrypt_token(token: str) -> str:
    """
    Encrypt an API token for secure storage.
    
    Args:
        token: Plain text API token
    
    Returns:
        Base64-encoded encrypted token
    """
    if not token:
        return ""
    
    try:
        key = derive_encryption_key()
        f = Fernet(key)
        encrypted = f.encrypt(token.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    except Exception as e:
        logger.error(f"Error encrypting token: {e}")
        raise


def decrypt_token(encrypted_token: str) -> str:
    """
    Decrypt a stored API token.
    
    Args:
        encrypted_token: Base64-encoded encrypted token
    
    Returns:
        Plain text API token
    """
    if not encrypted_token:
        return ""
    
    try:
        key = derive_encryption_key()
        f = Fernet(key)
        encrypted = base64.urlsafe_b64decode(encrypted_token.encode())
        decrypted = f.decrypt(encrypted)
        return decrypted.decode()
    except Exception as e:
        logger.error(f"Error decrypting token: {e}")
        raise


def hash_password(password: str) -> str:
    """
    Hash a password for comparison (not storage).
    
    This is only used for local validation, not for server authentication.
    
    Args:
        password: Plain text password
    
    Returns:
        SHA256 hash of password
    """
    return hashlib.sha256(password.encode()).hexdigest()


def migrate_plain_token(plain_token: str) -> str:
    """
    Migrate a plain text token to encrypted format.
    
    Args:
        plain_token: Plain text API token
    
    Returns:
        Encrypted token
    """
    if not plain_token:
        return ""
    
    logger.info("Migrating plain text token to encrypted format")
    return encrypt_token(plain_token)
