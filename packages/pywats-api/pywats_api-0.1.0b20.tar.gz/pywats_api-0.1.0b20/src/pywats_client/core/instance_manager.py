"""
Instance Manager for pyWATS Client

Handles multi-instance support using file-based locking to ensure
each instance has a unique lock and can be identified.
"""

import os
import sys
import json
import atexit
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class InstanceLock:
    """
    File-based instance lock for multi-instance support.
    
    Creates a lock file with instance information that other
    instances can read to identify running clients.
    """
    
    def __init__(self, instance_id: str, base_path: Optional[Path] = None):
        self.instance_id = instance_id
        self.base_path = base_path or self._get_default_lock_path()
        self.lock_file = self.base_path / f"instance_{instance_id}.lock"
        self._locked = False
    
    def _get_default_lock_path(self) -> Path:
        """Get default path for lock files"""
        if os.name == 'nt':
            base = Path(os.environ.get('TEMP', '')) / 'pyWATS_Client'
        else:
            base = Path('/tmp') / 'pywats_client'
        base.mkdir(parents=True, exist_ok=True)
        return base
    
    def acquire(self, instance_name: str = "", pid: Optional[int] = None) -> bool:
        """
        Acquire the lock for this instance.
        
        Returns True if lock acquired, False if instance already running.
        """
        if self._locked:
            return True
        
        # Check if lock file exists and is stale
        if self.lock_file.exists():
            try:
                with open(self.lock_file, 'r') as f:
                    lock_data = json.load(f)
                
                # Check if the process is still running
                old_pid = lock_data.get('pid')
                if old_pid and self._is_process_running(old_pid):
                    logger.warning(f"Instance {self.instance_id} already running (PID: {old_pid})")
                    return False
                
                # Stale lock, remove it
                logger.info(f"Removing stale lock for instance {self.instance_id}")
                self.lock_file.unlink()
            except (json.JSONDecodeError, KeyError):
                # Corrupted lock file, remove it
                self.lock_file.unlink()
        
        # Create lock file
        lock_data = {
            'instance_id': self.instance_id,
            'instance_name': instance_name,
            'pid': pid or os.getpid(),
            'started': datetime.now().isoformat(),
        }
        
        self.lock_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.lock_file, 'w') as f:
            json.dump(lock_data, f)
        
        self._locked = True
        
        # Register cleanup on exit
        atexit.register(self.release)
        
        return True
    
    def release(self) -> None:
        """Release the lock"""
        if self._locked and self.lock_file.exists():
            try:
                self.lock_file.unlink()
            except OSError:
                pass
            self._locked = False
    
    def _is_process_running(self, pid: int) -> bool:
        """Check if a process with given PID is running"""
        if os.name == 'nt':
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                handle = kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
                if handle:
                    kernel32.CloseHandle(handle)
                    return True
                return False
            except Exception as e:
                logger.debug(f"Error checking if process {pid} is running: {e}")
                return False
        else:
            try:
                os.kill(pid, 0)
                return True
            except OSError:
                return False
    
    def __enter__(self):
        if not self.acquire():
            raise RuntimeError(f"Could not acquire lock for instance {self.instance_id}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
        return False


class InstanceManager:
    """
    Manages multiple pyWATS Client instances.
    
    Provides functionality to:
    - List running instances
    - Get instance information
    - Create new instance configurations
    """
    
    def __init__(self, base_path: Optional[Path] = None):
        self.base_path = base_path or self._get_default_path()
    
    def _get_default_path(self) -> Path:
        """Get default path for instance data"""
        if os.name == 'nt':
            return Path(os.environ.get('TEMP', '')) / 'pyWATS_Client'
        return Path('/tmp') / 'pywats_client'
    
    def get_running_instances(self) -> List[Dict[str, Any]]:
        """Get information about all running instances"""
        instances = []
        
        if not self.base_path.exists():
            return instances
        
        for lock_file in self.base_path.glob("instance_*.lock"):
            try:
                with open(lock_file, 'r') as f:
                    lock_data = json.load(f)
                
                pid = lock_data.get('pid')
                if pid and self._is_process_running(pid):
                    instances.append(lock_data)
            except (json.JSONDecodeError, IOError):
                continue
        
        return instances
    
    def _is_process_running(self, pid: int) -> bool:
        """Check if a process with given PID is running"""
        if os.name == 'nt':
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                handle = kernel32.OpenProcess(0x1000, False, pid)
                if handle:
                    kernel32.CloseHandle(handle)
                    return True
                return False
            except Exception as e:
                logger.debug(f"Error checking if process {pid} is running: {e}")
                return False
        else:
            try:
                os.kill(pid, 0)
                return True
            except OSError:
                return False
    
    def is_instance_running(self, instance_id: str) -> bool:
        """Check if a specific instance is running"""
        lock_file = self.base_path / f"instance_{instance_id}.lock"
        
        if not lock_file.exists():
            return False
        
        try:
            with open(lock_file, 'r') as f:
                lock_data = json.load(f)
            
            pid = lock_data.get('pid')
            return pid and self._is_process_running(pid)
        except (json.JSONDecodeError, IOError):
            return False
    
    def cleanup_stale_locks(self) -> int:
        """Remove stale lock files and return count of removed locks"""
        removed = 0
        
        if not self.base_path.exists():
            return removed
        
        for lock_file in self.base_path.glob("instance_*.lock"):
            try:
                with open(lock_file, 'r') as f:
                    lock_data = json.load(f)
                
                pid = lock_data.get('pid')
                if not pid or not self._is_process_running(pid):
                    lock_file.unlink()
                    removed += 1
            except (json.JSONDecodeError, IOError):
                lock_file.unlink()
                removed += 1
        
        return removed
